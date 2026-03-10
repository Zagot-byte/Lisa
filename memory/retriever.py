#!/usr/bin/env python3
"""Retriever — RAG layer. Formats past memory into prompt-injectable context."""

from memory.db import search, init_db


MAX_CONTEXT_ENTRIES = 3  # keep prompt lean
MAX_COMMANDS_SHOWN = 5   # cap commands per entry


def retrieve(task: str, distro: str = None) -> str:
    """
    Search memory for relevant past sessions.
    Returns a formatted string ready to inject into system prompt.
    Returns empty string if no relevant memory found.
    """
    try:
        # sanitize query for FTS5 — strip special chars that break matching
        query = _sanitize(task)
        if not query:
            return ""

        results = search(query, distro=distro, limit=MAX_CONTEXT_ENTRIES)
        if not results:
            return ""

        return _format(results)

    except Exception:
        # memory retrieval should never crash the agent
        return ""


def _sanitize(query: str) -> str:
    """Strip FTS5 special characters to avoid query syntax errors."""
    special = set('":*^()OR AND NOT')
    cleaned = "".join(c for c in query if c not in special)
    return cleaned.strip()


def _format(results: list[dict]) -> str:
    """Format search results into a clean context block for prompt injection."""
    lines = ["## Relevant past sessions:", ""]

    for i, r in enumerate(results, 1):
        outcome_emoji = {"success": "✅", "failed": "❌", "incomplete": "⚠️"}.get(r["outcome"], "❔")
        commands = r["commands"][:MAX_COMMANDS_SHOWN]
        cmd_str = ", ".join(f"`{c}`" for c in commands)
        if len(r["commands"]) > MAX_COMMANDS_SHOWN:
            cmd_str += f" ... (+{len(r['commands']) - MAX_COMMANDS_SHOWN} more)"

        lines += [
            f"### [{i}] {outcome_emoji} {r['task']}",
            f"- Commands: {cmd_str}",
            f"- Learned: {r['learnings']}",
            f"- Distro: {r['distro']} | {r['timestamp'][:10]}",
            "",
        ]

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lisa memory retriever")
    parser.add_argument("query", type=str, help="Task to search for")
    parser.add_argument("--distro", type=str, help="Filter by distro")
    args = parser.parse_args()

    context = retrieve(args.query, distro=args.distro)
    if context:
        print(context)
    else:
        print("[lisa] No relevant memory found.")
