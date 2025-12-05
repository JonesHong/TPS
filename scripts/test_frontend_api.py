#!/usr/bin/env python3
"""Test the new frontend API endpoints."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
load_dotenv()


async def test_apis():
    print("=" * 50)
    print("🔍 Testing Frontend API Endpoints")
    print("=" * 50)
    
    from tps.db.connection import DatabaseManager
    from tps.db.dao import TranslationDAO
    
    # Initialize database
    db_manager = await DatabaseManager.get_instance()
    dao = TranslationDAO(db_manager)
    
    # Test 1: Dashboard Stats
    print("\n📊 Test 1: Dashboard Stats")
    print("-" * 30)
    try:
        stats = await dao.get_dashboard_stats(days=30)
        print(f"✅ Dashboard stats retrieved:")
        print(f"   Total Requests: {stats['total_requests']}")
        print(f"   Total Chars: {stats['total_chars']}")
        print(f"   Total Cost: ${stats['total_cost_usd']:.4f}")
        print(f"   Cache Hit Rate: {stats['cache_hit_rate']*100:.1f}%")
        print(f"   Provider Usage: {stats['provider_usage']}")
        print(f"   Daily Trend (last 7 days): {len(stats['daily_trend'])} entries")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Translations List (Pagination)
    print("\n📋 Test 2: Translations List (Pagination)")
    print("-" * 30)
    try:
        items, total = await dao.get_translations_paginated(
            page=1,
            page_size=5
        )
        print(f"✅ Translations retrieved:")
        print(f"   Total: {total}")
        print(f"   Items on page 1: {len(items)}")
        for item in items[:3]:
            print(f"   - [{item.provider}] {item.original_text[:30]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Languages
    print("\n🌐 Test 3: Available Languages")
    print("-" * 30)
    try:
        languages = await dao.get_available_languages()
        print(f"✅ Languages retrieved:")
        print(f"   Source: {languages['source_languages']}")
        print(f"   Target: {languages['target_languages']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Search & Filter
    print("\n🔎 Test 4: Search & Filter")
    print("-" * 30)
    try:
        items, total = await dao.get_translations_paginated(
            page=1,
            page_size=5,
            providers=["deepl"]
        )
        print(f"✅ Filter by DeepL: {total} items found")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ All API tests completed!")
    print("=" * 50)
    
    # Close database
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_apis())
