import news
import traceback

try:
    # Fetch top 500 coins (2 pages, 250 per page)
    print("Starting full fetch_top_movers_data test...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params1 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1}
    params2 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 2}
    
    import requests
    resp1 = requests.get(url, params=params1)
    resp2 = requests.get(url, params=params2)
    
    data1 = resp1.json() if resp1.ok else []
    data2 = resp2.json() if resp2.ok else []
    data = data1 + data2
    
    print(f"Total data items: {len(data)}")
    
    # Check for missing price_change_percentage_24h
    missing_changes = sum(1 for item in data if item.get("price_change_percentage_24h") is None)
    print(f"Items missing price_change_percentage_24h: {missing_changes}")
    
    # Sort for gainers and losers
    print("Sorting for gainers and losers...")
    try:
        gainers = sorted(data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
        losers = sorted(data, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]
        
        print(f"Top gainer: {gainers[0].get('symbol')} with change: {gainers[0].get('price_change_percentage_24h')}%")
        print(f"Top loser: {losers[0].get('symbol')} with change: {losers[0].get('price_change_percentage_24h')}%")
        
        # Format message
        print("Formatting messages...")
        msg = "*🔺 Crypto Top Gainers:*\n"
        gainers_list = []
        for i, c in enumerate(gainers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            gainers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        
        print("Final message and list created successfully")
        print(f"First gainer entry: {gainers_list[0]}")
        
    except Exception as e:
        print(f"Error in sorting/formatting: {e}")
        traceback.print_exc()
        
except Exception as e:
    print(f"Error in API call: {e}")
    traceback.print_exc()
