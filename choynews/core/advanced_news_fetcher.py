"""
Advanced News Fetcher with AI Analysis for Choy News Bot.

This module fetches real-time breaking news, crypto data with AI analysis,
and weather data while ensuring no duplicate news across time slots.
"""

import requests
import feedparser
import json
import os
import sqlite3
from datetime import datetime, timedelta
import hashlib
import pytz
from choynews.utils.logging import get_logger
from choynews.utils.config import Config
from choynews.utils.time_utils import get_bd_now

logger = get_logger(__name__)

# Database for tracking sent news
NEWS_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "news_history.db")

def init_news_history_db():
    """Initialize the news history database."""
    os.makedirs(os.path.dirname(NEWS_DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(NEWS_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_hash TEXT UNIQUE,
            title TEXT,
            source TEXT,
            published_time TEXT,
            sent_time TEXT,
            category TEXT,
            url TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_news_hash(title, source):
    """Generate a unique hash for news item to track duplicates."""
    return hashlib.md5(f"{title.lower().strip()}{source}".encode()).hexdigest()

def is_news_already_sent(news_hash, hours_back=6):
    """Check if news was already sent in the last N hours."""
    try:
        conn = sqlite3.connect(NEWS_DB_PATH)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        cursor.execute('''
            SELECT COUNT(*) FROM news_history 
            WHERE news_hash = ? AND sent_time > ?
        ''', (news_hash, cutoff_time.isoformat()))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    except Exception as e:
        logger.error(f"Error checking news history: {e}")
        return False

def mark_news_as_sent(news_hash, title, source, published_time, category, url=""):
    """Mark news as sent to prevent future duplicates."""
    try:
        conn = sqlite3.connect(NEWS_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO news_history 
            (news_hash, title, source, published_time, sent_time, category, url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (news_hash, title, source, published_time, datetime.now().isoformat(), category, url))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error marking news as sent: {e}")

def cleanup_old_news_history(days_back=7):
    """Clean up old news history to prevent database bloat."""
    try:
        conn = sqlite3.connect(NEWS_DB_PATH)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(days=days_back)
        
        cursor.execute('''
            DELETE FROM news_history WHERE sent_time < ?
        ''', (cutoff_time.isoformat(),))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error cleaning up news history: {e}")

def format_time_ago(published_time):
    """Convert published time to relative time format."""
    try:
        if isinstance(published_time, str):
            try:
                pub_time = datetime.strptime(published_time, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                try:
                    pub_time = datetime.strptime(published_time, "%Y-%m-%dT%H:%M:%S%z")
                    pub_time = pub_time.replace(tzinfo=None)
                except:
                    try:
                        pub_time = datetime.strptime(published_time[:19], "%Y-%m-%dT%H:%M:%S")
                    except:
                        return "now"
        else:
            pub_time = published_time
            
        now = datetime.now()
        diff = now - pub_time
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}hr ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}min ago"
        else:
            return "now"
    except Exception as e:
        logger.debug(f"Error formatting time: {e}")
        return "now"

def fetch_breaking_news_rss(sources, limit=15, category="news", target_count=5):
    """Fetch breaking news from RSS sources with deduplication, ensuring target count."""
    fresh_entries = []
    
    for source_name, rss_url in sources.items():
        try:
            logger.debug(f"Fetching breaking news from {source_name}")
            
            headers = {
                'User-Agent': 'ChoyNewsBot/1.0 (Breaking News Fetcher)'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                continue
                
            # Get more entries to ensure we have enough after filtering
            for entry in feed.entries[:limit]:
                try:
                    title = entry.get('title', '').strip()
                    if not title:
                        continue
                        
                    # Clean and limit title length
                    if len(title) > 120:
                        title = title[:117] + "..."
                    
                    link = entry.get('link', '')
                    pub_time = entry.get('published', entry.get('updated', ''))
                    time_ago = format_time_ago(pub_time)
                    
                    # Check if this is recent news (within last 48 hours for more coverage)
                    is_recent = True
                    try:
                        if pub_time:
                            if isinstance(pub_time, str):
                                try:
                                    parsed_time = datetime.strptime(pub_time, "%a, %d %b %Y %H:%M:%S %Z")
                                except:
                                    try:
                                        parsed_time = datetime.strptime(pub_time[:19], "%Y-%m-%dT%H:%M:%S")
                                    except:
                                        parsed_time = datetime.now()  # Use current time if parsing fails
                            else:
                                parsed_time = pub_time
                                
                            # Allow news from last 48 hours to ensure enough content
                            if (datetime.now() - parsed_time).days > 2:
                                is_recent = False
                    except:
                        is_recent = True  # Include if we can't parse time
                    
                    if not is_recent:
                        continue
                    
                    # Check for duplicates with shorter time window for more variety
                    news_hash = get_news_hash(title, source_name)
                    if is_news_already_sent(news_hash, hours_back=4):  # Reduced from 6 to 4 hours
                        continue
                    
                    entry_data = {
                        'title': title,
                        'link': link,
                        'source': source_name,
                        'published': pub_time,
                        'time_ago': time_ago,
                        'hash': news_hash,
                        'category': category
                    }
                    
                    fresh_entries.append(entry_data)
                    
                    # Stop if we have enough entries
                    if len(fresh_entries) >= target_count * 3:  # Get 3x target for good selection
                        break
                    
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            continue
        
        # Break early if we have enough entries
        if len(fresh_entries) >= target_count * 2:
            break
    
    # Sort by recency and return most recent
    try:
        fresh_entries.sort(key=lambda x: x.get('published', ''), reverse=True)
    except:
        pass
        
    return fresh_entries

def format_news_section(section_title, entries, limit=5):
    """Format news entries with source attribution and timestamps, ensuring exactly 5 items."""
    formatted = f"*{section_title}:*\n"
    
    # Define fallback messages for each category
    category_fallbacks = {
        "🇧🇩 LOCAL NEWS": [
            "Breaking local news updates coming soon...",
            "Local political developments being monitored...",
            "Regional economic updates being tracked...",
            "Local social updates will be available shortly...",
            "Community news updates in progress..."
        ],
        "🌍 GLOBAL NEWS": [
            "International breaking news being updated...",
            "Global political developments being tracked...", 
            "World economic updates coming soon...",
            "International affairs updates in progress...",
            "Global crisis updates being monitored..."
        ],
        "🚀 TECH NEWS": [
            "Latest technology breakthroughs being analyzed...",
            "AI and innovation updates coming soon...",
            "Tech industry developments being tracked...",
            "Startup and venture updates in progress...",
            "Digital transformation news being compiled..."
        ],
        "🏆 SPORTS NEWS": [
            "Sports scores and updates being compiled...",
            "League standings and results coming soon...",
            "Player transfers and moves being tracked...",
            "Tournament updates in progress...",
            "Sports analysis and commentary being prepared..."
        ],
        "🪙 FINANCE & CRYPTO NEWS": [
            "Cryptocurrency market movements being analyzed...",
            "DeFi protocol updates being tracked...",
            "Blockchain developments coming soon...",
            "Digital asset regulatory news in progress...",
            "Crypto trading insights being compiled..."
        ]
    }
    
    count = 0
    
    # First, add real news entries
    for entry in entries:
        if count >= limit:
            break
            
        title = entry.get('title', '')
        source = entry.get('source', '')
        time_ago = entry.get('time_ago', '')
        link = entry.get('link', '')
        
        # Skip empty titles
        if not title.strip():
            continue
        
        # Escape markdown characters in title
        title_escaped = title.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
        
        count += 1
        if link:
            formatted += f"{count}. [{title_escaped}]({link}) - {source} ({time_ago})\n"
        else:
            formatted += f"{count}. {title_escaped} - {source} ({time_ago})\n"
        
        # Mark as sent to prevent duplicates
        try:
            mark_news_as_sent(entry['hash'], title, source, entry.get('published', ''), entry.get('category', ''), link)
        except Exception as e:
            logger.debug(f"Error marking news as sent: {e}")
    
    # Fill remaining slots with fallback messages if needed
    fallback_messages = category_fallbacks.get(section_title, [
        "News updates will be available shortly...",
        "Breaking news being monitored...",
        "Latest developments being tracked...",
        "Updates coming soon...",
        "News compilation in progress..."
    ])
    
    fallback_index = 0
    while count < limit:
        count += 1
        fallback_msg = fallback_messages[fallback_index % len(fallback_messages)]
        formatted += f"{count}. {fallback_msg}\n"
        fallback_index += 1
    
    return formatted + "\n"

# ===================== NEWS SOURCES =====================

def get_breaking_local_news():
    """Get breaking Bangladesh news."""
    bd_sources = {
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "The Daily Star": "https://www.thedailystar.net/frontpage/rss.xml",
        "BDNews24": "https://bdnews24.com/feed",
        "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
        "Kaler Kantho": "https://www.kalerkantho.com/rss.xml",
        "Bangladesh Pratidin": "https://www.bd-pratidin.com/rss.xml",
        "Jugantor": "https://www.jugantor.com/feed",
        "New Age": "http://www.newagebd.net/rss/rss.xml",
        "Financial Express": "https://thefinancialexpress.com.bd/rss",
        "Dhaka Post": "https://www.dhakapost.com/rss.xml"
    }
    
    entries = fetch_breaking_news_rss(bd_sources, limit=20, category="local", target_count=5)
    return format_news_section("🇧🇩 LOCAL NEWS", entries, limit=5)

def get_breaking_global_news():
    """Get breaking global news."""
    global_sources = {
        "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
        "Reuters": "http://feeds.reuters.com/reuters/topNews",
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "New York Post": "https://nypost.com/feed/",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "NBC News": "https://feeds.nbcnews.com/nbcnews/public/news",
        "Associated Press": "https://feeds.apnews.com/rss/apf-topnews",
        "Sky News": "http://feeds.skynews.com/feeds/rss/world.xml",
        "France24": "https://www.france24.com/en/rss"
    }
    
    entries = fetch_breaking_news_rss(global_sources, limit=20, category="global", target_count=5)
    return format_news_section("🌍 GLOBAL NEWS", entries, limit=5)

def get_breaking_tech_news():
    """Get breaking technology news."""
    tech_sources = {
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Wired": "https://www.wired.com/feed/rss",
        "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index/",
        "Mashable": "https://mashable.com/feeds/rss/all",
        "VentureBeat": "https://venturebeat.com/feed/",
        "Engadget": "https://www.engadget.com/rss.xml",
        "ZDNet": "https://www.zdnet.com/news/rss.xml",
        "TechRadar": "https://www.techradar.com/rss"
    }
    
    entries = fetch_breaking_news_rss(tech_sources, limit=15, category="tech", target_count=5)
    return format_news_section("🚀 TECH NEWS", entries, limit=5)

def get_breaking_sports_news():
    """Get breaking sports news."""
    sports_sources = {
        "ESPN": "https://www.espn.com/espn/rss/news",
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "Yahoo Sports": "https://sports.yahoo.com/rss/",
        "Sporting News": "https://www.sportingnews.com/rss",
        "Sports Illustrated": "https://www.si.com/rss/si_topstories.rss",
        "Fox Sports": "https://www.foxsports.com/feeds/rss/1.0/sports-news",
        "CBS Sports": "https://www.cbssports.com/rss/headlines",
        "Sky Sports": "http://www.skysports.com/rss/12040"
    }
    
    entries = fetch_breaking_news_rss(sports_sources, limit=15, category="sports", target_count=5)
    return format_news_section("🏆 SPORTS NEWS", entries, limit=5)

def get_breaking_crypto_news():
    """Get breaking cryptocurrency news."""
    crypto_sources = {
        "Cointelegraph": "https://cointelegraph.com/rss",
        "Decrypt": "https://decrypt.co/feed",
        "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "The Block": "https://www.theblock.co/rss.xml",
        "Bitcoin Magazine": "https://bitcoinmagazine.com/feed",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "NewsBTC": "https://www.newsbtc.com/feed/",
        "CoinTelegraph": "https://cointelegraph.com/rss",
        "Crypto News": "https://cryptonews.com/news/feed/"
    }
    
    entries = fetch_breaking_news_rss(crypto_sources, limit=15, category="crypto", target_count=5)
    return format_news_section("🪙 FINANCE & CRYPTO NEWS", entries, limit=5)

# ===================== CRYPTO DATA WITH AI =====================

def fetch_crypto_market_with_ai():
    """Fetch crypto market data with DeepSeek AI analysis."""
    try:
        # Fetch market overview
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()["data"]
        market_cap = data["total_market_cap"]["usd"]
        volume = data["total_volume"]["usd"]
        market_change = data["market_cap_change_percentage_24h_usd"]
        
        # Fetch top cryptos for AI analysis
        crypto_url = "https://api.coingecko.com/api/v3/coins/markets"
        crypto_params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": False
        }
        
        crypto_response = requests.get(crypto_url, params=crypto_params, timeout=10)
        crypto_data = crypto_response.json()
        
        # Fetch Fear & Greed Index
        try:
            fear_response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
            fear_index = fear_response.json()["data"][0]["value"]
            fear_text = fear_response.json()["data"][0]["value_classification"]
        except:
            fear_index = "N/A"
            fear_text = "Unknown"
        
        # Prepare data for AI analysis
        market_summary = {
            "market_cap": market_cap,
            "volume": volume,
            "market_change": market_change,
            "fear_greed": fear_index,
            "top_cryptos": crypto_data[:10]
        }
        
        # Get AI analysis
        ai_analysis = get_crypto_ai_analysis(market_summary)
        
        # Format response
        market_cap_str = f"${market_cap/1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap/1e9:.2f}B"
        volume_str = f"${volume/1e12:.2f}T" if volume >= 1e12 else f"${volume/1e9:.2f}B"
        
        crypto_section = f"""*💰 CRYPTO MARKET:*
Market Cap (24h): {market_cap_str} ({market_change:+.2f}%)
Volume (24h): {volume_str}
Fear/Greed Index: {fear_index}/100 ({fear_text})

🤖 AI Market Summary:
{ai_analysis}

"""
        
        return crypto_section
        
    except Exception as e:
        logger.error(f"Error fetching crypto market data: {e}")
        return "*💰 CRYPTO MARKET:*\nMarket data temporarily unavailable.\n\n"

def get_crypto_ai_analysis(market_data):
    """Get AI analysis of crypto market using DeepSeek API."""
    try:
        api_key = Config.DEEPSEEK_API
        if not api_key:
            return "AI analysis unavailable (API key not configured)."
        
        # Prepare prompt for DeepSeek
        top_cryptos_info = []
        for crypto in market_data["top_cryptos"][:5]:
            name = crypto.get("name", "")
            price = crypto.get("current_price", 0)
            change = crypto.get("price_change_percentage_24h", 0)
            top_cryptos_info.append(f"{name}: ${price:.2f} ({change:+.2f}%)")
        
        prompt = f"""Analyze the current cryptocurrency market:

Market Cap: ${market_data['market_cap']/1e12:.2f}T ({market_data['market_change']:+.2f}%)
24h Volume: ${market_data['volume']/1e9:.2f}B
Fear & Greed Index: {market_data['fear_greed']}/100

Top 5 Cryptocurrencies:
{chr(10).join(top_cryptos_info)}

Provide a concise 2-3 sentence market analysis focusing on:
1. Overall market sentiment and trend direction
2. Key factors driving current movements
3. Brief prediction for next 24 hours (BULLISH/BEARISH/CONSOLIDATION)

Keep it under 250 characters and end with prediction like: "Prediction (Next 24h): BULLISH 📈" or "BEARISH 📉" or "CONSOLIDATION 🤔"
"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result["choices"][0]["message"]["content"].strip()
            return analysis
        else:
            logger.error(f"DeepSeek API error: {response.status_code}")
            return "AI analysis temporarily unavailable."
            
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        return "AI analysis temporarily unavailable."

def get_individual_crypto_stats(symbol):
    """Get detailed crypto stats with AI analysis for individual coins."""
    try:
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            'btc': 'bitcoin',
            'eth': 'ethereum', 
            'doge': 'dogecoin',
            'ada': 'cardano',
            'sol': 'solana',
            'xrp': 'ripple',
            'matic': 'matic-network',
            'dot': 'polkadot',
            'link': 'chainlink',
            'uni': 'uniswap'
        }
        
        coin_id = symbol_map.get(symbol.lower(), symbol.lower())
        
        # Fetch detailed coin data
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        market_data = data.get("market_data", {})
        
        # Extract key metrics
        name = data.get("name", symbol.upper())
        current_price = market_data.get("current_price", {}).get("usd", 0)
        price_change_24h = market_data.get("price_change_percentage_24h", 0)
        market_cap = market_data.get("market_cap", {}).get("usd", 0)
        volume_24h = market_data.get("total_volume", {}).get("usd", 0)
        market_cap_rank = market_data.get("market_cap_rank", "N/A")
        
        # Calculate support/resistance (simplified)
        high_24h = market_data.get("high_24h", {}).get("usd", current_price)
        low_24h = market_data.get("low_24h", {}).get("usd", current_price)
        
        # Get AI analysis for this specific coin
        ai_analysis = get_individual_crypto_ai_analysis({
            "name": name,
            "symbol": symbol.upper(),
            "price": current_price,
            "change_24h": price_change_24h,
            "market_cap": market_cap,
            "volume": volume_24h,
            "high_24h": high_24h,
            "low_24h": low_24h
        })
        
        # Format price
        if current_price >= 1:
            price_str = f"${current_price:.2f}"
        else:
            price_str = f"${current_price:.4f}"
        
        # Format market cap
        if market_cap >= 1e9:
            mcap_str = f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            mcap_str = f"${market_cap/1e6:.2f}M"
        else:
            mcap_str = f"${market_cap:.0f}"
        
        # Format volume
        if volume_24h >= 1e9:
            vol_str = f"${volume_24h/1e9:.2f}B"
        elif volume_24h >= 1e6:
            vol_str = f"${volume_24h/1e6:.2f}M"
        else:
            vol_str = f"${volume_24h:.0f}"
        
        # Direction indicator
        direction = "▲" if price_change_24h > 0 else "▼" if price_change_24h < 0 else "→"
        
        stats_message = f"""Price: {symbol.upper()} {price_str} ({price_change_24h:+.2f}%) {direction}
Market Summary: {name} is currently trading at {price_str} with a 24h change of ({price_change_24h:+.2f}%) {direction}. 24h Market Cap: {mcap_str}. 24h Volume: {vol_str}.

{ai_analysis}"""
        
        return stats_message
        
    except Exception as e:
        logger.error(f"Error fetching {symbol} stats: {e}")
        return f"Sorry, I couldn't get detailed stats for {symbol.upper()}. Please try again later."

def get_individual_crypto_ai_analysis(coin_data):
    """Get AI analysis for individual cryptocurrency."""
    try:
        api_key = Config.DEEPSEEK_API
        if not api_key:
            return "AI analysis unavailable."
        
        prompt = f"""Analyze {coin_data['name']} ({coin_data['symbol']}):

Current Price: ${coin_data['price']:.4f}
24h Change: {coin_data['change_24h']:+.2f}%
Market Cap: ${coin_data['market_cap']/1e9:.2f}B
24h Volume: ${coin_data['volume']/1e9:.2f}B
24h High: ${coin_data['high_24h']:.4f}
24h Low: ${coin_data['low_24h']:.4f}

Provide analysis in this exact format:
"[Sentiment assessment]. 

Technicals:
- Support: $[support_level]
- Resistance: $[resistance_level] 
- RSI ([value]): [Neutral/Overbought/Oversold], [interpretation]
- 30D MA ($[value]): [Position vs MA], [momentum assessment]
- Volume: [High/Medium/Low] ($[volume]), [liquidity comment]
- Sentiment: [Brief sentiment analysis]

Forecast (Next 24h): [Brief prediction]

Prediction (Next 24hr): 🟢 BUY / 🟠 HOLD / 🔴 SELL"

Keep technical values realistic based on the data provided.
"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result["choices"][0]["message"]["content"].strip()
            return analysis
        else:
            logger.error(f"DeepSeek API error: {response.status_code}")
            return "AI analysis temporarily unavailable."
            
    except Exception as e:
        logger.error(f"Error getting individual crypto AI analysis: {e}")
        return "AI analysis temporarily unavailable."

# ===================== WEATHER DATA =====================

def get_dhaka_weather():
    """Get comprehensive Dhaka weather data."""
    try:
        api_key = Config.WEATHERAPI_KEY
        if not api_key:
            return ""
            
        url = "http://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": "Dhaka",
            "aqi": "yes"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current = data.get("current", {})
        location = data.get("location", {})
        
        temp_c = current.get("temp_c", 0)
        feels_like = current.get("feelslike_c", temp_c)
        condition = current.get("condition", {}).get("text", "N/A")
        humidity = current.get("humidity", 0)
        
        # Rain probability (if available)
        rain_chance = "N/A"  # WeatherAPI current doesn't include rain probability
        
        # Air quality
        aqi_data = current.get("air_quality", {})
        us_epa = aqi_data.get("us-epa-index", 0)
        aqi_levels = {
            1: "Good", 2: "Moderate", 3: "Unhealthy for Sensitive", 
            4: "Unhealthy", 5: "Very Unhealthy", 6: "Hazardous"
        }
        aqi_text = aqi_levels.get(us_epa, "Moderate")
        aqi_value = int(aqi_data.get("pm2_5", 50))  # Use PM2.5 as AQI approximation
        
        uv = current.get("uv", 0)
        uv_level = "Low" if uv < 3 else "Moderate" if uv < 6 else "High" if uv < 8 else "Very High"
        
        weather_section = f"""🌦️ Dhaka: {temp_c:.1f}°C ~ {feels_like:.1f}°C
🌧️ {condition}
🫧 AQI: {aqi_text} ({aqi_value})
🔆 UV: {uv_level} ({uv})

"""
        
        return weather_section
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return ""

# ===================== HOLIDAYS =====================

def get_bd_holidays():
    """Get Bangladesh holidays for today."""
    try:
        api_key = Config.CALENDARIFIC_API_KEY
        if not api_key:
            return ""
            
        today = get_bd_now()
        url = "https://calendarific.com/api/v2/holidays"
        params = {
            "api_key": api_key,
            "country": "BD",
            "year": today.year,
            "month": today.month,
            "day": today.day
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        holidays = data.get("response", {}).get("holidays", [])
        
        if holidays:
            holiday_names = [h.get("name", "Holiday") for h in holidays]
            return f"🎉 Today's Holiday: {', '.join(holiday_names)}\n\n"
        else:
            return ""
            
    except Exception as e:
        logger.debug(f"Error fetching holidays: {e}")
        return ""

# Initialize on import
init_news_history_db()
