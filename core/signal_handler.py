#!/usr/bin/env python3
"""Signal handler — SIGINT → rollback → clean exit."""

import signal
import sys
from core.executor import rollback

_current_snapshot = {}
_current_cmd = []


def register(snapshot: dict, cmd: list[str]) -> None:
    """Register current snapshot before each command execution."""
    global _current_snapshot, _current_cmd
    _current_snapshot = snapshot
    _current_cmd = cmd


def clear() -> None:
    """Clear snapshot after successful execution."""
    global _current_snapshot, _current_cmd
    _current_snapshot = {}
    _current_cmd = []


def _handle_sigint(sig, frame) -> None:
    print("\n[lisa] Interrupted. Rolling back...")
    if _current_snapshot:
        rollback(_current_snapshot)
    else:
        print("[lisa] Nothing to rollback.")
    print("[lisa] Exiting cleanly.")
    sys.exit(0)


# register globally on import
signal.signal(signal.SIGINT, _handle_sigint)
