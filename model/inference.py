#!/usr/bin/env python3
"""Inference — Ollama REST API interface. No external dependencies."""

import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/chat"

# swap this to fine-tuned model later
DEFAULT_MODEL = "llama3.2:3b"


def call_model(
    prompt: str,
    system: str = "",
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,  # low temp = more deterministic, better for commands
) -> str:
    """
    Send prompt to Ollama, return response string.
    Raises RuntimeError if Ollama is unreachable or returns an error.
    """
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [],
    }

    if system:
        payload["messages"].append({"role": "system", "content": system})

    payload["messages"].append({"role": "user", "content": prompt})

    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data["message"]["content"].strip()

    except urllib.error.URLError:
        raise RuntimeError(
            "[lisa] Cannot reach Ollama. Is it running? Try: ollama serve"
        )
    except KeyError:
        raise RuntimeError(f"[lisa] Unexpected Ollama response: {data}")


def is_ollama_running() -> bool:
    """Quick health check before any model call."""
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=3)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lisa inference tester")
    parser.add_argument("prompt", type=str, help="Prompt to send")
    parser.add_argument("--system", type=str, default="", help="System prompt")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Model to use")
    args = parser.parse_args()

    if not is_ollama_running():
        print("[lisa] Ollama not running. Start with: ollama serve")
        exit(1)

    print(f"[lisa] Using model: {args.model}\n")
    response = call_model(args.prompt, system=args.system, model=args.model)
    print(response)
