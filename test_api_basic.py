import requests

try:
    print("Testing CoinGecko API...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    
    resp = requests.get(url, params=params)
    print(f"Response status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"Got {len(data)} items")
        
        # Check for None values
        for i, item in enumerate(data):
            change = item.get("price_change_percentage_24h")
            print(f"Item {i+1}: {item.get('symbol')} - change: {change} - type: {type(change)}")
            
except Exception as e:
    print(f"Error: {e}")
