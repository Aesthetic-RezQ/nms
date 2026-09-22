from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.api import (
    auth, users, categories, groups, locations, devices,
    settings as settings_api, health, monitoring, incidents, dashboard, notifications, maintenance, ping_timeouts
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="LAN Network Monitoring System Backend",
    version="1.0.0",
    docs_url="/docs",
    redirect_slashes=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(groups.router)
app.include_router(locations.router)
app.include_router(devices.router)
app.include_router(monitoring.router)
app.include_router(incidents.router)
app.include_router(incidents.device_incidents_router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(maintenance.router)
app.include_router(settings_api.router)
app.include_router(settings_api.audit_router)
app.include_router(ping_timeouts.router)
app.include_router(ping_timeouts.device_router)
app.include_router(ping_timeouts.incident_router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME}...")
    try:
        # Auto-create all tables on startup (idempotent via CREATE IF NOT EXISTS)
        from app.models.base import Base
        from app.database import engine
        import app.models  # ensure all models are registered before create_all

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Existing installations were created before CentralAuth was
            # introduced. Keep their monitoring data and add only the nullable
            # identity mapping needed for the cache.
            if conn.dialect.name == "postgresql":
                from sqlalchemy import text
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS central_user_id VARCHAR(36)"))
                await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_central_user_id ON users (central_user_id)"))
                await conn.execute(text("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS timeout_count INTEGER NOT NULL DEFAULT 0"))
                # Parent/dependency suppression uses a descriptive status value
                # longer than the original MVP varchar(20) column. Only alter
                # legacy installations; repeating ALTER TABLE on every startup
                # would unnecessarily lock the monitoring tables.
                for table_name, column_name in (("devices", "current_status"), ("monitoring_results", "status")):
                    length_result = await conn.execute(text(
                        "SELECT character_maximum_length FROM information_schema.columns "
                        "WHERE table_name = :table_name AND column_name = :column_name"
                    ), {"table_name": table_name, "column_name": column_name})
                    max_length = length_result.scalar_one_or_none()
                    if max_length is not None and max_length < 40:
                        await conn.execute(text(
                            f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE VARCHAR(40)"
                        ))
        logger.info("Database tables ensured.")

        # Seed monitoring data only; identities are provisioned in CentralAuth.
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from sqlalchemy import select
        from app.models.user import User
        from app.models.category import Category
        from app.models.group import DeviceGroup
        from app.models.location import Location
        from app.models.system_setting import SystemSetting

        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as db:
            # Seed categories
            for name in ["Firewall", "Router", "Core Switch", "Distribution Switch", "Access Switch",
                         "Server", "Virtual Machine", "Access Point", "CCTV", "NVR",
                         "Printer", "PLC", "UPS", "Storage", "IoT", "Other"]:
                res = await db.execute(select(Category).where(Category.name == name))
                if not res.scalars().first():
                    db.add(Category(name=name))

            # Seed groups
            for name in ["Network Infrastructure", "Servers", "CCTV System",
                         "WiFi Infrastructure", "OT Network", "Office Equipment"]:
                res = await db.execute(select(DeviceGroup).where(DeviceGroup.name == name))
                if not res.scalars().first():
                    db.add(DeviceGroup(name=name))

            # Seed locations
            for name in ["Main Office", "Data Center"]:
                res = await db.execute(select(Location).where(Location.name == name))
                if not res.scalars().first():
                    db.add(Location(name=name))

            # Seed default system settings
            for k, v, t in [
                ("default_monitoring_interval", "15", "integer"),
                ("down_monitoring_interval", "60", "integer"),
                ("long_down_threshold_minutes", "15", "integer"),
                ("long_down_monitoring_interval", "300", "integer"),
                ("ping_timeout_retention_days", "365", "integer"),
                ("default_ping_timeout", "2", "integer"),
                ("default_failure_threshold", "3", "integer"),
                ("default_recovery_threshold", "2", "integer"),
                ("latency_warning_threshold", "100", "integer"),
                ("latency_critical_threshold", "250", "integer"),
                ("app_timezone", "Asia/Jakarta", "string"),
                ("data_retention_raw_days", "7", "integer"),
                ("data_retention_aggregate_days", "30", "integer"),
                ("telegram_enabled", "false", "boolean"),
                ("telegram_bot_token", "", "secret"),
                ("telegram_chat_id", "", "string"),
                ("email_notifications_enabled", "true", "boolean"),
                ("down_notifications_enabled", "true", "boolean"),
                ("recovery_notifications_enabled", "true", "boolean"),
                ("degraded_notifications_enabled", "true", "boolean"),
                ("reminder_notifications_enabled", "true", "boolean"),
                ("maintenance_suppression_enabled", "true", "boolean"),
                ("parent_down_suppression_enabled", "true", "boolean"),
                ("smtp_enabled", "false", "boolean"),
                ("smtp_host", "", "string"),
                ("smtp_port", "587", "integer"),
                ("smtp_encryption", "TLS", "string"),
                ("smtp_user", "", "string"),
                ("smtp_password", "", "secret"),
                ("smtp_from_email", "nms-alert@local", "string"),
                ("smtp_sender_name", "NMS", "string"),
                ("smtp_reply_to", "", "string"),
                ("smtp_to_emails", "", "string"),
                ("critical_reminder_1_minutes", "15", "integer"),
                ("critical_reminder_2_minutes", "60", "integer"),
                ("critical_reminder_repeat_hours", "4", "integer"),
                ("high_reminder_1_minutes", "30", "integer"),
                ("high_reminder_2_minutes", "120", "integer"),
                ("high_reminder_repeat_hours", "6", "integer"),
                ("medium_reminder_enabled", "false", "boolean"),
                ("low_reminder_enabled", "false", "boolean"),
            ]:
                res = await db.execute(select(SystemSetting).where(SystemSetting.key == k))
                if not res.scalars().first():
                    db.add(SystemSetting(key=k, value=v, data_type=t))

            await db.commit()
        logger.info("Seed data verified.")
    except Exception as e:
        logger.error(f"Startup initialization error: {e}")
