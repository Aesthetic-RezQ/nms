from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None

class CategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: int
    device_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
