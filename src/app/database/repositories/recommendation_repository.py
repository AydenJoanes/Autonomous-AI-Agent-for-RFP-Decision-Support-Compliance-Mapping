"""
Recommendation Repository - Database operations for recommendations with similarity search
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from src.app.database.repositories.base_repository import BaseRepository
from src.app.database.schema import Recommendation as RecommendationDB


class RecommendationRepository(BaseRepository[RecommendationDB]):
    """Repository for recommendation operations with pgvector similarity search."""
    
    # Default similarity threshold (lower = more similar for cosine distance)
    DEFAULT_SIMILARITY_THRESHOLD = 0.5
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
    
    def get_all(self, limit: int = 100) -> List[Dict]:
        """
        Get all recommendations.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of all recommendations
        """
        query = "SELECT * FROM recommendations ORDER BY created_at DESC LIMIT :limit"
        return self.fetch_all(query, {"limit": limit})
    
    def get_by_id(self, recommendation_id: int) -> Optional[Dict]:
        """
        Get a recommendation by ID.
        
        Args:
            recommendation_id: Recommendation ID
            
        Returns:
            Recommendation data or None
        """
        query = "SELECT * FROM recommendations WHERE id = :rec_id"
        return self.fetch_one(query, {"rec_id": recommendation_id})
    
    def get_by_analysis_id(self, analysis_id: str) -> Optional[Dict]:
        """
        Get a recommendation by analysis ID.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Recommendation data or None
        """
        query = "SELECT * FROM recommendations WHERE analysis_id = :analysis_id"
        return self.fetch_one(query, {"analysis_id": analysis_id})
    
    def find_similar(
        self, 
        embedding: List[float], 
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict]:
        """
        Find similar recommendations using pgvector cosine distance.
        
        Args:
            embedding: Query embedding vector (1536 dimensions)
            limit: Maximum number of results
            threshold: Maximum distance threshold (optional)
            
        Returns:
            List of similar recommendations with distance scores
        """
        if not embedding or len(embedding) != 1536:
            logger.warning("[REPO] Invalid embedding for similarity search")
            return []
        
        threshold = threshold or self.DEFAULT_SIMILARITY_THRESHOLD
        
        # Convert embedding to PostgreSQL vector format
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # Query with pgvector cosine distance operator <=>
        query = f"""
            SELECT 
                *,
                (embedding <=> '{embedding_str}'::vector) as distance
            FROM recommendations 
            WHERE embedding IS NOT NULL
            AND (embedding <=> '{embedding_str}'::vector) < :threshold
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """
        
        results = self.fetch_all(query, {"threshold": threshold, "limit": limit})
        logger.info(f"[REPO] Found {len(results)} similar recommendations")
        return results
    
    def get_with_outcomes(self, limit: int = 100) -> List[Dict]:
        """
        Get recommendations that have recorded outcomes.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of recommendations with outcomes
        """
        query = """
            SELECT * FROM recommendations 
            WHERE outcome IS NOT NULL
            ORDER BY outcome_recorded_at DESC
            LIMIT :limit
        """
        return self.fetch_all(query, {"limit": limit})
    
    def get_by_outcome_status(self, outcome: str) -> List[Dict]:
        """
        Get recommendations by outcome status.
        
        Args:
            outcome: 'WON', 'LOST', 'NO_BID_CONFIRMED', or 'WITHDRAWN'
            
        Returns:
            List of recommendations with the specified outcome
        """
        query = """
            SELECT * FROM recommendations 
            WHERE outcome = :outcome
            ORDER BY created_at DESC
        """
        return self.fetch_all(query, {"outcome": outcome})
    
    def get_by_decision(self, decision: str) -> List[Dict]:
        """
        Get recommendations by decision type.
        
        Args:
            decision: 'BID', 'NO_BID', or 'CONDITIONAL_BID'
            
        Returns:
            List of recommendations with the specified decision
        """
        query = """
            SELECT * FROM recommendations 
            WHERE decision = :decision
            ORDER BY created_at DESC
        """
        return self.fetch_all(query, {"decision": decision})
    
    def update_embedding(self, recommendation_id: int, embedding: List[float]) -> bool:
        """
        Update the embedding for a recommendation.
        
        Args:
            recommendation_id: Recommendation ID
            embedding: New embedding vector (1536 dimensions)
            
        Returns:
            True if updated successfully
        """
        if not embedding or len(embedding) != 1536:
            logger.error("[REPO] Invalid embedding dimensions")
            return False
        
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        query = f"""
            UPDATE recommendations 
            SET embedding = '{embedding_str}'::vector
            WHERE id = :rec_id
        """
        
        try:
            self.execute(query, {"rec_id": recommendation_id})
            self.commit()
            logger.info(f"[REPO] Updated embedding for recommendation {recommendation_id}")
            return True
        except Exception as e:
            logger.error(f"[REPO] Failed to update embedding: {e}")
            return False
    
    def count_by_outcome(self) -> Dict[str, int]:
        """
        Count recommendations by outcome status.
        
        Returns:
            Dictionary mapping outcome to count
        """
        query = """
            SELECT outcome, COUNT(*) as count
            FROM recommendations 
            WHERE outcome IS NOT NULL
            GROUP BY outcome
        """
        results = self.fetch_all(query)
        return {r['outcome']: r['count'] for r in results}
    
    def get_recent_with_reflections(self, limit: int = 10) -> List[Dict]:
        """
        Get recent recommendations with reflection notes.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of recommendations with reflections
        """
        query = """
            SELECT * FROM recommendations 
            WHERE reflection_notes IS NOT NULL
            ORDER BY created_at DESC
            LIMIT :limit
        """
        return self.fetch_all(query, {"limit": limit})
