#!/usr/bin/env python3
"""Sudo handler — privilege escalation tool. Ported from command-butler."""

import subprocess
import time
import getpass
from core.executor import ExecutionResult, get_timeout, _handle_timeout
from utils.formatter import format_confirm, format_sudo_prompt, format_sudo_success


def handle_sudo(cmd: list[str], risk: str = "medium") -> ExecutionResult:
    """
    Ask user for confirmation + password, run command with sudo.
    Returns ExecutionResult. Never raises.
    """
    # confirm with user first
    confirm = input(format_confirm(f"Run with sudo: {' '.join(cmd)}?")).strip().lower()
    if confirm != "y":
        return ExecutionResult(
            success=False,
            output="[lisa] Sudo cancelled by user.",
            exit_code=1,
            duration=0.0,
        )

    password = getpass.getpass(format_sudo_prompt())
    sudo_cmd = ["sudo", "-S"] + cmd
    timeout = get_timeout(cmd[0], risk)
    start = time.time()

    try:
        process = subprocess.Popen(
            sudo_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=f"{password}\n", timeout=timeout)

        # strip sudo prompt noise from output
        output = (stdout + stderr).replace("[sudo] password for", "").strip()
        success = process.returncode == 0

        if success:
            print(format_sudo_success())

        return ExecutionResult(
            success=success,
            output=output,
            exit_code=process.returncode,
            duration=time.time() - start,
        )

    except subprocess.TimeoutExpired:
        return _handle_timeout(process, cmd, start)

    except Exception as e:
        return ExecutionResult(
            success=False,
            output=f"Sudo error: {e}",
            exit_code=-1,
            duration=time.time() - start,
        )


def needs_sudo(result: ExecutionResult) -> bool:
    """
    Detect if a failed command needs sudo.
    Called by orchestrator after a failed execute().
    """
    indicators = ["permission denied", "operation not permitted", "eacces"]
    return any(i in result.output.lower() for i in indicators)
