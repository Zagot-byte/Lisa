#!/usr/bin/env python3
"""Orchestrator — decomposes tasks, runs ReAct loop."""

import re
from model.inference import call_model, is_ollama_running
from model.intent_parser import parse
from core.executor import execute, snapshot
from core.signal_handler import register, clear
from tools.sudo_handler import handle_sudo, needs_sudo
from memory.retriever import retrieve
from memory.db import insert
from env.probe import load_env
from utils.formatter import (
    format_execution, format_result, format_error, format_warning
)

MAX_STEPS = 10  # safety ceiling — loop never runs forever


def run(intent: str) -> None:
    """
    Full agentic pipeline:
    intent → parse → ReAct loop → log to memory
    """
    if not is_ollama_running():
        print(format_error("Ollama not running", "Start with: ollama serve"))
        return

    env = load_env()
    distro = env.get("distro", "unknown")
    pm = env.get("package_manager", "unknown")
    context = retrieve(intent, distro=distro)

    system = f"""You are Lisa, an AI terminal assistant for Linux.
Distro: {distro} | Package manager: {pm}
You translate user intent into safe shell commands.
Respond with ONLY the shell command to run. No explanation. No markdown.
If multiple steps are needed, output ONE command per response.
Never include sudo — the system handles privilege escalation.
{context}"""

    session_log = []
    steps = 0
    current_intent = intent

    print(f"\n[lisa] Working on: {intent}\n")

    while steps < MAX_STEPS:
        steps += 1

        # ask model for next command
        cmd_str = call_model(current_intent, system=system).strip()

        # strip any accidental sudo/markdown from model output
        cmd_str = _clean(cmd_str)

        if not cmd_str or cmd_str.lower() in ("done", "complete", "finished"):
            break

        # guardrail — reject hallucinated output before execution
        valid, reason = _is_valid_cmd(cmd_str)
        if not valid:
            print(format_warning("Guardrail triggered", reason))
            break

        cmd = cmd_str.split()
        print(format_execution(cmd))

        # snapshot before execution
        snap = snapshot(cmd)
        register(snap, cmd)

        # execute
        result = execute(cmd, risk="medium")

        # sudo escalation if needed
        if not result.success and needs_sudo(result):
            print(format_warning("Permission denied", f"Escalating: {cmd_str}"))
            result = handle_sudo(cmd, risk="medium")

        session_log.append({
            "step": steps,
            "cmd": cmd_str,
            "success": result.success,
            "output": result.output[:500],
        })

        clear()  # clear snapshot after step

        print(format_result(result.output, steps, cmd_str))

        if not result.success:
            print(format_error("Step failed", f"Stopped at step {steps}"))
            break

        # feed output back to model as context for next step
        current_intent = (
            f"Previous command: {cmd_str}\n"
            f"Output: {result.output[:300]}\n"
            f"Original goal: {intent}\n"
            f"What is the next command to run? Reply DONE if the goal is complete."
        )

    # log session to memory
    _log_session(intent, session_log, distro)


def _clean(cmd_str: str) -> str:
    """Strip sudo, backticks, markdown fences from model output."""
    cmd_str = re.sub(r"^```.*\n?", "", cmd_str)
    cmd_str = re.sub(r"```$", "", cmd_str)
    cmd_str = cmd_str.strip("`").strip()
    if cmd_str.startswith("sudo "):
        cmd_str = cmd_str[5:]
    return cmd_str.strip()


def _log_session(intent: str, log: list[dict], distro: str) -> None:
    """Write session summary to SQLite FTS memory."""
    commands = [s["cmd"] for s in log]
    outcomes = [s["success"] for s in log]
    overall = "success" if all(outcomes) else "failed" if not any(outcomes) else "incomplete"
    learnings = f"Ran {len(log)} step(s) for: '{intent}'. " + (
        "All succeeded." if overall == "success"
        else f"Failed at step {next(i+1 for i,s in enumerate(log) if not s['success'])}."
    )
    insert({
        "task": intent,
        "outcome": overall,
        "commands": commands,
        "learnings": learnings,
        "distro": distro,
    })


# ── Guardrails ─────────────────────────────────────────────────────

# commands that make no sense as single outputs
HALLUCINATION_PATTERNS = [
    r"^(yes|no|done|ok|sure|of course|i will|i can|here|this|that)$",
    r"^(the|a|an|to|is|are|was|were)\s",  # starts with article/verb
    r"\n.*\n",   # multi-line — model should output ONE command
    r"^#",       # comment only
    r"sorry|cannot|unable|don't|as an ai",  # refusal patterns
]

import re as _re

def _is_valid_cmd(cmd_str: str) -> tuple[bool, str]:
    """Basic sanity check on model output before execution."""
    if not cmd_str or len(cmd_str) < 2:
        return False, "Empty or too short"
    for pattern in HALLUCINATION_PATTERNS:
        if _re.search(pattern, cmd_str.strip().lower()):
            return False, f"Looks like hallucination: {cmd_str[:50]}"
    # must start with a known executable-like token
    first_word = cmd_str.strip().split()[0]
    if not _re.match(r"^[\w./-]+$", first_word):
        return False, f"Invalid command start: {first_word}"
    return True, ""
