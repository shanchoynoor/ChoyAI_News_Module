import news
import traceback

try:
    # Modified fetch_top_movers_data function
    def fetch_top_movers_data_fixed():
        """Fetch and format top crypto gainers and losers from top 500 coins by market cap."""
        try:
            # Fetch top 500 coins (2 pages, 250 per page)
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params1 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 1}
            params2 = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 250, "page": 2}
            
            import requests
            print("Fetching page 1...")
            resp1 = requests.get(url, params=params1, timeout=10)
            print(f"Response 1 status: {resp1.status_code}")
            
            print("Fetching page 2...")
            resp2 = requests.get(url, params=params2, timeout=10)
            print(f"Response 2 status: {resp2.status_code}")
            
            data1 = resp1.json() if resp1.ok else []
            data2 = resp2.json() if resp2.ok else []
            data = data1 + data2
            
            print(f"Total data items: {len(data)}")
            
            if not isinstance(data, list) or len(data) == 0:
                raise Exception("Invalid CoinGecko response")
            
            # Filter out any items with None price_change_percentage_24h
            filtered_data = [item for item in data if item.get("price_change_percentage_24h") is not None]
            print(f"Filtered data items: {len(filtered_data)}")
            
            if len(filtered_data) == 0:
                raise Exception("No valid price change data found")
            
            # Sort for gainers and losers
            gainers = sorted(filtered_data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
            losers = sorted(filtered_data, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]
            
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
            
            print("Successfully generated top movers message")
            return msg + "\n", ", ".join(gainers_list), ", ".join(losers_list)
            
        except Exception as e:
            print(f"Error in fetch_top_movers_data: {e}")
            traceback.print_exc()
            return "*Top Movers Error:* N/A\n\n", "N/A", "N/A"
    
    # Run the fixed function
    result = fetch_top_movers_data_fixed()
    print("\nFinal Result:")
    print(result[0])
    
except Exception as e:
    print(f"Error in main: {e}")
    traceback.print_exc()
