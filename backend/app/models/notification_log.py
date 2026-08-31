from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, BigInteger, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from typing import Optional
from datetime import datetime, timezone
import uuid

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # EMAIL, TELEGRAM, WEBHOOK
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # DOWN, RECOVERY, TEST, WARNING
    
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="SENT", nullable=False)  # SENT, FAILED, SKIPPED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    incident = relationship("Incident", backref="notification_logs")
    device = relationship("Device", backref="notification_logs")

    __table_args__ = (
        Index("ix_notification_logs_channel_event", "channel", "event_type"),
    )
