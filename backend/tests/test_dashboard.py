import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models.device import Device
from app.models.category import Category
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_get_dashboard_summary(async_client, admin_headers, test_db: AsyncSession):
    now = datetime.now(timezone.utc)
    
    # 1. Create devices in different states
    d1 = Device(
        id=uuid.uuid4(),
        device_name="Core Router",
        ip_address="10.0.0.1",
        current_status="UP",
        last_check=now
    )
    d2 = Device(
        id=uuid.uuid4(),
        device_name="Switch 01",
        ip_address="10.0.0.2",
        current_status="DOWN",
        last_check=now
    )
    d3 = Device(
        id=uuid.uuid4(),
        device_name="AP 01",
        ip_address="10.0.0.3",
        current_status="WARNING",
        last_check=now
    )
    test_db.add_all([d1, d2, d3])
    await test_db.commit()

    # 2. Query summary
    res = await async_client.get("/api/dashboard/summary", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    
    counts = data["status_counts"]
    assert counts["total"] == 3
    assert counts["up"] == 1
    assert counts["down"] == 1
    assert counts["warning"] == 1
    assert counts["unknown"] == 0
    assert counts["maintenance"] == 0

    assert data["worker_status"]["is_active"] is True
    assert data["worker_status"]["is_stale"] is False

@pytest.mark.asyncio
async def test_dashboard_stale_detection(async_client, admin_headers, test_db: AsyncSession):
    old_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    d1 = Device(
        id=uuid.uuid4(),
        device_name="Firewall",
        ip_address="10.0.0.254",
        current_status="UP",
        last_check=old_time
    )
    test_db.add(d1)
    await test_db.commit()

    res = await async_client.get("/api/dashboard/summary", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    
    assert data["worker_status"]["is_stale"] is True
    assert "DATA STALE" in data["worker_status"]["status_message"]

@pytest.mark.asyncio
async def test_get_dashboard_summary_filters_by_category(async_client, admin_headers, test_db: AsyncSession):
    category = Category(name="Network Infrastructure")
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    selected_device = Device(
        id=uuid.uuid4(),
        device_name="Selected Device",
        ip_address="10.0.0.10",
        category_id=category.id,
        current_status="UP",
    )
    other_device = Device(
        id=uuid.uuid4(),
        device_name="Other Device",
        ip_address="10.0.0.11",
        current_status="DOWN",
    )
    test_db.add_all([selected_device, other_device])
    await test_db.commit()

    res = await async_client.get(
        f"/api/dashboard/summary?category_id={category.id}",
        headers=admin_headers,
    )
    assert res.status_code == 200

    counts = res.json()["status_counts"]
    assert counts["total"] == 1
    assert counts["up"] == 1
    assert counts["down"] == 0
