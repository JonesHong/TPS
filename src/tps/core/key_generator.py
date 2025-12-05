"""Cache key generation utilities"""

import hashlib
from typing import Optional


def generate_cache_key(
    text: str,
    source_lang: str,
    target_lang: str,
    format_type: Optional[str] = None
) -> str:
    """
    Generate a unique cache key for a translation request.
    
    The key is an MD5 hash of the normalized input parameters.
    This ensures consistent cache hits for identical requests.
    
    Args:
        text: The text to translate (will be stripped but preserve internal structure)
        source_lang: Source language code (normalized to lowercase)
        target_lang: Target language code (normalized to lowercase)
        format_type: Optional format type (e.g., 'html', 'plain')
        
    Returns:
        MD5 hash string as the cache key
        
    Note:
        - Whitespace at start/end is stripped
        - Internal whitespace, variables, and HTML tags are preserved
        - Language codes are normalized to lowercase
    """
    # Normalize inputs
    normalized_text = text.strip()
    normalized_source = source_lang.lower().strip()
    normalized_target = target_lang.lower().strip()
    normalized_format = (format_type or "plain").lower().strip()
    
    # Create composite string for hashing
    composite = f"{normalized_source}|{normalized_target}|{normalized_format}|{normalized_text}"
    
    # Generate MD5 hash
    hash_object = hashlib.md5(composite.encode("utf-8"))
    return hash_object.hexdigest()


def normalize_language_code(lang: str) -> str:
    """
    Normalize language codes to a consistent format.
    
    Examples:
        - "EN" -> "en"
        - "zh-TW" -> "zh-tw"
        - "ZH_HANT" -> "zh-hant"
    """
    return lang.lower().replace("_", "-").strip()
