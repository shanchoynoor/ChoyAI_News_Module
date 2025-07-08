import news
import traceback

try:
    # Fetch top 500 coins (2 pages, 250 per page)
    print("Starting full fetch_top_movers_data test with None filtering...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params1 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1}
    params2 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 2}
    
    import requests
    resp1 = requests.get(url, params=params1)
    resp2 = requests.get(url, params=params2)
    
    data1 = resp1.json() if resp1.ok else []
    data2 = resp2.json() if resp2.ok else []
    data = data1 + data2
    
    print(f"Total data items before filtering: {len(data)}")
    
    # Filter out items with None price_change_percentage_24h
    filtered_data = [item for item in data if item.get("price_change_percentage_24h") is not None]
    
    print(f"Total data items after filtering: {len(filtered_data)}")
    print(f"Removed {len(data) - len(filtered_data)} items with None price_change_percentage_24h")
    
    # Sort for gainers and losers
    print("Sorting for gainers and losers...")
    try:
        gainers = sorted(filtered_data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
        losers = sorted(filtered_data, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]
        
        print(f"Top gainer: {gainers[0].get('symbol')} with change: {gainers[0].get('price_change_percentage_24h')}%")
        print(f"Top loser: {losers[0].get('symbol')} with change: {losers[0].get('price_change_percentage_24h')}%")
        
        # Test complete message formatting
        print("Formatting full message...")
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
        
        msg += "\n*🔻 Crypto Top Losers:*\n"
        losers_list = []
        for i, c in enumerate(losers, 1):
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
            losers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        
        print("Final message created successfully:")
        print(msg)
        print("\nGainers string:", ", ".join(gainers_list))
        print("\nLosers string:", ", ".join(losers_list))
        
    except Exception as e:
        print(f"Error in sorting/formatting: {e}")
        traceback.print_exc()
        
except Exception as e:
    print(f"Error in API call: {e}")
    traceback.print_exc()
