#!/usr/bin/env python3
"""
Quick end-to-end test:
user task → retrieve context → inject into prompt → model responds
"""
import sys
sys.path.insert(0, ".")

from memory.retriever import retrieve
from model.inference import call_model, is_ollama_running

TASK = "install nmap and scan my local network"
DISTRO = "arch"

SYSTEM = f"""You are Lisa, an AI terminal assistant for Linux.
You help users run shell commands safely.
Always respond with the exact command to run, nothing else.
Package manager for this system: pacman
{retrieve(TASK, distro=DISTRO)}
"""

print("=" * 60)
print(f"TASK: {TASK}")
print("=" * 60)
print("INJECTED CONTEXT:")
print(retrieve(TASK, distro=DISTRO) or "(none)")
print("=" * 60)

if not is_ollama_running():
    print("[lisa] Ollama not running.")
    sys.exit(1)

print("MODEL RESPONSE:")
print(call_model(TASK, system=SYSTEM))
