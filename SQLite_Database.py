import sqlite3
from datetime import datetime

DB_FILE = "processed_emails.db"

def init_db():
    """Create the database and table if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_threads (
            thread_id TEXT PRIMARY KEY,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_thread_processed(thread_id: str) -> bool:
    """Check if a thread ID has already been processed."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_threads WHERE thread_id = ?", (thread_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_thread_processed(thread_id: str):
    """Mark a thread ID as processed."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO processed_threads (thread_id) VALUES (?)", 
        (thread_id,)
    )
    conn.commit()
    conn.close()

def clear_all_processed():  # Optional helper
    """Clear all stored thread IDs (use cautiously)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processed_threads")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()