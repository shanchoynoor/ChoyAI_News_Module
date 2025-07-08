import requests
import traceback

try:
    print("Testing CoinGecko API with timeout...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    
    print("Sending request...")
    resp = requests.get(url, params=params, timeout=10)
    print(f"Response received: {resp.status_code}")
    
except requests.exceptions.Timeout:
    print("Request timed out after 10 seconds")
except requests.exceptions.ConnectionError:
    print("Connection error - could not connect to the API")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
