"""FastAPI application entry point for TPS"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import settings
from .db.connection import DatabaseManager
from .core.external_data import ExternalDataService


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    # SECURITY: Do not log request bodies or translation content
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown"""
    # Startup
    logger.info("Starting Translation Proxy System...")
    
    # Initialize database
    db_manager = await DatabaseManager.get_instance()
    logger.info(f"Database initialized at {settings.db_path}")
    
    # Initialize external data service (Exchange rates & Pricing)
    external_data = ExternalDataService(db_manager)
    await external_data.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Translation Proxy System...")
    await db_manager.close()


# Create FastAPI application
app = FastAPI(
    title="Translation Proxy System",
    description="""
高可用、低成本的翻譯中介層 API。

## 功能特點

- **多層次翻譯策略**: Cache → DeepL → OpenAI → Google
- **智慧快取**: SQLite 本地快取，減少 API 呼叫
- **AI 校稿**: 可選的 LLM 翻譯品質提升
- **成本控制**: 每日預算熔斷機制
- **高可用性**: 自動 Failover 機制

## 使用方式

```bash
curl -X POST "http://localhost:8000/translate" \\
     -H "Content-Type: application/json" \\
     -d '{"text": "Hello, world!", "source_lang": "en", "target_lang": "zh-tw"}'
```
    """,
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


def main():
    """Entry point for running the server"""
    import uvicorn
    
    uvicorn.run(
        "tps.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True  # Disable in production
    )


if __name__ == "__main__":
    main()
