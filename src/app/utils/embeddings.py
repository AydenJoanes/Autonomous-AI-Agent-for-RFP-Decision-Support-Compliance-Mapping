"""
Embeddings Utility - Generate text embeddings using SentenceTransformers
"""

from typing import List, Optional
from loguru import logger

# Singleton pattern for model caching
_model_instance = None


def get_embedding_model():
    """
    Get or create the embedding model instance (singleton pattern).
    Uses all-MiniLM-L6-v2 which produces 384-dimensional embeddings.
    
    Returns:
        SentenceTransformer model instance
    """
    global _model_instance
    
    if _model_instance is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2...")
        try:
            from sentence_transformers import SentenceTransformer
            _model_instance = SentenceTransformer('all-MiniLM-L6-v2')
            logger.success("Embedding model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    return _model_instance


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector from text.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding (384 dimensions)
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding, returning zeros")
        return [0.0] * 384
    
    model = get_embedding_model()
    
    try:
        logger.debug(f"Generating embedding for text: {text[:50]}...")
        embedding = model.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()
        logger.debug(f"Generated embedding with {len(embedding_list)} dimensions")
        return embedding_list
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.
    
    Args:
        texts: List of input texts
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    model = get_embedding_model()
    
    try:
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        embeddings_list = [emb.tolist() for emb in embeddings]
        logger.success(f"Generated {len(embeddings_list)} embeddings")
        return embeddings_list
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        raise
