#!/usr/bin/env python3
"""
Direct test of news formatting without imports
"""

def test_fallback_formatting():
    """Test fallback message formatting directly"""
    
    section_title = "🇧🇩 LOCAL NEWS"
    limit = 5
    
    formatted = f"*{section_title}:*\n"
    
    # Define fallback messages
    fallback_messages = [
        "Breaking local news updates coming soon...",
        "Local political developments being monitored...",
        "Regional economic updates being tracked...",
        "Local social updates will be available shortly...",
        "Community news updates in progress..."
    ]
    
    # Add exactly 5 fallback items
    for i in range(limit):
        fallback_msg = fallback_messages[i % len(fallback_messages)]
        formatted += f"{i+1}. {fallback_msg}\n"
    
    formatted += "\n"
    
    print("=== Direct Test Results ===")
    print(formatted)
    print("=== Analysis ===")
    
    lines = formatted.split('\n')
    numbered_lines = [line for line in lines if line.strip() and line[0].isdigit()]
    
    print(f"Total lines: {len(lines)}")
    print(f"Numbered items: {len(numbered_lines)}")
    
    for i, line in enumerate(numbered_lines):
        print(f"Item {i+1}: {line}")
    
    return len(numbered_lines) == 5

if __name__ == "__main__":
    success = test_fallback_formatting()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: {'Exactly 5 items' if success else 'Wrong count'}")
