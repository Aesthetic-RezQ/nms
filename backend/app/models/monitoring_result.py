from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy import String, Text, ForeignKey, Boolean, Float, DateTime, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from typing import Optional
from datetime import datetime, timezone
import uuid

class MonitoringResult(Base):
    __tablename__ = "monitoring_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # UP, DOWN, WARNING, UNKNOWN, MAINTENANCE
    latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in milliseconds (ms)
    packet_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in percentage (0-100)
    is_successful: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    device = relationship("Device", backref=backref("monitoring_results", passive_deletes=True))

    __table_args__ = (
        Index("ix_monitoring_results_device_checked", "device_id", "checked_at"),
    )
