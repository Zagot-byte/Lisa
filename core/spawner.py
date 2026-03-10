#!/usr/bin/env python3
"""Spawner — entry point. Routes to passive or active mode."""

import sys
from core.orchestrator import run
from utils.formatter import format_prompt, format_error


def spawn(intent: str, interactive: bool = False, stderr_context: str = None) -> None:
    """
    Routes invocation to correct mode:
    - stderr_context set → passive mode (triggered by shell hook)
    - interactive        → REPL mode
    - intent set         → active/agentic mode
    """
    if stderr_context:
        _passive_mode(stderr_context)
    elif interactive:
        _interactive_mode()
    elif intent:
        run(intent)
    else:
        print(format_error("No input", "Provide an intent or use --interactive"))
        sys.exit(1)


def _passive_mode(stderr_output: str) -> None:
    """
    Triggered by shell hook on stderr.
    Lisa reads the error and suggests a fix.
    """
    from model.inference import call_model, is_ollama_running
    from utils.formatter import format_confirm

    if not is_ollama_running():
        return  # silent fail in passive mode — don't interrupt user

    system = """You are Lisa, a Linux terminal assistant.
A command just failed. Suggest ONE fix command.
Reply with ONLY the command. No explanation. No markdown.
If no fix is possible, reply: NONE"""

    suggestion = call_model(
        f"This command failed with this error:\n{stderr_output}\nWhat is the fix?",
        system=system
    ).strip()

    if not suggestion or suggestion.upper() == "NONE":
        return  # nothing useful to suggest, stay silent

    answer = input(format_confirm(f"Run fix: {suggestion}")).strip().lower()
    if answer == "y":
        run(suggestion)


def _interactive_mode() -> None:
    """Simple REPL loop."""
    import readline  # enables up-arrow history
    print("[lisa] Interactive mode. Type 'exit' to quit.\n")
    while True:
        try:
            intent = input(format_prompt()).strip()
            if intent.lower() in ("exit", "quit", "q"):
                print("[lisa] Bye.")
                break
            if intent:
                run(intent)
        except (EOFError, KeyboardInterrupt):
            print("\n[lisa] Bye.")
            break
