from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from uuid import UUID
from datetime import datetime, timezone
import math
from typing import Optional, Dict, Any

from app.models.incident import Incident
from app.models.device import Device
from app.models.category import Category
from app.models.location import Location
from app.models.user import User
from app.schemas.incident import IncidentListFilter
from app.core.exceptions import NotFoundException, ValidationException
from app.services.audit_service import AuditService

def format_duration(seconds: Optional[int]) -> Optional[str]:
    if seconds is None:
        return None
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {rem_seconds}s" if rem_seconds > 0 else f"{minutes}m"
    hours = minutes // 60
    rem_minutes = minutes % 60
    if hours < 24:
        return f"{hours}h {rem_minutes}m"
    days = hours // 24
    rem_hours = hours % 24
    return f"{days}d {rem_hours}h"

class IncidentService:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 25,
        filters: Optional[IncidentListFilter] = None
    ) -> Dict[str, Any]:
        query = select(
            Incident,
            Device.device_name.label("device_name"),
            Device.ip_address.label("ip_address"),
            Location.name.label("location_name"),
            Category.name.label("category_name"),
            User.full_name.label("acknowledged_by_name")
        ).join(Device, Incident.device_id == Device.id)\
         .outerjoin(Location, Device.location_id == Location.id)\
         .outerjoin(Category, Device.category_id == Category.id)\
         .outerjoin(User, Incident.acknowledged_by_id == User.id)

        count_query = select(func.count(Incident.id)).join(Device, Incident.device_id == Device.id)

        if filters:
            if filters.status:
                query = query.where(Incident.status == filters.status)
                count_query = count_query.where(Incident.status == filters.status)
            if filters.device_id:
                query = query.where(Incident.device_id == filters.device_id)
                count_query = count_query.where(Incident.device_id == filters.device_id)
            if filters.is_acknowledged is not None:
                query = query.where(Incident.is_acknowledged == filters.is_acknowledged)
                count_query = count_query.where(Incident.is_acknowledged == filters.is_acknowledged)
            if filters.search:
                term = f"%{filters.search}%"
                query = query.where(or_(
                    Device.device_name.ilike(term),
                    Device.ip_address.ilike(term),
                    Incident.failure_reason.ilike(term)
                ))
                count_query = count_query.where(or_(
                    Device.device_name.ilike(term),
                    Device.ip_address.ilike(term),
                    Incident.failure_reason.ilike(term)
                ))

        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        query = query.order_by(desc(Incident.detected_at)).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)

        data = []
        for row in result.all():
            inc = row.Incident
            data.append({
                "id": inc.id,
                "device_id": inc.device_id,
                "device_name": row.device_name,
                "ip_address": row.ip_address,
                "location_name": row.location_name,
                "category_name": row.category_name,
                "status": inc.status,
                "detected_at": inc.detected_at,
                "down_since": inc.down_since,
                "recovered_at": inc.recovered_at,
                "duration_seconds": inc.duration_seconds,
                "duration_formatted": format_duration(inc.duration_seconds),
                "failure_reason": inc.failure_reason,
                "notification_status": inc.notification_status,
                "is_acknowledged": inc.is_acknowledged,
                "acknowledged_by_id": inc.acknowledged_by_id,
                "acknowledged_by_name": row.acknowledged_by_name,
                "acknowledged_at": inc.acknowledged_at,
                "notes": inc.notes,
                "created_at": inc.created_at,
                "updated_at": inc.updated_at
            })

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, incident_id: UUID) -> Dict[str, Any]:
        query = select(
            Incident,
            Device.device_name.label("device_name"),
            Device.ip_address.label("ip_address"),
            Location.name.label("location_name"),
            Category.name.label("category_name"),
            User.full_name.label("acknowledged_by_name")
        ).join(Device, Incident.device_id == Device.id)\
         .outerjoin(Location, Device.location_id == Location.id)\
         .outerjoin(Category, Device.category_id == Category.id)\
         .outerjoin(User, Incident.acknowledged_by_id == User.id)\
         .where(Incident.id == incident_id)

        res = await db.execute(query)
        row = res.first()
        if not row:
            raise NotFoundException("Incident not found")

        inc = row.Incident
        return {
            "id": inc.id,
            "device_id": inc.device_id,
            "device_name": row.device_name,
            "ip_address": row.ip_address,
            "location_name": row.location_name,
            "category_name": row.category_name,
            "status": inc.status,
            "detected_at": inc.detected_at,
            "down_since": inc.down_since,
            "recovered_at": inc.recovered_at,
            "duration_seconds": inc.duration_seconds,
            "duration_formatted": format_duration(inc.duration_seconds),
            "failure_reason": inc.failure_reason,
            "notification_status": inc.notification_status,
            "is_acknowledged": inc.is_acknowledged,
            "acknowledged_by_id": inc.acknowledged_by_id,
            "acknowledged_by_name": row.acknowledged_by_name,
            "acknowledged_at": inc.acknowledged_at,
            "notes": inc.notes,
            "created_at": inc.created_at,
            "updated_at": inc.updated_at
        }

    @staticmethod
    async def acknowledge(
        db: AsyncSession,
        incident_id: UUID,
        user_id: UUID,
        username: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        res = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = res.scalars().first()
        if not incident:
            raise NotFoundException("Incident not found")

        if incident.status == "RESOLVED":
            raise ValidationException("Cannot acknowledge a resolved incident")

        now = datetime.now(timezone.utc)
        incident.is_acknowledged = True
        incident.acknowledged_by_id = user_id
        incident.acknowledged_at = now
        incident.status = "ACKNOWLEDGED"
        
        if notes:
            if incident.notes:
                incident.notes += f"\n[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] {username}: {notes}"
            else:
                incident.notes = f"[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] {username}: {notes}"

        await db.commit()
        await AuditService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            action="INCIDENT_ACKNOWLEDGED",
            object_type="incident",
            object_id=str(incident_id),
            new_value={"status": "ACKNOWLEDGED", "acknowledged_by": username}
        )

        return await IncidentService.get_by_id(db, incident_id)

    @staticmethod
    async def add_note(
        db: AsyncSession,
        incident_id: UUID,
        user_id: UUID,
        username: str,
        notes: str
    ) -> Dict[str, Any]:
        res = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = res.scalars().first()
        if not incident:
            raise NotFoundException("Incident not found")

        now = datetime.now(timezone.utc)
        formatted_note = f"[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] {username}: {notes}"
        if incident.notes:
            incident.notes += f"\n{formatted_note}"
        else:
            incident.notes = formatted_note

        await db.commit()
        return await IncidentService.get_by_id(db, incident_id)
