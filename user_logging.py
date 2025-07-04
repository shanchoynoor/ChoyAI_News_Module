import sqlite3
from datetime import datetime

DB_FILE = "user_logs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            interaction_time TEXT,
            message_type TEXT,
            location TEXT,
            last_interaction TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_user_interaction(user_id, username, first_name, last_name, message_type, location=None, last_interaction=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute('''
        INSERT INTO user_logs (user_id, username, first_name, last_name, interaction_time, message_type, location, last_interaction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, now, message_type, location, last_interaction))
    conn.commit()
    conn.close()
