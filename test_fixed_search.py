#!/usr/bin/env python3
import sys
import os
sys.path.append('../bot')

import asyncio
from utils.db_search import search_classifier_db

async def test_fixed_search():
    print("🔧 Testing FIXED TNVED search algorithm...")
    
    # Test cases that were failing before
    test_queries = [
        "оцинкованный профиль для гипсокартона",
        "профиль металлический",
        "стальной профиль",
        "профиль оцинкованный",
        "металлический уголок"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("=" * 50)
        
        try:
            results = await search_classifier_db(query, limit=5)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    code = result.get('code', 'N/A')
                    desc = result.get('description', 'No description')[:80]
                    
                    # Check if this looks like a construction/metal code
                    is_construction = (
                        code.startswith('73') or  # Articles of iron or steel
                        code.startswith('72') or  # Iron and steel
                        'профил' in desc.lower() or
                        'метал' in desc.lower() or
                        'стал' in desc.lower()
                    )
                    
                    status = "✅ CORRECT" if is_construction else "❌ WRONG"
                    print(f"  {i}. {code} -> {desc}... [{status}]")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("🎯 SUMMARY: The search should now return steel/metal profile codes")
    print("   instead of agricultural/potato codes!")

if __name__ == "__main__":
    asyncio.run(test_fixed_search()) 