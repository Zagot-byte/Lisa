#!/usr/bin/env python3
"""SQLite FTS memory store for Lisa."""

import sqlite3
import json
import os
import shutil
from datetime import datetime, timezone

DB_PATH = os.path.expanduser("~/.config/lisa/memory.db")
BACKUP_PATH = os.path.expanduser("~/.config/lisa/memory.backup.db")


def init_db() -> sqlite3.Connection:
    """Initialize DB and FTS table. Safe to call multiple times."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memory
        USING fts5(
            task,        -- what the user asked for
            outcome,     -- what happened (success/failed/incomplete)
            commands,    -- commands that were run
            learnings,   -- what lisa learned from this session
            distro,      -- distro context (for distro-specific filtering)
            timestamp    -- ISO timestamp
        )
    """)
    conn.commit()
    return conn


def insert(entry: dict) -> None:
    """
    Insert a session entry into memory.
    entry = {
        "task": str,
        "outcome": str,       # "success" | "failed" | "incomplete"
        "commands": [str],    # list of commands run
        "learnings": str,     # freeform summary from session_writer
        "distro": str         # from env.json
    }
    """
    _backup()
    conn = init_db()
    conn.execute(
        "INSERT INTO memory VALUES (?, ?, ?, ?, ?, ?)",
        (
            entry.get("task", ""),
            entry.get("outcome", ""),
            json.dumps(entry.get("commands", [])),
            entry.get("learnings", ""),
            entry.get("distro", ""),
            datetime.now(timezone.utc).isoformat(),
        )
    )
    conn.commit()
    conn.close()


def search(query: str, distro: str = None, limit: int = 5) -> list[dict]:
    """
    FTS search over memory. Returns list of matching entries.
    Optionally filter by distro for distro-specific context.
    """
    conn = init_db()
    if distro:
        rows = conn.execute(
            """
            SELECT task, outcome, commands, learnings, distro, timestamp
            FROM memory
            WHERE memory MATCH ? AND distro = ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, distro, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT task, outcome, commands, learnings, distro, timestamp
            FROM memory
            WHERE memory MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit)
        ).fetchall()
    conn.close()
    return [
        {
            "task": r[0],
            "outcome": r[1],
            "commands": json.loads(r[2]),
            "learnings": r[3],
            "distro": r[4],
            "timestamp": r[5],
        }
        for r in rows
    ]


def count() -> int:
    """Return total number of entries in memory."""
    conn = init_db()
    n = conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
    conn.close()
    return n


def _backup() -> None:
    """Backup DB before every write. Silent if DB doesn't exist yet."""
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)


if __name__ == "__main__":
    # Quick smoke test
    print("[lisa] Initializing memory DB...")
    init_db()

    print("[lisa] Inserting test entry...")
    insert({
        "task": "install nmap and scan localhost",
        "outcome": "success",
        "commands": ["pacman -S nmap", "nmap localhost"],
        "learnings": "nmap was not installed. installed via pacman. scan completed successfully.",
        "distro": "arch"
    })

    print(f"[lisa] Total entries: {count()}")

    print("[lisa] Searching for 'nmap'...")
    results = search("nmap")
    for r in results:
        print(json.dumps(r, indent=2))
