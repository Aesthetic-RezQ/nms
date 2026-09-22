"""Add raw individual ICMP timeout audit records.

Revision ID: 003
Revises: 002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("timeout_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "ping_timeout_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("probe_no", sa.Integer(), nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=False),
        sa.Column("reason_code", sa.String(length=24), nullable=False, server_default="TIMEOUT"),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ping_timeout_logs_device_timestamp", "ping_timeout_logs", ["device_id", "timestamp"])
    op.create_index("ix_ping_timeout_logs_timestamp", "ping_timeout_logs", ["timestamp"])
    op.create_index("ix_ping_timeout_logs_incident_id", "ping_timeout_logs", ["incident_id"])


def downgrade() -> None:
    op.drop_column("incidents", "timeout_count")
    op.drop_index("ix_ping_timeout_logs_incident_id", table_name="ping_timeout_logs")
    op.drop_index("ix_ping_timeout_logs_timestamp", table_name="ping_timeout_logs")
    op.drop_index("ix_ping_timeout_logs_device_timestamp", table_name="ping_timeout_logs")
    op.drop_table("ping_timeout_logs")
