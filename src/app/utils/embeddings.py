"""
Embeddings Utility - Generate text embeddings using OpenAI
"""

import time
import math
from typing import List
from loguru import logger

from config.settings import settings

# Constants
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 100

# Singleton pattern for OpenAI client caching
_client_instance = None


def get_openai_client():
    """
    Get or create the OpenAI client instance (singleton pattern).
    
    Returns:
        OpenAI client instance
    """
    global _client_instance
    
    if _client_instance is None:
        try:
            from openai import OpenAI
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                logger.warning("OpenAI API Key is missing in settings")
            
            _client_instance = OpenAI(api_key=api_key)
            logger.info(f"Embedding utility initialized with {EMBEDDING_MODEL}")
        except ImportError:
            logger.error("openai not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    return _client_instance


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector from text using OpenAI.
    Uses 'text-embedding-3-small' model.
    Produces 1536-dimensional embeddings.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding (1536 dimensions)
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding, returning zeros")
        return [0.0] * EMBEDDING_DIMENSION
    
    client = get_openai_client()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Validate dimension
            if len(embedding) != EMBEDDING_DIMENSION:
                logger.error(f"Dimension mismatch: expected {EMBEDDING_DIMENSION}, got {len(embedding)}")
                raise ValueError(f"Invalid embedding dimension: {len(embedding)}")
            
            logger.debug(f"Generated embedding for {len(text)} chars")
            return embedding
            
        except Exception as e:
            logger.warning(f"Embedding generation failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"All retry attempts failed for text: {text[:50]}...")
                raise e
            
            # Exponential backoff: 1s, 2s, 4s
            sleep_time = 2 ** attempt
            time.sleep(sleep_time)


def generate_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently using OpenAI batch API.
    Handles batching automatically (max 100 texts per call).
    
    Args:
        texts: List of input texts
        
    Returns:
        List of embedding vectors (each 1536 dimensions) in the same order
    """
    if not texts:
        return []
    
    # Filter valid texts to save tokens, but keep index alignment
    # Actually, simpler to embed all, replacing empty strings with placeholder if needed
    # But for strict batching, we usually just pass them through. 
    # OpenAI handles empty strings by erroring usually, so let's replace empty with space/placeholder
    # OR just process normally and catch errors? 
    # The requirement says "Handle batching if > 100 texts".
    
    sanitized_texts = [t if t and t.strip() else " " for t in texts]
    all_embeddings = []
    
    client = get_openai_client()
    total_texts = len(sanitized_texts)
    
    for i in range(0, total_texts, BATCH_SIZE):
        batch = sanitized_texts[i : i + BATCH_SIZE]
        logger.debug(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} texts)")
        
        try:
            # We wrap batch call in a retry too just in case
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
        except Exception as e:
            logger.error(f"Batch embedding failed for range {i}-{i+len(batch)}: {e}")
            # If a batch fails, we could retry or just raise. 
            # For simplicity in this utility, we raise to ensure data consistency
            raise
            
    return all_embeddings
