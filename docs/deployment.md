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
