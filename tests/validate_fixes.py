
import sys
import os
import unittest
from datetime import datetime

from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.getcwd())

from src.app.database.connection import SessionLocal
from src.app.database.repositories.cert_repository import CertificationRepository
from src.app.services.llm_requirement_extractor import LLMRequirementExtractor
from src.app.models.requirement import Requirement, RequirementType

class TestFixes(unittest.TestCase):
    
    def test_01_cert_dates_updated(self):
        """Verify certification dates were updated."""
        session = SessionLocal()
        repo = CertificationRepository(session)
        try:
            # Check ISO 27001
            cert = repo.get_by_name("ISO 27001")
            self.assertIsNotNone(cert)
            # 2028-03-14
            self.assertEqual(str(cert['valid_until']), "2028-03-14")
            self.assertEqual(cert['status'], 'active')
            
            # Check GDPR
            cert = repo.get_by_name("GDPR Compliance") or repo.get_by_name("GDPR")
            self.assertIsNotNone(cert)
            # 2029-01-09
            self.assertEqual(str(cert['valid_until']), "2029-01-09")
            
        finally:
            session.close()

    @patch('src.app.services.llm_requirement_extractor.LLMRequirementExtractor.__init__', return_value=None)
    def test_02_deduplication_logic(self, mock_init):
        """Verify LLM requirement extractor deduplication."""
        extractor = LLMRequirementExtractor()
        
        # Create duplicate requirements
        req1 = Requirement(
            type=RequirementType.CERTIFICATION,
            text="Must be HIPAA compliant",
            extracted_value="HIPAA Compliance",
            is_mandatory=True
        )
        req2 = Requirement(
            type=RequirementType.CERTIFICATION,
            text="System requires HIPAA",
            extracted_value="HIPAA", # Shorter, contained in req1 value
            is_mandatory=True
        )
        req3 = Requirement(
            type=RequirementType.CERTIFICATION,
            text="Vendor must have ISO 27001",
            extracted_value="ISO 27001",
            is_mandatory=True
        )
        
        # Input as separate chunks
        chunks = [[req1], [req2], [req3]]
        
        merged = extractor.merge_chunk_extractions(chunks)
        
        values = [r.extracted_value for r in merged]
        print(f"Merged values: {values}")
        
        # Should have HIPAA Compliance (longer) and ISO 27001
        self.assertEqual(len(merged), 2)
        self.assertIn("HIPAA Compliance", values)
        self.assertIn("ISO 27001", values)
        self.assertNotIn("HIPAA", values) # Should be deduped

    @patch('src.app.services.llm_requirement_extractor.LLMRequirementExtractor.__init__', return_value=None)
    def test_03_deduplication_exact_match(self, mock_init):
        """Verify strict exact match deduplication."""
        extractor = LLMRequirementExtractor()
        
        req1 = Requirement(
            type=RequirementType.EXPERIENCE,
            text="Cloud experience",
            extracted_value="Cloud Native",
            is_mandatory=True
        )
        req2 = Requirement(
            type=RequirementType.EXPERIENCE,
            text="Experience with cloud",
            extracted_value="cloud native", # Case diff
            is_mandatory=True
        )
        
        merged = extractor.merge_chunk_extractions([[req1, req2]])
        self.assertEqual(len(merged), 1)
        
if __name__ == "__main__":
    unittest.main()
