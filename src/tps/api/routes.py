"""FastAPI REST API routes for TPS"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..core.workflow import TranslationWorkflow, TranslationOptions, TranslationResponse
from ..core.cost_control import CostController
from ..db.connection import DatabaseManager
from ..db.dao import TranslationDAO


router = APIRouter()


# === Request/Response Models ===

class TranslationRequest(BaseModel):
    """Request model for translation endpoint"""
    text: str = Field(..., min_length=1, description="Text to translate")
    source_lang: Optional[str] = Field(default=None, description="Source language code (e.g., 'en', 'zh-tw'). If not provided, auto-detect will be used.")
    target_lang: str = Field(..., min_length=2, description="Target language code (e.g., 'zh-tw', 'en')")
    format: str = Field(default="plain", description="Format type: 'plain' or 'html'")
    enable_refinement: bool = Field(default=False, description="Enable AI refinement for better quality")
    refinement_model: Optional[str] = Field(default=None, description="Model for refinement (default: gpt-4o-mini)")
    preferred_provider: Optional[str] = Field(default=None, description="Preferred translation provider: 'auto', 'deepl', 'openai', 'google'")


class TranslationData(BaseModel):
    """Data portion of successful translation response"""
    text: str
    provider: str
    is_refined: bool
    is_cached: bool


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[TranslationData] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str


class StatsResponse(BaseModel):
    """Usage statistics response"""
    date: str
    providers: dict
    total_cost: float
    total_requests: int
    budgets: dict


# === Pagination Models ===

class TranslationItem(BaseModel):
    """Single translation item for list response"""
    cache_key: str
    source_lang: str
    target_lang: str
    original_text: str
    translated_text: str
    provider: str
    is_refined: bool
    char_count: int
    created_at: str


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int
    page: int
    page_size: int
    total_pages: int


class TranslationsListResponse(BaseModel):
    """Response for paginated translations list"""
    items: List[TranslationItem]
    meta: PaginationMeta


# === Dashboard Models ===

class DailyTrendItem(BaseModel):
    """Daily trend data point"""
    date: str
    count: int


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response"""
    total_requests: int
    total_chars: int
    total_cost_usd: float
    cache_hit_rate: float
    provider_usage: dict
    daily_trend: List[DailyTrendItem]
    # Provider quota details (monthly)
    deepl_chars_month: int = 0
    google_chars_month: int = 0
    openai_tokens_input_month: int = 0
    openai_tokens_output_month: int = 0
    openai_cost_month: float = 0.0
    deepl_quota_percent: float = 0.0
    google_quota_percent: float = 0.0


class LanguagesResponse(BaseModel):
    """Available languages response"""
    source_languages: List[str]
    target_languages: List[str]


# === Dependency Injection ===

async def get_dao() -> TranslationDAO:
    """Dependency to get TranslationDAO instance"""
    db_manager = await DatabaseManager.get_instance()
    return TranslationDAO(db_manager)


async def get_workflow() -> TranslationWorkflow:
    """Dependency to get TranslationWorkflow instance"""
    db_manager = await DatabaseManager.get_instance()
    dao = TranslationDAO(db_manager)
    cost_controller = CostController(dao)
    return TranslationWorkflow(dao, cost_controller)


async def get_cost_controller() -> CostController:
    """Dependency to get CostController instance"""
    db_manager = await DatabaseManager.get_instance()
    dao = TranslationDAO(db_manager)
    return CostController(dao)


# === Endpoints ===

@router.post("/translate", response_model=APIResponse, tags=["Translation"])
async def translate(
    request: TranslationRequest,
    workflow: TranslationWorkflow = Depends(get_workflow)
) -> APIResponse:
    """
    Translate text using the multi-tier translation system.
    
    Translation Priority:
    1. Local Cache (instant, free)
    2. DeepL (high quality, free tier)
    3. OpenAI gpt-4o-mini (very low cost)
    4. Google Translate (last resort)
    
    Optional: AI refinement to improve translation quality.
    """
    options = TranslationOptions(
        format_type=request.format,
        enable_refinement=request.enable_refinement,
        refinement_model=request.refinement_model,
        preferred_provider=request.preferred_provider
    )
    
    result: TranslationResponse = await workflow.translate(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        options=options
    )
    
    if result.success:
        return APIResponse(
            success=True,
            data=TranslationData(
                text=result.text,
                provider=result.provider,
                is_refined=result.is_refined,
                is_cached=result.is_cached
            )
        )
    else:
        return APIResponse(
            success=False,
            error=result.error
        )


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Simple health check endpoint.
    
    Returns the service status and version.
    """
    from .. import __version__
    return HealthResponse(
        status="healthy",
        version=__version__
    )


@router.get("/stats", response_model=StatsResponse, tags=["System"])
async def get_stats(
    date: Optional[str] = None,
    cost_controller: CostController = Depends(get_cost_controller)
) -> StatsResponse:
    """
    Get usage statistics for the current day or a specific date.
    
    Args:
        date: Optional date in 'YYYY-MM-DD' format. Defaults to today.
        
    Returns:
        Usage statistics including request counts, costs, and budget status.
    """
    summary = await cost_controller.get_daily_summary(date)
    return StatsResponse(**summary)


@router.get("/providers", tags=["System"])
async def get_provider_status(
    workflow: TranslationWorkflow = Depends(get_workflow)
) -> dict:
    """
    Get availability status of all translation providers.
    """
    return {
        "providers": {
            "deepl": {
                "available": await workflow.deepl.is_available(),
                "quota_exceeded": workflow.cost_controller.is_quota_exceeded("deepl")
            },
            "openai": {
                "available": await workflow.openai.is_available(),
                "budget_exceeded": await workflow.cost_controller.is_openai_budget_exceeded()
            },
            "google": {
                "available": await workflow.google.is_available(),
                "budget_exceeded": await workflow.cost_controller.is_budget_exceeded("google")
            }
        }
    }


# === Frontend API Endpoints ===

@router.get("/translations", response_model=TranslationsListResponse, tags=["Frontend"])
async def list_translations(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(default=None, description="Search query for original/translated text"),
    providers: Optional[str] = Query(default=None, description="Comma-separated provider names (deepl,google,openai)"),
    source_lang: Optional[str] = Query(default=None, description="Filter by source language"),
    target_lang: Optional[str] = Query(default=None, description="Filter by target language"),
    is_refined: Optional[bool] = Query(default=None, description="Filter by refinement status"),
    dao: TranslationDAO = Depends(get_dao)
) -> TranslationsListResponse:
    """
    Get paginated list of cached translations with optional filters.
    
    Supports:
    - Full-text search on original and translated text
    - Filter by provider (multiple allowed)
    - Filter by source/target language
    - Filter by AI refinement status
    """
    # Parse providers string to list
    provider_list = None
    if providers:
        provider_list = [p.strip().lower() for p in providers.split(",")]
    
    items, total = await dao.get_translations_paginated(
        page=page,
        page_size=page_size,
        search_query=q,
        providers=provider_list,
        source_lang=source_lang,
        target_lang=target_lang,
        is_refined=is_refined
    )
    
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    
    return TranslationsListResponse(
        items=[
            TranslationItem(
                cache_key=item.cache_key,
                source_lang=item.source_lang,
                target_lang=item.target_lang,
                original_text=item.original_text,
                translated_text=item.translated_text,
                provider=item.provider,
                is_refined=item.is_refined,
                char_count=item.char_count,
                created_at=str(item.created_at) if item.created_at else ""
            )
            for item in items
        ],
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/stats/dashboard", response_model=DashboardStatsResponse, tags=["Frontend"])
async def get_dashboard_stats(
    days: int = Query(default=30, ge=1, le=365, description="Number of days for trend data"),
    dao: TranslationDAO = Depends(get_dao)
) -> DashboardStatsResponse:
    """
    Get comprehensive dashboard statistics.
    
    Returns:
    - Total translation requests
    - Total characters translated
    - Total estimated cost (USD)
    - Cache hit rate
    - Usage breakdown by provider
    - Daily volume trend
    - Provider quota details (monthly)
    """
    stats = await dao.get_dashboard_stats(days=days)
    
    return DashboardStatsResponse(
        total_requests=stats["total_requests"],
        total_chars=stats["total_chars"],
        total_cost_usd=stats["total_cost_usd"],
        cache_hit_rate=stats["cache_hit_rate"],
        provider_usage=stats["provider_usage"],
        daily_trend=[
            DailyTrendItem(date=item["date"], count=item["count"])
            for item in stats["daily_trend"]
        ],
        # Provider quota details
        deepl_chars_month=stats.get("deepl_chars_month", 0),
        google_chars_month=stats.get("google_chars_month", 0),
        openai_tokens_input_month=stats.get("openai_tokens_input_month", 0),
        openai_tokens_output_month=stats.get("openai_tokens_output_month", 0),
        openai_cost_month=stats.get("openai_cost_month", 0.0),
        deepl_quota_percent=stats.get("deepl_quota_percent", 0.0),
        google_quota_percent=stats.get("google_quota_percent", 0.0)
    )


@router.get("/languages", response_model=LanguagesResponse, tags=["Frontend"])
async def get_available_languages(
    dao: TranslationDAO = Depends(get_dao)
) -> LanguagesResponse:
    """
    Get list of available source and target languages from cached translations.
    Useful for populating filter dropdowns in the frontend.
    """
    languages = await dao.get_available_languages()
    return LanguagesResponse(**languages)
