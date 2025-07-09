# User Guide

This guide explains how to use the Choy News Telegram Bot.

## Getting Started

1. Start a chat with the bot on Telegram
2. Send the `/start` command to initialize the bot
3. Follow the instructions to set up your preferences

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize the bot and get a welcome message | `/start` |
| `/news` | Get the full daily news digest | `/news` |
| `/weather` | Get Dhaka weather | `/weather` |
| `/cryptostats` | Get AI summary of crypto market | `/cryptostats` |
| `/coin` | Get price and 24h change for a coin | `/btc`, `/eth` |
| `/coinstats` | Get price, 24h change, and AI summary | `/btcstats` |
| `/timezone <zone>` | Set your timezone for news digest times | `/timezone Asia/Dhaka` |
| `/subscribe` | Get news digests at scheduled times | `/subscribe` |
| `/unsubscribe` | Stop receiving automatic news digests | `/unsubscribe` |
| `/status` | Check your subscription status and timezone | `/status` |
| `/support` | Contact the developer for support | `/support` |
| `/help` | Show the help message | `/help` |

## News Digest Schedule

The bot sends news digests at the following times in your local timezone:
- 8:00 AM - Morning digest
- 1:00 PM - Midday digest
- 7:00 PM - Evening digest
- 11:00 PM - Night digest

## News Categories

Each digest includes news from the following categories:

- **Local News**: Top stories from Bangladesh (Prothom Alo, The Daily Star)
- **Global News**: International headlines (BBC, Reuters)
- **Tech News**: Technology updates (TechCrunch, The Verge)
- **Sports News**: Sports highlights (ESPN, Sky Sports)
- **Crypto News**: Cryptocurrency updates (Cointelegraph, Coindesk)
- **Crypto Market**: Market overview with price movements

## Setting Your Timezone

To receive news at the correct local time, set your timezone:

```
/timezone Asia/Dhaka
```

Replace `Asia/Dhaka` with your timezone. For a list of valid timezones, visit [this link](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

## Subscription Management

- To start receiving scheduled digests: `/subscribe`
- To stop receiving scheduled digests: `/unsubscribe`
- To check your current subscription status: `/status`
