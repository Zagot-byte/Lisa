#!/usr/bin/env python3
"""Package manager tool — install/remove packages using distro-detected manager."""

import shutil
from core.executor import execute, ExecutionResult
from tools.sudo_handler import handle_sudo, needs_sudo
from env.probe import load_env

# package manager command map
PM_COMMANDS = {
    "pacman":       {"install": ["pacman", "-S", "--noconfirm"], "remove": ["pacman", "-Rs", "--noconfirm"], "update": ["pacman", "-Sy"]},
    "apt":          {"install": ["apt", "install", "-y"],         "remove": ["apt", "remove", "-y"],          "update": ["apt", "update"]},
    "dnf":          {"install": ["dnf", "install", "-y"],         "remove": ["dnf", "remove", "-y"],          "update": ["dnf", "check-update"]},
    "zypper":       {"install": ["zypper", "install", "-y"],      "remove": ["zypper", "remove", "-y"],       "update": ["zypper", "refresh"]},
    "apk":          {"install": ["apk", "add"],                   "remove": ["apk", "del"],                   "update": ["apk", "update"]},
    "xbps-install": {"install": ["xbps-install", "-y"],           "remove": ["xbps-remove", "-y"],            "update": ["xbps-install", "-Su"]},
}


def _get_pm() -> str:
    env = load_env()
    pm = env.get("package_manager", "unknown")
    if pm == "unknown" or pm not in PM_COMMANDS:
        raise RuntimeError(f"[lisa] Unsupported or unknown package manager: {pm}")
    return pm


def install(package: str) -> ExecutionResult:
    """Install a package. Escalates to sudo automatically if needed."""
    pm = _get_pm()
    cmd = PM_COMMANDS[pm]["install"] + [package]
    result = execute(cmd, risk="medium")
    if not result.success and needs_sudo(result):
        result = handle_sudo(cmd, risk="medium")
    return result


def remove(package: str) -> ExecutionResult:
    """Remove a package."""
    pm = _get_pm()
    cmd = PM_COMMANDS[pm]["remove"] + [package]
    result = execute(cmd, risk="medium")
    if not result.success and needs_sudo(result):
        result = handle_sudo(cmd, risk="medium")
    return result


def update_index() -> ExecutionResult:
    """Update package index."""
    pm = _get_pm()
    cmd = PM_COMMANDS[pm]["update"]
    result = execute(cmd, risk="low")
    if not result.success and needs_sudo(result):
        result = handle_sudo(cmd, risk="low")
    return result


def is_installed(package: str) -> bool:
    """Check if a package is already installed."""
    return shutil.which(package) is not None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lisa package manager tool")
    parser.add_argument("action", choices=["install", "remove", "update"], help="Action to perform")
    parser.add_argument("package", nargs="?", help="Package name")
    args = parser.parse_args()

    if args.action == "install":
        if not args.package:
            print("[lisa] Specify a package to install.")
        elif is_installed(args.package):
            print(f"[lisa] {args.package} is already installed.")
        else:
            r = install(args.package)
            print(r.output)
    elif args.action == "remove":
        r = remove(args.package)
        print(r.output)
    elif args.action == "update":
        r = update_index()
        print(r.output)
