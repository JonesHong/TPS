"""Integration tests for translation workflow with mocked providers"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from tps.core.workflow import TranslationWorkflow, TranslationOptions
from tps.core.cost_control import CostController
from tps.db.dao import TranslationDAO, CachedTranslation
from tps.clients.base import (
    TranslationResult,
    TranslationProvider,
    QuotaExceededException,
    TranslationError,
)


class TestTranslationWorkflow:
    """Tests for the main translation workflow"""
    
    @pytest.fixture
    def mock_dao(self):
        """Create mock DAO"""
        dao = MagicMock(spec=TranslationDAO)
        dao.get_cached_translation = AsyncMock(return_value=None)
        dao.upsert_translation = AsyncMock()
        dao.update_last_accessed = AsyncMock()
        dao.get_daily_usage = AsyncMock(return_value=None)
        dao.increment_usage_stats = AsyncMock()
        return dao
    
    @pytest.fixture
    def mock_cost_controller(self, mock_dao):
        """Create mock cost controller"""
        controller = CostController(mock_dao)
        return controller
    
    @pytest.fixture
    def mock_deepl(self):
        """Create mock DeepL client"""
        client = MagicMock()
        client.is_available = AsyncMock(return_value=True)
        client.translate = AsyncMock(return_value=TranslationResult(
            text="你好世界",
            provider=TranslationProvider.DEEPL,
            char_count=12
        ))
        return client
    
    @pytest.fixture
    def mock_openai(self):
        """Create mock OpenAI client"""
        client = MagicMock()
        client.is_available = AsyncMock(return_value=True)
        client.translate = AsyncMock(return_value=TranslationResult(
            text="你好世界",
            provider=TranslationProvider.OPENAI,
            char_count=12,
            token_input=50,
            token_output=20,
            cost_estimated=0.001
        ))
        client.refine = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_google(self):
        """Create mock Google client"""
        client = MagicMock()
        client.is_available = AsyncMock(return_value=True)
        client.translate = AsyncMock(return_value=TranslationResult(
            text="你好世界",
            provider=TranslationProvider.GOOGLE,
            char_count=12,
            cost_estimated=0.0002
        ))
        return client
    
    @pytest.fixture
    def workflow(self, mock_dao, mock_cost_controller, mock_deepl, mock_openai, mock_google):
        """Create workflow with mock dependencies"""
        return TranslationWorkflow(
            dao=mock_dao,
            cost_controller=mock_cost_controller,
            deepl_client=mock_deepl,
            openai_client=mock_openai,
            google_client=mock_google
        )
    
    # === Cache Hit Tests ===
    
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self, workflow, mock_dao):
        """Cache hit should return cached translation without calling providers"""
        mock_dao.get_cached_translation = AsyncMock(return_value=CachedTranslation(
            cache_key="abc123",
            source_lang="en",
            target_lang="zh-tw",
            original_text="Hello world",
            translated_text="你好世界",
            provider="deepl",
            is_refined=False,
            refinement_model=None,
            char_count=11,
            created_at=datetime.now(),
            last_accessed_at=datetime.now(),
            expires_at=None
        ))
        
        result = await workflow.translate("Hello world", "en", "zh-tw")
        
        assert result.success
        assert result.text == "你好世界"
        assert result.provider == "cache"
        assert result.is_cached
        mock_dao.update_last_accessed.assert_called_once()
        workflow.deepl.translate.assert_not_called()
    
    # === Failover Tests ===
    
    @pytest.mark.asyncio
    async def test_deepl_success(self, workflow):
        """Successful DeepL translation"""
        result = await workflow.translate("Hello world", "en", "zh-tw")
        
        assert result.success
        assert result.text == "你好世界"
        assert result.provider == "deepl"
        assert not result.is_cached
    
    @pytest.mark.asyncio
    async def test_deepl_failure_falls_back_to_openai(self, workflow, mock_deepl):
        """DeepL failure should fall back to OpenAI"""
        mock_deepl.translate = AsyncMock(side_effect=TranslationError("DeepL error"))
        
        result = await workflow.translate("Hello world", "en", "zh-tw")
        
        assert result.success
        assert result.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_deepl_quota_exceeded_falls_back_to_openai(self, workflow, mock_deepl, mock_cost_controller):
        """DeepL quota exceeded should fall back to OpenAI"""
        mock_deepl.translate = AsyncMock(side_effect=QuotaExceededException("Quota exceeded"))
        
        result = await workflow.translate("Hello world", "en", "zh-tw")
        
        assert result.success
        assert result.provider == "openai"
        assert mock_cost_controller.is_quota_exceeded("deepl")
    
    @pytest.mark.asyncio
    async def test_deepl_and_openai_failure_falls_back_to_google(
        self, workflow, mock_deepl, mock_openai
    ):
        """DeepL and OpenAI failure should fall back to Google"""
        mock_deepl.translate = AsyncMock(side_effect=TranslationError("DeepL error"))
        mock_openai.translate = AsyncMock(side_effect=TranslationError("OpenAI error"))
        
        result = await workflow.translate("Hello world", "en", "zh-tw")
        
        assert result.success
        assert result.provider == "google"
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self, workflow, mock_deepl, mock_openai, mock_google):
        """All provider failures should return error response"""
        mock_deepl.translate = AsyncMock(side_effect=TranslationError("DeepL error"))
        mock_openai.translate = AsyncMock(side_effect=TranslationError("OpenAI error"))
        mock_google.translate = AsyncMock(side_effect=TranslationError("Google error"))
        
        result = await workflow.translate("Hello world", "en", "zh-tw")
        
        assert not result.success
        assert result.error is not None
        assert result.original_text == "Hello world"
    
    # === Budget Exceeded Tests ===
    
    @pytest.mark.asyncio
    async def test_openai_budget_exceeded_skips_to_google(
        self, workflow, mock_deepl, mock_cost_controller
    ):
        """OpenAI budget exceeded should skip to Google"""
        mock_deepl.translate = AsyncMock(side_effect=TranslationError("DeepL error"))
        
        # Mock budget exceeded
        with patch.object(mock_cost_controller, 'is_openai_budget_exceeded', AsyncMock(return_value=True)):
            workflow.cost_controller = mock_cost_controller
            result = await workflow.translate("Hello world", "en", "zh-tw")
        
            assert result.success
            assert result.provider == "google"
    
    # === Refinement Tests ===
    
    @pytest.mark.asyncio
    async def test_refinement_applied_when_enabled(self, workflow, mock_openai):
        """Refinement should be applied when enabled"""
        from tps.clients.base import RefinementResult
        
        mock_openai.refine = AsyncMock(return_value=MagicMock(
            text="優化後的翻譯",
            model="gpt-4o-mini",
            token_input=100,
            token_output=50,
            cost_estimated=0.002
        ))
        
        options = TranslationOptions(enable_refinement=True)
        result = await workflow.translate("Hello world", "en", "zh-tw", options)
        
        assert result.success
        assert result.is_refined
        mock_openai.refine.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refinement_skipped_for_openai_provider(self, workflow, mock_deepl, mock_openai):
        """Refinement should be skipped when provider is already OpenAI"""
        mock_deepl.translate = AsyncMock(side_effect=TranslationError("DeepL error"))
        
        options = TranslationOptions(enable_refinement=True)
        result = await workflow.translate("Hello world", "en", "zh-tw", options)
        
        assert result.success
        assert result.provider == "openai"
        assert not result.is_refined  # Should not refine OpenAI output
        mock_openai.refine.assert_not_called()
