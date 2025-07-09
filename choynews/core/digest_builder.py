"""
News Digest Builder for Choy News Bot.

This module builds personalized news digests for users.
"""

import logging
from datetime import datetime
from choynews.utils.logging import get_logger

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
    # Apply user preferences if provided
    if user:
        include_crypto = bool(user.get("crypto_alerts", 1))
        include_weather = bool(user.get("weather_info", 1))
        include_world_news = bool(user.get("world_news", 1))
        include_tech_news = bool(user.get("tech_news", 1))
    
    # Build the digest header
    now = datetime.now()
    header = f"*📰 CHOY NEWS DIGEST*\n"
    header += f"*{now.strftime('%A, %B %d, %Y')}*\n\n"
    
    sections = [header]
    
    # Add each section based on preferences
    if include_crypto:
        crypto_section = build_crypto_section()
        if crypto_section:
            sections.append(crypto_section)
    
    if include_weather:
        weather_section = build_weather_section(user)
        if weather_section:
            sections.append(weather_section)
    
    if include_world_news:
        world_news_section = build_world_news_section()
        if world_news_section:
            sections.append(world_news_section)
    
    if include_tech_news:
        tech_news_section = build_tech_news_section()
        if tech_news_section:
            sections.append(tech_news_section)
    
    # Add footer
    footer = "\n\n_Powered by Choy News_"
    sections.append(footer)
    
    # Combine all sections
    digest = "\n\n".join(sections)
    
    return digest

def build_crypto_section():
    """
    Build the cryptocurrency section of the digest.
    
    Returns:
        str: Formatted crypto section in Markdown
    """
    try:
        # Implementation for fetching and formatting crypto data
        section = "*💰 CRYPTOCURRENCY MARKET*\n"
        section += "Market data temporarily unavailable."
        return section
    except Exception as e:
        logger.error(f"Error building crypto section: {e}")
        return None

def build_weather_section(user=None):
    """
    Build the weather section of the digest.
    
    Args:
        user (dict, optional): User data with location preferences
        
    Returns:
        str: Formatted weather section in Markdown
    """
    try:
        # Implementation for fetching and formatting weather data
        section = "*☀️ WEATHER FORECAST*\n"
        section += "Weather data temporarily unavailable."
        return section
    except Exception as e:
        logger.error(f"Error building weather section: {e}")
        return None

def build_world_news_section():
    """
    Build the world news section of the digest.
    
    Returns:
        str: Formatted world news section in Markdown
    """
    try:
        # Implementation for fetching and formatting world news
        section = "*🌍 WORLD NEWS*\n"
        section += "World news temporarily unavailable."
        return section
    except Exception as e:
        logger.error(f"Error building world news section: {e}")
        return None

def build_tech_news_section():
    """
    Build the technology news section of the digest.
    
    Returns:
        str: Formatted tech news section in Markdown
    """
    try:
        # Implementation for fetching and formatting tech news
        section = "*💻 TECHNOLOGY NEWS*\n"
        section += "Technology news temporarily unavailable."
        return section
    except Exception as e:
        logger.error(f"Error building tech news section: {e}")
        return None
