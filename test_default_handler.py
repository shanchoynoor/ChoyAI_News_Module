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
        handle_updates([mock_update])
        handle_updates([mock_update_unknown_command])
        
        # Check if we received the expected responses
        if len(sent_messages) >= 2:
            print("✅ Test 1: Bot responded to a non-command message")
            if "Hey! Please command only from this.." in sent_messages[0]["message"]:
                print("✅ Test 2: Response contains the correct message prefix")
                if get_help_text() in sent_messages[0]["message"]:
                    print("✅ Test 3: Response contains the help text")
                else:
                    print("❌ Test 3: Response does not contain the help text")
            else:
                print("❌ Test 2: Response does not contain the correct message prefix")
                
            if "Unrecognized command" in sent_messages[1]["message"]:
                print("✅ Test 4: Bot responded to an unrecognized command")
                if get_help_text() in sent_messages[1]["message"]:
                    print("✅ Test 5: Response to unrecognized command contains the help text")
                else:
                    print("❌ Test 5: Response to unrecognized command does not contain the help text")
            else:
                print("❌ Test 4: Bot did not respond correctly to an unrecognized command")
        else:
            print("❌ Test failed: Bot did not send the expected number of responses")            print("\nMessages that would be sent:")
            for i, msg in enumerate(sent_messages):
                print(f"\nMessage {i+1}:")
                print(f"Chat ID: {msg['chat_id']}")
                print(f"Message preview: {msg['message'][:150]}...")
                
        # Print everything regardless of previous test outcomes
        if len(sent_messages) == 0:
            print("❌ No messages were sent!")
        elif len(sent_messages) == 1:
            print("⚠️ Only one message was sent, expected at least two (for both test cases)")
        elif len(sent_messages) >= 2:
            print("Total messages sent:", len(sent_messages))
            
    finally:
        # Restore the original function
        news.send_telegram = original_send_telegram

if __name__ == "__main__":
    test_non_command_handling()
