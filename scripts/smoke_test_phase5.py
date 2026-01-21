"""
Phase 5 Smoke Test
Quick validation of all components
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def smoke_test():
    print("=" * 60)
    print("PHASE 5 SMOKE TEST")
    print("=" * 60)
    
    # Test 1: Imports
    print("\n[1/5] Testing imports...")
    try:
        from src.app.models.recommendation import (
            Recommendation, RecommendationDecision, RiskItem,
            ComplianceSummary, RFPMetadata
        )
        from src.app.services.decision_config import CONFIDENCE_BASE_SCORES
        from src.app.services.value_extractor import ValueExtractor
        from src.app.utils.retry import retry_with_backoff
        from src.app.services.decision_engine import DecisionEngine
        from src.app.services.justification_generator import JustificationGenerator
        from src.app.services.tool_executor import ToolExecutorService
        from src.app.services.recommendation_service import RecommendationService
        from src.app.agent.recommendation_agent import RecommendationAgent
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
         print(f"❌ Import failed with unexpected error: {e}")
         return False
    
    # Test 2: Model creation
    print("\n[2/5] Testing model creation...")
    try:
        decision = RecommendationDecision.BID
        print(f"✅ RecommendationDecision: {decision.value}")
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False
    
    # Test 3: Value extractor
    print("\n[3/5] Testing value extractor...")
    try:
        extractor = ValueExtractor()
        budget = extractor.extract_budget("Budget is $150,000")
        print(f"✅ Extracted budget: {budget}")
    except Exception as e:
        print(f"❌ Value extractor failed: {e}")
        return False
    
    # Test 4: Decision engine
    print("\n[4/5] Testing decision engine...")
    try:
        engine = DecisionEngine()
        print("✅ Decision engine initialized")
    except Exception as e:
        print(f"❌ Decision engine failed: {e}")
        return False
    
    # Test 5: Agent initialization
    print("\n[5/5] Testing agent initialization...")
    try:
        agent = RecommendationAgent()
        health = agent.health_check()
        print(f"✅ Agent health: {health}")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        # Continue anyway for smoke test to see what else fails or if it's just this
        return False
    
    print("\n" + "=" * 60)
    print("SMOKE TEST PASSED ✅")
    print("=" * 60)
    return True

if __name__ == "__main__":
    smoke_test()
