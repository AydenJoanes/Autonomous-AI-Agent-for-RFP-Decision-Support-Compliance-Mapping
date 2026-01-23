"""
LLM Client Utility
Centralized client for LLM API calls with retry logic, token counting, and error handling.
"""

import json
import time
from typing import Dict, Any, Optional, List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from openai import OpenAI, OpenAIError, APITimeoutError, RateLimitError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. LLM features will be disabled.")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not installed. Token counting will be approximate.")


class LLMClient:
    """Centralized LLM client with retry logic and cost tracking."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (if None, will try settings.OPENAI_API_KEY, then env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai tiktoken")
        
        # Priority: explicit param > settings > environment
        if not api_key:
            try:
                from config.settings import settings
                api_key = settings.OPENAI_API_KEY
            except (ImportError, AttributeError):
                api_key = None  # Will let OpenAI() try env var
        
        self.client = OpenAI(api_key=api_key)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0
        
        # Cost per 1M tokens (as of Jan 2026)
        self.cost_per_million = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        }
    
    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            model: Model name for encoding
            
        Returns:
            Token count
        """
        if not TIKTOKEN_AVAILABLE:
            return len(text) // 4  # Rough estimation
            
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")
        
        return len(encoding.encode(text))
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Extract base model name (handle versioned models)
        base_model = model.split("-")[0:2]  # e.g., "gpt-4o" from "gpt-4o-2024-08-06"
        base_model = "-".join(base_model)
        
        if base_model not in self.cost_per_million:
            logger.warning(f"Unknown model {model}, using gpt-4o pricing")
            base_model = "gpt-4o"
        
        costs = self.cost_per_million[base_model]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        
        return input_cost + output_cost
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        reraise=True
    )
    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Call LLM with retry logic.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            model: Model name
            temperature: Temperature (0.0 = deterministic)
            max_tokens: Max tokens in response
            timeout: Timeout in seconds
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            LLM response text
            
        Raises:
            OpenAIError: On API error after retries
        """
        start_time = time.time()
        
        try:
            # Count input tokens
            input_tokens = self.count_tokens(system_prompt + user_prompt, model)
            
            # Build request
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "timeout": timeout
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            if response_format:
                kwargs["response_format"] = response_format
            
            # Make API call
            response = self.client.chat.completions.create(**kwargs)
            
            # Extract response
            content = response.choices[0].message.content
            
            # Track usage
            output_tokens = response.usage.completion_tokens
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.call_count += 1
            
            cost = self.estimate_cost(input_tokens, output_tokens, model)
            self.total_cost += cost
            
            elapsed = time.time() - start_time
            
            logger.info(
                f"LLM call completed | model={model} | "
                f"input_tokens={input_tokens} | output_tokens={output_tokens} | "
                f"cost=${cost:.4f} | latency={elapsed:.2f}s"
            )
            
            return content
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"LLM call failed after {elapsed:.2f}s: {e}")
            raise
    
    def call_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: int = 60
    ) -> Any:
        """
        Call LLM and parse JSON response.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            model: Model name
            temperature: Temperature
            max_tokens: Max tokens
            timeout: Timeout in seconds
            
        Returns:
            Parsed JSON object (dict or list)
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
            OpenAIError: On API error
        """
        # Request JSON format
        response_format = {"type": "json_object"}
        
        # Ensure system prompt mentions JSON
        if "json" not in system_prompt.lower():
            system_prompt += "\n\nRespond with valid JSON only."
        
        response_text = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            response_format=response_format
        )
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        return {
            "total_calls": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "avg_cost_per_call": round(self.total_cost / max(self.call_count, 1), 4)
        }
    
    def reset_stats(self):
        """Reset usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0


# Global singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get global LLM client instance.
    
    Returns:
        LLM client singleton
    """
    global _llm_client
    
    if _llm_client is None:
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        _llm_client = LLMClient()
    
    return _llm_client
