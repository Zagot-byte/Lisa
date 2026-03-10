#!/usr/bin/env python3
"""Spawner — decides passive (stderr) vs active (explicit call) mode."""
# TODO: implement spawn()

def spawn(intent: str, interactive: bool = False, stderr_context: str = None) -> None:
    """
    Entry point for all Lisa invocations.
    - stderr_context set   → passive mode (triggered by shell hook)
    - intent set           → active/agentic mode
    - interactive          → REPL mode
    """
    raise NotImplementedError
