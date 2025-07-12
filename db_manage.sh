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
    echo "  logs         Show recent user logs (last 10)"
    echo "  logs-today   Show today's user login logs"
    echo "  logs-7d      Show last 7 days user login logs"
    echo "  logs-30d     Show last 30 days user login logs"
    echo "  users        Show user subscriptions"
    echo "  news         Show news history"
    echo "  clean        Clean old data (interactive)"
    echo "  backup       Backup all databases"
    echo ""
}

init_databases() {
    echo "🗄️  Initializing databases..."
    python3 init_db_simple.py
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
        echo "📊 Recent User Interactions (Last 10):"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "SELECT user_id, username, first_name, interaction_time, message_type FROM user_logs ORDER BY interaction_time DESC LIMIT 10;" 2>/dev/null || echo "❌ No user_logs table found"
    else
        echo "❌ user_logs.db not found"
    fi
}

show_logs_today() {
    if [ -f "$DB_DIR/user_logs.db" ]; then
        today=$(date '+%Y-%m-%d')
        echo "📊 Today's User Login Logs ($today):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Count today's interactions
        count=$(sqlite3 "$DB_DIR/user_logs.db" "SELECT COUNT(*) FROM user_logs WHERE DATE(interaction_time) = '$today';" 2>/dev/null || echo "0")
        unique_users=$(sqlite3 "$DB_DIR/user_logs.db" "SELECT COUNT(DISTINCT user_id) FROM user_logs WHERE DATE(interaction_time) = '$today';" 2>/dev/null || echo "0")
        
        echo "📈 Summary: $count total interactions from $unique_users unique users today"
        echo ""
        
        # Show detailed logs
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            user_id,
            COALESCE(username, 'N/A') as username,
            COALESCE(first_name, 'Unknown') as name,
            interaction_time,
            message_type,
            COALESCE(location, 'N/A') as location
        FROM user_logs 
        WHERE DATE(interaction_time) = '$today'
        ORDER BY interaction_time DESC;" 2>/dev/null || echo "❌ No data found for today"
        
        echo ""
        echo "📊 Today's Activity Breakdown:"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            message_type,
            COUNT(*) as count,
            COUNT(DISTINCT user_id) as unique_users
        FROM user_logs 
        WHERE DATE(interaction_time) = '$today'
        GROUP BY message_type 
        ORDER BY count DESC;" 2>/dev/null || echo "❌ No activity data found"
    else
        echo "❌ user_logs.db not found"
    fi
}

show_logs_7days() {
    if [ -f "$DB_DIR/user_logs.db" ]; then
        seven_days_ago=$(date -d '7 days ago' '+%Y-%m-%d')
        echo "📊 Last 7 Days User Login Logs (since $seven_days_ago):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Count 7-day interactions
        count=$(sqlite3 "$DB_DIR/user_logs.db" "SELECT COUNT(*) FROM user_logs WHERE DATE(interaction_time) >= '$seven_days_ago';" 2>/dev/null || echo "0")
        unique_users=$(sqlite3 "$DB_DIR/user_logs.db" "SELECT COUNT(DISTINCT user_id) FROM user_logs WHERE DATE(interaction_time) >= '$seven_days_ago';" 2>/dev/null || echo "0")
        
        echo "📈 Summary: $count total interactions from $unique_users unique users in last 7 days"
        echo ""
        
        # Show daily breakdown
        echo "📅 Daily Activity Breakdown:"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            DATE(interaction_time) as date,
            COUNT(*) as interactions,
            COUNT(DISTINCT user_id) as unique_users,
            GROUP_CONCAT(DISTINCT message_type) as activity_types
        FROM user_logs 
        WHERE DATE(interaction_time) >= '$seven_days_ago'
        GROUP BY DATE(interaction_time) 
        ORDER BY date DESC;" 2>/dev/null || echo "❌ No data found for last 7 days"
        
        echo ""
        echo "👤 Most Active Users (Last 7 Days):"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            user_id,
            COALESCE(username, 'N/A') as username,
            COALESCE(first_name, 'Unknown') as name,
            COUNT(*) as total_interactions,
            MAX(interaction_time) as last_seen
        FROM user_logs 
        WHERE DATE(interaction_time) >= '$seven_days_ago'
        GROUP BY user_id 
        ORDER BY total_interactions DESC 
        LIMIT 10;" 2>/dev/null || echo "❌ No user data found"
        
        echo ""
        echo "📊 Command Usage (Last 7 Days):"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            message_type,
            COUNT(*) as usage_count,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM user_logs WHERE DATE(interaction_time) >= '$seven_days_ago'), 2) as percentage
        FROM user_logs 
        WHERE DATE(interaction_time) >= '$seven_days_ago'
        GROUP BY message_type 
        ORDER BY usage_count DESC;" 2>/dev/null || echo "❌ No command data found"
    else
        echo "❌ user_logs.db not found"
    fi
}

show_logs_30days() {
    if [ -f "$DB_DIR/user_logs.db" ]; then
        thirty_days_ago=$(date -d '30 days ago' '+%Y-%m-%d')
        echo "📊 Last 30 Days User Login Logs (since $thirty_days_ago):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Count 30-day interactions
        count=$(sqlite3 "$DB_DIR/user_logs.db" "SELECT COUNT(*) FROM user_logs WHERE DATE(interaction_time) >= '$thirty_days_ago';" 2>/dev/null || echo "0")
        unique_users=$(sqlite3 "$DB_DIR/user_logs.db" "SELECT COUNT(DISTINCT user_id) FROM user_logs WHERE DATE(interaction_time) >= '$thirty_days_ago';" 2>/dev/null || echo "0")
        avg_daily=$(sqlite3 "$DB_DIR/user_logs.db" "SELECT ROUND(COUNT(*) / 30.0, 1) FROM user_logs WHERE DATE(interaction_time) >= '$thirty_days_ago';" 2>/dev/null || echo "0")
        
        echo "📈 Summary: $count total interactions from $unique_users unique users in last 30 days"
        echo "📊 Average: $avg_daily interactions per day"
        echo ""
        
        # Show weekly breakdown
        echo "📅 Weekly Activity Breakdown:"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            'Week ' || ((julianday('now') - julianday(DATE(interaction_time))) / 7 + 1) as week,
            COUNT(*) as interactions,
            COUNT(DISTINCT user_id) as unique_users,
            MIN(DATE(interaction_time)) as week_start,
            MAX(DATE(interaction_time)) as week_end
        FROM user_logs 
        WHERE DATE(interaction_time) >= '$thirty_days_ago'
        GROUP BY (julianday('now') - julianday(DATE(interaction_time))) / 7
        ORDER BY week_start DESC;" 2>/dev/null || echo "❌ No weekly data found"
        
        echo ""
        echo "👤 Top 15 Most Active Users (Last 30 Days):"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            user_id,
            COALESCE(username, 'N/A') as username,
            COALESCE(first_name, 'Unknown') as name,
            COUNT(*) as total_interactions,
            ROUND(COUNT(*) / 30.0, 1) as avg_per_day,
            MAX(interaction_time) as last_seen,
            MIN(interaction_time) as first_seen
        FROM user_logs 
        WHERE DATE(interaction_time) >= '$thirty_days_ago'
        GROUP BY user_id 
        ORDER BY total_interactions DESC 
        LIMIT 15;" 2>/dev/null || echo "❌ No user data found"
        
        echo ""
        echo "📊 Command Usage Statistics (Last 30 Days):"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            message_type,
            COUNT(*) as usage_count,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM user_logs WHERE DATE(interaction_time) >= '$thirty_days_ago'), 2) as percentage,
            ROUND(COUNT(*) / 30.0, 1) as avg_per_day
        FROM user_logs 
        WHERE DATE(interaction_time) >= '$thirty_days_ago'
        GROUP BY message_type 
        ORDER BY usage_count DESC;" 2>/dev/null || echo "❌ No command data found"
        
        echo ""
        echo "🕐 Hourly Usage Pattern (Last 30 Days):"
        sqlite3 -header -column "$DB_DIR/user_logs.db" "
        SELECT 
            PRINTF('%02d:00', CAST(strftime('%H', interaction_time) AS INTEGER)) as hour,
            COUNT(*) as interactions,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM user_logs WHERE DATE(interaction_time) >= '$thirty_days_ago'), 1) as percentage
        FROM user_logs 
        WHERE DATE(interaction_time) >= '$thirty_days_ago'
        GROUP BY strftime('%H', interaction_time) 
        ORDER BY CAST(strftime('%H', interaction_time) AS INTEGER);" 2>/dev/null || echo "❌ No hourly data found"
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
    logs-today)
        show_logs_today
        ;;
    logs-7d)
        show_logs_7days
        ;;
    logs-30d)
        show_logs_30days
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
