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

def get_hours_ago(published_time_str):
    """Calculate accurate hours ago from published time string."""
    if not published_time_str:
        return "Unknown"
    
    try:
        # Parse various date formats
        if "GMT" in published_time_str or "UTC" in published_time_str:
            # Handle RFC 822 format: "Mon, 25 Nov 2024 14:30:00 GMT"
            pub_time = datetime.strptime(published_time_str.replace("GMT", "").replace("UTC", "").strip(), "%a, %d %b %Y %H:%M:%S")
        elif "T" in published_time_str:
            # Handle ISO format: "2024-11-25T14:30:00Z" or "2024-11-25T14:30:00"
            if published_time_str.endswith('Z'):
                pub_time = datetime.strptime(published_time_str[:-1], "%Y-%m-%dT%H:%M:%S")
            elif '+' in published_time_str:
                # Handle timezone offset
                pub_time = datetime.strptime(published_time_str.split('+')[0], "%Y-%m-%dT%H:%M:%S")
            else:
                pub_time = datetime.strptime(published_time_str[:19], "%Y-%m-%dT%H:%M:%S")
        else:
            # Try other common formats
            try:
                pub_time = datetime.strptime(published_time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # If all else fails, try parsing just the first 19 characters
                pub_time = datetime.strptime(published_time_str[:19], "%Y-%m-%d %H:%M:%S")
        
        # Calculate time difference
        now = datetime.now()
        time_diff = now - pub_time
        
        # Convert to hours
        hours_diff = time_diff.total_seconds() / 3600
        
        if hours_diff < 1:
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
                    time_ago = get_hours_ago(pub_time)
                    
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

# ===================== EXISTING CRYPTO DATA =====================
