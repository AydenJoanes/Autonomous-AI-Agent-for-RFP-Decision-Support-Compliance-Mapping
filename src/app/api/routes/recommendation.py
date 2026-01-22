"""
Recommendation API Routes
Exposes RecommendationAgent capabilities via FastAPI.
"""

from pathlib import Path
from typing import List, Dict, Optional
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
    # Phase 6 Capabilities
    clarification_enabled: bool = True
    reflection_enabled: bool = True
    memory_similarity_enabled: bool = True
    calibration_metrics_enabled: bool = True
    learning_enabled: bool = False


# Phase 6 Response Models
class SimilarRecommendation(BaseModel):
    """Similar recommendation from memory."""
    recommendation_id: int = Field(..., description="ID of similar recommendation")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1)")
    decision: str = Field(..., description="Recommendation decision")
    confidence_score: int = Field(..., description="Confidence score")
    timestamp: str = Field(..., description="When recommendation was created")


class CalibrationMetricsResponse(BaseModel):
    """Calibration metrics for a recommendation."""
    recommendation_id: int = Field(..., description="ID of recommendation")
    metrics: Optional[Dict] = Field(None, description="Calibration metrics if available")
    message: Optional[str] = Field(None, description="Status message if no metrics")


# ============================================================================
# ROUTER & AGENT
# ============================================================================

router = APIRouter(tags=["Recommendation"])
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
    Includes Phase 6 capability advertisement.
    """
    try:
        # Use agent's health check
        health_status = agent.health_check()
        return HealthResponse(
            status=health_status.get("status", "unknown"),
            tools_available=health_status.get("tools_available", 0),
            service_ready=health_status.get("service_ready", False),
            clarification_enabled=True,
            reflection_enabled=True,
            memory_similarity_enabled=True,
            calibration_metrics_enabled=True,
            learning_enabled=False  # Awaits 30+ diverse outcomes
        )
    except Exception as e:
        logger.error(f"[API] Health check failed: {str(e)}")
        return HealthResponse(
            status="error",
            tools_available=0,
            service_ready=False,
            clarification_enabled=True,
            reflection_enabled=True,
            memory_similarity_enabled=True,
            calibration_metrics_enabled=True,
            learning_enabled=False
        )

# ============================================================================
# PHASE 6 MEMORY & METRICS ENDPOINTS (READ-ONLY)
# ============================================================================

@router.get("/{recommendation_id}/similar", response_model=List[SimilarRecommendation])
async def get_similar_recommendations(
    recommendation_id: int,
    limit: int = 5
):
    """
    Get similar past recommendations using memory (Phase 6).
    
    - SELECT-only operation
    - Uses pgvector similarity search
    - Returns top-N similar recommendations
    - No writes, no learning triggered
    """
    if limit < 1 or limit > 20:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 20")
    
    try:
        logger.info(f"[API] Similarity query for recommendation {recommendation_id}")
        
        # Fetch the target recommendation's embedding
        target_rec = agent.db_session.query(
            agent.recommendation_repository.model
        ).filter(
            agent.recommendation_repository.model.id == recommendation_id
        ).first()
        
        if not target_rec:
            raise HTTPException(status_code=404, detail=f"Recommendation {recommendation_id} not found")
        
        if not target_rec.embedding:
            raise HTTPException(
                status_code=400, 
                detail=f"Recommendation {recommendation_id} has no embedding (Phase 5 data?)"
            )
        
        # Query for similar recommendations
        similar = agent.recommendation_repository.find_similar(
            embedding=list(target_rec.embedding),
            limit=limit,
            threshold=0.5
        )
        
        results = []
        for rec in similar:
            results.append(SimilarRecommendation(
                recommendation_id=rec.id,
                similarity_score=rec.get('distance', 1.0),  # Convert distance to similarity
                decision=rec.decision or "UNKNOWN",
                confidence_score=rec.confidence_score or 0,
                timestamp=rec.created_at.isoformat() if rec.created_at else "unknown"
            ))
        
        logger.info(f"[API] Found {len(results)} similar recommendations")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Similarity search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")


@router.get("/{recommendation_id}/calibration", response_model=CalibrationMetricsResponse)
async def get_calibration_metrics(recommendation_id: int):
    """
    Get calibration quality metrics for a recommendation (Phase 6).
    
    - SELECT-only operation
    - Returns stored metrics or null message
    - No computation, no writes
    - No learning triggered
    """
    try:
        logger.info(f"[API] Calibration metrics query for recommendation {recommendation_id}")
        
        # Fetch the recommendation's calibration metrics
        rec = agent.db_session.query(
            agent.recommendation_repository.model
        ).filter(
            agent.recommendation_repository.model.id == recommendation_id
        ).first()
        
        if not rec:
            raise HTTPException(status_code=404, detail=f"Recommendation {recommendation_id} not found")
        
        if rec.calibration_metrics:
            logger.info(f"[API] Returning metrics for recommendation {recommendation_id}")
            return CalibrationMetricsResponse(
                recommendation_id=recommendation_id,
                metrics=rec.calibration_metrics,
                message=None
            )
        else:
            logger.info(f"[API] No calibration metrics for recommendation {recommendation_id}")
            return CalibrationMetricsResponse(
                recommendation_id=recommendation_id,
                metrics=None,
                message="No calibration metrics available (Phase 6 outcome required)"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Calibration query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calibration query failed: {str(e)}")