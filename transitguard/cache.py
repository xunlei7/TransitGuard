from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CachedFeed:
    payload: bytes
    fetched_at: datetime


class FeedCache:
    def __init__(self, path: str | Path = ".cache/transitguard.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feeds (
                    url TEXT PRIMARY KEY,
                    payload BLOB NOT NULL,
                    fetched_at TEXT NOT NULL
                )
                """
            )

    def get(self, url: str) -> CachedFeed | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload, fetched_at FROM feeds WHERE url = ?", (url,)
            ).fetchone()
        if not row:
            return None
        return CachedFeed(row[0], datetime.fromisoformat(row[1]))

    def put(self, url: str, payload: bytes, *, fetched_at: datetime | None = None) -> None:
        fetched_at = fetched_at or datetime.now(timezone.utc)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feeds(url, payload, fetched_at) VALUES (?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET payload = excluded.payload, fetched_at = excluded.fetched_at
                """,
                (url, payload, fetched_at.isoformat()),
            )

