"""
Retry Utility
Provides retry logic with exponential backoff for external calls.
"""

import time
from typing import Callable, Tuple, Any
from loguru import logger


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple = (Exception,)
) -> Any:
    """
    Retry a function call with exponential backoff.
    
    Args:
        func: Callable to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Result of the successful function call
        
    Raises:
        The last exception if all retries fail
        
    Usage:
        result = retry_with_backoff(lambda: llm_call(), max_retries=3)
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            result = func()
            return result
        except exceptions as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt)
                logger.warning(f'[RETRY] Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...')
                time.sleep(delay)
            else:
                # Final attempt failed
                logger.error(f'[RETRY] Attempt {attempt + 1} failed: {e}. No more retries.')
    
    # All retries exhausted, raise the last exception
    raise last_exception
