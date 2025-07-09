"""
News Fetcher Module for Choy News Bot.

This module handles fetching news from various RSS sources and external APIs.
"""

import requests
import feedparser
import json
import os
from datetime import datetime, timedelta
from choynews.utils.logging import get_logger
from choynews.utils.config import Config

logger = get_logger(__name__)

def format_time_ago(published_time):
    """Convert published time to relative time format."""
    try:
        if isinstance(published_time, str):
            # Try to parse various time formats
            try:
                pub_time = datetime.strptime(published_time, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                try:
                    pub_time = datetime.strptime(published_time, "%Y-%m-%dT%H:%M:%S%z")
                except:
                    return "Unknown"
        else:
            pub_time = published_time
            
        now = datetime.now()
        diff = now - pub_time.replace(tzinfo=None)
        
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
        return "Unknown"

def fetch_rss_entries(sources, limit=5):
    """
    Fetch RSS entries from multiple sources.
    
    Args:
        sources (dict): Dictionary of source_name: rss_url
        limit (int): Maximum number of entries per source
        
    Returns:
        list: List of news entries with metadata
    """
    all_entries = []
    
    for source_name, rss_url in sources.items():
        try:
            logger.debug(f"Fetching RSS from {source_name}: {rss_url}")
            
            # Set timeout and headers
            headers = {
                'User-Agent': 'ChoyNewsBot/1.0 (+https://github.com/shanchoynoor/ChoyAI_News_Module)'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {source_name}")
                continue
                
            # Process entries
            for entry in feed.entries[:limit]:
                try:
                    # Extract publication time
                    pub_time = entry.get('published', entry.get('updated', ''))
                    time_ago = format_time_ago(pub_time)
                    
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
                        'summary': entry.get('summary', '')[:200] + "..." if entry.get('summary') else ''
                    }
                    
                    all_entries.append(entry_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {e}")
                    continue
                    
        except requests.RequestException as e:
            logger.error(f"Error fetching RSS from {source_name}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error with {source_name}: {e}")
            continue
    
    # Sort by time (newest first) and return
    try:
        all_entries.sort(key=lambda x: x.get('published', ''), reverse=True)
    except:
        pass  # If sorting fails, return as is
        
    return all_entries

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
        "ESPN": "https://www.espn.com/espn/rss/news",
        "Sky Sports": "https://www.skysports.com/rss/12040",
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "NBC Sports": "https://scores.nbcsports.com/rss/headlines.asp",
        "Yahoo Sports": "https://sports.yahoo.com/rss/",
        "The Guardian Sport": "https://www.theguardian.com/sport/rss",
        "Sporting News": "https://www.sportingnews.com/rss"
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
            else:
                price_str = f"${price:.4f}"
                
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
            else:
                price_str = f"${price:.4f}"
                
            msg += f"{i}. {name} {price_str} ({change:+.2f}%)\n"

        msg += "\n*📉 Crypto Top 5 Losers:*\n"
        for i, c in enumerate(losers, 1):
            name = c.get('name', 'Unknown')
            price = c.get('current_price', 0)
            change = c.get('price_change_percentage_24h', 0)
            
            if price >= 1:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.4f}"
                
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
            return "*🌤️ WEATHER:*\nWeather API key not configured.\n\n"
            
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
        
        # Air quality
        aqi = current.get('air_quality', {})
        us_epa_index = aqi.get('us-epa-index', 'N/A')
        
        aqi_levels = {1: "Good", 2: "Moderate", 3: "Unhealthy for Sensitive", 4: "Unhealthy", 5: "Very Unhealthy", 6: "Hazardous"}
        aqi_text = aqi_levels.get(us_epa_index, "N/A")
        
        weather_msg = (
            f"*🌤️ WEATHER - {location.get('name', city)}:*\n"
            f"🌡️ Temperature: {temp_c}°C\n"
            f"☁️ Condition: {condition}\n"
            f"💧 Humidity: {humidity}%\n"
            f"💨 Wind: {wind_kph} km/h {wind_dir}\n"
            f"☀️ UV Index: {uv}\n"
            f"🌬️ Air Quality: {aqi_text}\n\n"
        )
        
        return weather_msg
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return "*🌤️ WEATHER:*\nWeather data temporarily unavailable.\n\n"

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
