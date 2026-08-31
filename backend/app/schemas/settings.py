from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SettingRead(BaseModel):
    id: int
    key: str
    value: Optional[str]
    data_type: str
    description: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True

class SettingUpdate(BaseModel):
    key: str
    value: str

class SettingBulkUpdate(BaseModel):
    settings: List[SettingUpdate]
