"""
Verification script for RFP Parser and Requirement Processor Tools
"""
import sys
import os
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.agent.tools.rfp_parser_tool import RFPParserTool
from src.app.agent.tools.requirement_processor_tool import RequirementProcessorTool
from src.app.services.parser.factory import DocumentParserFactory

def test_parser_factory():
    logger.info("Testing DocumentParserFactory...")
    
    # Create a dummy file
    dummy_path = Path("test_rfp.md")
    dummy_path.write_text("# Test RFP\n\nThe vendor shall provide an AI solution.", encoding="utf-8")
    
    try:
        text = DocumentParserFactory.parse_with_fallback(str(dummy_path.absolute()))
        assert "AI solution" in text
        logger.success(f"Factory parsed file successfully: {text}")
    except Exception as e:
        logger.error(f"Factory test failed: {e}")
    finally:
        if dummy_path.exists():
            dummy_path.unlink()

def test_rfp_parser_tool():
    logger.info("Testing RFPParserTool...")
    tool = RFPParserTool()
    
    # Create dummy file
    dummy_path = Path("test_parser_tool.md")
    dummy_path.write_text("# Header\n\nMust compliance with ISO 27001.", encoding="utf-8")
    
    try:
        result = tool._run(str(dummy_path.absolute()))
        assert "compliance" in result
        logger.success(f"RFPParserTool passed")
    except Exception as e:
        logger.error(f"RFPParserTool failed: {e}")
    finally:
        if dummy_path.exists():
            dummy_path.unlink()

def test_requirement_processor_tool():
    logger.info("Testing RequirementProcessorTool...")
    tool = RequirementProcessorTool()
    
    markdown_text = """
    # Technical Requirements
    
    1. The system must support Python 3.10.
    2. The vendor shall have ISO 27001 certification.
    3. The solution should be deployed on Azure.
    4. Project completion is required within 6 months.
    """
    
    try:
        requirements = tool._run(markdown_text)
        logger.info(f"Extracted {len(requirements)} requirements")
        
        for req in requirements:
            logger.info(f"  - [{req.type}] {req.text} (Priority: {req.priority})")
            
        if len(requirements) >= 3:
            logger.success("RequirementProcessorTool passed (found expected requirements)")
        else:
            logger.warning("RequirementProcessorTool found fewer requirements than expected")
            
    except Exception as e:
        logger.error(f"RequirementProcessorTool failed: {e}")

if __name__ == "__main__":
    logger.info("Starting RFP Tool Verification")
    test_parser_factory()
    test_rfp_parser_tool()
    test_requirement_processor_tool()
