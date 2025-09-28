# httpayer_cli/ai_cache.py
from __future__ import annotations
import sqlite3
from pathlib import Path
import json
import hashlib
from typing import Optional


def _db_path(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root / "ai_cache.db"


def ensure_tables(dbfile: Path):
    with sqlite3.connect(dbfile) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            model TEXT,
            bazaar_hash TEXT,
            prompt TEXT,
            response TEXT
        )
        """)
        con.commit()


def bazaar_hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_key(model: str, prompt: str, bhash: str, mode: str) -> str:
    return hashlib.sha256(f"{model}|{bhash}|{mode}|{prompt}".encode("utf-8")).hexdigest()


def get_cache(root: Path, key: str) -> Optional[str]:
    db = _db_path(root)
    ensure_tables(db)
    with sqlite3.connect(db) as con:
        cur = con.execute("SELECT response FROM cache WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None


def put_cache(root: Path, key: str, model: str, bhash: str, prompt: str, response: str):
    db = _db_path(root)
    ensure_tables(db)
    with sqlite3.connect(db) as con:
        con.execute(
            "INSERT OR REPLACE INTO cache(key, model, bazaar_hash, prompt, response) VALUES (?, ?, ?, ?, ?)",
            (key, model, bhash, prompt, response),
        )
        con.commit()
