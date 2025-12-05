#!/usr/bin/env python3
"""
Cache cleanup script for TPS.

Deletes translation cache entries older than 90 days (configurable).
Should be run weekly via cron job.

Usage:
    uv run python scripts/cleanup_cache.py [--days 90] [--dry-run]

Cron example (every Sunday at 3 AM):
    0 3 * * 0 cd /path/to/tps && uv run python scripts/cleanup_cache.py
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tps.db.connection import DatabaseManager
from tps.db.dao import TranslationDAO
from tps.config import settings


async def cleanup_cache(days: int, dry_run: bool = False) -> int:
    """
    Clean up cache entries older than specified days.
    
    Args:
        days: Delete entries older than this many days
        dry_run: If True, only count entries without deleting
        
    Returns:
        Number of entries deleted (or would be deleted in dry run)
    """
    db_manager = await DatabaseManager.get_instance()
    
    async with db_manager.get_connection() as conn:
        if dry_run:
            # Count entries that would be deleted
            cursor = await conn.execute(
                """
                SELECT COUNT(*) as count FROM translations 
                WHERE last_accessed_at < datetime('now', ? || ' days')
                """,
                (f"-{days}",)
            )
            row = await cursor.fetchone()
            return row["count"] if row else 0
        else:
            # Actually delete entries
            dao = TranslationDAO(db_manager)
            return await dao.delete_expired_entries(days)


async def main():
    parser = argparse.ArgumentParser(
        description="Clean up old translation cache entries"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=settings.cache_expire_days,
        help=f"Delete entries older than N days (default: {settings.cache_expire_days})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be deleted, don't actually delete"
    )
    
    args = parser.parse_args()
    
    print(f"TPS Cache Cleanup")
    print(f"Database: {settings.db_path}")
    print(f"Threshold: {args.days} days")
    print(f"Mode: {'Dry run' if args.dry_run else 'Live'}")
    print("-" * 40)
    
    count = await cleanup_cache(args.days, args.dry_run)
    
    if args.dry_run:
        print(f"Would delete {count} entries")
    else:
        print(f"Deleted {count} entries")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
