#!/usr/bin/env python3
"""Trimmer — pure Python dedup + cap. No model. Triggered by systemd timer."""

import sqlite3
import os

DB_PATH = os.path.expanduser("~/.config/lisa/memory.db")
MAX_ENTRIES = 500


def trim() -> None:
    if not os.path.exists(DB_PATH):
        print("[lisa] No memory DB found. Nothing to trim.")
        return

    conn = sqlite3.connect(DB_PATH)

    # get total count
    total = conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
    print(f"[lisa] Memory entries before trim: {total}")

    # remove exact duplicate tasks keeping latest
    conn.execute("""
        DELETE FROM memory WHERE rowid NOT IN (
            SELECT MAX(rowid) FROM memory GROUP BY task, outcome
        )
    """)

    # if still over cap, delete oldest entries
    after_dedup = conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
    if after_dedup > MAX_ENTRIES:
        excess = after_dedup - MAX_ENTRIES
        conn.execute(f"""
            DELETE FROM memory WHERE rowid IN (
                SELECT rowid FROM memory ORDER BY timestamp ASC LIMIT {excess}
            )
        """)

    conn.commit()
    final = conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
    conn.close()
    print(f"[lisa] Memory entries after trim: {final} (removed {total - final})")


if __name__ == "__main__":
    trim()
