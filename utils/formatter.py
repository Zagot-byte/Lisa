#!/usr/bin/env python3
"""Formatter — box-style terminal UI for Lisa. Ported from command-butler."""


def format_plan(intent: str, command: list[str], description: str, risk: str, requires_sudo: bool = False) -> str:
    cmd_str = " ".join(command)
    risk_upper = risk.upper()
    sudo_note = " (REQUIRES SUDO)" if requires_sudo else ""
    width = 66
    inner_width = width - 4
    lines = [
        "╔" + "═" * (width - 2) + "╗",
        "║" + " LISA — EXECUTION PLAN ".center(width - 2) + "║",
        "╠" + "═" * (width - 2) + "╣",
        "║" + f" Intent: {intent[:inner_width - 10]}".ljust(width - 2) + "║",
        "║" + f" Description: {description[:inner_width - 14]}".ljust(width - 2) + "║",
        "║" + " ".ljust(width - 2) + "║",
        "║" + f" Command: {cmd_str[:inner_width - 11]}".ljust(width - 2) + "║",
        "║" + " ".ljust(width - 2) + "║",
        "║" + f" Risk: {risk_upper}{sudo_note}".ljust(width - 2) + "║",
        "╚" + "═" * (width - 2) + "╝",
    ]
    return "\n".join(lines)


def format_result(output: str, steps: int, cmd_executed: str = None) -> str:
    width = 66
    output_lines = output.strip().split('\n') if output else []
    if len(output_lines) > 20:
        summary = '\n'.join(output_lines[:10]) + f'\n... ({len(output_lines) - 10} more lines)'
    else:
        summary = output.strip() if output else "(no output)"
    header = [
        "",
        "╔" + "═" * (width - 2) + "╗",
        "║" + f" RESULT (completed in {steps} step{'s' if steps != 1 else ''}) ".center(width - 2) + "║",
    ]
    if cmd_executed:
        header.append("║" + f" Command: {cmd_executed[:width - 12]}".ljust(width - 2) + "║")
    header.extend(["╚" + "═" * (width - 2) + "╝", "", "📋 Output:", ""])
    return "\n".join(header) + "\n" + summary


def format_error(title: str, message: str) -> str:
    width = 66
    lines = ["", "╔" + "═" * (width - 2) + "╗",
        "║" + f" ❌ {title} ".center(width - 2) + "║",
        "╠" + "═" * (width - 2) + "╣",
        "║" + f" {message[:width - 4]}".ljust(width - 2) + "║",
        "╚" + "═" * (width - 2) + "╝", ""]
    return "\n".join(lines)


def format_warning(title: str, message: str) -> str:
    width = 66
    lines = ["", "╔" + "═" * (width - 2) + "╗",
        "║" + f" ⚠️  {title} ".center(width - 2) + "║",
        "╠" + "═" * (width - 2) + "╣",
        "║" + f" {message[:width - 4]}".ljust(width - 2) + "║",
        "╚" + "═" * (width - 2) + "╝", ""]
    return "\n".join(lines)


def format_execution(cmd: list[str]) -> str:
    cmd_str = " ".join(cmd)
    width = 66
    lines = ["", "┌" + "─" * (width - 2) + "┐",
        "│" + " 🔧 EXECUTING ".center(width - 2) + "│",
        "├" + "─" * (width - 2) + "┤",
        "│" + f" $ {cmd_str[:width - 6]}".ljust(width - 2) + "│",
        "└" + "─" * (width - 2) + "┘", ""]
    return "\n".join(lines)


def format_success(title: str, message: str) -> str:
    width = 66
    lines = ["", "╔" + "═" * (width - 2) + "╗",
        "║" + f" ✅ {title} ".center(width - 2) + "║",
        "╠" + "═" * (width - 2) + "╣",
        "║" + f" {message[:width - 4]}".ljust(width - 2) + "║",
        "╚" + "═" * (width - 2) + "╝", ""]
    return "\n".join(lines)


def format_confirm(message: str) -> str:
    """One-line confirmation prompt. Always clean and short."""
    return f"\n[lisa] {message} (y/n) "


def format_prompt() -> str:
    return "lisa> "


def format_sudo_prompt() -> str:
    return "\n🔑 Enter sudo password: "


def format_sudo_success() -> str:
    return "\n🛡️  Sudo escalation successful.\n"


def format_rollback(cmd: str) -> str:
    width = 66
    lines = ["", "╔" + "═" * (width - 2) + "╗",
        "║" + " ↩️  ROLLING BACK ".center(width - 2) + "║",
        "╠" + "═" * (width - 2) + "╣",
        "║" + f" Undoing: {cmd[:width - 12]}".ljust(width - 2) + "║",
        "╚" + "═" * (width - 2) + "╝", ""]
    return "\n".join(lines)
