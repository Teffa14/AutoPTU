"""SQLite-backed event log with snapshot support."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


@dataclass
class StoredEvent:
    id: str
    type: str
    time: str
    actor_id: Optional[str]
    payload: Dict[str, Any]


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id TEXT PRIMARY KEY,
                  type TEXT NOT NULL,
                  time TEXT NOT NULL,
                  actor_id TEXT,
                  payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                  id TEXT PRIMARY KEY,
                  time TEXT NOT NULL,
                  payload TEXT NOT NULL
                )
                """
            )

    def append(self, event: Dict[str, Any]) -> StoredEvent:
        payload = dict(event)
        time = payload.get("time") or datetime.now(timezone.utc).isoformat()
        payload["time"] = time
        record = StoredEvent(
            id=str(payload.get("id")),
            type=str(payload.get("type")),
            time=str(time),
            actor_id=payload.get("actor_id"),
            payload=payload.get("payload") or {},
        )
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO events (id, type, time, actor_id, payload) VALUES (?, ?, ?, ?, ?)",
                (record.id, record.type, record.time, record.actor_id, json.dumps(record.payload)),
            )
        return record

    def events(self, since: Optional[str] = None) -> Iterable[StoredEvent]:
        query = "SELECT id, type, time, actor_id, payload FROM events"
        params = []
        if since:
            query += " WHERE time >= ?"
            params.append(since)
        query += " ORDER BY time ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        for row in rows:
            yield StoredEvent(
                id=row["id"],
                type=row["type"],
                time=row["time"],
                actor_id=row["actor_id"],
                payload=json.loads(row["payload"] or "{}"),
            )

    def save_snapshot(self, snapshot_id: str, payload: Dict[str, Any]) -> None:
        time = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO snapshots (id, time, payload) VALUES (?, ?, ?)",
                (snapshot_id, time, json.dumps(payload)),
            )

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM snapshots WHERE id = ?",
                (snapshot_id,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row["payload"] or "{}")
