from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, DateTime, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin
from typing import Optional, List
from datetime import datetime
import uuid

# Association table for MaintenanceWindow <-> Device many-to-many
maintenance_devices = Table(
    "maintenance_devices",
    Base.metadata,
    Column("maintenance_id", UUID(as_uuid=True), ForeignKey("maintenance_windows.id", ondelete="CASCADE"), primary_key=True),
    Column("device_id", UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
)

class MaintenanceWindow(Base, TimestampMixin):
    __tablename__ = "maintenance_windows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by = relationship("User")
    devices = relationship("Device", secondary=maintenance_devices, backref="maintenance_windows")
