from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, Boolean
from app.models.base import Base, TimestampMixin
from typing import Optional

class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Criticality & monitoring policy (Change2.md: NON-CRITICAL Workstation support)
    criticality: Mapped[str] = mapped_column(String(20), default="CRITICAL", nullable=False)
    incident_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sla_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    devices = relationship("Device", back_populates="category")
