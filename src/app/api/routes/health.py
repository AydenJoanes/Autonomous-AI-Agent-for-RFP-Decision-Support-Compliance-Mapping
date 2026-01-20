"""
Health Check Endpoint
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

from config.settings import settings


router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Status, version, and timestamp information.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENV,
        "service": "RFP Bid Decision Agent"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with component status.
    
    Returns:
        Detailed status of all components.
    """
    components = {
        "api": {"status": "healthy"},
        "config": {"status": "healthy", "log_level": settings.LOG_LEVEL},
        "knowledge_base": {"status": "healthy", "path": settings.KNOWLEDGE_BASE_PATH}
    }
    
    try:
        # Test database connection
        from src.app.database.connection import test_connection
        if test_connection(max_retries=1):
            components["database"] = {"status": "healthy"}
        else:
             components["database"] = {"status": "unhealthy", "error": "Connection failed"}
    except Exception as e:
        components["database"] = {"status": "unhealthy", "error": str(e)}
    
    all_healthy = all(c["status"] == "healthy" for c in components.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENV,
        "components": components
    }
