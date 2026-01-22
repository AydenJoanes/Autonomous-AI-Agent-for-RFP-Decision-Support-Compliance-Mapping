"""
Outcome Service
Handles recording of real-world outcomes for recommendations to enable future learning.
"""
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
from fastapi import HTTPException

from src.app.database.connection import get_db_context
from src.app.database.schema import Recommendation as DBRecommendation
from src.app.models.recommendation import OutcomeCreate, Recommendation as PydanticRecommendation

class OutcomeService:
    """
    Service for managing recommendation outcomes.
    Ensures that historical decision data remains immutable while updating outcome status.
    """

    def record_outcome(self, recommendation_id: int, outcome_data: OutcomeCreate) -> DBRecommendation:
        """
        Record the real-world outcome for a specific recommendation.

        Args:
            recommendation_id: ID of the recommendation to update
            outcome_data: The outcome data (status, notes, metrics)

        Returns:
            Updated DBRecommendation object
            
        Raises:
            HTTPException: If recommendation not found or other error
        """
        logger.info(f"[OUTCOME_SERVICE] Recording outcome for recommendation {recommendation_id}: {outcome_data.outcome}")

        with get_db_context() as db:
            # 1. Fetch recommendation
            recommendation = db.query(DBRecommendation).filter(DBRecommendation.id == recommendation_id).first()
            
            if not recommendation:
                logger.error(f"[OUTCOME_SERVICE] Recommendation {recommendation_id} not found")
                raise HTTPException(status_code=404, detail=f"Recommendation with ID {recommendation_id} not found")

            # 2. Validate state (Optional: could prevent overwriting if already finalized, but requirement says "Attach outcome")
            # For now, we allow updates/corrections to outcomes.
            
            # 3. Update outcome fields
            # CRITICAL: Do NOT modify decision, confidence, or original justification
            recommendation.outcome_status = outcome_data.outcome.value
            recommendation.outcome_notes = outcome_data.notes
            recommendation.outcome_recorded_at = datetime.now(timezone.utc)
            
            if outcome_data.calibration_metrics:
                recommendation.calibration_metrics = outcome_data.calibration_metrics

            # 4. Commit changes
            try:
                db.commit()
                db.refresh(recommendation)
                logger.info(f"[OUTCOME_SERVICE] Successfully recorded outcome for {recommendation_id}")
                return recommendation
            except Exception as e:
                logger.error(f"[OUTCOME_SERVICE] Database commit failed: {e}")
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to save outcome: {str(e)}")
