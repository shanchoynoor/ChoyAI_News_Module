import news
import traceback

try:
    # Fetch top 500 coins (2 pages, 250 per page)
    print("Starting fetch_top_movers_data test...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params1 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1}
    
    print("Fetching page 1...")
    import requests
    resp1 = requests.get(url, params=params1)
    print(f"Response status: {resp1.status_code}")
    if resp1.status_code != 200:
        print(f"Error response: {resp1.text}")
    else:
        data1 = resp1.json()
        print(f"Received data: {type(data1)}, length: {len(data1) if isinstance(data1, list) else 'not a list'}")
        if isinstance(data1, list) and len(data1) > 0:
            print(f"First item sample: {data1[0].keys()}")
        elif not isinstance(data1, list):
            print(f"Response content: {data1}")
        
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
