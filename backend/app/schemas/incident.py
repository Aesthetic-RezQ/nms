from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class IncidentRead(BaseModel):
    id: UUID
    device_id: UUID
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    location_name: Optional[str] = None
    category_name: Optional[str] = None
    
    status: str
    detected_at: datetime
    down_since: datetime
    recovered_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    duration_formatted: Optional[str] = None
    
    failure_reason: Optional[str] = None
    notification_status: str
    is_acknowledged: bool
    acknowledged_by_id: Optional[UUID] = None
    acknowledged_by_name: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IncidentAcknowledgeRequest(BaseModel):
    notes: Optional[str] = Field(default=None, description="Optional notes regarding the acknowledgement")

class IncidentNoteRequest(BaseModel):
    notes: str = Field(..., min_length=1, description="Troubleshooting note to add/update")

class IncidentListFilter(BaseModel):
    status: Optional[str] = None           # OPEN, ACKNOWLEDGED, RESOLVED
    device_id: Optional[UUID] = None
    is_acknowledged: Optional[bool] = None
    search: Optional[str] = None
