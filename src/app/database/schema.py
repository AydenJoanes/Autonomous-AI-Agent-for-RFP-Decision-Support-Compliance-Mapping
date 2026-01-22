import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class CompanyProfile(Base):
    __tablename__ = 'company_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    overview = Column(Text, nullable=False)
    years_of_experience = Column(Integer)
    team_size = Column(Integer)
    delivery_regions = Column(ARRAY(String))
    budget_capacity_min = Column(Integer)
    budget_capacity_max = Column(Integer)
    industries_served = Column(ARRAY(String))
    core_services = Column(ARRAY(String))
    created_at = Column(DateTime, default=func.now())

class Certification(Base):
    __tablename__ = 'certifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    status = Column(String(50), nullable=False)
    valid_from = Column(Date)
    valid_until = Column(Date)
    scope = Column(Text)
    issuing_body = Column(String(200))
    created_at = Column(DateTime, default=func.now())

class TechStack(Base):
    __tablename__ = 'tech_stacks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    technology = Column(String(100), nullable=False, unique=True)
    proficiency = Column(String(50), nullable=False)
    years_experience = Column(Integer)
    team_size = Column(Integer)
    last_used = Column(Date)
    created_at = Column(DateTime, default=func.now())

class StrategicPreference(Base):
    __tablename__ = 'strategic_preferences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    preference_type = Column(String(100), nullable=False)
    value = Column(String(200), nullable=False)
    priority = Column(Integer, CheckConstraint('priority >= 1 AND priority <= 10'))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())

class ProjectPortfolio(Base):
    __tablename__ = 'project_portfolio'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    industry = Column(String(100), nullable=False)
    technologies = Column(ARRAY(String))
    budget = Column(Integer, nullable=False)
    duration_months = Column(Integer, nullable=False)
    outcome = Column(String(50), CheckConstraint("outcome IN ('success', 'partial_success', 'failure')"))
    description = Column(Text, nullable=False)
    year = Column(Integer)
    client_sector = Column(String(50))
    team_size = Column(Integer)
    embedding = Column(Vector(1536))  # pgvector type - OpenAI text-embedding-3-small
    created_at = Column(DateTime, default=func.now())
    
    # Indexes will be defined in the setup script or via explicit Index constructs if needed,
    # but HNSW index on embedding is often best done via DDL in setup script as in the plan.
    # Standard indexes can be defined here if desired, but user plan separates them mostly.
    # The user asked to "Define indexes" in the list, so I will add __table_args__ for standard ones
    # but leave HNSW for the script or DDL as it's cleaner for vector ops often.
    # Actually, user checklist says "Index: idx_project_embedding HNSW on embedding" in the define schema section.
    # SQLAlchemy can define this but it requires correct dialect imports. 
    # For now I will focus on standard columns and let setup script handle complex index creation as per plan
    # "Create HNSW index for vector search: Execute raw SQL".

class RFPUpload(Base):
    __tablename__ = 'rfp_uploads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rfp_id = Column(String(100), nullable=False, unique=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=func.now())
    status = Column(String(50), default='uploaded')
    parsed_markdown = Column(Text, nullable=True)
    parsed_at = Column(DateTime, nullable=True)
    parser_used = Column(String(50), nullable=True)

class Analysis(Base):
    __tablename__ = 'analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(100), nullable=False, unique=True)
    rfp_id = Column(String(100), ForeignKey('rfp_uploads.rfp_id'), nullable=False)
    status = Column(String(50), default='pending')
    progress = Column(Integer, default=0)
    current_step = Column(String(200))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

class Recommendation(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(100), ForeignKey('analyses.analysis_id'), nullable=True)
    decision = Column(String(20), nullable=False)
    confidence_score = Column(Integer, CheckConstraint('confidence_score >= 0 AND confidence_score <= 100'))
    justification = Column(Text, nullable=False)
    risks = Column(JSON)
    requirements_met = Column(Integer)
    requirements_failed = Column(Integer)
    clarification_questions = Column(JSON)
    escalation_needed = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    reasoning_steps = Column(JSON)
    
    # Phase 6: Memory & Feedback Extensions
    outcome_status = Column(String(50), nullable=True)  # WON, LOST, NO_BID_CONFIRMED, UNKNOWN
    outcome_recorded_at = Column(DateTime, nullable=True)
    outcome_notes = Column(Text, nullable=True)
    reflection_notes = Column(JSON, nullable=True)
    calibration_metrics = Column(JSON, nullable=True)
    embedding = Column(Vector(1536), nullable=True)

    created_at = Column(DateTime, default=func.now())
