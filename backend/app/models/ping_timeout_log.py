from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from app.models.base import Base, TimestampMixin


class PingTimeoutLog(Base, TimestampMixin):
    """Raw evidence for an individual missed ICMP probe."""

    __tablename__ = "ping_timeout_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    probe_no: Mapped[int] = mapped_column(Integer, nullable=False)
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(24), nullable=False, default="TIMEOUT")
    incident_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )

    device = relationship("Device", backref=backref("ping_timeout_logs", passive_deletes=True))
    incident = relationship("Incident", backref="ping_timeout_logs")

    __table_args__ = (
        Index("ix_ping_timeout_logs_device_timestamp", "device_id", "timestamp"),
        Index("ix_ping_timeout_logs_timestamp", "timestamp"),
        Index("ix_ping_timeout_logs_incident_id", "incident_id"),
    )
