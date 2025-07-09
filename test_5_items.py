#!/usr/bin/env python3
"""
Simple test for 5-item news formatting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_format_function():
    """Test the format_news_section function"""
    try:
        from choynews.core.advanced_news_fetcher import format_news_section
        
        # Test with empty entries to see fallback behavior
        result = format_news_section("🇧🇩 LOCAL NEWS", [], limit=5)
        
        print("=== Format Test Results ===")
        print(result)
        print("=== Analysis ===")
        
        lines = result.split('\n')
        numbered_lines = [line for line in lines if line.strip() and line[0].isdigit()]
        
        print(f"Total lines: {len(lines)}")
        print(f"Numbered items: {len(numbered_lines)}")
        
        for i, line in enumerate(numbered_lines):
            print(f"Item {i+1}: {line[:50]}...")
            
        return len(numbered_lines) == 5
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_format_function()
    print(f"\n✅ Test {'PASSED' if success else 'FAILED'}: {'5 items' if success else 'Wrong count'}")
