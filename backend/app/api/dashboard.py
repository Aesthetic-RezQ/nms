from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime, timezone, timedelta
import asyncio
import json
import logging
import uuid
from typing import List, Set

from app.database import get_db, async_session_maker
from app.models.device import Device
from app.models.incident import Incident
from app.models.monitoring_result import MonitoringResult
from app.schemas.dashboard import DashboardSummaryResponse, DeviceStatusCounts, WorkerStatus
from app.services.incident_service import IncidentService
from app.services.device_service import DeviceService
from app.api.deps import get_current_user

logger = logging.getLogger("nms.api.dashboard")
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

async def get_dashboard_summary_data(db: AsyncSession) -> dict:
    # 1. Device Counts
    status_counts_res = await db.execute(
        select(
            func.count(Device.id).label("total"),
            func.count(Device.id).filter(Device.current_status == "UP").label("up"),
            func.count(Device.id).filter(Device.current_status == "DOWN").label("down"),
            func.count(Device.id).filter(Device.current_status == "WARNING").label("warning"),
            func.count(Device.id).filter(Device.current_status == "UNKNOWN").label("unknown"),
            func.count(Device.id).filter(Device.current_status == "MAINTENANCE").label("maintenance"),
            func.max(Device.last_check).label("latest_check")
        )
    )
    counts_row = status_counts_res.first()
    
    total = counts_row.total if counts_row else 0
    up = counts_row.up if counts_row else 0
    down = counts_row.down if counts_row else 0
    warning = counts_row.warning if counts_row else 0
    unknown = counts_row.unknown if counts_row else 0
    maintenance = counts_row.maintenance if counts_row else 0
    latest_check = counts_row.latest_check if counts_row else None

    # 2. Worker health & stale detection (PRD §46)
    now = datetime.now(timezone.utc)
    is_stale = False
    stale_sec = None
    status_msg = "Monitoring engine active"

    if latest_check:
        latest_dt = latest_check if latest_check.tzinfo else latest_check.replace(tzinfo=timezone.utc)
        stale_sec = int((now - latest_dt).total_seconds())
        # If enabled devices exist and last check was > 60 seconds ago
        if total > 0 and stale_sec > 60:
            is_stale = True
            status_msg = f"MONITORING DATA STALE - Last check was {stale_sec}s ago"
    elif total > 0:
        is_stale = True
        status_msg = "MONITORING ENGINE OFFLINE - No checks recorded yet"

    # 3. Overall 24h network availability
    since = now - timedelta(hours=24)
    avail_res = await db.execute(
        select(
            func.count(MonitoringResult.id).label("total_checks"),
            func.count(MonitoringResult.id).filter(MonitoringResult.status == "UP").label("up_checks")
        ).where(MonitoringResult.checked_at >= since)
    )
    avail_row = avail_res.first()
    tot_chk = avail_row.total_checks if avail_row else 0
    up_chk = avail_row.up_checks if avail_row else 0
    overall_avail = (up_chk / tot_chk * 100.0) if tot_chk > 0 else (100.0 if total > 0 and down == 0 else 0.0)

    # 4. Recent Incidents
    incidents_dict = await IncidentService.get_all(db=db, page=1, page_size=5)
    recent_incidents = incidents_dict["data"]

    # 5. Recent Devices
    devices_dict = await DeviceService.get_all(db=db, page=1, page_size=10)
    recent_devices = devices_dict["data"]

    return {
        "status_counts": {
            "total": total,
            "up": up,
            "down": down,
            "warning": warning,
            "unknown": unknown,
            "maintenance": maintenance
        },
        "worker_status": {
            "is_active": not is_stale,
            "last_check_time": latest_check,
            "stale_seconds": stale_sec,
            "is_stale": is_stale,
            "status_message": status_msg
        },
        "overall_availability_24h": round(overall_avail, 2),
        "recent_incidents": recent_incidents,
        "recent_devices": recent_devices
    }

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Fetch aggregated live dashboard summary, counts, worker health, and recent items."""
    return await get_dashboard_summary_data(db)

# WebSocket Connection Manager
class DashboardConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, data: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception:
                self.active_connections.discard(connection)

ws_manager = DashboardConnectionManager()

@router.websocket("/ws")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard status streaming.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Poll DB and stream summary every 3 seconds
            async with async_session_maker() as db:
                data = await get_dashboard_summary_data(db)
                # Convert datetimes and UUIDs to JSON-safe strings
                def serialize_dt(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    if isinstance(obj, uuid.UUID):
                        return str(obj)
                    raise TypeError(f"Type {type(obj)} not serializable")

                await websocket.send_text(json.dumps(data, default=serialize_dt))
            await asyncio.sleep(3.0)
    except (WebSocketDisconnect, asyncio.CancelledError):
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
