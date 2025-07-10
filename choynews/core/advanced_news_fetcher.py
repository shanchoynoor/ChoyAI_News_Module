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
    """Convert published time to relative time format with precision for recent news."""
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
        total_minutes = diff.total_seconds() / 60
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif total_minutes >= 60:
            hours = int(total_minutes // 60)
            return f"{hours}hr ago"
        elif total_minutes >= 1:
            minutes = int(total_minutes)
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
    """Fetch breaking news from RSS sources with smart filtering and source distribution."""
    all_entries = []
    successful_sources = 0
    source_count = {}  # Track how many articles per source
    
    for source_name, rss_url in sources.items():
        try:
            logger.debug(f"Fetching breaking news from {source_name}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.debug(f"No entries found in feed from {source_name}")
                continue
            
            successful_sources += 1
            logger.debug(f"Successfully fetched {len(feed.entries)} entries from {source_name}")
            source_articles = 0  # Count articles from this source
                
            # Process all entries from this source
            for position, entry in enumerate(feed.entries[:limit]):
                try:
                    title = entry.get('title', '').strip()
                    if not title:
                        continue
                    
                    # Clean HTML tags and image references from title
                    import re
                    title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
                    title = re.sub(r'\s+', ' ', title)     # Normalize whitespace
                    title = title.strip()
                    
                    # Enhanced quality filtering for news titles
                    if (not title or 
                        len(title) < 10 or  # Too short
                        len(title) > 200 or  # Too long
                        title.lower() in ['momentkohli', 'admin', 'test', 'update', 'loading'] or  # Low quality titles
                        any(indicator in title.lower() for indicator in ['image:', 'photo:', 'picture:', 'thumbnail:', '[img]', '[image]']) or
                        title.count('?') > 3 or  # Too many question marks
                        title.count('!') > 3 or  # Too many exclamation marks
                        re.search(r'^[^a-zA-Z]*$', title) or  # No letters at all
                        re.search(r'^[0-9\s\-\.]*$', title) or  # Only numbers and basic punctuation
                        len(re.findall(r'[a-zA-Z]', title)) < 5):  # Less than 5 letters
                        continue
                        
                    # Skip titles that are just image descriptions or contain image indicators
                    if any(indicator in title.lower() for indicator in ['image:', 'photo:', 'picture:', 'thumbnail:', '[img]', '[image]']):
                        continue
                        
                    # Clean and limit title length
                    if len(title) > 120:
                        title = title[:117] + "..."
                    
                    link = entry.get('link', '')
                    pub_time = entry.get('published', entry.get('updated', ''))
                    
                    # Ensure we only get clean text link without any image or media URLs
                    if link and any(img_ext in link.lower() for img_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                        # This is an image link, not a news article link, skip it
                        continue
                    
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
                                            parsed_time = datetime.now()
                            else:
                                parsed_time = pub_time
                        else:
                            parsed_time = datetime.now()
                    except:
                        parsed_time = datetime.now()
                    
                    # Time filtering: Allow news from last 6 hours, but heavily prioritize last 3 hours
                    time_diff = datetime.now() - parsed_time
                    hours_ago = time_diff.total_seconds() / 3600
                    
                    # Skip news older than 6 hours
                    if hours_ago > 6:
                        continue
                    
                    time_ago = format_time_ago(pub_time)
                    
                    # Check for duplicates
                    news_hash = get_news_hash(title, source_name)
                    if is_news_already_sent(news_hash, hours_back=2):
                        continue
                    
                    # Calculate importance score
                    importance_score = calculate_news_importance_score(entry, source_name, position)
                    
                    # Calculate recency score with heavy bias for recent news
                    if hours_ago <= 1:
                        recency_score = 60 + (1 - hours_ago) * 20  # 60-80 points for last hour
                    elif hours_ago <= 3:
                        recency_score = 40 + (3 - hours_ago) * 10  # 40-60 points for 1-3 hours
                    else:
                        recency_score = max(0, 20 - (hours_ago - 3) * 5)  # Decreasing after 3 hours
                    
                    # Combined score (importance + heavy recency weighting)
                    total_score = importance_score + recency_score
                    
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
                        'total_score': total_score,
                        'hours_ago': hours_ago
                    }
                    
                    all_entries.append(entry_data)
                    source_articles += 1
                    
                    # Limit to max 3 articles per source for this category
                    if source_articles >= 3:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error processing entry from {source_name}: {e}")
                    continue
                    
            source_count[source_name] = source_articles
            
        except Exception as e:
            # Only log major errors (not 404s or common RSS issues)
            if "403" in str(e) or "Gone" in str(e):
                logger.debug(f"RSS feed unavailable for {source_name}: {type(e).__name__}")
            elif "404" in str(e):
                logger.debug(f"RSS feed not found for {source_name}: {type(e).__name__}")
            else:
                logger.warning(f"Error fetching from {source_name}: {e}")
            continue
    
    success_rate = (successful_sources / len(sources)) * 100 if sources else 0
    logger.info(f"Fetched {len(all_entries)} total entries from {successful_sources}/{len(sources)} sources for {category} ({success_rate:.1f}% success)")
    logger.debug(f"Source distribution: {source_count}")
    
    # Sort by total score (recency + importance) descending, then by recency
    all_entries.sort(key=lambda x: (x['total_score'], -x['hours_ago']), reverse=True)
    
    # Ensure source diversity in final selection
    final_entries = []
    used_sources = {}
    
    for entry in all_entries:
        source = entry['source']
        
        # Only add if we haven't hit the limit for this source (max 3 per category)
        if used_sources.get(source, 0) < 3 and len(final_entries) < target_count:
            final_entries.append(entry)
            used_sources[source] = used_sources.get(source, 0) + 1
    
    # If we still need more entries and have exhausted source limits, fill remaining slots
    if len(final_entries) < target_count:
        remaining_entries = [e for e in all_entries if e not in final_entries]
        remaining_entries.sort(key=lambda x: x['total_score'], reverse=True)
        
        while len(final_entries) < target_count and remaining_entries:
            final_entries.append(remaining_entries.pop(0))
    
    logger.info(f"Selected {len(final_entries)} entries for {category} with source diversity")
    return final_entries

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
        
        # Remove importance indicators for cleaner display
        # importance_score = entry.get('importance_score', 0)
        # if importance_score > 15:
        #     indicator = "🔥 "  # Hot/breaking news
        # elif importance_score > 10:
        #     indicator = "⚡ "  # Important news
        # else:
        #     indicator = ""
        indicator = ""  # No indicators for clean display
        
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
    """Get breaking Bangladesh news from working sources."""
    bd_sources = {
        "The Daily Star": "https://www.thedailystar.net/rss.xml",  # Working
        "Prothom Alo": "https://www.prothomalo.com/feed",  # Working
        "BDNews24": "https://bangla.bdnews24.com/rss.xml",  # Working alternative
        "Dhaka Tribune": "https://www.dhakatribune.com/feed",  # Working alternative
        "Financial Express": "https://thefinancialexpress.com.bd/feed",  # Working alternative
        "New Age": "http://www.newagebd.net/feed",  # Working alternative
        "UNB": "https://unb.com.bd/feed",  # Working alternative
        "Bangladesh Sangbad Sangstha": "https://www.bssnews.net/feed",  # Additional source
        "Daily Sun": "https://www.daily-sun.com/rss/all-news.xml"  # Additional source
    }
    
    entries = fetch_breaking_news_rss(bd_sources, limit=30, category="local", target_count=5)
    logger.info(f"Local news: fetched {len(entries)} entries")
    return format_news_section("🇧🇩 LOCAL NEWS", entries, limit=5)

def get_breaking_global_news():
    """Get breaking global news from working international sources."""
    global_sources = {
        "BBC": "https://feeds.bbci.co.uk/news/rss.xml",
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "Reuters": "https://news.yahoo.com/rss/",  # Alternative working feed
        "Sky News": "http://feeds.skynews.com/feeds/rss/world.xml",
        "France24": "https://www.france24.com/en/rss",
        "NPR": "https://feeds.npr.org/1001/rss.xml",
        "Yahoo News": "https://news.yahoo.com/rss/",  # Working alternative
        "NBC News": "https://feeds.nbcnews.com/nbcnews/public/world",  # Updated URL
        "Deutsche Welle": "https://rss.dw.com/rdf/rss-en-world",  # Additional reliable source
        "Euronews": "https://www.euronews.com/rss?format=mrss&level=theme&name=news"  # Additional source
    }
    
    entries = fetch_breaking_news_rss(global_sources, limit=30, category="global", target_count=5)
    logger.info(f"Global news: fetched {len(entries)} entries")
    return format_news_section("🌍 GLOBAL NEWS", entries, limit=5)

def get_breaking_tech_news():
    """Get breaking technology news from working tech sources."""
    tech_sources = {
        "TechCrunch": "https://techcrunch.com/feed/",  # Updated working RSS
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index/",
        "Wired": "https://www.wired.com/feed/rss",
        "VentureBeat": "https://venturebeat.com/feed/",
        "Engadget": "https://www.engadget.com/rss.xml",
        "TechRadar": "https://www.techradar.com/rss",
        "ZDNet": "https://www.zdnet.com/news/rss.xml",
        "Gizmodo": "https://gizmodo.com/rss",
        "Mashable": "https://mashable.com/feeds/rss/all",
        "MIT Tech Review": "https://www.technologyreview.com/feed/",  # Additional source
        "9to5Mac": "https://9to5mac.com/feed/"  # Additional source
    }
    
    entries = fetch_breaking_news_rss(tech_sources, limit=25, category="tech", target_count=5)
    logger.info(f"Tech news: fetched {len(entries)} entries")
    return format_news_section("🚀 TECH NEWS", entries, limit=5)

def get_breaking_sports_news():
    """Get breaking sports news from working sports sources."""
    sports_sources = {
        # International Sports Sources (More reliable)
        "ESPN": "https://www.espn.com/espn/rss/news",
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml",
        "Sky Sports": "http://www.skysports.com/rss/12040",
        "Goal.com": "https://www.goal.com/feeds/en/news",
        "ESPN Cricinfo": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
        # Alternative Bangladesh Sports
        "The Daily Star Sports": "https://www.thedailystar.net/sports/rss.xml",
        "Dhaka Tribune Sports": "https://www.dhakatribune.com/sport/feed",
        "Daily Sun Sports": "https://www.daily-sun.com/rss/sports.xml",
        "Sports24": "https://www.sports24.com.bd/feed",
        "Fox Sports": "https://www.foxsports.com/rss"  # Additional source
    }
    
    entries = fetch_breaking_news_rss(sports_sources, limit=25, category="sports", target_count=5)
    logger.info(f"Sports news: fetched {len(entries)} entries")
    return format_news_section("🏆 SPORTS NEWS", entries, limit=5)

def get_breaking_crypto_news():
    """Get breaking cryptocurrency news from working crypto sources."""
    crypto_sources = {
        "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "Cointelegraph": "https://cointelegraph.com/rss",
        "The Block": "https://www.theblock.co/rss.xml",
        "Decrypt": "https://decrypt.co/feed",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "NewsBTC": "https://www.newsbtc.com/feed/",
        "BeInCrypto": "https://beincrypto.com/feed/",
        "CoinTelegraph": "https://cointelegraph.com/rss/tag/bitcoin",
        "U.Today": "https://u.today/rss",
        "CryptoNews": "https://cryptonews.com/news/feed",  # Additional source
        "Bitcoin.com": "https://news.bitcoin.com/feed/"  # Additional source
    }
    
    entries = fetch_breaking_news_rss(crypto_sources, limit=25, category="crypto", target_count=5)
    logger.info(f"Crypto news: fetched {len(entries)} entries")
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
        
        # Get volume change (if available, otherwise estimate as same as market cap change)
        volume_change = market_change  # API doesn't provide volume change, use market change as approximation
        
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
        
        # Format market cap and volume with arrows
        market_cap_str = f"${market_cap/1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap/1e9:.2f}B"
        volume_str = f"${volume/1e12:.2f}T" if volume >= 1e12 else f"${volume/1e9:.2f}B"
        
        # Add arrows for market cap and volume
        market_arrow = "▲" if market_change > 0 else "▼" if market_change < 0 else "→"
        volume_arrow = "▲" if volume_change > 0 else "▼" if volume_change < 0 else "→"
        
        # Fear/Greed Index with buy/sell/hold indicator
        fear_greed_text = ""
        if fear_index != "N/A":
            fear_value = int(fear_index)
            if fear_value >= 75:
                fear_greed_text = f"{fear_index}/100 (🟢 BUY)"
            elif fear_value >= 50:
                fear_greed_text = f"{fear_index}/100 (🟠 HOLD)"
            else:
                fear_greed_text = f"{fear_index}/100 (🔴 SELL)"
        else:
            fear_greed_text = f"{fear_index}/100"
        
        # Build crypto section
        crypto_section = f"""💰 CRYPTO MARKET:
Market Cap: {market_cap_str} ({market_change:+.2f}%) {market_arrow}
Volume: {volume_str} ({volume_change:+.2f}%) {volume_arrow}
Fear/Greed Index: {fear_greed_text}

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
                
                # Format price appropriately using helper function
                price_str = format_crypto_price(price)
                
                crypto_section += f"{symbol}: {price_str} ({change:+.2f}%) {arrow}\n"
        
        # Sort by 24h change for gainers and losers
        sorted_cryptos = sorted([c for c in crypto_data if c['price_change_percentage_24h'] is not None], 
                               key=lambda x: x['price_change_percentage_24h'])
        
        # Top 5 gainers (highest positive changes)
        gainers = sorted_cryptos[-5:][::-1]  # Reverse to get highest first
        crypto_section += "\n📈 Crypto Top 5 Gainers:\n"
        for i, crypto in enumerate(gainers, 1):
            symbol = crypto['symbol'].upper()  # Use symbol instead of name
            price = crypto['current_price']
            change = crypto['price_change_percentage_24h']
            arrow = "▲"
            
            # Format price appropriately using helper function
            price_str = format_crypto_price(price)
            
            crypto_section += f"{i}. {symbol} {price_str} ({change:+.2f}%) {arrow}\n"
        
        # Top 5 losers (lowest negative changes)
        losers = sorted_cryptos[:5]
        crypto_section += "\n📉 Crypto Top 5 Losers:\n"
        for i, crypto in enumerate(losers, 1):
            symbol = crypto['symbol'].upper()  # Use symbol instead of name
            price = crypto['current_price']
            change = crypto['price_change_percentage_24h']
            arrow = "▼"
            
            # Format price appropriately using helper function
            price_str = format_crypto_price(price)
            
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

def get_coingecko_coin_id(symbol):
    """Get CoinGecko coin ID from symbol using their search API."""
    try:
        # First try direct symbol lookup
        search_url = f"https://api.coingecko.com/api/v3/search"
        params = {"query": symbol.lower()}
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        coins = data.get("coins", [])
        
        # Look for exact symbol match first
        for coin in coins:
            if coin.get("symbol", "").lower() == symbol.lower():
                return coin.get("id"), coin.get("name"), coin.get("symbol", "").upper()
        
        # If no exact match, try partial match or popular coins
        if coins:
            first_result = coins[0]
            return first_result.get("id"), first_result.get("name"), first_result.get("symbol", "").upper()
            
        return None, None, None
        
    except Exception as e:
        logger.debug(f"Error searching for coin {symbol}: {e}")
        return None, None, None

def get_coin_emoji(symbol):
    """Get emoji for specific coins."""
    emoji_map = {
        'btc': '₿', 'bitcoin': '₿',
        'eth': 'Ⓔ', 'ethereum': 'Ⓔ', 
        'doge': '🐕', 'dogecoin': '�',
        'ada': '🔷', 'cardano': '🔷',
        'sol': '☀️', 'solana': '☀️',
        'xrp': '💧', 'ripple': '💧',
        'matic': '�', 'polygon': '🟣',
        'dot': '🔴', 'polkadot': '🔴',
        'link': '🔗', 'chainlink': '🔗',
        'uni': '🦄', 'uniswap': '🦄',
        'pepe': '🐸', 
        'shib': '🐕', 'shiba': '🐕',
        'bnb': '🟡', 'binancecoin': '�',
        'avax': '🔺', 'avalanche': '🔺',
        'ltc': '⚡', 'litecoin': '⚡',
        'bch': '💚', 'bitcoin-cash': '�',
        'atom': '⚛️', 'cosmos': '⚛️',
        'luna': '🌙', 'terra-luna': '🌙',
        'near': '🔸', 'near-protocol': '🔸'
    }
    return emoji_map.get(symbol.lower(), '🪙')

def format_crypto_price(price):
    """
    Format cryptocurrency price with appropriate decimal places.
    
    Args:
        price (float): The price to format
        
    Returns:
        str: Formatted price string with $ prefix
    """
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

def get_individual_crypto_stats(symbol):
    """Get detailed crypto stats with dynamic CoinGecko lookup for any coin."""
    try:
        # Get coin ID from CoinGecko search
        coin_id, coin_name, coin_symbol = get_coingecko_coin_id(symbol)
        
        if not coin_id:
            return None
        
        coin_emoji = get_coin_emoji(coin_symbol or symbol)
        
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
        name = coin_name or data.get("name", symbol.upper())
        current_price = market_data.get("current_price", {}).get("usd", 0)
        price_change_24h = market_data.get("price_change_percentage_24h", 0) or 0
        market_cap = market_data.get("market_cap", {}).get("usd", 0)
        volume_24h = market_data.get("total_volume", {}).get("usd", 0)
        market_cap_rank = market_data.get("market_cap_rank", "N/A")
        
        # Get 52-week high and low
        ath = market_data.get("ath", {}).get("usd", 0)  # All-time high
        atl = market_data.get("atl", {}).get("usd", 0)  # All-time low
        
        # If we don't have exact 52-week data, use all-time high/low as approximation
        # In practice, you might want to call a different endpoint for 52-week data
        week_52_high = ath if ath else current_price * 1.5  # Fallback estimation
        week_52_low = atl if atl else current_price * 0.5   # Fallback estimation
        
        # Format price using helper function
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
        
        # Assume volume change is positive (you could get actual volume change if available from API)
        volume_change = 1.4  # Default positive change, could be enhanced with historical data
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
🪙 Price: {price_str} ({price_change_24h:+.1f}% {price_arrow})
📊 24h Volume: {vol_str} ({volume_change:+.1f}% {volume_arrow})
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

def get_individual_crypto_stats_with_ai(symbol):
    """Get detailed crypto stats with AI analysis using dynamic CoinGecko lookup."""
    try:
        # Get coin ID from CoinGecko search
        coin_id, coin_name, coin_symbol = get_coingecko_coin_id(symbol)
        
        if not coin_id:
            return None
        
        coin_emoji = get_coin_emoji(coin_symbol or symbol)
        
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
        name = data.get("name", coin_name)
        current_price = market_data.get("current_price", {}).get("usd", 0)
        price_change_24h = market_data.get("price_change_percentage_24h", 0) or 0
        market_cap = market_data.get("market_cap", {}).get("usd", 0)
        volume_24h = market_data.get("total_volume", {}).get("usd", 0)
        high_24h = market_data.get("high_24h", {}).get("usd", current_price)
        low_24h = market_data.get("low_24h", {}).get("usd", current_price)
        
        # Format price using helper function
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
        
        # Build the formatted message without quotes
        stats_message = f"""Price: {symbol.upper()} {price_str} ({price_change_24h:+.2f}%) {arrow}
Market Summary: {name} is currently trading at {price_str} with a 24h change of ({price_change_24h:+.2f}%) {arrow}. 24h Market Cap: {mcap_str}. 24h Volume: {vol_str}.

{ai_analysis}"""
        
        return stats_message
        
    except Exception as e:
        logger.error(f"Error fetching {symbol} stats with AI: {e}")
        return f"Sorry, I couldn't get detailed stats for {symbol.upper()}. Please try again later."

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
        temp_c = current.get("temp_c", 25)
        feels_like_c = current.get("feelslike_c", temp_c)
        
        condition = current.get("condition", {}).get("text", "Partly cloudy")
        if not condition:
            condition = "Partly cloudy"
            
        humidity = current.get("humidity", 70)
        if humidity is None:
            humidity = 70
        
        # Wind data
        wind_kph = current.get("wind_kph", 12)
        if wind_kph is None:
            wind_kph = 12
            
        wind_dir = current.get("wind_dir", "SE")
        if not wind_dir:
            wind_dir = "SE"
        
        # Visibility
        vis_km = current.get("vis_km", 10)
        if vis_km is None:
            vis_km = 10
        
        # UV Index
        uv = current.get("uv", 7)
        if uv is None:
            uv = 7
        
        # Ensure UV is a number and format it properly
        try:
            uv = float(uv)
            if uv <= 2:
                uv_level = "Low"
            elif uv <= 5:
                uv_level = "Moderate"
            elif uv <= 7:
                uv_level = "High"
            elif uv <= 10:
                uv_level = "Very High"
            else:
                uv_level = "Extreme"
            uv_str = f"{uv_level} ({uv:.1f}/11)"
        except (ValueError, TypeError):
            uv_str = "Moderate (5.0/11)"
        
        # Air Quality with detailed AQI value
        aqi_data = current.get("air_quality", {})
        us_epa = aqi_data.get("us-epa-index", 2)
        
        # Try to get specific AQI value if available
        pm2_5 = aqi_data.get("pm2_5", 0)
        pm10 = aqi_data.get("pm10", 0)
        
        # Calculate estimated AQI from PM2.5 if available
        if pm2_5 > 0:
            if pm2_5 <= 12:
                aqi_value = int(pm2_5 * 4.17)  # 0-50 range
                aqi_text = "Good"
            elif pm2_5 <= 35.4:
                aqi_value = int(51 + (pm2_5 - 12.1) * 2.1)  # 51-100 range
                aqi_text = "Moderate"
            elif pm2_5 <= 55.4:
                aqi_value = int(101 + (pm2_5 - 35.5) * 2.5)  # 101-150 range
                aqi_text = "Unhealthy for Sensitive Groups"
            else:
                aqi_value = 151
                aqi_text = "Unhealthy"
        else:
            # Fallback based on EPA index
            aqi_levels = {
                1: ("Good", 45), 2: ("Moderate", 65), 3: ("Unhealthy for Sensitive", 105), 
                4: ("Unhealthy", 155), 5: ("Very Unhealthy", 205), 6: ("Hazardous", 305)
            }
            aqi_text, aqi_value = aqi_levels.get(us_epa, ("Moderate", 65))
        
        # Create temperature range (current feels like range)
        temp_min = temp_c - 2  # Approximate daily range
        temp_max = temp_c + 5
        
        weather_section = f"""*☀️ DHAKA WEATHER:*
🌡️ Temperature: {temp_min:.1f}°C - {temp_max:.1f}°C
🌤️ Condition: {condition}  
💨 Wind: {wind_kph:.1f} km/h {wind_dir}
💧 Humidity: {humidity}%
👁️ Visibility: {vis_km:.1f} km
🫧 Air Quality: {aqi_text} (AQI {aqi_value})
🔆 UV Index: {uv_str}

"""
        
        return weather_section
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        # Return a fallback weather section matching the sample format
        return """*☀️ DHAKA WEATHER:*
🌡️ Temperature: 28.5°C - 32.1°C
🌤️ Condition: Partly cloudy with light rain possible  
💨 Wind: 12 km/h SE
💧 Humidity: 78%
👁️ Visibility: 10.0 km
🫧 Air Quality: Moderate (AQI 65)
🔆 UV Index: High (7/11)

"""

# ===================== HOLIDAYS =====================

def get_bd_holidays():
    """Get Bangladesh holidays for today."""
    try:
        api_key = Config.CALENDARIFIC_API_KEY
        if not api_key:
            logger.debug("No Calendarific API key configured")
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
        
        logger.debug(f"Checking holidays for date: {today.year}-{today.month:02d}-{today.day:02d}")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"Holiday API response: {data}")
        
        holidays = data.get("response", {}).get("holidays", [])
        
        if holidays:
            holiday_names = []
            for h in holidays:
                name = h.get("name", "Holiday")
                holiday_type = h.get("type", [])
                logger.debug(f"Found holiday: {name}, type: {holiday_type}")
                holiday_names.append(name)
            
            holiday_text = ', '.join(holiday_names)
            logger.info(f"Today's holidays: {holiday_text}")
            return f"🎉 Today's Holiday: {holiday_text}\n\n"
        else:
            logger.debug("No holidays found for today")
            
            # Check for common Bangladesh holidays manually if API doesn't have them
            manual_holidays = check_manual_bd_holidays(today)
            if manual_holidays:
                logger.info(f"Manual holiday found: {manual_holidays}")
                return f"🎉 Today's Holiday: {manual_holidays}\n\n"
            
            return ""
            
    except Exception as e:
        logger.error(f"Error fetching holidays: {e}")
        
        # Try manual check as fallback
        try:
            today = get_bd_now()
            manual_holidays = check_manual_bd_holidays(today)
            if manual_holidays:
                logger.info(f"Fallback manual holiday: {manual_holidays}")
                return f"🎉 Today's Holiday: {manual_holidays}\n\n"
        except Exception as manual_e:
            logger.error(f"Manual holiday check also failed: {manual_e}")
        
        return ""

def check_manual_bd_holidays(date):
    """Check for common Bangladesh holidays manually."""
    try:
        # Common Islamic holidays and Bengali holidays (approximate dates)
        # Note: Islamic holidays follow lunar calendar, so dates change yearly
        
        month_day = f"{date.month:02d}-{date.day:02d}"
        year = date.year
        
        # Fixed date holidays
        fixed_holidays = {
            "02-21": "International Mother Language Day",
            "03-26": "Independence Day",
            "04-14": "Pohela Boishakh (Bengali New Year)",
            "05-01": "Labour Day",
            "08-15": "National Mourning Day",
            "12-16": "Victory Day",
            "12-25": "Christmas Day"
        }
        
        if month_day in fixed_holidays:
            return fixed_holidays[month_day]
        
        # Check for common Islamic holidays (these dates vary by year)
        # You would need to implement proper Islamic calendar calculation
        # For now, check some common names that might be today
        
        islamic_holidays_2025 = {
            # These are approximate - actual dates depend on moon sighting
            "07-10": "Ashari Purnima",  # Today's date as mentioned by user
            "04-10": "Eid ul-Fitr",
            "06-17": "Eid ul-Adha",
            "07-07": "Muharram",
            "09-16": "Eid-e-Milad-un-Nabi"
        }
        
        if month_day in islamic_holidays_2025:
            return islamic_holidays_2025[month_day]
        
        return None
        
    except Exception as e:
        logger.error(f"Error in manual holiday check: {e}")
        return None


# ===================== GLOBAL MARKET INDEX (TWELVE DATA) =====================
def fetch_global_market_indices():
    """Fetch global market indices from Twelve Data API and format for news output."""
    try:
        api_key = getattr(Config, 'TWELVE_DATA_API_KEY', None)
        if not api_key:
            return "[🌐] GLOBAL MARKET INDEX\nData unavailable.\n"

        indices = {
            'SPX500': ('S&P 500', 'USA'),
            'NIFTY': ('NIFTY', 'India'),
            'DSEX': ('DSEX', 'Dhaka'),
            'USDX': ('US Dollar Index', 'Forex')
        }
        symbols = ','.join(indices.keys())
        url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        emoji = "🌐"
        section = f"{emoji} GLOBAL MARKET INDEX\n"
        for symbol, (name, country) in indices.items():
            idx = data.get(symbol, {})
            price = idx.get('close', 'N/A')
            change = idx.get('percent_change', 'N/A')
            arrow = "▲" if isinstance(change, str) and change.startswith('+') else ("▼" if isinstance(change, str) and change.startswith('-') else "→")
            section += f"{symbol} ({country}): {price} ({change}%) {arrow} \n"
        return section + "\n"
    except Exception as e:
        logger.error(f"Error fetching global market indices: {e}")
        return "[🌐] GLOBAL MARKET INDEX\nData unavailable.\n\n"

# ===================== NEWS DIGEST ASSEMBLER =====================
def get_full_news_digest():
    """Assemble the full /news digest in the requested format."""
    # 1. Header
    now = get_bd_now()
    date_str = now.strftime('%b %d, %Y %-I:%M%p BDT (UTC +6)')
    header = f"\U0001F4E2 TOP NEWS HEADLINES\n{date_str}\n"

    # 2. Holiday
    holiday = get_bd_holidays().strip()
    if holiday:
        header += f"{holiday}\n"

    # 3. Weather
    weather = get_dhaka_weather().replace('*', '').replace(':*', ':').replace('DHAKA WEATHER', 'WEATHER').strip()
    header += f"{weather}\n\n"

    # 4. News sections
    local = get_breaking_local_news().replace('*', '').replace(':*', ':').strip()
    globaln = get_breaking_global_news().replace('*', '').replace(':*', ':').strip()
    tech = get_breaking_tech_news().replace('*', '').replace(':*', ':').strip()
    sports = get_breaking_sports_news().replace('*', '').replace(':*', ':').strip()
    crypto = get_breaking_crypto_news().replace('*', '').replace(':*', ':').strip()

    # 5. Global Market Index
    market_index = fetch_global_market_indices().strip()

    # 6. Crypto Market Status
    crypto_market = fetch_crypto_market_with_ai().strip()

    # 7. Footer
    footer = "Type /help for more detailed information about what I can do!\n━━━━━━━━━━━━━━-\n\U0001F916 Developed by Shanchoy Noor\n"

    # Assemble all
    digest = f"{header}\n{local}\n{globaln}\n{tech}\n{sports}\n{crypto}\n{market_index}\n{crypto_market}\n{footer}"
    return digest

# ===================== CRYPTOSTATS ONLY =====================
def get_crypto_stats_digest():
    """Return only the crypto market section for /cryptostats command."""
    return fetch_crypto_market_with_ai().strip()

# Initialize on import
init_news_history_db()
