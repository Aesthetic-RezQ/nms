import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.incident import Incident
from monitoring.notifications import WorkerNotifier
from monitoring.dependency import DependencyResolver

logger = logging.getLogger("nms.worker.incident_manager")

class IncidentManager:
    @staticmethod
    async def handle_down_event(
        db: AsyncSession,
        device_id: UUID,
        device_name: str,
        first_failure_at: Optional[datetime] = None,
        failure_reason: str = "Consecutive ICMP check failures",
        device_dict: Optional[dict] = None
    ) -> Optional[Incident]:
        """
        Handle a device transitioning to DOWN state:
        Ensure an active incident is created if not already present.
        Apply alert suppression if parent is down (PRD §24).
        Send DOWN notification (Anti-spam: only once per incident).
        """
        try:
            # Check for existing active incident
            query = select(Incident).where(
                and_(
                    Incident.device_id == device_id,
                    Incident.status.in_(["OPEN", "ACKNOWLEDGED"])
                )
            )
            res = await db.execute(query)
            existing = res.scalars().first()
            if existing:
                logger.debug(f"Incident already active for device {device_name} (ID: {existing.id}) - Alert suppressed by anti-spam")
                return existing

            now = datetime.now(timezone.utc)
            down_since_time = first_failure_at or now

            incident = Incident(
                device_id=device_id,
                status="OPEN",
                detected_at=now,
                down_since=down_since_time,
                failure_reason=failure_reason,
                notification_status="PENDING",
                is_acknowledged=False
            )
            db.add(incident)
            await db.commit()
            await db.refresh(incident)

            logger.info(
                f"🚨 [INCIDENT OPENED] Device: {device_name} | Down Since: {down_since_time.strftime('%Y-%m-%d %H:%M:%S UTC')} | Incident ID: {incident.id}"
            )

            dev_data = device_dict or {"id": device_id, "device_name": device_name}
            inc_data = {
                "id": incident.id,
                "down_since": down_since_time,
                "failure_reason": failure_reason
            }

            # Check if parent device is DOWN -> suppress alert (PRD §24)
            is_suppressed = await DependencyResolver.apply_alert_suppression_if_needed(db, dev_data, incident)
            if not is_suppressed:
                incident.notification_status = "SENT"
                await db.commit()
                await WorkerNotifier.trigger_down_notification(db, dev_data, inc_data)

            return incident

        except Exception as e:
            logger.error(f"Failed to create incident for device {device_name}: {e}")
            return None

    @staticmethod
    async def handle_recovery_event(
        db: AsyncSession,
        device_id: UUID,
        device_name: str,
        device_dict: Optional[dict] = None
    ) -> Optional[Incident]:
        """
        Handle a device recovering to UP state:
        Resolve any active incident and calculate total downtime duration.
        Send RECOVERY notification.
        """
        try:
            query = select(Incident).where(
                and_(
                    Incident.device_id == device_id,
                    Incident.status.in_(["OPEN", "ACKNOWLEDGED"])
                )
            )
            res = await db.execute(query)
            active_incidents = res.scalars().all()

            if not active_incidents:
                logger.debug(f"No active incidents to resolve for recovered device {device_name}")
                return None

            now = datetime.now(timezone.utc)
            resolved_incident = None

            for inc in active_incidents:
                inc.status = "RESOLVED"
                inc.recovered_at = now
                
                # Calculate downtime duration in seconds
                if inc.down_since:
                    down_dt = inc.down_since if inc.down_since.tzinfo else inc.down_since.replace(tzinfo=timezone.utc)
                    duration = int((now - down_dt).total_seconds())
                    inc.duration_seconds = max(0, duration)
                
                resolved_incident = inc
                logger.info(
                    f"✅ [INCIDENT RESOLVED] Device: {device_name} | Downtime: {inc.duration_seconds}s | Incident ID: {inc.id}"
                )

                # Trigger RECOVERY notification only if original alert was not suppressed by dependency
                if inc.notification_status != "SUPPRESSED_BY_DEPENDENCY":
                    dev_data = device_dict or {"id": device_id, "device_name": device_name}
                    inc_data = {
                        "id": inc.id,
                        "recovered_at": now,
                        "duration_seconds": inc.duration_seconds
                    }
                    await WorkerNotifier.trigger_recovery_notification(db, dev_data, inc_data)

            await db.commit()
            return resolved_incident

        except Exception as e:
            logger.error(f"Failed to resolve incident for device {device_name}: {e}")
            return None
