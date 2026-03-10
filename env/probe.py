#!/usr/bin/env python3
"""Probe — runs ONCE at install time, writes env.json."""

import json
import os
import shutil
import sys
import subprocess

ENV_PATH = os.path.expanduser("~/.config/lisa/env.json")


def run_probe() -> dict:
    env = {
        "distro": _detect_distro(),
        "package_manager": _detect_pkg_manager(),
        "aur_helper": _detect_aur_helper(),
        "init_system": _detect_init(),
        "environment": _detect_environment(),
        "shell": os.environ.get("SHELL", "bash").split("/")[-1],
        "sudo_available": shutil.which("sudo") is not None,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
    }
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    with open(ENV_PATH, "w") as f:
        json.dump(env, f, indent=2)
    print("[lisa] Environment detected and saved.")
    print(json.dumps(env, indent=2))
    return env


def load_env() -> dict:
    """Load env.json — call this everywhere instead of detecting at runtime."""
    if not os.path.exists(ENV_PATH):
        print("[lisa] env.json not found. Run install.sh first.")
        sys.exit(1)
    with open(ENV_PATH) as f:
        return json.load(f)


def _detect_distro() -> str:
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.strip().split("=")[1].strip('"').lower()
    except FileNotFoundError:
        pass
    return "unknown"


def _detect_pkg_manager() -> str:
    managers = ["pacman", "apt", "dnf", "zypper", "apk", "xbps-install", "emerge"]
    for mgr in managers:
        if shutil.which(mgr):
            return mgr
    return "unknown"


def _detect_aur_helper() -> str:
    helpers = ["yay", "paru", "trizen", "pikaur", "aurman"]
    for helper in helpers:
        if shutil.which(helper):
            return helper
    return "none"


def _detect_init() -> str:
    # systemd
    if os.path.isdir("/run/systemd/system"):
        return "systemd"
    # openrc
    if shutil.which("rc-service"):
        return "openrc"
    # runit
    if os.path.isdir("/run/runit"):
        return "runit"
    # s6
    if os.path.isdir("/run/s6"):
        return "s6"
    return "unknown"


def _detect_environment() -> str:
    # container check
    if os.path.exists("/.dockerenv"):
        return "docker"
    try:
        with open("/proc/1/cgroup") as f:
            if "docker" in f.read() or "lxc" in f.read():
                return "container"
    except FileNotFoundError:
        pass
    # WSL check
    try:
        with open("/proc/version") as f:
            if "microsoft" in f.read().lower():
                return "wsl"
    except FileNotFoundError:
        pass
    return "bare_metal"


if __name__ == "__main__":
    run_probe()
