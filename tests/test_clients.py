#!/usr/bin/env python3
"""Test translation clients (Google & OpenAI) connectivity and authentication."""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv

# Load .env if exists
load_dotenv()


async def test_openai():
    """Test OpenAI client connectivity"""
    print("\n" + "=" * 50)
    print("🤖 Testing OpenAI Client")
    print("=" * 50)
    
    from tps.config import settings
    
    if not settings.openai_api_key:
        print("❌ OPENAI_API_KEY not set in .env")
        return False
    
    print(f"✓ API Key found: {settings.openai_api_key[:8]}...{settings.openai_api_key[-4:]}")
    print(f"✓ Translation Model: {settings.openai_translation_model}")
    
    try:
        from tps.clients.openai_client import OpenAIClient
        client = OpenAIClient()
        
        # Test translation
        print("\n📝 Testing translation...")
        result = await client.translate(
            text="Hello, world!",
            source_lang="en",
            target_lang="zh-TW"
        )
        print(f"✅ Translation successful!")
        print(f"   Input: 'Hello, world!'")
        print(f"   Output: '{result.text}'")
        print(f"   Tokens: {result.token_input} in / {result.token_output} out")
        print(f"   Cost: ${result.cost_estimated:.6f}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Error: {type(e).__name__}: {e}")
        return False


async def test_google():
    """Test Google Translate client connectivity"""
    print("\n" + "=" * 50)
    print("🌐 Testing Google Cloud Translation Client")
    print("=" * 50)
    
    from tps.config import settings
    
    # Check credentials
    creds_path = settings.google_application_credentials
    project_id = settings.google_cloud_project
    
    print(f"Credentials Path: {creds_path or '(not set)'}")
    print(f"Project ID: {project_id or '(not set)'}")
    
    if creds_path:
        if os.path.exists(creds_path):
            print(f"✓ Credentials file exists: {creds_path}")
        else:
            print(f"❌ Credentials file NOT found: {creds_path}")
            return False
    else:
        # Check for Application Default Credentials (platform-specific paths)
        adc_paths = [
            os.path.join(os.environ.get("APPDATA", ""), "gcloud", "application_default_credentials.json"),  # Windows
            os.path.expanduser("~/.config/gcloud/application_default_credentials.json"),  # Linux/macOS
        ]
        adc_found = None
        for adc_path in adc_paths:
            if os.path.exists(adc_path):
                adc_found = adc_path
                break
        
        if adc_found:
            print(f"✓ Application Default Credentials found: {adc_found}")
        else:
            print("❌ No credentials configured!")
            print("   Option 1: Set GOOGLE_APPLICATION_CREDENTIALS in .env")
            print("   Option 2: Run: gcloud auth application-default login")
            return False
    
    try:
        from tps.clients.google_client import GoogleTranslateClient
        client = GoogleTranslateClient()
        
        # Test translation
        print("\n📝 Testing translation...")
        result = await client.translate(
            text="Hello, world!",
            source_lang="en",
            target_lang="zh-TW"
        )
        print(f"✅ Translation successful!")
        print(f"   Input: 'Hello, world!'")
        print(f"   Output: '{result.text}'")
        print(f"   Chars: {result.char_count}")
        return True
        
    except Exception as e:
        print(f"❌ Google Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 50)
    print("🔍 TPS Client Connectivity Test")
    print("=" * 50)
    
    # Check .env file
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        print(f"✓ .env file found")
    else:
        print(f"⚠️  .env file NOT found - using .env.example or environment variables")
    
    results = {}
    
    # Test OpenAI
    results['openai'] = await test_openai()
    
    # Test Google
    results['google'] = await test_google()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {name.upper()}: {status}")
    
    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
