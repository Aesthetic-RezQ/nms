import pytest
import uuid
from datetime import datetime, timezone
from app.models.monitoring_result import MonitoringResult
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_get_device_monitoring_history(async_client, admin_headers, test_db: AsyncSession):
    # 1. Create a test device via API
    dev_res = await async_client.post("/api/devices/", json={
        "device_name": "Core Router",
        "ip_address": "192.168.1.1"
    }, headers=admin_headers)
    assert dev_res.status_code == 200
    device_id = uuid.UUID(dev_res.json()["id"])

    # 2. Add monitoring results
    res1 = MonitoringResult(
        device_id=device_id,
        checked_at=datetime.now(timezone.utc),
        status="UP",
        latency=12.5,
        packet_loss=0.0,
        is_successful=True
    )
    res2 = MonitoringResult(
        device_id=device_id,
        checked_at=datetime.now(timezone.utc),
        status="UP",
        latency=14.2,
        packet_loss=0.0,
        is_successful=True
    )
    test_db.add_all([res1, res2])
    await test_db.commit()

    # 3. Call history endpoint
    resp = await async_client.get(f"/api/devices/{device_id}/history", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["status"] == "UP"
    assert data[0]["latency"] in (12.5, 14.2)

@pytest.mark.asyncio
async def test_get_device_metrics_summary(async_client, admin_headers, test_db: AsyncSession):
    dev_res = await async_client.post("/api/devices/", json={
        "device_name": "Switch 01",
        "ip_address": "192.168.1.2"
    }, headers=admin_headers)
    assert dev_res.status_code == 200
    device_id = uuid.UUID(dev_res.json()["id"])

    # Add 1 successful check and 1 failed check
    r1 = MonitoringResult(
        device_id=device_id,
        checked_at=datetime.now(timezone.utc),
        status="UP",
        latency=5.0,
        is_successful=True
    )
    r2 = MonitoringResult(
        device_id=device_id,
        checked_at=datetime.now(timezone.utc),
        status="DOWN",
        latency=None,
        is_successful=False
    )
    test_db.add_all([r1, r2])
    await test_db.commit()

    resp = await async_client.get(f"/api/devices/{device_id}/metrics", headers=admin_headers)
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["availability_24h"] == 50.0
    assert metrics["avg_latency_24h"] == 5.0
