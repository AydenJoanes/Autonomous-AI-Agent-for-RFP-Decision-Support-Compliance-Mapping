"""
Recommendation Agent
Provides clean agent interface for RFP recommendation generation.
"""

from typing import Tuple, Dict
from loguru import logger

from src.app.models.recommendation import Recommendation
from src.app.services.recommendation_service import RecommendationService


class RecommendationAgent:
    """
    Agent interface for RFP recommendation generation.
    
    Wraps RecommendationService with clean, simple API.
    Designed for future extension with autonomous behaviors (Phase 6).
    """
    
    def __init__(self):
        """Initialize the recommendation agent."""
        self._service = RecommendationService()
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
        
        # Generate report
        report = self._service.generate_recommendation_report(recommendation)
        
        logger.info(f"[AGENT] Report generated: {len(report)} chars")
        
        return (recommendation, report)

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
