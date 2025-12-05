"""Unit tests for key generation"""

import pytest
from tps.core.key_generator import generate_cache_key, normalize_language_code


class TestGenerateCacheKey:
    """Tests for cache key generation"""
    
    def test_basic_key_generation(self):
        """Test basic key generation produces consistent hash"""
        key1 = generate_cache_key("Hello", "en", "zh-tw")
        key2 = generate_cache_key("Hello", "en", "zh-tw")
        assert key1 == key2
        assert len(key1) == 32  # MD5 hex digest length
    
    def test_different_text_different_key(self):
        """Different text should produce different keys"""
        key1 = generate_cache_key("Hello", "en", "zh-tw")
        key2 = generate_cache_key("World", "en", "zh-tw")
        assert key1 != key2
    
    def test_different_languages_different_key(self):
        """Different language pairs should produce different keys"""
        key1 = generate_cache_key("Hello", "en", "zh-tw")
        key2 = generate_cache_key("Hello", "en", "ja")
        key3 = generate_cache_key("Hello", "de", "zh-tw")
        assert key1 != key2
        assert key1 != key3
    
    def test_whitespace_normalization(self):
        """Leading/trailing whitespace should be stripped"""
        key1 = generate_cache_key("Hello", "en", "zh-tw")
        key2 = generate_cache_key("  Hello  ", "en", "zh-tw")
        assert key1 == key2
    
    def test_internal_whitespace_preserved(self):
        """Internal whitespace should be preserved"""
        key1 = generate_cache_key("Hello World", "en", "zh-tw")
        key2 = generate_cache_key("HelloWorld", "en", "zh-tw")
        assert key1 != key2
    
    def test_case_insensitive_language(self):
        """Language codes should be case-insensitive"""
        key1 = generate_cache_key("Hello", "EN", "ZH-TW")
        key2 = generate_cache_key("Hello", "en", "zh-tw")
        assert key1 == key2
    
    def test_format_type_affects_key(self):
        """Different format types should produce different keys"""
        key1 = generate_cache_key("Hello", "en", "zh-tw", "plain")
        key2 = generate_cache_key("Hello", "en", "zh-tw", "html")
        assert key1 != key2
    
    def test_html_tags_preserved(self):
        """HTML tags should be preserved in key"""
        key1 = generate_cache_key("<b>Hello</b>", "en", "zh-tw")
        key2 = generate_cache_key("Hello", "en", "zh-tw")
        assert key1 != key2
    
    def test_variables_preserved(self):
        """Template variables should be preserved in key"""
        key1 = generate_cache_key("Hello {name}", "en", "zh-tw")
        key2 = generate_cache_key("Hello name", "en", "zh-tw")
        assert key1 != key2


class TestNormalizeLanguageCode:
    """Tests for language code normalization"""
    
    def test_lowercase(self):
        assert normalize_language_code("EN") == "en"
        assert normalize_language_code("ZH-TW") == "zh-tw"
    
    def test_underscore_to_hyphen(self):
        assert normalize_language_code("zh_TW") == "zh-tw"
        assert normalize_language_code("pt_BR") == "pt-br"
    
    def test_strip_whitespace(self):
        assert normalize_language_code("  en  ") == "en"
