#!/usr/bin/env python3
"""
Database VACUUM script for TPS.

Reclaims unused space and optimizes the SQLite database.
Should be run monthly.

Usage:
    uv run python scripts/vacuum_db.py

Cron example (1st of each month at 4 AM):
    0 4 1 * * cd /path/to/tps && uv run python scripts/vacuum_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tps.db.connection import DatabaseManager
from tps.config import settings


async def vacuum_database() -> dict:
    """
    Run VACUUM on the database to reclaim space.
    
    Returns:
        Dict with before/after file sizes
    """
    db_path = settings.db_path
    
    # Get size before
    size_before = db_path.stat().st_size if db_path.exists() else 0
    
    # Run VACUUM
    db_manager = await DatabaseManager.get_instance()
    async with db_manager.get_connection() as conn:
        await conn.execute("VACUUM")
        await conn.execute("ANALYZE")  # Update statistics for query optimizer
    
    # Get size after
    size_after = db_path.stat().st_size
    
    return {
        "size_before": size_before,
        "size_after": size_after,
        "saved": size_before - size_after
    }


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


async def main():
    print("TPS Database Vacuum")
    print(f"Database: {settings.db_path}")
    print("-" * 40)
    
    if not settings.db_path.exists():
        print("Database file does not exist yet.")
        return 0
    
    result = await vacuum_database()
    
    print(f"Size before: {format_size(result['size_before'])}")
    print(f"Size after:  {format_size(result['size_after'])}")
    print(f"Space saved: {format_size(result['saved'])}")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
