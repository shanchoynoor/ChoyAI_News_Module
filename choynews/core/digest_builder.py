"""
News Digest Builder for Choy News Bot.        # Build the digest header with Bangladesh time
        now = get_bd_now()
        time_str = get_bd_time_str(now)
        header = f"📰 *DAILY NEWS DIGEST*\n{time_str}\n━━━━━━━━━━━━━━━━━━━━━\n\n"is module builds personalized news digests for users.
"""

import logging
from datetime import datetime
from choynews.utils.logging import get_logger
from choynews.utils.time_utils import get_bd_now, get_bd_time_str

logger = get_logger(__name__)

def build_news_digest(user=None, include_crypto=True, include_weather=True, include_world_news=True, include_tech_news=True):
    """
    Build a personalized news digest for a user.
    
    Args:
        user (dict, optional): User data dict with preferences
        include_crypto (bool): Whether to include crypto section
        include_weather (bool): Whether to include weather section
        include_world_news (bool): Whether to include world news section
        include_tech_news (bool): Whether to include tech news section
        
    Returns:
        str: Formatted news digest in Markdown format
    """
    try:
        # Import advanced news fetcher functions
        from choynews.core.advanced_news_fetcher import (
            get_breaking_local_news, get_breaking_global_news, get_breaking_tech_news, 
            get_breaking_sports_news, get_breaking_crypto_news, fetch_crypto_market_with_ai,
            get_dhaka_weather, get_bd_holidays
        )
        
        # Apply user preferences if provided
        if user:
            include_crypto = bool(user.get("crypto_alerts", 1))
            include_weather = bool(user.get("weather_info", 1))
            include_world_news = bool(user.get("world_news", 1))
            include_tech_news = bool(user.get("tech_news", 1))
        
        # Build the digest header with Bangladesh time
        now = get_bd_now()
        time_str = get_bd_time_str(now)
        header = f"� *DAILY NEWS DIGEST*\n{time_str}\n\n"
        
        sections = []
        
        # Add weather and holidays first
        if include_weather:
            weather_section = get_dhaka_weather()
            if weather_section:
                sections.append(weather_section)
        
        # Add holidays
        holidays_section = get_bd_holidays()
        if holidays_section:
            sections.append(holidays_section)
        
        # Add news sections
        sections.append(get_breaking_local_news())
        
        if include_world_news:
            sections.append(get_breaking_global_news())
        
        if include_tech_news:
            sections.append(get_breaking_tech_news())
            
        sections.append(get_breaking_sports_news())
        sections.append(get_breaking_crypto_news())
        
        # Add crypto market data with AI analysis if enabled
        if include_crypto:
            sections.append(fetch_crypto_market_with_ai())
        
        # Combine all sections
        digest = header + "".join(sections)
        
        # Add footer
        digest += "\n━━━━━━━━━━━━━━━━━━━━━\n_Built by Shanchoy with 🤖 AI_"
        
        logger.info("Successfully built news digest")
        return digest
        
    except Exception as e:
        logger.error(f"Error building news digest: {e}", exc_info=True)
        return build_fallback_digest()

def build_fallback_digest():
    """Build a fallback digest when the main builder fails."""
    now = datetime.now()
    header = f"📰 *CHOY NEWS DIGEST*\n"
    header += f"*{now.strftime('%A, %B %d, %Y')}*\n\n"
    
    sections = [
        "*💰 CRYPTOCURRENCY MARKET*\nMarket data temporarily unavailable.\n\n",
        "*☀️ WEATHER FORECAST*\nWeather data temporarily unavailable.\n\n", 
        "*🌍 WORLD NEWS*\nWorld news temporarily unavailable.\n\n",
        "*💻 TECHNOLOGY NEWS*\nTechnology news temporarily unavailable.\n\n"
    ]
    
    digest = header + "".join(sections) + "\n\n_Powered by Choy News_"
    return digest

def build_crypto_section():
    """
    Build the cryptocurrency section of the digest.
    
    Returns:
        str: Formatted crypto section in Markdown
    """
    try:
        from choynews.core.advanced_news_fetcher import fetch_crypto_market_with_ai
        
        return fetch_crypto_market_with_ai()
    except Exception as e:
        logger.error(f"Error building crypto section: {e}")
        return "*💰 CRYPTOCURRENCY MARKET*\nMarket data temporarily unavailable.\n\n"

def build_weather_section(user=None):
    """
    Build the weather section of the digest.
    
    Args:
        user (dict, optional): User data with location preferences
        
    Returns:
        str: Formatted weather section in Markdown
    """
    try:
        from choynews.core.advanced_news_fetcher import get_dhaka_weather
        
        # For now, we only support Dhaka weather
        # TODO: Add location-based weather support
        return get_dhaka_weather()
    except Exception as e:
        logger.error(f"Error building weather section: {e}")
        return "*☀️ WEATHER FORECAST*\nWeather data temporarily unavailable.\n\n"

def build_world_news_section():
    """
    Build the world news section of the digest.
    
    Returns:
        str: Formatted world news section in Markdown
    """
    try:
        from choynews.core.advanced_news_fetcher import get_breaking_global_news
        return get_breaking_global_news()
    except Exception as e:
        logger.error(f"Error building world news section: {e}")
        return "*🌍 WORLD NEWS*\nWorld news temporarily unavailable.\n\n"

def build_tech_news_section():
    """
    Build the technology news section of the digest.
    
    Returns:
        str: Formatted tech news section in Markdown
    """
    try:
        from choynews.core.advanced_news_fetcher import get_breaking_tech_news
        return get_breaking_tech_news()
    except Exception as e:
        logger.error(f"Error building tech news section: {e}")
        return "*💻 TECHNOLOGY NEWS*\nTechnology news temporarily unavailable.\n\n"
