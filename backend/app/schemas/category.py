from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = 0
    criticality: Optional[str] = "CRITICAL"
    incident_enabled: Optional[bool] = True
    alert_enabled: Optional[bool] = True
    sla_enabled: Optional[bool] = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None
    criticality: Optional[str] = None
    incident_enabled: Optional[bool] = None
    alert_enabled: Optional[bool] = None
    sla_enabled: Optional[bool] = None

class CategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: int
    criticality: str = "CRITICAL"
    incident_enabled: bool = True
    alert_enabled: bool = True
    sla_enabled: bool = True
    device_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
