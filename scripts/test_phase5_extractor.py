import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app.services.value_extractor import ValueExtractor

class TestPhase5Extractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = ValueExtractor()

    def test_3_1_budget_extraction(self):
        """Verify Budget Extraction"""
        cases = [
            ("$150,000", "150000"),
            ("$1,500,000.00", "1500000"),
            ("150k", "150000"),
            ("1.5M", "1500000"),
            ("150000 USD", "150000"),
            ("no budget mentioned", None)
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(self.extractor.extract_budget(text), expected)

    def test_3_2_timeline_extraction(self):
        """Verify Timeline Extraction"""
        cases = [
            ("4 months", "4 months"),
            ("16 weeks", "3 months"), # 16/4.33 = 3.69 -> int = 3
            ("90 days", "3 months"),  # Logic might approximate 90/30 = 3
            ("2 years", "24 months"),
            ("no timeline", None),
            ("15 days", "1 months") # Minimum 1
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                # Note: The expected output relies on the specific logic in implementation.
                # If implementation differs slightly (e.g. 15 days -> 0.5 months), this test might need adjustment based on verified implementation.
                # Assuming the prompt's expected output matches the implementation logic.
                self.assertEqual(self.extractor.extract_timeline(text), expected)

    def test_3_3_certification_extraction(self):
        """Verify Certification Extraction"""
        cases = [
            ("ISO 27001 required", "ISO 27001"),
            ("PCI-DSS certified", "PCI-DSS"),
            ("HIPAA compliant", "HIPAA"),
            ("GDPR ready", "GDPR"),
            ("no certification", None)
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(self.extractor.extract_certification(text), expected)

    def test_3_4_technology_extraction(self):
        """Verify Technology Extraction"""
        cases = [
            ("Python experience required", "Python"),
            ("AWS cloud platform", "AWS"),
            ("PostgreSQL database", "PostgreSQL"),
            ("LangChain framework", "LangChain"),
            ("no technology", None)
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(self.extractor.extract_technology(text), expected)

    def test_3_5_extract_all(self):
        """Verify Extract All"""
        text = "Budget is $150,000. Need SOC 2. Start in 3 months. Use Python."
        result = self.extractor.extract_all(text)
        
        self.assertEqual(result.get("budget"), "150000")
        self.assertEqual(result.get("timeline"), "3 months")
        self.assertIn("SOC 2", result.get("certification")) # Returns string
        self.assertIn("Python", result.get("technology"))   # Returns string

if __name__ == "__main__":
    print("Value Extractor Test Results:")
    unittest.main(verbosity=2)
