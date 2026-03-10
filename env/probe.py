#!/usr/bin/env python3
"""Probe — runs ONCE at install time, writes env.json."""
import json, shutil, os, subprocess

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
        "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}"
    }
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    with open(ENV_PATH, "w") as f:
        json.dump(env, f, indent=2)
    print(f"[lisa] Environment detected and saved to {ENV_PATH}")
    print(json.dumps(env, indent=2))
    return env

def _detect_distro() -> str:
    # TODO: parse /etc/os-release
    raise NotImplementedError

def _detect_pkg_manager() -> str:
    # TODO: check shutil.which for pacman, apt, dnf, zypper
    raise NotImplementedError

def _detect_aur_helper() -> str:
    # TODO: check for yay, paru, trizen
    raise NotImplementedError

def _detect_init() -> str:
    # TODO: check systemd, openrc, runit
    raise NotImplementedError

def _detect_environment() -> str:
    # TODO: check for WSL, container (/.dockerenv), bare metal
    raise NotImplementedError

if __name__ == "__main__":
    run_probe()
