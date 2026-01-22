"""
Learning Gatekeeper Service
Cold-start protection - prevents learning until sufficient outcomes exist.
"""

from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from loguru import logger
from enum import Enum

from sqlalchemy.orm import Session


class LearningStatus(str, Enum):
    """Learning readiness status."""
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    LOW_DIVERSITY = "LOW_DIVERSITY"
    STALE_DATA = "STALE_DATA"


class LearningGatekeeper:
    """
    Cold-start protection for learning systems.
    
    Prevents any learning or parameter adjustment until:
    - Minimum number of outcomes recorded
    - Outcome diversity exists (not all wins/losses)
    - Data is fresh enough
    """
    
    # Default thresholds (configurable)
    MIN_OUTCOMES_THRESHOLD = 30
    MIN_DIVERSITY_RATIO = 0.1  # At least 10% of each outcome type
    MAX_DATA_AGE_DAYS = 180  # Outcomes older than 6 months considered stale
    
    def __init__(
        self,
        min_outcomes: int = MIN_OUTCOMES_THRESHOLD,
        min_diversity_ratio: float = MIN_DIVERSITY_RATIO,
        max_data_age_days: int = MAX_DATA_AGE_DAYS
    ):
        """
        Initialize the learning gatekeeper.
        
        Args:
            min_outcomes: Minimum outcomes required to enable learning
            min_diversity_ratio: Minimum ratio for each outcome type
            max_data_age_days: Maximum age of outcomes to consider fresh
        """
        self.min_outcomes = min_outcomes
        self.min_diversity_ratio = min_diversity_ratio
        self.max_data_age_days = max_data_age_days
        logger.info(f"[GATEKEEPER] Initialized with min_outcomes={min_outcomes}, "
                   f"diversity_ratio={min_diversity_ratio}, max_age_days={max_data_age_days}")
    
    def check_learning_allowed(
        self, 
        db: Session
    ) -> Tuple[bool, LearningStatus, List[str]]:
        """
        Check if learning is allowed based on outcome data.
        
        Args:
            db: Database session
            
        Returns:
            Tuple of (is_allowed, status, reasons)
        """
        reasons: List[str] = []
        
        # Import here to avoid circular imports
        from src.app.database.schema import Recommendation as RecommendationDB
        
        # Get all recommendations with outcomes
        outcomes = db.query(RecommendationDB).filter(
            RecommendationDB.outcome.isnot(None)
        ).all()
        
        total_outcomes = len(outcomes)
        
        # Check 1: Minimum outcomes threshold
        if total_outcomes < self.min_outcomes:
            reason = f"Insufficient outcomes: {total_outcomes}/{self.min_outcomes} required"
            reasons.append(reason)
            logger.warning(f"[GATEKEEPER] Learning blocked: {reason}")
            return (False, LearningStatus.INSUFFICIENT_DATA, reasons)
        
        # Check 2: Outcome diversity
        outcome_counts = self._count_outcomes(outcomes)
        is_diverse, diversity_reason = self._check_diversity(outcome_counts, total_outcomes)
        if not is_diverse:
            reasons.append(diversity_reason)
            logger.warning(f"[GATEKEEPER] Learning blocked: {diversity_reason}")
            return (False, LearningStatus.LOW_DIVERSITY, reasons)
        
        # Check 3: Data freshness
        is_fresh, freshness_reason = self._check_freshness(outcomes)
        if not is_fresh:
            reasons.append(freshness_reason)
            logger.warning(f"[GATEKEEPER] Learning blocked: {freshness_reason}")
            return (False, LearningStatus.STALE_DATA, reasons)
        
        # All checks passed
        logger.info(f"[GATEKEEPER] Learning ENABLED with {total_outcomes} outcomes")
        return (True, LearningStatus.ENABLED, ["All thresholds met"])
    
    def _count_outcomes(self, outcomes: List[Any]) -> Dict[str, int]:
        """Count outcomes by status."""
        counts: Dict[str, int] = {}
        for rec in outcomes:
            status = getattr(rec, 'outcome', 'UNKNOWN')
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    def _check_diversity(
        self, 
        outcome_counts: Dict[str, int], 
        total: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if outcomes are diverse enough.
        
        Requires at least min_diversity_ratio of WON and LOST outcomes.
        """
        if total == 0:
            return (False, "No outcomes to evaluate")
        
        won_count = outcome_counts.get('WON', 0)
        lost_count = outcome_counts.get('LOST', 0)
        
        won_ratio = won_count / total
        lost_ratio = lost_count / total
        
        # Need at least some wins AND some losses
        if won_ratio < self.min_diversity_ratio:
            return (False, f"Insufficient WON outcomes: {won_ratio:.1%} < {self.min_diversity_ratio:.1%}")
        
        if lost_ratio < self.min_diversity_ratio:
            return (False, f"Insufficient LOST outcomes: {lost_ratio:.1%} < {self.min_diversity_ratio:.1%}")
        
        return (True, None)
    
    def _check_freshness(self, outcomes: List[Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if outcome data is fresh enough.
        
        At least 50% of outcomes must be within max_data_age_days.
        """
        if not outcomes:
            return (False, "No outcomes to evaluate")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.max_data_age_days)
        
        fresh_count = 0
        for rec in outcomes:
            outcome_date = getattr(rec, 'outcome_recorded_at', None)
            if outcome_date and outcome_date >= cutoff_date:
                fresh_count += 1
        
        fresh_ratio = fresh_count / len(outcomes)
        
        if fresh_ratio < 0.5:
            return (False, f"Data too stale: only {fresh_ratio:.1%} outcomes within {self.max_data_age_days} days")
        
        return (True, None)
    
    def get_learning_status(self, db: Session) -> Dict[str, Any]:
        """
        Get detailed learning status report.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with learning status details
        """
        is_allowed, status, reasons = self.check_learning_allowed(db)
        
        # Import here to avoid circular imports
        from src.app.database.schema import Recommendation as RecommendationDB
        
        # Get outcome stats
        outcomes = db.query(RecommendationDB).filter(
            RecommendationDB.outcome.isnot(None)
        ).all()
        
        outcome_counts = self._count_outcomes(outcomes)
        
        return {
            "learning_allowed": is_allowed,
            "status": status.value,
            "reasons": reasons,
            "thresholds": {
                "min_outcomes": self.min_outcomes,
                "min_diversity_ratio": self.min_diversity_ratio,
                "max_data_age_days": self.max_data_age_days
            },
            "current_counts": {
                "total_outcomes": len(outcomes),
                "by_status": outcome_counts
            },
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
