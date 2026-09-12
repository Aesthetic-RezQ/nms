import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.config import settings
from app.models.base import Base
from app.models import User, Device, Category, DeviceGroup, Location, SystemSetting, AuditLog

async def seed():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        # User identities and passwords are provisioned in CentralAuth. This
        # seed creates monitoring data only and intentionally does not create a
        # local administrator account.
        # Standard infrastructure categories (CRITICAL by default)
        categories = ["Firewall", "Router", "Core Switch", "Distribution Switch", "Access Switch", "Server", "Virtual Machine", "Access Point", "CCTV", "NVR", "Printer", "PLC", "UPS", "Storage", "IoT", "Other"]
        for c in categories:
            res = await db.execute(select(Category).where(Category.name == c))
            if not res.scalars().first():
                db.add(Category(name=c))

        # Non-critical categories (Change2.md: Workstations)
        non_critical_categories = {
            "Workstation": "Workstations are not expected to stay online 24/7. DOWN status does not trigger incidents or alerts."
        }
        for name, desc in non_critical_categories.items():
            res = await db.execute(select(Category).where(Category.name == name))
            if not res.scalars().first():
                db.add(Category(
                    name=name,
                    description=desc,
                    criticality="NON_CRITICAL",
                    incident_enabled=False,
                    alert_enabled=False,
                    sla_enabled=False
                ))
                
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
