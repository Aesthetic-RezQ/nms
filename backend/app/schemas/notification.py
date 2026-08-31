from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class NotificationLogRead(BaseModel):
    id: int
    incident_id: Optional[UUID] = None
    device_id: Optional[UUID] = None
    channel: str
    recipient: str
    event_type: str
    subject: Optional[str] = None
    message_body: str
    status: str
    error_message: Optional[str] = None
    sent_at: datetime

    class Config:
        from_attributes = True

class TestNotificationRequest(BaseModel):
    channel: str = Field(..., description="Notification channel to test: EMAIL or TELEGRAM")
    recipient: Optional[str] = Field(default=None, description="Target recipient email address or Telegram Chat ID override")
    custom_message: Optional[str] = Field(default=None, description="Optional custom test message")

class NotificationTestResponse(BaseModel):
    success: bool
    channel: str
    message: str
    recipient: str
