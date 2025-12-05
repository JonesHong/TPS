"""OpenAI API Client - Tier 3 Translation & Refinement Provider"""

import json
from typing import Optional, Tuple
import tiktoken
from openai import AsyncOpenAI, APIError, RateLimitError as OpenAIRateLimitError

from .base import (
    BaseTranslationClient,
    TranslationProvider,
    TranslationResult,
    RefinementResult,
    RateLimitError,
    ContextWindowExceededError,
    AuthenticationError,
    TranslationError,
)
from ..config import settings


class OpenAIClient(BaseTranslationClient):
    """
    OpenAI API client for translation and refinement.
    
    Tier 3 in translation hierarchy - fallback when DeepL fails.
    Also used for AI refinement (校稿) to improve translation quality.
    
    Uses gpt-4o-mini by default (~$0.15/1M input tokens).
    """
    
    # System prompts - using safe placeholders for format()
    TRANSLATION_SYSTEM_PROMPT = """You are a professional translator API. Your task is to translate the user's text accurately.

Rules:
1. Translate from {source_lang} to {target_lang}
2. Preserve ALL HTML tags exactly as they appear
3. Preserve ALL variables (e.g., {{{{name}}}}, {{{{0}}}}, %s) exactly as they appear
4. Do not add explanations or notes
5. Return ONLY the translated text, nothing else

Respond with a JSON object: {{"translation": "your translated text here"}}"""

    REFINEMENT_SYSTEM_PROMPT = """You are a localization expert specializing in making translations sound natural and fluent.

Your task is to improve the draft translation for better readability while maintaining accuracy.

Rules:
1. Keep technical terms and proper nouns consistent
2. Improve naturalness and flow without changing the meaning
3. Preserve ALL HTML tags and variables exactly
4. Do not add explanations

Respond with a JSON object: {{"refined": "your refined translation here"}}"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        translation_model: Optional[str] = None,
        refinement_model: Optional[str] = None
    ):
        self.api_key = api_key or settings.openai_api_key
        self.translation_model = translation_model or settings.openai_translation_model
        self.refinement_model = refinement_model or settings.openai_refinement_model
        
        self._client: Optional[AsyncOpenAI] = None
        self._encoder: Optional[tiktoken.Encoding] = None
    
    @property
    def provider(self) -> TranslationProvider:
        return TranslationProvider.OPENAI
    
    def _get_client(self) -> AsyncOpenAI:
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.api_key:
                raise AuthenticationError("OpenAI API key not configured")
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    def _get_encoder(self) -> tiktoken.Encoding:
        """Get tiktoken encoder for accurate token counting"""
        if self._encoder is None:
            try:
                # Try to get encoder for the specific model
                self._encoder = tiktoken.encoding_for_model(self.translation_model)
            except KeyError:
                # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
                self._encoder = tiktoken.get_encoding("cl100k_base")
        return self._encoder
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        encoder = self._get_encoder()
        return len(encoder.encode(text))
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token usage"""
        input_cost = (input_tokens / 1_000_000) * settings.openai_price_input
        output_cost = (output_tokens / 1_000_000) * settings.openai_price_output
        return input_cost + output_cost
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text using OpenAI.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            model: Model to use (default: gpt-4o-mini)
            
        Returns:
            TranslationResult with translated text and token usage
        """
        model = model or self.translation_model
        client = self._get_client()
        
        # Prepare prompts
        system_prompt = self.TRANSLATION_SYSTEM_PROMPT.format(
            source_lang=source_lang,
            target_lang=target_lang
        )
        user_content = json.dumps({"text": text}, ensure_ascii=False)
        
        # Estimate max tokens (input * 2 to prevent truncation)
        input_tokens = self.count_tokens(system_prompt + user_content)
        max_tokens = max(input_tokens * 2, 1000)
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,  # Low temperature for consistent translations
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result_data = json.loads(content)
            translated_text = result_data.get("translation", content)
            
            # Get actual token usage
            usage = response.usage
            token_input = usage.prompt_tokens if usage else input_tokens
            token_output = usage.completion_tokens if usage else self.count_tokens(translated_text)
            
            return TranslationResult(
                text=translated_text,
                provider=TranslationProvider.OPENAI,
                char_count=len(text),
                token_input=token_input,
                token_output=token_output,
                cost_estimated=self._estimate_cost(token_input, token_output)
            )
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract text directly
            if 'content' in locals():
                return TranslationResult(
                    text=content.strip(),
                    provider=TranslationProvider.OPENAI,
                    char_count=len(text),
                    token_input=input_tokens,
                    token_output=self.count_tokens(content),
                    cost_estimated=self._estimate_cost(input_tokens, self.count_tokens(content))
                )
            raise TranslationError("Failed to parse OpenAI response")
        except OpenAIRateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
        except APIError as e:
            if "context_length_exceeded" in str(e).lower():
                raise ContextWindowExceededError(f"Text too long for OpenAI: {e}")
            raise TranslationError(f"OpenAI API error: {e}")
        except Exception as e:
            raise TranslationError(f"OpenAI unexpected error: {e}")
    
    async def refine(
        self,
        original_text: str,
        draft_translation: str,
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None
    ) -> RefinementResult:
        """
        Refine a draft translation using AI.
        
        Args:
            original_text: Original source text
            draft_translation: Draft translation to refine
            source_lang: Source language code
            target_lang: Target language code
            model: Model to use (default: refinement_model)
            
        Returns:
            RefinementResult with refined text and usage stats
        """
        model = model or self.refinement_model
        client = self._get_client()
        
        # Prepare user content
        user_content = json.dumps({
            "source_lang": source_lang,
            "target_lang": target_lang,
            "original": original_text,
            "draft_translation": draft_translation
        }, ensure_ascii=False)
        
        # Estimate tokens
        input_tokens = self.count_tokens(self.REFINEMENT_SYSTEM_PROMPT + user_content)
        max_tokens = max(input_tokens * 2, 1000)
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.REFINEMENT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,  # Slightly higher for natural refinement
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result_data = json.loads(content)
            refined_text = result_data.get("refined", content)
            
            # Get token usage
            usage = response.usage
            token_input = usage.prompt_tokens if usage else input_tokens
            token_output = usage.completion_tokens if usage else self.count_tokens(refined_text)
            
            return RefinementResult(
                text=refined_text,
                model=model,
                token_input=token_input,
                token_output=token_output,
                cost_estimated=self._estimate_cost(token_input, token_output)
            )
            
        except json.JSONDecodeError:
            if 'content' in locals():
                return RefinementResult(
                    text=content.strip(),
                    model=model,
                    token_input=input_tokens,
                    token_output=self.count_tokens(content),
                    cost_estimated=self._estimate_cost(input_tokens, self.count_tokens(content))
                )
            raise TranslationError("Failed to parse OpenAI refinement response")
        except OpenAIRateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
        except APIError as e:
            if "context_length_exceeded" in str(e).lower():
                raise ContextWindowExceededError(f"Text too long for refinement: {e}")
            raise TranslationError(f"OpenAI refinement error: {e}")
        except Exception as e:
            raise TranslationError(f"OpenAI refinement unexpected error: {e}")
    
    async def is_available(self) -> bool:
        """Check if OpenAI client is properly configured"""
        if not self.api_key:
            return False
        
        try:
            client = self._get_client()
            # Simple API check - list models
            await client.models.list()
            return True
        except Exception:
            return False
