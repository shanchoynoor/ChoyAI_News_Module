# ChoyNewsBot - Northflank Deployment Guide

## 🚀 Quick Deployment Fix

If your Telegram bot is not responding on Northflank, follow these steps:

### 1. Update Northflank Service Configuration

**Start Command:**
```bash
./northflank-start.sh
```

**Environment Variables** (set these individually in Northflank):
```
TELEGRAM_BOT_TOKEN=7814094161:AAETeXoaaKKiEn-f0_eqAD0E1Ej7NzMcIXc
DEEPSEEK_API_KEY=sk-c4a39fed278944c08bac571dae3655d3
WEATHERAPI_KEY=3c10be7e7e344bdfa42130020250407
CALENDARIFIC_API_KEY=EGQWwZ8aIvQQ2E8uXkbbvuIJugXhmSjN
TWELVE_DATA_API_KEY=c99fa9536eee44acaee038a840a7f309
COINGECKO_API_KEY=CG-9C6w3YASi2NMRk8mWtxUgn4h
LOG_LEVEL=INFO
PYTHONPATH=/app
```

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

## 📋 Common Issues & Solutions

### Issue: Bot not responding
**Solution:** Ensure `TELEGRAM_BOT_TOKEN` is set correctly and bot has proper permissions

### Issue: Import errors
**Solution:** Check `PYTHONPATH` is set to `/app`

### Issue: Dependencies not installed
**Solution:** Use the build command above or ensure `requirements.txt` is accessible

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