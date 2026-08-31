from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None

class LocationRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    device_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
