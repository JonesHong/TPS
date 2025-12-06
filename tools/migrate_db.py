import asyncio
import aiosqlite
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tps.config import settings

async def migrate():
    print(f"Migrating database at {settings.db_path}...")
    
    async with aiosqlite.connect(settings.db_path) as conn:
        try:
            await conn.execute("ALTER TABLE translations ADD COLUMN refined_text TEXT;")
            print("Added 'refined_text' column to 'translations' table.")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("'refined_text' column already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
