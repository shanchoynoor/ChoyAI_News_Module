"""
News Digest Bot - A Telegram bot that provides daily news, cryptocurrency market data, and weather information.

This module provides functionality to fetch, format, and send daily news digests to Telegram users.
It includes features for tracking cryptocurrency prices, providing AI-based market analysis, and 
serving personalized news based on user preferences and timezone.

Author: Shanchoy
"""

# Standard library imports
import os
import re
import json
import time
import threading
import logging
import sqlite3
from datetime import datetime, timezone, timedelta

# Third-party imports
import requests
import feedparser
from pytz import timezone as pytz_timezone
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from timezonefinder import TimezoneFinder

# Local imports
from user_logging import init_db, log_user_interaction

# Configure logging
logging.basicConfig(level=logging.WARNING)

# Constants
SENT_NEWS_FILE = "sent_news.json"

# ===================== SENT NEWS PERSISTENCE =====================
def load_sent_news():
    """
    Load previously sent news links from file to avoid duplicates.
    
    Returns:
        set: A set of URLs that have already been sent to users
    """
    if not os.path.exists(SENT_NEWS_FILE):
        return set()
    try:
        with open(SENT_NEWS_FILE, "r") as f:
            return set(json.load(f))
    except Exception as e:
        logging.warning(f"Failed to load sent news: {e}")
        return set()

def save_sent_news(sent_links):
    """
    Save the set of sent news links to file for persistence.
    
    Args:
        sent_links (set): Set of URLs that have been sent to users
    """
    try:
        with open(SENT_NEWS_FILE, "w") as f:
            json.dump(list(sent_links), f)
    except Exception as e:
        logging.error(f"Failed to save sent news: {e}")

# ===================== MARKDOWN ESCAPE =====================
def escape_markdown_v2(text):
    """
    Escapes special characters for Telegram MarkdownV2 format.
    
    Args:
        text (str): The text to escape
        
    Returns:
        str: Escaped text safe for Telegram MarkdownV2 formatting
    """
    if not text:
        return ""
    escape_chars = r'_\*\[\]()~`>#+=|{}.!-'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# ===================== ENVIRONMENT VARIABLES =====================
# Load environment variables from .env file
load_dotenv()

# API Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FINNHUB_API = os.getenv("FINNHUB_API_KEY")

# ===================== UTILITIES =====================
def human_readable_number(num):
    """
    Format large numbers with currency suffixes for better readability.
    
    Args:
        num (float): The number to format
        
    Returns:
        str: Formatted string with appropriate suffix (K, M, B, T)
    
    Examples:
        >>> human_readable_number(1500)
        '$1.50K'
        >>> human_readable_number(1500000)
        '$1.50M'
    """
    abs_num = abs(num)
    if abs_num >= 1_000_000_000_000:
        return f"${num / 1_000_000_000_000:.2f}T"
    elif abs_num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"${num / 1_000:.2f}K"
    else:
        return f"${num:.2f}"

def send_telegram(msg, chat_id):
    """
    Send a message to a Telegram chat using the Telegram Bot API.
    
    Args:
        msg (str): The message text to send (supports Markdown formatting)
        chat_id (int): The Telegram chat ID to send the message to
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    r = requests.post(url, data=data)
    if not r.ok:
        logging.error(f"Telegram send failed: {r.text}")
    return r.ok

def get_hours_ago(published):
    """
    Convert a publication timestamp to a human-readable time difference string.
    
    Args:
        published (time.struct_time or tuple): Publication timestamp 
        
    Returns:
        str: A string like '2hr ago' or '3d ago', or None if invalid
        
    Examples:
        >>> get_hours_ago(time.struct_time([2025, 7, 7, 10, 0, 0, 0, 0, 0]))
        '24hr ago'  # if current time is July 8, 2025 10:00
    """
    try:
        if not published:
            return None
            
        # Convert input to datetime object
        if isinstance(published, time.struct_time):
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        elif isinstance(published, tuple):
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        else:
            return None
            
        # Calculate time difference
        now = datetime.now(timezone.utc)
        delta = now - dt
        
        # Skip invalid or very recent timestamps
        if delta.total_seconds() < 60 or delta.total_seconds() < 0:
            return None
            
        # Format the time difference
        hours = int(delta.total_seconds() // 3600)
        days = int(hours // 24)
        
        if days > 0:
            return f"{days}d ago"
        elif hours > 0:
            return f"{hours}hr ago"
        else:
            minutes = int((delta.total_seconds() % 3600) // 60)
            return f"{minutes}min ago"
    except Exception as e:
        logging.debug(f"Error calculating time difference: {e}")
        return None

# ===================== RSS FETCHING =====================
def fetch_rss_entries(sources, limit=5, max_per_source=3, max_age_hours=12):
    """
    Always return `limit` news entries per category.
    Strictly prefer the most recent news overall (from any source, max 3 per source).
    Only use older news if not enough recent items.
    """
    sent_links = load_sent_news()
    new_links = set()
    now = datetime.now(timezone.utc)
    min_timestamp = now.timestamp() - max_age_hours * 3600
    recent_entries = []
    older_entries = []

    def fetch_source(name_url):
        name, url = name_url
        results_recent = []
        results_older = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                published_parsed = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_parsed = entry.published_parsed
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published_parsed = entry.updated_parsed
                else:
                    for key in ['published', 'updated']:
                        try:
                            published_str = getattr(entry, key, None)
                            if published_str:
                                published_parsed = feedparser._parse_date(published_str)
                                if published_parsed:
                                    break
                        except Exception:
                            continue
                if not published_parsed:
                    continue
                published_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                title = escape_markdown_v2(getattr(entry, "title", "No Title").replace('[', '').replace(']', ''))
                link = getattr(entry, "link", "#")
                if link in sent_links or link == "#":
                    continue
                published_str = get_hours_ago(published_parsed)
                if not published_str:
                    continue
                entry_obj = {
                    "title": title,
                    "link": link,
                    "source": escape_markdown_v2(name),
                    "published": published_str,
                    "timestamp": published_dt.timestamp()
                }
                if published_dt.timestamp() >= min_timestamp:
                    results_recent.append(entry_obj)
                else:
                    results_older.append(entry_obj)
        except Exception as e:
            print(f"Error fetching {name}: {e}")
        # Sort by recency
        results_recent.sort(key=lambda x: x["timestamp"], reverse=True)
        results_older.sort(key=lambda x: x["timestamp"], reverse=True)
        return (results_recent, results_older)

    # Fetch all feeds in parallel
    with ThreadPoolExecutor(max_workers=min(8, len(sources))) as executor:
        futures = [executor.submit(fetch_source, item) for item in sources.items()]
        for future in as_completed(futures):
            recents, olders = future.result()
            recent_entries.extend(recents)
            older_entries.extend(olders)

    # Sort all recent entries by recency
    recent_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    older_entries.sort(key=lambda x: x["timestamp"], reverse=True)

    # Pick up to limit, max max_per_source per source, from recent_entries
    picked = []
    per_source_count = {}
    for entry in recent_entries:
        count = per_source_count.get(entry["source"], 0)
        if count < max_per_source and entry not in picked:
            picked.append(entry)
            per_source_count[entry["source"]] = count + 1
        if len(picked) >= limit:
            break
    # If still not enough, fill with older news (beyond max_age_hours), still respecting max_per_source
    if len(picked) < limit:
        for entry in older_entries:
            count = per_source_count.get(entry["source"], 0)
            if count < max_per_source and entry not in picked:
                picked.append(entry)
                per_source_count[entry["source"]] = count + 1
            if len(picked) >= limit:
                break
    # Save sent links
    for entry in picked:
        new_links.add(entry["link"])
    sent_links.update(new_links)
    save_sent_news(sent_links)
    # Remove timestamp before returning
    for entry in picked:
        entry.pop("timestamp", None)
    return picked

# ===================== BANGLA FONT CONVERSION =====================
def to_bangla(text):
    """Placeholder for Bangla font conversion (returns text as is)."""
    return text

# ===================== NEWS FORMATTING =====================
def format_news(title, entries, bangla=False):
    """Format news entries for display."""
    msg = f"*{title}:*\n"
    for idx, e in enumerate(entries, 1):
        display_title = to_bangla(e['title']) if bangla else e['title']
        msg += f"{idx}. [{display_title}]({e['link']}) - {e['source']} ({e['published']})\n"
    return msg + "\n"

# ===================== DEEPSEEK AI SUMMARY =====================
def get_crypto_summary_with_deepseek(market_cap, market_cap_change, volume, volume_change, fear_greed, big_caps, gainers, losers, api_key):
    """
    Generate a market summary and prediction using the DeepSeek AI API.
    
    Args:
        market_cap (str): Total market capitalization
        market_cap_change (str): Market cap 24h change percentage
        volume (str): 24h trading volume
        volume_change (str): Volume 24h change percentage
        fear_greed (str): Fear and Greed index value
        big_caps (str): Summary of big cap cryptocurrencies
        gainers (str): Top gaining cryptocurrencies
        losers (str): Top losing cryptocurrencies
        api_key (str): DeepSeek API key
        
    Returns:
        str: AI-generated market summary with prediction
    """
    # Construct prompt with market data
    prompt = (
        "Here is the latest crypto market data:\n"
        f"- Market Cap: {market_cap} ({market_cap_change})\n"
        f"- Volume: {volume} ({volume_change})\n"
        f"- Fear/Greed Index: {fear_greed}/100\n"
        f"- Big Cap Crypto: {big_caps}\n"
        f"- Top Gainers: {gainers}\n"
        f"- Top Losers: {losers}\n\n"
        "Write a short summary paragraph about the current crypto market status and predict if the market will be bullish or bearish tomorrow. "
        "Also, provide your confidence as a percentage (e.g., 75%) in your prediction. Be concise and insightful."
    )
    
    # API request setup
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120,
        "temperature": 0.7
    }
    
    # Make API request with error handling
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        logging.error("DeepSeek API request timed out")
        return "AI summary not available due to API timeout."
    except requests.exceptions.HTTPError as e:
        logging.error(f"DeepSeek API HTTP error: {e}")
        return f"AI summary not available due to API error: {e}"
    except Exception as e:
        logging.error(f"Error in DeepSeek API call: {str(e)}")
        try:
            logging.error(f"Response content: {response.text}")
        except:
            pass
        return "AI summary not available due to API error."

# ===================== NEWS CATEGORIES =====================
def get_local_news():
    """Fetch and format local Bangladeshi news."""
    bd_sources = {
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "BDNews24": "https://bdnews24.com/feed",
        "Bangladesh Pratidin": "https://www.bd-pratidin.com/rss.xml",
        "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
        "Jugantor": "https://www.jugantor.com/rss.xml",
        "Samakal": "https://samakal.com/rss.xml",
        "Jagonews24": "https://www.jagonews24.com/rss.xml",
        "Kaler Kantho": "https://www.kalerkantho.com/rss.xml",
        "Ittefaq": "https://www.ittefaq.com.bd/rss.xml",
        "Shomoy TV": "https://www.shomoynews.com/rss.xml",
    }
    return format_news("🇧🇩 LOCAL NEWS", fetch_rss_entries(bd_sources), bangla=True)

def get_global_news():
    """Fetch and format global news."""
    global_sources = {
        "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Reuters": "http://feeds.reuters.com/reuters/topNews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "New York Post": "https://nypost.com/feed/",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "The Washington Post": "https://feeds.washingtonpost.com/rss/world",
        "MSN": "https://www.msn.com/en-us/feed",
        "NBC News": "https://feeds.nbcnews.com/nbcnews/public/news",
        "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "The Economist": "https://www.economist.com/latest/rss.xml",
        "Axios": "https://www.axios.com/rss",
        "Fox News": "https://feeds.foxnews.com/foxnews/latest"
    }
    return format_news("🌍 GLOBAL NEWS", fetch_rss_entries(global_sources))

def get_tech_news():
    """Fetch and format technology news."""
    tech_sources = {
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Wired": "https://www.wired.com/feed/rss",
        "CNET": "https://www.cnet.com/rss/news/",
        "Social Media Today": "https://www.socialmediatoday.com/rss.xml",
        "Tech Times": "https://www.techtimes.com/rss/tech.xml",
        "Droid Life": "https://www.droid-life.com/feed/",
        "Live Science": "https://www.livescience.com/home/feed/site.xml",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
        "Engadget": "https://www.engadget.com/rss.xml",
        "Mashable": "https://mashable.com/feed",
        "Gizmodo": "https://gizmodo.com/rss",
        "ZDNet": "https://www.zdnet.com/news/rss.xml",
        "VentureBeat": "https://venturebeat.com/feed/",
        "The Next Web": "https://thenextweb.com/feed/",
        "TechRadar": "https://www.techradar.com/rss",
        "Android Authority": "https://www.androidauthority.com/feed",
        "MacRumors": "https://www.macrumors.com/macrumors.xml"
    }
    return format_news("🚀 TECH NEWS", fetch_rss_entries(tech_sources))

def get_sports_news():
    """Fetch and format sports news, prioritizing football, cricket, and celebrity news."""
    sports_sources = {
        "ESPN": "https://www.espn.com/espn/rss/news",
        "Sky Sports": "https://www.skysports.com/rss/12040",
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "NBC Sports": "https://scores.nbcsports.com/rss/headlines.asp",
        "Yahoo Sports": "https://sports.yahoo.com/rss/",
        "The Guardian Sport": "https://www.theguardian.com/sport/rss",
        "CBS Sports": "https://www.cbssports.com/rss/headlines/",
        "Bleacher Report": "https://bleacherreport.com/articles/feed",
        "Sports Illustrated": "https://www.si.com/rss/si_topstories.rss",
        "Reuters Sports": "http://feeds.reuters.com/reuters/sportsNews",
        "Fox Sports": "https://www.foxsports.com/feedout/syndicatedContent?categoryId=0",
        "USA Today Sports": "https://rssfeeds.usatoday.com/usatodaycomsports-topstories",
        "Sporting News": "https://www.sportingnews.com/us/rss",
        "Goal.com": "https://www.goal.com/en/feeds/news?fmt=rss",
        "NBA": "https://www.nba.com/rss/nba_rss.xml",
        "NFL": "http://www.nfl.com/rss/rsslanding?searchString=home"
    }
    all_entries = fetch_rss_entries(sports_sources, limit=20)  # Fetch more to allow filtering
    football_keywords = [
        'football', 'soccer', 'fifa', 'uefa', 'champions league', 'premier league', 'la liga', 'bundesliga',
        'serie a', 'euro', 'world cup', 'goal', 'match', 'fixture', 'score', 'draw', 'win', 'penalty', 'final',
        'quarterfinal', 'semifinal', 'tournament', 'cup', 'league', 'ronaldo', 'messi', 'mbappe', 'haaland', 'bellingham',
        'live', 'vs', 'minute', 'kick-off', 'halftime', 'fulltime', 'result', 'update', 'lineup', 'stadium', 'group', 'knockout'
    ]
    cricket_keywords = [
        'cricket', 'icc', 't20', 'odi', 'test', 'ipl', 'bpl', 'psl', 'cpl', 'big bash', 'wicket', 'run', 'six', 'four',
        'over', 'innings', 'batsman', 'bowler', 'all-rounder', 'match', 'score', 'result', 'final', 'semi-final', 'quarter-final',
        'world cup', 'asia cup', 'shakib', 'kohli', 'rohit', 'babar', 'warner', 'root', 'williamson', 'smith', 'starc', 'rashid',
        'live', 'vs', 'innings break', 'powerplay', 'chase', 'target', 'runs', 'wickets', 'umpire', 'no-ball', 'wide', 'out', 'not out', 'review', 'super over', 'rain', 'dl method', 'points table', 'series', 'trophy', 'stadium', 'captain', 'squad', 'team', 'playing xi', 'update', 'result', 'scorecard', 'highlights', 'stream', 'broadcast', 'telecast', 'coverage', 'commentary', 'fixture', 'schedule', 'venue', 'fans', 'crowd', 'tickets', 'stadium', 'pitch', 'toss', 'bat', 'bowl', 'field', 'catch', 'drop', 'boundary', 'partnership', 'century', 'fifty', 'duck', 'debut', 'retire', 'injury', 'suspension', 'ban', 'controversy', 'award', 'record', 'milestone', 'legend', 'icon', 'star', 'hero', 'superstar', 'profile', 'tribute', 'obituary', 'death', 'birthday', 'marriage', 'divorce'
    ]
    def is_football(entry):
        title = entry['title'].lower()
        return any(kw in title for kw in football_keywords)
    def is_cricket(entry):
        title = entry['title'].lower()
        return any(kw in title for kw in cricket_keywords)
    football_news = [e for e in all_entries if is_football(e)]
    cricket_news = [e for e in all_entries if is_cricket(e) and e not in football_news]
    top_football = football_news[:2]
    top_cricket = cricket_news[:1]
    celebrity_keywords = [
        'star', 'legend', 'coach', 'manager', 'transfer', 'sign', 'deal', 'injury', 'scandal', 'award', 'record',
        'retire', 'comeback', 'controversy', 'ban', 'suspension', 'mvp', 'gold', 'silver', 'bronze', 'medal',
        'olympic', 'world record', 'breaking', 'exclusive', 'statement', 'announcement', 'trending', 'viral', 'hot',
        'player', 'celebrity', 'icon', 'hero', 'captain', 'superstar', 'profile', 'tribute', 'obituary', 'death', 'birthday', 'marriage', 'divorce'
    ]
    def is_celebrity(entry):
        title = entry['title'].lower()
        return any(kw in title for kw in celebrity_keywords)
    celebrity_news = [e for e in all_entries if is_celebrity(e) and e not in top_football and e not in top_cricket]
    top_celebrity = celebrity_news[:2]
    other_news = [e for e in all_entries if e not in top_football and e not in top_cricket and e not in top_celebrity]
    picked = top_football + top_cricket + top_celebrity
    if len(picked) < 5:
        picked += other_news[:5-len(picked)]
    return format_news("🏆 SPORTS NEWS", picked)

def get_crypto_news():
    """Fetch and format crypto and finance news."""
    crypto_sources = {
        "Cointelegraph": "https://cointelegraph.com/rss",
        "Decrypt": "https://decrypt.co/feed",
        "Coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "Forbes Crypto": "https://www.forbes.com/crypto-blockchain/feed/",
        "Bloomberg Crypto": "https://www.bloomberg.com/crypto/rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "CNBC Finance": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "Financial Times": "https://www.ft.com/?format=rss",
        "MarketWatch": "https://www.marketwatch.com/rss/topstories",
        "Bloomberg Markets": "https://www.bloomberg.com/feed/podcast/etf-report.xml",
        "The Block": "https://www.theblock.co/rss",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
        "Investing.com": "https://www.investing.com/rss/news_301.rss"
    }
    return format_news("🪙  FINANCE & CRYPTO NEWS", fetch_rss_entries(crypto_sources))

# ===================== CRYPTO DATA =====================
def fetch_crypto_market():
    """Fetch and format global crypto market data."""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        resp = requests.get(url)
        if not resp.ok:
            raise Exception("CoinGecko API error")
        data = resp.json().get("data", {})
        market_cap = data.get("total_market_cap", {}).get("usd")
        volume = data.get("total_volume", {}).get("usd")
        market_change = data.get("market_cap_change_percentage_24h_usd")
        if None in (market_cap, volume, market_change):
            raise Exception("Missing market data")
        volume_yesterday = volume / (1 + market_change / 100)
        volume_change = ((volume - volume_yesterday) / volume_yesterday) * 100
        # Fear/Greed index
        try:
            fg_resp = requests.get("https://api.alternative.me/fng/?limit=1")
            fg_data = fg_resp.json().get("data", [{}])
            fear_index = fg_data[0].get("value")
            if not fear_index or not str(fear_index).isdigit():
                fear_index = "N/A"
        except Exception:
            fear_index = "N/A"
        market_cap_str = human_readable_number(market_cap) if market_cap else "N/A"
        market_cap_change_str = f"{market_change:+.2f}%" if market_change is not None else "N/A"
        volume_str = human_readable_number(volume) if volume else "N/A"
        volume_change_str = f"{volume_change:+.2f}%" if volume_change is not None else "N/A"
        fear_greed_str = str(fear_index)
        return (market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, market_cap, market_change, volume, volume_change, fear_index)
    except Exception:
        return ("N/A", "N/A", "N/A", "N/A", "N/A", 0, 0, 0, 0, 0)

def fetch_big_cap_prices():
    """Fetch and format big cap crypto prices."""
    ids = "bitcoin,ethereum,ripple,binancecoin,solana,tron,dogecoin,cardano"
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": ids}
        resp = requests.get(url, params=params)
        data = resp.json()
        if not isinstance(data, list):
            raise Exception("Invalid CoinGecko response")
        msg = "*💎 Crypto Big Cap:*\n"
        big_caps_list = []
        for c in data:
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            big_caps_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        return msg + "\n", ", ".join(big_caps_list)
    except Exception:
        return "*Crypto Big Cap:*\nN/A\n\n", "N/A"

def fetch_top_movers():
    """
    Fetch and format top crypto gainers and losers for display in the news digest.
    
    Returns:
        str: Formatted markdown string with top gainers and losers information
    """
    try:
        msg, _, _ = fetch_top_movers_data()
        return msg
    except Exception as e:
        logging.error(f"Error in fetch_top_movers: {e}")
        return "*Top Movers:* Data unavailable\n\n"

def fetch_crypto_market_data():
    """
    Fetch global cryptocurrency market data from CoinGecko and Fear & Greed Index.
    Uses caching to reduce API calls and provide fallback data if API is unavailable.
    
    Returns:
        tuple: Contains the following elements:
            - market_cap_str (str): Formatted market cap with currency symbol
            - market_cap_change_str (str): 24h market cap change percentage
            - volume_str (str): Formatted 24h trading volume with currency symbol
            - volume_change_str (str): 24h volume change percentage
            - fear_greed_str (str): Fear and Greed index value (0-100)
            - market_cap (float): Raw market cap value
            - market_change (float): Raw market cap change percentage
            - volume (float): Raw trading volume value
            - volume_change (float): Raw volume change percentage
            - fear_greed (int): Raw Fear and Greed index value
    """
    # Import crypto cache module
    try:
        import crypto_cache
        # Check if we have cached data
        cached_data = crypto_cache.get_market_cache()
        if cached_data:
            logging.info("Using cached market data")
            return cached_data
    except ImportError:
        logging.warning("crypto_cache module not found, proceeding without caching")
    except Exception as e:
        logging.error(f"Error accessing market cache: {e}")
    
    # Initialize with default values in case of failure
    result = ("N/A", "N/A", "N/A", "N/A", "N/A", 0, 0, 0, 0, 0)
    
    try:
        # Fetch global market data from CoinGecko with retries
        url = "https://api.coingecko.com/api/v3/global"
        headers = {"Accept": "application/json", "User-Agent": "News Digest Bot/1.0"}
        
        # Try up to 3 times with increasing delays
        max_retries = 3
        for retry in range(max_retries):
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.ok:
                    break
                elif resp.status_code == 429:  # Rate limit exceeded
                    wait_time = min(2 ** retry, 8)  # Exponential backoff: 1, 2, 4, 8 seconds
                    logging.warning(f"Rate limit hit, waiting {wait_time}s before retry {retry+1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"CoinGecko API error: {resp.status_code} - {resp.text[:100]}")
                    if retry < max_retries - 1:
                        time.sleep(1)
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error on attempt {retry+1}: {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
        
        # If we couldn't get a successful response after all retries
        if not resp.ok:
            logging.error(f"Failed to fetch market data after {max_retries} attempts")
            raise Exception(f"CoinGecko API error: {resp.status_code}")
            
        # Extract relevant data points
        data = resp.json().get("data", {})
        market_cap = data.get("total_market_cap", {}).get("usd")
        volume = data.get("total_volume", {}).get("usd")
        market_change = data.get("market_cap_change_percentage_24h_usd")
        
        if None in (market_cap, volume, market_change):
            logging.error("Missing market data from CoinGecko response")
            raise Exception("Missing market data")
            
        # Calculate volume change using market cap change as reference
        # (volume yesterday = today's volume / (1 + market_change/100))
        volume_yesterday = volume / (1 + market_change / 100)
        volume_change = ((volume - volume_yesterday) / volume_yesterday) * 100
        
        # Fetch Fear & Greed Index with retries
        fear_index = "N/A"
        for retry in range(max_retries):
            try:
                fg_resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
                if fg_resp.ok:
                    fg_data = fg_resp.json().get("data", [{}])
                    fear_index = fg_data[0].get("value")
                    if fear_index and str(fear_index).isdigit():
                        break
                    else:
                        logging.warning("Invalid Fear & Greed index value")
                        fear_index = "N/A"
                else:
                    logging.error(f"Fear & Greed API error: {fg_resp.status_code}")
                    if retry < max_retries - 1:
                        time.sleep(1)
            except Exception as e:
                logging.error(f"Error fetching Fear & Greed index (attempt {retry+1}): {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
        
        # Format values for display
        market_cap_str = human_readable_number(market_cap) if market_cap else "N/A"
        market_cap_change_str = f"{market_change:+.2f}%" if market_change is not None else "N/A"
        volume_str = human_readable_number(volume) if volume else "N/A"
        volume_change_str = f"{volume_change:+.2f}%" if volume_change is not None else "N/A"
        fear_greed_str = str(fear_index)
        
        # Create the result tuple
        result = (market_cap_str, market_cap_change_str, volume_str, volume_change_str, 
                fear_greed_str, market_cap, market_change, volume, volume_change, 
                int(fear_index) if fear_index != "N/A" else 0)
        
        # Cache the successful result
        try:
            import crypto_cache
            crypto_cache.save_market_cache(result)
            logging.info("Successfully cached market data")
        except Exception as e:
            logging.error(f"Error caching market data: {e}")
        
        return result
                
    except Exception as e:
        logging.error(f"Failed to fetch crypto market data: {e}")
        return result

def fetch_big_cap_prices_data():
    """
    Fetch and format big cap crypto prices.
    Uses caching to reduce API calls and provide fallback data if API is unavailable.
    
    Returns:
        tuple: (formatted_message, comma_separated_string)
    """
    # Check for cached data first
    try:
        import crypto_cache
        cached_data = crypto_cache.get_bigcap_cache()
        if cached_data:
            logging.info("Using cached big cap prices data")
            return cached_data
    except ImportError:
        logging.warning("crypto_cache module not found, proceeding without caching")
    except Exception as e:
        logging.error(f"Error accessing big cap cache: {e}")
    
    # Default fallback result
    default_result = ("*💎 Crypto Big Cap:*\nN/A\n\n", "N/A")
    
    ids = "bitcoin,ethereum,ripple,binancecoin,solana,tron,dogecoin,cardano"
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": ids}
        headers = {"Accept": "application/json", "User-Agent": "News Digest Bot/1.0"}
        
        # Try up to 3 times with increasing delays
        max_retries = 3
        for retry in range(max_retries):
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=15)
                if resp.ok:
                    break
                elif resp.status_code == 429:  # Rate limit exceeded
                    wait_time = min(2 ** retry, 8)  # Exponential backoff
                    logging.warning(f"Rate limit hit, waiting {wait_time}s before retry {retry+1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"CoinGecko API error: {resp.status_code} - {resp.text[:100]}")
                    if retry < max_retries - 1:
                        time.sleep(1)
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error on attempt {retry+1}: {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
        
        # If we couldn't get a successful response after all retries
        if not resp.ok:
            logging.error(f"Failed to fetch big cap prices after {max_retries} attempts")
            return default_result
            
        data = resp.json()
        if not isinstance(data, list):
            logging.error(f"Invalid CoinGecko response format: {type(data)}")
            return default_result
            
        if len(data) == 0:
            logging.error("Empty response from CoinGecko API")
            return default_result
            
        msg = "*💎 Crypto Big Cap:*\n"
        big_caps_list = []
        for c in data:
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            big_caps_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        
        result = (msg + "\n", ", ".join(big_caps_list))
        
        # Cache the successful result
        try:
            import crypto_cache
            crypto_cache.save_bigcap_cache(result)
            logging.info("Successfully cached big cap prices data")
        except Exception as e:
            logging.error(f"Error caching big cap prices data: {e}")
            
        return result
    except Exception as e:
        logging.error(f"Failed to fetch big cap prices: {e}")
        return default_result

def fetch_top_movers_data():
    """Fetch and format top crypto gainers and losers from top 500 coins by market cap.
    Uses caching to reduce API calls and provide fallback data if API is unavailable.
    
    Returns:
        tuple: (formatted_message, gainers_string, losers_string)
            - formatted_message: Markdown-formatted string with top gainers and losers
            - gainers_string: Comma-separated string of top gainers
            - losers_string: Comma-separated string of top losers
    """
    # Default fallback values
    default_result = ("*🔺 Crypto Top Movers:*\nData temporarily unavailable\n\n", "N/A", "N/A")
    
    # Check for cached data first
    try:
        import crypto_cache
        cached_data = crypto_cache.get_movers_cache()
        if cached_data:
            logging.info("Using cached top movers data")
            return cached_data
    except ImportError:
        logging.warning("crypto_cache module not found, proceeding without caching")
    except Exception as e:
        logging.error(f"Error accessing top movers cache: {e}")
    
    try:
        # Fetch top 500 coins (2 pages, 250 per page)
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params1 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1}
        params2 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 2}
        headers = {"Accept": "application/json", "User-Agent": "News Digest Bot/1.0"}
        
        # Add timeout to avoid hanging requests
        timeout_seconds = 15
        
        # Get first page with improved error handling and retries
        max_retries = 3
        data1 = []
        
        for retry in range(max_retries):
            try:
                resp1 = requests.get(url, params=params1, headers=headers, timeout=timeout_seconds)
                if resp1.ok:
                    data1 = resp1.json()
                    if not isinstance(data1, list):
                        logging.error(f"CoinGecko API returned non-list for page 1: {type(data1)}")
                        data1 = []
                    else:
                        break
                elif resp1.status_code == 429:  # Rate limit exceeded
                    wait_time = min(2 ** retry, 8)  # Exponential backoff
                    logging.warning(f"Rate limit hit, waiting {wait_time}s before retry {retry+1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"CoinGecko API error (page 1): Status {resp1.status_code}, Response: {resp1.text[:100]}")
                    if retry < max_retries - 1:
                        time.sleep(1)
            except Exception as e:
                logging.error(f"Error fetching CoinGecko page 1 (attempt {retry+1}): {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
        
        # If we couldn't get data from page 1, try to use cache or return default
        if len(data1) == 0:
            logging.error("Failed to fetch data for page 1 after multiple attempts")
            return default_result
            
        # Short delay to avoid rate limiting
        time.sleep(1)
        
        # Get second page with improved error handling and retries
        data2 = []
        for retry in range(max_retries):
            try:
                resp2 = requests.get(url, params=params2, headers=headers, timeout=timeout_seconds)
                if resp2.ok:
                    data2 = resp2.json()
                    if not isinstance(data2, list):
                        logging.error(f"CoinGecko API returned non-list for page 2: {type(data2)}")
                        data2 = []
                    else:
                        break
                elif resp2.status_code == 429:  # Rate limit exceeded
                    wait_time = min(2 ** retry, 8)  # Exponential backoff
                    logging.warning(f"Rate limit hit, waiting {wait_time}s before retry {retry+1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"CoinGecko API error (page 2): Status {resp2.status_code}, Response: {resp2.text[:100]}")
                    if retry < max_retries - 1:
                        time.sleep(1)
            except Exception as e:
                logging.error(f"Error fetching CoinGecko page 2 (attempt {retry+1}): {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
        
        # Combine data from both pages
        data = data1 + data2
        
        # Check if we have enough data to show meaningful results
        # Even if page 2 failed, we can still proceed with page 1 data only
        if len(data) == 0:
            logging.error("No valid data received from CoinGecko API for top movers")
            return default_result
            
        logging.info(f"Successfully fetched {len(data)} coins for top movers analysis")
        
        # Filter out entries with missing price change data
        valid_data = [coin for coin in data if coin.get("price_change_percentage_24h") is not None]
        
        # Need at least 10 coins to show 5 gainers and 5 losers
        if len(valid_data) < 10:
            logging.error(f"Not enough coins with valid price change data: {len(valid_data)}")
            return default_result
            
        # Sort for gainers and losers
        gainers = sorted(valid_data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
        losers = sorted(valid_data, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]
        
        # Format gainers
        msg = "*🔺 Crypto Top Gainers:*\n"
        gainers_list = []
        for i, c in enumerate(gainers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            gainers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        
        # Format losers
        msg += "\n*🔻 Crypto Top Losers:*\n"
        losers_list = []
        for i, c in enumerate(losers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            losers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        
        result = (msg + "\n", ", ".join(gainers_list), ", ".join(losers_list))
        
        # Cache the successful result
        try:
            import crypto_cache
            crypto_cache.save_movers_cache(result)
            logging.info("Successfully cached top movers data")
        except Exception as e:
            logging.error(f"Error caching top movers data: {e}")
            
        return result
    except Exception as e:
        logging.error(f"Unexpected error in fetch_top_movers_data: {e}")
        return default_result

# ===================== WEATHER =====================
def get_dhaka_weather():
    try:
        api_key = os.getenv("WEATHERAPI_KEY")
        if not api_key:
            return "🌦️ Dhaka: Weather N/A"
        url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q=Dhaka&days=1&aqi=yes&alerts=no"
        resp = requests.get(url)
        data = resp.json()
        forecast = data["forecast"]["forecastday"][0]
        day = forecast["day"]
        temp_min = day["mintemp_c"]
        temp_max = day["maxtemp_c"]
        rain_chance = day.get("daily_chance_of_rain", 0)
        uv_val = day.get("uv", "N/A")
        aq = data.get("current", {}).get("air_quality", {})
        pm25 = aq.get("pm2_5")
        def pm25_to_aqi(pm25):
            breakpoints = [
                (0.0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 500.4, 301, 500)
            ]
            try:
                pm25 = float(pm25)
                for bp in breakpoints:
                    if bp[0] <= pm25 <= bp[1]:
                        Clow, Chigh, Ilow, Ihigh = bp[0], bp[1], bp[2], bp[3]
                        aqi = ((Ihigh - Ilow) / (Chigh - Clow)) * (pm25 - Clow) + Ilow
                        return round(aqi)
            except Exception:
                pass
            return None
        aqi_val = None
        if pm25 is not None:
            aqi_val = pm25_to_aqi(pm25)
        if aqi_val is None:
            epa_index = aq.get("us-epa-index")
            if epa_index is not None:
                epa_index = int(epa_index)
                if epa_index == 1:
                    aqi_val = 50
                elif epa_index == 2:
                    aqi_val = 100
                elif epa_index == 3:
                    aqi_val = 150
                elif epa_index == 4:
                    aqi_val = 200
                elif epa_index == 5:
                    aqi_val = 300
                elif epa_index == 6:
                    aqi_val = 400
        if aqi_val is not None:
            if aqi_val <= 50:
                aq_str = "Good"
            elif aqi_val <= 100:
                aq_str = "Moderate"
            elif aqi_val <= 150:
                aq_str = "Unhealthy for Sensitive Groups"
            elif aqi_val <= 200:
                aq_str = "Unhealthy"
            elif aqi_val <= 300:
                aq_str = "Very Unhealthy"
            else:
                aq_str = "Hazardous"
        else:
            aq_str = "N/A"
            aqi_val = "N/A"
        try:
            uv_val_num = float(uv_val)
            if uv_val_num < 3:
                uv_str = "Low"
            elif uv_val_num < 6:
                uv_str = "Moderate"
            elif uv_val_num < 8:
                uv_str = "High"
            elif uv_val_num < 11:
                uv_str = "Very High"
            else:
                uv_str = "Extreme"
        except Exception:
            uv_str = str(uv_val)
        rain_emoji = "🌧️ "
        aq_emoji = "🫧 "
        uv_emoji = "🔆 "
        lines = [
            f"🌦️ Dhaka: {temp_min:.1f}°C ~ {temp_max:.1f}°C",
            f"{rain_emoji}Rain: {rain_chance}%",
            f"{aq_emoji}AQI: {aq_str} ({aqi_val})",
            f"{uv_emoji}UV: {uv_str} ({uv_val})"
        ]
        return "\n".join(lines)
    except Exception:
        return "🌦️ Dhaka: Weather N/A"

# ===================== COINLIST LOADING =====================
COINLIST_PATH = os.path.join(os.path.dirname(__file__), "coinlist.json")
_coinlist_cache = None
_coinlist_lock = threading.Lock()
def load_coinlist():
    global _coinlist_cache
    with _coinlist_lock:
        if _coinlist_cache is not None:
            return _coinlist_cache
        try:
            with open(COINLIST_PATH, "r") as f:
                _coinlist_cache = json.load(f)
        except Exception as e:
            print(f"Failed to load coinlist.json: {e}")
            _coinlist_cache = []
        return _coinlist_cache

# Helper: symbol to id lookup (case-insensitive)
def get_coin_id_from_symbol(symbol):
    coinlist = load_coinlist()
    symbol = symbol.lower()
    for c in coinlist:
        if c.get("symbol", "").lower() == symbol:
            logging.debug(f"Found symbol: {symbol} -> {c['id']}")
            return c["id"], c["name"]
    logging.debug(f"Symbol not found: {symbol}")
    return None, None

# ===================== USER TIMEZONE STORAGE =====================
USER_TZ_DB = "user_timezones.db"

def set_user_timezone(user_id, tz_str):
    """
    Store a user's preferred timezone in the database.
    
    Args:
        user_id (int): Telegram user ID
        tz_str (str): Timezone string (e.g., 'Asia/Dhaka', 'Europe/London')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(USER_TZ_DB)
        c = conn.cursor()
        # Create table if it doesn't exist
        c.execute("CREATE TABLE IF NOT EXISTS user_timezones (user_id INTEGER PRIMARY KEY, tz TEXT)")
        # Insert or update user's timezone
        c.execute("INSERT OR REPLACE INTO user_timezones (user_id, tz) VALUES (?, ?)", (user_id, tz_str))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Failed to set user timezone: {e}")
        return False

def get_user_timezone(user_id):
    """
    Retrieve a user's preferred timezone from the database.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        str: Timezone string if found, None otherwise
    """
    try:
        conn = sqlite3.connect(USER_TZ_DB)
        c = conn.cursor()
        # Create table if it doesn't exist
        c.execute("CREATE TABLE IF NOT EXISTS user_timezones (user_id INTEGER PRIMARY KEY, tz TEXT)")
        # Query user's timezone
        c.execute("SELECT tz FROM user_timezones WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return None
    except Exception as e:
        logging.error(f"Failed to get user timezone: {e}")
        return None

# ===================== TIME =====================
def parse_timezone_input(tz_input):
    tz_input = tz_input.strip().lower()
    # Try UTC offset: +6, -5.5, etc.
    if tz_input.startswith("+utc"):
        tz_input = tz_input[4:].strip()
    if tz_input.startswith("+") or tz_input.startswith("-"):
        try:
            offset = float(tz_input)
            hours = int(offset)
            minutes = int((abs(offset) * 60) % 60)
            sign = "+" if offset >= 0 else "-"
            tz_name = f"Etc/GMT{sign}{abs(hours):d}"
            # Note: Etc/GMT+6 is actually UTC-6, so reverse sign
            tz_name = f"Etc/GMT{'-' if sign == '+' else '+'}{abs(hours):d}"
            return tz_name
        except Exception:
            pass
    # Try city or TZ database name
    from pytz import all_timezones
    # Try exact match
    for tz in all_timezones:
        if tz_input == tz.lower():
            return tz
    # Try partial match (city)
    for tz in all_timezones:
        if tz_input in tz.lower():
            return tz
    return None

def get_local_time_str(user_location=None, user_id=None):
    """Return current time string in user's local timezone (e.g. Jul 7, 2025 8:38PM BST (UTC +1)).
    
    Args:
        user_location (dict, optional): Dictionary containing latitude and longitude.
        user_id (int, optional): User ID to look up timezone preference.
        
    Returns:
        str: Formatted time string with timezone abbreviation and UTC offset.
    """
    try:
        tz_str = None
        if user_id:
            tz_str = get_user_timezone(user_id)
        
        # Default to Dhaka if no timezone specified
        if not tz_str:
            tz_str = 'Asia/Dhaka'
            
        # Get the timezone object
        local_tz = pytz_timezone(tz_str)
        
        # Get current time in UTC and convert to the local timezone
        utc_now = datetime.utcnow()
        utc_now = pytz_timezone('UTC').localize(utc_now)
        local_now = utc_now.astimezone(local_tz)
        
        # Format: Jul 7, 2025 8:38PM
        date_str = local_now.strftime("%b %-d, %Y %-I:%M%p")
        
        # Get UTC offset in hours
        offset_hr = int(local_now.utcoffset().total_seconds() // 3600)
        
        # Common timezone abbreviations
        common_tz_abbr = {
            'Asia/Dhaka': 'BDT',
            'Europe/London': 'BST', 
            'Europe/Paris': 'CEST',
            'America/New_York': 'EDT',
            'America/Chicago': 'CDT',
            'America/Denver': 'MDT',
            'America/Los_Angeles': 'PDT',
            'Asia/Kolkata': 'IST',
            'Asia/Tokyo': 'JST',
            'Asia/Singapore': 'SGT',
            'Australia/Sydney': 'AEST',
            'UTC': 'UTC',
        }
        
        # Get the timezone abbreviation
        tz_abbr = common_tz_abbr.get(tz_str, local_now.strftime('%Z'))
        
        # If the abbreviation is not helpful (sometimes it's just 'GMT+x')
        if not tz_abbr or tz_abbr.startswith('GMT') or len(tz_abbr) > 4:
            # Extract city from timezone string as fallback
            if tz_str and '/' in tz_str:
                city = tz_str.split('/')[-1].replace('_', ' ')
                tz_abbr = city[:3].upper()  # Use first 3 letters of city name
        
        # Format the final timestamp
        if tz_abbr:
            return f"{date_str} {tz_abbr} (UTC {offset_hr:+d})"
        else:
            return f"{date_str} (UTC {offset_hr:+d})"
            
    except Exception as e:
        logging.error(f"Error formatting local time: {e}")
        # Fallback to a simple format
        return datetime.now().strftime("%b %-d, %Y %-I:%M%p")

def get_bd_now():
    return datetime.now(timezone.utc) + timedelta(hours=6)

def get_bd_time_str(dt=None):
    """Return BD time as 'Jul 8, 2025 1:24AM (+6 Dhaka)'."""
    if dt is None:
        dt = get_bd_now()
    date_str = dt.strftime("%b %-d, %Y %-I:%M%p")
    offset_hr = 6  # For Bangladesh
    return f"{date_str} (+{offset_hr} Dhaka)"

# ===================== MAIN ENTRY =====================
def build_news_digest(return_msg=False, chat_id=None):
    """
    Main entry point: builds and sends the comprehensive news digest.
    
    This function fetches and formats news from various sources and categories,
    adds cryptocurrency market data, and either returns the formatted message
    or sends it via Telegram.
    
    Args:
        return_msg (bool): If True, return the message as string instead of sending
        chat_id (int, optional): Telegram chat ID to send the digest to
        
    Returns:
        str: The formatted digest message if return_msg is True
    """
    # Initialize user logging database
    init_db()
    
    # Use Bangladesh time for timestamp
    now = get_bd_time_str()
    
    # Create digest header
    msg = f"*DAILY NEWS DIGEST*\n_{now}_\n\n"
    
    # Add news from different categories
    msg += get_local_news()
    msg += get_global_news()
    msg += get_tech_news()
    msg += get_sports_news()
    msg += get_crypto_news()
    
    # Add cryptocurrency market data
    msg += fetch_crypto_market()
    msg += fetch_big_cap_prices()
    msg += fetch_top_movers()

    # Return or send the digest
    if return_msg:
        return msg
        
    if chat_id is not None:
        send_telegram(msg, chat_id)
    else:
        logging.warning("No chat_id provided for sending news digest.")
        print("No chat_id provided for sending news digest.")

def main(return_msg=False, chat_id=None):
    """
    Legacy main entry point: builds and prints or sends the news digest.
    
    This function is maintained for backward compatibility.
    For new code, use build_news_digest() instead.
    
    Args:
        return_msg (bool): If True, return the message as string instead of sending
        chat_id (int, optional): Telegram chat ID to send the digest to
        
    Returns:
        str: The formatted digest message if return_msg is True
    """
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"*DAILY NEWS DIGEST*\n_{now}_\n\n"
    
    # Fetch all news categories
    msg += get_local_news()
    msg += get_global_news()
    msg += get_tech_news()
    msg += get_sports_news()
    msg += get_crypto_news()
    
    # Add crypto market data
    msg += fetch_crypto_market()
    msg += fetch_big_cap_prices()
    msg += fetch_top_movers()

    if return_msg:
        return msg
        
    # Send via Telegram if chat_id is provided
    if chat_id is not None:
        send_telegram(msg, chat_id)
    else:
        logging.warning("No chat_id provided for sending news digest.")
        print(msg)  # Fallback to console output

def get_crypto_ai_summary():
    """
    Get AI-generated cryptocurrency market summary for the /cryptostats command.
    
    This function fetches market data, processes it with DeepSeek AI API,
    and formats the response with prediction information.
    
    Returns:
        str: Formatted AI market summary with prediction line, or error message
    """
    try:
        # Fetch all necessary market data
        market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, _, _, _, _, _ = fetch_crypto_market_data()
        big_caps_msg, big_caps_str = fetch_big_cap_prices_data()
        top_movers_msg, gainers_str, losers_str = fetch_top_movers_data()
        
        # Check if API key is available
        DEEPSEEK_API = os.getenv("DEEPSEEK_API")
        if not DEEPSEEK_API:
            return "AI summary not available: DeepSeek API key is missing."
        
        # Validate data completeness
        missing_data = [k for k, v in {
            "Market Cap": market_cap_str,
            "Market Change": market_cap_change_str,
            "Volume": volume_str,
            "Volume Change": volume_change_str,
            "Fear/Greed": fear_greed_str,
            "Big Caps": big_caps_str,
            "Gainers": gainers_str,
            "Losers": losers_str
        }.items() if v == "N/A"]
        
        # If critical data is missing, return an error message
        if any(x == "N/A" for x in [market_cap_str, market_cap_change_str, volume_str, volume_change_str]):
            logging.warning(f"Critical market data missing for AI summary: {', '.join(missing_data)}")
            return f"AI summary limited: Missing critical market data for {', '.join(missing_data)}. Try again later."
        
        # If only non-critical data is missing, continue with available data
        if missing_data:
            logging.info(f"Some non-critical market data missing for AI summary: {', '.join(missing_data)}")
            # Replace N/A values with placeholders for non-critical data
            if gainers_str == "N/A":
                gainers_str = "Data unavailable"
            if losers_str == "N/A":
                losers_str = "Data unavailable"
            if big_caps_str == "N/A":
                big_caps_str = "Data unavailable"
            if fear_greed_str == "N/A":
                fear_greed_str = "Unknown"
        
        # Get AI summary from DeepSeek
        ai_summary = get_crypto_summary_with_deepseek(
            market_cap_str, market_cap_change_str, volume_str, volume_change_str, 
            fear_greed_str, big_caps_str, gainers_str, losers_str, DEEPSEEK_API
        )
        
        # Handle error responses from AI service
        if ai_summary.startswith("AI summary not available"):
            return ai_summary
        
        # Clean and format the summary text
        ai_summary_clean = re.sub(r'^\s*prediction:.*$', '', ai_summary, flags=re.IGNORECASE | re.MULTILINE).strip()
        if ai_summary_clean and not ai_summary_clean.rstrip().endswith('.'):
            ai_summary_clean = ai_summary_clean.rstrip() + '.'
        
        # Extract confidence percentage from AI response
        summary_lower = ai_summary.lower()
        accuracy_match = re.search(r'(\d{2,3})\s*%\s*(?:confidence|accuracy|probability)?', ai_summary)
        try:
            accuracy = int(accuracy_match.group(1)) if accuracy_match else 80
        except Exception:
            accuracy = 80
        
        # Generate appropriate prediction line based on analysis
        if accuracy <= 60:
            prediction_line = "\nPrediction (Next 24h): CONSOLIDATION 🤔"
        elif "bullish" in summary_lower and accuracy > 60:
            prediction_line = f"\nPrediction (Next 24h): BULLISH 🟢 ({accuracy}% probability)"
        elif "bearish" in summary_lower and accuracy > 60:
            prediction_line = f"\nPrediction (Next 24h): BEARISH 🔴 ({accuracy}% probability)"
        else:
            prediction_line = "\nPrediction (Next 24h): CONSOLIDATION! 🤔"
        
        # Return formatted summary with prediction
        return f"*🤖 AI Market Summary:*\n{ai_summary_clean}\n{prediction_line}"
    
    except Exception as e:
        logging.error(f"Error in get_crypto_ai_summary: {str(e)}")
        return f"AI summary not available: {str(e)}"

def get_coin_stats(symbol):
    """Return price and 24h % change for a given coin symbol (e.g. BTC, ETH)."""
    try:
        coin_id, coin_name = get_coin_id_from_symbol(symbol)
        if not coin_id:
            return f"Coin '{symbol.upper()}' not found in local list."
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": coin_id}
        data = requests.get(url, params=params).json()
        if not data:
            return f"Coin '{symbol.upper()}' not found."
        c = data[0]
        price = c['current_price']
        change = c.get('price_change_percentage_24h', 0)
        arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
        # Format price: 2 decimals if >=1, 6 decimals if <1
        if price >= 1:
            price_str = f"${price:,.2f}"
        else:
            price_str = f"${price:.6f}"
        symbol_upper = c['symbol'].upper()
        change_str = f"({change:+.2f}%)"
        return f"{symbol_upper}: {price_str} {change_str}{arrow}"
    except Exception:
        return f"Error fetching data for '{symbol.upper()}'."

def get_coin_stats_ai(symbol):
    """Return detailed analysis for a given coin symbol (e.g. BTC, ETH) with price, market summary, and forecast."""
    try:
        coin_id, coin_name = get_coin_id_from_symbol(symbol)
        if not coin_id:
            return f"Coin '{symbol.upper()}' not found in local list."
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": coin_id}
        data = requests.get(url, params=params).json()
        if not data:
            return f"Coin '{symbol.upper()}' not found."
        c = data[0]
        price = c['current_price']
        change = c.get('price_change_percentage_24h', 0)
        arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
        # Format price: 2 decimals if >=1, 6 decimals if <1
        if price >= 1:
            price_str = f"${price:,.2f}"
        else:
            price_str = f"${price:.6f}"
        symbol_upper = c['symbol'].upper()
        change_str = f"({change:+.2f}%)"
        
        # Get market cap and volume
        market_cap = c.get('market_cap', 0)
        volume = c.get('total_volume', 0)
        market_cap_str = human_readable_number(market_cap)
        volume_str = human_readable_number(volume)
        
        # --- Fetch RSI and MA30 ---
        rsi_val = 'N/A'
        ma30_val = 'N/A'
        try:
            chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            chart_params = {"vs_currency": "usd", "days": 31, "interval": "daily"}
            chart_data = requests.get(chart_url, params=chart_params).json()
            prices = [p[1] for p in chart_data.get('prices', [])]
            if len(prices) >= 15:
                # RSI calculation (14 period)
                deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                gains = [d for d in deltas if d > 0]
                losses = [-d for d in deltas if d < 0]
                avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else (sum(gains) / len(gains) if gains else 0.0)
                avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else (sum(losses) / len(losses) if losses else 0.0)
                if avg_loss == 0:
                    rsi = 100.0
                else:
                    rs = avg_gain / avg_loss if avg_loss != 0 else 0
                    rsi = 100 - (100 / (1 + rs))
                rsi_val = f"{rsi:.2f}"
            if len(prices) >= 30:
                ma30 = sum(prices[-30:]) / 30
                ma30_val = f"${ma30:,.2f}" if ma30 >= 1 else f"${ma30:.6f}"
                
            # Calculate support and resistance levels (use 7-day high/low as approximation)
            if len(prices) >= 7:
                sorted_prices = sorted(prices[-7:])
                support = sorted_prices[1]  # Second lowest price
                resistance = sorted_prices[-2]  # Second highest price
                support_str = f"${support:,.2f}" if support >= 1 else f"${support:.6e}"
                resistance_str = f"${resistance:,.2f}" if resistance >= 1 else f"${resistance:.6e}"
            else:
                support_str = f"${c['low_24h']:.6e}" if c['low_24h'] < 1 else f"${c['low_24h']:,.2f}"
                resistance_str = f"${c['high_24h']:.6e}" if c['high_24h'] < 1 else f"${c['high_24h']:,.2f}"
        except Exception as e:
            logging.error(f"Error calculating technical indicators: {e}")
            support_str = f"${c['low_24h']:.6e}" if c['low_24h'] < 1 else f"${c['low_24h']:,.2f}"
            resistance_str = f"${c['high_24h']:.6e}" if c['high_24h'] < 1 else f"${c['high_24h']:,.2f}"
            
        # RSI interpretation
        rsi_interpretation = "N/A"
        if rsi_val != 'N/A':
            rsi_float = float(rsi_val)
            if rsi_float > 70:
                rsi_interpretation = "Overbought, potential reversal or correction"
            elif rsi_float < 30:
                rsi_interpretation = "Oversold, potential buying opportunity"
            else:
                rsi_interpretation = "Neutral, no overbought/oversold signal"
        
        # MA interpretation
        ma_interpretation = "N/A"
        if ma30_val != 'N/A' and price is not None:
            ma30_float = float(ma30_val.replace('$', '').replace(',', ''))
            if price > ma30_float * 1.05:
                ma_interpretation = f"Price well above MA, suggesting strong bullish momentum"
            elif price > ma30_float:
                ma_interpretation = f"Price above MA, suggesting bullish momentum"
            elif price < ma30_float * 0.95:
                ma_interpretation = f"Price well below MA, suggesting strong bearish momentum"
            else:
                ma_interpretation = f"Price below MA, suggesting bearish momentum"
        
        # Volume interpretation
        volume_interpretation = "N/A"
        if volume < 10000:
            volume_interpretation = f"Very low ({volume_str}), indicating minimal liquidity and high risk"
        elif volume < 100000:
            volume_interpretation = f"Low ({volume_str}), suggesting limited liquidity"
        elif volume < 1000000:
            volume_interpretation = f"Moderate ({volume_str}), indicating average liquidity"
        elif volume < 10000000:
            volume_interpretation = f"High ({volume_str}), suggesting good liquidity"
        else:
            volume_interpretation = f"Very high ({volume_str}), indicating excellent liquidity"
        
        # Generate AI summary
        ai_summary = ""
        forecast_text = ""
        
        # Create a market analysis based on the available data
        if change > 5:
            ai_summary = f"{symbol_upper} is showing strong bullish momentum with significant price growth over the last 24 hours."
            forecast_text = f"The bullish momentum is likely to continue, though some profit-taking might occur. Watch for increased volume to confirm the trend."
            recommendation = "BUY"
        elif change > 2:
            ai_summary = f"{symbol_upper} is showing moderate bullish movement in the last 24 hours."
            forecast_text = f"Current positive momentum may continue if market conditions remain favorable. Monitor volume for confirmation."
            recommendation = "BUY"
        elif change > 0:
            ai_summary = f"{symbol_upper} is slightly up, indicating neutral to mildly positive sentiment."
            forecast_text = f"Price may continue to consolidate with a slight upward bias. Look for breakout signals for stronger directional moves."
            recommendation = "HOLD"
        elif change > -2:
            ai_summary = f"{symbol_upper} is slightly down but relatively stable in the last 24 hours."
            forecast_text = f"Expect continued sideways movement with slight bearish bias. Support levels should be monitored closely."
            recommendation = "HOLD"
        elif change > -5:
            ai_summary = f"{symbol_upper} is showing moderate bearish movement with notable price decline."
            forecast_text = f"Downward pressure is likely to continue in the short term unless significant support is found."
            recommendation = "SELL"
        else:
            ai_summary = f"{symbol_upper} is experiencing significant bearish pressure with substantial price drops."
            forecast_text = f"Strong downtrend may continue. Wait for signs of stabilization before considering entry positions."
            recommendation = "SELL"
        
        # RSI-based recommendations to override the basic ones if available
        if rsi_val != 'N/A':
            rsi_float = float(rsi_val)
            if rsi_float > 75:
                recommendation = "SELL"
            elif rsi_float < 25:
                recommendation = "BUY"
                
        # Determine emoji for prediction
        if recommendation == "BUY":
            pred_emoji = "🟢"
        elif recommendation == "HOLD":
            pred_emoji = "🟠"
        else:  # SELL
            pred_emoji = "🔴"
            
        # Format the complete response according to the template
        response = (
            f"Price: {symbol_upper} {price_str} {change_str}{arrow}\n"
            f"Market Summary: {symbol_upper} is currently trading at {price_str} with a 24h change of {change_str}{arrow}. "
            f"24h Market Cap: {market_cap_str}. 24h Volume: {volume_str}. {ai_summary}\n\n"
            f"Technicals:\n"
            f"- Support: {support_str}\n"
            f"- Resistance: {resistance_str}\n"
            f"- RSI ({rsi_val}): {rsi_interpretation}\n"
            f"- 30D MA ({ma30_val}): {ma_interpretation}\n"
            f"- Volume: {volume_interpretation}\n"
            f"- Sentiment: {ai_summary}\n\n"
            f"Forecast (Next 24h): {forecast_text}\n\n"
            f"Prediction (Next 24hr): {pred_emoji} {recommendation}"
        )
        
        return response
    except Exception as e:
        logging.error(f"Error in get_coin_stats_ai: {e}")
        return f"Error fetching detailed data for '{symbol.upper()}'. {str(e)}"

def clean_ai_summary(summary):
    """
    Clean and sanitize AI-generated summary text.
    
    Removes HTML tags and other unwanted formatting from AI summaries.
    
    Args:
        summary (str): The raw AI-generated summary text
        
    Returns:
        str: Cleaned summary text
    """
    # Remove HTML tags
    summary = re.sub(r'<[^>]+>', '', summary)
    
    # Normalize whitespace
    summary = re.sub(r'\s+', ' ', summary).strip()
    
    return summary

def format_ai_prediction(summary):
    """
    Standardize prediction format in AI-generated summaries.
    
    This function finds prediction lines in the AI summary and standardizes them
    to the format "Prediction (Next 24h): TREND (XX% Probability)".
    It handles both the new format and legacy format for backward compatibility.
    
    Args:
        summary (str): The AI-generated summary text
        
    Returns:
        str: Summary with standardized prediction formatting
    """
    # Check for current format: "Prediction (Next 24h): TREND (XX% confidence/probability)"
    match = re.search(r'Prediction \(Next 24h\): (.+?) \((\d{2,3})% (confidence|probability)\)', summary, re.IGNORECASE)
    if match:
        trend = match.group(1).strip().upper()
        percent = int(match.group(2))
        
        # Determine if we should show the trend or default to CONSOLIDATION
        if percent > 60 and ("BULLISH" in trend or "BEARISH" in trend):
            new_line = f"Prediction (Next 24h): {trend} ({percent}% Probability)"
        else:
            new_line = "Prediction (Next 24h): CONSOLIDATION"
            
        # Replace the prediction line with standardized format
        summary = re.sub(r'Prediction \(Next 24h\): .+?\(\d{2,3}% (confidence|probability)\)', 
                         new_line, summary, flags=re.IGNORECASE)
    else:
        # Legacy format support: "Prediction For Tomorrow: TREND (XX% confidence/probability)"
        match = re.search(r'Prediction For Tomorrow: (.+?) \((\d{2,3})% (confidence|probability)\)', 
                          summary, re.IGNORECASE)
        if match:
            trend = match.group(1).strip().upper()
            percent = int(match.group(2))
            
            # Determine if we should show the trend or default to CONSOLIDATION
            if percent > 60 and ("BULLISH" in trend or "BEARISH" in trend):
                new_line = f"Prediction (Next 24h): {trend} ({percent}% Probability)"
            else:
                new_line = "Prediction (Next 24h): CONSOLIDATION"
                
            # Replace the legacy format with the new standardized format
            summary = re.sub(r'Prediction For Tomorrow: .+?\(\d{2,3}% (confidence|probability)\)', 
                             new_line, summary, flags=re.IGNORECASE)
        else:
            # If no structured prediction found, just standardize terminology
            summary = re.sub(r'(\d{2,3})% confidence', r'\1% Probability', summary, flags=re.IGNORECASE)
            
    return summary

def get_help_text():
    return (
        "*ChoyNewsBot Commands:*\n"
        "/start - Initialize the bot and get a welcome message\n"
        "/news - Get the full daily news digest\n"
        "/weather - Get Dhaka weather\n"
        "/cryptostats - Get AI summary of crypto market\n"
        "/coin - Get price and 24h change for a coin (e.g. /btc, /eth, /doge)\n"
        "/coinstats - Get price, 24h change, and AI summary (e.g. /btcstats)\n"
        "/timezone <zone> - Set your timezone for news digest times (e.g. /timezone +6, /timezone dhaka, /timezone Europe/Berlin). Shows time in format: Jul 8, 2025 9:52AM BST (UTC +6)\n"
        "/support - Contact the developer for support\n"
        "/help - Show this help message\n"
    )

# --- Telegram polling bot ---
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    resp = requests.get(url, params=params)
    return resp.json().get("result", [])

def handle_updates(updates):
    for update in updates:
        message = update.get("message")
        if not message:
            continue
        chat_id = message["chat"]["id"]
        user = message["from"]
        user_id = user.get("id")
        username = user.get("username")
        first_name = user.get("first_name")
        last_name = user.get("last_name")
        # Log user interaction
        log_user_interaction(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            message_type=message.get("text", "other"),
            location=str(message.get("location")) if message.get("location") else None
        )
        text = message.get("text", "").lower().strip()
        logging.debug(f"Received text: {text}")
        user_location = message.get("location")
        # Welcome message for new users (first interaction)
        if message.get("new_chat_members") or text in ["/start"]:
            send_telegram("Welcome to ChoyNewsBot!", chat_id)
            send_telegram(get_help_text(), chat_id)
            continue
        if text == "/help":
            send_telegram(get_help_text(), chat_id)
            continue
        if text == "/cryptostats":
            try:
                logging.info(f"User {username} requested crypto stats")
                summary = get_crypto_ai_summary()
                send_telegram(summary, chat_id)
                logging.info("Successfully sent crypto stats")
            except Exception as e:
                error_msg = f"Error generating crypto stats: {e}"
                logging.error(error_msg)
                send_telegram("Sorry, there was an error generating the crypto market summary. Please try again later.", chat_id)
            continue
        if text == "/weather":
            send_telegram(get_dhaka_weather(), chat_id)
            continue
        # --- /support command ---
        if text == "/support":
            support_msg = (
                "*Developer Support:*\n"
                "Developer ID: [@shanchoynoor](https://t.me/shanchoynoor)\n"
                "Developer Email: shanchoyzone@gmail.com"
            )
            send_telegram(support_msg, chat_id)
            continue
        # --- /timezone command ---
        if text.startswith("/timezone"):
            args = message.get("text", "").split(maxsplit=1)
            if len(args) < 2:
                send_telegram("Please provide a timezone. Example: /timezone +6 or /timezone dhaka or /timezone Europe/Berlin. Times will be shown in format: Jul 8, 2025 9:52AM BST (UTC +6)", chat_id)
                continue
            tz_input = args[1].strip()
            tz_str = parse_timezone_input(tz_input)
            if not tz_str:
                send_telegram("Invalid timezone. Please use a valid UTC offset, city, or timezone name. Example: /timezone +6 or /timezone dhaka or /timezone Europe/Berlin. Times will be shown in format: Jul 8, 2025 9:52AM BST (UTC +6)", chat_id)
                continue
            set_user_timezone(user_id, tz_str)
            send_telegram(f"Timezone set to {tz_str}. All news digests will now show your local time.", chat_id)
            continue
        if text in ["/news"]:
            send_telegram("Loading latest news...", chat_id)
            now_str = get_local_time_str(user_location, user_id)
            # --- Bangladesh holiday info ---
            now_dt = datetime.now()
            def get_bd_holiday():
                try:
                    api_key = os.getenv("CALENDARIFIC_API_KEY")
                    if not api_key:
                        return ""
                    url = f"https://calendarific.com/api/v2/holidays?api_key={api_key}&country=BD&year={now_dt.year}"
                    resp = requests.get(url)
                    data = resp.json()
                    holidays = data.get("response", {}).get("holidays", [])
                    today_str = now_dt.strftime("%Y-%m-%d")
                    upcoming = None
                    for h in holidays:
                        h_date = h.get("date", {}).get("iso", "")
                        if h_date == today_str:
                            return f"🎉 *Today's Holiday:* {h['name']}"
                        elif h_date > today_str:
                            if not upcoming or h_date < upcoming["date"]:
                                upcoming = {"date": h_date, "name": h["name"]}
                    if upcoming:
                        # Format date as 'Jul 4, 2025'
                        up_date = datetime.strptime(upcoming["date"], "%Y-%m-%d").strftime("%b %d, %Y")
                        return f"🎉 *Next Holiday:* {upcoming['name']} ({up_date})"
                    return ""
                except Exception as e:
                    return ""
            holiday_line = get_bd_holiday()
            # Build the full digest as before
            digest = f"*📢 DAILY NEWS DIGEST*\n_{now_str}_\n\n"
            digest += get_dhaka_weather() + "\n"
            if holiday_line:
                digest += f"{holiday_line}\n"
            digest += "\n"
            digest += get_local_news()
            digest += get_global_news()
            digest += get_tech_news()
            digest += get_sports_news()
            digest += get_crypto_news()
            
            # --- Collect crypto data for DeepSeek summary ---
            market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, market_cap, market_cap_change, volume, volume_change, fear_greed = fetch_crypto_market_data()
            def arrow_only(val):
                try:
                    v = float(val.replace('%','').replace('+','').replace(',',''))
                except Exception:
                    return ''
                if v > 0:
                    return ' ▲'
                elif v < 0:
                    return ' ▼'
                else:
                    return ''
            cap_arrow = arrow_only(market_cap_change_str)
            vol_arrow = arrow_only(volume_change_str)
            # --- FEAR/GREED EMOJI & SUGGESTION ---
            def fear_greed_emoji_suggestion(fear_val):
                try:
                    fg = int(fear_val)
                except Exception:
                    return '😨', '(N/A)'
                if fg <= 24:
                    return '😱', '(🟢 Buy)'
                elif fg <= 49:
                    return '😨', '(🟡 Buy Slowly)'
                elif fg <= 74:
                    return '😏', '(🟠 Hold)'
                else:
                    return '🤯', '(🔴 Sell)'
            fg_emoji, fg_suggestion = fear_greed_emoji_suggestion(fear_greed)
            # Format with brackets for percentage
            def add_brackets(val):
                if val and not val.startswith('('):
                    return f'({val})'
                return val
            market_cap_change_str_b = add_brackets(market_cap_change_str)
            volume_change_str_b = add_brackets(volume_change_str)
            crypto_section = (
                f"*📊 CRYPTO MARKET:*\n"
                f"💰 Market Cap: {market_cap_str} {market_cap_change_str_b}{cap_arrow}\n"
                f"💵 Volume: {volume_str} {volume_change_str_b}{vol_arrow}\n"
                f"{fg_emoji} Fear/Greed: {fear_greed_str}/100 → {fg_suggestion}\n\n"
            )
            big_caps_msg, big_caps_str = fetch_big_cap_prices_data()
            crypto_section += big_caps_msg
            
            # Fetch top movers with better error handling
            try:
                top_movers_msg, gainers_str, losers_str = fetch_top_movers_data()
                # If top movers data is unavailable, use a more user-friendly message
                if "Data temporarily unavailable" in top_movers_msg or "Error fetching data" in top_movers_msg:
                    logging.warning("Top movers data unavailable, using improved placeholder message")
                    top_movers_msg = "*🔺 Crypto Top Movers:*\nData temporarily unavailable\n\n"
                    gainers_str = "Data unavailable"
                    losers_str = "Data unavailable"
                crypto_section += top_movers_msg
            except Exception as e:
                logging.error(f"Error adding top movers to crypto section: {e}")
                crypto_section += "*🔺 Crypto Top Movers:*\nData temporarily unavailable\n\n"
                gainers_str = "Data unavailable"
                losers_str = "Data unavailable"
            DEEPSEEK_API = os.getenv("DEEPSEEK_API")
            ai_summary = None
            prediction_line = ""
            if DEEPSEEK_API and all(x != "N/A" for x in [market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, big_caps_str, gainers_str, losers_str]):
                ai_summary = get_crypto_summary_with_deepseek(
                    market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, big_caps_str, gainers_str, losers_str, DEEPSEEK_API
                )
                import re
                ai_summary_clean = re.sub(r'^\s*prediction:.*$', '', ai_summary, flags=re.IGNORECASE | re.MULTILINE).strip()
                if ai_summary_clean and not ai_summary_clean.rstrip().endswith('.'):
                    ai_summary_clean = ai_summary_clean.rstrip() + '.'
                crypto_section += f"\n*🤖 AI Market Summary:*\n{ai_summary_clean}\n"
                summary_lower = ai_summary.lower()
                accuracy_match = re.search(r'(\d{2,3})\s*%\s*(?:confidence|accuracy|probability)?', ai_summary)
                try:
                    accuracy = int(accuracy_match.group(1)) if accuracy_match else 80
                except Exception:
                    accuracy = 80
                if accuracy <= 60:
                    prediction_line = "\nPrediction (Next 24h): CONSOLIDATION 🤔"
                elif "bullish" in summary_lower and accuracy > 60:
                    prediction_line = f"\nPrediction (Next 24h): BULLISH 🟢 ({accuracy}% probability)"
                elif "bearish" in summary_lower and accuracy > 60:
                    prediction_line = f"\nPrediction (Next 24h): BEARISH 🔴 ({accuracy}% probability)"
                else:
                    prediction_line = "\nPrediction (Next 24h): CONSOLIDATION! 🤔"
                crypto_section += prediction_line
            crypto_section += "\n\n\n- Built by Shanchoy"
            # --- SPLIT DIGEST: send news and crypto in separate messages at CRYPTO MARKET marker ---
            marker = "*📊 CRYPTO MARKET:*\n"
            idx = digest.find(marker)
            if idx != -1:
                news_part = digest[:idx]
                crypto_part = digest[idx:] + crypto_section[len(marker):]  # Avoid duplicate marker
                send_telegram(news_part, chat_id)
                send_telegram(crypto_part, chat_id)
            else:
                # fallback: send as two messages
                send_telegram(digest, chat_id)
                send_telegram(crypto_section, chat_id)
            continue
        # --- Coin stats handlers ---
        # /[coin]stats (e.g. /btcstats)
        if text.startswith("/") and text.endswith("stats") and len(text) > 6:
            symbol = text[1:-5]  # remove leading / and trailing stats
            if symbol:
                reply = get_coin_stats_ai(symbol)
                send_telegram(reply, chat_id)
                continue
        # /[coin] (e.g. /btc)
        if text.startswith("/") and len(text) > 1 and text[1:].isalpha():
            symbol = text[1:]
            reply = get_coin_stats(symbol)
            send_telegram(reply, chat_id)
            continue
def main():
    """
    Main entry point for the Telegram bot polling loop.
    
    This function initializes the bot and continuously polls for new messages,
    handling user commands and requests.
    """
    # Initialize user database
    init_db()
    
    logging.info("Bot started. Listening for messages...")
    print("Bot started. Listening for messages...")
    
    last_update_id = None
    
    # Main polling loop
    while True:
        try:
            # Get updates from Telegram API
            updates = get_updates(last_update_id)
            
            if updates:
                # Process new messages
                handle_updates(updates)
                
                # Update the offset to acknowledge processed updates
                last_update_id = updates[-1]["update_id"] + 1
                
        except Exception as e:
            logging.error(f"Error in main polling loop: {e}")
            # Continue polling despite errors
            
        # Avoid excessive API calls
        time.sleep(2)

if __name__ == "__main__":
    main()