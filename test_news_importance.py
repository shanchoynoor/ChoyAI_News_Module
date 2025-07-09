#!/usr/bin/env python3
"""
Test the improved news fetching with importance scoring.
"""

import sys
import os
sys.path.append('/workspaces/ChoyAI_News_Module')

def test_news_importance():
    """Test the news importance scoring and recent news fetching."""
    
    print("="*60)
    print("TESTING IMPROVED NEWS FETCHING")
    print("="*60)
    
    try:
        from choynews.core.advanced_news_fetcher import (
            get_breaking_local_news, 
            get_breaking_global_news, 
            get_breaking_tech_news,
            calculate_news_importance_score
        )
        
        # Test importance scoring function
        print("\n--- TESTING IMPORTANCE SCORING ---")
        
        # Mock entries for testing
        test_entries = [
            {"title": "Breaking: Major earthquake hits Bangladesh", "source": "BBC"},
            {"title": "Bitcoin surges to new all-time high amid market rally", "source": "CoinDesk"}, 
            {"title": "AI breakthrough: ChatGPT-5 officially launched by OpenAI", "source": "TechCrunch"},
            {"title": "Regular technology review article", "source": "TechCrunch"},
        ]
        
        for i, entry in enumerate(test_entries):
            score = calculate_news_importance_score(entry, entry["source"], i)
            print(f"'{entry['title'][:50]}...': Score = {score}")
        
        print("\n--- TESTING LOCAL NEWS ---")
        try:
            local_news = get_breaking_local_news()
            print("✅ Local news fetched successfully")
            print(f"Sample: {local_news[:200]}...")
        except Exception as e:
            print(f"❌ Local news error: {e}")
        
        print("\n--- TESTING GLOBAL NEWS ---")
        try:
            global_news = get_breaking_global_news()
            print("✅ Global news fetched successfully")
            print(f"Sample: {global_news[:200]}...")
        except Exception as e:
            print(f"❌ Global news error: {e}")
        
        print("\n--- TESTING TECH NEWS ---")
        try:
            tech_news = get_breaking_tech_news()
            print("✅ Tech news fetched successfully")
            print(f"Sample: {tech_news[:200]}...")
        except Exception as e:
            print(f"❌ Tech news error: {e}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ General error: {e}")
    
    print("\n" + "="*60)
    print("NEWS IMPORTANCE TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_news_importance()
