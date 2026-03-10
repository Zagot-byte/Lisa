#!/usr/bin/env python3
"""Session writer — summarizes completed session into memory."""

from model.inference import call_model
from memory.db import insert


def write_session(intent: str, steps: list[dict], distro: str) -> None:
    """
    Call model once at session end to summarize what happened.
    Writes structured entry to SQLite FTS memory.
    """
    if not steps:
        return

    commands = [s["cmd"] for s in steps]
    outcomes = [s["success"] for s in steps]
    overall = (
        "success" if all(outcomes)
        else "failed" if not any(outcomes)
        else "incomplete"
    )

    # ask model to summarize learnings in one sentence
    step_summary = "\n".join(
        f"- {s['cmd']} → {'ok' if s['success'] else 'failed'}: {s['output'][:100]}"
        for s in steps
    )

    system = """You are summarizing a terminal session for future memory.
Write ONE sentence describing what was learned or what worked.
Be specific. No filler. No markdown."""

    prompt = f"""Task: {intent}
Steps:
{step_summary}
What is the key learning from this session?"""

    try:
        learnings = call_model(prompt, system=system)
    except Exception:
        # fallback if model unavailable
        learnings = f"Completed '{intent}' in {len(steps)} step(s). Outcome: {overall}."

    insert({
        "task": intent,
        "outcome": overall,
        "commands": commands,
        "learnings": learnings,
        "distro": distro,
    })
