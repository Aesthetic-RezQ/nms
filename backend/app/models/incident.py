from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin
from typing import Optional
from datetime import datetime
import uuid

class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False, index=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    down_since: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notification_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    device = relationship("Device", backref="incidents")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])

    __table_args__ = (
        Index("ix_incidents_device_status", "device_id", "status"),
    )
