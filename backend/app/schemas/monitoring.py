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

class DeviceUptimeHistory(BaseModel):
    timestamps: List[datetime]
    uptimes: List[float]

class DeviceMetricsSummary(BaseModel):
    current_status: str
    current_latency: Optional[float] = None
    last_check: Optional[datetime] = None
    availability_24h: float = 100.0
    avg_latency_24h: Optional[float] = None
    min_latency_24h: Optional[float] = None
    max_latency_24h: Optional[float] = None


class PingTimeoutRead(BaseModel):
    id: int
    device_id: UUID
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    probe_no: int
    timeout_ms: int
    reason_code: str
    incident_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
