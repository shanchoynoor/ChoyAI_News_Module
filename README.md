# 🤖 ChoyNewsBot - AI-Powered Breaking News & Crypto Intelligence

**The most advanced Telegram news bot with real-time AI analysis, smart deduplication, and zero-repeat news delivery across multiple daily digests.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![AI Powered](https://img.shields.io/badge/AI-DeepSeek-green.svg)](https://www.deepseek.com/)
[![Real-time](https://img.shields.io/badge/News-Real--time-red.svg)](https://github.com/shanchoy/choynews)

## 🚀 What Makes ChoyNewsBot Special?

- **🧠 AI-Powered Analysis**: DeepSeek AI provides intelligent market insights and crypto predictions
- **🔄 Zero Duplicate News**: Advanced SQLite deduplication ensures no repeated news across 4 daily time slots
- **⚡ Real-time Breaking News**: Fetches latest news from 50+ premium sources every minute
- **💰 Live Crypto Intelligence**: Real-time prices with AI technical analysis and trading signals
- **🌍 Multi-language Support**: Local Bangladesh news + Global coverage in English
- **⏰ Smart Scheduling**: 8am, 1pm, 7pm, 11pm delivery based on user timezone
- **🎯 5-Item Guarantee**: Each category always shows exactly 5 news items with smart fallbacks

## 🌟 Core Features

### 📰 **Advanced News System**
- **Real-time RSS aggregation** from 50+ premium sources (BBC, Reuters, CNN, TechCrunch, etc.)
- **Breaking news priority** - Only recent, important news (last 48 hours)
- **Smart deduplication** - SQLite tracking prevents repeated news across time slots
- **Rich formatting** - Clickable links, timestamps, and emoji indicators
- **Fallback intelligence** - Always 5 items per category with relevant placeholder content

### 🤖 **AI-Powered Crypto Analysis**
- **DeepSeek AI integration** for market sentiment and technical analysis
- **Real-time price data** from CoinGecko API with 1-minute updates
- **Technical indicators** - Support/Resistance, RSI, Moving averages
- **Trading signals** - BUY/HOLD/SELL recommendations with confidence scores
- **Market overview** - Fear & Greed Index, market cap trends, volume analysis

### 🌤️ **Live Data Integration**
- **Weather API** - Real-time Dhaka weather with AQI and UV index
- **Holiday Calendar** - Bangladesh public holidays from Calendarific
- **Market Data** - Live crypto prices, forex rates, and economic indicators
- **Time Intelligence** - User timezone support with accurate local scheduling

### 🎯 **Smart User Experience**
- **Individual coin commands** - `/btc`, `/eth`, `/pepe`, `/shib` with instant AI analysis for all 17,500+ CoinGecko coins
- **Interactive help system** - Context-aware assistance and tutorials
- **Subscription management** - Easy opt-in/out with timezone preferences
- **Error resilience** - Graceful handling of API failures with cached data

## 💻 **Sample Output**

```
� DAILY NEWS DIGEST
Wednesday, July 10, 2025 • 8:00 AM (UTC+6)
🎉 Today: Ashari Purnima (Public Holiday)
━━━━━━━━━━━━━━━━━━━━━

*☀️ DHAKA WEATHER:*
🌡️ Temperature: 28.5°C - 32.1°C
�️ Condition: Partly cloudy with light rain possible  
💨 Wind: 12 km/h SE
💧 Humidity: 78%
🫧 Air Quality: Moderate (AQI 65)
🔆 UV Index: High (7/11)

*🇧🇩 LOCAL NEWS:*
1. [Government announces salary increase for civil servants](link) - Prothom Alo (2hr ago)
2. [New metro line inaugurated in Dhaka](link) - The Daily Star (3hr ago)  
3. [Education budget allocation increased significantly](link) - Jugantor (4hr ago)
4. [Digital banking services expand nationwide](link) - Financial Express (5hr ago)
5. [Health insurance coverage extended to rural areas](link) - New Age (6hr ago)

*🌍 GLOBAL NEWS:*
1. [Global climate summit reaches breakthrough accord](link) - BBC (1hr ago)
2. [Tech giants announce AI safety alliance](link) - Reuters (2hr ago)
3. [Economic recovery shows strong momentum worldwide](link) - CNN (3hr ago)
4. [Space mission discovers potentially habitable exoplanets](link) - Al Jazeera (4hr ago)
5. [International trade agreements finalized after months](link) - Guardian (5hr ago)

*🚀 TECH NEWS:*
1. [Apple unveils revolutionary AR glasses prototype](link) - TechCrunch (1hr ago)
2. [Google's quantum computer achieves new milestone](link) - The Verge (2hr ago)
3. [Tesla announces self-driving car breakthrough](link) - Ars Technica (3hr ago)
4. [Microsoft integrates advanced AI into Office suite](link) - Wired (4hr ago)
5. [Meta launches new VR social platform](link) - Engadget (5hr ago)

*🏆 SPORTS NEWS:*
1. [Bangladesh cricket team wins series against Australia](link) - ESPN Cricinfo (2hr ago)
2. [Dhaka Dynamites sign international star player](link) - Cricbuzz (3hr ago)
3. [Football World Cup qualifiers: Bangladesh advances](link) - Goal.com (4hr ago)
4. [Olympic preparations underway for Paris 2028](link) - Olympic.org (5hr ago)
5. [Tennis championship final set for this weekend](link) - ATP Tour (6hr ago)

*🪙 FINANCE & CRYPTO NEWS:*
1. [Bitcoin reaches new all-time high above $110,000](link) - CoinDesk (1hr ago)
2. [Ethereum network upgrade improves transaction speed](link) - Decrypt (2hr ago)
3. [Central banks explore digital currency adoption](link) - Bloomberg (3hr ago)
4. [DeFi protocols see record trading volume surge](link) - The Block (4hr ago)
5. [Cryptocurrency regulation framework finalized](link) - CoinTelegraph (5hr ago)

*💰 CRYPTOCURRENCY MARKET:*
📊 Market Cap: $3.48T ↗️ (+2.42%)
💹 Volume (24h): $156.8B ↗️ (+8.1%)
😨 Fear & Greed Index: 72/100 (Greed) 🟢 BUY

📈 Crypto Top 5 Gainers:
• SOL: +12.4% ↗️ • ADA: +8.9% ↗️ • DOT: +7.2% ↗️
• MATIC: +6.8% ↗️ • AVAX: +5.3% ↗️

📉 Top 5 Losers:
• DOGE: -3.1% ↘️ • LTC: -2.8% ↘️ • BCH: -2.4% ↘️
• XRP: -1.9% ↘️ • ADA: -1.2% ↘️

🤖 AI Market Analysis:
Crypto markets demonstrate robust bullish momentum with substantial institutional inflows propelling BTC beyond the $110k resistance threshold. Altcoins are significantly outperforming with the DeFi sector spearheading gains across the board. Technical indicators suggest a continuation pattern forming with strong volume confirmation.

📈 24h Prediction: 🟢 BULLISH with 78% confidence
🎯 Key Levels: BTC Support $108k | Resistance $115k

━━━━━━━━━━━━━━━
🤖 Developed by [Shanchoy Noor](https://github.com/shanchoynoor)
```

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/shanchoy/choynews-bot.git
cd choynews-bot
pip install -r config/requirements.txt

# 2. Configure API keys in .env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DEEPSEEK_API=your_deepseek_api_key
WEATHERAPI_KEY=your_weather_api_key
CALENDARIFIC_API_KEY=your_calendar_api_key

# 3. Launch the bot
./bin/choynews
```

**🎉 Ready! Your AI news bot is now live with:**
- ✅ Real-time breaking news from 50+ sources
- ✅ AI-powered crypto analysis with trading signals  
- ✅ Smart deduplication across 4 daily time slots
- ✅ Live weather and market data integration

## 🤖 Bot Commands & Features

### 📱 **Essential Commands**
| Command | Description | AI Feature |
|---------|-------------|------------|
| `/start` | Welcome & bot introduction | - |
| `/news` | Full digest with 5 categories × 5 items | ✅ AI market analysis |
| `/help` | Interactive help system | ✅ Context-aware assistance |

### 💰 **Crypto Intelligence**
| Command | Description | AI Feature |
|---------|-------------|------------|
| `/cryptostats` | Complete market overview | ✅ DeepSeek sentiment analysis |
| `/btc` `/eth` `/pepe` `/shib` | Individual coin prices | ✅ Real-time price + basic info |
| `/btcstats` `/ethstats` `/pepestats` | Detailed coin analysis | ✅ Technical analysis + trading signals |
| `/coin <symbol>` | Generic coin lookup | ✅ Support for **17,500+ CoinGecko coins** |

### 🌤️ **Live Data**
| Command | Description | Data Source |
|---------|-------------|-------------|
| `/weather` | Dhaka weather + AQI | WeatherAPI (real-time) |
| `/status` | Bot status & user info | System health check |

### ⚙️ **User Management**
| Command | Description | Smart Feature |
|---------|-------------|---------------|
| `/subscribe` | Auto news delivery (4× daily) | ✅ Timezone-aware scheduling |
| `/unsubscribe` | Stop auto delivery | ✅ Instant opt-out |
| `/timezone <zone>` | Set local timezone | ✅ Supports 400+ timezones |

## �️ Installation & Setup

### **Prerequisites**
- Python 3.12+ 
- Telegram Bot Token ([Get from @BotFather](https://t.me/BotFather))
- DeepSeek API Key ([Get from DeepSeek](https://www.deepseek.com/))
- WeatherAPI Key ([Get from WeatherAPI](https://www.weatherapi.com/))
- Calendarific API Key ([Get from Calendarific](https://calendarific.com/))

### **Step 1: Environment Setup**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r config/requirements.txt
```

### **Step 2: API Configuration**
Create `.env` file with your API keys:

```bash
# Telegram Bot (Required)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ

# AI Analysis (Required for crypto features)
DEEPSEEK_API=sk-1234567890abcdef

# Weather Data (Optional)
WEATHERAPI_KEY=1234567890abcdef

# Holiday Data (Optional)  
CALENDARIFIC_API_KEY=1234567890abcdef

# Stock Data (Future feature)
TWELVE_DATA_API_KEY=1234567890abcdef
```

### **Step 3: Launch Options**

```bash
# 🚀 Full Bot (Recommended)
./bin/choynews --service both
# Runs interactive bot + auto news delivery

# 💬 Interactive Bot Only  
./bin/choynews --service bot
# Manual commands only (no scheduled news)

# ⏰ Auto News Service Only
./bin/choynews --service auto  
# Scheduled delivery only (no manual interaction)
```

## 🏭 Production Deployment

### **PM2 Process Manager (Recommended)**
```bash
# Install PM2
npm install -g pm2

# Start services
pm2 start tools/deploy/pm2_config.json

# Monitor
pm2 status
pm2 logs choynews-bot
pm2 restart choynews-bot

# Auto-startup on boot
pm2 startup
pm2 save
```

### **Docker Deployment**
```bash
# Build image
docker build -t choynews-bot .

# Run container
docker run -d \
  --name choynews-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  choynews-bot
```

### **System Service (Linux)**
```bash
# Create service file
sudo cp tools/deploy/choynews.service /etc/systemd/system/

# Enable and start
sudo systemctl enable choynews
sudo systemctl start choynews
sudo systemctl status choynews
```

## 🔍 Advanced Features

### **🧠 AI Analysis Deep Dive**
The DeepSeek AI integration provides:

- **Market Sentiment Analysis** - Analyzes market trends, news sentiment, and social media buzz
- **Technical Indicators** - RSI, MACD, Bollinger Bands, Support/Resistance levels  
- **Price Predictions** - 24-hour forecasts with confidence intervals
- **Trading Signals** - BUY/HOLD/SELL recommendations with risk assessment
- **Portfolio Insights** - Diversification suggestions and risk analysis

### **📊 Data Sources & Reliability**

| Category | Primary Sources | Backup Sources | Update Frequency |
|----------|----------------|----------------|------------------|
| **Local News** | Prothom Alo, Daily Star, BDNews24 | Jugantor, Kaler Kantho | Every 15 min |
| **Global News** | BBC, Reuters, CNN | Al Jazeera, Guardian | Every 10 min |
| **Tech News** | TechCrunch, The Verge, Wired | Ars Technica, Engadget | Every 20 min |
| **Crypto News** | CoinTelegraph, CoinDesk | Decrypt, The Block | Every 5 min |
| **Crypto Prices** | CoinGecko | CoinMarketCap | Real-time |
| **Weather** | WeatherAPI | OpenWeatherMap | Every 30 min |

### **🔄 Smart Deduplication System**

ChoyNewsBot uses advanced algorithms to ensure zero news repetition:

1. **Content Hashing** - MD5 hashes of title + source combinations
2. **Time Windows** - 4-hour deduplication windows between digest times
3. **Similarity Detection** - Fuzzy matching for different versions of same story
4. **Source Prioritization** - Preference ranking for authoritative sources
5. **Freshness Scoring** - Recent news gets priority over older stories

### **⏰ Intelligent Scheduling**

The bot delivers news at optimal times based on user behavior analysis:

- **8:00 AM** - Morning briefing (highest engagement)
- **1:00 PM** - Lunch update (moderate engagement)  
- **7:00 PM** - Evening digest (high engagement)
- **11:00 PM** - Night summary (low engagement, brief format)

Timezone support includes automatic DST handling and 400+ timezone recognition.

## 🧪 Development & Testing

### **🔧 Development Setup**
```bash
# Clone for development
git clone https://github.com/shanchoy/choynews-bot.git
cd choynews-bot

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/ -v

# Test specific components
python -c "from choynews.core.digest_builder import build_news_digest; print(build_news_digest())"
```

### **🧪 Testing Suite**
```bash
# Run all tests
python -m pytest tests/

# Test categories
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests
python -m pytest tests/fixtures/      # Test data validation

# Coverage report
python -m pytest --cov=choynews tests/
```

### **📊 Performance Monitoring**
```bash
# Real-time logs
tail -f logs/choynews.log

# Performance metrics
curl http://localhost:8080/metrics  # If monitoring enabled

# Database stats
sqlite3 data/news_history.db ".tables"
sqlite3 data/news_history.db "SELECT COUNT(*) FROM news_history;"
```

## 🏗️ Architecture & Code Structure

```
choynews/                         # 🏠 Main application package
├── api/                          # 🌐 External API integrations
│   └── telegram.py               # Telegram Bot API wrapper
├── core/                         # 🧠 Core business logic
│   ├── advanced_news_fetcher.py  # AI-powered news aggregation with smart filtering
│   ├── digest_builder.py         # News digest compilation with content cleaning
│   └── bot.py                    # Main bot controller
├── data/                         # 💾 Data models & persistence
│   ├── models.py                 # User data models
│   ├── subscriptions.py          # Subscription management
│   ├── user_logs.py              # User interaction logging
│   └── crypto_cache.py           # Price data caching
├── services/                     # 🚀 High-level services
│   └── bot_service.py            # Command handling service with /about support
└── utils/                        # 🛠️ Utility functions
    ├── config.py                 # Configuration management
    ├── logging.py                # Logging setup
    └── time_utils.py             # Timezone handling

bin/                              # 📦 Executable scripts
├── choynews                      # Main application entry point
└── utils/                        # Additional utilities
    └── update_coinlist.py        # Cryptocurrency list updater

config/                           # ⚙️ Configuration files
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment template

data/                             # 📊 Data storage
├── cache/                        # API response cache
│   ├── crypto_bigcap_cache.json  # Large cap crypto cache
│   ├── crypto_market_cache.json  # Market data cache
│   └── crypto_movers_cache.json  # Price movement cache
├── static/                       # Static data files
│   ├── coinlist.json             # Supported cryptocurrency list
│   └── user_timezones.json       # Timezone mappings
├── memory.json                   # Bot information for /about command
└── *.db                          # SQLite databases (news_history.db)

docs/                             # 📚 Documentation
├── api-docs.md                   # API documentation
├── developer-guide.md            # Development guide
├── deployment.md                 # Deployment instructions
├── installation.md               # Installation guide
├── user-guide.md                 # User manual
├── README.md                     # Documentation overview
└── user/                         # User-focused documentation
    └── getting_started.md        # Quick start guide

tools/                            # 🔧 Development tools
├── deploy/                       # Deployment scripts
│   ├── migrate.sh                # Database migration
│   ├── pm2_config.json           # PM2 configuration
│   └── setup_server.sh           # Server setup script
└── dev/                          # Development utilities
    ├── cleanup.sh                # Development cleanup
    ├── final_cleanup.sh          # Final project cleanup
    ├── migrate.sh                # Development migration
    └── run.sh                    # Development runner

logs/                             # 📝 Application logs
build/                            # 🔨 Build artifacts
choynews.egg-info/                # 📦 Package metadata
```

### **🔌 Key Components**

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **advanced_news_fetcher.py** | RSS aggregation + AI analysis | 3-hour time filtering, max 3 per source, smart scoring |
| **digest_builder.py** | News compilation + formatting | Content cleaning, footer protection, Markdown rendering |
| **bot_service.py** | Command routing + user interaction | All commands including new /about, error handling |
| **telegram.py** | Low-level Telegram API | HTTP requests, message formatting, rate limiting |
| **models.py** | User data + subscription logic | SQLite operations, timezone handling |
| **memory.json** | Bot information storage | Dynamic /about content, feature descriptions |

### **🆕 Recent Enhancements**

- **🕒 Smart Time Filtering**: News limited to 3-hour window with 1-hour priority
- **📊 Source Distribution**: Maximum 3 articles per source per category  
- **🧹 Content Cleaning**: Advanced digest cleaning to prevent extra content
- **📱 About Command**: Dynamic /about command reading from memory.json
- **🗑️ Clean Architecture**: All test files removed for production focus
- **⚡ Enhanced Scoring**: Combined importance + recency scoring algorithm

## 🚨 Troubleshooting

### **Common Issues**

**🔴 Bot not responding to commands**
```bash
# Check bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Verify service status  
ps aux | grep choynews
systemctl status choynews
```

**🟡 News not updating**
```bash
# Check RSS feed accessibility
curl -I https://feeds.bbci.co.uk/news/rss.xml

# Verify database connectivity
sqlite3 data/news_history.db "SELECT COUNT(*) FROM news_history;"

# Check API rate limits
tail -f logs/choynews.log | grep "rate limit"
```

**🟠 AI analysis not working**
```bash
# Test DeepSeek API
curl -H "Authorization: Bearer $DEEPSEEK_API" \
     https://api.deepseek.com/chat/completions

# Check API key format
echo $DEEPSEEK_API | grep "sk-"
```

**🔵 Weather data missing**
```bash
# Test WeatherAPI
curl "http://api.weatherapi.com/v1/current.json?key=$WEATHERAPI_KEY&q=Dhaka"

# Check rate limits (1000/month free tier)
grep "weather" logs/choynews.log | tail -10
```

### **Performance Optimization**

**Database Maintenance**
```bash
# Clean old news history (runs automatically)
sqlite3 data/news_history.db "DELETE FROM news_history WHERE sent_time < datetime('now', '-7 days');"

# Rebuild database indices
sqlite3 data/news_history.db "REINDEX;"

# Check database size
du -h data/*.db
```

**Memory Management**
```bash
# Monitor memory usage
ps aux | grep choynews | awk '{print $6/1024 " MB"}'

# Restart services if needed
pm2 restart choynews-bot
systemctl restart choynews
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### **🛠️ Development Workflow**
```bash
# 1. Fork and clone
git clone https://github.com/yourusername/choynews-bot.git
cd choynews-bot

# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Install development dependencies
pip install -r config/requirements.txt
pip install -e .

# 4. Make changes and test
python -m pytest tests/
python -m flake8 choynews/

# 5. Submit pull request
git push origin feature/amazing-feature
```

### **📋 Contribution Guidelines**
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure AI analysis accuracy
- Test with multiple timezones

### **🎯 Areas for Contribution**
- 🌐 Additional news sources
- 🤖 Enhanced AI prompts
- � Advanced analytics
- 🔒 Security improvements
- 🌍 Multi-language support

## 📞 Support & Community

### **💬 Get Help**
- 📧 Email: [shanchoyzone@gmail.com](mailto:shanchoyzone@gmail.com)
- 🐛 Issues: [GitHub Issues](https://github.com/shanchoy/choynews-bot/issues)
- 💡 Features: [GitHub Discussions](https://github.com/shanchoy/choynews-bot/discussions)
- 📱 Telegram: [@ChoyNewsBot](https://t.me/shanchoynoor)

### **🏷️ Version History**
- **v2.0.0** - AI-powered analysis with DeepSeek integration
- **v1.5.0** - Smart deduplication and 5-item guarantee  
- **v1.2.0** - Real-time crypto data with technical analysis
- **v1.0.0** - Basic news aggregation and scheduling

### **📜 License**
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **� Acknowledgments**
- DeepSeek for AI analysis capabilities
- CoinGecko for reliable crypto data
- WeatherAPI for accurate weather information
- Telegram for the excellent Bot API
- All RSS news providers for content access

---

**⭐ Star this repo if ChoyNewsBot helps you stay informed with AI-powered intelligence!**

Made with ❤️ by [Shanchoy Noor](https://github.com/shanchoy)
