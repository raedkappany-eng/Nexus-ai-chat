import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "API_CHAT.DB")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                target_bot TEXT DEFAULT 'all',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

    conn.commit()
    conn.close()


def create_user(username: str, hashed_password: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(username, hashed_password) VALUES(?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None


def get_user_by_username(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, hashed_password FROM users WHERE username=?",
        (username,)
    )
    user = cur.fetchone()
    conn.close()
    if user:
        return {"id": user["id"], "username": user["username"], "hashed_password": user["hashed_password"]}
    return None


def save_message(user_id: int, sender: str, content: str, target_bot: str = 'all'):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages(user_id, sender, content, target_bot) VALUES (?, ?, ?, ?)",
            (user_id, sender, content, target_bot)
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_messages(limit=25):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT sender, content FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    rows.reverse()
    formatted = [f"{r[0]}:{r[1]}" for r in rows]
    return "\n".join(formatted)


def get_all_messages_row(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, sender, content, target_bot, timestamp FROM messages WHERE user_id=? ORDER BY id ASC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]