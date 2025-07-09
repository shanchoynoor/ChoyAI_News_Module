#!/usr/bin/env python3
"""
Test script to verify Telegram bot configuration and connectivity.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_telegram_bot():
    """Test the Telegram bot configuration."""
    
    # Get token from environment
    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ ERROR: No TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN found in environment")
        return False
    
    print(f"✅ Bot token found: {token[:10]}...{token[-5:]}")
    
    # Test bot info
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"✅ Bot is valid: @{bot_info.get('username', 'unknown')}")
            print(f"   Bot name: {bot_info.get('first_name', 'unknown')}")
            print(f"   Bot ID: {bot_info.get('id', 'unknown')}")
            return True
        else:
            print(f"❌ Bot token is invalid: {data.get('description')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        return False

def test_webhook_status():
    """Test webhook status."""
    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    
    try:
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        response = requests.get(url)
        data = response.json()
        
        if data.get("ok"):
            webhook_info = data.get("result", {})
            webhook_url = webhook_info.get("url", "")
            
            if webhook_url:
                print(f"⚠️  WARNING: Webhook is set to: {webhook_url}")
                print("   This might prevent polling from working. Consider removing it.")
                return False
            else:
                print("✅ No webhook set - polling should work")
                return True
        else:
            print(f"❌ Error getting webhook info: {data.get('description')}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking webhook: {e}")
        return False

if __name__ == "__main__":
    print("=== Telegram Bot Test ===")
    
    if test_telegram_bot() and test_webhook_status():
        print("\n✅ Bot configuration looks good!")
        print("\nNext steps:")
        print("1. Start your bot: python3 bin/choynews --service bot")
        print("2. Send a message to your bot on Telegram")
        print("3. Check the logs for any errors")
    else:
        print("\n❌ Bot configuration has issues that need to be fixed.")
