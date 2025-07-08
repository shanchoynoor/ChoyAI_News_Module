#!/bin/bash
# Diagnostic script for News Digest Bot

echo "===== SYSTEM INFORMATION ====="
echo "Date and time: $(date)"
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version)"
echo "Node version: $(node --version 2>/dev/null || echo 'Not installed')"
echo "NPM version: $(npm --version 2>/dev/null || echo 'Not installed')"
echo "PM2 version: $(pm2 --version 2>/dev/null || echo 'Not installed')"

echo -e "\n===== ENVIRONMENT VARIABLES ====="
# Check for critical environment variables
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "WARNING: TELEGRAM_TOKEN is not set!"
else
    echo "TELEGRAM_TOKEN: [Set]"
fi

if [ -z "$DEEPSEEK_API" ]; then
    echo "WARNING: DEEPSEEK_API is not set!"
else
    echo "DEEPSEEK_API: [Set]"
fi

if [ -z "$AUTO_NEWS_CHAT_ID" ]; then
    echo "WARNING: AUTO_NEWS_CHAT_ID is not set!"
else
    echo "AUTO_NEWS_CHAT_ID: [Set]"
fi

echo -e "\n===== FILE PERMISSIONS ====="
ls -la

echo -e "\n===== DATABASE STATUS ====="
echo "User Timezones DB:"
ls -la user_timezones.db
echo "User Subscriptions DB:"
ls -la user_subscriptions.db
echo "User Logs DB:"
ls -la user_logs.db

echo -e "\n===== PM2 STATUS ====="
pm2 status

echo -e "\n===== LOG FILES ====="
if [ -d "logs" ]; then
    echo "Log directory exists. Contents:"
    ls -la logs/
else
    echo "Log directory does not exist!"
fi

echo "auto_news.log:"
if [ -f "auto_news.log" ]; then
    echo "Last 10 lines:"
    tail -n 10 auto_news.log
else
    echo "File does not exist!"
fi

echo -e "\n===== TESTING PYTHON IMPORTS ====="
python3 -c "
try:
    import dotenv
    import pytz
    import requests
    import sqlite3
    print('All basic imports successful')
except ImportError as e:
    print(f'Import error: {e}')
"

echo -e "\n===== TESTING NEWS MODULE ====="
python3 -c "
try:
    from news import get_help_text
    print('Successfully imported from news module')
    print(get_help_text())
except Exception as e:
    print(f'Error importing from news module: {e}')
"

echo -e "\n===== TESTING AUTO_NEWS MODULE ====="
python3 -c "
try:
    from auto_news import get_bd_now, should_send_news
    now = get_bd_now()
    print(f'Current BD time: {now}')
    print(f'Should send news: {should_send_news(now)}')
    print('Successfully tested auto_news module')
except Exception as e:
    print(f'Error testing auto_news module: {e}')
"

echo -e "\n===== DIAGNOSTICS COMPLETE ====="
echo "If you're experiencing issues, check the logs directory and fix any warnings above."
