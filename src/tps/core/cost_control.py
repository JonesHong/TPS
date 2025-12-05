"""Cost control and circuit breaker logic"""

from datetime import date
from typing import Dict, Set
import asyncio

from ..config import settings
from ..db.dao import TranslationDAO, DailyUsageStats


class CostController:
    """
    Manages budget limits and circuit breaker logic for translation providers.
    
    Circuit Breaker Logic:
    - DeepL: Triggered by QuotaExceededException (HTTP 456)
    - Google: Local budget check (char_count / 1M * $20 > daily_limit)
    - OpenAI: Local budget check (estimated_cost > daily_limit)
    """
    
    def __init__(self, dao: TranslationDAO):
        self.dao = dao
        
        # In-memory circuit breaker state (resets on restart)
        self._quota_exceeded: Set[str] = set()
        self._lock = asyncio.Lock()
    
    # === Quota Exceeded (External API limits) ===
    
    def set_quota_exceeded(self, provider: str) -> None:
        """Mark a provider as having exceeded its external quota"""
        self._quota_exceeded.add(provider.lower())
    
    def is_quota_exceeded(self, provider: str) -> bool:
        """Check if provider has exceeded external quota"""
        return provider.lower() in self._quota_exceeded
    
    def reset_quota_exceeded(self, provider: str) -> None:
        """Reset quota exceeded status for a provider"""
        self._quota_exceeded.discard(provider.lower())
    
    # === Budget Exceeded (Internal limits) ===
    
    async def is_budget_exceeded(self, provider: str) -> bool:
        """
        Check if daily budget limit has been exceeded for a provider.
        
        Args:
            provider: Provider name ('google', 'openai', 'openai_trans', 'openai_refine')
            
        Returns:
            True if budget exceeded, False otherwise
        """
        today = date.today().isoformat()
        provider_lower = provider.lower()
        
        # Get current usage
        usage = await self.dao.get_daily_usage(today, provider_lower)
        
        if usage is None:
            return False
        
        # Check based on provider type
        if provider_lower == "google":
            return self._check_google_budget(usage)
        elif provider_lower.startswith("openai"):
            return self._check_openai_budget(usage, provider_lower)
        
        # DeepL uses external quota, not budget
        return False
    
    def _check_google_budget(self, usage: DailyUsageStats) -> bool:
        """
        Check Google budget: (char_count / 1M) * $20 > daily_limit
        """
        estimated_cost = (usage.char_count / 1_000_000) * settings.google_price_per_million_chars
        return estimated_cost >= settings.daily_budget_google
    
    def _check_openai_budget(self, usage: DailyUsageStats, provider: str) -> bool:
        """
        Check OpenAI budget based on accumulated cost estimate.
        
        For combined OpenAI budget, we need to check both openai_trans and openai_refine.
        """
        # If checking specific provider, use its cost
        if provider in ("openai_trans", "openai_refine"):
            return usage.cost_estimated >= settings.daily_budget_openai
        
        # For general "openai" check, we'd need to sum both
        # This is handled separately
        return usage.cost_estimated >= settings.daily_budget_openai
    
    async def get_total_openai_cost(self, target_date: str = None) -> float:
        """Get combined cost for all OpenAI usage (translation + refinement)"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        total = 0.0
        for provider in ("openai_trans", "openai_refine"):
            usage = await self.dao.get_daily_usage(target_date, provider)
            if usage:
                total += usage.cost_estimated
        
        return total
    
    async def is_openai_budget_exceeded(self) -> bool:
        """Check if combined OpenAI budget is exceeded"""
        total_cost = await self.get_total_openai_cost()
        return total_cost >= settings.daily_budget_openai
    
    # === Usage Recording ===
    
    async def record_usage(
        self,
        provider: str,
        char_count: int = 0,
        token_input: int = 0,
        token_output: int = 0,
        cost_estimated: float = 0.0
    ) -> None:
        """
        Record usage for a provider.
        
        Args:
            provider: Provider name
            char_count: Characters processed (for DeepL/Google)
            token_input: Input tokens (for OpenAI)
            token_output: Output tokens (for OpenAI)
            cost_estimated: Estimated cost in USD
        """
        await self.dao.increment_usage_stats(
            provider=provider.lower(),
            char_count=char_count,
            token_input=token_input,
            token_output=token_output,
            cost_estimated=cost_estimated
        )
    
    # === Statistics ===
    
    async def get_daily_summary(self, target_date: str = None) -> Dict:
        """Get summary of all provider usage for a date"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        all_usage = await self.dao.get_all_daily_usage(target_date)
        
        summary = {
            "date": target_date,
            "providers": {},
            "total_cost": 0.0,
            "total_requests": 0
        }
        
        for usage in all_usage:
            summary["providers"][usage.provider] = {
                "request_count": usage.request_count,
                "char_count": usage.char_count,
                "token_input": usage.token_input,
                "token_output": usage.token_output,
                "cost_estimated": usage.cost_estimated
            }
            summary["total_cost"] += usage.cost_estimated
            summary["total_requests"] += usage.request_count
        
        # Add budget status
        summary["budgets"] = {
            "google": {
                "limit": settings.daily_budget_google,
                "exceeded": await self.is_budget_exceeded("google")
            },
            "openai": {
                "limit": settings.daily_budget_openai,
                "exceeded": await self.is_openai_budget_exceeded()
            }
        }
        
        return summary
