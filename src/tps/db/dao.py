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

    # === Pagination & Search Operations ===

    async def get_translations_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        search_query: Optional[str] = None,
        providers: Optional[list[str]] = None,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        is_refined: Optional[bool] = None
    ) -> tuple[list[CachedTranslation], int]:
        """
        Get paginated translations with optional filters.
        
        Returns:
            Tuple of (items, total_count)
        """
        # Build WHERE conditions
        conditions = []
        params = []
        
        if search_query:
            conditions.append("(original_text LIKE ? OR translated_text LIKE ?)")
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern])
        
        if providers:
            placeholders = ",".join("?" * len(providers))
            conditions.append(f"provider IN ({placeholders})")
            params.extend(providers)
        
        if source_lang:
            conditions.append("source_lang = ?")
            params.append(source_lang)
        
        if target_lang:
            conditions.append("target_lang = ?")
            params.append(target_lang)
        
        if is_refined is not None:
            conditions.append("is_refined = ?")
            params.append(int(is_refined))
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        async with self.db.get_connection() as conn:
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM translations WHERE {where_clause}"
            cursor = await conn.execute(count_query, params)
            row = await cursor.fetchone()
            total_count = row["total"]
            
            # Get paginated results
            offset = (page - 1) * page_size
            data_query = f"""
                SELECT * FROM translations 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            cursor = await conn.execute(data_query, params + [page_size, offset])
            rows = await cursor.fetchall()
            
            items = [
                CachedTranslation(
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
                for row in rows
            ]
            
            return items, total_count

    # === Dashboard Statistics ===

    async def get_dashboard_stats(self, days: int = 30) -> dict:
        """
        Get comprehensive dashboard statistics.
        
        Returns:
            Dictionary with total_requests, total_chars, total_cost_usd,
            cache_hit_rate, provider_usage, provider_details, and daily_trend.
        """
        async with self.db.get_connection() as conn:
            # Total counts from translations table
            cursor = await conn.execute(
                "SELECT COUNT(*) as total, SUM(char_count) as chars FROM translations"
            )
            row = await cursor.fetchone()
            total_translations = row["total"] or 0
            total_chars = row["chars"] or 0
            
            # Provider usage from translations table
            cursor = await conn.execute(
                """
                SELECT provider, COUNT(*) as count 
                FROM translations 
                GROUP BY provider
                """
            )
            rows = await cursor.fetchall()
            provider_usage = {row["provider"]: row["count"] for row in rows}
            
            # Add cache count (from daily_usage_stats where provider='cache')
            cursor = await conn.execute(
                """
                SELECT SUM(request_count) as cache_hits 
                FROM daily_usage_stats 
                WHERE provider = 'cache'
                """
            )
            row = await cursor.fetchone()
            cache_hits = row["cache_hits"] or 0
            provider_usage["cache"] = cache_hits
            
            # Total requests (translations + cache hits)
            total_requests = total_translations + cache_hits
            
            # Cache hit rate
            cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0
            
            # Total cost from daily_usage_stats
            cursor = await conn.execute(
                "SELECT SUM(cost_estimated) as total_cost FROM daily_usage_stats"
            )
            row = await cursor.fetchone()
            total_cost = row["total_cost"] or 0.0
            
            # Provider details with char/token counts for quota tracking
            cursor = await conn.execute(
                """
                SELECT 
                    provider,
                    SUM(request_count) as requests,
                    SUM(char_count) as chars,
                    SUM(token_input) as tokens_in,
                    SUM(token_output) as tokens_out,
                    SUM(cost_estimated) as cost
                FROM daily_usage_stats 
                GROUP BY provider
                """
            )
            rows = await cursor.fetchall()
            provider_details = {}
            for row in rows:
                provider_details[row["provider"]] = {
                    "requests": row["requests"] or 0,
                    "chars": row["chars"] or 0,
                    "tokens_in": row["tokens_in"] or 0,
                    "tokens_out": row["tokens_out"] or 0,
                    "cost": round(row["cost"] or 0.0, 6)
                }
            
            # Daily trend (last N days)
            cursor = await conn.execute(
                f"""
                SELECT date, SUM(request_count) as count 
                FROM daily_usage_stats 
                WHERE date >= date('now', '-{days} days')
                GROUP BY date
                ORDER BY date ASC
                """
            )
            rows = await cursor.fetchall()
            daily_trend = [{"date": row["date"], "count": row["count"]} for row in rows]
            
            # Monthly provider quota data (current month)
            cursor = await conn.execute(
                """
                SELECT 
                    provider,
                    SUM(char_count) as chars,
                    SUM(token_input) as tokens_in,
                    SUM(token_output) as tokens_out,
                    SUM(cost_estimated) as cost
                FROM daily_usage_stats 
                WHERE date >= date('now', 'start of month')
                GROUP BY provider
                """
            )
            rows = await cursor.fetchall()
            # Convert sqlite3.Row to dict for easier access
            monthly_stats = {row["provider"]: dict(row) for row in rows}
            
            # Extract monthly values for each provider
            deepl_data = monthly_stats.get("deepl", {})
            google_data = monthly_stats.get("google", {})
            # OpenAI has two providers: openai_trans and openai_refine - combine them
            openai_trans_data = monthly_stats.get("openai_trans", {})
            openai_refine_data = monthly_stats.get("openai_refine", {})
            
            deepl_chars_month = deepl_data.get("chars") or 0
            google_chars_month = google_data.get("chars") or 0
            # Combine openai_trans and openai_refine tokens/cost
            openai_tokens_input_month = (openai_trans_data.get("tokens_in") or 0) + (openai_refine_data.get("tokens_in") or 0)
            openai_tokens_output_month = (openai_trans_data.get("tokens_out") or 0) + (openai_refine_data.get("tokens_out") or 0)
            openai_cost_month = round((openai_trans_data.get("cost") or 0.0) + (openai_refine_data.get("cost") or 0.0), 4)
            
            # Calculate quota percentages (500K free limit for DeepL and Google)
            FREE_QUOTA_LIMIT = 500_000
            deepl_quota_percent = (deepl_chars_month / FREE_QUOTA_LIMIT) * 100 if FREE_QUOTA_LIMIT > 0 else 0.0
            google_quota_percent = (google_chars_month / FREE_QUOTA_LIMIT) * 100 if FREE_QUOTA_LIMIT > 0 else 0.0
            
            return {
                "total_requests": total_requests,
                "total_chars": total_chars,
                "total_cost_usd": round(total_cost, 4),
                "cache_hit_rate": round(cache_hit_rate, 4),
                "provider_usage": provider_usage,
                "provider_details": provider_details,
                "daily_trend": daily_trend,
                # Monthly provider quota data
                "deepl_chars_month": deepl_chars_month,
                "google_chars_month": google_chars_month,
                "openai_tokens_input_month": openai_tokens_input_month,
                "openai_tokens_output_month": openai_tokens_output_month,
                "openai_cost_month": openai_cost_month,
                "deepl_quota_percent": round(deepl_quota_percent, 2),
                "google_quota_percent": round(google_quota_percent, 2)
            }

    async def get_available_languages(self) -> dict:
        """Get list of unique source and target languages in the cache."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT DISTINCT source_lang FROM translations ORDER BY source_lang"
            )
            source_langs = [row["source_lang"] for row in await cursor.fetchall()]
            
            cursor = await conn.execute(
                "SELECT DISTINCT target_lang FROM translations ORDER BY target_lang"
            )
            target_langs = [row["target_lang"] for row in await cursor.fetchall()]
            
            return {
                "source_languages": source_langs,
                "target_languages": target_langs
            }
