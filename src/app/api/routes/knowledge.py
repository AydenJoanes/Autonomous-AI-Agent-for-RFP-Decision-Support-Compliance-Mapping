"""
Knowledge API Endpoints - Projects, Certifications, Technologies
"""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.app.database.connection import get_db
from src.app.database.repositories import (
    ProjectRepository,
    CertificationRepository,
    TechRepository,
)


router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])


# -----------------------------------------------------------------------------
# Projects Endpoint
# -----------------------------------------------------------------------------

@router.get("/projects", response_model=List[Dict[str, Any]])
async def get_projects(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    technology: Optional[str] = Query(None, description="Filter by technology"),
    limit: int = Query(10, ge=1, le=100, description="Max number of results"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get projects from the portfolio.

    - **industry**: Optional industry filter (e.g., Healthcare, Finance)
    - **technology**: Optional technology filter (e.g., Python, AWS)
    - **limit**: Maximum results to return (default 10)

    Returns a list of projects matching the filters.
    """
    repo = ProjectRepository(db)

    # Apply filters
    if industry:
        projects = repo.filter_by_industry(industry)
    elif technology:
        projects = repo.filter_by_technologies([technology])
    else:
        projects = repo.get_all()

    # Limit results
    return projects[:limit] if projects else []


# -----------------------------------------------------------------------------
# Certifications Endpoint
# -----------------------------------------------------------------------------

@router.get("/certifications", response_model=List[Dict[str, Any]])
async def get_certifications(
    active_only: bool = Query(False, description="Return only active non-expired certs"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get all certifications.

    - **active_only**: If true, returns only active non-expired certifications

    Returns a list of certifications.
    """
    repo = CertificationRepository(db)
    if active_only:
        return repo.get_active_certs()
    return repo.get_all()


# -----------------------------------------------------------------------------
# Technologies Endpoint
# -----------------------------------------------------------------------------

@router.get("/technologies", response_model=List[Dict[str, Any]])
async def get_technologies(
    proficiency: Optional[str] = Query(
        None,
        description="Filter by proficiency level (expert, advanced, intermediate, beginner)",
    ),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get all technologies with proficiency levels.

    - **proficiency**: Optional filter by proficiency level

    Returns a list of technologies in the tech stack.
    """
    repo = TechRepository(db)

    if proficiency:
        return repo.get_by_proficiency(proficiency)
    return repo.get_all()
