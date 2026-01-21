import sys
import os
import unittest
import time
from unittest.mock import MagicMock, call

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app.utils.retry import retry_with_backoff

class TestPhase5Retry(unittest.TestCase):

    def test_4_1_successful_first_attempt(self):
        """Verify successful first attempt"""
        mock_func = MagicMock(return_value="success")
        
        result = retry_with_backoff(mock_func)
            
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)

    def test_4_2_success_after_retries(self):
        """Verify success after retries"""
        # Fail twice, succeed third time
        mock_func = MagicMock(side_effect=[ValueError("Fail 1"), ValueError("Fail 2"), "success"])
        
        # Mock time.sleep to run fast
        with unittest.mock.patch('time.sleep') as mock_sleep:
            result = retry_with_backoff(mock_func, max_retries=3, base_delay=1)
            
            self.assertEqual(result, "success")
            self.assertEqual(mock_func.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 2)
            # Verify exponential backoff: 1s, 2s
            mock_sleep.assert_has_calls([call(1.0), call(2.0)])

    def test_4_3_all_retries_exhausted(self):
        """Verify all retries exhausted"""
        mock_func = MagicMock(side_effect=ValueError("Persistent Fail"))
        
        with unittest.mock.patch('time.sleep') as mock_sleep:
            with self.assertRaises(ValueError):
                retry_with_backoff(mock_func, max_retries=3)
                
            self.assertEqual(mock_func.call_count, 3) 

    def test_4_4_custom_parameters(self):
        """Verify custom parameters"""
        mock_func = MagicMock(side_effect=[KeyError("Fail"), "success"])
        
        with unittest.mock.patch('time.sleep') as mock_sleep:
            result = retry_with_backoff(mock_func, max_retries=5, base_delay=0.5, exceptions=(KeyError,))
            self.assertEqual(result, "success")
            mock_sleep.assert_called_with(0.5)

    def test_4_5_exponential_backoff_timing(self):
        """Verify backoff timing sequence"""
        # Fail 3 times, succeed 4th
        mock_func = MagicMock(side_effect=[Exception("E"), Exception("E"), Exception("E"), "success"])
        
        with unittest.mock.patch('time.sleep') as mock_sleep:
            retry_with_backoff(mock_func, max_retries=5, base_delay=1)
            
            # Expected delays: 1, 2, 4
            mock_sleep.assert_has_calls([call(1.0), call(2.0), call(4.0)])

if __name__ == "__main__":
    print("Retry Utility Test Results:")
    unittest.main(verbosity=2)
