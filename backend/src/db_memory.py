import os
import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger("db_memory")

# SQLite database file path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "memory.db")


def get_connection():
    """Ensure data directory exists and return SQLite connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize users memory table schema if it does not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                language_preference TEXT DEFAULT 'English',
                current_level TEXT DEFAULT 'Beginner',
                topics_covered TEXT DEFAULT '',
                mistakes_noted TEXT DEFAULT '',
                facts_json TEXT DEFAULT '{}',
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        logger.info(f"SQLite database initialized at {DB_PATH}")


def get_user(query: str) -> dict | None:
    """Look up a user record by user_id or case-insensitive name."""
    init_db()
    clean_query = query.strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE LOWER(user_id) = LOWER(?) OR LOWER(name) = LOWER(?)",
            (clean_query, clean_query),
        )
        row = cursor.fetchone()
        if row:
            res = dict(row)
            try:
                res["facts"] = json.loads(res.get("facts_json", "{}"))
            except Exception:
                res["facts"] = {}
            return res
    return None


def save_user(
    user_id: str,
    name: str,
    language_preference: str = "English",
    current_level: str = "IR Sensor Calibration",
    topics_covered: str = "",
    mistakes_noted: str = "",
) -> dict:
    """Save or update a caller's memory record in SQLite."""
    init_db()
    clean_id = user_id.strip() or name.strip()
    clean_name = name.strip() or user_id.strip()
    now_str = datetime.now().isoformat()

    facts = {
        "current_level": current_level,
        "topics_covered": topics_covered,
        "mistakes_noted": mistakes_noted,
    }
    facts_json = json.dumps(facts)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, name, language_preference, current_level, topics_covered, mistakes_noted, facts_json, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                current_level = excluded.current_level,
                topics_covered = excluded.topics_covered,
                mistakes_noted = excluded.mistakes_noted,
                facts_json = excluded.facts_json,
                last_interaction = excluded.last_interaction
            """,
            (
                clean_id,
                clean_name,
                language_preference,
                current_level,
                topics_covered,
                mistakes_noted,
                facts_json,
                now_str,
            ),
        )
        conn.commit()
        logger.info(f"Saved memory record for user {clean_name} ({clean_id})")

    return {
        "user_id": clean_id,
        "name": clean_name,
        "language_preference": language_preference,
        "current_level": current_level,
        "topics_covered": topics_covered,
        "mistakes_noted": mistakes_noted,
        "last_interaction": now_str,
    }


def forget_user(query: str) -> bool:
    """Wipe a user record from SQLite when requested ('forget me')."""
    init_db()
    clean_query = query.strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE LOWER(user_id) = LOWER(?) OR LOWER(name) = LOWER(?)",
            (clean_query, clean_query),
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        if deleted:
            logger.info(f"Deleted user memory record for {clean_query}")
        return deleted
