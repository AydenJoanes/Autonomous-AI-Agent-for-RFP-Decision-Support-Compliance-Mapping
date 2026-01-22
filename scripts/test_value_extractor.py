"""
Phase 5 Test: Value Extractor
Tests extraction of budget, timeline, certification, technology.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from src.app.services.value_extractor import ValueExtractor


class TestValueExtractor(unittest.TestCase):
    """Test suite for ValueExtractor."""

    @classmethod
    def setUpClass(cls):
        cls.extractor = ValueExtractor()

    # Budget Tests
    def test_01_budget_dollar_format(self):
        """Extract $150,000 format."""
        result = self.extractor.extract_budget("Budget is $150,000")
        self.assertEqual(result, "150000")

    def test_02_budget_dollar_with_cents(self):
        """Extract $1,500,000.00 format."""
        result = self.extractor.extract_budget("Cost: $1,500,000.00")
        self.assertEqual(result, "1500000")

    def test_03_budget_k_format(self):
        """Extract 150k format."""
        result = self.extractor.extract_budget("Budget 150k")
        self.assertEqual(result, "150000")

    def test_04_budget_m_format(self):
        """Extract 1.5M format."""
        result = self.extractor.extract_budget("Budget 1.5M")
        self.assertEqual(result, "1500000")

    def test_05_budget_usd_format(self):
        """Extract 150000 USD format."""
        result = self.extractor.extract_budget("150000 USD budget")
        self.assertEqual(result, "150000")

    def test_06_budget_not_found(self):
        """Return None when no budget found."""
        result = self.extractor.extract_budget("No budget mentioned here")
        self.assertIsNone(result)

    # Timeline Tests
    def test_07_timeline_months(self):
        """Extract 4 months."""
        result = self.extractor.extract_timeline("Complete in 4 months")
        self.assertEqual(result, "4 months")

    def test_08_timeline_weeks(self):
        """Convert 16 weeks to months."""
        result = self.extractor.extract_timeline("Deliver in 16 weeks")
        self.assertEqual(result, "3 months")

    def test_09_timeline_days(self):
        """Convert 90 days to months."""
        result = self.extractor.extract_timeline("Due in 90 days")
        self.assertEqual(result, "3 months")

    def test_10_timeline_years(self):
        """Convert 2 years to months."""
        result = self.extractor.extract_timeline("2 years contract")
        self.assertEqual(result, "24 months")

    def test_11_timeline_minimum_one_month(self):
        """15 days converts to minimum 1 month."""
        result = self.extractor.extract_timeline("Complete in 15 days")
        self.assertEqual(result, "1 months")

    def test_12_timeline_not_found(self):
        """Return None when no timeline found."""
        result = self.extractor.extract_timeline("No timeline here")
        self.assertIsNone(result)

    # Certification Tests
    def test_13_certification_iso(self):
        """Extract ISO 27001."""
        result = self.extractor.extract_certification("Must have ISO 27001")
        self.assertIn("ISO", result)
        self.assertIn("27001", result)

    def test_14_certification_soc(self):
        """Extract SOC 2."""
        result = self.extractor.extract_certification("SOC 2 Type II required")
        self.assertIn("SOC", result)

    def test_15_certification_pci(self):
        """Extract PCI-DSS."""
        result = self.extractor.extract_certification("PCI-DSS certified")
        self.assertEqual(result, "PCI-DSS")

    def test_16_certification_hipaa(self):
        """Extract HIPAA."""
        result = self.extractor.extract_certification("HIPAA compliant")
        self.assertEqual(result, "HIPAA")

    def test_17_certification_gdpr(self):
        """Extract GDPR."""
        result = self.extractor.extract_certification("GDPR ready")
        self.assertEqual(result, "GDPR")

    def test_18_certification_not_found(self):
        """Return None when no certification found."""
        result = self.extractor.extract_certification("No certification")
        self.assertIsNone(result)

    # Technology Tests
    def test_19_technology_python(self):
        """Extract Python."""
        result = self.extractor.extract_technology("Python experience required")
        self.assertEqual(result, "Python")

    def test_20_technology_aws(self):
        """Extract AWS."""
        result = self.extractor.extract_technology("AWS cloud platform")
        self.assertEqual(result, "AWS")

    def test_21_technology_postgresql(self):
        """Extract PostgreSQL."""
        result = self.extractor.extract_technology("PostgreSQL database")
        self.assertEqual(result, "PostgreSQL")

    def test_22_technology_not_found(self):
        """Return None when no technology found."""
        result = self.extractor.extract_technology("No technology mentioned")
        self.assertIsNone(result)

    # Extract All Test
    def test_23_extract_all_complete(self):
        """Extract all returns dict with all keys."""
        text = "Budget $150,000. SOC 2. Python. 3 months timeline."
        result = self.extractor.extract_all(text)
        
        self.assertIn("budget", result)
        self.assertIn("timeline", result)
        self.assertIn("certification", result)
        self.assertIn("technology", result)
        self.assertEqual(result["budget"], "150000")
        self.assertEqual(result["timeline"], "3 months")
        self.assertEqual(result["technology"], "Python")


def run_tests():
    """Run tests and save output."""
    output_dir = Path("data/test_output/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"test_extractor_{timestamp}.log"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestValueExtractor)
        result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print("VALUE EXTRACTOR TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Log saved: {log_file}")
    print(f"{'='*60}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
