"""
Strategic Preferences Repository - Database operations for strategic preferences
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.app.database.repositories.base_repository import BaseRepository
from src.app.database.schema import StrategicPreference


class StrategicPreferencesRepository(BaseRepository[StrategicPreference]):
    """Repository for strategic preferences operations."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
    
    def get_all(self) -> List[dict]:
        """
        Get all strategic preferences.
        
        Returns:
            List of all preferences
        """
        query = "SELECT * FROM strategic_preferences ORDER BY preference_type, priority"
        return self.fetch_all(query)
    
    def get_by_type(self, preference_type: str) -> List[dict]:
        """
        Get preferences by type.
        
        Args:
            preference_type: Type of preference (e.g., 'industry', 'project_type', 'geographic')
            
        Returns:
            List of preferences of the specified type
        """
        query = """
            SELECT * FROM strategic_preferences 
            WHERE LOWER(preference_type) = LOWER(:preference_type)
            ORDER BY priority
        """
        return self.fetch_all(query, {"preference_type": preference_type})
    
    def get_industry_priorities(self) -> List[dict]:
        """
        Get industry-related preferences ordered by priority.
        
        Returns:
            List of industry preferences
        """
        return self.get_by_type("industry")
    
    def add_preference(self, pref_data: dict) -> dict:
        """
        Add a new strategic preference.
        
        Args:
            pref_data: Dictionary with preference fields
            
        Returns:
            Created preference data
        """
        columns = ", ".join(pref_data.keys())
        placeholders = ", ".join([f":{k}" for k in pref_data.keys()])
        
        query = f"""
            INSERT INTO strategic_preferences ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        result = self.fetch_one(query, pref_data)
        self.commit()
        return result
    
    def get_high_priority(self, min_priority: int = 7) -> List[dict]:
        """
        Get high-priority preferences.
        
        Args:
            min_priority: Minimum priority level (1-10, higher is more important)
            
        Returns:
            List of high-priority preferences
        """
        query = """
            SELECT * FROM strategic_preferences 
            WHERE priority >= :min_priority
            ORDER BY priority DESC, preference_type
        """
        return self.fetch_all(query, {"min_priority": min_priority})
    
    def get_by_value(self, value: str) -> Optional[dict]:
        """
        Get a preference by its value.
        
        Args:
            value: Preference value to search for
            
        Returns:
            Preference data or None
        """
        query = """
            SELECT * FROM strategic_preferences 
            WHERE LOWER(value) = LOWER(:value)
        """
        return self.fetch_one(query, {"value": value})
    
    def update_priority(self, pref_id: int, new_priority: int) -> Optional[dict]:
        """
        Update the priority of a preference.
        
        Args:
            pref_id: Preference ID
            new_priority: New priority level (1-10)
            
        Returns:
            Updated preference data or None
        """
        query = """
            UPDATE strategic_preferences 
            SET priority = :new_priority
            WHERE id = :pref_id
            RETURNING *
        """
        result = self.fetch_one(query, {"pref_id": pref_id, "new_priority": new_priority})
        self.commit()
        return result
    
    def get_project_type_preferences(self) -> List[dict]:
        """
        Get project type preferences.
        
        Returns:
            List of project type preferences
        """
        return self.get_by_type("project_type")
    
    def get_client_preferences(self) -> List[dict]:
        """
        Get client-related preferences.
        
        Returns:
            List of client preferences
        """
        return self.get_by_type("client")
    
    def get_geographic_preferences(self) -> List[dict]:
        """
        Get geographic preferences.
        
        Returns:
            List of geographic preferences
        """
        return self.get_by_type("geographic")
