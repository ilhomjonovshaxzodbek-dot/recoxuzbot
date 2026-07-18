import sqlite3
import time
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            created_at INTEGER,
            last_message_at INTEGER,
            daily_active_seconds INTEGER DEFAULT 0,
            day_marker TEXT,
            blocked_until INTEGER,
            is_banned INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            content TEXT,
            status TEXT DEFAULT 'pending', -- pending / approved / rejected
            created_at INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER,
            to_id INTEGER,
            status TEXT DEFAULT 'pending', -- pending / accepted / declined
            created_at INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_chats (
            user_id INTEGER PRIMARY KEY,
            partner_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('paused', '0')")
    cur.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_info', '')")

    conn.commit()
    conn.close()


# ---------- USERS ----------

def add_user_if_not_exists(chat_id: int, first_name: str, username: str):
    conn = get_conn()
    cur = conn.cursor()
    now = int(time.time())
    cur.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (chat_id, first_name, username, created_at, last_message_at, day_marker) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, first_name, username, now, now, time.strftime("%Y-%m-%d")),
        )
        conn.commit()
    conn.close()


def get_user(chat_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE is_banned = 0")
    rows = cur.fetchall()
    conn.close()
    return rows


def touch_activity(chat_id: int, seconds_delta: int = 60):
    """Foydalanuvchi xabar yozganda chaqiriladi - kunlik faollik hisoblagichini yangilaydi."""
    conn = get_conn()
    cur = conn.cursor()
    today = time.strftime("%Y-%m-%d")
    now = int(time.time())
    cur.execute("SELECT daily_active_seconds, day_marker FROM users WHERE chat_id = ?", (chat_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return
    if row["day_marker"] != today:
        # yangi kun boshlandi - hisoblagichni asrash
        cur.execute(
            "UPDATE users SET daily_active_seconds = ?, day_marker = ?, last_message_at = ? WHERE chat_id = ?",
            (seconds_delta, today, now, chat_id),
        )
    else:
        cur.execute(
            "UPDATE users SET daily_active_seconds = daily_active_seconds + ?, last_message_at = ? WHERE chat_id = ?",
            (seconds_delta, now, chat_id),
        )
    conn.commit()
    conn.close()


def block_user(chat_id: int, hours: float):
    conn = get_conn()
    cur = conn.cursor()
    until = int(time.time() + hours * 3600)
    cur.execute("UPDATE users SET blocked_until = ? WHERE chat_id = ?", (until, chat_id))
    conn.commit()
    conn.close()
    return until


def unblock_user(chat_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET blocked_until = NULL WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def is_blocked(chat_id: int):
    user = get_user(chat_id)
    if not user or not user["blocked_until"]:
        return False
    return user["blocked_until"] > int(time.time())


def ban_user(chat_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = 1 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def is_banned(chat_id: int):
    user = get_user(chat_id)
    return bool(user and user["is_banned"])


# ---------- PROJECTS ----------

def add_project(owner_id: int, content: str, auto_approve: bool = False):
    conn = get_conn()
    cur = conn.cursor()
    now = int(time.time())
    status = "approved" if auto_approve else "pending"
    cur.execute(
        "INSERT INTO projects (owner_id, content, status, created_at) VALUES (?, ?, ?, ?)",
        (owner_id, content, status, now),
    )
    conn.commit()
    project_id = cur.lastrowid
    conn.close()
    return project_id


def get_project(project_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    conn.close()
    return row


def set_project_status(project_id: int, status: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
    conn.commit()
    conn.close()


def get_approved_projects():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE status = 'approved' ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------- CHAT REQUESTS (foydalanuvchilar o'zaro suhbati) ----------

def create_chat_request(from_id: int, to_id: int):
    conn = get_conn()
    cur = conn.cursor()
    now = int(time.time())
    cur.execute(
        "INSERT INTO chat_requests (from_id, to_id, status, created_at) VALUES (?, ?, 'pending', ?)",
        (from_id, to_id, now),
    )
    conn.commit()
    req_id = cur.lastrowid
    conn.close()
    return req_id


def get_chat_request(req_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM chat_requests WHERE id = ?", (req_id,))
    row = cur.fetchone()
    conn.close()
    return row


def set_chat_request_status(req_id: int, status: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE chat_requests SET status = ? WHERE id = ?", (status, req_id))
    conn.commit()
    conn.close()


def start_active_chat(user_a: int, user_b: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (user_a, user_b))
    cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (user_b, user_a))
    conn.commit()
    conn.close()


def get_chat_partner(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row["partner_id"] if row else None


def end_active_chat(user_id: int):
    partner_id = get_chat_partner(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM active_chats WHERE user_id = ?", (user_id,))
    if partner_id:
        cur.execute("DELETE FROM active_chats WHERE user_id = ?", (partner_id,))
    conn.commit()
    conn.close()
    return partner_id


# ---------- BOT SETTINGS ----------

def is_bot_paused():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM bot_settings WHERE key = 'paused'")
    row = cur.fetchone()
    conn.close()
    return row and row["value"] == "1"


def set_bot_paused(paused: bool):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE bot_settings SET value = ? WHERE key = 'paused'", ("1" if paused else "0",))
    conn.commit()
    conn.close()


def get_bot_info():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM bot_settings WHERE key = 'bot_info'")
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else ""


def set_bot_info(text: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE bot_settings SET value = ? WHERE key = 'bot_info'", (text,))
    conn.commit()
    conn.close()
