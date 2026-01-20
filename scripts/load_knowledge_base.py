"""
Knowledge Base Loader - Load JSON data into PostgreSQL database
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.app.database.connection import SessionLocal, test_connection
from src.app.database.schema import (
    CompanyProfile, 
    Certification, 
    TechStack, 
    StrategicPreference, 
    ProjectPortfolio
)
from src.app.utils.embeddings import generate_embedding


def load_json_file(filepath: str) -> dict:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_company_profile(db, kb_path: Path) -> int:
    """Load company profile into database."""
    logger.info("Loading company profile...")
    
    filepath = kb_path / "company_profile.json"
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return 0
    
    data = load_json_file(filepath)
    
    # Handle team_size - could be int or dict
    team_size = data.get("team_size", 0)
    if isinstance(team_size, dict):
        team_size = team_size.get("total", 0)
    
    # Handle budget_capacity - could be dict with min/max or minimum_usd/maximum_usd
    budget = data.get("budget_capacity", {})
    if isinstance(budget, dict):
        budget_min = budget.get("min", budget.get("minimum_usd", 0))
        budget_max = budget.get("max", budget.get("maximum_usd", 0))
    else:
        budget_min = 0
        budget_max = 0
    
    # Handle core_services - could be list of strings or list of dicts
    core_services = data.get("core_services", [])
    if core_services and isinstance(core_services[0], dict):
        core_services = [s.get("name", "") for s in core_services]
    
    # Extract relevant fields
    profile = CompanyProfile(
        name=data.get("company_name", "Unknown"),
        overview=data.get("overview", ""),
        years_of_experience=data.get("years_of_experience", 0),
        team_size=team_size,
        delivery_regions=data.get("delivery_regions", []),
        budget_capacity_min=budget_min,
        budget_capacity_max=budget_max,
        industries_served=data.get("industries_served", []),
        core_services=core_services
    )
    
    db.add(profile)
    db.commit()
    logger.success("Company profile loaded")
    return 1


def load_certifications(db, kb_path: Path) -> int:
    """Load certifications into database."""
    logger.info("Loading certifications...")
    
    filepath = kb_path / "certifications.json"
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return 0
    
    data = load_json_file(filepath)
    certs = data.get("certifications", [])
    
    count = 0
    for cert_data in certs:
        cert = Certification(
            name=cert_data.get("name", ""),
            status=cert_data.get("status", "unknown"),
            valid_from=parse_date(cert_data.get("issue_date")),
            valid_until=parse_date(cert_data.get("valid_until")),
            scope=cert_data.get("scope", ""),
            issuing_body=cert_data.get("issuing_body", "")
        )
        db.add(cert)
        count += 1
    
    db.commit()
    logger.success(f"Loaded {count} certifications")
    return count


def load_tech_stack(db, kb_path: Path) -> int:
    """Load technology stack into database."""
    logger.info("Loading tech stack...")
    
    filepath = kb_path / "tech_stack.json"
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return 0
    
    data = load_json_file(filepath)
    
    count = 0
    # Handle different possible structures
    if "categories" in data:
        for category in data["categories"]:
            for tech in category.get("technologies", []):
                add_tech(db, tech)
                count += 1
    elif "technologies" in data:
        for tech in data["technologies"]:
            add_tech(db, tech)
            count += 1
    else:
        # Flat structure - iterate over all values that are lists
        for key, value in data.items():
            if isinstance(value, list):
                for tech in value:
                    if isinstance(tech, dict):
                        add_tech(db, tech)
                        count += 1
    
    db.commit()
    logger.success(f"Loaded {count} technologies")
    return count


def add_tech(db, tech_data: dict):
    """Add a single technology to the database."""
    tech = TechStack(
        technology=tech_data.get("name", tech_data.get("technology", "")),
        proficiency=tech_data.get("proficiency", "intermediate"),
        years_experience=tech_data.get("years_experience", tech_data.get("years", 0)),
        team_size=tech_data.get("team_size", 0)
    )
    db.add(tech)


def load_strategic_preferences(db, kb_path: Path) -> int:
    """Load strategic preferences into database."""
    logger.info("Loading strategic preferences...")
    
    filepath = kb_path / "strategic_preferences.json"
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return 0
    
    data = load_json_file(filepath)
    
    count = 0
    
    # Handle different preference types
    preference_mappings = [
        ("preferred_industries", "industry"),
        ("preferred_project_types", "project_type"),
        ("preferred_client_profiles", "client"),
        ("geographic_preferences", "geographic"),
        ("strategic_priorities", "priority")
    ]
    
    for json_key, pref_type in preference_mappings:
        items = data.get(json_key, [])
        if isinstance(items, list):
            for i, item in enumerate(items):
                if isinstance(item, dict):
                    value = item.get("name", item.get("type", str(item)))
                    priority = item.get("priority", 10 - i)
                    notes = item.get("notes", item.get("description", ""))
                else:
                    value = str(item)
                    priority = 10 - i
                    notes = ""
                
                pref = StrategicPreference(
                    preference_type=pref_type,
                    value=value,
                    priority=priority,
                    notes=notes
                )
                db.add(pref)
                count += 1
    
    db.commit()
    logger.success(f"Loaded {count} strategic preferences")
    return count


def load_project_portfolio(db, kb_path: Path) -> int:
    """Load project portfolio with embeddings into database."""
    logger.info("Loading project portfolio...")
    
    filepath = kb_path / "project_portfolio.json"
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return 0
    
    data = load_json_file(filepath)
    projects = data.get("projects", [])
    
    count = 0
    for i, proj_data in enumerate(projects):
        logger.info(f"Processing project {i+1}/{len(projects)}: {proj_data.get('name', 'Unknown')[:30]}...")
        
        # Generate embedding from description
        description = proj_data.get("description", "")
        embedding = None
        if description:
            try:
                embedding = generate_embedding(description)
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")
        
        # Parse outcome
        outcome = proj_data.get("outcome", "success")
        if isinstance(outcome, dict):
            outcome = outcome.get("status", "success")
        if outcome not in ["success", "partial_success", "failure"]:
            outcome = "success"
        
        project = ProjectPortfolio(
            name=proj_data.get("name", f"Project {i+1}"),
            industry=proj_data.get("industry", proj_data.get("client_industry", "Technology")),
            technologies=proj_data.get("technologies_used", proj_data.get("technologies", [])),
            budget=parse_budget(proj_data.get("budget", proj_data.get("budget_usd", 0))),
            duration_months=proj_data.get("duration_months", proj_data.get("duration", 6)),
            outcome=outcome,
            description=description,
            year=proj_data.get("year", 2024),
            client_sector=proj_data.get("client_sector", "private"),
            team_size=proj_data.get("team_size", 5),
            embedding=embedding
        )
        
        db.add(project)
        count += 1
    
    db.commit()
    logger.success(f"Loaded {count} projects with embeddings")
    return count


def parse_date(date_str: str) -> datetime:
    """Parse a date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None


def parse_budget(budget) -> int:
    """Parse budget to integer."""
    if isinstance(budget, int):
        return budget
    if isinstance(budget, str):
        # Remove currency symbols and commas
        cleaned = budget.replace("$", "").replace(",", "").replace("USD", "").strip()
        try:
            return int(float(cleaned))
        except:
            return 0
    return 0


def main():
    """Main function to load all knowledge base data."""
    logger.info("=" * 60)
    logger.info("KNOWLEDGE BASE LOADER")
    logger.info("=" * 60)
    
    # Test database connection
    logger.info("Testing database connection...")
    test_connection()
    
    # Get knowledge base path
    kb_path = Path(settings.KNOWLEDGE_BASE_PATH)
    if not kb_path.exists():
        logger.error(f"Knowledge base path not found: {kb_path}")
        sys.exit(1)
    
    logger.info(f"Loading from: {kb_path.absolute()}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Load all data
        company_count = load_company_profile(db, kb_path)
        cert_count = load_certifications(db, kb_path)
        tech_count = load_tech_stack(db, kb_path)
        pref_count = load_strategic_preferences(db, kb_path)
        project_count = load_project_portfolio(db, kb_path)
        
        # Print summary
        logger.info("=" * 60)
        logger.success("LOADING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"  📊 Company Profiles: {company_count}")
        logger.info(f"  📜 Certifications:   {cert_count}")
        logger.info(f"  💻 Technologies:     {tech_count}")
        logger.info(f"  🎯 Preferences:      {pref_count}")
        logger.info(f"  📁 Projects:         {project_count}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Loading failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
