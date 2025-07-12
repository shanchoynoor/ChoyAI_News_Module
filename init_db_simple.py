#!/usr/bin/env python3
"""
Simple database initialization script that doesn't require dependencies.
Creates basic SQLite database tables without imports.
"""

import sqlite3
import os

def create_user_subscriptions_db():
    """Create user subscriptions database."""
    db_path = "data/user_subscriptions.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            preferred_time TEXT,
            timezone TEXT,
            is_active INTEGER DEFAULT 1,
            crypto_alerts INTEGER DEFAULT 1,
            market_updates INTEGER DEFAULT 1,
            weather_info INTEGER DEFAULT 1,
            world_news INTEGER DEFAULT 1,
            tech_news INTEGER DEFAULT 1,
            created_at TEXT,
            last_updated TEXT,
            last_sent TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ User subscriptions database created")

def create_user_logs_db():
    """Create user logs database."""
    db_path = "data/user_logs.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
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
    print("✅ User logs database created")

def create_news_history_db():
    """Create news history database for deduplication."""
    db_path = "data/news_history.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
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
    print("✅ News history database created")

def main():
    print("🗄️  Initializing ChoyNewsBot databases (simple version)...")
    
    try:
        create_user_subscriptions_db()
        create_user_logs_db()
        create_news_history_db()
        
        print("\n✅ All databases initialized successfully!")
        
        # Show created databases
        if os.path.exists("data"):
            print("\n📋 Created databases:")
            for file in sorted(os.listdir("data")):
                if file.endswith('.db'):
                    size = os.path.getsize(os.path.join("data", file))
                    print(f"   📁 {file}: {size} bytes")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
