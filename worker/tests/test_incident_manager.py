import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.models.base import Base
from app.models.device import Device
from app.models.incident import Incident
from monitoring.incident_manager import IncidentManager

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    async with test_session_maker() as session:
        yield session

@pytest.mark.asyncio
async def test_incident_creation_and_resolution(db_session):
    device_id = uuid.uuid4()
    device = Device(
        id=device_id,
        device_name="Switch Core",
        ip_address="10.10.10.1",
        current_status="UNKNOWN"
    )
    db_session.add(device)
    await db_session.commit()

    first_fail_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    # 1. Trigger DOWN event -> should create an incident
    incident = await IncidentManager.handle_down_event(
        db=db_session,
        device_id=device_id,
        device_name="Switch Core",
        first_failure_at=first_fail_time,
        failure_reason="Ping timeout"
    )
    assert incident is not None
    assert incident.status == "OPEN"
    assert incident.failure_reason == "Ping timeout"

    # 2. Trigger another DOWN event -> should NOT duplicate active incident
    dup_incident = await IncidentManager.handle_down_event(
        db=db_session,
        device_id=device_id,
        device_name="Switch Core",
        first_failure_at=first_fail_time,
        failure_reason="Ping timeout again"
    )
    assert dup_incident.id == incident.id

    # Verify only 1 incident exists in DB
    all_incidents = (await db_session.execute(select(Incident))).scalars().all()
    assert len(all_incidents) == 1

    # 3. Trigger RECOVERY event -> should resolve incident and calculate duration
    resolved = await IncidentManager.handle_recovery_event(
        db=db_session,
        device_id=device_id,
        device_name="Switch Core"
    )
    assert resolved is not None
    assert resolved.status == "RESOLVED"
    assert resolved.recovered_at is not None
    assert resolved.duration_seconds is not None
    assert resolved.duration_seconds >= 300  # >= 5 minutes (300s)
