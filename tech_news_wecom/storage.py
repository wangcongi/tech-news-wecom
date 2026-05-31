from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class SeenStore:
    db_path: Path

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_links (
                link TEXT PRIMARY KEY,
                first_seen_utc TEXT NOT NULL
            )
            """
        )
        return conn

    def filter_new(self, links: list[str]) -> list[str]:
        if not links:
            return []
        now = datetime.now(timezone.utc).isoformat()
        new_links: list[str] = []
        with self._connect() as conn:
            for link in links:
                cur = conn.execute("SELECT 1 FROM seen_links WHERE link = ?", (link,))
                if cur.fetchone():
                    continue
                new_links.append(link)
                conn.execute(
                    "INSERT OR IGNORE INTO seen_links(link, first_seen_utc) VALUES(?, ?)",
                    (link, now),
                )
        return new_links

