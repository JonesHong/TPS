"""Data Access Object for TPS database operations"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .connection import DatabaseManager


@dataclass
class CachedTranslation:
    """Represents a cached translation entry"""
    cache_key: str
    source_lang: str
    target_lang: str
    original_text: str
    translated_text: str
    provider: str
    is_refined: bool
    refinement_model: Optional[str]
    char_count: int
    created_at: datetime
    last_accessed_at: datetime
    expires_at: Optional[datetime]


@dataclass
class DailyUsageStats:
    """Represents daily usage statistics for a provider"""
    date: str
    provider: str
    request_count: int
    char_count: int
    token_input: int
    token_output: int
    cost_estimated: float


class TranslationDAO:
    """Data Access Object for translation cache and usage statistics"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # === Cache Operations ===
    
    async def get_cached_translation(self, cache_key: str) -> Optional[CachedTranslation]:
        """
        Retrieve a cached translation by its key.
        Returns None if not found or expired.
        """
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM translations 
                WHERE cache_key = ? 
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """,
                (cache_key,)
            )
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return CachedTranslation(
                cache_key=row["cache_key"],
                source_lang=row["source_lang"],
                target_lang=row["target_lang"],
                original_text=row["original_text"],
                translated_text=row["translated_text"],
                provider=row["provider"],
                is_refined=bool(row["is_refined"]),
                refinement_model=row["refinement_model"],
                char_count=row["char_count"],
                created_at=row["created_at"],
                last_accessed_at=row["last_accessed_at"],
                expires_at=row["expires_at"]
            )
    
    async def upsert_translation(
        self,
        cache_key: str,
        source_lang: str,
        target_lang: str,
        original_text: str,
        translated_text: str,
        provider: str,
        is_refined: bool = False,
        refinement_model: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> None:
        """Insert or update a translation in the cache"""
        char_count = len(original_text)
        
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO translations (
                    cache_key, source_lang, target_lang, original_text, 
                    translated_text, provider, is_refined, refinement_model,
                    char_count, created_at, last_accessed_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    translated_text = excluded.translated_text,
                    provider = excluded.provider,
                    is_refined = excluded.is_refined,
                    refinement_model = excluded.refinement_model,
                    last_accessed_at = CURRENT_TIMESTAMP
                """,
                (
                    cache_key, source_lang, target_lang, original_text,
                    translated_text, provider, int(is_refined), refinement_model,
                    char_count, expires_at
                )
            )
            await conn.commit()
    
    async def update_last_accessed(self, cache_key: str) -> None:
        """Update the last_accessed_at timestamp for cache hit tracking"""
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                UPDATE translations 
                SET last_accessed_at = CURRENT_TIMESTAMP 
                WHERE cache_key = ?
                """,
                (cache_key,)
            )
            await conn.commit()
    
    async def delete_expired_entries(self, days_old: int = 90) -> int:
        """Delete cache entries older than specified days. Returns count of deleted entries."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                """
                DELETE FROM translations 
                WHERE last_accessed_at < datetime('now', ? || ' days')
                """,
                (f"-{days_old}",)
            )
            await conn.commit()
            return cursor.rowcount
    
    # === Usage Statistics Operations ===
    
    async def get_daily_usage(self, target_date: str, provider: str) -> Optional[DailyUsageStats]:
        """
        Get usage statistics for a specific date and provider.
        
        Args:
            target_date: Date in 'YYYY-MM-DD' format
            provider: Provider name ('deepl', 'google', 'openai_trans', 'openai_refine')
        """
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM daily_usage_stats 
                WHERE date = ? AND provider = ?
                """,
                (target_date, provider)
            )
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return DailyUsageStats(
                date=row["date"],
                provider=row["provider"],
                request_count=row["request_count"],
                char_count=row["char_count"],
                token_input=row["token_input"],
                token_output=row["token_output"],
                cost_estimated=row["cost_estimated"]
            )
    
    async def increment_usage_stats(
        self,
        provider: str,
        char_count: int = 0,
        token_input: int = 0,
        token_output: int = 0,
        cost_estimated: float = 0.0,
        target_date: Optional[str] = None
    ) -> None:
        """
        Increment usage statistics for a provider.
        Creates a new entry if none exists for the date.
        """
        if target_date is None:
            target_date = date.today().isoformat()
        
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO daily_usage_stats (
                    date, provider, request_count, char_count, 
                    token_input, token_output, cost_estimated
                ) VALUES (?, ?, 1, ?, ?, ?, ?)
                ON CONFLICT(date, provider) DO UPDATE SET
                    request_count = request_count + 1,
                    char_count = char_count + excluded.char_count,
                    token_input = token_input + excluded.token_input,
                    token_output = token_output + excluded.token_output,
                    cost_estimated = cost_estimated + excluded.cost_estimated
                """,
                (target_date, provider, char_count, token_input, token_output, cost_estimated)
            )
            await conn.commit()
    
    async def get_all_daily_usage(self, target_date: Optional[str] = None) -> list[DailyUsageStats]:
        """Get all usage statistics for a specific date"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM daily_usage_stats WHERE date = ?",
                (target_date,)
            )
            rows = await cursor.fetchall()
            
            return [
                DailyUsageStats(
                    date=row["date"],
                    provider=row["provider"],
                    request_count=row["request_count"],
                    char_count=row["char_count"],
                    token_input=row["token_input"],
                    token_output=row["token_output"],
                    cost_estimated=row["cost_estimated"]
                )
                for row in rows
            ]
