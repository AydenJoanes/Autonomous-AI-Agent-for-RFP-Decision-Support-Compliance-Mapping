"""
Recommendation API Routes
Exposes RecommendationAgent capabilities via FastAPI.
"""

from pathlib import Path
from loguru import logger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.app.agent.recommendation_agent import RecommendationAgent
from src.app.models.recommendation import Recommendation

# ============================================================================
# MODELS
# ============================================================================

class RecommendationRequest(BaseModel):
    """Request model for RFP analysis."""
    file_path: str = Field(..., description="Absolute or relative path to RFP file")


class RecommendationReportResponse(BaseModel):
    """Response model containing recommendation and markdown report."""
    recommendation: Recommendation
    report_markdown: str


class HealthResponse(BaseModel):
    """API health status response."""
    status: str
    tools_available: int
    service_ready: bool


# ============================================================================
# ROUTER & AGENT
# ============================================================================

router = APIRouter(prefix="/api/v1/recommendation", tags=["Recommendation"])
agent = RecommendationAgent()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/analyze", response_model=Recommendation)
async def analyze_rfp(request: RecommendationRequest):
    """
    Generate structured recommendation from RFP file.
    
    - Validates file path
    - Runs RecommendationAgent
    - Returns structured JSON recommendation
    """
    file_path = request.file_path.strip()
    
    logger.info(f"[API] Analyze request received for {file_path}")
    
    if not file_path:
        raise HTTPException(status_code=400, detail="File path cannot be empty")
        
    path_obj = Path(file_path)
    if not path_obj.exists():
        logger.error(f"[API] File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
    try:
        recommendation = agent.run(file_path)
        logger.info(f"[API] Recommendation generated: {recommendation.recommendation} ({recommendation.confidence_score}%)")
        return recommendation
        
    except FileNotFoundError:
        # Agent might raise this internally even if check passed
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
    except ValueError as e:
        logger.error(f"[API] Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except RuntimeError as e:
        logger.error(f"[API] Agent runtime error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"[API] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during analysis")


@router.post("/analyze-with-report", response_model=RecommendationReportResponse)
async def analyze_with_report(request: RecommendationRequest):
    """
    Generate recommendation AND human-readable markdown report.
    """
    file_path = request.file_path.strip()
    
    logger.info(f"[API] Analyze+Report request received for {file_path}")
    
    if not file_path:
        raise HTTPException(status_code=400, detail="File path cannot be empty")
        
    path_obj = Path(file_path)
    if not path_obj.exists():
        logger.error(f"[API] File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
    try:
        recommendation, report = agent.run_with_report(file_path)
        logger.info(f"[API] Recommendation generated: {recommendation.recommendation} ({recommendation.confidence_score}%)")
        
        return RecommendationReportResponse(
            recommendation=recommendation,
            report_markdown=report
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
    except ValueError as e:
        logger.error(f"[API] Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except RuntimeError as e:
        logger.error(f"[API] Agent runtime error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"[API] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during analysis")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check recommendation service health.
    """
    try:
        # Use agent's health check
        health_status = agent.health_check()
        return HealthResponse(
            status=health_status.get("status", "unknown"),
            tools_available=health_status.get("tools_available", 0),
            service_ready=health_status.get("service_ready", False)
        )
    except Exception as e:
        logger.error(f"[API] Health check failed: {str(e)}")
        return HealthResponse(
            status="error",
            tools_available=0,
            service_ready=False
        )
