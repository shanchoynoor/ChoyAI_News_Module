#!/usr/bin/env python3
"""
Database initialization script for ChoyNewsBot.
Run this to initialize all required SQLite databases.
"""

import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from data_modules.models import init_user_subscriptions_db, init_user_logs_db
from core.advanced_news_fetcher import init_news_history_db
from utils.logging import get_logger

logger = get_logger(__name__)

def initialize_databases():
    """Initialize all required databases."""
    print("🗄️  Initializing ChoyNewsBot databases...")
    
    try:
        # Initialize user subscriptions database
        print("📝 Creating user subscriptions database...")
        init_user_subscriptions_db()
        
        # Initialize user logs database
        print("📊 Creating user logs database...")
        init_user_logs_db()
        
        # Initialize news history database (for deduplication)
        print("📰 Creating news history database...")
        init_news_history_db()
        
        print("✅ All databases initialized successfully!")
        
        # Show database status
        print("\n📋 Database Status:")
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.db'):
                    file_path = os.path.join(data_dir, file)
                    size = os.path.getsize(file_path)
                    print(f"   📁 {file}: {size} bytes")
        
    except Exception as e:
        logger.error(f"Error initializing databases: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    initialize_databases()
