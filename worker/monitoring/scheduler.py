import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, update, insert, and_, text
import math

from monitoring.config import worker_settings
from monitoring.icmp import AsyncICMPEngine, PingResult
from monitoring.state_machine import DeviceStateMachine
from monitoring.incident_manager import IncidentManager
from monitoring.notifications import WorkerNotifier
# Import models
from app.models.device import Device
from app.models.monitoring_result import MonitoringResult
from app.models.system_setting import SystemSetting
from app.models.incident import Incident
from app.models.notification_log import NotificationLog
from app.models.ping_timeout_log import PingTimeoutLog
from app.models.maintenance import MaintenanceWindow, maintenance_devices

logger = logging.getLogger("nms.worker.scheduler")

class MonitoringScheduler:
    def __init__(self, database_url: Optional[str] = None):
        self.db_url = database_url or worker_settings.database_url
        self.engine = create_async_engine(self.db_url, pool_size=10, max_overflow=20, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        
        self.icmp_engine = AsyncICMPEngine(ping_count=worker_settings.PING_COUNT)
        self.state_machine = DeviceStateMachine()
        self.semaphore = asyncio.Semaphore(worker_settings.MAX_CONCURRENT_PINGS)
        
        self.is_running = False
        self._last_checked_times: Dict[UUID, float] = {}
        self.global_settings: Dict[str, any] = {}
        self.active_maintenance_devices: Set[UUID] = set()
        self._last_retention_cleanup = 0.0

    async def load_global_settings(self, db: AsyncSession):
        """Fetch system settings for fallback thresholds."""
        try:
            res = await db.execute(select(SystemSetting))
            settings_rows = res.scalars().all()
            self.global_settings = {row.key: row.value for row in settings_rows}
        except Exception as e:
            logger.warning(f"Could not load system_settings, using defaults: {e}")

    async def load_active_maintenance_windows(self, db: AsyncSession):
        """Load set of device IDs currently in active maintenance window (PRD §20)."""
        try:
            if self.global_settings.get("maintenance_suppression_enabled", "true").lower() not in ("true", "1", "yes"):
                self.active_maintenance_devices = set()
                return
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
            self.active_maintenance_devices = set(res.scalars().all())
        except Exception as e:
            logger.debug(f"Could not check maintenance windows: {e}")
            self.active_maintenance_devices = set()

    def get_setting_int(self, key: str, default: int) -> int:
        try:
            return int(self.global_settings.get(key, default))
        except (ValueError, TypeError):
            return default

    def get_setting_float(self, key: str, default: float) -> float:
        try:
            return float(self.global_settings.get(key, default))
        except (ValueError, TypeError):
            return default

    async def _record_ping_timeouts(self, device_data: dict, ping_res: PingResult, timeout: int, timestamp: datetime):
        """Persist raw missed probes independently of the monitoring transaction."""
        timeout_count = ping_res.timed_out_probes
        if timeout_count <= 0:
            return
        reason = (ping_res.error_message or "").lower()
        reason_code = "UNREACHABLE" if "unreachable" in reason else ("TIMEOUT" if "timeout" in reason else "ICMP_ERROR")
        try:
            async with self.session_factory() as db:
                active = (await db.execute(
                    select(Incident).where(
                        Incident.device_id == device_data["id"],
                        Incident.status.in_(["OPEN", "ACKNOWLEDGED"]),
                    ).order_by(Incident.down_since.asc())
                )).scalars().first()
                db.add_all([
                    PingTimeoutLog(
                        device_id=device_data["id"],
                        timestamp=timestamp,
                        probe_no=probe_no,
                        timeout_ms=int(timeout * 1000),
                        reason_code=reason_code,
                        incident_id=active.id if active else None,
                    )
                    for probe_no in range(1, timeout_count + 1)
                ])
                if active:
                    active.timeout_count = (active.timeout_count or 0) + timeout_count
                await db.commit()
        except Exception as exc:
            # An audit write must never change the monitoring state decision.
            logger.warning("Database audit write failure for device %s: %s", device_data["id"], exc)

    async def dispatch_due_reminders(self, db: AsyncSession):
        """Send configured email reminders for incidents that remain open."""
        if self.global_settings.get("reminder_notifications_enabled", "true").lower() not in ("true", "1", "yes"):
            return
        try:
            from app.models.category import Category
            res = await db.execute(
                select(Incident, Device).join(Device, Device.id == Incident.device_id).where(
                    Incident.status.in_(["OPEN", "ACKNOWLEDGED"])
                )
            )
            rows = res.all()
            cat_res = await db.execute(select(Category))
            categories = {c.id: c for c in cat_res.scalars().all()}
            now = datetime.now(timezone.utc)

            for incident, device in rows:
                if not incident.down_since:
                    continue
                down_since = incident.down_since
                if down_since.tzinfo is None:
                    down_since = down_since.replace(tzinfo=timezone.utc)
                elapsed_minutes = (now - down_since).total_seconds() / 60
                category = categories.get(device.category_id)
                severity = (getattr(category, "criticality", "CRITICAL") if category else "CRITICAL").upper()

                if severity == "CRITICAL":
                    first = self.get_setting_int("critical_reminder_1_minutes", 15)
                    second = self.get_setting_int("critical_reminder_2_minutes", 60)
                    repeat_minutes = self.get_setting_int("critical_reminder_repeat_hours", 4) * 60
                elif severity == "HIGH":
                    first = self.get_setting_int("high_reminder_1_minutes", 30)
                    second = self.get_setting_int("high_reminder_2_minutes", 120)
                    repeat_minutes = self.get_setting_int("high_reminder_repeat_hours", 6) * 60
                elif severity == "MEDIUM":
                    if self.global_settings.get("medium_reminder_enabled", "false").lower() not in ("true", "1", "yes"):
                        continue
                    first, second, repeat_minutes = 60, 240, 480
                else:
                    if self.global_settings.get("low_reminder_enabled", "false").lower() not in ("true", "1", "yes"):
                        continue
                    first, second, repeat_minutes = 120, 480, 720

                log_res = await db.execute(
                    select(NotificationLog).where(
                        NotificationLog.incident_id == incident.id,
                        NotificationLog.channel == "EMAIL",
                        NotificationLog.event_type.in_(["DOWN", "REMINDER"])
                    ).order_by(NotificationLog.sent_at.desc())
                )
                logs = log_res.scalars().all()
                reminder_count = sum(1 for log in logs if log.event_type == "REMINDER")
                last_log = logs[0] if logs else None
                due = False
                if reminder_count == 0:
                    due = elapsed_minutes >= first
                elif reminder_count == 1:
                    due = elapsed_minutes >= second
                elif last_log and last_log.sent_at:
                    last_sent = last_log.sent_at
                    if last_sent.tzinfo is None:
                        last_sent = last_sent.replace(tzinfo=timezone.utc)
                    due = (now - last_sent).total_seconds() / 60 >= repeat_minutes
                if not due:
                    continue

                dev_data = {
                    "id": device.id,
                    "device_name": device.device_name,
                    "ip_address": device.ip_address,
                    "current_status": device.current_status,
                    "criticality": severity,
                }
                inc_data = {
                    "id": incident.id,
                    "down_since": incident.down_since,
                    "reminder_number": reminder_count + 1,
                }
                await WorkerNotifier.trigger_reminder_notification(db, dev_data, inc_data)
        except Exception as exc:
            logger.warning(f"Could not dispatch incident reminders: {exc}")

    async def cleanup_timeout_logs(self, db: AsyncSession):
        """Delete expired raw timeout evidence in small batches."""
        retention_days = self.get_setting_int("ping_timeout_retention_days", 365)
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, retention_days))
        total = 0
        batch_size = 1000
        try:
            while True:
                result = await db.execute(text("""
                    DELETE FROM ping_timeout_logs
                    WHERE id IN (
                        SELECT id FROM ping_timeout_logs
                        WHERE timestamp < :cutoff
                        ORDER BY id
                        LIMIT :batch_size
                    )
                """), {"cutoff": cutoff, "batch_size": batch_size})
                deleted = max(result.rowcount or 0, 0)
                await db.commit()
                total += deleted
                if deleted < batch_size:
                    break
            if total:
                logger.info("Ping timeout retention cleanup deleted %s records", total)
        except Exception as exc:
            await db.rollback()
            logger.warning("Ping timeout retention cleanup failed: %s", exc)

    async def cleanup_raw_monitoring_results(self, db: AsyncSession):
        """Delete monitoring results older than the configured raw-data retention."""
        retention_days = self.get_setting_int("data_retention_raw_days", 7)
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, retention_days))
        total = 0
        batch_size = 10000
        try:
            while True:
                result = await db.execute(text("""
                    DELETE FROM monitoring_results
                    WHERE id IN (
                        SELECT id FROM monitoring_results
                        WHERE checked_at < :cutoff
                        ORDER BY checked_at, id
                        LIMIT :batch_size
                    )
                """), {"cutoff": cutoff, "batch_size": batch_size})
                deleted = max(result.rowcount or 0, 0)
                await db.commit()
                total += deleted
                if deleted < batch_size:
                    break
            if total:
                logger.info("Raw monitoring retention cleanup deleted %s records", total)
        except Exception as exc:
            await db.rollback()
            logger.warning("Raw monitoring retention cleanup failed: %s", exc)

    async def check_single_device(self, device_data: dict):
        """
        Ping a single device, evaluate state machine, update database, manage incidents.
        """
        async with self.semaphore:
            device_id = device_data["id"]
            device_name = device_data["device_name"]
            ip_address = device_data["ip_address"]
            timeout = device_data["ping_timeout"] or self.get_setting_int("default_ping_timeout", worker_settings.DEFAULT_PING_TIMEOUT)
            
            # Execute ICMP Ping
            ping_res: PingResult = await self.icmp_engine.ping(ip_address=ip_address, timeout=timeout)
            now_utc = datetime.now(timezone.utc)
            if ping_res.timed_out_probes:
                logger.info(
                    "ICMP probe timeout: device=%s probes=%s timeout_ms=%s",
                    device_name, ping_res.timed_out_probes, int(timeout * 1000),
                )
                await self._record_ping_timeouts(device_data, ping_res, timeout, now_utc)
            
            # Extract thresholds
            fail_thresh = device_data["failure_threshold"] or self.get_setting_int("default_failure_threshold", worker_settings.DEFAULT_FAILURE_THRESHOLD)
            rec_thresh = device_data["recovery_threshold"] or self.get_setting_int("default_recovery_threshold", worker_settings.DEFAULT_RECOVERY_THRESHOLD)
            lat_warn = self.get_setting_float("latency_warning_threshold", worker_settings.DEFAULT_LATENCY_WARNING)
            lat_crit = self.get_setting_float("latency_critical_threshold", worker_settings.DEFAULT_LATENCY_CRITICAL)
            is_in_maintenance = device_id in self.active_maintenance_devices
            
            # Evaluate State Machine
            trans = self.state_machine.evaluate(
                device_id=device_id,
                ping_result=ping_res,
                failure_threshold=fail_thresh,
                recovery_threshold=rec_thresh,
                latency_warning_threshold=lat_warn,
                latency_critical_threshold=lat_crit,
                is_in_maintenance=is_in_maintenance,
                initial_status=device_data["current_status"]
            )

            parent_suppressed = (
                self.global_settings.get("parent_down_suppression_enabled", "true").lower() in ("true", "1", "yes")
                and device_data.get("parent_device_id")
                and device_data.get("parent_status") in ("DOWN", "UNREACHABLE_PARENT_DOWN")
            )
            if parent_suppressed:
                trans.new_status = "UNREACHABLE_PARENT_DOWN"
                trans.status_changed = device_data.get("current_status") != trans.new_status
                trans.event_type = None
            
            # Log transition if status changed
            if trans.status_changed:
                logger.info(
                    f"Device {device_name} ({ip_address}) status changed: "
                    f"{trans.previous_status} -> {trans.new_status} (Event: {trans.event_type})"
                )

            # Persist check result, update device table, and trigger IncidentManager
            try:
                async with self.session_factory() as db:
                    # 1. Insert into monitoring_results
                    mon_result = MonitoringResult(
                        device_id=device_id,
                        checked_at=now_utc,
                        status=trans.new_status,
                        latency=ping_res.latency,
                        packet_loss=ping_res.packet_loss,
                        is_successful=ping_res.is_alive,
                        error_message=ping_res.error_message
                    )
                    db.add(mon_result)

                    # 2. Update Device record
                    dev_update = {
                        "current_status": trans.new_status,
                        "current_latency": ping_res.latency,
                        "last_check": now_utc
                    }
                    if ping_res.is_alive:
                        dev_update["last_seen"] = now_utc
                    if trans.new_status == "UP":
                        dev_update["last_up"] = now_utc
                    elif trans.new_status == "DOWN" and trans.previous_status != "DOWN":
                        dev_update["last_down"] = now_utc

                    await db.execute(
                        update(Device).where(Device.id == device_id).values(**dev_update)
                    )
                    await db.commit()

                    # 3. Handle Incident creation or resolution (Change2.md: NON-CRITICAL bypass)
                    if parent_suppressed:
                        logger.info(
                            f"ℹ️ [DEPENDENCY SUPPRESSED] Device: {device_name} | parent is DOWN; no child incident or email"
                        )
                    elif trans.event_type == "DOWN":
                        # Check category policy: skip incident/alert for non-critical devices
                        incident_enabled = device_data.get("incident_enabled", True)
                        if not incident_enabled:
                            # Workstation / non-critical: record status only, no incident
                            logger.info(
                                f"ℹ️ [NON-CRITICAL DOWN] Device: {device_name} |"
                                f" Status recorded as DOWN, no incident/alert created"
                            )
                        else:
                            reason = ping_res.error_message or f"Consecutive ping failures ({trans.consecutive_failures}/{fail_thresh})"
                            await IncidentManager.handle_down_event(
                                db=db,
                                device_id=device_id,
                                device_name=device_name,
                                first_failure_at=trans.first_failure_at,
                                failure_reason=reason,
                                device_dict=device_data
                            )
                    elif trans.event_type == "WARNING_LATENCY":
                        if device_data.get("alert_enabled", True):
                            await WorkerNotifier.trigger_warning_notification(
                                db=db,
                                device_data={**device_data, "current_latency": ping_res.latency},
                                incident_data={"failure_reason": "Latency or packet loss threshold exceeded"}
                            )
                    elif trans.event_type == "RECOVERED":
                        # Check category policy: skip recovery alert for non-critical devices
                        alert_enabled = device_data.get("alert_enabled", True)
                        if not alert_enabled:
                            # Workstation / non-critical: record recovery, no recovery alert
                            logger.info(
                                f"ℹ️ [NON-CRITICAL RECOVERY] Device: {device_name} |"
                                f" Recovered, no recovery alert sent"
                            )
                        else:
                            await IncidentManager.handle_recovery_event(
                                db=db,
                                device_id=device_id,
                                device_name=device_name,
                                device_dict=device_data
                            )

            except Exception as e:
                logger.error(f"Error persisting monitoring result for device {device_id}: {e}")

    async def run_monitoring_cycle(self):
        """
        Fetch all enabled devices and schedule checks for those due.
        """
        try:
            async with self.session_factory() as db:
                await self.load_global_settings(db)
                await self.load_active_maintenance_windows(db)
                
                # Fetch enabled devices
                res = await db.execute(
                    select(Device).where(Device.monitoring_enabled == True)
                )
                devices = res.scalars().all()
                
                tasks = []
                current_time = asyncio.get_event_loop().time()
                default_interval = self.get_setting_int("default_monitoring_interval", worker_settings.DEFAULT_MONITORING_INTERVAL)

                # Pre-fetch categories for policy lookup
                from app.models.category import Category
                cat_res = await db.execute(select(Category))
                categories_map = {cat.id: cat for cat in cat_res.scalars().all()}

                for dev in devices:
                    category = categories_map.get(dev.category_id)
                    dev_dict = {
                        "id": dev.id,
                        "device_name": dev.device_name,
                        "ip_address": dev.ip_address,
                        "parent_device_id": dev.parent_device_id,
                        "parent_status": next((p.current_status for p in devices if p.id == dev.parent_device_id), None),
                        "ping_timeout": dev.ping_timeout,
                        "failure_threshold": dev.failure_threshold,
                        "recovery_threshold": dev.recovery_threshold,
                        "monitoring_interval": dev.monitoring_interval,
                        "current_status": dev.current_status,
                        # Category monitoring policy (Change2.md)
                        "criticality": getattr(category, 'criticality', 'CRITICAL') if category else 'CRITICAL',
                        "incident_enabled": getattr(category, 'incident_enabled', True) if category else True,
                        "alert_enabled": getattr(category, 'alert_enabled', True) if category else True,
                        "sla_enabled": getattr(category, 'sla_enabled', True) if category else True
                    }
                    interval = dev.monitoring_interval or default_interval
                    if dev.current_status == "DOWN":
                        down_interval = self.get_setting_int("down_monitoring_interval", 60)
                        long_down_minutes = self.get_setting_int("long_down_threshold_minutes", 15)
                        long_down_interval = self.get_setting_int("long_down_monitoring_interval", 300)
                        if dev.last_down:
                            down_since = dev.last_down if dev.last_down.tzinfo else dev.last_down.replace(tzinfo=timezone.utc)
                            down_age = (datetime.now(timezone.utc) - down_since).total_seconds()
                            interval = long_down_interval if down_age >= long_down_minutes * 60 else down_interval
                    last_checked = self._last_checked_times.get(dev.id, 0.0)

                    # Check if device check is due
                    if current_time - last_checked >= interval:
                        self._last_checked_times[dev.id] = current_time
                        tasks.append(self.check_single_device(dev_dict))

                if tasks:
                    logger.debug(f"Dispatching {len(tasks)} device monitoring checks...")
                    await asyncio.gather(*tasks, return_exceptions=True)
                await self.dispatch_due_reminders(db)
                now_monotonic = asyncio.get_event_loop().time()
                if now_monotonic - self._last_retention_cleanup >= 3600:
                    await self.cleanup_raw_monitoring_results(db)
                    await self.cleanup_timeout_logs(db)
                    self._last_retention_cleanup = now_monotonic

        except Exception as e:
            logger.error(f"Error during monitoring cycle: {e}")

    async def start(self):
        """Main monitoring loop."""
        self.is_running = True
        logger.info("Monitoring Scheduler started with Incident & Maintenance Engine.")
        
        while self.is_running:
            await self.run_monitoring_cycle()
            await asyncio.sleep(1.0)

    async def stop(self):
        """Gracefully stop monitoring engine and release connection pool."""
        self.is_running = False
        logger.info("Stopping Monitoring Scheduler...")
        await self.engine.dispose()
        logger.info("Monitoring Scheduler stopped.")
