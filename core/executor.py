#!/usr/bin/env python3
"""Executor — runs commands, manages snapshots, rollback."""

import subprocess
import signal
import time
import os
import shutil
from dataclasses import dataclass

# DANGEROUS command blocklist — never execute these
BLOCKLIST = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=",
    ":(){ :|:& };:", "> /dev/sda", "chmod -R 777 /",
    "shutdown", "reboot", "halt", "poweroff",
]

@dataclass
class ExecutionResult:
    success: bool
    output: str
    exit_code: int
    duration: float
    timed_out: bool = False
    killed: bool = False


TIMEOUTS = {
    "low":    {"default": 30,  "long": ["find", "grep"]},
    "medium": {"default": 120, "long": ["du", "find", "grep"]},
    "high":   {"default": 300, "long": ["fsck", "nmap", "rsync"]},
}


def get_timeout(cmd_name: str, risk: str = "low") -> int:
    cfg = TIMEOUTS.get(risk, TIMEOUTS["low"])
    return cfg["default"] * 2 if cmd_name in cfg["long"] else cfg["default"]


def is_safe(cmd: str) -> tuple[bool, str]:
    """Check command against blocklist. Returns (safe, reason)."""
    cmd_lower = cmd.lower().strip()
    for blocked in BLOCKLIST:
        if blocked in cmd_lower:
            return False, f"Blocked dangerous command: {blocked}"
    return True, ""


def execute(cmd: list[str] | str, risk: str = "low") -> ExecutionResult:
    """
    Run a command via shell — supports ~, pipes, redirects.
    Never raises — errors captured in result.
    """
    # normalize to string for shell=True
    cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
    cmd_name = cmd[0] if isinstance(cmd, list) else cmd_str.split()[0]

    # security check first
    safe, reason = is_safe(cmd_str)
    if not safe:
        return ExecutionResult(
            success=False,
            output=f"[lisa] Blocked: {reason}",
            exit_code=1,
            duration=0.0,
        )

    timeout = get_timeout(cmd_name, risk)
    start = time.time()

    try:
        process = subprocess.Popen(
            cmd_str,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if timeout > 30:
            print(f"⏳ Running {cmd_name}... (timeout: {timeout}s)", end="", flush=True)
            elapsed = 0
            while elapsed < timeout:
                if process.poll() is not None:
                    break
                if elapsed % 5 == 0 and elapsed > 0:
                    print(".", end="", flush=True)
                time.sleep(1)
                elapsed += 1
            print()
            if elapsed >= timeout and process.poll() is None:
                return _handle_timeout(process, cmd_name, start)
        else:
            try:
                process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                return _handle_timeout(process, cmd_name, start)

        stdout, stderr = process.communicate()
        return ExecutionResult(
            success=(process.returncode == 0),
            output=(stdout + stderr).strip(),
            exit_code=process.returncode,
            duration=time.time() - start,
        )

    except Exception as e:
        return ExecutionResult(
            success=False,
            output=f"Execution error: {e}",
            exit_code=-1,
            duration=time.time() - start,
        )


def _handle_timeout(process, cmd_name, start) -> ExecutionResult:
    print(f"\n⏰ {cmd_name} timed out, interrupting...")
    try:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=5)
        stdout, stderr = process.communicate()
        return ExecutionResult(
            success=False,
            output=(stdout + stderr).strip() + "\n⚠️  Interrupted due to timeout",
            exit_code=process.returncode,
            duration=time.time() - start,
            timed_out=True,
        )
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return ExecutionResult(
            success=False,
            output=f"❌ {cmd_name} force-killed after timeout.",
            exit_code=-9,
            duration=time.time() - start,
            timed_out=True,
            killed=True,
        )


# ── Snapshot & Rollback ────────────────────────────────────────────

SNAPSHOT_DIR = os.path.expanduser("~/.config/lisa/.snapshots")


def snapshot(cmd: list[str] | str) -> dict:
    """Snapshot file targets found in cmd for rollback."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    cmd_list = cmd if isinstance(cmd, list) else cmd.split()
    snapped = {}
    for arg in cmd_list:
        expanded = os.path.expanduser(arg)
        if os.path.isfile(expanded):
            dest = os.path.join(SNAPSHOT_DIR, expanded.replace("/", "_"))
            shutil.copy2(expanded, dest)
            snapped[expanded] = dest
    return {"files": snapped, "cmd": cmd}


def rollback(snap: dict) -> None:
    """Restore files from snapshot on SIGINT."""
    files = snap.get("files", {})
    if not files:
        print("[lisa] Nothing to rollback.")
        return
    for original, backup in files.items():
        if os.path.exists(backup):
            shutil.copy2(backup, original)
            os.remove(backup)
            print(f"[lisa] Restored: {original}")
