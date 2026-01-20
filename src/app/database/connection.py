import time
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from loguru import logger
from config.settings import settings

# Validate DATABASE_URL
if not settings.DATABASE_URL:
    logger.error("DATABASE_URL is not set in settings")
    raise ValueError("DATABASE_URL must be set")

# Mask password for logging
masked_url = str(settings.DATABASE_URL)
if "@" in masked_url:
    prefix, suffix = masked_url.split("@")
    if ":" in prefix:
        start = prefix.split("://")[0] + "://"
        # simple masking
        masked_url = f"{start}****:****@{suffix}"
logger.info(f"Connecting to database at {masked_url}")

# Create engine with pool config
engine = create_engine(
    str(settings.DATABASE_URL),
    poolclass=QueuePool,
    pool_size=5,  # Max connections
    max_overflow=10,  # Extra connections when pool full
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Test connection before using
    echo=False  # Don't log all SQL (too verbose)
)

@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    logger.debug("Database connection established")

@event.listens_for(engine, "close")
def receive_close(dbapi_connection, connection_record):
    logger.debug("Database connection closed")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """Dependency for FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_connection(max_retries=3):
    """Test database connection with retry"""
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.warning(f"Connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                logger.error("All connection attempts failed")
                raise

def close_db():
    """Cleanup function for shutdown"""
    engine.dispose()
    logger.info("Database connections closed")
