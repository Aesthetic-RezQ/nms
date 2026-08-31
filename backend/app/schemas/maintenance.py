from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class MaintenanceWindowCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_active: bool = True
    device_ids: List[UUID] = Field(default=[], description="List of device UUIDs under this maintenance window")

class MaintenanceWindowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    device_ids: Optional[List[UUID]] = None

class MaintenanceWindowRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_active: bool
    is_currently_active: bool = False
    device_ids: List[UUID] = []
    device_names: List[str] = []
    devices_count: int = 0
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
