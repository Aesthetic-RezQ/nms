"""Add criticality and monitoring policy fields to categories table

Revision ID: 001
Revises: 
Create Date: 2026-08-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add criticality and monitoring policy fields to categories table
    op.add_column('categories', sa.Column('criticality', sa.String(20), nullable=False, server_default='CRITICAL'))
    op.add_column('categories', sa.Column('incident_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('categories', sa.Column('alert_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('categories', sa.Column('sla_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    
    # Update existing 'Workstation' category if present (for existing databases)
    op.execute(
        sa.text(
            "UPDATE categories SET "
            "criticality = 'NON_CRITICAL', "
            "incident_enabled = false, "
            "alert_enabled = false, "
            "sla_enabled = false "
            "WHERE name = 'Workstation'"
        )
    )


def downgrade() -> None:
    op.drop_column('categories', 'sla_enabled')
    op.drop_column('categories', 'alert_enabled')
    op.drop_column('categories', 'incident_enabled')
    op.drop_column('categories', 'criticality')
