
import sys
from pathlib import Path
from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.app.database.connection import SessionLocal

def clear_kb():
    db = SessionLocal()
    try:
        logger.info("Clearing Knowledge Base tables...")
        # Order matters due to foreign keys if any, but these seem independent usually
        # using CASCADE to be safe
        tables = [
            "project_portfolio",
            "strategic_preferences",
            "tech_stacks",
            "certifications",
            "company_profiles"
        ]
        
        for table in tables:
            try:
                db.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
                logger.info(f"Table {table} truncated.")
            except Exception as e:
                # Fallback to delete if truncate fails (e.g. permission)
                logger.warning(f"Truncate failed for {table}, trying DELETE: {e}")
                db.execute(text(f"DELETE FROM {table};"))
                logger.info(f"Table {table} cleared via DELETE.")
        
        db.commit()
        logger.success("Knowledge Base cleared.")
    except Exception as e:
        logger.error(f"Failed to clear KB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_kb()
