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

def calculate_news_importance_score(entry, source_name, feed_position):
    """Calculate importance score for news entry based on multiple factors."""
    score = 0
    title = entry.get('title', '').lower()
    
    # Position in feed (earlier = more important)
    position_score = max(0, 10 - feed_position)  # First 10 entries get bonus
    score += position_score
    
    # Source credibility weight
    source_weights = {
        # Local sources
        'Prothom Alo': 10, 'The Daily Star': 9, 'BDNews24': 8, 'Dhaka Tribune': 7,
        'Financial Express': 8, 'New Age': 6, 'Kaler Kantho': 6,
        # Global sources
        'BBC': 10, 'Reuters': 10, 'CNN': 8, 'Al Jazeera': 8, 'Associated Press': 9,
        'The Guardian': 8, 'NBC News': 7, 'Sky News': 7, 'New York Post': 6,
        # Tech sources
        'TechCrunch': 10, 'The Verge': 9, 'Ars Technica': 8, 'Wired': 8,
        'VentureBeat': 7, 'Engadget': 7, 'ZDNet': 6, 'Mashable': 6,
        # Sports sources
        'ESPN': 10, 'BBC Sport': 9, 'Sports Illustrated': 8, 'Yahoo Sports': 7,
        'Fox Sports': 7, 'CBS Sports': 7, 'Sky Sports': 8,
        # Crypto sources
        'Cointelegraph': 8, 'CoinDesk': 9, 'Decrypt': 7, 'The Block': 8,
        'Bitcoin Magazine': 7, 'CryptoSlate': 6, 'NewsBTC': 6
    }
    score += source_weights.get(source_name, 5)  # Default weight 5
    
    # Breaking news keywords
    breaking_keywords = ['breaking', 'urgent', 'alert', 'emergency', 'crisis', 'live', 
                        'developing', 'update', 'latest', 'just in', 'confirmed',
                        'exclusive', 'major', 'significant', 'important', 'critical']
    for keyword in breaking_keywords:
        if keyword in title:
            score += 5
    
    # High-impact keywords by category
    if any(word in title for word in ['death', 'killed', 'murder', 'accident', 'disaster', 
                                     'earthquake', 'flood', 'fire', 'explosion', 'crash']):
        score += 8
    
    if any(word in title for word in ['election', 'government', 'minister', 'president', 
                                     'prime minister', 'parliament', 'court', 'verdict']):
        score += 7
    
    if any(word in title for word in ['bitcoin', 'crypto', 'blockchain', 'ethereum', 
                                     'market crash', 'surge', 'rally', 'all-time high']):
        score += 6
    
    if any(word in title for word in ['war', 'conflict', 'attack', 'bombing', 'invasion', 
                                     'ceasefire', 'peace', 'treaty']):
        score += 9
    
    # Technology impact keywords
    if any(word in title for word in ['ai', 'artificial intelligence', 'chatgpt', 'openai',
                                     'launch', 'release', 'breakthrough', 'innovation']):
        score += 5
    
    return score

def fetch_breaking_news_rss(sources, limit=25, category="news", target_count=5):
    """Fetch breaking news from RSS sources prioritizing both recency and importance."""
    all_entries = []
    
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
                
            # Process all entries from this source
            for position, entry in enumerate(feed.entries[:limit]):
                try:
                    title = entry.get('title', '').strip()
                    if not title:
                        continue
                        
                    # Clean and limit title length
                    if len(title) > 120:
                        title = title[:117] + "..."
                    
                    link = entry.get('link', '')
                    pub_time = entry.get('published', entry.get('updated', ''))
                    
                    # Parse and validate publication time
                    parsed_time = None
                    try:
                        if pub_time:
                            if isinstance(pub_time, str):
                                try:
                                    parsed_time = datetime.strptime(pub_time, "%a, %d %b %Y %H:%M:%S %Z")
                                except:
                                    try:
                                        parsed_time = datetime.strptime(pub_time, "%Y-%m-%dT%H:%M:%S%z")
                                        parsed_time = parsed_time.replace(tzinfo=None)
                                    except:
                                        try:
                                            parsed_time = datetime.strptime(pub_time[:19], "%Y-%m-%dT%H:%M:%S")
                                        except:
                                            parsed_time = datetime.now()  # Use current time as fallback
                            else:
                                parsed_time = pub_time
                        else:
                            parsed_time = datetime.now()
                    except:
                        parsed_time = datetime.now()
                    
                    # Only include news from last 24 hours for freshness
                    time_diff = datetime.now() - parsed_time
                    if time_diff.days > 1:  # Stricter time filter
                        continue
                    
                    time_ago = format_time_ago(pub_time)
                    
                    # Check for duplicates
                    news_hash = get_news_hash(title, source_name)
                    if is_news_already_sent(news_hash, hours_back=2):  # Reduced to 2 hours for more variety
                        continue
                    
                    # Calculate importance score
                    importance_score = calculate_news_importance_score(entry, source_name, position)
                    
                    # Calculate recency score (newer = higher score)
                    hours_ago = time_diff.total_seconds() / 3600
                    recency_score = max(0, 24 - hours_ago)  # 24 points for newest, decreasing
                    
                    # Combined score (importance + recency)
                    total_score = importance_score + (recency_score * 0.5)  # Weight recency at 50%
                    
                    entry_data = {
                        'title': title,
                        'link': link,
                        'source': source_name,
                        'published': pub_time,
                        'parsed_time': parsed_time,
                        'time_ago': time_ago,
                        'hash': news_hash,
                        'category': category,
                        'importance_score': importance_score,
                        'recency_score': recency_score,
                        'total_score': total_score
                    }
                    
                    all_entries.append(entry_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            continue
    
    # Sort by combined score (importance + recency) - highest first
    all_entries.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Filter out duplicates and return top entries
    seen_hashes = set()
    filtered_entries = []
    
    for entry in all_entries:
        if entry['hash'] not in seen_hashes:
            seen_hashes.add(entry['hash'])
            filtered_entries.append(entry)
            
            if len(filtered_entries) >= target_count * 2:  # Get 2x target for good selection
                break
    
    return filtered_entries[:target_count * 2]  # Return double for variety

def format_news_section(section_title, entries, limit=5):
    """Format news entries prioritizing importance and recency, ensuring exactly 5 items."""
    formatted = f"*{section_title}:*\n"
    
    # Define fallback messages for each category
    category_fallbacks = {
        "🇧🇩 LOCAL NEWS": [
            "🔄 Latest breaking local news being monitored...",
            "📊 Local political developments being tracked...",
            "💼 Regional economic updates in progress...",
            "🏛️ Government policy updates being compiled...",
            "🌟 Community developments being monitored..."
        ],
        "🌍 GLOBAL NEWS": [
            "🌍 International breaking news being updated...",
            "🔥 Global crisis developments being tracked...", 
            "💸 World economic updates coming soon...",
            "🕊️ International affairs updates in progress...",
            "⚡ Breaking global events being monitored..."
        ],
        "🚀 TECH NEWS": [
            "💡 Latest technology breakthroughs being analyzed...",
            "🤖 AI and innovation updates coming soon...",
            "🔧 Tech industry developments being tracked...",
            "💰 Startup and venture updates in progress...",
            "📱 Digital transformation news being compiled..."
        ],
        "🏆 SPORTS NEWS": [
            "⚽ Live sports scores and updates being compiled...",
            "🏅 League standings and results coming soon...",
            "🔄 Player transfers and moves being tracked...",
            "🏟️ Tournament updates in progress...",
            "📈 Sports analysis and commentary being prepared..."
        ],
        "🪙 FINANCE & CRYPTO NEWS": [
            "📊 Cryptocurrency market movements being analyzed...",
            "🔗 DeFi protocol updates being tracked...",
            "⛓️ Blockchain developments coming soon...",
            "📜 Digital asset regulatory news in progress...",
            "💹 Crypto trading insights being compiled..."
        ]
    }
    
    count = 0
    
    # Sort entries by total score to get the most important ones first
    if entries:
        entries = sorted(entries, key=lambda x: x.get('total_score', 0), reverse=True)
    
    # First, add real news entries (prioritizing high-importance ones)
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
        
        # Add importance indicator for high-scoring news
        importance_score = entry.get('importance_score', 0)
        if importance_score > 15:
            indicator = "🔥 "  # Hot/breaking news
        elif importance_score > 10:
            indicator = "⚡ "  # Important news
        else:
            indicator = ""
        
        if link:
            formatted += f"{count}. {indicator}[{title_escaped}]({link}) - {source} ({time_ago})\n"
        else:
            formatted += f"{count}. {indicator}{title_escaped} - {source} ({time_ago})\n"
        
        # Mark as sent to prevent duplicates
        try:
            mark_news_as_sent(entry['hash'], title, source, entry.get('published', ''), entry.get('category', ''), link)
        except Exception as e:
            logger.debug(f"Error marking news as sent: {e}")
    
    # Fill remaining slots with fallback messages if needed
    fallback_messages = category_fallbacks.get(section_title, [
        "📰 News updates will be available shortly...",
        "🔍 Breaking news being monitored...",
        "📈 Latest developments being tracked...",
        "⏰ Updates coming soon...",
        "📝 News compilation in progress..."
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
    """Get breaking Bangladesh news from top sources."""
    bd_sources = {
        "The Daily Star": "https://www.thedailystar.net/frontpage/rss.xml",  # Most reliable for breaking news
        "BDNews24": "https://bdnews24.com/feed",  # Fast breaking news
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
        "Financial Express": "https://thefinancialexpress.com.bd/rss",
        "New Age": "http://www.newagebd.net/rss/rss.xml",
        "The Business Standard": "https://www.tbsnews.net/feed",
        "United News": "https://unb.com.bd/feed",
        "Dhaka Post": "https://www.dhakapost.com/rss.xml"
    }
    
    entries = fetch_breaking_news_rss(bd_sources, limit=30, category="local", target_count=5)
    return format_news_section("🇧🇩 LOCAL NEWS", entries, limit=5)

def get_breaking_global_news():
    """Get breaking global news from top international sources."""
    global_sources = {
        "Reuters": "http://feeds.reuters.com/reuters/topNews",  # Most reliable for breaking news
        "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
        "Associated Press": "https://feeds.apnews.com/rss/apf-topnews", 
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "NBC News": "https://feeds.nbcnews.com/nbcnews/public/news",
        "Sky News": "http://feeds.skynews.com/feeds/rss/world.xml",
        "France24": "https://www.france24.com/en/rss",
        "NPR": "https://feeds.npr.org/1001/rss.xml"
    }
    
    entries = fetch_breaking_news_rss(global_sources, limit=30, category="global", target_count=5)
    return format_news_section("🌍 GLOBAL NEWS", entries, limit=5)

def get_breaking_tech_news():
    """Get breaking technology news from top tech sources."""
    tech_sources = {
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",  # Best for breaking tech news
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index/",
        "Wired": "https://www.wired.com/feed/rss",
        "VentureBeat": "https://venturebeat.com/feed/",
        "Engadget": "https://www.engadget.com/rss.xml",
        "TechRadar": "https://www.techradar.com/rss",
        "ZDNet": "https://www.zdnet.com/news/rss.xml",
        "Gizmodo": "https://gizmodo.com/rss"
    }
    
    entries = fetch_breaking_news_rss(tech_sources, limit=25, category="tech", target_count=5)
    return format_news_section("🚀 TECH NEWS", entries, limit=5)

def get_breaking_sports_news():
    """Get breaking sports news from top sports sources."""
    sports_sources = {
        "ESPN": "https://www.espn.com/espn/rss/news",  # Best for breaking sports news
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "Sports Illustrated": "https://www.si.com/rss/si_topstories.rss",
        "Yahoo Sports": "https://sports.yahoo.com/rss/",
        "Sporting News": "https://www.sportingnews.com/rss",
        "Fox Sports": "https://www.foxsports.com/feeds/rss/1.0/sports-news",
        "CBS Sports": "https://www.cbssports.com/rss/headlines",
        "Sky Sports": "http://www.skysports.com/rss/12040",
        "The Athletic": "https://theathletic.com/rss/"
    }
    
    entries = fetch_breaking_news_rss(sports_sources, limit=25, category="sports", target_count=5)
    return format_news_section("🏆 SPORTS NEWS", entries, limit=5)

def get_breaking_crypto_news():
    """Get breaking cryptocurrency news from top crypto sources."""
    crypto_sources = {
        "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",  # Most reliable for breaking crypto news
        "Cointelegraph": "https://cointelegraph.com/rss",
        "The Block": "https://www.theblock.co/rss.xml",
        "Decrypt": "https://decrypt.co/feed",
        "Bitcoin Magazine": "https://bitcoinmagazine.com/feed",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "NewsBTC": "https://www.newsbtc.com/feed/",
        "CoinTelegraph": "https://cointelegraph.com/rss",
        "Crypto News": "https://cryptonews.com/news/feed/",
        "BeInCrypto": "https://beincrypto.com/feed/"
    }
    
    entries = fetch_breaking_news_rss(crypto_sources, limit=25, category="crypto", target_count=5)
    return format_news_section("🪙 FINANCE & CRYPTO NEWS", entries, limit=5)

# ===================== CRYPTO DATA WITH AI =====================

def fetch_crypto_market_with_ai():
    """Fetch crypto market data with comprehensive formatting including big cap, gainers, and losers."""
    try:
        # Fetch market overview
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()["data"]
        market_cap = data["total_market_cap"]["usd"]
        volume = data["total_volume"]["usd"]
        market_change = data["market_cap_change_percentage_24h_usd"]
        
        # Fetch top 50 cryptos for comprehensive data
        crypto_url = "https://api.coingecko.com/api/v3/coins/markets"
        crypto_params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h"
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
        
        # Format market cap and volume
        market_cap_str = f"${market_cap/1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap/1e9:.2f}B"
        volume_str = f"${volume/1e12:.2f}T" if volume >= 1e12 else f"${volume/1e9:.2f}B"
        
        # Build crypto section
        crypto_section = f"""💰 CRYPTO MARKET:
Market Cap (24h): {market_cap_str} ({market_change:+.2f}%)
Volume (24h): {volume_str}
Fear/Greed Index: {fear_index}/100

💎 Big Cap Crypto:
"""
        
        # Define specific big cap cryptos to display
        big_cap_targets = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH', 
            'ripple': 'XRP',
            'binancecoin': 'BNB',
            'solana': 'SOL',
            'tron': 'TRX',
            'dogecoin': 'DOGE',
            'cardano': 'ADA'
        }
        
        # Add big cap cryptos in order
        for crypto in crypto_data:
            if crypto['id'] in big_cap_targets:
                symbol = big_cap_targets[crypto['id']]
                price = crypto['current_price']
                change = crypto['price_change_percentage_24h'] or 0
                arrow = "▲" if change > 0 else "▼" if change < 0 else "→"
                
                # Format price appropriately
                if price >= 1000:
                    price_str = f"${price:,.2f}"
                elif price >= 1:
                    price_str = f"${price:.2f}"
                else:
                    price_str = f"${price:.4f}"
                
                crypto_section += f"{symbol}: {price_str} ({change:+.2f}%) {arrow}\n"
        
        # Sort by 24h change for gainers and losers
        sorted_cryptos = sorted([c for c in crypto_data if c['price_change_percentage_24h'] is not None], 
                               key=lambda x: x['price_change_percentage_24h'])
        
        # Top 5 gainers (highest positive changes)
        gainers = sorted_cryptos[-5:][::-1]  # Reverse to get highest first
        crypto_section += "\n� Crypto Top 5 Gainers:\n"
        for i, crypto in enumerate(gainers, 1):
            symbol = crypto['name']
            price = crypto['current_price']
            change = crypto['price_change_percentage_24h']
            arrow = "▲"
            
            # Format price appropriately
            if price >= 1000:
                price_str = f"${price:,.2f}"
            elif price >= 1:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.4f}"
            
            crypto_section += f"{i}. {symbol} {price_str} ({change:+.2f}%) {arrow}\n"
        
        # Top 5 losers (lowest negative changes)
        losers = sorted_cryptos[:5]
        crypto_section += "\n📉 Crypto Top 5 Losers:\n"
        for i, crypto in enumerate(losers, 1):
            symbol = crypto['name']
            price = crypto['current_price']
            change = crypto['price_change_percentage_24h']
            arrow = "▼"
            
            # Format price appropriately
            if price >= 1000:
                price_str = f"${price:,.2f}"
            elif price >= 1:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.4f}"
            
            crypto_section += f"{i}. {symbol} {price_str} ({change:+.2f}%) {arrow}\n"
        
        crypto_section += "\n"
        
        return crypto_section
        
    except Exception as e:
        logger.error(f"Error fetching crypto market data: {e}")
        return "💰 CRYPTO MARKET:\nMarket data temporarily unavailable.\n\n"

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
    """Get comprehensive Dhaka weather data with detailed formatting."""
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
        
        # Temperature data
        temp_c = current.get("temp_c", 0)
        condition = current.get("condition", {}).get("text", "N/A")
        humidity = current.get("humidity", 0)
        
        # Wind data
        wind_kph = current.get("wind_kph", 0)
        wind_dir = current.get("wind_dir", "N")
        
        # UV Index
        uv = current.get("uv", 0)
        
        # Air quality
        aqi_data = current.get("air_quality", {})
        us_epa = aqi_data.get("us-epa-index", 0)
        aqi_levels = {
            1: "Good", 2: "Moderate", 3: "Unhealthy for Sensitive", 
            4: "Unhealthy", 5: "Very Unhealthy", 6: "Hazardous"
        }
        aqi_text = aqi_levels.get(us_epa, "Moderate")
        
        weather_section = f"""�️ WEATHER - Dhaka:
🌡️ Temperature: {temp_c}°C
☁️ Condition: {condition}
💧 Humidity: {humidity}%
💨 Wind: {wind_kph} km/h {wind_dir}
☀️ UV Index: {uv}
🌬️ Air Quality: {aqi_text}

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
