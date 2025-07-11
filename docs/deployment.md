# ChoyNewsBot Server Deployment Troubleshooting Guide

## Problem: "python3: No such file or directory" when running bin/choynews

This error typically occurs when the virtual environment is not properly set up or the Python executable is missing from the venv.

## Quick Diagnosis

Run the diagnostic script first:
```bash
chmod +x tools/server_diagnostic.sh
./tools/server_diagnostic.sh
```

## Common Solutions

### Solution 1: Fix Virtual Environment (Recommended)
```bash
# Run the automated fix script
chmod +x tools/deploy/setup_server_fix.sh
./tools/deploy/setup_server_fix.sh
```

### Solution 2: Manual Virtual Environment Recreation
```bash
# Remove corrupted venv
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .

# Test the bot
python3 -m choynews.core.bot
```

### Solution 3: Direct Python Execution
If the shebang script still fails, run directly:
```bash
# Activate venv first
source venv/bin/activate

# Run directly with python
python3 bin/choynews
```

### Solution 4: Alternative Module Execution
```bash
# Activate venv
source venv/bin/activate

# Run as module
python3 -m choynews.core.bot
```

## Environment Variables

Make sure your `.env` file contains:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
WEATHER_API_KEY=your_weather_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

## Troubleshooting Checklist

- [ ] Python3 is installed on the server
- [ ] Virtual environment is created and activated
- [ ] Dependencies are installed (`pip install -e .`)
- [ ] Environment variables are set
- [ ] choynews script has execute permissions
- [ ] Bot token is valid and active

## Testing Commands

```bash
# Test Python module import
python3 -c "import choynews; print('Success')"

# Test bot startup (should show help message or error details)
python3 -m choynews.core.bot --help

# Test with verbose logging
python3 -m choynews.core.bot --verbose
```

## Common Error Messages

| Error | Solution |
|-------|----------|
| `python3: No such file or directory` | Fix virtual environment or use Solution 2 |
| `ModuleNotFoundError: No module named 'choynews'` | Run `pip install -e .` |
| `ImportError: cannot import name` | Update dependencies |
| `telegram.error.InvalidToken` | Check TELEGRAM_BOT_TOKEN |
| `requests.exceptions.ConnectionError` | Check internet connection and API keys |

---

# Deployment Guide

This guide provides instructions for deploying the Choy News Telegram Bot to a production environment.

## Deployment Options

There are several ways to deploy the bot:

1. PM2 Process Manager (recommended)
2. Systemd Service
3. Docker Container

## PM2 Deployment (Recommended)

[PM2](https://pm2.keymetrics.io/) is a process manager for Node.js applications that can also manage Python processes.

### Prerequisites

- Node.js and npm installed
- PM2 installed globally: `npm install -g pm2`

### Deployment Steps

1. Clone the repository on your server:
   ```bash
   git clone https://github.com/username/choynews.git
   cd choynews
   ```

2. Set up the environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r config/requirements.txt
   pip install -e .
   ```

3. Configure environment variables:
   ```bash
   cp config/.env.example config/.env
   # Edit .env with your production settings
   nano config/.env
   ```

4. Start the bot using PM2:
   ```bash
   pm2 start tools/deploy/pm2_config.json
   ```

5. Monitor the processes:
   ```bash
   pm2 status
   pm2 logs choynews-bot
   pm2 logs choynews-auto
   ```

6. Configure PM2 to start on system boot:
   ```bash
   pm2 startup
   pm2 save
   ```

## Systemd Service Deployment

You can create a systemd service for more traditional Linux deployments.

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/choynews.service
   ```

2. Add the following content:
   ```ini
   [Unit]
   Description=Choy News Telegram Bot
   After=network.target

   [Service]
   User=yourusername
   WorkingDirectory=/path/to/choynews
   ExecStart=/path/to/choynews/.venv/bin/python /path/to/choynews/bin/choynews --service both
   Restart=on-failure
   RestartSec=5s
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable choynews
   sudo systemctl start choynews
   ```

4. Check the status:
   ```bash
   sudo systemctl status choynews
   journalctl -u choynews
   ```

## Docker Deployment

For containerized deployment, follow these steps:

1. Build the Docker image:
   ```bash
   docker build -t choynews .
   ```

2. Run the container:
   ```bash
   docker run -d --name choynews \
     --restart unless-stopped \
     -v /path/to/config/.env:/app/config/.env \
     -v /path/to/data:/app/data \
     -v /path/to/logs:/app/logs \
     choynews
   ```

3. Check container logs:
   ```bash
   docker logs -f choynews
   ```

## Server Requirements

Minimum server requirements:
- 1 CPU core
- 1GB RAM
- 10GB disk space
- Python 3.8 or higher
- Internet connectivity for API access

## Backup and Maintenance

1. Database backups:
   ```bash
   # Backup user subscription database
   cp data/db/user_subscriptions.db /path/to/backup/user_subscriptions.db.$(date +%Y%m%d)
   
   # Backup user logs database
   cp data/db/user_logs.db /path/to/backup/user_logs.db.$(date +%Y%m%d)
   ```

2. Log rotation:
   PM2 and systemd handle log rotation automatically. For manual setup, consider using logrotate.

## Monitoring

Monitor your bot's health using:
- PM2 monitoring dashboard
- Server monitoring tools (e.g., Prometheus, Grafana)
- Regular log checks
