import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.config import settings
from app.models.base import Base
from app.models import User, Device, Category, DeviceGroup, Location, SystemSetting, AuditLog
from app.core.security import hash_password

async def seed():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        admin = await db.execute(select(User).where(User.username == "admin"))
        if not admin.scalars().first():
            db.add(User(username="admin", email="admin@nms.local", password_hash=hash_password("admin"), role="admin", full_name="System Admin"))
            
        categories = ["Firewall", "Router", "Core Switch", "Distribution Switch", "Access Switch", "Server", "Virtual Machine", "Access Point", "CCTV", "NVR", "Printer", "PLC", "UPS", "Storage", "IoT", "Other"]
        for c in categories:
            res = await db.execute(select(Category).where(Category.name == c))
            if not res.scalars().first():
                db.add(Category(name=c))
                
        groups = ["Network Infrastructure", "Servers", "CCTV System", "WiFi Infrastructure", "OT Network", "Office Equipment"]
        for g in groups:
            res = await db.execute(select(DeviceGroup).where(DeviceGroup.name == g))
            if not res.scalars().first():
                db.add(DeviceGroup(name=g))
                
        locations = ["Main Office", "Data Center"]
        for loc in locations:
            res = await db.execute(select(Location).where(Location.name == loc))
            if not res.scalars().first():
                db.add(Location(name=loc))
                
        settings_data = [
            ("default_monitoring_interval", "15", "integer"),
            ("default_ping_timeout", "2", "integer"),
            ("default_failure_threshold", "3", "integer"),
            ("default_recovery_threshold", "2", "integer"),
            ("latency_warning_threshold", "100", "integer"),
            ("latency_critical_threshold", "250", "integer"),
            ("app_timezone", "Asia/Jakarta", "string"),
            ("data_retention_raw_days", "7", "integer"),
            ("data_retention_aggregate_days", "30", "integer")
        ]
        
        for k, v, t in settings_data:
            res = await db.execute(select(SystemSetting).where(SystemSetting.key == k))
            if not res.scalars().first():
                db.add(SystemSetting(key=k, value=v, data_type=t))
                
        await db.commit()
    await engine.dispose()
    print("Seed complete!")

if __name__ == "__main__":
    asyncio.run(seed())
