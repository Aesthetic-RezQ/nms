from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin
from typing import Optional
from datetime import datetime
import uuid

class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("device_groups.id"), nullable=True, index=True)
    location_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    
    vlan_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vlan_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subnet: Mapped[Optional[str]] = mapped_column(String(18), nullable=True)
    
    parent_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    monitoring_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ping_timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    failure_threshold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recovery_threshold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    current_status: Mapped[str] = mapped_column(String(20), default="UNKNOWN", index=True)
    
    last_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_up: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_down: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    current_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    category = relationship("Category", back_populates="devices", passive_deletes=True)
    group = relationship("DeviceGroup", back_populates="devices", passive_deletes=True)
    location = relationship("Location", back_populates="devices", passive_deletes=True)
    
    parent_device = relationship("Device", remote_side=[id], back_populates="children", passive_deletes=True)
    children = relationship("Device", back_populates="parent_device", passive_deletes=True)
