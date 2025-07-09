#!/usr/bin/env python3

import sys
import os
sys.path.append('/workspaces/ChoyAI_News_Module')

# Test basic functionality
print("Testing crypto formatting...")

# Mock crypto data for testing format
def test_crypto_format():
    """Test crypto format without API calls."""
    
    crypto_section = """💰 CRYPTO MARKET:
Market Cap (24h): $3.46T (-2.28%)
Volume (24h): $90.40B
Fear/Greed Index: 66/100

💎 Big Cap Crypto:
BTC: $109,140.00 (+0.18%) ▲
ETH: $2,659.12 (+1.65%) ▲
XRP: $2.38 (+3.15%) ▲
BNB: $662.61 (+0.17%) ▲
SOL: $153.45 (+0.91%) ▲
TRX: $0.2892 (+0.99%) ▲
DOGE: $0.1726 (+0.77%) ▲
ADA: $0.6065 (+2.83%) ▲

📈 Crypto Top 5 Gainers:
1. Stellar $0.2895 (+12.07%) ▲
2. SPX6900 $1.45 (+8.06%) ▲
3. POL (ex-MATIC) $0.2027 (+7.13%) ▲
4. Uniswap $8.19 (+5.22%) ▲
5. Hedera $0.1697 (+5.16%) ▲

📉 Crypto Top 5 Losers:
1. Tokenize Xchange $12.34 (-13.42%) ▼
2. Bonk $0.0000 (-10.27%) ▼
3. Cronos $0.0959 (-2.31%) ▼
4. Virtuals Protocol $1.46 (-1.14%) ▼
5. Worldcoin $0.8718 (-1.07%) ▼

"""
    return crypto_section

def test_weather_format():
    """Test weather format."""
    
    weather_section = """🌤️ WEATHER - Dhaka:
🌡️ Temperature: 25.6°C
☁️ Condition: Patchy rain nearby
💧 Humidity: 93%
💨 Wind: 19.4 km/h SE
☀️ UV Index: 0.0
🌬️ Air Quality: Moderate

"""
    return weather_section

def test_holiday_format():
    """Test holiday format."""
    return "🎉 Today's Holiday: Ashari Purnima\n\n"

if __name__ == "__main__":
    print("="*60)
    print("TESTING EXPECTED FORMATTING")
    print("="*60)
    
    print("\n--- CRYPTO MARKET FORMAT ---")
    print(test_crypto_format())
    
    print("--- WEATHER FORMAT ---")
    print(test_weather_format())
    
    print("--- HOLIDAY FORMAT ---")
    print(test_holiday_format())
    
    print("="*60)
    print("FORMATTING TEST COMPLETE")
    print("="*60)
