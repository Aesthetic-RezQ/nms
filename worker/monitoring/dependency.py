import logging
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.device import Device
from app.models.incident import Incident

logger = logging.getLogger("nms.worker.dependency")

class DependencyResolver:
    @staticmethod
    async def is_parent_down(db: AsyncSession, parent_device_id: Optional[UUID]) -> bool:
        """
        Check if the immediate upstream parent device is currently DOWN.
        """
        if not parent_device_id:
            return False

        res = await db.execute(select(Device.current_status).where(Device.id == parent_device_id))
        parent_status = res.scalar_one_or_none()
        return parent_status == "DOWN"

    @staticmethod
    async def get_affected_downstream_devices(db: AsyncSession, parent_device_id: UUID) -> List[str]:
        """
        Get names of all direct downstream children of a parent device.
        """
        res = await db.execute(select(Device.device_name).where(Device.parent_device_id == parent_device_id))
        return list(res.scalars().all())

    @staticmethod
    async def apply_alert_suppression_if_needed(
        db: AsyncSession,
        device_dict: dict,
        incident: Incident
    ) -> bool:
        """
        If the parent device is confirmed DOWN, suppress the downstream child alert (PRD §24).
        Returns True if alert was suppressed, False if normal alert should proceed.
        """
        parent_id = device_dict.get("parent_device_id")
        if not parent_id:
            return False

        parent_down = await DependencyResolver.is_parent_down(db, parent_id)
        if parent_down:
            incident.notification_status = "SUPPRESSED_BY_DEPENDENCY"
            await db.commit()
            logger.info(
                f"🔕 [ALERT SUPPRESSED] Device: {device_dict.get('device_name')} DOWN alert suppressed because parent device is confirmed DOWN (PRD §24)"
            )
            return True

        return False
