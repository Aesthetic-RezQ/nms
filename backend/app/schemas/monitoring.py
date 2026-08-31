from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class MonitoringResultRead(BaseModel):
    id: int
    device_id: UUID
    checked_at: datetime
    status: str
    latency: Optional[float] = None
    packet_loss: Optional[float] = None
    is_successful: bool
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class DeviceLatencyHistory(BaseModel):
    timestamps: List[datetime]
    latencies: List[Optional[float]]
    statuses: List[str]

class DeviceMetricsSummary(BaseModel):
    current_status: str
    current_latency: Optional[float] = None
    last_check: Optional[datetime] = None
    availability_24h: float = 100.0
    avg_latency_24h: Optional[float] = None
    min_latency_24h: Optional[float] = None
    max_latency_24h: Optional[float] = None
