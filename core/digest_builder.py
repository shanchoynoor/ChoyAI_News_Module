"""
News Digest Builder for Choy News Bot.        # Build the digest header with Bangladesh time
        now = get_bd_now()
        time_str = get_bd_time_str(now)
        header = f"📰 *DAILY NEWS DIGEST*\n{time_str}\n━━━━━━━━━━━━━━━━━━━━━\n\n"is module builds personalized news digests for users.
"""

import logging
from datetime import datetime
from utils.logging import get_logger
from utils.time_utils import get_bd_now, get_bd_time_str

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
        from core.advanced_news_fetcher import (
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
        
        # Get holiday information
        holidays_info = ""
        try:
            holidays_info = get_bd_holidays()
        except Exception as e:
            logger.debug(f"Holiday API failed: {e}")
        
        if not holidays_info.strip():
            # Fallback to manual check for today's holiday
            try:
                from core.advanced_news_fetcher import check_manual_bd_holidays
                manual_holiday = check_manual_bd_holidays(now)
                if manual_holiday:
                    holidays_info = f"🎉 Today: {manual_holiday}\n"
            except Exception as e:
                logger.debug(f"Manual holiday check failed: {e}")
        
        # Build header with proper formatting
        header = f"📢 *TOP NEWS HEADLINES*\n{time_str}\n"
        if holidays_info.strip():
            header += holidays_info
        header += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        sections = []
        
        # Add weather first
        if include_weather:
            weather_section = get_dhaka_weather()
            if weather_section:
                # Weather section already has its own header, don't duplicate
                sections.append(weather_section.strip())
        
        # Add news sections with better error handling
        try:
            local_news = get_breaking_local_news()
            sections.append(local_news if local_news and local_news.strip() else "*🇧🇩 LOCAL NEWS:*\n1. 🔄 Latest breaking local news being monitored...\n2. 📊 Local political developments being tracked...\n3. 💼 Regional economic updates in progress...\n4. 🏛️ Government policy updates being compiled...\n5. 🌟 Community developments being monitored...\n")
        except Exception as e:
            logger.warning(f"Error getting local news: {e}")
            sections.append("*🇧🇩 LOCAL NEWS:*\n1. 📰 News updates will be available shortly...\n2. 🔍 Breaking news being monitored...\n3. 📈 Latest developments being tracked...\n4. ⏰ Updates coming soon...\n5. 📝 News compilation in progress...\n")
        
        if include_world_news:
            try:
                global_news = get_breaking_global_news()
                sections.append(global_news if global_news and global_news.strip() else "*🌍 GLOBAL NEWS:*\n1. 🌍 International breaking news being updated...\n2. 🔥 Global crisis developments being tracked...\n3. 💸 World economic updates coming soon...\n4. 🕊️ International affairs updates in progress...\n5. ⚡ Breaking global events being monitored...\n")
            except Exception as e:
                logger.warning(f"Error getting global news: {e}")
                sections.append("*🌍 GLOBAL NEWS:*\n1. 📰 News updates will be available shortly...\n2. 🔍 Breaking news being monitored...\n3. 📈 Latest developments being tracked...\n4. ⏰ Updates coming soon...\n5. 📝 News compilation in progress...\n")
        
        if include_tech_news:
            try:
                tech_news = get_breaking_tech_news()
                sections.append(tech_news if tech_news and tech_news.strip() else "*🚀 TECH NEWS:*\n1. 💡 Latest technology breakthroughs being analyzed...\n2. 🤖 AI and innovation updates coming soon...\n3. 🔧 Tech industry developments being tracked...\n4. 💰 Startup and venture updates in progress...\n5. 📱 Digital transformation news being compiled...\n")
            except Exception as e:
                logger.warning(f"Error getting tech news: {e}")
                sections.append("*🚀 TECH NEWS:*\n1. 📰 News updates will be available shortly...\n2. 🔍 Breaking news being monitored...\n3. 📈 Latest developments being tracked...\n4. ⏰ Updates coming soon...\n5. 📝 News compilation in progress...\n")
        
        try:
            sports_news = get_breaking_sports_news()
            sections.append(sports_news if sports_news and sports_news.strip() else "*🏆 SPORTS NEWS:*\n1. ⚽ Live sports scores and updates being compiled...\n2. 🏅 League standings and results coming soon...\n3. 🔄 Player transfers and moves being tracked...\n4. 🏟️ Tournament updates in progress...\n5. 📈 Sports analysis and commentary being prepared...\n")
        except Exception as e:
            logger.warning(f"Error getting sports news: {e}")
            sections.append("*🏆 SPORTS NEWS:*\n1. 📰 News updates will be available shortly...\n2. 🔍 Breaking news being monitored...\n3. 📈 Latest developments being tracked...\n4. ⏰ Updates coming soon...\n5. 📝 News compilation in progress...\n")
        
        try:
            crypto_news = get_breaking_crypto_news()
            sections.append(crypto_news if crypto_news and crypto_news.strip() else "*🪙 FINANCE & CRYPTO NEWS:*\n1. 📊 Cryptocurrency market movements being analyzed...\n2. 🔗 DeFi protocol updates being tracked...\n3. ⛓️ Blockchain developments coming soon...\n4. 📜 Digital asset regulatory news in progress...\n5. 💹 Crypto trading insights being compiled...\n")
        except Exception as e:
            logger.warning(f"Error getting crypto news: {e}")
            sections.append("*🪙 FINANCE & CRYPTO NEWS:*\n1. 📰 News updates will be available shortly...\n2. 🔍 Breaking news being monitored...\n3. 📈 Latest developments being tracked...\n4. ⏰ Updates coming soon...\n5. 📝 News compilation in progress...\n")
        
        # Add crypto market data with AI analysis if enabled
        if include_crypto:
            try:
                crypto_market = fetch_crypto_market_with_ai()
                sections.append(crypto_market if crypto_market and crypto_market.strip() else "*💰 CRYPTOCURRENCY MARKET:*\nMarket data temporarily unavailable. Updates coming soon...\n")
            except Exception as e:
                logger.warning(f"Error getting crypto market data: {e}")
                sections.append("*💰 CRYPTOCURRENCY MARKET:*\nMarket data temporarily unavailable. Updates coming soon...\n")
        
        # Combine all sections with proper spacing
        digest = header
        for section in sections:
            if section and section.strip():  # Only add non-empty sections
                # Ensure proper spacing between sections
                if not digest.endswith('\n\n'):
                    digest += '\n'
                digest += section
                if not digest.endswith('\n'):
                    digest += '\n'
        
        # Add footer with proper spacing
        if not digest.endswith('\n'):
            digest += '\n'
        digest += "━━━━━━━━━━━━━━━━━━━━━\n🤖 Developed by Shanchoy Noor\n"
        
        logger.info("Successfully built news digest")
        # Clean and return only the digest content, nothing more
        cleaned_digest = clean_digest_content(digest)
        
        # Additional safety check: ensure no article content leaked through
        final_digest = final_content_safety_check(cleaned_digest)
        
        # Debug logging to track content
        logger.debug(f"Digest length: {len(final_digest)} chars")
        logger.debug(f"Digest ends with: {repr(final_digest[-50:])}")
        
        return final_digest
        
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
        from core.advanced_news_fetcher import fetch_crypto_market_with_ai
        
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
        from core.advanced_news_fetcher import get_dhaka_weather
        
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
        from core.advanced_news_fetcher import get_breaking_global_news
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
        from core.advanced_news_fetcher import get_breaking_tech_news
        return get_breaking_tech_news()
    except Exception as e:
        logger.error(f"Error building tech news section: {e}")
        return "*💻 TECHNOLOGY NEWS*\nTechnology news temporarily unavailable.\n\n"

def clean_digest_content(content):
    """Clean and validate digest content to prevent extra unwanted content."""
    if not content:
        return ""
    
    # Split by the footer marker to ensure nothing appears after it
    footer_marker = "🤖 Developed by [Shanchoy Noor]"
    
    if footer_marker in content:
        # Find the footer and cut everything after the GitHub link
        footer_index = content.find(footer_marker)
        github_end = content.find(")", footer_index)
        if github_end > footer_index:
            # Keep content only up to the end of the GitHub link
            content = content[:github_end + 1]
        else:
            # Fallback: add the GitHub link properly
            content = content[:footer_index] + f"{footer_marker}(https://github.com/shanchoynoor)"
    
    # Remove any stray content that doesn't belong in a news digest
    lines = content.split('\n')
    cleaned_lines = []
    in_valid_section = False
    
    # Define valid section headers that should appear in our digest
    valid_section_markers = [
        '📢', '📰', '🇧🇩', '🌍', '🚀', '🏆', '🪙', '💰', '☀️', '🌤️', '🌡️', 
        '*DAILY NEWS DIGEST*', '*LOCAL NEWS*', '*GLOBAL NEWS*', '*TECH NEWS*', 
        '*SPORTS NEWS*', '*FINANCE & CRYPTO NEWS*', '*CRYPTOCURRENCY MARKET*',
        '*WEATHER FORECAST*', 'Today:', '━━━━━', footer_marker
    ]
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Stop processing once we hit the footer
        if footer_marker in line:
            cleaned_lines.append(original_line)
            break
        
        # Skip empty lines at the start, but keep them within sections
        if not line and not cleaned_lines:
            continue
        
        # Check if this line starts a valid section
        if any(marker in line for marker in valid_section_markers):
            in_valid_section = True
            cleaned_lines.append(original_line)
            continue
        
        # Skip lines that are clearly not part of a news digest
        if not in_valid_section:
            continue
            
        # Skip lines that look like raw RSS content or article body text
        if (
            # URLs or domain patterns
            line.startswith(('http://', 'https://', 'www.')) or
            # Image URLs or HTML image tags
            ('<img' in line.lower() or 'src=' in line.lower() or 
             any(img_ext in line.lower() for img_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']) or
             line.lower().strip().startswith(('data:image', 'blob:'))) or
            # Long text blocks that might be article content (over 200 chars without proper formatting)
            (len(line) > 200 and not line.startswith(('*', '[', '1.', '2.', '3.', '4.', '5.'))) or
            # Lines with common RSS/article patterns
            any(pattern in line.lower() for pattern in [
                'read more at', 'continue reading', 'full article', 'source:', 'reuters.com',
                'cnn.com', 'bbc.com', 'ap.org', 'bloomberg.com', 'published by',
                'copyright', '© ', 'all rights reserved', 'terms of use', 'privacy policy',
                'image:', 'photo:', 'picture:', 'thumbnail:', 'media:'
            ]) or
            # Very long single sentences that look like article content
            (len(line) > 150 and line.count('.') == 1 and line.endswith('.') and 
             not any(num in line for num in ['1.', '2.', '3.', '4.', '5.'])) or
            # Lines that look like metadata or RSS feed info
            (any(word in line.lower() for word in ['feed', 'rss', 'xml', 'syndication']) and 
             not line.startswith(('*', '[', '1.', '2.', '3.', '4.', '5.')))
        ):
            # This looks like stray RSS content, skip it
            logger.debug(f"Filtering out RSS content: {line[:100]}...")
            continue
        
        # Only include numbered list items (1-5) and section headers
        if (line.startswith(('1.', '2.', '3.', '4.', '5.', '*', '�', '🇧🇩', '🌍', '🚀', '🏆', '🪙', '💰', '☀️', '🌤️', '━━━━━')) or
            line == '' or  # Allow empty lines for spacing
            'Today:' in line or  # Holiday info
            any(marker in line for marker in valid_section_markers)):
            cleaned_lines.append(original_line)
        else:
            # Log what we're filtering out for debugging
            logger.debug(f"Filtering out non-digest content: {line[:100]}...")
    
    result = '\n'.join(cleaned_lines).strip()
    
    # Final safety check: ensure we don't have any long paragraphs that snuck through
    final_lines = result.split('\n')
    final_cleaned = []
    
    for line in final_lines:
        # Allow all lines that are clearly part of our format
        if (line.strip() == '' or 
            line.strip().startswith(('*', '1.', '2.', '3.', '4.', '5.', '📢', '🇧🇩', '🌍', '🚀', '🏆', '🪙', '💰', '☀️', '🌤️', '━━━━━')) or
            'Today:' in line or
            footer_marker in line):
            final_cleaned.append(line)
        elif len(line.strip()) > 300:  # Very long lines are likely article content
            logger.debug(f"Final filter: removing long line: {line.strip()[:100]}...")
            continue
        else:
            final_cleaned.append(line)
    
    return '\n'.join(final_cleaned).strip()

def final_content_safety_check(content):
    """Final safety check to remove any remaining unwanted content."""
    if not content:
        return ""
    
    lines = content.split('\n')
    safe_lines = []
    footer_seen = False
    
    for line in lines:
        # Once we see the footer, only include the footer line itself
        if "🤖 Developed by [Shanchoy Noor]" in line:
            safe_lines.append(line)
            footer_seen = True
            break
        
        # Skip any line that looks like raw article content
        stripped = line.strip()
        if not stripped:
            safe_lines.append(line)  # Keep empty lines for formatting
            continue
            
        # Check for patterns that indicate raw article content
        is_article_content = (
            # Very long single paragraphs without proper formatting
            (len(stripped) > 250 and not stripped.startswith(('*', '[', '1.', '2.', '3.', '4.', '5.', '📢', '🇧🇩', '🌍', '🚀', '🏆', '🪙', '💰', '☀️', '🌤️', '━━━━━'))) or
            # Image content or HTML tags
            ('<img' in stripped.lower() or 'src=' in stripped.lower() or 
             '<html' in stripped.lower() or '<div' in stripped.lower() or '<p>' in stripped.lower() or
             any(img_ext in stripped.lower() for img_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']) or
             stripped.lower().startswith(('data:image', 'blob:', 'image:', 'photo:', 'picture:')) or
             'thumbnail' in stripped.lower()) or
            # Article-like sentences ending with attribution
            (len(stripped) > 100 and any(pattern in stripped.lower() for pattern in [
                'according to', 'reuters reports', 'cnn said', 'the report said',
                'officials said', 'sources said', 'the statement read'
            ])) or
            # Copyright and legal text
            any(pattern in stripped.lower() for pattern in [
                'copyright', '©', 'all rights reserved', 'terms of service',
                'privacy policy', 'disclaimer', 'contact us'
            ]) or
            # URLs that aren't part of markdown links
            (('http://' in stripped or 'https://' in stripped) and not '[' in stripped) or
            # RSS feed metadata
            any(pattern in stripped.lower() for pattern in [
                'rss feed', 'subscribe to', 'xml feed', 'syndication'
            ])
        )
        
        if is_article_content:
            logger.debug(f"Final safety check: filtering {stripped[:100]}...")
            continue
        
        safe_lines.append(line)
    
    return '\n'.join(safe_lines).strip()
