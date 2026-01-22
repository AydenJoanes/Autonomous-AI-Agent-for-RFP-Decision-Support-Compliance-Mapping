"""
Outcome API Routes
Endpoints for recording and retrieving outcomes.
"""
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.app.services.outcome_service import OutcomeService
from src.app.models.recommendation import OutcomeCreate

router = APIRouter(tags=["Outcomes"])

@router.post("/{recommendation_id}", summary="Record a bid outcome")
def record_outcome(
    recommendation_id: int, 
    outcome_data: OutcomeCreate,
    service: OutcomeService = Depends(OutcomeService)
):
    """
    Record the real-world outcome of a recommendation.
    
    - **recommendation_id**: The numeric ID of the recommendation
    - **outcome**: The status (WON, LOST, NO_BID_CONFIRMED, UNKNOWN)
    - **notes**: Optional reflection notes
    - **calibration_metrics**: Optional dict of metrics
    """
    try:
        updated_rec = service.record_outcome(recommendation_id, outcome_data)
        return {
            "status": "success",
            "message": "Outcome recorded successfully",
            "data": {
                "recommendation_id": updated_rec.id,
                "outcome_status": updated_rec.outcome_status,
                "recorded_at": updated_rec.outcome_recorded_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))
