"""
Test script for non-command message handling in the news digest bot.
This script simulates sending a non-command message to the bot and 
verifies that the bot responds with the expected 'please command only from this..' message.
"""

import os
import sys
import json
from news import handle_updates, get_help_text

def test_non_command_handling():
    """
    Test that the bot responds correctly to non-command messages.
    """
    # Initialize a variable to capture the message that would be sent
    sent_messages = []

    # Override the send_telegram function to capture the message without sending it
    def mock_send_telegram(msg, chat_id):
        sent_messages.append({"message": msg, "chat_id": chat_id})
        return True

    # Store the original function to restore it later
    import news
    original_send_telegram = news.send_telegram
    news.send_telegram = mock_send_telegram

    try:
        # Create a mock update with a non-command message
        mock_update = {
            "update_id": 12345,
            "message": {
                "message_id": 67890,
                "from": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "date": 1627984000,
                "text": "hello, this is a non-command message"
            }
        }

        # Create a mock update with an unrecognized command
        mock_update_unknown_command = {
            "update_id": 12346,
            "message": {
                "message_id": 67891,
                "from": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "date": 1627984001,
                "text": "/unknowncommand"
            }
        }

        # Process the mock updates
        print("Testing non-command message handling...")
        handle_updates([mock_update])
        
        print("Testing unrecognized command handling...")
        handle_updates([mock_update_unknown_command])
        
        # Print the results
        print(f"\nTotal messages sent: {len(sent_messages)}")
        
        for i, msg in enumerate(sent_messages):
            print(f"\nMessage {i+1}:")
            print(f"Chat ID: {msg['chat_id']}")
            print(f"Message preview: {msg['message'][:150]}...")
        
        # Check if we received the expected responses
        if len(sent_messages) >= 1:
            if "Hey! Please command only from this.." in sent_messages[0]["message"]:
                print("\n✅ Test 1 PASSED: Bot correctly responded to non-command message")
            else:
                print("\n❌ Test 1 FAILED: Bot did not respond correctly to non-command message")
                
        if len(sent_messages) >= 2:
            if "Unrecognized command" in sent_messages[1]["message"]:
                print("✅ Test 2 PASSED: Bot correctly responded to unrecognized command")
            else:
                print("❌ Test 2 FAILED: Bot did not respond correctly to unrecognized command")
        else:
            print("❌ Test 2 FAILED: Bot did not send a response for the unrecognized command")
            
    finally:
        # Restore the original function
        news.send_telegram = original_send_telegram

if __name__ == "__main__":
    test_non_command_handling()
