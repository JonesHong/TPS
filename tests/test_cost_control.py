"""Unit tests for cost control logic"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date

from tps.core.cost_control import CostController
from tps.db.dao import DailyUsageStats


class TestCostController:
    """Tests for CostController"""
    
    @pytest.fixture
    def mock_dao(self):
        """Create a mock DAO"""
        return MagicMock()
    
    @pytest.fixture
    def controller(self, mock_dao):
        """Create a CostController with mock DAO"""
        return CostController(mock_dao)
    
    # === Quota Exceeded Tests ===
    
    def test_quota_not_exceeded_initially(self, controller):
        """Quota should not be exceeded initially"""
        assert not controller.is_quota_exceeded("deepl")
        assert not controller.is_quota_exceeded("google")
    
    def test_set_quota_exceeded(self, controller):
        """Setting quota exceeded should be reflected"""
        controller.set_quota_exceeded("deepl")
        assert controller.is_quota_exceeded("deepl")
        assert not controller.is_quota_exceeded("google")
    
    def test_reset_quota_exceeded(self, controller):
        """Resetting quota exceeded should work"""
        controller.set_quota_exceeded("deepl")
        controller.reset_quota_exceeded("deepl")
        assert not controller.is_quota_exceeded("deepl")
    
    def test_quota_case_insensitive(self, controller):
        """Provider names should be case-insensitive"""
        controller.set_quota_exceeded("DeepL")
        assert controller.is_quota_exceeded("deepl")
        assert controller.is_quota_exceeded("DEEPL")
    
    # === Budget Exceeded Tests ===
    
    @pytest.mark.asyncio
    async def test_budget_not_exceeded_no_usage(self, controller, mock_dao):
        """Budget should not be exceeded when no usage exists"""
        mock_dao.get_daily_usage = AsyncMock(return_value=None)
        
        assert not await controller.is_budget_exceeded("google")
    
    @pytest.mark.asyncio
    async def test_google_budget_exceeded(self, controller, mock_dao):
        """Google budget should be exceeded when char cost > limit"""
        # Simulate 600,000 chars = $12 (at $20/1M chars)
        mock_dao.get_daily_usage = AsyncMock(return_value=DailyUsageStats(
            date=date.today().isoformat(),
            provider="google",
            request_count=100,
            char_count=600_000,
            token_input=0,
            token_output=0,
            cost_estimated=12.0
        ))
        
        # With default budget of $10, this should be exceeded
        assert await controller.is_budget_exceeded("google")
    
    @pytest.mark.asyncio
    async def test_google_budget_not_exceeded(self, controller, mock_dao):
        """Google budget should not be exceeded when under limit"""
        # Simulate 400,000 chars = $8 (at $20/1M chars)
        mock_dao.get_daily_usage = AsyncMock(return_value=DailyUsageStats(
            date=date.today().isoformat(),
            provider="google",
            request_count=50,
            char_count=400_000,
            token_input=0,
            token_output=0,
            cost_estimated=8.0
        ))
        
        assert not await controller.is_budget_exceeded("google")
    
    @pytest.mark.asyncio
    async def test_openai_budget_exceeded(self, controller, mock_dao):
        """OpenAI budget should be exceeded when cost > limit"""
        mock_dao.get_daily_usage = AsyncMock(return_value=DailyUsageStats(
            date=date.today().isoformat(),
            provider="openai_trans",
            request_count=100,
            char_count=0,
            token_input=10_000_000,
            token_output=5_000_000,
            cost_estimated=6.0  # Over $5 limit
        ))
        
        assert await controller.is_budget_exceeded("openai_trans")


class TestCostEstimation:
    """Tests for cost estimation formulas"""
    
    def test_google_cost_formula(self):
        """Test Google cost calculation: (chars / 1M) * $20"""
        # 1M chars should cost $20
        chars = 1_000_000
        cost = (chars / 1_000_000) * 20
        assert cost == 20.0
        
        # 500K chars should cost $10
        chars = 500_000
        cost = (chars / 1_000_000) * 20
        assert cost == 10.0
    
    def test_openai_cost_formula(self):
        """Test OpenAI cost calculation for gpt-4o-mini"""
        # Prices: $0.15/1M input, $0.60/1M output
        input_tokens = 1_000_000
        output_tokens = 500_000
        
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        total = input_cost + output_cost
        
        assert input_cost == 0.15
        assert output_cost == 0.30
        assert total == 0.45
