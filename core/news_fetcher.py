"""
News Fetcher Module for Choy News Bot.

This module handles fetching news from various RSS sources and external APIs.
"""

import requests
import feedparser
import json
import os
from datetime import datetime, timedelta
from utils.logging import get_logger
from utils.config import Config

logger = get_logger(__name__)

def get_hours_ago(published_time_str):
    """Calculate accurate hours ago from published time string."""
    if not published_time_str:
        return "Unknown"
    
    try:
        pub_time = None
        
        # Clean the input string
        time_str = published_time_str.strip()
        
        # Handle different date formats
        try:
            # RFC 822 format: "Mon, 25 Nov 2024 14:30:00 GMT" or "Thu, 12 Jul 2025 01:31:44 +0000"
            if "GMT" in time_str or "UTC" in time_str:
                clean_str = time_str.replace("GMT", "").replace("UTC", "").strip()
                pub_time = datetime.strptime(clean_str, "%a, %d %b %Y %H:%M:%S")
            elif "+0000" in time_str or "+0600" in time_str or "-" in time_str.split()[-1]:
                # Handle timezone offsets like "+0000", "+0600", etc.
                # Remove timezone offset
                parts = time_str.rsplit(' ', 1)
                if len(parts) == 2 and ('+' in parts[1] or '-' in parts[1]):
                    clean_str = parts[0]
                    pub_time = datetime.strptime(clean_str, "%a, %d %b %Y %H:%M:%S")
                else:
                    # Try full string
                    pub_time = datetime.strptime(time_str, "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)
            # ISO format: "2024-11-25T14:30:00Z" or "2024-11-25T14:30:00"
            elif "T" in time_str:
                if time_str.endswith('Z'):
                    pub_time = datetime.strptime(time_str[:-1], "%Y-%m-%dT%H:%M:%S")
                elif '+' in time_str:
                    # Handle timezone offset in ISO format
                    pub_time = datetime.strptime(time_str.split('+')[0], "%Y-%m-%dT%H:%M:%S")
                elif '-' in time_str and time_str.count('-') > 2:
                    # Handle negative timezone offset
                    parts = time_str.split('-')
                    if len(parts) >= 4:  # Year-Month-Day-timezone
                        clean_str = '-'.join(parts[:-1])
                        pub_time = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
                else:
                    pub_time = datetime.strptime(time_str[:19], "%Y-%m-%dT%H:%M:%S")
            # Standard format: "2024-11-25 14:30:00"
            elif time_str.count('-') == 2 and ':' in time_str:
                pub_time = datetime.strptime(time_str[:19], "%Y-%m-%d %H:%M:%S")
            # RSS common format: "Thu, 12 Jul 2025 01:31:44"
            elif ',' in time_str and len(time_str.split()) >= 5:
                # Try without timezone first
                try:
                    pub_time = datetime.strptime(time_str, "%a, %d %b %Y %H:%M:%S")
                except ValueError:
                    # If that fails, try with just the date part
                    parts = time_str.split()
                    if len(parts) >= 5:
                        date_part = ' '.join(parts[:5])
                        pub_time = datetime.strptime(date_part, "%a, %d %b %Y %H:%M:%S")
        except ValueError:
            pass
        
        # If all specific formats fail, try common fallbacks
        if pub_time is None:
            fallback_formats = [
                "%Y-%m-%d %H:%M:%S",
                "%d %b %Y %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%Y-%m-%d",
                "%d %b %Y"
            ]
            
            for fmt in fallback_formats:
                try:
                    pub_time = datetime.strptime(time_str[:len(fmt)], fmt)
                    break
                except ValueError:
                    continue
        
        # If we still don't have a time, return Unknown
        if pub_time is None:
            logger.debug(f"Could not parse time format: '{published_time_str}'")
            return "Unknown"
        
        # Calculate time difference (assume UTC if no timezone specified)
        now = datetime.now()
        time_diff = now - pub_time
        
        # Convert to hours
        hours_diff = time_diff.total_seconds() / 3600
        
        if hours_diff < 0:
            # Future time, likely timezone issue
            hours_diff = abs(hours_diff)
            if hours_diff < 1:
                return "now"
            elif hours_diff < 24:
                return f"{int(hours_diff)}hr ago"
            else:
                return f"{int(hours_diff/24)}d ago"
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
            return f"{days_diff}d ago"
            
    except Exception as e:
        logger.debug(f"Error parsing time '{published_time_str}': {e}")
        return "Unknown"

def fetch_rss_entries(sources, limit=5, max_age_hours=2):
    """
    Fetch RSS entries from multiple sources, prioritizing recent news.
    
    Args:
        sources (dict): Dictionary of source_name: rss_url
        limit (int): Maximum number of entries per source
        max_age_hours (int): Maximum age of news in hours (default 2 hours)
        
    Returns:
        list: List of recent news entries with metadata
    """
    all_entries = []
    very_recent_entries = []  # Less than 20 minutes
    recent_entries = []       # 20 minutes to 2 hours
    
    for source_name, rss_url in sources.items():
        try:
            logger.info(f"Fetching RSS from {source_name}: {rss_url}")
            
            # Set timeout and headers
            headers = {
                'User-Agent': 'ChoyNewsBot/1.0 (+https://github.com/shanchoynoor/ChoyAI_News_Module)'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {source_name}")
                continue
            
            logger.info(f"Found {len(feed.entries)} entries from {source_name}")
                
            # Process entries
            for entry in feed.entries[:limit*2]:  # Get more entries to filter recent ones
                try:
                    # Extract publication time - try multiple fields
                    pub_time = (entry.get('published') or 
                              entry.get('updated') or 
                              entry.get('pubDate') or 
                              entry.get('date') or '')
                    
                    pub_time_dt = None
                    time_ago = "Unknown"
                    hours_diff = 999  # Default to very old
                    
                    # If we have a published_parsed field, use it for more accuracy
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            import time
                            # Convert struct_time to datetime
                            pub_time_struct = entry.published_parsed
                            pub_time_dt = datetime(*pub_time_struct[:6])
                            
                            # Calculate time difference
                            now = datetime.now()
                            time_diff = now - pub_time_dt
                            hours_diff = time_diff.total_seconds() / 3600
                            
                            if hours_diff < 0:
                                hours_diff = abs(hours_diff)  # Handle future times
                            
                            if hours_diff < 1/60:  # Less than 1 minute
                                time_ago = "now"
                            elif hours_diff < 1:
                                minutes_diff = int(time_diff.total_seconds() / 60)
                                time_ago = f"{minutes_diff}min ago"
                            elif hours_diff < 24:
                                time_ago = f"{int(hours_diff)}hr ago"
                            else:
                                days_diff = int(hours_diff / 24)
                                time_ago = f"{days_diff}d ago"
                        except:
                            time_ago = get_hours_ago(pub_time)
                            # Try to extract hours for filtering
                            if "min ago" in time_ago:
                                try:
                                    hours_diff = int(time_ago.split("min")[0]) / 60
                                except:
                                    hours_diff = 0.5
                            elif "hr ago" in time_ago:
                                try:
                                    hours_diff = int(time_ago.split("hr")[0])
                                except:
                                    hours_diff = 1
                            elif "now" in time_ago:
                                hours_diff = 0
                    else:
                        time_ago = get_hours_ago(pub_time)
                        # Try to extract hours for filtering
                        if "min ago" in time_ago:
                            try:
                                hours_diff = int(time_ago.split("min")[0]) / 60
                            except:
                                hours_diff = 0.5
                        elif "hr ago" in time_ago:
                            try:
                                hours_diff = int(time_ago.split("hr")[0])
                            except:
                                hours_diff = 1
                        elif "now" in time_ago:
                            hours_diff = 0
                        elif "d ago" in time_ago:
                            hours_diff = 25  # Older than 24 hours
                    
                    # Skip very old news (older than max_age_hours)
                    if hours_diff > max_age_hours:
                        continue
                    
                    # Clean title
                    title = entry.get('title', 'No title').strip()
                    if len(title) > 100:
                        title = title[:97] + "..."
                    
                    # Extract link
                    link = entry.get('link', '')
                    
                    entry_data = {
                        'title': title,
                        'link': link,
                        'source': source_name,
                        'published': pub_time,
                        'time_ago': time_ago,
                        'hours_diff': hours_diff,
                        'summary': entry.get('summary', '')[:200] + "..." if entry.get('summary') else ''
                    }
                    
                    # Categorize by recency
                    if hours_diff <= 1/3:  # 20 minutes or less
                        very_recent_entries.append(entry_data)
                    else:
                        recent_entries.append(entry_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {e}")
                    continue
                    
        except requests.RequestException as e:
            logger.error(f"Error fetching RSS from {source_name}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error with {source_name}: {e}")
            continue
    
    # Prioritize very recent news
    if very_recent_entries:
        logger.info(f"Found {len(very_recent_entries)} very recent entries (≤20min)")
        all_entries = very_recent_entries
        # If we have enough very recent news, just add a few recent ones for context
        if len(very_recent_entries) >= limit:
            all_entries = very_recent_entries[:limit]
        else:
            # Add some recent entries to fill up
            remaining_slots = limit - len(very_recent_entries)
            all_entries.extend(recent_entries[:remaining_slots])
    else:
        logger.info(f"No very recent news found, using recent entries (≤{max_age_hours}hr). Found {len(recent_entries)} recent entries")
        all_entries = recent_entries
    
    logger.info(f"Returning {len(all_entries)} total entries out of requested {limit}")
    
    # Sort by time (newest first)
    try:
        all_entries.sort(key=lambda x: x.get('hours_diff', 999))
    except:
        # Fallback sorting
        try:
            def get_sort_time(entry):
                time_str = entry.get('published', '')
                if not time_str:
                    return datetime.min
                
                try:
                    if "GMT" in time_str or "UTC" in time_str:
                        clean_str = time_str.replace("GMT", "").replace("UTC", "").strip()
                        return datetime.strptime(clean_str, "%a, %d %b %Y %H:%M:%S")
                    elif "+0000" in time_str or "+0600" in time_str:
                        parts = time_str.rsplit(' ', 1)
                        if len(parts) == 2:
                            clean_str = parts[0]
                            return datetime.strptime(clean_str, "%a, %d %b %Y %H:%M:%S")
                    elif "T" in time_str:
                        if time_str.endswith('Z'):
                            return datetime.strptime(time_str[:-1], "%Y-%m-%dT%H:%M:%S")
                        else:
                            return datetime.strptime(time_str[:19], "%Y-%m-%dT%H:%M:%S")
                    elif ',' in time_str:
                        return datetime.strptime(time_str, "%a, %d %b %Y %H:%M:%S")
                    else:
                        return datetime.strptime(time_str[:19], "%Y-%m-%d %H:%M:%S")
                except:
                    return datetime.min
            
            all_entries.sort(key=get_sort_time, reverse=True)
        except:
            pass
        
    return all_entries[:limit]

def format_news(section_title, entries, limit=5):
    """
    Format news entries into markdown.
    
    Args:
        section_title (str): Title of the section
        entries (list): List of news entries
        limit (int): Maximum number of entries to include
        
    Returns:
        str: Formatted markdown section
    """
    if not entries:
        return f"*{section_title}*\nNo news available at the moment.\n\n"
    
    formatted = f"*{section_title}*\n"
    
    for i, entry in enumerate(entries[:limit], 1):
        title = entry.get('title', 'No title')
        source = entry.get('source', 'Unknown')
        time_ago = entry.get('time_ago', 'Unknown')
        link = entry.get('link', '')
        
        # Escape markdown special characters in title
        title_escaped = title.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
        
        if link:
            formatted += f"{i}. [{title_escaped}]({link}) - {source} ({time_ago})\n"
        else:
            formatted += f"{i}. {title_escaped} - {source} ({time_ago})\n"
    
    return formatted + "\n"

# ===================== CATEGORY FETCHERS =====================

def get_local_news():
    """Fetch local Bangladesh news."""
    bd_sources = {
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "The Daily Star": "https://www.thedailystar.net/frontpage/rss.xml",
        "BDNews24": "https://bdnews24.com/feed",
        "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
        "Jugantor": "https://www.jugantor.com/rss.xml",
        "Samakal": "https://samakal.com/rss.xml",
        "Jagonews24": "https://www.jagonews24.com/rss.xml",
        "Kaler Kantho": "https://www.kalerkantho.com/rss.xml",
        "Ittefaq": "https://www.ittefaq.com.bd/rss.xml",
        "Shomoy TV": "https://www.shomoynews.com/rss.xml",
        "Bangladesh Pratidin": "https://www.bd-pratidin.com/rss.xml"
    }
    return format_news("🇧🇩 LOCAL NEWS", fetch_rss_entries(bd_sources))

def get_global_news():
    """Fetch global news."""
    global_sources = {
        "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Reuters": "http://feeds.reuters.com/reuters/topNews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "New York Post": "https://nypost.com/feed/",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "The Washington Post": "https://feeds.washingtonpost.com/rss/world",
        "NBC News": "https://feeds.nbcnews.com/nbcnews/public/news",
        "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "The Economist": "https://www.economist.com/latest/rss.xml",
        "Axios": "https://www.axios.com/rss",
        "Fox News": "https://feeds.foxnews.com/foxnews/latest"
    }
    return format_news("🌍 GLOBAL NEWS", fetch_rss_entries(global_sources))

def get_tech_news():
    """Fetch technology news."""
    tech_sources = {
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Wired": "https://www.wired.com/feed/rss",
        "CNET": "https://www.cnet.com/rss/news/",
        "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index/",
        "Mashable": "https://mashable.com/feeds/rss/all",
        "Engadget": "https://www.engadget.com/rss.xml",
        "TechRadar": "https://www.techradar.com/rss"
    }
    return format_news("🚀 TECH NEWS", fetch_rss_entries(tech_sources))

def get_sports_news():
    """Fetch sports news."""
    sports_sources = {
        "সমকাল খেলা": "https://samakal.com/sports/rss.xml",
        "প্রথম আলো খেলা": "https://www.prothomalo.com/sports/feed",
        "কালের কণ্ঠ খেলা": "https://www.kalerkantho.com/sports/rss.xml",
        "বণিক বার্তা খেলা": "https://www.bonikbarta.net/sports/feed",
        "জুগান্তর খেলা": "https://www.jugantor.com/sports-news/rss.xml",
        "ইত্তেফাক খেলা": "https://www.ittefaq.com.bd/sports/rss.xml",
        "বাংলানিউজ খেলা": "https://www.banglanews24.com/sports/rss.xml"
    }
    return format_news("🏆 SPORTS NEWS", fetch_rss_entries(sports_sources))

def get_crypto_news():
    """Fetch cryptocurrency news."""
    crypto_sources = {
        "Cointelegraph": "https://cointelegraph.com/rss",
        "Decrypt": "https://decrypt.co/feed",
        "Coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "BeInCrypto": "https://beincrypto.com/feed/",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "The Block": "https://www.theblock.co/rss.xml",
        "CoinTelegraph": "https://cointelegraph.com/rss/tag/bitcoin"
    }
    return format_news("🪙 FINANCE & CRYPTO NEWS", fetch_rss_entries(crypto_sources))

# ===================== CRYPTO DATA =====================

def human_readable_number(num):
    """Convert large numbers to human readable format."""
    try:
        num = float(num)
        if num >= 1e12:
            return f"${num/1e12:.2f}T"
        elif num >= 1e9:
            return f"${num/1e9:.2f}B"
        elif num >= 1e6:
            return f"${num/1e6:.2f}M"
        elif num >= 1e3:
            return f"${num/1e3:.2f}K"
        else:
            return f"${num:.2f}"
    except:
        return str(num)

def fetch_crypto_market():
    """Fetch cryptocurrency market overview."""
    try:
        volume_file = os.path.join(Config.LOG_FILE.replace('choynews.log', ''), "volume_log.json")
        os.makedirs(os.path.dirname(volume_file), exist_ok=True)
        
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()["data"]
        market_cap = data["total_market_cap"]["usd"]
        volume = data["total_volume"]["usd"]
        market_change = data["market_cap_change_percentage_24h_usd"]

        # Calculate volume change
        prev_volume = None
        try:
            if os.path.exists(volume_file):
                with open(volume_file, "r") as f:
                    prev_volume = json.load(f).get("volume", None)
        except:
            pass

        if prev_volume and prev_volume > 0:
            volume_change = ((volume - prev_volume) / prev_volume) * 100
            volume_change_str = f"{volume_change:+.2f}%"
        else:
            volume_change_str = "N/A"

        try:
            with open(volume_file, "w") as f:
                json.dump({"volume": volume}, f)
        except:
            pass

        # Fetch Fear & Greed Index
        try:
            fear_response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
            fear_index = fear_response.json()["data"][0]["value"]
        except:
            fear_index = "N/A"

        return (
            "*💰 CRYPTO MARKET:*\n"
            f"Market Cap (24h): {human_readable_number(market_cap)} ({market_change:+.2f}%)\n"
            f"Volume (24h): {human_readable_number(volume)} ({volume_change_str})\n"
            f"Fear/Greed Index: {fear_index}/100\n\n"
        )
    except Exception as e:
        logger.error(f"Error fetching crypto market data: {e}")
        return "*💰 CRYPTO MARKET:*\nMarket data temporarily unavailable.\n\n"

def fetch_big_cap_prices():
    """Fetch top cryptocurrency prices."""
    ids = "bitcoin,ethereum,ripple,binancecoin,solana,tron,dogecoin,cardano"
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": ids}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        msg = "*💎 Big Cap Crypto:*\n"
        for c in data:
            price = c.get('current_price', 0)
            change = c.get('price_change_percentage_24h', 0)
            symbol = c.get('symbol', '').upper()
            
            if price >= 1:
                price_str = f"${price:.2f}"
            elif price >= 0.0001:
                price_str = f"${price:.4f}"
            elif price >= 0.000001:
                price_str = f"${price:.6f}"
            else:
                price_str = f"${price:.8f}"
                
            msg += f"{symbol}: {price_str} ({change:+.2f}%)\n"
        return msg + "\n"
    except Exception as e:
        logger.error(f"Error fetching big cap prices: {e}")
        return "*💎 Big Cap Crypto:*\nPrices temporarily unavailable.\n\n"

def fetch_top_movers():
    """Fetch top crypto gainers and losers."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd", 
            "order": "market_cap_desc", 
            "per_page": 100,
            "page": 1
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Filter out coins with null price changes
        valid_data = [c for c in data if c.get("price_change_percentage_24h") is not None]
        
        gainers = sorted(valid_data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
        losers = sorted(valid_data, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]

        msg = "*📈 Crypto Top 5 Gainers:*\n"
        for i, c in enumerate(gainers, 1):
            name = c.get('name', 'Unknown')
            price = c.get('current_price', 0)
            change = c.get('price_change_percentage_24h', 0)
            
            if price >= 1:
                price_str = f"${price:.2f}"
            elif price >= 0.0001:
                price_str = f"${price:.4f}"
            elif price >= 0.000001:
                price_str = f"${price:.6f}"
            else:
                price_str = f"${price:.8f}"
                
            msg += f"{i}. {name} {price_str} ({change:+.2f}%)\n"

        msg += "\n*📉 Crypto Top 5 Losers:*\n"
        for i, c in enumerate(losers, 1):
            name = c.get('name', 'Unknown')
            price = c.get('current_price', 0)
            change = c.get('price_change_percentage_24h', 0)
            
            if price >= 1:
                price_str = f"${price:.2f}"
            elif price >= 0.0001:
                price_str = f"${price:.4f}"
            elif price >= 0.000001:
                price_str = f"${price:.6f}"
            else:
                price_str = f"${price:.8f}"
                
            msg += f"{i}. {name} {price_str} ({change:+.2f}%)\n"

        return msg + "\n"
    except Exception as e:
        logger.error(f"Error fetching top movers: {e}")
        return "*📈📉 Top Movers:*\nData temporarily unavailable.\n\n"

# ===================== WEATHER DATA =====================

def get_weather_data(city="Dhaka"):
    """Fetch weather data for a city."""
    try:
        api_key = Config.WEATHERAPI_KEY
        if not api_key:
            return "☀️ WEATHER NOW\nWeather API key not configured.\n\n"
            
        url = f"http://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": city,
            "aqi": "yes"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        current = data.get('current', {})
        location = data.get('location', {})
        
        temp_c = current.get('temp_c', 'N/A')
        condition = current.get('condition', {}).get('text', 'N/A')
        humidity = current.get('humidity', 'N/A')
        wind_kph = current.get('wind_kph', 'N/A')
        wind_dir = current.get('wind_dir', 'N/A')
        uv = current.get('uv', 'N/A')
        visibility_km = current.get('vis_km', 'N/A')
        
        # Get additional weather data
        feels_like = current.get('feelslike_c', temp_c)
        
        # Format UV Index properly
        if uv != 'N/A':
            try:
                uv_value = float(uv)
                if uv_value == 0:
                    uv_display = f"Minimal ({uv_value})"
                elif uv_value <= 2:
                    uv_display = f"Low ({uv_value})"
                elif uv_value <= 5:
                    uv_display = f"Moderate ({uv_value})"
                elif uv_value <= 7:
                    uv_display = f"High ({uv_value})"
                elif uv_value <= 10:
                    uv_display = f"Very High ({uv_value})"
                else:
                    uv_display = f"Extreme ({uv_value})"
            except:
                uv_display = str(uv)
        else:
            uv_display = "N/A"
        
        # Air quality with value
        aqi = current.get('air_quality', {})
        us_epa_index = aqi.get('us-epa-index', 'N/A')
        
        aqi_levels = {1: "Good", 2: "Moderate", 3: "Unhealthy", 4: "Unhealthy", 5: "Very Unhealthy", 6: "Hazardous"}
        aqi_text = aqi_levels.get(us_epa_index, "N/A")
        if us_epa_index != 'N/A':
            aqi_display = f"{aqi_text} ({us_epa_index})"
        else:
            aqi_display = "N/A"
        
        # Visibility with description for driving conditions
        if visibility_km != 'N/A':
            try:
                vis_value = float(visibility_km)
                # Based on real-world driving visibility standards:
                # - 5km+ is generally safe for normal driving
                # - Below 5km requires caution and reduced speed
                if vis_value >= 5:
                    vis_description = "clear"
                else:
                    vis_description = "unclear"
                vis_display = f"{visibility_km} km ({vis_description})"
            except:
                vis_display = f"{visibility_km} km"
        else:
            vis_display = "N/A"
        
        weather_msg = (
            f"☀️ WEATHER\n"
            f"🌡️ Temperature: {temp_c}°C - {feels_like}°C\n"
            f"☁️ Condition: {condition}\n"
            f"💧 Humidity: {humidity}%\n"
            f"💨 Wind: {wind_kph} km/h {wind_dir}\n"
            f"👁️ Visibility: {vis_display}\n"
            f"🌬️ Air Quality: {aqi_display}\n"
            f"☀️ UV Index: {uv_display}"
        )
        
        return weather_msg
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return "☀️ WEATHER NOW\nWeather data temporarily unavailable."

# ===================== HOLIDAYS DATA =====================

def get_bd_holidays():
    """Fetch Bangladesh holidays for today."""
    try:
        api_key = Config.CALENDARIFIC_API_KEY
        if not api_key:
            return ""
            
        today = datetime.now()
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
        holidays = data.get('response', {}).get('holidays', [])
        
        if holidays:
            holiday_names = [h.get('name', 'Holiday') for h in holidays]
            return f"🎉 Today's Holiday: {', '.join(holiday_names)}\n\n"
        else:
            return ""
            
    except Exception as e:
        logger.debug(f"Error fetching holidays: {e}")
        return ""

# ===================== ADVANCED CRYPTO ANALYSIS =====================

def calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index) from price data."""
    if len(prices) < period + 1:
        return 50  # Default neutral RSI if not enough data
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50
        
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

def calculate_support_resistance(prices):
    """Calculate basic support and resistance levels."""
    if len(prices) < 5:
        return None, None
    
    # Simple method: recent low/high over last period
    recent_prices = prices[-20:] if len(prices) >= 20 else prices
    support = min(recent_prices)
    resistance = max(recent_prices)
    
    return support, resistance

def get_sentiment_signal(price_change, volume_24h, rsi, ma_signal):
    """Generate trading sentiment and signal based on multiple factors."""
    score = 0
    
    # Price change factor
    if price_change > 10:
        score += 3
    elif price_change > 5:
        score += 2
    elif price_change > 0:
        score += 1
    elif price_change > -5:
        score -= 1
    else:
        score -= 2
    
    # Volume factor (simplified)
    if volume_24h > 1e9:  # >$1B volume
        score += 1
    
    # RSI factor
    if rsi > 70:
        score -= 1  # Overbought
    elif rsi < 30:
        score += 1  # Oversold
    
    # MA signal factor
    if ma_signal == "bullish":
        score += 1
    elif ma_signal == "bearish":
        score -= 1
    
    # Generate signal
    if score >= 4:
        return "🟢 BUY", "Strong bullish momentum across all indicators"
    elif score >= 2:
        return "🟠 HOLD", "Bullish trend intact, but some caution advised"
    elif score >= 0:
        return "🟡 WATCH", "Mixed signals, wait for clearer direction"
    elif score >= -2:
        return "🟠 HOLD", "Bearish pressure building, consider reducing exposure"
    else:
        return "🔴 SELL", "Strong bearish signals across multiple indicators"

def get_rsi_interpretation(rsi):
    """Get RSI interpretation with trading advice."""
    if rsi >= 70:
        return f"Overbought → caution advised"
    elif rsi <= 30:
        return f"Oversold → potential buying opportunity"
    elif rsi >= 50:
        return f"Bullish momentum"
    else:
        return f"Bearish momentum"

def fetch_coin_detailed_stats(coin_symbol):
    """
    Fetch comprehensive cryptocurrency statistics and analysis.
    
    Args:
        coin_symbol (str): Cryptocurrency symbol (e.g., 'pepe', 'bitcoin', 'ethereum')
        
    Returns:
        str: Formatted detailed analysis message
    """
    try:
        # First get coin ID from symbol
        search_url = "https://api.coingecko.com/api/v3/search"
        search_params = {"query": coin_symbol}
        search_response = requests.get(search_url, params=search_params, timeout=10)
        
        if search_response.status_code != 200:
            return f"❌ Unable to find coin: {coin_symbol.upper()}"
        
        search_data = search_response.json()
        
        # Find the best match
        coin_id = None
        coin_name = None
        
        for coin in search_data.get('coins', []):
            if (coin.get('symbol', '').lower() == coin_symbol.lower() or 
                coin.get('id', '').lower() == coin_symbol.lower() or
                coin.get('name', '').lower() == coin_symbol.lower()):
                coin_id = coin.get('id')
                coin_name = coin.get('name')
                break
        
        if not coin_id:
            return f"❌ Coin not found: {coin_symbol.upper()}"
        
        # Get detailed market data
        market_url = "https://api.coingecko.com/api/v3/coins/markets"
        market_params = {
            "vs_currency": "usd",
            "ids": coin_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "1h,24h,7d,30d"
        }
        
        market_response = requests.get(market_url, params=market_params, timeout=10)
        market_response.raise_for_status()
        market_data = market_response.json()
        
        if not market_data:
            return f"❌ No market data available for {coin_symbol.upper()}"
        
        coin = market_data[0]
        
        # Get historical price data for technical analysis
        history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        history_params = {
            "vs_currency": "usd",
            "days": "30",
            "interval": "daily"
        }
        
        try:
            history_response = requests.get(history_url, params=history_params, timeout=10)
            history_data = history_response.json()
            prices = [price[1] for price in history_data.get('prices', [])]
        except:
            prices = [coin.get('current_price', 0)] * 30  # Fallback
        
        # Extract data
        symbol = coin.get('symbol', '').upper()
        name = coin.get('name', 'Unknown')
        current_price = coin.get('current_price', 0)
        price_change_24h = coin.get('price_change_percentage_24h', 0)
        price_change_1h = coin.get('price_change_percentage_1h', 0)
        price_change_7d = coin.get('price_change_percentage_7d', 0)
        price_change_30d = coin.get('price_change_percentage_30d', 0)
        market_cap = coin.get('market_cap', 0)
        volume_24h = coin.get('total_volume', 0)
        market_cap_rank = coin.get('market_cap_rank', 'N/A')
        
        # Format price based on value
        if current_price >= 1:
            price_str = f"${current_price:.2f}"
        elif current_price >= 0.01:
            price_str = f"${current_price:.4f}"
        elif current_price >= 0.000001:
            price_str = f"${current_price:.6f}"
        else:
            price_str = f"${current_price:.8f}"
        
        # Direction indicator
        direction = "▲" if price_change_24h > 0 else "▼" if price_change_24h < 0 else "→"
        
        # Technical analysis
        rsi = calculate_rsi(prices)
        support, resistance = calculate_support_resistance(prices)
        
        # Support/Resistance formatting
        if support and resistance:
            if support >= 1:
                support_str = f"${support:.2f}"
            elif support >= 0.01:
                support_str = f"${support:.4f}"
            else:
                support_str = f"${support:.6f}"
                
            if resistance >= 1:
                resistance_str = f"${resistance:.2f}"
            elif resistance >= 0.01:
                resistance_str = f"${resistance:.4f}"
            else:
                resistance_str = f"${resistance:.6f}"
        else:
            support_str = "N/A"
            resistance_str = "N/A"
        
        # Moving Average Signal (simplified)
        if len(prices) >= 30:
            ma_30 = sum(prices[-30:]) / 30
            ma_signal = "bullish" if current_price > ma_30 else "bearish"
            ma_signal_text = "Price above MA → bullish signal" if ma_signal == "bullish" else "Price below MA → bearish signal"
        else:
            ma_signal = "neutral"
            ma_signal_text = "Insufficient data for MA analysis"
        
        # Volume analysis
        if volume_24h > 1e9:
            volume_analysis = "High → strong liquidity"
        elif volume_24h > 1e8:
            volume_analysis = "Moderate → decent liquidity"
        elif volume_24h > 1e7:
            volume_analysis = "Low → limited liquidity"
        else:
            volume_analysis = "Very Low → poor liquidity"
        
        # Generate sentiment and forecast
        signal, signal_reason = get_sentiment_signal(price_change_24h, volume_24h, rsi, ma_signal)
        
        # Create forecast based on multiple factors
        if price_change_24h > 5 and rsi > 70:
            forecast = f"{name} shows strong upward momentum, but RSI in overbought territory suggests a possible short-term pullback. A retest of support is likely before another push toward resistance. Volume confirms continued interest, but profit-taking could trigger volatility."
        elif price_change_24h > 0 and rsi < 70:
            forecast = f"{name} maintains positive momentum with healthy technical indicators. Current levels suggest room for further upside, though normal market volatility should be expected. Volume and momentum support continued bullish bias."
        elif price_change_24h < -5 and rsi < 30:
            forecast = f"{name} is experiencing significant selling pressure but may be approaching oversold levels. A potential bounce could occur if support holds, though further downside remains possible if key levels break."
        else:
            forecast = f"{name} is in a consolidation phase with mixed signals. Price action suggests uncertainty, with direction likely to be determined by broader market sentiment and volume patterns."
        
        # Build the response message
        response = f"""Price: {symbol} {price_str} ({price_change_24h:+.2f}%) {direction}
Market Summary: {name} is trading at {price_str}, {'up' if price_change_24h > 0 else 'down'} {abs(price_change_24h):.2f}% in the last 24 hours. With a {'massive ' if volume_24h > 5e9 else ''}daily volume of {human_readable_number(volume_24h)} and a {human_readable_number(market_cap)} market cap, the {'memecoin' if symbol in ['PEPE', 'SHIB', 'DOGE', 'FLOKI'] else 'cryptocurrency'} is seeing {'renewed momentum and heightened trading activity' if volume_24h > 1e9 else 'moderate trading interest'}.

Technicals:
- Support: {support_str}
- Resistance: {resistance_str}
- RSI ({rsi}): {get_rsi_interpretation(rsi)}
- 30D MA: {ma_signal_text}
- Volume ({human_readable_number(volume_24h)}): {volume_analysis}
- Sentiment: {'Bullish' if price_change_24h > 0 else 'Bearish'} → fueled by {'price spike + volume surge' if price_change_24h > 5 and volume_24h > 1e9 else 'current market dynamics'}

Forecast (Next 24h):
{forecast}

Bot Signal (Next 24h): {signal} → {signal_reason}"""

        return response
        
    except requests.RequestException as e:
        logger.error(f"Error fetching detailed stats for {coin_symbol}: {e}")
        return f"❌ Unable to fetch data for {coin_symbol.upper()}. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error in detailed stats for {coin_symbol}: {e}")
        return f"❌ Error analyzing {coin_symbol.upper()}. Please check the symbol and try again."

# ===================== COMPACT NEWS FORMAT =====================

def get_compact_weather():
    """Get compact weather format for news digest."""
    try:
        weather_data = get_weather_data("Dhaka")
        
        # Extract key data from weather response
        if "☀️ WEATHER" not in weather_data:
            return "☀️ WEATHER\n🌡️ Data unavailable"
        
        lines = weather_data.split('\n')
        temp_line = ""
        condition_line = ""
        aqi_line = ""
        uv_line = ""
        
        for line in lines:
            if line.startswith('🌡️ Temperature:'):
                # Extract temperature: "25.1°C - 30.1°C" -> "24.8°C"
                temp_part = line.split(': ')[1].split(' - ')[0] if ': ' in line else "N/A"
                temp_line = temp_part
            elif line.startswith('☁️ Condition:'):
                condition_line = line.split(': ')[1] if ': ' in line else "N/A"
            elif line.startswith('🌬️ Air Quality:'):
                # Extract AQI: "Moderate (2)" -> "(98)"
                aqi_part = line.split(': ')[1] if ': ' in line else "N/A"
                aqi_line = aqi_part
            elif line.startswith('☀️ UV Index:'):
                # Extract UV: "Low (1.2)" -> "Low (0.0/11)"
                uv_part = line.split(': ')[1] if ': ' in line else "N/A"
                if uv_part != "N/A" and "(" in uv_part:
                    uv_value = uv_part.split('(')[1].split(')')[0]
                    uv_level = uv_part.split('(')[0].strip()
                    uv_line = f"{uv_level} ({uv_value}/11)"
                else:
                    uv_line = uv_part
        
        compact_weather = (
            f"☀️ WEATHER\n"
            f"🌡️ {temp_line} | ☁️ {condition_line}\n"
            f"🫧 Air: {aqi_line}\n"
            f"🔆 UV: {uv_line}"
        )
        
        return compact_weather
        
    except Exception as e:
        logger.error(f"Error creating compact weather: {e}")
        return "☀️ WEATHER\n🌡️ Data unavailable"

def get_compact_crypto_market():
    """Get compact crypto market format for news digest."""
    try:
        crypto_data = fetch_crypto_market()
        
        # Parse the crypto data to extract key values
        lines = crypto_data.split('\n')
        market_cap = "N/A"
        volume = "N/A"
        fear_greed = "N/A"
        
        for line in lines:
            if "Market Cap" in line and "24h" in line:
                # Extract: "Market Cap (24h): $3.75T (+0.35%)" -> "$3.75T (+0.35%)"
                parts = line.split(': ')
                if len(parts) > 1:
                    market_cap = parts[1]
            elif "Volume" in line and "24h" in line:
                # Extract: "Volume (24h): $275.19B (+0.35%)" -> "$275.19B (+0.35%)"
                parts = line.split(': ')
                if len(parts) > 1:
                    volume = parts[1]
            elif "Fear/Greed Index" in line:
                # Extract: "Fear/Greed Index: 71/100" -> "71/100"
                parts = line.split(': ')
                if len(parts) > 1:
                    fear_greed = parts[1]
        
        # Determine trend symbol and sentiment
        market_symbol = "▲" if "(+" in market_cap else "▼" if "(-" in market_cap else "→"
        volume_symbol = "▲" if "(+" in volume else "▼" if "(-" in volume else "→"
        
        # Determine sentiment from Fear/Greed index
        try:
            fg_value = int(fear_greed.split('/')[0]) if '/' in fear_greed else 50
            if fg_value >= 75:
                sentiment = "🟢 BUY"
            elif fg_value >= 55:
                sentiment = "🟠 HOLD"
            elif fg_value >= 25:
                sentiment = "🟡 WATCH"
            else:
                sentiment = "🔴 SELL"
        except:
            sentiment = "🟡 WATCH"
        
        compact_crypto = (
            f"💰 CRYPTO MARKET: [SEE MORE]\n"
            f"Market Cap: {market_cap} {market_symbol}\n"
            f"Volume: {volume} {volume_symbol}\n"
            f"Fear/Greed: {fear_greed} = {sentiment}"
        )
        
        return compact_crypto
        
    except Exception as e:
        logger.error(f"Error creating compact crypto market: {e}")
        return "💰 CRYPTO MARKET: [SEE MORE]\nData temporarily unavailable"

def get_compact_news_section(section_title, entries, limit=4, lang='en'):
    """
    Format news entries into compact format with [SEE MORE] button and [Details] links.
    For local and sports news, use Bangla headlines if available.
    Args:
        section_title (str): Title of the section
        entries (list): List of news entries
        limit (int): Maximum number of entries to include
        lang (str): 'en' for English, 'bn' for Bangla
    Returns:
        str: Formatted compact section
    """
    if not entries:
        return f"{section_title}: [SEE MORE]\nNo recent news available."

    formatted = f"{section_title}: [SEE MORE]\n"

    for i, entry in enumerate(entries[:limit], 1):
        # For Bangla, use 'title_bn' if available, else fallback to 'title'
        if lang == 'bn' and entry.get('title_bn'):
            title = entry.get('title_bn', 'No title')
        else:
            title = entry.get('title', 'No title')
        source = entry.get('source', 'Unknown')
        time_ago = entry.get('time_ago', 'Unknown')
        link = entry.get('link', '')

        # Truncate title if too long
        if len(title) > 80:
            title = title[:77] + "..."

        # Make title clickable if link available and add [Details]
        if link:
            formatted += f"{i}. [{title}]({link}) - {source} ({time_ago}) [Details]\n"
        else:
            formatted += f"{i}. {title} - {source} ({time_ago}) [Details]\n"

    return formatted

def get_compact_news_digest():
    """
    Generate a compact news digest for the /news command.
    Returns:
        str: Compact formatted news digest
    """
    try:
        from datetime import datetime
        from utils.time_utils import get_bd_now, get_bd_time_str
        # Get current time in Bangladesh timezone (UTC+6) - FIXED
        bd_now = get_bd_now()
        timestamp = get_bd_time_str(bd_now)
        # Header
        digest = f"📢 TOP NEWS HEADLINES\n{timestamp}\n"
        # Add holiday information if available
        holiday_info = get_bd_holidays().strip()
        if holiday_info:
            digest += holiday_info + "\n"
        digest += "\n"
        # Fetch news entries first
        local_entries = fetch_rss_entries({
            "Prothom Alo": "https://www.prothomalo.com/feed",
            "The Daily Star": "https://www.thedailystar.net/frontpage/rss.xml",
            "BDNews24": "https://bdnews24.com/feed",
            "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
            "Kaler Kantho": "https://www.kalerkantho.com/rss.xml",
            "Samakal": "https://samakal.com/rss.xml"
        }, limit=8, max_age_hours=6)
        global_entries = fetch_rss_entries({
            "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
            "CNN": "http://rss.cnn.com/rss/edition.rss",
            "Reuters": "http://feeds.reuters.com/reuters/topNews",
            "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "New York Post": "https://nypost.com/feed/"
        }, limit=8, max_age_hours=6)
        tech_entries = fetch_rss_entries({
            "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
            "The Verge": "https://www.theverge.com/rss/index.xml",
            "Wired": "https://www.wired.com/feed/rss",
            "CNET": "https://www.cnet.com/rss/news/"
        }, limit=8, max_age_hours=8)
        sports_entries = fetch_rss_entries({
            "ESPN": "https://www.espn.com/espn/rss/news",
            "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
            "Sky Sports": "https://www.skysports.com/rss/12040",
            "সমকাল খেলা": "https://samakal.com/sports/rss.xml",
            "প্রথম আলো খেলা": "https://www.prothomalo.com/sports/feed"
        }, limit=8, max_age_hours=12)
        finance_entries = fetch_rss_entries({
            "Reuters Business": "http://feeds.reuters.com/reuters/businessNews",
            "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
            "প্রথম আলো অর্থনীতি": "https://www.prothomalo.com/business/feed",
            "বণিক বার্তা": "https://www.bonikbarta.net/feed"
        }, limit=8, max_age_hours=8)
        # Add compact weather
        digest += get_compact_weather() + "\n\n"
        # Add sections with [SEE MORE] and [Details], Bangla for local/sports
        digest += get_compact_news_section("🇧�� LOCAL NEWS", local_entries, lang='bn') + "\n"
        digest += get_compact_news_section("🌍 GLOBAL NEWS", global_entries, lang='en') + "\n"
        digest += get_compact_news_section("🚀 TECH NEWS", tech_entries, lang='en') + "\n"
        digest += get_compact_news_section("🏆 SPORTS NEWS", sports_entries, lang='bn') + "\n"
        digest += get_compact_news_section("💼 FINANCE NEWS", finance_entries, lang='en') + "\n"
        # Compact crypto market with [SEE MORE] for /cryptostats
        crypto_market = get_compact_crypto_market()
        digest += crypto_market + "\n"
        # Footer with proper spacing
        digest += "\n📌 Quick Navigation:\n"
        digest += "Type /help for complete command list or the commands (e.g., /local, /global, /tech, /sports, /finance, /weather, /cryptostats, /btc, btcstats etc.)\n\n"
        digest += "━━━━━━━━━━━━━━\n"
        digest += "🤖 By Shanchoy Noor"
        # Ensure nothing is appended after the credit line
        return digest.strip()
    except Exception as e:
        logger.error(f"Error generating compact news digest: {e}")
        return "📢 NEWS DIGEST\nTemporarily unavailable. Please try again later."

# ===================== EXISTING CRYPTO DATA =====================

def get_category_news(category, limit=10):
    """
    Get detailed news for a specific category.
    
    Args:
        category (str): Category type ('local', 'global', 'tech', 'sports', 'finance')
        limit (int): Number of news items to return
        
    Returns:
        str: Formatted news list for the category
    """
    try:
        if category == 'local':
            sources = {
                "Prothom Alo": "https://www.prothomalo.com/feed",
                "The Daily Star": "https://www.thedailystar.net/frontpage/rss.xml",
                "BDNews24": "https://bdnews24.com/feed",
                "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
                "Jugantor": "https://www.jugantor.com/rss.xml",
                "Samakal": "https://samakal.com/rss.xml"
            }
            title = "🇧🇩 LOCAL NEWS"
            
        elif category == 'global':
            sources = {
                "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
                "CNN": "http://rss.cnn.com/rss/edition.rss",
                "Reuters": "http://feeds.reuters.com/reuters/topNews",
                "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
                "The Guardian": "https://www.theguardian.com/world/rss",
                "New York Post": "https://nypost.com/feed/"
            }
            title = "🌍 GLOBAL NEWS"
            
        elif category == 'tech':
            sources = {
                "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
                "The Verge": "https://www.theverge.com/rss/index.xml",
                "Wired": "https://www.wired.com/feed/rss",
                "CNET": "https://www.cnet.com/rss/news/",
                "Ars Technica": "http://feeds.arstechnica.com/arstechnica/index/",
                "Engadget": "https://www.engadget.com/rss.xml",
                "TechRadar": "https://www.techradar.com/rss",
                "ZDNet": "https://www.zdnet.com/news/rss.xml"
            }
            title = "🚀 TECH NEWS"
            
        elif category == 'sports':
            sources = {
                "ESPN": "https://www.espn.com/espn/rss/news",
                "Sky Sports": "https://www.skysports.com/rss/12040",
                "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
                "Yahoo Sports": "https://sports.yahoo.com/rss/",
                "The Guardian Sport": "https://www.theguardian.com/sport/rss",
                "সমকাল খেলা": "https://samakal.com/sports/rss.xml",
                "প্রথম আলো খেলা": "https://www.prothomalo.com/sports/feed"
            }
            title = "🏆 SPORTS NEWS"
            
        elif category == 'finance':
            # Mix of international and local sources
            sources = {
                "Reuters Business": "http://feeds.reuters.com/reuters/businessNews",
                "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
                "Yahoo Finance": "https://feeds.finance.yahoo.com/rss/2.0/headline",
                "প্রথম আলো অর্থনীতি": "https://www.prothomalo.com/business/feed",
                "বণিক বার্তা": "https://www.bonikbarta.net/feed",
                "ফিন্যান্সিয়াল এক্সপ্রেস": "https://thefinancialexpress.com.bd/feed"
            }
            title = "💼 FINANCE NEWS"
            
        else:
            return f"❌ Unknown category: {category}"
        
        # Fetch entries with more reasonable age limits
        if category in ['local', 'global']:
            max_age = 12  # 12 hours for local/global news
        elif category == 'tech':
            max_age = 24  # 24 hours for tech news
        elif category == 'sports':
            max_age = 48  # 48 hours for sports news
        elif category == 'finance':
            max_age = 24  # 24 hours for finance news
        else:
            max_age = 12
            
        entries = fetch_rss_entries(sources, limit=15, max_age_hours=max_age)  # Get more to ensure we have enough
        
        if not entries:
            return f"{title}\nNo news available at the moment."
        
        # Format the response
        response = f"{title}\n"
        response += "━━━━━━━━━━━━━━\n"
        
        for i, entry in enumerate(entries[:limit], 1):
            title_text = entry.get('title', 'No title')
            source = entry.get('source', 'Unknown')
            time_ago = entry.get('time_ago', 'Unknown')
            
            # Truncate title if too long
            if len(title_text) > 100:
                title_text = title_text[:97] + "..."
            
            response += f"{i}. {title_text} - {source} ({time_ago})\n"
        
        response += "\nType /news to go back to main digest."
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching {category} news: {e}")
        return f"❌ Error fetching {category} news. Please try again later."

def analyze_news_item(title, summary="", source=""):
    """
    Generate AI analysis for a specific news item.
    
    Args:
        title (str): News headline
        summary (str): News summary/content
        source (str): News source
        
    Returns:
        str: AI analysis of the news item
    """
    try:
        # Simple AI analysis based on keywords and content
        analysis = f"📰 NEWS ANALYSIS\n"
        analysis += f"━━━━━━━━━━━━━━\n"
        analysis += f"Headline: {title[:150]}{'...' if len(title) > 150 else ''}\n\n"
        
        # Determine category and impact
        title_lower = title.lower()
        summary_lower = summary.lower()
        combined_text = f"{title_lower} {summary_lower}"
        
        # Category detection
        if any(word in combined_text for word in ['crypto', 'bitcoin', 'ethereum', 'blockchain', 'defi']):
            category = "💰 Cryptocurrency/Finance"
            impact = "Could affect crypto markets and digital asset prices"
        elif any(word in combined_text for word in ['war', 'conflict', 'military', 'attack', 'bomb']):
            category = "⚔️ Conflict/Security"
            impact = "May have geopolitical implications and market volatility"
        elif any(word in combined_text for word in ['economy', 'inflation', 'gdp', 'market', 'stock']):
            category = "📈 Economic"
            impact = "Likely to influence financial markets and economic indicators"
        elif any(word in combined_text for word in ['tech', 'ai', 'artificial intelligence', 'technology', 'startup']):
            category = "🚀 Technology"
            impact = "Could impact tech sector and innovation trends"
        elif any(word in combined_text for word in ['health', 'medical', 'vaccine', 'disease', 'hospital']):
            category = "🏥 Healthcare"
            impact = "May affect public health policies and medical sector"
        elif any(word in combined_text for word in ['election', 'political', 'government', 'policy', 'minister']):
            category = "🏛️ Political"
            impact = "Could influence political landscape and policy decisions"
        elif any(word in combined_text for word in ['sports', 'football', 'cricket', 'olympic', 'championship']):
            category = "🏆 Sports"
            impact = "Relevant for sports enthusiasts and related industries"
        else:
            category = "📰 General News"
            impact = "General interest with potential local/regional impact"
        
        # Sentiment analysis (basic)
        positive_words = ['success', 'win', 'growth', 'improve', 'positive', 'gain', 'boost', 'rise']
        negative_words = ['fail', 'loss', 'decline', 'crash', 'fall', 'crisis', 'problem', 'concern']
        
        pos_count = sum(1 for word in positive_words if word in combined_text)
        neg_count = sum(1 for word in negative_words if word in combined_text)
        
        if pos_count > neg_count:
            sentiment = "🟢 Positive"
        elif neg_count > pos_count:
            sentiment = "🔴 Negative"
        else:
            sentiment = "🟡 Neutral"
        
        # Urgency level
        urgent_words = ['breaking', 'urgent', 'emergency', 'crisis', 'immediate', 'alert']
        if any(word in combined_text for word in urgent_words):
            urgency = "🚨 High - Breaking news requiring immediate attention"
        elif any(word in combined_text for word in ['today', 'now', 'just', 'latest']):
            urgency = "⚡ Medium - Recent development worth monitoring"
        else:
            urgency = "📅 Normal - Regular news update"
        
        # Build analysis
        analysis += f"Category: {category}\n"
        analysis += f"Sentiment: {sentiment}\n"
        analysis += f"Urgency: {urgency}\n\n"
        analysis += f"📊 IMPACT ASSESSMENT:\n{impact}\n\n"
        
        # Key insights
        analysis += f"🔍 KEY INSIGHTS:\n"
        if len(summary) > 50:
            analysis += f"• This story appears to be developing with multiple angles\n"
        if source in ['BBC', 'CNN', 'Reuters', 'Al Jazeera']:
            analysis += f"• Reported by major international outlet ({source})\n"
        elif source in ['Prothom Alo', 'The Daily Star', 'BDNews24']:
            analysis += f"• Local Bangladesh coverage from {source}\n"
        
        if 'government' in combined_text or 'minister' in combined_text:
            analysis += f"• Involves government/official entities\n"
        if any(word in combined_text for word in ['billion', 'million', 'trillion']):
            analysis += f"• Significant financial figures mentioned\n"
        
        analysis += f"\n💡 RECOMMENDATION:\n"
        if sentiment == "🔴 Negative":
            analysis += f"Monitor for potential impacts and follow-up developments"
        elif sentiment == "🟢 Positive":
            analysis += f"Positive development worth sharing and celebrating"
        else:
            analysis += f"Stay informed as story develops - neutral impact expected"
        
        analysis += f"\n\nSource: {source}\nGenerated: {datetime.now().strftime('%H:%M %Z')}"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing news item: {e}")
        return f"📰 NEWS ANALYSIS\n━━━━━━━━━━━━━━\nSorry, unable to analyze this news item at the moment."

# ===================== EXISTING CRYPTO DATA =====================
