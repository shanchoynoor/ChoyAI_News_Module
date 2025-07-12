#!/usr/bin/env python3
"""
Coinlist Update Script for Choy News Bot.

This script fetches the latest cryptocurrency coin list from CoinGecko API
and saves it to the coinlist.json file used by the bot.
"""

import os
import json
import requests
import logging
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging import setup_logging
from utils.config import Config
from data_modules.crypto_cache import save_coinlist

logger = setup_logging(__name__)

def fetch_coinlist():
    """
    Fetch the latest cryptocurrency coin list from CoinGecko API.
    
    Returns:
        dict: Dictionary of coin data with symbol as key
    """
    logger.info("Fetching coin list from CoinGecko API...")
    
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        coins = response.json()
        logger.info(f"Fetched {len(coins)} coins from CoinGecko API")
        
        # Convert to dict with symbol as key
        coin_dict = {}
        for coin in coins:
            symbol = coin.get('symbol', '').lower()
            id = coin.get('id', '')
            name = coin.get('name', '')
            
            if symbol and id and name:
                coin_dict[symbol] = {
                    'id': id,
                    'name': name,
                    'symbol': symbol
                }
        
        logger.info(f"Processed {len(coin_dict)} valid coins")
        return coin_dict
    except Exception as e:
        logger.error(f"Error fetching coin list: {e}")
        return {}

def update_coinlist():
    """
    Update the coinlist.json file with the latest coin data.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Fetch the latest coin data
        coin_dict = fetch_coinlist()
        
        if not coin_dict:
            logger.error("Failed to fetch coin list")
            return False
        
        # Add metadata
        coin_dict['_metadata'] = {
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'count': len(coin_dict) - 1  # Subtract 1 for metadata
        }
        
        # Save to file
        save_coinlist(coin_dict)
        
        logger.info(f"Coinlist updated successfully with {len(coin_dict) - 1} coins")
        return True
    except Exception as e:
        logger.error(f"Error updating coinlist: {e}")
        return False

if __name__ == "__main__":
    result = update_coinlist()
    sys.exit(0 if result else 1)
