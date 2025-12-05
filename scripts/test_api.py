#!/usr/bin/env python3
"""Test the translation API endpoints directly."""
import asyncio
import sys
sys.path.insert(0, "src")

from tps.core.workflow import TranslationWorkflow
from tps.db.dao import TranslationDAO
from tps.core.cost_control import CostController
from tps.config import settings

async def test_api():
    """Test translation workflow directly."""
    print("Testing translation workflow...")
    
    dao = TranslationDAO()
    await dao.initialize()
    cost_controller = CostController(dao)
    workflow = TranslationWorkflow(dao, cost_controller)
    
    # Test translation
    result = await workflow.translate(
        text="Hello, world!",
        source_lang="en",
        target_lang="zh-TW"
    )
    
    print(f"\nTranslation Result:")
    print(f"  Input: Hello, world!")
    print(f"  Output: {result.translated_text}")
    print(f"  Provider: {result.provider}")
    print(f"  Cached: {result.cached}")
    print(f"  Tokens: {result.tokens_used}")
    print(f"  Cost: ${result.estimated_cost:.6f}")
    
    # Close connections
    await workflow.close()

if __name__ == "__main__":
    asyncio.run(test_api())
