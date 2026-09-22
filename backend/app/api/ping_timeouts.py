from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.device import Device
from app.models.ping_timeout_log import PingTimeoutLog
from app.schemas.common import PaginatedResponse
from app.schemas.monitoring import PingTimeoutRead

router = APIRouter(prefix="/api/ping-timeouts", tags=["Ping Timeout Audit"])
device_router = APIRouter(prefix="/api/devices", tags=["Ping Timeout Audit"])
incident_router = APIRouter(prefix="/api/incidents", tags=["Ping Timeout Audit"])


def _query_base():
    return select(
        PingTimeoutLog,
        Device.device_name.label("device_name"),
        Device.ip_address.label("ip_address"),
    ).join(Device, PingTimeoutLog.device_id == Device.id)


def _serialize(row):
    log = row.PingTimeoutLog
    return {
        "id": log.id,
        "device_id": log.device_id,
        "device_name": row.device_name,
        "ip_address": row.ip_address,
        "timestamp": log.timestamp,
        "probe_no": log.probe_no,
        "timeout_ms": log.timeout_ms,
        "reason_code": log.reason_code,
        "incident_id": log.incident_id,
        "created_at": log.created_at,
    }


async def _list_logs(
    db: AsyncSession,
    page: int,
    page_size: int,
    device_id: Optional[UUID] = None,
    device: Optional[str] = None,
    category_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    incident_id: Optional[UUID] = None,
    reason_code: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    filters = []
    if device_id:
        filters.append(PingTimeoutLog.device_id == device_id)
    if category_id:
        filters.append(Device.category_id == category_id)
    if device:
        term = f"%{device}%"
        filters.append(or_(Device.device_name.ilike(term), Device.ip_address.ilike(term)))
    if ip_address:
        filters.append(Device.ip_address.ilike(f"%{ip_address}%"))
    if incident_id:
        filters.append(PingTimeoutLog.incident_id == incident_id)
    if reason_code:
        filters.append(PingTimeoutLog.reason_code == reason_code.upper())
    if start_time:
        filters.append(PingTimeoutLog.timestamp >= start_time)
    if end_time:
        filters.append(PingTimeoutLog.timestamp <= end_time)

    count_query = select(func.count(PingTimeoutLog.id)).join(Device, PingTimeoutLog.device_id == Device.id)
    query = _query_base()
    if filters:
        count_query = count_query.where(*filters)
        query = query.where(*filters)

    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(
        query.order_by(desc(PingTimeoutLog.timestamp))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all()
    return {
        "data": [_serialize(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("", response_model=PaginatedResponse[PingTimeoutRead])
@router.get("/", response_model=PaginatedResponse[PingTimeoutRead], include_in_schema=False)
async def list_ping_timeouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    device_id: Optional[UUID] = None,
    device: Optional[str] = None,
    category_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    incident_id: Optional[UUID] = None,
    reason_code: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await _list_logs(db, page, page_size, device_id, device, category_id, ip_address, incident_id, reason_code, start_time, end_time)


@device_router.get("/{device_id}/ping-timeouts", response_model=PaginatedResponse[PingTimeoutRead])
async def list_device_ping_timeouts(
    device_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hours: Optional[int] = Query(None, ge=1, le=8760),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    if not (await db.execute(select(Device.id).where(Device.id == device_id))).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours) if hours else None
    return await _list_logs(db, page, page_size, device_id=device_id, start_time=start_time)


@device_router.get("/{device_id}/ping-timeouts/summary")
async def device_ping_timeout_summary(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    if not (await db.execute(select(Device.id).where(Device.id == device_id))).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    query = select(
        func.count(PingTimeoutLog.id).filter(PingTimeoutLog.timestamp >= day_ago).label("last_24h"),
        func.count(PingTimeoutLog.id).filter(PingTimeoutLog.timestamp >= week_ago).label("last_7d"),
        func.max(PingTimeoutLog.timestamp).label("last_timeout"),
    ).where(PingTimeoutLog.device_id == device_id)
    row = (await db.execute(query)).one()
    return {
        "timeouts_last_24h": row.last_24h or 0,
        "timeouts_last_7d": row.last_7d or 0,
        "last_timeout": row.last_timeout,
    }


@incident_router.get("/{incident_id}/ping-timeouts", response_model=PaginatedResponse[PingTimeoutRead])
async def list_incident_ping_timeouts(
    incident_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await _list_logs(db, page, page_size, incident_id=incident_id)
