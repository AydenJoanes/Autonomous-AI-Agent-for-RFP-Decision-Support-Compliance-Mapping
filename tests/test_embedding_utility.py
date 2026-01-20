"""
Test script for Embedding Utility
"""
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.utils.embeddings import generate_embedding, generate_batch_embeddings, EMBEDDING_DIMENSION

def test_single_embedding():
    logger.info("Testing single embedding generation...")
    text = "Artificial Intelligence usage in RFP analysis"
    try:
        embedding = generate_embedding(text)
        assert len(embedding) == EMBEDDING_DIMENSION
        logger.success("Single embedding test passed matches dimension " + str(EMBEDDING_DIMENSION))
    except Exception as e:
        logger.error(f"Single embedding test failed: {e}")

def test_batch_embedding():
    logger.info("Testing batch embedding generation...")
    texts = [f"This is test sentence {i}" for i in range(105)] # 105 to test batching > 100
    try:
        embeddings = generate_batch_embeddings(texts)
        assert len(embeddings) == 105
        assert len(embeddings[0]) == EMBEDDING_DIMENSION
        logger.success("Batch embedding test passed (processed 105 items)")
    except Exception as e:
        logger.error(f"Batch embedding test failed: {e}")

if __name__ == "__main__":
    logger.info("Starting Embedding Utility Verification")
    test_single_embedding()
    test_batch_embedding()
