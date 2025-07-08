"""
Simple file-based caching module for crypto data to avoid exceeding API rate limits.
"""
import os
import json
import time
import logging
from datetime import datetime

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))
MARKET_CACHE_FILE = os.path.join(CACHE_DIR, "crypto_market_cache.json")
BIGCAP_CACHE_FILE = os.path.join(CACHE_DIR, "crypto_bigcap_cache.json")
MOVERS_CACHE_FILE = os.path.join(CACHE_DIR, "crypto_movers_cache.json")

# Cache expiration times in seconds
MARKET_CACHE_EXPIRY = 15 * 60  # 15 minutes
BIGCAP_CACHE_EXPIRY = 10 * 60  # 10 minutes
MOVERS_CACHE_EXPIRY = 20 * 60  # 20 minutes

def load_cache(cache_file):
    """Load data from cache file if it exists and is not expired."""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            timestamp = cache_data.get('timestamp', 0)
            expiry = cache_data.get('expiry', 0)
            current_time = time.time()
            
            if current_time - timestamp <= expiry:
                logging.info(f"Using cached data from {cache_file}")
                return cache_data.get('data')
            else:
                logging.info(f"Cache expired for {cache_file}")
                return None
        else:
            logging.info(f"No cache file found at {cache_file}")
            return None
    except Exception as e:
        logging.error(f"Error loading cache from {cache_file}: {e}")
        return None

def save_cache(cache_file, data, expiry):
    """Save data to cache file with timestamp and expiry."""
    try:
        cache_data = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'expiry': expiry,
            'data': data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
            
        logging.info(f"Saved data to cache file {cache_file}")
        return True
    except Exception as e:
        logging.error(f"Error saving cache to {cache_file}: {e}")
        return False

# Market data cache functions
def get_market_cache():
    return load_cache(MARKET_CACHE_FILE)

def save_market_cache(data):
    return save_cache(MARKET_CACHE_FILE, data, MARKET_CACHE_EXPIRY)

# Big cap prices cache functions
def get_bigcap_cache():
    return load_cache(BIGCAP_CACHE_FILE)

def save_bigcap_cache(data):
    return save_cache(BIGCAP_CACHE_FILE, data, BIGCAP_CACHE_EXPIRY)

# Top movers cache functions
def get_movers_cache():
    return load_cache(MOVERS_CACHE_FILE)

def save_movers_cache(data):
    return save_cache(MOVERS_CACHE_FILE, data, MOVERS_CACHE_EXPIRY)
