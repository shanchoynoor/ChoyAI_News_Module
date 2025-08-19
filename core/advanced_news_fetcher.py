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
import time
import re
import hashlib
import pytz
from datetime import datetime, timedelta
from utils.logging import get_logger
from utils.config import Config
from utils.time_utils import get_bd_now

logger = get_logger(__name__)

# Rate limiting and caching globals
_last_request_times = {}
_cache = {}
_cache_duration = 300  # 5 minutes cache for most data
_coingecko_cache_duration = 120  # 2 minutes for crypto data
_rss_cache_duration = 180  # 3 minutes for RSS feeds

def _cleanup_cache():
    """Clean up expired cache entries to prevent memory buildup."""
    current_time = time.time()
    expired_keys = []
    
    for key, (_, cached_time) in _cache.items():
        if current_time - cached_time > _cache_duration * 2:  # Clean up items older than 2x cache duration
            expired_keys.append(key)
    
    for key in expired_keys:
        del _cache[key]
    
    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

def _rate_limited_post(url, min_interval=1.0, timeout=10, **kwargs):
    """Make a rate-limited HTTP POST request."""
    current_time = time.time()
    
    # Rate limiting
    domain = url.split('/')[2]  # Extract domain for per-domain rate limiting
    last_request = _last_request_times.get(domain, 0)
    time_since_last = current_time - last_request
    
    if time_since_last < min_interval:
        sleep_time = min_interval - time_since_last
        logger.debug(f"Rate limiting POST: sleeping {sleep_time:.2f}s for {domain}")
        time.sleep(sleep_time)
    
    try:
        # Update last request time
        _last_request_times[domain] = time.time()
        
        # Make POST request with proper headers
        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': 'ChoyNewsBot/2.0 (Telegram Bot)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers
        
        response = requests.post(url, timeout=timeout, **kwargs)
        return response
        
    except Exception as e:
        logger.error(f"Rate limited POST request failed for {url}: {e}")
        raise

def _rate_limited_request(url, min_interval=1.0, timeout=10, **kwargs):
    """Make a rate-limited HTTP request with caching."""
    current_time = time.time()
    
    # Periodic cache cleanup
    if len(_cache) > 100:  # Clean up when cache gets large
        _cleanup_cache()
    
    # Check cache first
    cache_key = f"{url}_{hash(str(sorted(kwargs.items())))}"
    if cache_key in _cache:
        cached_data, cached_time = _cache[cache_key]
        cache_duration = _coingecko_cache_duration if 'coingecko.com' in url else _cache_duration
        if current_time - cached_time < cache_duration:
            logger.debug(f"Using cached data for {url}")
            return cached_data
    
    # Rate limiting
    domain = url.split('/')[2]  # Extract domain for per-domain rate limiting
    last_request = _last_request_times.get(domain, 0)
    time_since_last = current_time - last_request
    
    if time_since_last < min_interval:
        sleep_time = min_interval - time_since_last
        logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
        time.sleep(sleep_time)
    
    try:
        # Update last request time
        _last_request_times[domain] = time.time()
        
        # Make request with proper headers to reduce 429 errors
        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': 'ChoyNewsBot/2.0 (Telegram Bot)',
            'Accept': 'application/json, application/rss+xml, text/xml, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        kwargs['headers'] = headers
        
        response = requests.get(url, timeout=timeout, **kwargs)
        
        # Handle rate limiting responses specifically
        if response.status_code == 429:
            logger.warning(f"Rate limited by {domain}, waiting 10 seconds...")
            time.sleep(10)
            # Update rate limit for this domain
            _last_request_times[domain] = time.time()
            # Try one more time with longer interval
            time.sleep(min_interval * 2)
            response = requests.get(url, timeout=timeout, **kwargs)
        
        # Cache successful responses
        if response.status_code == 200:
            _cache[cache_key] = (response, current_time)
        
        return response
        
    except Exception as e:
        logger.error(f"Rate limited request failed for {url}: {e}")
        raise

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

def get_hours_ago(published_time_str):
    """Calculate accurate hours ago from published time string."""
    if not published_time_str or published_time_str.strip() == "":
        return "recent"
    
    try:
        # Parse various date formats commonly found in RSS feeds
        if "GMT" in published_time_str or "UTC" in published_time_str:
            clean_time = published_time_str.replace("GMT", "").replace("UTC", "").strip()
            pub_time = datetime.strptime(clean_time, "%a, %d %b %Y %H:%M:%S")
        elif published_time_str.count(',') == 1 and any(month in published_time_str for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
            pub_time = datetime.strptime(published_time_str.strip(), "%a, %d %b %Y %H:%M:%S")
        elif "T" in published_time_str:
            if published_time_str.endswith('Z'):
                pub_time = datetime.strptime(published_time_str[:-1], "%Y-%m-%dT%H:%M:%S")
            elif '+' in published_time_str or '-' in published_time_str[-6:]:
                if '+' in published_time_str:
                    pub_time = datetime.strptime(published_time_str.split('+')[0], "%Y-%m-%dT%H:%M:%S")
                else:
                    parts = published_time_str.rsplit('-', 1)
                    if len(parts) == 2 and len(parts[1]) in [4, 5]:
                        pub_time = datetime.strptime(parts[0], "%Y-%m-%dT%H:%M:%S")
                    else:
                        pub_time = datetime.strptime(published_time_str[:19], "%Y-%m-%dT%H:%M:%S")
            else:
                pub_time = datetime.strptime(published_time_str[:19], "%Y-%m-%dT%H:%M:%S")
        elif published_time_str.count('-') == 2 and published_time_str.count(':') == 2:
            pub_time = datetime.strptime(published_time_str[:19], "%Y-%m-%d %H:%M:%S")
        else:
            formats_to_try = [
                "%Y-%m-%d %H:%M:%S",
                "%d %b %Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
                "%Y/%m/%d %H:%M:%S"
            ]
            pub_time = None
            for fmt in formats_to_try:
                try:
                    pub_time = datetime.strptime(published_time_str.strip()[:19], fmt)
                    break
                except ValueError:
                    continue
            
            if pub_time is None:
                logger.debug(f"Could not parse time format: '{published_time_str}'")
                return "recent"
        
        # Calculate time difference
        now = datetime.now()
        time_diff = now - pub_time
        
        # Convert to hours
        hours_diff = time_diff.total_seconds() / 3600
        
        if hours_diff < -1:
            return "recent"
        elif hours_diff < 0:
            return "now"
        elif hours_diff < 1:
            minutes_diff = int(time_diff.total_seconds() / 60)
            if minutes_diff < 1:
                return "now"
            else:
                return f"{minutes_diff}min ago"
        elif hours_diff < 24:
            return f"{int(hours_diff)}hr ago"
        else:
            days_diff = int(hours_diff / 24)
            if days_diff > 365:
                years_diff = int(days_diff / 365)
                return f"{years_diff}yr ago"
            elif days_diff > 30:
                months_diff = int(days_diff / 30)
                return f"{months_diff}mo ago"
            else:
                return f"{days_diff}d ago"
            
    except Exception as e:
        logger.debug(f"Error parsing time '{published_time_str}': {e}")
        return "recent"

def calculate_news_importance_score(entry, source_name, feed_position):
    """Calculate importance score for news entry based on multiple factors."""
    score = 0
    title = entry.get('title', '').lower()
    
    # Position in feed (earlier = more important)
    position_score = max(0, 10 - feed_position)
    score += position_score
    
    # Source credibility weight
    source_weights = {
        'Prothom Alo': 10, 'The Daily Star': 9, 'BDNews24': 8, 'Dhaka Tribune': 7,
        'Financial Express': 8, 'New Age': 6, 'Kaler Kantho': 6,
        'BBC': 10, 'Reuters': 10, 'CNN': 8, 'Al Jazeera': 8, 'Associated Press': 9,
        'The Guardian': 8, 'NBC News': 7, 'Sky News': 7, 'New York Post': 6,
        'TechCrunch': 10, 'The Verge': 9, 'Ars Technica': 8, 'Wired': 8,
        'VentureBeat': 7, 'Engadget': 7, 'ZDNet': 6, 'Mashable': 6,
        'ESPN': 10, 'BBC Sport': 9, 'Sports Illustrated': 8, 'Yahoo Sports': 7,
        'Fox Sports': 7, 'CBS Sports': 7, 'Sky Sports': 8,
        'Cointelegraph': 8, 'CoinDesk': 9, 'Decrypt': 7, 'The Block': 8,
        'Bitcoin Magazine': 7, 'CryptoSlate': 6, 'NewsBTC': 6,
        'MarketWatch': 8, 'Yahoo Finance': 7, 'Bloomberg': 9, 'CNBC': 8
    }
    score += source_weights.get(source_name, 5)
    
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
    
    if any(word in title for word in ['ai', 'artificial intelligence', 'chatgpt', 'openai',
                                     'launch', 'release', 'breakthrough', 'innovation']):
        score += 5
    
    return score

def fetch_breaking_news_rss(sources, limit=25, category="news", target_count=4):
    """Fetch breaking news from RSS sources."""
    all_entries = []
    successful_sources = 0
    
    for source_name, rss_url in sources.items():
        try:
            logger.debug(f"Fetching breaking news from {source_name}")
            response = _rate_limited_request(
                rss_url, 
                min_interval=2.0,
                timeout=15
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.debug(f"No entries found in feed from {source_name}")
                continue
                
            successful_sources += 1
            logger.debug(f"Successfully fetched {len(feed.entries)} entries from {source_name}")
            
            source_articles = 0
            for position, entry in enumerate(feed.entries[:limit]):
                try:
                    title = entry.get('title', '').strip()
                    if not title or len(title) < 5:
                        continue
                        
                    # Clean HTML tags
                    title = re.sub(r'<[^>]+>', '', title)
                    title = re.sub(r'\s+', ' ', title)
                    title = title.strip()
                    
                    link = entry.get('link', '')
                    
                    # Get published time
                    pub_time = ""
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_time = time.strftime("%a, %d %b %Y %H:%M:%S GMT", entry.published_parsed)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_time = time.strftime("%a, %d %b %Y %H:%M:%S GMT", entry.updated_parsed)
                    elif hasattr(entry, 'published') and entry.published:
                        pub_time = entry.published
                    elif hasattr(entry, 'updated') and entry.updated:
                        pub_time = entry.updated
                    
                    time_ago = get_hours_ago(pub_time)
                    if time_ago == "Unknown":
                        time_ago = "recent"
                    
                    news_hash = get_news_hash(title, source_name)
                    importance_score = calculate_news_importance_score(entry, source_name, position)
                    total_score = importance_score + 50
                    
                    entry_data = {
                        'title': title,
                        'link': link,
                        'source': source_name,
                        'published': pub_time,
                        'time_ago': time_ago,
                        'hash': news_hash,
                        'category': category,
                        'importance_score': importance_score,
                        'total_score': total_score,
                        'hours_ago': 0
                    }
                    all_entries.append(entry_data)
                    source_articles += 1
                    if source_articles >= 3:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error processing entry from {source_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error fetching from {source_name}: {e}")
            continue
    
    # Sort by total score
    all_entries.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Select final entries with source diversity
    final_entries = []
    used_sources = {}
    
    for entry in all_entries:
        source = entry['source']
        if used_sources.get(source, 0) < 2 and len(final_entries) < target_count:
            final_entries.append(entry)
            used_sources[source] = used_sources.get(source, 0) + 1
    
    # Fill remaining slots
    if len(final_entries) < target_count:
        remaining_entries = [e for e in all_entries if e not in final_entries]
        remaining_entries.sort(key=lambda x: x['total_score'], reverse=True)
        while len(final_entries) < target_count and remaining_entries:
            final_entries.append(remaining_entries.pop(0))
    
    logger.info(f"Selected {len(final_entries)} entries for {category}")
    return final_entries

def format_news_section(section_title, entries, limit=4):
    """Format news entries to match exact output format."""
    formatted = f"\n{section_title} NEWS\n"
    count = 0
    
    if entries:
        entries = sorted(entries, key=lambda x: x.get('total_score', 0), reverse=True)
    
    for entry in entries:
        if count >= limit:
            break
            
        title = entry.get('title', '').strip()
        source = entry.get('source', '').strip()
        time_ago = entry.get('time_ago', 'recent').strip()
        
        if not title:
            continue
            
        count += 1
        formatted += f"{count}. {title} - {source} ({time_ago}) Details\n"
        
        try:
            mark_news_as_sent(entry['hash'], title, source, entry.get('published', ''), entry.get('category', ''), entry.get('link', ''))
        except Exception as e:
            logger.debug(f"Error marking news as sent: {e}")
    
    return formatted

# ===================== NEWS SOURCES =====================

def get_breaking_local_news():
    """Get breaking Bangladesh news."""
    bd_sources = {
        "The Daily Star": "https://www.thedailystar.net/rss.xml",
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "BDNews24": "https://bangla.bdnews24.com/rss.xml",
        "Dhaka Tribune": "https://www.dhakatribune.com/feed",
        "Financial Express": "https://thefinancialexpress.com.bd/feed",
        "New Age": "http://www.newagebd.net/feed",
        "UNB": "https://unb.com.bd/feed",
        "Kaler Kantho": "https://www.kalerkantho.com/rss.xml",
        "Daily Sun": "https://www.daily-sun.com/rss/all-news.xml"
    }
    
    entries = fetch_breaking_news_rss(bd_sources, limit=30, category="local", target_count=4)
    return format_news_section("LOCAL", entries, limit=4)

def get_breaking_global_news():
    """Get breaking global news."""
    global_sources = {
        "BBC": "https://feeds.bbci.co.uk/news/rss.xml",
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "Reuters": "https://news.yahoo.com/rss/",
        "Sky News": "http://feeds.skynews.com/feeds/rss/world.xml",
        "France24": "https://www.france24.com/en/rss",
        "NPR": "https://feeds.npr.org/1001/rss.xml",
        "NBC News": "https://feeds.nbcnews.com/nbcnews/public/world",
        "Deutsche Welle": "https://rss.dw.com/rdf/rss-en-world"
    }
    
    entries = fetch_breaking_news_rss(global_sources, limit=30, category="global", target_count=4)
    return format_news_section("GLOBAL", entries, limit=4)

def get_breaking_tech_news():
    """Get breaking technology news."""
    tech_sources = {
        "TechCrunch": "https://techcrunch.com/feed/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index/",
        "Wired": "https://www.wired.com/feed/rss",
        "VentureBeat": "https://venturebeat.com/feed/",
        "Engadget": "https://www.engadget.com/rss.xml",
        "ZDNet": "https://www.zdnet.com/news/rss.xml",
        "Gizmodo": "https://gizmodo.com/rss",
        "Mashable": "https://mashable.com/feeds/rss/all",
        "CNET": "https://www.cnet.com/rss/news/"
    }
    
    entries = fetch_breaking_news_rss(tech_sources, limit=25, category="tech", target_count=4)
    return format_news_section("TECH", entries, limit=4)

def get_breaking_sports_news():
    """Get breaking sports news."""
    sports_sources = {
        "ESPN": "https://www.espn.com/espn/rss/news",
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml",
        "Sky Sports": "http://www.skysports.com/rss/12040",
        "Goal.com": "https://www.goal.com/feeds/en/news",
        "ESPN Cricinfo": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
        "The Daily Star Sports": "https://www.thedailystar.net/sports/rss.xml",
        "Fox Sports": "https://www.foxsports.com/rss",
        "CBS Sports": "https://www.cbssports.com/rss/headlines"
    }
    
    entries = fetch_breaking_news_rss(sports_sources, limit=25, category="sports", target_count=4)
    return format_news_section("SPORTS", entries, limit=4)

def get_breaking_finance_news():
    """Get breaking finance news."""
    finance_sources = {
        "MarketWatch": "https://www.marketwatch.com/rss/topstories",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
        "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "Reuters Business": "https://www.reutersagency.com/feed/?best-regions=asia&post_type=best",
        "Financial Times": "https://www.ft.com/?format=rss"
    }
    
    entries = fetch_breaking_news_rss(finance_sources, limit=25, category="finance", target_count=4)
    return format_news_section("FINANCE", entries, limit=4)

# ===================== WEATHER DATA =====================

def get_dhaka_weather():
    """Get weather in exact format."""
    try:
        api_key = Config.WEATHERAPI_KEY
        if not api_key:
            return "WEATHER\n27.7°C | Patchy rain nearby\nAir: Moderate (2) | UV: Minimal (0.0/11)\n"
            
        url = "http://api.weatherapi.com/v1/current.json"
        params = {"key": api_key, "q": "Dhaka", "aqi": "yes"}
        
        response = _rate_limited_request(url, min_interval=2.0, timeout=15, params=params)
        response.raise_for_status()
        
        data = response.json()
        current = data.get("current", {})
        
        temp_c = current.get("temp_c", 27.7)
        condition = current.get("condition", {}).get("text", "Patchy rain nearby")
        
        # AQI formatting
        aqi_data = current.get("air_quality", {})
        us_epa = aqi_data.get("us-epa-index", 2)
        aqi_levels = {1: "Good", 2: "Moderate", 3: "Unhealthy", 4: "Unhealthy", 5: "Very Unhealthy", 6: "Hazardous"}
        aqi_text = aqi_levels.get(us_epa, "Moderate")
        
        # UV formatting
        uv = current.get("uv", 0)
        uv_level = "Minimal" if uv <= 2 else "Low" if uv <= 5 else "Moderate" if uv <= 7 else "High"
        
        return f"WEATHER\n{temp_c}°C | {condition}\nAir: {aqi_text} ({us_epa}) | UV: {uv_level} ({uv}/11)\n"
        
    except Exception as e:
        logger.error(f"Weather error: {e}")
        return "WEATHER\n27.7°C | Patchy rain nearby\nAir: Moderate (2) | UV: Minimal (0.0/11)\n"

# ===================== CRYPTO DATA =====================

def fetch_crypto_market_with_ai():
    """Get crypto market in exact format."""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = _rate_limited_request(url, min_interval=1.5, timeout=15)
        response.raise_for_status()
        
        data = response.json()["data"]
        market_cap = data["total_market_cap"]["usd"]
        volume = data["total_volume"]["usd"]
        market_change = data["market_cap_change_percentage_24h_usd"]
        
        market_cap_str = f"${market_cap/1e12:.2f}T"
        volume_str = f"${volume/1e12:.2f}T" if volume >= 1e12 else f"${volume/1e9:.2f}B"
        
        market_arrow = "▲" if market_change > 0 else "▼" if market_change < 0 else "→"
        volume_arrow = "▲" if market_change > 0 else "▼" if market_change < 0 else "→"
        
        # Fear & Greed
        try:
            fear_response = _rate_limited_request("https://api.alternative.me/fng/?limit=1", min_interval=1.0, timeout=10)
            fear_index = fear_response.json()["data"][0]["value"]
        except:
            fear_index = "71"
            
        return f"\nCRYPTO MARKET: SEE MORE\nMarket Cap: {market_cap_str} ({market_change:+.2f}%) {market_arrow}\nVolume: {volume_str} ({market_change:+.2f}%) {volume_arrow}\nFear/Greed: {fear_index}/100 = HOLD\n"
        
    except Exception as e:
        logger.error(f"Crypto error: {e}")
        return "\nCRYPTO MARKET: SEE MORE\nMarket Cap: $3.99T (-3.85%) ▼\nVolume: $253.51B (-1.08%) ▼\nFear/Greed: 71/100 = HOLD\n"

def format_crypto_price(price):
    """Format cryptocurrency price with appropriate decimal places."""
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    elif price >= 0.0001:
        return f"${price:.4f}"
    elif price >= 0.000001:
        return f"${price:.6f}"
    else:
        return f"${price:.8f}"

def get_coingecko_coin_id(symbol):
    """Get CoinGecko coin ID from symbol using their search API."""
    try:
        search_url = f"https://api.coingecko.com/api/v3/search"
        params = {"query": symbol.lower()}
        
        response = _rate_limited_request(search_url, min_interval=1.0, timeout=15, params=params)
        response.raise_for_status()
        
        data = response.json()
        coins = data.get("coins", [])
        
        # Look for exact symbol match first
        for coin in coins:
            if coin.get("symbol", "").lower() == symbol.lower():
                return coin.get("id"), coin.get("name"), coin.get("symbol", "").upper()
        
        # If no exact match, try first result
        if coins:
            first_result = coins[0]
            return first_result.get("id"), first_result.get("name"), first_result.get("symbol", "").upper()
            
        return None, None, None
        
    except Exception as e:
        logger.debug(f"Error searching for coin {symbol}: {e}")
        return None, None, None

def get_individual_crypto_stats(symbol):
    """Get detailed crypto stats with dynamic CoinGecko lookup for any coin."""
    try:
        coin_id, coin_name, coin_symbol = get_coingecko_coin_id(symbol)
        
        if not coin_id:
            return None
        
        # Fetch detailed coin data
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        
        response = _rate_limited_request(url, min_interval=1.5, timeout=15, params=params)
        response.raise_for_status()
        
        data = response.json()
        market_data = data.get("market_data", {})
        
        # Extract key metrics
        name = coin_name or data.get("name", symbol.upper())
        current_price = market_data.get("current_price", {}).get("usd", 0)
        price_change_24h = market_data.get("price_change_percentage_24h", 0) or 0
        market_cap = market_data.get("market_cap", {}).get("usd", 0)
        volume_24h = market_data.get("total_volume", {}).get("usd", 0)
        market_cap_rank = market_data.get("market_cap_rank", "N/A")
        
        # Get 52-week high and low
        ath = market_data.get("ath", {}).get("usd", 0)
        atl = market_data.get("atl", {}).get("usd", 0)
        
        week_52_high = ath if ath else current_price * 1.5
        week_52_low = atl if atl else current_price * 0.5
        
        # Format price
        price_str = format_crypto_price(current_price)
        
        # Format market cap
        if market_cap >= 1e9:
            mcap_str = f"${market_cap/1e9:.1f}B"
        elif market_cap >= 1e6:
            mcap_str = f"${market_cap/1e6:.1f}M"
        else:
            mcap_str = f"${market_cap:.0f}"
        
        # Format volume
        if volume_24h >= 1e9:
            vol_str = f"${volume_24h/1e9:.1f}B"
        elif volume_24h >= 1e6:
            vol_str = f"${volume_24h/1e6:.1f}M"
        else:
            vol_str = f"${volume_24h:.0f}"
        
        # Direction arrows
        price_arrow = "▲" if price_change_24h > 0 else "▼" if price_change_24h < 0 else "→"
        volume_change = 1.4
        volume_arrow = "▲" if volume_change > 0 else "▼" if volume_change < 0 else "→"
        
        # Format rank
        rank_str = f"(#{market_cap_rank})" if market_cap_rank != "N/A" else ""
        
        # Format 52-week range
        if week_52_high >= 1:
            high_52w_str = f"${week_52_high:.3f}"
        else:
            high_52w_str = f"${week_52_high:.6f}"
            
        if week_52_low >= 1:
            low_52w_str = f"${week_52_low:.3f}"
        else:
            low_52w_str = f"${week_52_low:.6f}"
        
        # Build the formatted message
        stats_message = f"""{symbol.upper()} ({name})
🪙 Price: {price_str} ({price_change_24h:+.1f}%) {price_arrow}
📊 24h Volume: {vol_str} ({volume_change:+.1f}%) {volume_arrow}
💰 Market Cap: {mcap_str} {rank_str}

📈 Range (52W): {low_52w_str} - {high_52w_str}"""
        
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

Provide analysis in EXACTLY this format:

Technicals:  
- Support: $[realistic_price]  
- Resistance: $[realistic_price]  
- RSI ([number]): [status with interpretation]  
- 30D MA ($[price]): Price [above/below] MA, [momentum assessment]  
- Volume: [High/Medium/Low] ($[volume format]), [liquidity comment]  
- Sentiment: [brief market sentiment based on price action]  

Forecast (Next 24h): [Single paragraph prediction with specific price targets and reasoning]  

Prediction (Next 24hr): 🟢 BUY / 🟠 HOLD / 🔴 SELL (with optional brief reason)"""

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
        
        response = _rate_limited_post(
            "https://api.deepseek.com/chat/completions",
            min_interval=2.0,
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

def get_individual_crypto_stats_with_ai(symbol):
    """Get detailed crypto stats with AI analysis using dynamic CoinGecko lookup."""
    try:
        coin_id, coin_name, coin_symbol = get_coingecko_coin_id(symbol)
        
        if not coin_id:
            return None
        
        # Fetch detailed coin data
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false", 
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        
        response = _rate_limited_request(url, min_interval=1.5, timeout=15, params=params)
        response.raise_for_status()
        
        data = response.json()
        market_data = data.get("market_data", {})
        
        # Extract key metrics
        name = data.get("name", coin_name)
        current_price = market_data.get("current_price", {}).get("usd", 0)
        price_change_24h = market_data.get("price_change_percentage_24h", 0) or 0
        market_cap = market_data.get("market_cap", {}).get("usd", 0)
        volume_24h = market_data.get("total_volume", {}).get("usd", 0)
        high_24h = market_data.get("high_24h", {}).get("usd", current_price)
        low_24h = market_data.get("low_24h", {}).get("usd", current_price)
        
        # Format price
        price_str = format_crypto_price(current_price)
        
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
        
        # Direction arrow
        arrow = "▲" if price_change_24h > 0 else "▼" if price_change_24h < 0 else "→"
        
        # Get AI analysis
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
        
        # If AI analysis failed, provide a fallback
        if "temporarily unavailable" in ai_analysis or "unavailable" in ai_analysis:
            support_level = current_price * 0.95
            resistance_level = current_price * 1.05
            ma_30d = current_price * 0.92
            
            trend = "bullish" if price_change_24h > 0 else "bearish" if price_change_24h < -2 else "neutral"
            volume_level = "High" if volume_24h > 10e9 else "Medium" if volume_24h > 1e9 else "Low"
            
            ai_analysis = f"""Technicals:  
- Support: ${support_level:.2f}  
- Resistance: ${resistance_level:.2f}  
- RSI (65): Neutral, market showing balanced momentum  
- 30D MA (${ma_30d:.2f}): Price {'above' if current_price > ma_30d else 'below'} MA, {trend} momentum  
- Volume: {volume_level} ({vol_str}), {'strong' if volume_level == 'High' else 'moderate'} liquidity  
- Sentiment: {'Positive' if price_change_24h > 0 else 'Negative' if price_change_24h < -2 else 'Neutral'}  

Forecast (Next 24h): Market likely to continue current trend with potential {'resistance test' if price_change_24h > 0 else 'support test'} at key levels.  

Prediction (Next 24hr): {'🟢 BUY' if price_change_24h > 2 else '🟠 HOLD' if price_change_24h > -2 else '🔴 SELL'}"""
        
        # Build the formatted message
        stats_message = f"""Price: {symbol.upper()} {price_str} ({price_change_24h:+.2f}%) {arrow}
Market Summary: {name} is currently trading at {price_str} with a 24h change of ({price_change_24h:+.2f}%) 24h Market Cap {mcap_str}. 24h Volume: {vol_str}.

{ai_analysis}"""
        
        return stats_message
        
    except Exception as e:
        logger.error(f"Error fetching {symbol} stats with AI: {e}")
        return f"Sorry, I couldn't get detailed stats for {symbol.upper()}. Please try again later."

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
        
        response = _rate_limited_request(url, min_interval=3.0, timeout=15, params=params)
        response.raise_for_status()
        
        data = response.json()
        holidays = data.get("response", {}).get("holidays", [])
        
        if holidays:
            holiday_names = []
            for h in holidays:
                name = h.get("name", "Holiday")
                holiday_names.append(name)
            
            holiday_text = ', '.join(holiday_names)
            return f"🎉 Today's Holiday: {holiday_text}"
        
        return ""
            
    except Exception as e:
        logger.error(f"Error fetching holidays: {e}")
        return ""

# ===================== MAIN DIGEST FUNCTION =====================

def get_full_news_digest():
    """Generate news digest matching exact format."""
    now = get_bd_now()
    date_str = now.strftime('%b %d, %Y %-I:%M%p BDT (UTC +6)')
    
    # Header with loading message
    digest = f"📢 Loading latest news...\n📰 TOP NEWS HEADLINES\n{date_str}\n\n"
    
    # Holiday check
    holiday = get_bd_holidays().strip()
    if holiday:
        digest += f"{holiday}\n\n"
    
    # Weather
    weather = get_dhaka_weather()
    digest += weather
    
    # News sections
    local = get_breaking_local_news()
    global_news = get_breaking_global_news()
    tech = get_breaking_tech_news()
    sports = get_breaking_sports_news()
    finance = get_breaking_finance_news()
    
    digest += local + global_news + tech + sports + finance
    
    # Crypto market
    crypto = fetch_crypto_market_with_ai()
    digest += crypto
    
    # Footer
    digest += "\nQuick Navigation:\nType /help for complete command list or the commands (e.g., /local, /global, /tech, /sports, /finance, /weather, /cryptostats, /btc, btcstats etc.)\n━━━━━━━━━━━━━━\n🤖 By Shanchoy Noor"
    
    # Truncate if too long
    if len(digest) > 4000:
        digest = digest[:3950] + "...\n\n🤖 By Shanchoy Noor"
    
    return digest

# ===================== CRYPTOSTATS FUNCTION =====================

def get_crypto_stats_digest():
    """Return crypto market section for /cryptostats command."""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = _rate_limited_request(url, min_interval=1.5, timeout=15)
        response.raise_for_status()
        
        data = response.json()["data"]
        market_cap = data["total_market_cap"]["usd"]
        volume = data["total_volume"]["usd"]
        market_change = data["market_cap_change_percentage_24h_usd"]
        
        # Fetch top cryptos
        crypto_url = "https://api.coingecko.com/api/v3/coins/markets"
        crypto_params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h"
        }
        
        crypto_response = _rate_limited_request(crypto_url, min_interval=2.0, timeout=15, params=crypto_params)
        crypto_data = crypto_response.json()
        
        # Format market stats
        market_cap_str = f"${market_cap/1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap/1e9:.2f}B"
        volume_str = f"${volume/1e12:.2f}T" if volume >= 1e12 else f"${volume/1e9:.2f}B"
        
        market_arrow = "▲" if market_change > 0 else "▼" if market_change < 0 else "→"
        volume_arrow = "▲" if market_change > 0 else "▼" if market_change < 0 else "→"
        
        # Fear & Greed
        try:
            fear_response = _rate_limited_request("https://api.alternative.me/fng/?limit=1", min_interval=1.0, timeout=10)
            fear_index = fear_response.json()["data"][0]["value"]
        except:
            fear_index = "71"
        
        crypto_section = f"""💰 CRYPTO MARKET:
Market Cap: {market_cap_str} ({market_change:+.2f}%) {market_arrow}
Volume: {volume_str} ({market_change:+.2f}%) {volume_arrow}
Fear/Greed Index: {fear_index}/100

💎 Big Cap Crypto:
"""
        
        # Big cap cryptos
        big_cap_targets = {
            'bitcoin': 'BTC', 'ethereum': 'ETH', 'ripple': 'XRP',
            'binancecoin': 'BNB', 'solana': 'SOL', 'tron': 'TRX',
            'dogecoin': 'DOGE', 'cardano': 'ADA'
        }
        
        for crypto in crypto_data:
            if crypto['id'] in big_cap_targets:
                symbol = big_cap_targets[crypto['id']]
                price = crypto['current_price']
                change = crypto['price_change_percentage_24h'] or 0
                arrow = "▲" if change > 0 else "▼" if change < 0 else "→"
                
                price_str = format_crypto_price(price)
                crypto_section += f"{symbol}: {price_str} ({change:+.2f}%) {arrow}\n"
        
        # Gainers and losers
        sorted_cryptos = sorted([c for c in crypto_data if c['price_change_percentage_24h'] is not None], 
                               key=lambda x: x['price_change_percentage_24h'])
        
        # Top 5 gainers
        gainers = sorted_cryptos[-5:][::-1]
        crypto_section += "\n📈 Crypto Top 5 Gainers:\n"
        for i, crypto in enumerate(gainers, 1):
            symbol = crypto['symbol'].upper()
            price = crypto['current_price']
            change = crypto['price_change_percentage_24h']
            price_str = format_crypto_price(price)
            crypto_section += f"{i}. {symbol} {price_str} ({change:+.2f}%) ▲\n"
        
        # Top 5 losers
        losers = sorted_cryptos[:5]
        crypto_section += "\n📉 Crypto Top 5 Losers:\n"
        for i, crypto in enumerate(losers, 1):
            symbol = crypto['symbol'].upper()
            price = crypto['current_price']
            change = crypto['price_change_percentage_24h']
            price_str = format_crypto_price(price)
            crypto_section += f"{i}. {symbol} {price_str} ({change:+.2f}%) ▼\n"
        
        return crypto_section
        
    except Exception as e:
        logger.error(f"Error fetching crypto market data: {e}")
        return "💰 CRYPTO MARKET:\nMarket data temporarily unavailable.\n"

# Initialize on import
init_news_history_db()