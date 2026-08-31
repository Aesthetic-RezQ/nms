from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.api import (
    auth, users, categories, groups, locations, devices,
    settings as settings_api, health, monitoring, incidents, dashboard, notifications, maintenance
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
        logger.info("Database tables ensured.")

        # Run seed to create default admin user and base data
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from sqlalchemy import select
        from app.models.user import User
        from app.models.category import Category
        from app.models.group import DeviceGroup
        from app.models.location import Location
        from app.models.system_setting import SystemSetting
        from app.core.security import hash_password

        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as db:
            # Create default admin if not exists
            res = await db.execute(select(User).where(User.username == "admin"))
            if not res.scalars().first():
                db.add(User(
                    username="admin",
                    email="admin@nms.local",
                    password_hash=hash_password("admin"),
                    role="admin",
                    full_name="System Admin"
                ))
                logger.info("Default admin user created.")

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
                ("default_ping_timeout", "2", "integer"),
                ("default_failure_threshold", "3", "integer"),
                ("default_recovery_threshold", "2", "integer"),
                ("latency_warning_threshold", "100", "integer"),
                ("latency_critical_threshold", "250", "integer"),
                ("app_timezone", "Asia/Jakarta", "string"),
                ("data_retention_raw_days", "7", "integer"),
                ("data_retention_aggregate_days", "30", "integer"),
            ]:
                res = await db.execute(select(SystemSetting).where(SystemSetting.key == k))
                if not res.scalars().first():
                    db.add(SystemSetting(key=k, value=v, data_type=t))

            await db.commit()
        logger.info("Seed data verified.")
    except Exception as e:
        logger.error(f"Startup initialization error: {e}")

