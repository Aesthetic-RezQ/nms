from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class GroupRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    device_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
