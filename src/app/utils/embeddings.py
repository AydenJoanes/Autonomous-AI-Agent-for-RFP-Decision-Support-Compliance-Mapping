"""
Embeddings Utility - Generate text embeddings using OpenAI
"""

from typing import List
from loguru import logger

from config.settings import settings

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
        logger.info("Initializing OpenAI client...")
        try:
            from openai import OpenAI
            _client_instance = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.success("OpenAI client initialized successfully")
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
    Uses the model specified in settings (default: text-embedding-3-small).
    Produces 1536-dimensional embeddings.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding (1536 dimensions)
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding, returning zeros")
        return [0.0] * 1536
    
    client = get_openai_client()
    
    try:
        logger.debug(f"Generating OpenAI embedding for text: {text[:50]}...")
        
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently using OpenAI batch API.
    
    Args:
        texts: List of input texts
        
    Returns:
        List of embedding vectors (each 1536 dimensions)
    """
    if not texts:
        return []
    
    # Filter out empty texts
    valid_texts = [t for t in texts if t and t.strip()]
    if not valid_texts:
        return [[0.0] * 1536 for _ in texts]
    
    client = get_openai_client()
    
    try:
        logger.info(f"Generating OpenAI embeddings for {len(valid_texts)} texts...")
        
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=valid_texts
        )
        
        embeddings = [item.embedding for item in response.data]
        logger.success(f"Generated {len(embeddings)} embeddings")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        raise
