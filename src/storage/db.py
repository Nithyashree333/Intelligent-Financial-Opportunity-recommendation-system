"""SQLite persistence of validated opportunity records (rebuildable from docs)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..schemas import Opportunity


class OpportunityDB:
    def __init__(self, cfg: dict):
        self.path = cfg["paths"]["db"]
        # Ensure the parent directory exists so SQLite can create the file.
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS opportunities (id TEXT PRIMARY KEY, json TEXT NOT NULL)"
        )

    def clear(self) -> None:
        """Wipe all rows so a fresh --extract starts from a clean slate."""
        self._conn.execute("DELETE FROM opportunities")
        self._conn.commit()

    def upsert(self, opp: Opportunity) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO opportunities VALUES (?, ?)",
            (opp.id, opp.model_dump_json()),
        )
        self._conn.commit()

    def get(self, oid: str) -> Opportunity | None:
        row = self._conn.execute(
            "SELECT json FROM opportunities WHERE id = ?", (oid,)).fetchone()
        return Opportunity(**json.loads(row[0])) if row else None

    def get_many(self, ids: list[str]) -> list[Opportunity]:
        """Return opportunities in the SAME ORDER as ids (unknown ids skipped)."""
        return [o for oid in ids if (o := self.get(oid)) is not None]

    def all(self) -> list[Opportunity]:
        rows = self._conn.execute("SELECT json FROM opportunities").fetchall()
        return [Opportunity(**json.loads(r[0])) for r in rows]
