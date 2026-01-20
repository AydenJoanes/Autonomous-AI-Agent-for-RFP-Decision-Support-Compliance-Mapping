"""
Certification Repository - Database operations for certifications
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.app.database.repositories.base_repository import BaseRepository
from src.app.database.schema import Certification


class CertificationRepository(BaseRepository[Certification]):
    """Repository for certification operations."""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
    
    def get_all(self) -> List[dict]:
        """
        Get all certifications.
        
        Returns:
            List of all certifications
        """
        query = "SELECT * FROM certifications ORDER BY name"
        return self.fetch_all(query)
    
    def get_by_name(self, cert_name: str) -> Optional[dict]:
        """
        Get a certification by name.
        
        Args:
            cert_name: Certification name
            
        Returns:
            Certification data or None
        """
        query = """
            SELECT * FROM certifications 
            WHERE LOWER(name) = LOWER(:cert_name)
        """
        return self.fetch_one(query, {"cert_name": cert_name})
    
    def get_active_certs(self) -> List[dict]:
        """
        Get all active (non-expired) certifications.
        
        Returns:
            List of active certifications
        """
        query = """
            SELECT * FROM certifications 
            WHERE status = 'active' 
            AND (valid_until IS NULL OR valid_until >= CURRENT_DATE)
            ORDER BY name
        """
        return self.fetch_all(query)
    
    def add_certification(self, cert_data: dict) -> dict:
        """
        Add a new certification.
        
        Args:
            cert_data: Dictionary with certification fields
            
        Returns:
            Created certification data
        """
        columns = ", ".join(cert_data.keys())
        placeholders = ", ".join([f":{k}" for k in cert_data.keys()])
        
        query = f"""
            INSERT INTO certifications ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        result = self.fetch_one(query, cert_data)
        self.commit()
        return result
    
    def get_by_status(self, status: str) -> List[dict]:
        """
        Get certifications by status.
        
        Args:
            status: 'active', 'expired', 'pending', 'ready'
            
        Returns:
            List of certifications with the specified status
        """
        query = """
            SELECT * FROM certifications 
            WHERE LOWER(status) = LOWER(:status)
            ORDER BY name
        """
        return self.fetch_all(query, {"status": status})
    
    def get_expiring_soon(self, days: int = 90) -> List[dict]:
        """
        Get certifications expiring within the specified days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of certifications expiring soon
        """
        query = """
            SELECT * FROM certifications 
            WHERE status = 'active'
            AND valid_until IS NOT NULL
            AND valid_until <= CURRENT_DATE + :days
            ORDER BY valid_until
        """
        return self.fetch_all(query, {"days": days})
