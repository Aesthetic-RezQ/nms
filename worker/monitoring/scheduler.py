import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, update, insert, and_
import math

from monitoring.config import worker_settings
from monitoring.icmp import AsyncICMPEngine, PingResult
from monitoring.state_machine import DeviceStateMachine
from monitoring.incident_manager import IncidentManager
# Import models
from app.models.device import Device
from app.models.monitoring_result import MonitoringResult
from app.models.system_setting import SystemSetting
from app.models.incident import Incident
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
            
            now_utc = datetime.now(timezone.utc)
            
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
                    elif trans.new_status == "DOWN":
                        dev_update["last_down"] = now_utc

                    await db.execute(
                        update(Device).where(Device.id == device_id).values(**dev_update)
                    )
                    await db.commit()

                    # 3. Handle Incident creation or resolution
                    if trans.event_type == "DOWN":
                        reason = ping_res.error_message or f"Consecutive ping failures ({trans.consecutive_failures}/{fail_thresh})"
                        await IncidentManager.handle_down_event(
                            db=db,
                            device_id=device_id,
                            device_name=device_name,
                            first_failure_at=trans.first_failure_at,
                            failure_reason=reason,
                            device_dict=device_data
                        )
                    elif trans.event_type == "RECOVERED":
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

                for dev in devices:
                    dev_dict = {
                        "id": dev.id,
                        "device_name": dev.device_name,
                        "ip_address": dev.ip_address,
                        "parent_device_id": dev.parent_device_id,
                        "ping_timeout": dev.ping_timeout,
                        "failure_threshold": dev.failure_threshold,
                        "recovery_threshold": dev.recovery_threshold,
                        "monitoring_interval": dev.monitoring_interval,
                        "current_status": dev.current_status
                    }
                    interval = dev.monitoring_interval or default_interval
                    last_checked = self._last_checked_times.get(dev.id, 0.0)

                    # Check if device check is due
                    if current_time - last_checked >= interval:
                        self._last_checked_times[dev.id] = current_time
                        tasks.append(self.check_single_device(dev_dict))

                if tasks:
                    logger.debug(f"Dispatching {len(tasks)} device monitoring checks...")
                    await asyncio.gather(*tasks, return_exceptions=True)

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
