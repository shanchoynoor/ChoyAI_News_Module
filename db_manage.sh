#!/bin/bash

# ChoyNewsBot Database Management Script
# Usage: ./db_manage.sh [command]

DB_DIR="data"

show_help() {
    echo "ChoyNewsBot Database Management"
    echo "Usage: ./db_manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  init         Initialize all databases"
    echo "  status       Show database status"
    echo "  logs         Show user logs"
    echo "  users        Show user subscriptions"
    echo "  news         Show news history"
    echo "  clean        Clean old data (interactive)"
    echo "  backup       Backup all databases"
    echo ""
}

init_databases() {
    echo "🗄️  Initializing databases..."
    python3 init_db.py
}

show_status() {
    echo "📋 Database Status:"
    if [ -d "$DB_DIR" ]; then
        for db in "$DB_DIR"/*.db; do
            if [ -f "$db" ]; then
                filename=$(basename "$db")
                size=$(du -h "$db" | cut -f1)
                echo "   📁 $filename: $size"
                
                # Check table count
                tables=$(sqlite3 "$db" ".tables" 2>/dev/null | wc -w)
                echo "      Tables: $tables"
            fi
        done
    else
        echo "❌ Data directory not found"
    fi
}

show_logs() {
    if [ -f "$DB_DIR/user_logs.db" ]; then
        echo "📊 Recent User Interactions:"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "SELECT * FROM user_logs ORDER BY interaction_time DESC LIMIT 10;" 2>/dev/null || echo "❌ No user_logs table found"
    else
        echo "❌ user_logs.db not found"
    fi
}

show_users() {
    if [ -f "$DB_DIR/user_subscriptions.db" ]; then
        echo "👥 User Subscriptions:"
        sqlite3 -header -column "$DB_DIR/user_subscriptions.db" "SELECT user_id, username, first_name, preferred_time, timezone, is_active FROM subscriptions;" 2>/dev/null || echo "❌ No subscriptions table found"
    else
        echo "❌ user_subscriptions.db not found"
    fi
}

show_news() {
    if [ -f "$DB_DIR/news_history.db" ]; then
        echo "📰 Recent News History:"
        sqlite3 -header -column "$DB_DIR/news_history.db" "SELECT title, source, category, sent_time FROM news_history ORDER BY sent_time DESC LIMIT 5;" 2>/dev/null || echo "❌ No news_history table found"
    else
        echo "❌ news_history.db not found"
    fi
}

backup_databases() {
    backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    echo "💾 Creating backup in $backup_dir..."
    mkdir -p "$backup_dir"
    
    if [ -d "$DB_DIR" ]; then
        cp -r "$DB_DIR"/*.db "$backup_dir/" 2>/dev/null
        echo "✅ Backup completed: $backup_dir"
    else
        echo "❌ No databases to backup"
    fi
}

clean_data() {
    echo "🧹 Database Cleanup Options:"
    echo "1. Clean old news history (7+ days)"
    echo "2. Clean old user logs (30+ days)"
    echo "3. Cancel"
    read -p "Choose option [1-3]: " choice
    
    case $choice in
        1)
            if [ -f "$DB_DIR/news_history.db" ]; then
                cutoff=$(date -d '7 days ago' '+%Y-%m-%d')
                sqlite3 "$DB_DIR/news_history.db" "DELETE FROM news_history WHERE sent_time < '$cutoff';"
                echo "✅ Cleaned old news history"
            fi
            ;;
        2)
            if [ -f "$DB_DIR/user_logs.db" ]; then
                cutoff=$(date -d '30 days ago' '+%Y-%m-%d')
                sqlite3 "$DB_DIR/user_logs.db" "DELETE FROM user_logs WHERE interaction_time < '$cutoff';"
                echo "✅ Cleaned old user logs"
            fi
            ;;
        *)
            echo "❌ Cancelled"
            ;;
    esac
}

# Main script
case "${1:-help}" in
    init)
        init_databases
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    users)
        show_users
        ;;
    news)
        show_news
        ;;
    clean)
        clean_data
        ;;
    backup)
        backup_databases
        ;;
    help|*)
        show_help
        ;;
esac
