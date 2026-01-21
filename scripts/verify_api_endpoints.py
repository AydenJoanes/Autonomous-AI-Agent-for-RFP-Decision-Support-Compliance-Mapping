
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.app.models.recommendation import Recommendation, RecommendationDecision, ComplianceSummary, RFPMetadata, ComplianceLevel

def create_mock_recommendation():
    """Create a valid dummy Recommendation object."""
    return Recommendation(
        recommendation=RecommendationDecision.BID,
        confidence_score=85,
        justification="Strong technical fit and compliance. " * 5,  # > 50 chars
        executive_summary="This is a great opportunity. " * 2,  # > 20 chars
        risks=[],
        compliance_summary=ComplianceSummary(
            overall_compliance=ComplianceLevel.COMPLIANT,
            compliant_count=10,
            total_evaluated=10,
            confidence_avg=0.9
        ),
        requires_human_review=False,
        rfp_metadata=RFPMetadata(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            word_count=100,
            requirement_count=10
        )
    )

def verify_endpoints():
    print("Starting API Verification...")
    
    # Patch the agent in the routes module BEFORE importing main/app if possible, 
    # but since main imports routes, we need to patch existing module
    
    # Import app
    from main import app
    from src.app.api.routes import recommendation as recommendation_module
    
    # Mock the agent on the imported module
    mock_agent = MagicMock()
    original_agent = recommendation_module.agent
    recommendation_module.agent = mock_agent
    
    client = TestClient(app)
    
    try:
        # 1. Test GET /health
        print("\nTesting GET /health...")
        mock_agent.health_check.return_value = {
            "status": "ok",
            "tools_available": 6,
            "service_ready": True
        }
        
        response = client.get("/api/v1/recommendation/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("✅ /health passed")
        
        # 2. Test POST /analyze
        print("\nTesting POST /analyze...")
        mock_rec = create_mock_recommendation()
        mock_agent.run.return_value = mock_rec
        
        # Create a dummy file for validation
        test_file = Path("test_rfp.pdf")
        test_file.touch()
        
        payload = {"file_path": str(test_file.absolute())}
        response = client.post("/api/v1/recommendation/analyze", json=payload)
        
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] == "BID"
        assert data["confidence_score"] == 85
        print("✅ /analyze passed")
        
        # 3. Test POST /analyze-with-report
        print("\nTesting POST /analyze-with-report...")
        mock_report = "# Report\n\nThis is a test report."
        mock_agent.run_with_report.return_value = (mock_rec, mock_report)
        
        response = client.post("/api/v1/recommendation/analyze-with-report", json=payload)
        
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["report_markdown"] == mock_report
        assert data["recommendation"]["recommendation"] == "BID"
        print("✅ /analyze-with-report passed")
        
        # Clean up
        test_file.unlink()
        
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore agent
        recommendation_module.agent = original_agent

if __name__ == "__main__":
    verify_endpoints()
