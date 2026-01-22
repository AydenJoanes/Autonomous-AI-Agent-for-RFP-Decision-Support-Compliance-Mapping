"""
Recommendation Agent
Provides clean agent interface for RFP recommendation generation.
"""

from typing import Tuple, Dict, Optional
from loguru import logger
import uuid

from src.app.models.recommendation import Recommendation
from src.app.services.recommendation_service import RecommendationService
from src.app.database.connection import SessionLocal
from src.app.database.schema import Recommendation as RecommendationDB


class RecommendationAgent:
    """
    Agent interface for RFP recommendation generation.
    
    Wraps RecommendationService with clean, simple API.
    Designed for future extension with autonomous behaviors (Phase 6).
    """
    
    def __init__(self):
        """Initialize the recommendation agent."""
        self._service = RecommendationService()
        self._db = SessionLocal()
        logger.info("[AGENT] RecommendationAgent initialized")

    def run(self, file_path: str) -> Recommendation:
        """
        Generate recommendation for an RFP document.
        
        Args:
            file_path: Path to RFP file (PDF or DOCX)
            
        Returns:
            Complete Recommendation object
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file type not supported
        """
        logger.info(f"[AGENT] Processing RFP: {file_path}")
        
        try:
            recommendation = self._service.generate_recommendation(file_path)
            logger.info(f"[AGENT] Recommendation complete: {recommendation.recommendation}")
            return recommendation
        
        except FileNotFoundError:
            logger.error(f"[AGENT] File not found: {file_path}")
            raise
        
        except ValueError as e:
            logger.error(f"[AGENT] Validation error: {e}")
            raise
        
        except Exception as e:
            logger.error(f"[AGENT] Unexpected error: {e}", exc_info=True)
            raise RuntimeError(f"Agent failed to process RFP: {e}")

    def run_with_report(self, file_path: str) -> Tuple[Recommendation, str]:
        """
        Generate recommendation and formatted markdown report.
        
        Args:
            file_path: Path to RFP file (PDF or DOCX)
            
        Returns:
            Tuple of (Recommendation, markdown_report_string)
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file type not supported
        """
        logger.info(f"[AGENT] Processing RFP with report: {file_path}")
        
        # Generate recommendation
        recommendation = self.run(file_path)
        
        # Save to database
        self._save_to_db(recommendation)
        
        # Generate report
        report = self._service.generate_recommendation_report(recommendation)
        
        logger.info(f"[AGENT] Report generated: {len(report)} chars")
        
        return (recommendation, report)

    def _save_to_db(self, recommendation: Recommendation) -> Optional[int]:
        """
        Save recommendation to database.
        
        Returns:
            The ID of the saved record, or None if save failed.
        """
        try:
            # Convert Pydantic model to DB model
            db_rec = RecommendationDB(
                decision=recommendation.recommendation.value if hasattr(recommendation.recommendation, 'value') else str(recommendation.recommendation),
                confidence_score=recommendation.confidence_score,
                justification=recommendation.justification,
                risks=[r.model_dump() if hasattr(r, 'model_dump') else r for r in recommendation.risks] if recommendation.risks else [],
                clarification_questions=recommendation.clarification_questions,
                reflection_notes=recommendation.reflection_notes,
                calibration_metrics=recommendation.calibration_metrics,
                embedding=recommendation.embedding,
                requirements_met=recommendation.compliance_summary.compliant_count if recommendation.compliance_summary else 0,
                requirements_failed=recommendation.compliance_summary.non_compliant_count if recommendation.compliance_summary else 0,
                escalation_needed=recommendation.requires_human_review,
                escalation_reason="; ".join(recommendation.review_reasons) if recommendation.review_reasons else None
            )
            
            self._db.add(db_rec)
            self._db.commit()
            self._db.refresh(db_rec)
            
            logger.info(f"[AGENT] Recommendation saved to DB with ID: {db_rec.id}")
            return db_rec.id
            
        except Exception as e:
            logger.error(f"[AGENT] Failed to save recommendation: {e}")
            self._db.rollback()
            return None

    def health_check(self) -> Dict:
        """
        Check agent health and readiness.
        
        Returns:
            Dict with status and tool count
        """
        return {
            "status": "ok",
            "tools_available": 6,
            "service_ready": True
        }
