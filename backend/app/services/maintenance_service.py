from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.models.maintenance import MaintenanceWindow, maintenance_devices
from app.models.device import Device
from app.models.user import User
from app.schemas.maintenance import MaintenanceWindowCreate, MaintenanceWindowUpdate
from app.core.exceptions import NotFoundException, ValidationException
from app.services.audit_service import AuditService

class MaintenanceService:
    @staticmethod
    async def get_all(db: AsyncSession) -> List[Dict[str, Any]]:
        query = select(MaintenanceWindow).options(
            selectinload(MaintenanceWindow.devices),
            selectinload(MaintenanceWindow.created_by)
        ).order_by(MaintenanceWindow.start_time.desc())

        res = await db.execute(query)
        windows = res.scalars().all()
        now = datetime.now(timezone.utc)

        result = []
        for w in windows:
            # Ensure timezone-aware comparison
            st = w.start_time if w.start_time.tzinfo else w.start_time.replace(tzinfo=timezone.utc)
            et = w.end_time if w.end_time.tzinfo else w.end_time.replace(tzinfo=timezone.utc)
            is_active_now = w.is_active and (st <= now <= et)

            result.append({
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "start_time": w.start_time,
                "end_time": w.end_time,
                "is_active": w.is_active,
                "is_currently_active": is_active_now,
                "device_ids": [d.id for d in w.devices],
                "device_names": [d.device_name for d in w.devices],
                "devices_count": len(w.devices),
                "created_by_name": w.created_by.full_name if w.created_by else None,
                "created_at": w.created_at,
                "updated_at": w.updated_at
            })
        return result

    @staticmethod
    async def get_by_id(db: AsyncSession, window_id: UUID) -> Dict[str, Any]:
        query = select(MaintenanceWindow).options(
            selectinload(MaintenanceWindow.devices),
            selectinload(MaintenanceWindow.created_by)
        ).where(MaintenanceWindow.id == window_id)

        res = await db.execute(query)
        w = res.scalars().first()
        if not w:
            raise NotFoundException("Maintenance window not found")

        now = datetime.now(timezone.utc)
        st = w.start_time if w.start_time.tzinfo else w.start_time.replace(tzinfo=timezone.utc)
        et = w.end_time if w.end_time.tzinfo else w.end_time.replace(tzinfo=timezone.utc)
        is_active_now = w.is_active and (st <= now <= et)

        return {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "start_time": w.start_time,
            "end_time": w.end_time,
            "is_active": w.is_active,
            "is_currently_active": is_active_now,
            "device_ids": [d.id for d in w.devices],
            "device_names": [d.device_name for d in w.devices],
            "devices_count": len(w.devices),
            "created_by_name": w.created_by.full_name if w.created_by else None,
            "created_at": w.created_at,
            "updated_at": w.updated_at
        }

    @staticmethod
    async def create(
        db: AsyncSession,
        data: MaintenanceWindowCreate,
        user_id: UUID,
        username: str
    ) -> Dict[str, Any]:
        if data.start_time >= data.end_time:
            raise ValidationException("End time must be after start time")

        # Fetch associated devices
        devices_list = []
        if data.device_ids:
            dev_res = await db.execute(select(Device).where(Device.id.in_(data.device_ids)))
            devices_list = dev_res.scalars().all()

        window = MaintenanceWindow(
            name=data.name,
            description=data.description,
            start_time=data.start_time,
            end_time=data.end_time,
            is_active=data.is_active,
            created_by_id=user_id,
            devices=devices_list
        )
        db.add(window)
        await db.commit()
        await db.refresh(window)

        await AuditService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            action="MAINTENANCE_CREATED",
            object_type="maintenance",
            object_id=str(window.id),
            new_value={"name": window.name, "device_count": len(devices_list)}
        )

        return await MaintenanceService.get_by_id(db, window.id)

    @staticmethod
    async def update(
        db: AsyncSession,
        window_id: UUID,
        data: MaintenanceWindowUpdate,
        user_id: UUID,
        username: str
    ) -> Dict[str, Any]:
        query = select(MaintenanceWindow).options(selectinload(MaintenanceWindow.devices)).where(MaintenanceWindow.id == window_id)
        res = await db.execute(query)
        window = res.scalars().first()
        if not window:
            raise NotFoundException("Maintenance window not found")

        if data.name is not None:
            window.name = data.name
        if data.description is not None:
            window.description = data.description
        if data.start_time is not None:
            window.start_time = data.start_time
        if data.end_time is not None:
            window.end_time = data.end_time
        if data.is_active is not None:
            window.is_active = data.is_active

        if window.start_time >= window.end_time:
            raise ValidationException("End time must be after start time")

        if data.device_ids is not None:
            dev_res = await db.execute(select(Device).where(Device.id.in_(data.device_ids)))
            window.devices = dev_res.scalars().all()

        await db.commit()
        await AuditService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            action="MAINTENANCE_UPDATED",
            object_type="maintenance",
            object_id=str(window.id),
            new_value={"name": window.name}
        )

        return await MaintenanceService.get_by_id(db, window_id)

    @staticmethod
    async def delete(
        db: AsyncSession,
        window_id: UUID,
        user_id: UUID,
        username: str
    ):
        query = select(MaintenanceWindow).where(MaintenanceWindow.id == window_id)
        res = await db.execute(query)
        window = res.scalars().first()
        if not window:
            raise NotFoundException("Maintenance window not found")

        name = window.name
        await db.delete(window)
        await db.commit()

        await AuditService.create_log(
            db=db,
            user_id=user_id,
            username=username,
            action="MAINTENANCE_DELETED",
            object_type="maintenance",
            object_id=str(window_id),
            old_value={"name": name}
        )

    @staticmethod
    async def get_active_maintenance_device_ids(db: AsyncSession) -> set[UUID]:
        """Returns set of device UUIDs that are currently under active maintenance."""
        now = datetime.now(timezone.utc)
        query = select(maintenance_devices.c.device_id).join(
            MaintenanceWindow, maintenance_devices.c.maintenance_id == MaintenanceWindow.id
        ).where(
            and_(
                MaintenanceWindow.is_active == True,
                MaintenanceWindow.start_time <= now,
                MaintenanceWindow.end_time >= now
            )
        )
        res = await db.execute(query)
        return set(res.scalars().all())
