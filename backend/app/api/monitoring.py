from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.device import Device
from app.models.monitoring_result import MonitoringResult
from app.schemas.monitoring import MonitoringResultRead, DeviceMetricsSummary, DeviceLatencyHistory
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/devices", tags=["Device Monitoring History"])

@router.get("/{device_id}/history", response_model=List[MonitoringResultRead])
async def get_device_history(
    device_id: UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    hours: Optional[int] = Query(default=None, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get historical monitoring results for a specific device."""
    device_res = await db.execute(select(Device).where(Device.id == device_id))
    device = device_res.scalars().first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        
    query = select(MonitoringResult).where(MonitoringResult.device_id == device_id)
    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = query.where(MonitoringResult.checked_at >= since)
        
    query = query.order_by(desc(MonitoringResult.checked_at)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{device_id}/metrics", response_model=DeviceMetricsSummary)
async def get_device_metrics(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get calculated metrics and 24h availability for a device."""
    device_res = await db.execute(select(Device).where(Device.id == device_id))
    device = device_res.scalars().first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # Calculate stats from last 24h
    stats_query = select(
        func.count(MonitoringResult.id).label("total_checks"),
        func.count(MonitoringResult.id).filter(MonitoringResult.status == "UP").label("up_checks"),
        func.avg(MonitoringResult.latency).filter(MonitoringResult.is_successful == True).label("avg_latency"),
        func.min(MonitoringResult.latency).filter(MonitoringResult.is_successful == True).label("min_latency"),
        func.max(MonitoringResult.latency).filter(MonitoringResult.is_successful == True).label("max_latency"),
    ).where(
        MonitoringResult.device_id == device_id,
        MonitoringResult.checked_at >= since
    )
    
    stats_res = await db.execute(stats_query)
    row = stats_res.first()

    total_checks = row.total_checks if row else 0
    up_checks = row.up_checks if row else 0
    availability = (up_checks / total_checks * 100.0) if total_checks > 0 else (100.0 if device.current_status == "UP" else 0.0)

    return DeviceMetricsSummary(
        current_status=device.current_status,
        current_latency=device.current_latency,
        last_check=device.last_check,
        availability_24h=round(availability, 2),
        avg_latency_24h=round(row.avg_latency, 2) if row and row.avg_latency is not None else None,
        min_latency_24h=round(row.min_latency, 2) if row and row.min_latency is not None else None,
        max_latency_24h=round(row.max_latency, 2) if row and row.max_latency is not None else None,
    )
