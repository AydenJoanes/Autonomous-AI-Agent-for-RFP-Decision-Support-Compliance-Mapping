"""
Calibration Metrics Service
Measures confidence quality without modifying behavior.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy.orm import Session

# Model version - update when decision logic changes
MODEL_VERSION = "1.0.0"


class CalibrationMetrics:
    """
    Computes calibration metrics for recommendation confidence.
    
    Metrics:
    - Brier Score: Mean squared error between predicted probability and outcome
    - ECE: Expected Calibration Error
    - Over/Under-confidence Ratio: How often confidence exceeds actual success rate
    
    IMPORTANT: Metrics are READ-ONLY. They do NOT modify confidence or decision logic.
    """
    
    def __init__(self, model_version: str = MODEL_VERSION):
        """
        Initialize calibration metrics calculator.
        
        Args:
            model_version: Version tag for tracking model changes
        """
        self.model_version = model_version
        logger.info(f"[CALIBRATION] Initialized with model_version={model_version}")
    
    def compute_brier_score(self, confidence: int, outcome: str) -> float:
        """
        Compute Brier Score for a single prediction.
        
        Brier Score = (predicted_probability - actual_outcome)^2
        
        Args:
            confidence: Predicted confidence (0-100)
            outcome: Actual outcome ('WON' or 'LOST')
            
        Returns:
            Brier score (0 = perfect, 1 = worst)
        """
        # Convert confidence to probability (0-1)
        predicted_prob = confidence / 100.0
        
        # Convert outcome to binary (1 = WON/success, 0 = LOST/failure)
        actual = 1.0 if outcome == 'WON' else 0.0
        
        brier = (predicted_prob - actual) ** 2
        return round(brier, 4)
    
    def compute_ece(
        self, 
        predictions: List[Dict[str, Any]], 
        n_bins: int = 10
    ) -> float:
        """
        Compute Expected Calibration Error (ECE).
        
        ECE measures the average gap between predicted confidence and actual accuracy
        across calibration bins.
        
        Args:
            predictions: List of dicts with 'confidence' and 'outcome'
            n_bins: Number of calibration bins
            
        Returns:
            ECE score (0 = perfectly calibrated)
        """
        if not predictions:
            return 0.0
        
        # Create bins
        bins = [[] for _ in range(n_bins)]
        
        for pred in predictions:
            conf = pred.get('confidence', 50) / 100.0
            bin_idx = min(int(conf * n_bins), n_bins - 1)
            
            actual = 1.0 if pred.get('outcome') == 'WON' else 0.0
            bins[bin_idx].append({'conf': conf, 'actual': actual})
        
        # Compute ECE
        total_samples = len(predictions)
        ece = 0.0
        
        for bin_items in bins:
            if not bin_items:
                continue
            
            n = len(bin_items)
            avg_conf = sum(item['conf'] for item in bin_items) / n
            avg_accuracy = sum(item['actual'] for item in bin_items) / n
            
            # Weighted absolute difference
            ece += (n / total_samples) * abs(avg_accuracy - avg_conf)
        
        return round(ece, 4)
    
    def compute_overconfidence_ratio(
        self, 
        predictions: List[Dict[str, Any]]
    ) -> float:
        """
        Compute overconfidence ratio.
        
        Overconfidence = predictions where confidence > actual success rate
        
        Args:
            predictions: List of dicts with 'confidence' and 'outcome'
            
        Returns:
            Ratio of overconfident predictions (0-1)
        """
        if not predictions:
            return 0.0
        
        # Calculate overall success rate
        won_count = sum(1 for p in predictions if p.get('outcome') == 'WON')
        actual_success_rate = won_count / len(predictions)
        
        # Count overconfident predictions
        overconfident_count = 0
        for pred in predictions:
            pred_conf = pred.get('confidence', 50) / 100.0
            if pred_conf > actual_success_rate:
                overconfident_count += 1
        
        ratio = overconfident_count / len(predictions)
        return round(ratio, 4)
    
    def compute_for_recommendation(
        self, 
        confidence: int, 
        outcome: str
    ) -> Dict[str, Any]:
        """
        Compute all metrics for a single recommendation with outcome.
        
        Args:
            confidence: Predicted confidence (0-100)
            outcome: Actual outcome ('WON', 'LOST', etc.)
            
        Returns:
            Dictionary with all calibration metrics
        """
        if outcome not in ('WON', 'LOST'):
            logger.warning(f"[CALIBRATION] Skipping metrics for non-binary outcome: {outcome}")
            return {
                "error": f"Cannot compute metrics for outcome: {outcome}",
                "model_version": self.model_version,
                "computed_at": datetime.now(timezone.utc).isoformat()
            }
        
        brier = self.compute_brier_score(confidence, outcome)
        
        metrics = {
            "brier_score": brier,
            "expected_calibration_error": None,  # Requires multiple predictions
            "overconfidence_ratio": None,  # Requires multiple predictions
            "model_version": self.model_version,
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"[CALIBRATION] Computed metrics: brier={brier} for confidence={confidence}, outcome={outcome}")
        return metrics
    
    def compute_aggregate_metrics(
        self, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Compute aggregate calibration metrics over all recommendations with outcomes.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with aggregate metrics
        """
        from src.app.database.schema import Recommendation as RecommendationDB
        
        # Get all recommendations with binary outcomes
        recs = db.query(RecommendationDB).filter(
            RecommendationDB.outcome.in_(['WON', 'LOST'])
        ).all()
        
        if not recs:
            logger.warning("[CALIBRATION] No recommendations with outcomes for aggregate metrics")
            return {
                "total_predictions": 0,
                "error": "No recommendations with binary outcomes",
                "model_version": self.model_version,
                "computed_at": datetime.now(timezone.utc).isoformat()
            }
        
        # Build prediction list
        predictions = [
            {
                "confidence": rec.confidence_score,
                "outcome": rec.outcome
            }
            for rec in recs
        ]
        
        # Compute all metrics
        brier_scores = [
            self.compute_brier_score(p['confidence'], p['outcome']) 
            for p in predictions
        ]
        avg_brier = sum(brier_scores) / len(brier_scores)
        
        ece = self.compute_ece(predictions)
        overconf_ratio = self.compute_overconfidence_ratio(predictions)
        
        metrics = {
            "total_predictions": len(predictions),
            "brier_score_avg": round(avg_brier, 4),
            "expected_calibration_error": ece,
            "overconfidence_ratio": overconf_ratio,
            "model_version": self.model_version,
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"[CALIBRATION] Aggregate metrics: brier={avg_brier:.4f}, ECE={ece:.4f}, overconf={overconf_ratio:.4f}")
        return metrics
    
    def store_metrics_for_recommendation(
        self, 
        db: Session, 
        recommendation_id: int, 
        metrics: Dict[str, Any]
    ) -> bool:
        """
        Store calibration metrics on a recommendation record.
        
        Args:
            db: Database session
            recommendation_id: ID of recommendation
            metrics: Computed metrics dictionary
            
        Returns:
            True if stored successfully
        """
        from src.app.database.schema import Recommendation as RecommendationDB
        import json
        
        try:
            rec = db.query(RecommendationDB).filter(
                RecommendationDB.id == recommendation_id
            ).first()
            
            if not rec:
                logger.error(f"[CALIBRATION] Recommendation {recommendation_id} not found")
                return False
            
            # Store as JSON in calibration_metrics column
            rec.calibration_metrics = json.dumps(metrics)
            db.commit()
            
            logger.info(f"[CALIBRATION] Stored metrics for recommendation {recommendation_id}")
            return True
            
        except Exception as e:
            logger.error(f"[CALIBRATION] Failed to store metrics: {e}")
            db.rollback()
            return False
