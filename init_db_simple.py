#!/usr/bin/env python3
"""
Simple database initialization script for ChoyNewsBot.
"""

import os
import sqlite3
from pathlib import Path

# Create data directory if it doesn't exist
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

# Initialize news history database
news_db_path = data_dir / "news_history.db"

def init_news_history_db():
    """Initialize the news history database."""
    print(f"Initializing news history database at {news_db_path}")

    conn = sqlite3.connect(news_db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_hash TEXT UNIQUE,
            title TEXT,
            source TEXT,
            published_time TEXT,
            sent_time TEXT,
            category TEXT,
            url TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ News history database initialized")

def init_user_subscriptions_db():
    """Initialize user subscriptions database."""
    user_db_path = data_dir / "user_subscriptions.db"
    print(f"Initializing user subscriptions database at {user_db_path}")

    conn = sqlite3.connect(user_db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            subscribed INTEGER DEFAULT 1,
            timezone TEXT DEFAULT 'Asia/Dhaka',
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ User subscriptions database initialized")

def init_user_logs_db():
    """Initialize user logs database."""
    logs_db_path = data_dir / "user_logs.db"
    print(f"Initializing user logs database at {logs_db_path}")

    conn = sqlite3.connect(logs_db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            command TEXT,
            message TEXT,
            timestamp TEXT,
            success INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ User logs database initialized")

if __name__ == "__main__":
    print("🚀 Initializing ChoyNewsBot databases...")

    try:
        init_news_history_db()
        init_user_subscriptions_db()
        init_user_logs_db()
        print("\n✅ All databases initialized successfully!")
        print("You can now start the bot with: python bin/choynews.py")
    except Exception as e:
        print(f"❌ Error initializing databases: {e}")
        exit(1)