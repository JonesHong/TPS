"""Base classes and exceptions for API clients"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class TranslationProvider(str, Enum):
    """Supported translation providers"""
    DEEPL = "deepl"
    OPENAI = "openai"
    GOOGLE = "google"
    CACHE = "cache"


@dataclass
class TranslationResult:
    """Standard result from any translation provider"""
    text: str
    provider: TranslationProvider
    char_count: int
    token_input: int = 0
    token_output: int = 0
    cost_estimated: float = 0.0


@dataclass
class RefinementResult:
    """Result from AI refinement operation"""
    text: str
    model: str
    token_input: int
    token_output: int
    cost_estimated: float


# === Custom Exceptions ===

class TranslationError(Exception):
    """Base exception for translation errors"""
    pass


class QuotaExceededException(TranslationError):
    """Raised when API quota is exceeded (e.g., DeepL monthly limit)"""
    pass


class RateLimitError(TranslationError):
    """Raised when hitting rate limits"""
    pass


class ContextWindowExceededError(TranslationError):
    """Raised when input exceeds LLM context window"""
    pass


class AuthenticationError(TranslationError):
    """Raised when API authentication fails"""
    pass


class BudgetExceededError(TranslationError):
    """Raised when daily budget limit is exceeded"""
    pass


class ProviderUnavailableError(TranslationError):
    """Raised when a provider is temporarily unavailable"""
    pass


# === Abstract Base Client ===

class BaseTranslationClient(ABC):
    """Abstract base class for translation clients"""
    
    @property
    @abstractmethod
    def provider(self) -> TranslationProvider:
        """Return the provider identifier"""
        pass
    
    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> TranslationResult:
        """
        Translate text from source to target language.
        
        Args:
            text: The text to translate
            source_lang: Source language code (ISO 639-1)
            target_lang: Target language code (ISO 639-1)
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            TranslationError: On any translation failure
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the client is properly configured and available"""
        pass
