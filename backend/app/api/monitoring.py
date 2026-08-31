from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
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
    limit: int = Query(default=100, ge=1, le=50000),
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

@router.get("/{device_id}/latency-history", response_model=DeviceLatencyHistory)
async def get_device_latency_history(
    device_id: UUID,
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get latency history with server-side time-bucket aggregation.
    - 1h: raw data (~240 points at 15s intervals)
    - 24h:5-min buckets (~288 points)
    - 7d: 1-hour buckets (~168 points)
    """
    device_res = await db.execute(select(Device).where(Device.id == device_id))
    device = device_res.scalars().first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Choose bucket size based on time range
    if hours <= 1:
        # Raw data — no aggregation
        query = (
            select(
                MonitoringResult.checked_at.label("ts"),
                MonitoringResult.latency,
                MonitoringResult.status,
            )
            .where(MonitoringResult.device_id == device_id)
            .where(MonitoringResult.checked_at >= since)
            .order_by(MonitoringResult.checked_at.asc())
        )
        result = await db.execute(query)
        rows = result.all()
        timestamps = [row.ts for row in rows]
        latencies = [row.latency for row in rows]
        statuses = [row.status for row in rows]
    else:
        # Aggregated — use date_trunc to bucket by 5min (24h) or 1h (7d)
        if hours <= 24:
            sql = text("""
                SELECT
                    date_trunc('hour', checked_at) +
                    (floor(extract(minute from checked_at) / 5) * 5) * interval '1 minute'
                        AS bucket,
                    ROUND(AVG(latency)::numeric, 2) AS avg_latency,
                    MODE() WITHIN GROUP (ORDER BY status) AS status
                FROM monitoring_results
                WHERE device_id = :device_id
                  AND checked_at >= :since
                GROUP BY bucket
                ORDER BY bucket ASC
            """)
        else:
            sql = text("""
                SELECT
                    date_trunc('hour', checked_at) AS bucket,
                    ROUND(AVG(latency)::numeric, 2) AS avg_latency,
                    MODE() WITHIN GROUP (ORDER BY status) AS status
                FROM monitoring_results
                WHERE device_id = :device_id
                  AND checked_at >= :since
                GROUP BY bucket
                ORDER BY bucket ASC
            """)
        result = await db.execute(sql, {"device_id": str(device_id), "since": since})
        rows = result.all()
        timestamps = [row.bucket for row in rows]
        latencies = [float(row.avg_latency) if row.avg_latency is not None else None for row in rows]
        statuses = [row.status or "UNKNOWN" for row in rows]

    return DeviceLatencyHistory(
        timestamps=timestamps,
        latencies=latencies,
        statuses=statuses,
    )

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
