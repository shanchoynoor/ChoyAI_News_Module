# Choy News Telegram Bot 📰

A Telegram bot that delivers curated, 6-hourly news digests at 8 AM, 1 PM, 7 PM, and 11 PM (local time). It fetches the latest news across categories—Local (Bangladesh), Global, Tech, Sports, and Crypto—along with crypto market data, ensuring fresh updates without repetition.

## Features at a Glance

- Scheduled news delivery at convenient times
- Multi-category news from reliable sources
- Cryptocurrency market insights and price tracking
- User-specific timezone and subscription management
- Smart caching for reliability during API outages

## Quick Start

```bash
# Clone repository
git clone https://github.com/username/choynews.git
cd choynews

# Setup environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r config/requirements.txt
pip install -e .

# Configure and run
cp config/.env.example config/.env  # Edit with your API keys
choynews --service both
```

For detailed documentation, installation instructions, and usage guide, please refer to the `docs` directory.

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/username/choynews.git
cd choynews
```

2. Set up environment:
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r config/requirements.txt

# Install package in development mode
pip install -e .
```

3. Configure environment variables:
```bash
cp config/.env.example config/.env
# Edit .env with your API keys and configuration
```

## 🏃 Running the Bot

```bash
# Run both the bot and auto news services
choynews --service both

# Run only the interactive bot
choynews --service bot

# Run only the auto news service
choynews --service auto
```

## 🔄 Deployment with PM2

For production deployment, PM2 process manager is recommended:

```bash
# Install PM2
npm install -g pm2

# Start the bot using the config file
pm2 start tools/deploy/pm2_config.json

# Monitor and manage
pm2 status
pm2 logs choynews-bot
pm2 logs choynews-auto

# Configure startup
pm2 startup
pm2 save
```

## 💬 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot and get a welcome message |
| `/news` | Get the full daily news digest |
| `/weather` | Get Dhaka weather |
| `/cryptostats` | Get AI summary of crypto market |
| `/coin` | Get price and 24h change for a coin (e.g. /btc, /eth) |
| `/coinstats` | Get price, 24h change, and AI summary (e.g. /btcstats) |
| `/timezone <zone>` | Set your timezone for news digest times |
| `/subscribe` | Get news digests at scheduled times in your timezone |
| `/unsubscribe` | Stop receiving automatic news digests |
| `/status` | Check your subscription status and timezone |
| `/support` | Contact the developer for support |
| `/help` | Show the help message |

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/
```

## 📅 Scheduling

For alternative scheduling methods, use cron or Task Scheduler:

```bash
# Example cron job (8 AM, 1 PM, 7 PM, 12 AM)
0 8,13,19,0 * * * /path/to/.venv/bin/python /path/to/choynews/bin/choynews
```

## 📰 Content Details

Each news digest contains:

| Category | Sources |
|----------|---------|
| **Local News** | Prothom Alo, The Daily Star |
| **Global News** | BBC, Reuters, AP |
| **Tech News** | TechCrunch, The Verge, Wired |
| **Sports News** | ESPN, Sky Sports |
| **Crypto News** | Cointelegraph, Coindesk |
| **Crypto Market** | Market cap, volume, Fear/Greed Index |

All content is formatted in Markdown with clickable links and publication timestamps.

## 🏗️ Project Structure

```
choynews/                  # Main package
├── api/                   # API integrations
├── core/                  # Core business logic
├── data/                  # Data models and persistence
├── services/              # Higher-level services
└── utils/                 # Utility functions

bin/                       # Executable scripts
config/                    # Configuration files
data/                      # Data storage
docs/                      # Documentation
logs/                      # Log files
tests/                     # Tests
tools/                     # Development and deployment tools
```

## 📄 License

[MIT](LICENSE)

## 👤 Author

Shanchoy Noor
