import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path.home() / ".mg400ai" / "library.db"

class ToneLibrary:
    def __init__(self):
        self._ensure_db()

    def _ensure_db(self):
        os.makedirs(DB_PATH.parent, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    tags TEXT,
                    description TEXT,
                    parameters TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_tone(self, name: str, tags: str, description: str, parameters: dict):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tones (name, tags, description, parameters)
                VALUES (?, ?, ?, ?)
            """, (name, tags, description, json.dumps(parameters)))
            conn.commit()
            return cursor.lastrowid

    def load_all_tones(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tones ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_tone(self, tone_id: int):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tones WHERE id = ?", (tone_id,))
            conn.commit()
