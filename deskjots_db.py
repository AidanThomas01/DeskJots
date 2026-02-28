"""
db.py - SQLite database layer for DeskJots
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.expanduser("~"), ".deskjots.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL DEFAULT 'New Note',
                content     TEXT    NOT NULL DEFAULT '',
                colour      TEXT    NOT NULL DEFAULT '#f5c842',
                font_size   INTEGER NOT NULL DEFAULT 12,
                pos_x       INTEGER NOT NULL DEFAULT 100,
                pos_y       INTEGER NOT NULL DEFAULT 100,
                width       INTEGER NOT NULL DEFAULT 280,
                height      INTEGER NOT NULL DEFAULT 320,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def create_note(title="New Note", colour="#f5c842", font_size=12):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO notes (title, colour, font_size) VALUES (?, ?, ?)",
            (title, colour, font_size)
        )
        conn.commit()
        return cur.lastrowid


def get_all_notes():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(
            "SELECT * FROM notes ORDER BY updated_at DESC"
        ).fetchall()]


def get_note(note_id):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
        return dict(row) if row else None


def update_note(note_id, **kwargs):
    allowed = {"title", "content", "colour", "font_size",
               "pos_x", "pos_y", "width", "height"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_parts  = [f"{k} = ?" for k in fields]
    set_parts.append("updated_at = datetime('now')")
    values = list(fields.values())
    values.append(note_id)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE notes SET {', '.join(set_parts)} WHERE id=?", values
        )
        conn.commit()


def delete_note(note_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.commit()
