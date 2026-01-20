"""
Project Repository - Database operations for project portfolio
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.app.database.repositories.base_repository import BaseRepository
from src.app.database.schema import ProjectPortfolio


class ProjectRepository(BaseRepository[ProjectPortfolio]):
    """Repository for project portfolio operations with vector search support."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
    
    def get_all(self) -> List[ProjectPortfolio]:
        """
        Get all projects.
        
        Returns:
            List of all projects
        """
        query = "SELECT * FROM project_portfolio ORDER BY created_at DESC"
        return self.fetch_all(query)
    
    def get_by_id(self, project_id: int) -> Optional[dict]:
        """
        Get a project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project data or None
        """
        query = "SELECT * FROM project_portfolio WHERE id = :project_id"
        return self.fetch_one(query, {"project_id": project_id})
    
    def search_similar(self, embedding: List[float], limit: int = 5) -> List[dict]:
        """
        Search for similar projects using vector similarity (pgvector).
        Uses cosine distance for similarity matching.
        
        Args:
            embedding: Query embedding vector (384 dimensions)
            limit: Maximum number of results
            
        Returns:
            List of similar projects ordered by similarity
        """
        # Convert embedding to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        query = """
            SELECT *, (embedding <=> :embedding::vector) as distance
            FROM project_portfolio 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """
        return self.fetch_all(query, {"embedding": embedding_str, "limit": limit})
    
    def add_project(self, project_data: dict) -> dict:
        """
        Add a new project to the portfolio.
        
        Args:
            project_data: Dictionary with project fields
            
        Returns:
            Created project data
        """
        columns = ", ".join(project_data.keys())
        placeholders = ", ".join([f":{k}" for k in project_data.keys()])
        
        query = f"""
            INSERT INTO project_portfolio ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        result = self.fetch_one(query, project_data)
        self.commit()
        return result
    
    def filter_by_industry(self, industry: str) -> List[dict]:
        """
        Filter projects by industry.
        
        Args:
            industry: Industry name to filter by
            
        Returns:
            List of projects in the specified industry
        """
        query = """
            SELECT * FROM project_portfolio 
            WHERE LOWER(industry) = LOWER(:industry)
            ORDER BY year DESC
        """
        return self.fetch_all(query, {"industry": industry})
    
    def filter_by_technologies(self, technologies: List[str]) -> List[dict]:
        """
        Filter projects that use any of the specified technologies.
        
        Args:
            technologies: List of technology names
            
        Returns:
            List of matching projects
        """
        query = """
            SELECT * FROM project_portfolio 
            WHERE technologies && :technologies
            ORDER BY year DESC
        """
        return self.fetch_all(query, {"technologies": technologies})
    
    def get_by_outcome(self, outcome: str) -> List[dict]:
        """
        Get projects by outcome status.
        
        Args:
            outcome: 'success', 'partial_success', or 'failure'
            
        Returns:
            List of projects with the specified outcome
        """
        query = """
            SELECT * FROM project_portfolio 
            WHERE outcome = :outcome
            ORDER BY year DESC
        """
        return self.fetch_all(query, {"outcome": outcome})
