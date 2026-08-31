from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.incident import IncidentRead
from app.schemas.device import DeviceRead

class DeviceStatusCounts(BaseModel):
    total: int = 0
    up: int = 0
    down: int = 0
    warning: int = 0
    unknown: int = 0
    maintenance: int = 0

class WorkerStatus(BaseModel):
    is_active: bool = True
    last_check_time: Optional[datetime] = None
    stale_seconds: Optional[int] = None
    is_stale: bool = False
    status_message: str = "Monitoring worker operational"

class DashboardSummaryResponse(BaseModel):
    status_counts: DeviceStatusCounts
    worker_status: WorkerStatus
    overall_availability_24h: float = 100.0
    recent_incidents: List[IncidentRead] = []
    recent_devices: List[DeviceRead] = []
