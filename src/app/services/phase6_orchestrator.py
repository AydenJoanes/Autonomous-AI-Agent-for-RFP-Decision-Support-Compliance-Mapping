"""
Phase 6 Orchestrator - Non-Invasive Coordination Layer

Purpose:
  Sequences Phase 6 enhancements (reflection, clarification, embedding)
  AFTER a recommendation is finalized.

  Does NOT touch Phase 5 logic.
  Does NOT introduce autonomy or control loops.
  Does NOT trigger learning.

Execution Order (FIXED):
  1. Reflection (observational, non-blocking)
  2. Clarification Questions (already attached by service)
  3. Embedding Generation (for future similarity search)
  4. Return recommendation unchanged

All failures are logged but never raised.
"""

from typing import Optional
from loguru import logger

from src.app.models.recommendation import Recommendation
from src.app.services.reflection_engine import ReflectionEngine
from src.app.services.clarification_generator import ClarificationGenerator
from src.app.utils.embeddings import generate_embedding


class Phase6Orchestrator:
    """
    Non-invasive orchestrator for Phase 6 enhancements.
    
    This class coordinates post-decision enhancements without modifying
    Phase 5 logic or introducing control loops.
    
    Key Properties:
    - Optional dependency (Phase 5 works without it)
    - Non-blocking (failures logged, never raised)
    - No recursion or retries
    - No learning triggers
    - Deterministic output
    """
    
    def __init__(self):
        """Initialize Phase 6 services."""
        self._reflection_engine = ReflectionEngine()
        self._clarification_generator = ClarificationGenerator()
        logger.info("[ORCHESTRATOR] Phase 6 Orchestrator initialized")
    
    def orchestrate(self, recommendation: Recommendation) -> Recommendation:
        """
        Apply Phase 6 enhancements to a finalized recommendation.
        
        This method is called AFTER the recommendation object is fully built
        (decision, confidence, justification, clarifications all finalized).
        
        It then:
        1. Runs reflection (if not already done)
        2. Ensures clarification questions present
        3. Generates embedding for future similarity search
        4. Returns the same recommendation with optional metadata attached
        
        Args:
            recommendation: Fully finalized Recommendation object
        
        Returns:
            The same Recommendation object with optional Phase 6 metadata:
            - reflection_notes (if not already present)
            - embedding (for pgvector similarity)
        
        Guarantees:
            - Decision never changed
            - Confidence never changed
            - Justification never changed
            - Clarification questions never removed
            - No database writes
            - No learning triggered
            - All failures logged, not raised
            - Response always returned
        """
        logger.info("[ORCHESTRATOR] Starting Phase 6 orchestration")
        
        # ====================================================================
        # STEP 1: Reflection (if not already applied)
        # ====================================================================
        
        if not recommendation.reflection_notes:
            self._apply_reflection(recommendation)
        else:
            logger.info("[ORCHESTRATOR] Reflection already applied, skipping")
        
        # ====================================================================
        # STEP 2: Clarification Questions (already applied by RecommendationService)
        # ====================================================================
        
        # This is just a checkpoint to confirm they're present
        clarifications_count = len(recommendation.clarification_questions or [])
        logger.info(f"[ORCHESTRATOR] Clarification questions present: {clarifications_count}")
        
        # ====================================================================
        # STEP 3: Embedding Generation (for similarity search)
        # ====================================================================
        
        self._generate_embedding(recommendation)
        
        # ====================================================================
        # STEP 4: Return unchanged recommendation
        # ====================================================================
        
        logger.info("[ORCHESTRATOR] Phase 6 orchestration complete")
        return recommendation
    
    # ========================================================================
    # REFLECTION HOOK
    # ========================================================================
    
    def _apply_reflection(self, recommendation: Recommendation) -> None:
        """
        Apply reflection engine to recommendation (non-blocking).
        
        Reflection analyzes the finalized recommendation for logical issues,
        confidence calibration, and patterns.
        
        Rules:
        - Never modifies decision or confidence
        - Never blocks response
        - Failures logged and ignored
        
        Args:
            recommendation: Recommendation object to reflect on
        """
        try:
            logger.debug("[ORCHESTRATOR] Running reflection engine")
            
            reflection = self._reflection_engine.reflect(recommendation)
            recommendation.reflection_notes = reflection
            
            flags_count = len(reflection.get('flags', [])) if reflection else 0
            logger.info(f"[ORCHESTRATOR] Reflection complete: {flags_count} flags")
            
        except Exception as e:
            # Reflection is observational only - failure must not block response
            logger.error(f"[ORCHESTRATOR] Reflection failed (non-blocking): {e}")
            # Do not set reflection_notes on failure
    
    # ========================================================================
    # CLARIFICATION HOOK
    # ========================================================================
    
    def _verify_clarifications(self, recommendation: Recommendation) -> None:
        """
        Verify clarification questions are present (informational only).
        
        This is a checkpoint - clarifications are generated upstream by
        RecommendationService. This just confirms they're available.
        
        Args:
            recommendation: Recommendation object to check
        """
        if recommendation.clarification_questions:
            logger.debug(
                f"[ORCHESTRATOR] Clarifications present: "
                f"{len(recommendation.clarification_questions)} questions"
            )
        else:
            logger.debug("[ORCHESTRATOR] No clarification questions generated")
    
    # ========================================================================
    # EMBEDDING HOOK (NEW - Required for future similarity search)
    # ========================================================================
    
    def _generate_embedding(self, recommendation: Recommendation) -> None:
        """
        Generate embedding for recommendation (non-blocking).
        
        This creates a vector representation of the recommendation for
        future similarity search. The embedding is based on:
        - Justification text
        - Risk descriptions
        
        The embedding is stored but NOT used for any decisions or logic.
        It exists purely to enable future similarity queries.
        
        Rules:
        - Generated AFTER decision is finalized
        - No similarity search happens here
        - No decision influence
        - Failures logged and ignored
        - Stored in recommendations.embedding column
        
        Args:
            recommendation: Recommendation object to embed
        """
        try:
            logger.debug("[ORCHESTRATOR] Generating embedding")
            
            # Build embedding source text from justification and risks
            embedding_text = self._build_embedding_text(recommendation)
            
            if not embedding_text.strip():
                logger.warning("[ORCHESTRATOR] No text available for embedding, skipping")
                return
            
            # Generate vector using OpenAI embeddings
            embedding_vector = generate_embedding(embedding_text)
            
            # Store in recommendation (will be persisted when saved)
            # Note: This field is currently read-only in the response model
            # but can be set here for database storage
            if not hasattr(recommendation, 'embedding'):
                # If model doesn't have this field yet, log and continue
                logger.debug("[ORCHESTRATOR] Embedding model field not available, skipping storage")
            else:
                recommendation.embedding = embedding_vector
                logger.info(f"[ORCHESTRATOR] Embedding generated: {len(embedding_vector)} dimensions")
            
        except Exception as e:
            # Embedding is optional - failure must not block response
            logger.error(f"[ORCHESTRATOR] Embedding generation failed (non-blocking): {e}")
            # Do not set embedding on failure
    
    def _build_embedding_text(self, recommendation: Recommendation) -> str:
        """
        Build source text for embedding from recommendation.
        
        Combines:
        - Justification (primary text)
        - Risk descriptions (secondary context)
        
        This text captures the decision rationale and risk analysis,
        enabling future similarity search.
        
        Args:
            recommendation: Recommendation to extract text from
        
        Returns:
            Concatenated text suitable for embedding
        """
        parts = []
        
        # Primary: Justification
        if recommendation.justification:
            parts.append(recommendation.justification)
        
        # Secondary: Risks
        if recommendation.risks:
            risk_descriptions = []
            for risk in recommendation.risks:
                if risk.description:
                    risk_descriptions.append(risk.description)
            
            if risk_descriptions:
                parts.append("Risks: " + " | ".join(risk_descriptions))
        
        # Combine with separator
        embedding_text = " | ".join(parts)
        
        return embedding_text
