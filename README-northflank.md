# ChoyNewsBot - Northflank Deployment Guide

## 🚀 Quick Deployment Fix

If your Telegram bot is not responding on Northflank, follow these steps:

### 1. Update Northflank Service Configuration

**Start Command:**
```bash
./northflank-start.sh
```

**Environment Variables** (set these individually in Northflank):


### 2. Alternative Start Command (if script doesn't work):
```bash
python3 bin/choynews.py --service bot
```

### 3. Build Command (if needed):
```bash
pip3 install -r config/requirements.txt
```

### 4. Working Directory:
Set to `/app` (project root)

## 🔍 Debugging Steps

1. **Check Northflank Logs** for startup errors
2. **Verify Environment Variables** are properly set
3. **Test Telegram API** connectivity
4. **Check Dependencies** are installed
5. **Check File Permissions** - ensure `data/` directory is writable
6. **Database Issues** - SQLite database needs write permissions

## 📋 Common Issues & Solutions

### Issue: Bot not responding
**Solution:** Ensure `TELEGRAM_BOT_TOKEN` is set correctly and bot has proper permissions

### Issue: Import errors
**Solution:** Check `PYTHONPATH` is set to `/app`

### Issue: Dependencies not installed
**Solution:** Use the build command above or ensure `requirements.txt` is accessible

### Issue: Permission denied: '/app/core/../../data'
**Solution:** The `data/` directory needs write permissions. The startup script now handles this.

### Issue: SQLite database creation fails
**Solution:** Ensure the application has write permissions to create `data/news_history.db`

### Issue: Working directory issues
**Solution:** Set working directory to `/app` in Northflank service settings

## ✅ Verification

After deployment, check logs for:
- "Environment validation passed!"
- "Telegram API test successful!"
- "Starting Choy News Bot interactive service..."

## 🆘 Support

If issues persist:
1. Check Northflank service logs
2. Verify all environment variables are set
3. Test locally with `python3 bin/choynews.py --service bot --debug`
4. Contact: @shanchoynoor