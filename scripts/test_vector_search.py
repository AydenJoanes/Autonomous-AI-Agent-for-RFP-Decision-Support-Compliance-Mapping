"""
Test Vector Search - Verify pgvector similarity search works correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from config.settings import settings
from src.app.database.connection import SessionLocal, test_connection
from src.app.database.repositories.project_repository import ProjectRepository
from src.app.utils.embeddings import generate_embedding


def test_vector_search():
    """Test vector similarity search with sample queries."""
    
    logger.info("=" * 60)
    logger.info("VECTOR SEARCH TEST")
    logger.info("=" * 60)
    
    # Test database connection
    logger.info("Testing database connection...")
    test_connection()
    
    # Create session and repository
    db = SessionLocal()
    project_repo = ProjectRepository(db)
    
    # Test queries
    test_queries = [
        "healthcare AI project",
        "financial fraud detection machine learning",
        "government public sector automation",
        "retail e-commerce platform"
    ]
    
    try:
        for query in test_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"Query: '{query}'")
            logger.info("=" * 60)
            
            # Generate embedding for the query
            logger.info("Generating embedding...")
            embedding = generate_embedding(query)
            logger.info(f"Embedding dimensions: {len(embedding)}")
            
            # Search for similar projects
            logger.info("Searching for similar projects...")
            results = project_repo.search_similar(embedding, limit=5)
            
            if results:
                logger.success(f"Found {len(results)} similar projects:\n")
                for i, project in enumerate(results, 1):
                    distance = project.get('distance', 'N/A')
                    # Lower distance = more similar (cosine distance)
                    similarity = 1 - float(distance) if distance != 'N/A' else 'N/A'
                    
                    print(f"  {i}. {project['name'][:50]}")
                    print(f"     Industry: {project['industry']}")
                    print(f"     Distance: {distance:.4f}" if isinstance(distance, float) else f"     Distance: {distance}")
                    print(f"     Similarity: {similarity:.2%}" if isinstance(similarity, float) else f"     Similarity: {similarity}")
                    print()
            else:
                logger.warning("No results found!")
        
        logger.info("=" * 60)
        logger.success("VECTOR SEARCH TEST COMPLETED!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_vector_search()
