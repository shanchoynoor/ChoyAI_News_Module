"""
Telegram API integration for the Choy News application.

This module provides functions for sending messages and retrieving updates from Telegram.
"""

import requests
import logging
import os
from utils.config import Config
from utils.logging import get_logger

logger = get_logger(__name__)

def send_telegram(message, chat_id, parse_mode="Markdown"):
    """
    Send a message to a Telegram chat.
    
    Args:
        message (str): The message to send
        chat_id (int/str): The Telegram chat ID to send to
        parse_mode (str): The parsing mode for the message text
        
    Returns:
        dict: The response from the Telegram API, or None on error
    """
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if data.get("ok"):
            logger.debug(f"Message sent successfully to chat {chat_id}")
            return data
        else:
            logger.error(f"Failed to send message: {data.get('description')}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending telegram message: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error sending telegram message: {str(e)}")
        return None

def send_telegram_with_markup(text, chat_id, reply_markup):
    try:
        from telegram import Bot
        import asyncio
        bot_token = Config.TELEGRAM_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")
        bot = Bot(token=bot_token)
        asyncio.run(bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown'))
    except Exception as e:
        logger.error(f"Error sending markup message: {e}")

def get_updates(offset=None, timeout=30):
    """
    Get updates from the Telegram API.
    
    Args:
        offset (int, optional): The offset ID for updates
        timeout (int, optional): Long polling timeout in seconds
        
    Returns:
        list: List of update objects, or empty list on error
    """
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/getUpdates"
        payload = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"]
        }
        
        if offset:
            payload["offset"] = offset
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if data.get("ok"):
            return data.get("result", [])
        else:
            logger.error(f"Failed to get updates: {data.get('description')}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error getting telegram updates: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error getting telegram updates: {str(e)}")
        return []