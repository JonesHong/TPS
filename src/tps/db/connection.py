"""SQLite Database Connection Manager with WAL mode and optimized settings"""

import asyncio
import aiosqlite
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from ..config import settings


class DatabaseManager:
    """
    Manages SQLite database connections with WAL mode and performance optimizations.
    
    CRITICAL PRAGMA settings applied on each connection:
    - journal_mode = WAL (Write-Ahead Logging for concurrency)
    - synchronous = NORMAL (balance between safety and speed)
    - cache_size = -64000 (64MB cache)
    - busy_timeout = 5000 (5 second wait on locks)
    """
    
    _instance: Optional["DatabaseManager"] = None
    _lock = asyncio.Lock()
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.db_path
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> "DatabaseManager":
        """Get singleton instance of DatabaseManager"""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance.initialize()
            return cls._instance
    
    async def initialize(self) -> None:
        """Initialize database and create tables if not exists"""
        if self._initialized:
            return
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with self.get_connection() as conn:
            await self._apply_pragmas(conn)
            await self._create_tables(conn)
        
        self._initialized = True
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection with proper settings applied"""
        conn = await aiosqlite.connect(self.db_path)
        try:
            await self._apply_pragmas(conn)
            conn.row_factory = aiosqlite.Row
            yield conn
        finally:
            await conn.close()
    
    async def _apply_pragmas(self, conn: aiosqlite.Connection) -> None:
        """Apply critical PRAGMA settings for performance and reliability"""
        await conn.execute("PRAGMA journal_mode = WAL;")
        await conn.execute("PRAGMA synchronous = NORMAL;")
        await conn.execute("PRAGMA cache_size = -64000;")  # 64MB
        await conn.execute("PRAGMA busy_timeout = 5000;")  # 5 seconds
        await conn.execute("PRAGMA temp_store = MEMORY;")
        await conn.execute("PRAGMA mmap_size = 268435456;")  # 256MB memory-mapped I/O
    
    async def _create_tables(self, conn: aiosqlite.Connection) -> None:
        """Create database tables and indices if not exists"""
        
        # translations table (Cache Layer)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                cache_key TEXT PRIMARY KEY,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                refined_text TEXT,
                provider TEXT NOT NULL,
                is_refined INTEGER DEFAULT 0,
                refinement_model TEXT,
                char_count INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
            )
        """)
        
        # daily_usage_stats table (Cost Control)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage_stats (
                date TEXT NOT NULL,
                provider TEXT NOT NULL,
                request_count INTEGER DEFAULT 0,
                char_count INTEGER DEFAULT 0,
                token_input INTEGER DEFAULT 0,
                token_output INTEGER DEFAULT 0,
                cost_estimated REAL DEFAULT 0.0,
                PRIMARY KEY (date, provider)
            )
        """)
        
        # Indices for cleanup operations
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cleanup 
            ON translations(last_accessed_at)
        """)
        
        # Index for expiration queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires 
            ON translations(expires_at)
        """)
        
        await conn.commit()
    
    async def close(self) -> None:
        """Clean up resources"""
        self._initialized = False
        DatabaseManager._instance = None
