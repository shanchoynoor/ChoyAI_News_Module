"""
Cryptocurrency Cache Module for Choy News Bot.

This module handles caching cryptocurrency data to reduce API calls
and provide faster responses to users.
"""

import os
import json
import time
from datetime import datetime, timedelta

from utils.logging import get_logger
from utils.config import Config

# Get logger
logger = get_logger(__name__)

# Cache file paths
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
MARKET_CACHE_FILE = os.path.join(CACHE_DIR, "crypto_market_cache.json")
MOVERS_CACHE_FILE = os.path.join(CACHE_DIR, "crypto_movers_cache.json")
BIGCAP_CACHE_FILE = os.path.join(CACHE_DIR, "crypto_bigcap_cache.json")
COINLIST_FILE = os.path.join(CACHE_DIR, "coinlist.json")

# Cache expiration (in seconds)
MARKET_CACHE_EXPIRY = 60 * 30  # 30 minutes
MOVERS_CACHE_EXPIRY = 60 * 15  # 15 minutes
BIGCAP_CACHE_EXPIRY = 60 * 30  # 30 minutes

def ensure_cache_dir():
    """Ensure the cache directory exists."""
    os.makedirs(CACHE_DIR, exist_ok=True)

def save_cache(data, cache_file):
    """
    Save data to cache file.
    
    Args:
        data (dict): Data to cache
        cache_file (str): Path to cache file
    """
    try:
        # Ensure the cache directory exists
        ensure_cache_dir()
        
        # Add timestamp to the cache
        data['_cache_timestamp'] = time.time()
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            
        logger.debug(f"Cache saved to {cache_file}")
    except Exception as e:
        logger.error(f"Error saving cache to {cache_file}: {e}")

def load_cache(cache_file, expiry_seconds):
    """
    Load data from cache file if it exists and is not expired.
    
    Args:
        cache_file (str): Path to cache file
        expiry_seconds (int): Cache expiration time in seconds
        
    Returns:
        dict: Cached data or None if cache is invalid or expired
    """
    try:
        if not os.path.exists(cache_file):
            logger.debug(f"Cache file {cache_file} does not exist")
            return None
            
        with open(cache_file, 'r') as f:
            data = json.load(f)
            
        # Check if cache has timestamp and is not expired
        if '_cache_timestamp' not in data:
            logger.warning(f"Cache file {cache_file} has no timestamp")
            return None
            
        cache_time = data['_cache_timestamp']
        current_time = time.time()
        
        if current_time - cache_time > expiry_seconds:
            logger.debug(f"Cache file {cache_file} has expired")
            return None
            
        logger.debug(f"Using cached data from {cache_file}")
        return data
    except Exception as e:
        logger.error(f"Error loading cache from {cache_file}: {e}")
        return None

def cache_market_data(data):
    """
    Cache overall cryptocurrency market data.
    
    Args:
        data (dict): Market data to cache
    """
    save_cache(data, MARKET_CACHE_FILE)

def get_cached_market_data():
    """
    Get cached cryptocurrency market data.
    
    Returns:
        dict: Cached market data or None if cache is invalid or expired
    """
    return load_cache(MARKET_CACHE_FILE, MARKET_CACHE_EXPIRY)

def cache_movers_data(data):
    """
    Cache cryptocurrency market movers data.
    
    Args:
        data (dict): Movers data to cache
    """
    save_cache(data, MOVERS_CACHE_FILE)

def get_cached_movers_data():
    """
    Get cached cryptocurrency market movers data.
    
    Returns:
        dict: Cached movers data or None if cache is invalid or expired
    """
    return load_cache(MOVERS_CACHE_FILE, MOVERS_CACHE_EXPIRY)

def cache_bigcap_data(data):
    """
    Cache big cap cryptocurrency data.
    
    Args:
        data (dict): Big cap data to cache
    """
    save_cache(data, BIGCAP_CACHE_FILE)

def get_cached_bigcap_data():
    """
    Get cached big cap cryptocurrency data.
    
    Returns:
        dict: Cached big cap data or None if cache is invalid or expired
    """
    return load_cache(BIGCAP_CACHE_FILE, BIGCAP_CACHE_EXPIRY)

def load_coinlist():
    """
    Load the cryptocurrency coin list.
    
    Returns:
        dict: Coin list or empty dict if file doesn't exist or is invalid
    """
    try:
        if not os.path.exists(COINLIST_FILE):
            logger.warning(f"Coin list file {COINLIST_FILE} does not exist")
            return {}
            
        with open(COINLIST_FILE, 'r') as f:
            data = json.load(f)
            
        logger.debug(f"Loaded coin list with {len(data)} coins")
        return data
    except Exception as e:
        logger.error(f"Error loading coin list: {e}")
        return {}

def save_coinlist(data):
    """
    Save the cryptocurrency coin list.
    
    Args:
        data (dict): Coin list data
    """
    try:
        # Ensure the cache directory exists
        ensure_cache_dir()
        
        with open(COINLIST_FILE, 'w') as f:
            json.dump(data, f)
            
        logger.info(f"Saved coin list with {len(data)} coins")
    except Exception as e:
        logger.error(f"Error saving coin list: {e}")

# Ensure cache directory exists when module is imported
ensure_cache_dir()
