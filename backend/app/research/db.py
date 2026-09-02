"""Persistent research memory. Every run is stored so the next run on the same
asset can see how the thesis has moved."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  asset TEXT NOT NULL,
  investor_id TEXT NOT NULL,
  created TEXT NOT NULL,
  direction TEXT,
  action TEXT,
  confidence REAL,
  degraded INTEGER DEFAULT 0,
  thesis TEXT,
  decision TEXT,
  metrics TEXT,
  snapshot TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_asset ON runs(asset, created);
CREATE TABLE IF NOT EXISTS signals (
  run_id TEXT, asset TEXT, created TEXT, score REAL, direction TEXT, price REAL
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def save_run(row: dict[str, Any]) -> None:
    conn = connect()
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO runs
            (run_id, asset, investor_id, created, direction, action, confidence,
             degraded, thesis, decision, metrics, snapshot)
            VALUES (:run_id,:asset,:investor_id,:created,:direction,:action,
                    :confidence,:degraded,:thesis,:decision,:metrics,:snapshot)""",
            row,
        )
    conn.close()


def save_signal(run_id: str, asset: str, created: str, score: float,
                direction: str, price: float) -> None:
    conn = connect()
    with conn:
        conn.execute(
            "INSERT INTO signals VALUES (?,?,?,?,?,?)",
            (run_id, asset, created, score, direction, price),
        )
    conn.close()


def history(asset: str, limit: int = 20) -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        "SELECT run_id, asset, investor_id, created, direction, action, confidence,"
        " degraded, thesis FROM runs WHERE asset=? ORDER BY created DESC LIMIT ?",
        (asset.upper(), limit),
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["thesis"] = json.loads(d["thesis"]) if d["thesis"] else None
        out.append(d)
    return out


def recent_runs(limit: int = 25) -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        "SELECT run_id, asset, investor_id, created, direction, action, confidence,"
        " degraded FROM runs ORDER BY created DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
