#!/usr/bin/env python3
"""Test DeepL client connectivity."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
load_dotenv()


async def test_deepl():
    print("=" * 50)
    print("🔵 Testing DeepL Client")
    print("=" * 50)
    
    from tps.config import settings
    
    if not settings.deepl_api_key:
        print("❌ DEEPL_API_KEY not set")
        return False
    
    print(f"✓ API Key found: {settings.deepl_api_key[:8]}...{settings.deepl_api_key[-4:]}")
    
    try:
        from tps.clients.deepl_client import DeepLClient
        client = DeepLClient()
        
        print("\n📝 Testing translation...")
        result = await client.translate(
            text="Hello, world!",
            source_lang="en",
            target_lang="zh"
        )
        print(f"✅ Translation successful!")
        print(f'   Input: "Hello, world!"')
        print(f'   Output: "{result.text}"')
        print(f"   Chars: {result.char_count}")
        return True
        
    except Exception as e:
        print(f"❌ DeepL Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_deepl())
    sys.exit(0 if success else 1)
