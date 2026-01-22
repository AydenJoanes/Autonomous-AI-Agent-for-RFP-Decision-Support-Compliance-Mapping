"""add phase6 columns

Revision ID: phase6_001
Revises: previous_revision_id
Create Date: 2026-01-22 11:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'phase6_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to recommendations table
    op.add_column('recommendations', sa.Column('outcome_status', sa.String(length=50), nullable=True))
    op.add_column('recommendations', sa.Column('outcome_recorded_at', sa.DateTime(), nullable=True))
    op.add_column('recommendations', sa.Column('outcome_notes', sa.Text(), nullable=True))
    op.add_column('recommendations', sa.Column('reflection_notes', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('recommendations', sa.Column('calibration_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    # Ensure pgvector extension exists before adding vector column
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.add_column('recommendations', sa.Column('embedding', Vector(1536), nullable=True))


def downgrade() -> None:
    # Remove columns from recommendations table
    op.drop_column('recommendations', 'embedding')
    op.drop_column('recommendations', 'calibration_metrics')
    op.drop_column('recommendations', 'reflection_notes')
    op.drop_column('recommendations', 'outcome_notes')
    op.drop_column('recommendations', 'outcome_recorded_at')
    op.drop_column('recommendations', 'outcome_status')
