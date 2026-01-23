
import sys
import json
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.services.recommendation_service import RecommendationService
from src.app.models.recommendation import RecommendationDecision

def test_full_pipeline():
    logger.info("Starting Full Pipeline Integration Test")
    
    # 1. Setup
    service = RecommendationService()
    rfp_path = project_root / "data" / "sample_rfps" / "smol_rfp.pdf"
    
    output_dir = project_root / "tests" / "llm_integration" / "test_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "full_recommendation_report.md"
    json_file = output_dir / "full_recommendation_data.json"
    
    if not rfp_path.exists():
        logger.error(f"RFP file not found: {rfp_path}")
        return

    try:
        # 2. Execute
        logger.info(f"Processing RFP: {rfp_path}")
        recommendation = service.generate_recommendation(str(rfp_path))
        
        # 3. Verify
        logger.info(f"Recommendation: {recommendation.recommendation}")
        logger.info(f"Confidence: {recommendation.confidence_score}")
        logger.info(f"Requirements: {recommendation.rfp_metadata.requirement_count}")
        logger.info(f"Compliance: {recommendation.compliance_summary.overall_compliance}")
        
        # 4. Generate Report
        report_text = service.generate_recommendation_report(recommendation)
        
        # 5. Save Results
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_text)
            
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(recommendation.model_dump_json(indent=2))
            
        logger.success(f"Integration Test Complete. Report saved to {report_file}")
        
        # 6. Assertions
        assert recommendation.rfp_metadata.requirement_count > 0, "No requirements extracted"
        assert recommendation.recommendation in [RecommendationDecision.BID, RecommendationDecision.NO_BID, RecommendationDecision.CONDITIONAL_BID], "Invalid decision"
        assert len(recommendation.risks) >= 0, "Risks list should be present (even if empty)"
        assert len(recommendation.justification) > 50, "Justification too short"

    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise

if __name__ == "__main__":
    test_full_pipeline()
