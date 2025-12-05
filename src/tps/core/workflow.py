"""Main translation workflow orchestrator"""

import logging
from typing import Optional
from dataclasses import dataclass

from .key_generator import generate_cache_key
from .cost_control import CostController
from ..db.dao import TranslationDAO
from ..clients.base import (
    TranslationProvider,
    TranslationResult,
    QuotaExceededException,
    BudgetExceededError,
    TranslationError,
)
from ..clients.deepl_client import DeepLClient
from ..clients.openai_client import OpenAIClient
from ..clients.google_client import GoogleTranslateClient


logger = logging.getLogger(__name__)


@dataclass
class TranslationResponse:
    """Standard response from translation workflow"""
    success: bool
    text: Optional[str] = None
    provider: Optional[str] = None
    is_refined: bool = False
    is_cached: bool = False
    error: Optional[str] = None
    original_text: Optional[str] = None


@dataclass
class TranslationOptions:
    """Options for translation request"""
    format_type: str = "plain"
    enable_refinement: bool = False
    refinement_model: Optional[str] = None


class TranslationWorkflow:
    """
    Main workflow orchestrator implementing the multi-tier translation strategy.
    
    Tier 1: Cache (SQLite) - $0, <10ms
    Tier 2: DeepL - Low cost (free tier)
    Tier 3: OpenAI gpt-4o-mini - Very low cost (~$0.15/1M tokens)
    Tier 4: Google Translate - Higher cost ($20/1M chars)
    
    Optional: AI Refinement using OpenAI
    """
    
    def __init__(
        self,
        dao: TranslationDAO,
        cost_controller: CostController,
        deepl_client: Optional[DeepLClient] = None,
        openai_client: Optional[OpenAIClient] = None,
        google_client: Optional[GoogleTranslateClient] = None
    ):
        self.dao = dao
        self.cost_controller = cost_controller
        
        # Initialize clients (lazy - they check availability internally)
        self.deepl = deepl_client or DeepLClient()
        self.openai = openai_client or OpenAIClient()
        self.google = google_client or GoogleTranslateClient()
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        options: Optional[TranslationOptions] = None
    ) -> TranslationResponse:
        """
        Main translation entry point implementing the full workflow.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            options: Translation options
            
        Returns:
            TranslationResponse with result or error
        """
        options = options or TranslationOptions()
        
        # Step 1: Generate cache key and check cache
        cache_key = generate_cache_key(
            text, source_lang, target_lang, options.format_type
        )
        
        cached = await self.dao.get_cached_translation(cache_key)
        
        # Cache hit logic: return if exists AND (no refinement needed OR already refined)
        if cached:
            if not options.enable_refinement or cached.is_refined:
                await self.dao.update_last_accessed(cache_key)
                logger.info(f"Cache hit for key {cache_key[:8]}...")
                return TranslationResponse(
                    success=True,
                    text=cached.translated_text,
                    provider="cache",
                    is_refined=cached.is_refined,
                    is_cached=True
                )
        
        # Step 2-4: Translation chain with failover
        result: Optional[TranslationResult] = None
        provider_used: Optional[str] = None
        
        try:
            result, provider_used = await self._execute_translation_chain(
                text, source_lang, target_lang
            )
        except Exception as e:
            logger.error(f"Translation chain failed: {e}")
            return TranslationResponse(
                success=False,
                error=str(e),
                original_text=text
            )
        
        if result is None:
            return TranslationResponse(
                success=False,
                error="All translation providers failed or exceeded budget",
                original_text=text
            )
        
        translated_text = result.text
        is_refined = False
        refinement_model = None
        
        # Step 5: Optional refinement
        if options.enable_refinement and provider_used != "openai":
            refined_result = await self._try_refinement(
                text, translated_text, source_lang, target_lang,
                options.refinement_model
            )
            if refined_result:
                translated_text = refined_result.text
                is_refined = True
                refinement_model = refined_result.model
        
        # Step 6: Save to cache
        await self.dao.upsert_translation(
            cache_key=cache_key,
            source_lang=source_lang,
            target_lang=target_lang,
            original_text=text,
            translated_text=translated_text,
            provider=provider_used,
            is_refined=is_refined,
            refinement_model=refinement_model
        )
        
        return TranslationResponse(
            success=True,
            text=translated_text,
            provider=provider_used,
            is_refined=is_refined,
            is_cached=False
        )
    
    async def _execute_translation_chain(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> tuple[Optional[TranslationResult], Optional[str]]:
        """
        Execute the translation chain with failover.
        
        Order: DeepL -> OpenAI -> Google
        """
        # Tier 2: DeepL
        if not self.cost_controller.is_quota_exceeded("deepl"):
            try:
                if await self.deepl.is_available():
                    result = await self.deepl.translate(text, source_lang, target_lang)
                    await self.cost_controller.record_usage(
                        "deepl",
                        char_count=result.char_count
                    )
                    logger.info(f"DeepL translation successful ({result.char_count} chars)")
                    return result, "deepl"
            except QuotaExceededException:
                self.cost_controller.set_quota_exceeded("deepl")
                logger.warning("DeepL quota exceeded, switching to fallback")
            except Exception as e:
                logger.warning(f"DeepL failed: {e}")
        
        # Tier 3: OpenAI (gpt-4o-mini)
        if not await self.cost_controller.is_openai_budget_exceeded():
            try:
                if await self.openai.is_available():
                    result = await self.openai.translate(text, source_lang, target_lang)
                    await self.cost_controller.record_usage(
                        "openai_trans",
                        token_input=result.token_input,
                        token_output=result.token_output,
                        cost_estimated=result.cost_estimated
                    )
                    logger.info(f"OpenAI translation successful ({result.token_input}+{result.token_output} tokens)")
                    return result, "openai"
            except Exception as e:
                logger.warning(f"OpenAI translation failed: {e}")
        else:
            logger.warning("OpenAI budget exceeded, skipping")
        
        # Tier 4: Google (last resort)
        if not await self.cost_controller.is_budget_exceeded("google"):
            try:
                if await self.google.is_available():
                    result = await self.google.translate(text, source_lang, target_lang)
                    await self.cost_controller.record_usage(
                        "google",
                        char_count=result.char_count,
                        cost_estimated=result.cost_estimated
                    )
                    logger.info(f"Google translation successful ({result.char_count} chars)")
                    return result, "google"
            except Exception as e:
                logger.warning(f"Google translation failed: {e}")
        else:
            logger.warning("Google budget exceeded, skipping")
        
        return None, None
    
    async def _try_refinement(
        self,
        original_text: str,
        draft_translation: str,
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None
    ) -> Optional[any]:
        """
        Attempt AI refinement of translation.
        
        Returns None if refinement fails or budget exceeded.
        """
        if await self.cost_controller.is_openai_budget_exceeded():
            logger.warning("OpenAI budget exceeded, skipping refinement")
            return None
        
        try:
            result = await self.openai.refine(
                original_text, draft_translation,
                source_lang, target_lang, model
            )
            
            await self.cost_controller.record_usage(
                "openai_refine",
                token_input=result.token_input,
                token_output=result.token_output,
                cost_estimated=result.cost_estimated
            )
            
            logger.info(f"Refinement successful ({result.token_input}+{result.token_output} tokens)")
            return result
            
        except Exception as e:
            logger.warning(f"Refinement failed: {e}")
            return None
