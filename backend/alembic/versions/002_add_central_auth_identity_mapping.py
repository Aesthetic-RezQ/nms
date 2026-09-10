"""Add the immutable CentralAuth identity mapping to the NMS cache.

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("central_user_id", sa.String(length=36), nullable=True))
    op.create_index("ix_users_central_user_id", "users", ["central_user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_central_user_id", table_name="users")
    op.drop_column("users", "central_user_id")
