"""DeepL API Client - Tier 2 Translation Provider"""

import asyncio
from typing import Optional
import deepl

from .base import (
    BaseTranslationClient,
    TranslationProvider,
    TranslationResult,
    QuotaExceededException,
    AuthenticationError,
    TranslationError,
)
from ..config import settings


class DeepLClient(BaseTranslationClient):
    """
    DeepL API client wrapper.
    
    Tier 2 in the translation hierarchy - primary external translation engine.
    Utilizes monthly free quota (500,000 characters).
    """
    
    # Language code mapping (ISO 639-1 to DeepL format)
    LANG_MAP = {
        "en": "EN",
        "zh": "ZH",
        "zh-tw": "ZH-HANT",  # Traditional Chinese
        "zh-cn": "ZH-HANS",  # Simplified Chinese
        "ja": "JA",
        "ko": "KO",
        "de": "DE",
        "fr": "FR",
        "es": "ES",
        "it": "IT",
        "pt": "PT-PT",
        "pt-br": "PT-BR",
        "ru": "RU",
        "nl": "NL",
        "pl": "PL",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.deepl_api_key
        self._translator: Optional[deepl.Translator] = None
    
    @property
    def provider(self) -> TranslationProvider:
        return TranslationProvider.DEEPL
    
    def _get_translator(self) -> deepl.Translator:
        """Lazy initialization of DeepL translator"""
        if self._translator is None:
            if not self.api_key:
                raise AuthenticationError("DeepL API key not configured")
            self._translator = deepl.Translator(self.api_key)
        return self._translator
    
    def _map_language(self, lang: str, is_target: bool = False) -> str:
        """Map standard language codes to DeepL format"""
        lang_lower = lang.lower()
        
        # Direct mapping
        if lang_lower in self.LANG_MAP:
            mapped = self.LANG_MAP[lang_lower]
            # DeepL requires specific format for target languages
            if is_target and mapped == "EN":
                return "EN-US"  # Default to US English for target
            return mapped
        
        # Try uppercase as-is (DeepL might accept it)
        return lang.upper()
    
    async def translate(
        self,
        text: str,
        source_lang: Optional[str],
        target_lang: str
    ) -> TranslationResult:
        """
        Translate text using DeepL API.
        
        Args:
            text: Text to translate
            source_lang: Source language code (None for auto-detect)
            target_lang: Target language code
            
        Returns:
            TranslationResult with translated text
            
        Raises:
            QuotaExceededException: When monthly quota is exceeded
            AuthenticationError: When API key is invalid
            TranslationError: On other failures
        """
        try:
            translator = self._get_translator()
            
            # Map language codes (None for source means auto-detect)
            source = self._map_language(source_lang, is_target=False) if source_lang else None
            target = self._map_language(target_lang, is_target=True)
            
            # Run synchronous DeepL call in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: translator.translate_text(
                    text,
                    source_lang=source,
                    target_lang=target,
                    preserve_formatting=True
                )
            )
            
            translated_text = result.text
            
            return TranslationResult(
                text=translated_text,
                provider=TranslationProvider.DEEPL,
                char_count=len(text),
                cost_estimated=0.0  # DeepL free tier or included in subscription
            )
            
        except deepl.QuotaExceededException as e:
            raise QuotaExceededException(f"DeepL quota exceeded: {e}")
        except deepl.AuthorizationException as e:
            raise AuthenticationError(f"DeepL authentication failed: {e}")
        except deepl.DeepLException as e:
            # Check for quota exceeded in error message (HTTP 456)
            if "456" in str(e) or "quota" in str(e).lower():
                raise QuotaExceededException(f"DeepL quota exceeded: {e}")
            raise TranslationError(f"DeepL translation failed: {e}")
        except Exception as e:
            raise TranslationError(f"DeepL unexpected error: {e}")
    
    async def is_available(self) -> bool:
        """Check if DeepL client is properly configured"""
        if not self.api_key:
            return False
        
        try:
            translator = self._get_translator()
            # Try to get usage to verify API key works
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, translator.get_usage)
            return True
        except Exception:
            return False
    
    async def get_usage(self) -> dict:
        """Get current quota usage from DeepL"""
        try:
            translator = self._get_translator()
            loop = asyncio.get_event_loop()
            usage = await loop.run_in_executor(None, translator.get_usage)
            
            return {
                "character_count": usage.character.count if usage.character else 0,
                "character_limit": usage.character.limit if usage.character else 0,
            }
        except Exception as e:
            return {"error": str(e)}
