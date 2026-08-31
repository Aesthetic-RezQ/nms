import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.base import Base
from app.models.device import Device
from app.models.incident import Incident
from worker.monitoring.dependency import DependencyResolver

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
async def test_parent_down_alert_suppression(db_session):
    # 1. Create Parent Device (DOWN)
    parent_id = uuid.uuid4()
    parent = Device(
        id=parent_id,
        device_name="Access Switch 01",
        ip_address="192.168.1.10",
        current_status="DOWN"
    )
    # 2. Create Child Device (connected to parent)
    child_id = uuid.uuid4()
    child = Device(
        id=child_id,
        device_name="AP Office 1",
        ip_address="192.168.1.101",
        parent_device_id=parent_id,
        current_status="DOWN"
    )
    db_session.add_all([parent, child])
    await db_session.commit()

    # 3. Create Child Incident
    child_incident = Incident(
        id=uuid.uuid4(),
        device_id=child_id,
        status="OPEN",
        detected_at=datetime.now(timezone.utc),
        down_since=datetime.now(timezone.utc),
        notification_status="PENDING"
    )
    db_session.add(child_incident)
    await db_session.commit()

    # 4. Check Dependency Suppression
    child_dict = {
        "id": child_id,
        "device_name": "AP Office 1",
        "parent_device_id": parent_id
    }
    is_suppressed = await DependencyResolver.apply_alert_suppression_if_needed(
        db=db_session,
        device_dict=child_dict,
        incident=child_incident
    )

    assert is_suppressed is True
    assert child_incident.notification_status == "SUPPRESSED_BY_DEPENDENCY"
