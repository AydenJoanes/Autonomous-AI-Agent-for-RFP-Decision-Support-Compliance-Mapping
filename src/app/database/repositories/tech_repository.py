"""
Tech Repository - Database operations for technology stack
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.app.database.repositories.base_repository import BaseRepository
from src.app.database.schema import TechStack


class TechRepository(BaseRepository[TechStack]):
    """Repository for technology stack operations."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
    
    def get_all(self) -> List[dict]:
        """
        Get all technologies.
        
        Returns:
            List of all technologies
        """
        query = "SELECT * FROM tech_stacks ORDER BY technology"
        return self.fetch_all(query)
    
    def get_by_name(self, tech_name: str) -> Optional[dict]:
        """
        Get a technology by name.
        
        Args:
            tech_name: Technology name
            
        Returns:
            Technology data or None
        """
        query = """
            SELECT * FROM tech_stacks 
            WHERE LOWER(technology) = LOWER(:tech_name)
        """
        return self.fetch_one(query, {"tech_name": tech_name})
    
    def search_technology(self, search_term: str) -> List[dict]:
        """
        Search technologies by partial name match.
        
        Args:
            search_term: Search term to match against technology names
            
        Returns:
            List of matching technologies
        """
        query = """
            SELECT * FROM tech_stacks 
            WHERE LOWER(technology) LIKE LOWER(:search_term)
            ORDER BY technology
        """
        return self.fetch_all(query, {"search_term": f"%{search_term}%"})
    
    def add_technology(self, tech_data: dict) -> dict:
        """
        Add a new technology.
        
        Args:
            tech_data: Dictionary with technology fields
            
        Returns:
            Created technology data
        """
        columns = ", ".join(tech_data.keys())
        placeholders = ", ".join([f":{k}" for k in tech_data.keys()])
        
        query = f"""
            INSERT INTO tech_stacks ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        result = self.fetch_one(query, tech_data)
        self.commit()
        return result
    
    def get_by_proficiency(self, proficiency: str) -> List[dict]:
        """
        Get technologies by proficiency level.
        
        Args:
            proficiency: 'expert', 'advanced', 'intermediate', 'beginner'
            
        Returns:
            List of technologies with the specified proficiency
        """
        query = """
            SELECT * FROM tech_stacks 
            WHERE LOWER(proficiency) = LOWER(:proficiency)
            ORDER BY technology
        """
        return self.fetch_all(query, {"proficiency": proficiency})
    
    def get_expert_technologies(self) -> List[dict]:
        """
        Get all technologies with expert proficiency.
        
        Returns:
            List of expert-level technologies
        """
        return self.get_by_proficiency("expert")
    
    def update_proficiency(self, tech_name: str, proficiency: str) -> Optional[dict]:
        """
        Update the proficiency level of a technology.
        
        Args:
            tech_name: Technology name
            proficiency: New proficiency level
            
        Returns:
            Updated technology data or None
        """
        query = """
            UPDATE tech_stacks 
            SET proficiency = :proficiency
            WHERE LOWER(technology) = LOWER(:tech_name)
            RETURNING *
        """
        result = self.fetch_one(query, {"tech_name": tech_name, "proficiency": proficiency})
        self.commit()
        return result
