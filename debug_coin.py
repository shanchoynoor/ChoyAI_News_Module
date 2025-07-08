import news
import traceback

try:
    print("Testing coin stats...")
    result = news.get_coin_stats_ai('btc')
    print(result)
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
