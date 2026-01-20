"""
Base Repository - Abstract base class for all repositories
"""

import time
from typing import Any, List, Optional, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository class providing common database operations.
    All repositories should extend this class.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize repository with database session.
        
        Args:
            db_session: SQLAlchemy session object
        """
        self.db = db_session
        self.logger = logger.bind(type="repository")
    
    def execute_query(self, query: str, params: Optional[dict] = None) -> Any:
        """
        Execute a raw SQL query with timing and logging.
        
        Args:
            query: SQL query string
            params: Optional dictionary of query parameters
            
        Returns:
            Query result
        """
        start_time = time.time()
        try:
            result = self.db.execute(text(query), params or {})
            execution_time = (time.time() - start_time) * 1000
            self.logger.debug(f"Query executed in {execution_time:.2f}ms: {query[:100]}...")
            return result
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise
    
    def fetch_one(self, query: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        Fetch a single row from a query.
        
        Args:
            query: SQL query string
            params: Optional dictionary of query parameters
            
        Returns:
            Single row as dictionary or None
        """
        result = self.execute_query(query, params)
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None
    
    def fetch_all(self, query: str, params: Optional[dict] = None) -> List[dict]:
        """
        Fetch all rows from a query.
        
        Args:
            query: SQL query string
            params: Optional dictionary of query parameters
            
        Returns:
            List of rows as dictionaries
        """
        result = self.execute_query(query, params)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    
    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.db.commit()
            self.logger.debug("Transaction committed")
        except Exception as e:
            self.logger.error(f"Commit failed: {e}")
            self.rollback()
            raise
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            self.db.rollback()
            self.logger.warning("Transaction rolled back")
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            raise
    
    def add(self, entity: T) -> T:
        """
        Add an entity to the session.
        
        Args:
            entity: SQLAlchemy model instance
            
        Returns:
            The added entity
        """
        self.db.add(entity)
        return entity
    
    def delete(self, entity: T) -> None:
        """
        Delete an entity from the session.
        
        Args:
            entity: SQLAlchemy model instance
        """
        self.db.delete(entity)
    
    def refresh(self, entity: T) -> T:
        """
        Refresh an entity from the database.
        
        Args:
            entity: SQLAlchemy model instance
            
        Returns:
            The refreshed entity
        """
        self.db.refresh(entity)
        return entity
