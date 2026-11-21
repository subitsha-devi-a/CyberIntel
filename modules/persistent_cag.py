
import sqlite3
import hashlib
from pathlib import Path


DB_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "cyberintel_memory.db"
)


def get_connection():
    return sqlite3.connect(DB_FILE)


def initialize_memory():

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS context_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_hash TEXT UNIQUE,
                question TEXT,
                context TEXT,
                answer TEXT
            )
        """)


def make_hash(question, context):

    content = question.strip().lower() + "|" + context.strip().lower()

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def get_answer(question, context):

    initialize_memory()
    key = make_hash(question, context)

    with get_connection() as connection:
        result = connection.execute(
            "SELECT answer FROM context_memory WHERE question_hash = ?",
            (key,)
        ).fetchone()

    return result[0] if result else None


def save_answer(question, context, answer):

    initialize_memory()
    key = make_hash(question, context)

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO context_memory
            (question_hash, question, context, answer)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(question_hash)
            DO UPDATE SET answer = excluded.answer
        """, (key, question, context, answer))


def memory_count():

    initialize_memory()

    with get_connection() as connection:
        result = connection.execute(
            "SELECT COUNT(*) FROM context_memory"
        ).fetchone()

    return result[0]


def clear_memory():

    initialize_memory()

    with get_connection() as connection:
        connection.execute("DELETE FROM context_memory")
