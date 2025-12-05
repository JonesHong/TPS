"""FastAPI REST API routes for TPS"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
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
    source_lang: str = Field(..., min_length=2, description="Source language code (e.g., 'en', 'zh-tw')")
    target_lang: str = Field(..., min_length=2, description="Target language code (e.g., 'zh-tw', 'en')")
    format: str = Field(default="plain", description="Format type: 'plain' or 'html'")
    enable_refinement: bool = Field(default=False, description="Enable AI refinement for better quality")
    refinement_model: Optional[str] = Field(default=None, description="Model for refinement (default: gpt-4o-mini)")


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


# === Dependency Injection ===

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
        refinement_model=request.refinement_model
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
