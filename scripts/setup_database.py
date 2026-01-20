import sys
from pathlib import Path
from loguru import logger
from sqlalchemy import text

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.database.schema import Base
from src.app.database.connection import engine, test_connection

def setup_database():
    """Initialize the database schema and indexes with detailed logging"""
    try:
        # Test connection first
        test_connection()
        logger.info("Starting database setup")
        
        # Drop all existing tables
        logger.info("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped existing tables")

        # Create all tables
        logger.info("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Created all tables")

        # Create HNSW index for vector search
        logger.info("Creating HNSW index on project_portfolio.embedding...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_embedding_hnsw 
                ON project_portfolio 
                USING hnsw (embedding vector_cosine_ops);
            """))
            conn.commit()
        logger.info("Created HNSW index on project_portfolio.embedding")

        # Verify tables created
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result]
            logger.info(f"Created {len(tables)} tables")
            for table in tables:
                logger.info(f"  - {table}")

        # Verify indexes created
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname"
            ))
            indexes = [row[0] for row in result]
            logger.info(f"Created {len(indexes)} indexes")
            
        logger.success("✅ Database setup complete")
        logger.success(f"Tables: {len(tables)}")
        logger.success(f"Indexes: {len(indexes)}")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
