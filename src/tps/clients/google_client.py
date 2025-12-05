"""Google Cloud Translation API Client - Tier 4 Last Resort Provider"""

import asyncio
import os
from typing import Optional

from .base import (
    BaseTranslationClient,
    TranslationProvider,
    TranslationResult,
    AuthenticationError,
    TranslationError,
)
from ..config import settings


class GoogleTranslateClient(BaseTranslationClient):
    """
    Google Cloud Translation API v3 client.
    
    Tier 4 in translation hierarchy - last resort when DeepL and OpenAI fail.
    Pricing: $20 per 1M characters (after 500K free monthly).
    
    Supports both:
    - Service Account JSON file (GOOGLE_APPLICATION_CREDENTIALS)
    - Application Default Credentials (gcloud auth application-default login)
    """
    
    def __init__(
        self, 
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        self.credentials_path = credentials_path or settings.google_application_credentials
        self._project_id = project_id or settings.google_cloud_project
        self._client = None
    
    @property
    def provider(self) -> TranslationProvider:
        return TranslationProvider.GOOGLE
    
    def _get_client(self):
        """Lazy initialization of Google Translate client"""
        if self._client is None:
            try:
                # Set credentials environment variable if path is provided
                if self.credentials_path:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                
                from google.cloud import translate_v3 as translate
                self._client = translate.TranslationServiceClient()
                
                # Try to get project ID from various sources
                if not self._project_id:
                    # Try from credentials file
                    if self.credentials_path and os.path.exists(self.credentials_path):
                        import json
                        try:
                            with open(self.credentials_path) as f:
                                creds = json.load(f)
                                self._project_id = creds.get("project_id") or creds.get("quota_project_id")
                        except (json.JSONDecodeError, KeyError):
                            pass
                    
                    # Try from environment
                    if not self._project_id:
                        self._project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or \
                                          os.environ.get("GCLOUD_PROJECT") or \
                                          os.environ.get("CLOUDSDK_CORE_PROJECT")
                
                if not self._project_id:
                    raise AuthenticationError(
                        "Google Cloud project ID not found. "
                        "Set GOOGLE_CLOUD_PROJECT in .env or use gcloud config set project"
                    )
                    
            except ImportError:
                raise AuthenticationError("google-cloud-translate package not installed")
            except Exception as e:
                if "credentials" in str(e).lower() or "auth" in str(e).lower():
                    raise AuthenticationError(f"Google authentication failed: {e}")
                raise AuthenticationError(f"Failed to initialize Google client: {e}")
        
        return self._client
    
    def _map_language(self, lang: str) -> str:
        """Map language codes to Google format"""
        # Google uses BCP-47 language codes
        mapping = {
            "zh-tw": "zh-TW",
            "zh-cn": "zh-CN",
            "zh": "zh-CN",  # Default Chinese to Simplified
            "pt-br": "pt-BR",
        }
        return mapping.get(lang.lower(), lang.lower())
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> TranslationResult:
        """
        Translate text using Google Cloud Translation API.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            TranslationResult with translated text
        """
        try:
            client = self._get_client()
            
            # Map language codes
            source = self._map_language(source_lang)
            target = self._map_language(target_lang)
            
            # Prepare request
            parent = f"projects/{self._project_id}/locations/global"
            
            # Run synchronous Google call in executor
            loop = asyncio.get_event_loop()
            
            def do_translate():
                response = client.translate_text(
                    request={
                        "parent": parent,
                        "contents": [text],
                        "mime_type": "text/plain",
                        "source_language_code": source,
                        "target_language_code": target,
                    }
                )
                return response.translations[0].translated_text
            
            translated_text = await loop.run_in_executor(None, do_translate)
            
            # Calculate cost estimate
            char_count = len(text)
            cost_estimated = (char_count / 1_000_000) * settings.google_price_per_million_chars
            
            return TranslationResult(
                text=translated_text,
                provider=TranslationProvider.GOOGLE,
                char_count=char_count,
                cost_estimated=cost_estimated
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "permission" in error_str or "auth" in error_str or "credential" in error_str:
                raise AuthenticationError(f"Google authentication failed: {e}")
            raise TranslationError(f"Google translation failed: {e}")
    
    async def is_available(self) -> bool:
        """Check if Google client is properly configured (ADC or service account)"""
        try:
            # Check if credentials file exists (if specified)
            if self.credentials_path and not os.path.exists(self.credentials_path):
                return False
            
            # Try to initialize client - this will use ADC if no file specified
            self._get_client()
            return True
        except Exception:
            return False
    
    async def get_supported_languages(self, display_language: str = "en") -> list[dict]:
        """Get list of supported languages"""
        try:
            client = self._get_client()
            parent = f"projects/{self._project_id}/locations/global"
            
            loop = asyncio.get_event_loop()
            
            def do_get_languages():
                response = client.get_supported_languages(
                    request={
                        "parent": parent,
                        "display_language_code": display_language,
                    }
                )
                return [
                    {
                        "code": lang.language_code,
                        "name": lang.display_name,
                        "support_source": lang.support_source,
                        "support_target": lang.support_target,
                    }
                    for lang in response.languages
                ]
            
            return await loop.run_in_executor(None, do_get_languages)
            
        except Exception as e:
            return [{"error": str(e)}]
