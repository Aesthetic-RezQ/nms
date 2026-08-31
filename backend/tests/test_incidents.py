import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models.incident import Incident
from app.models.device import Device
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_list_and_filter_incidents(async_client, admin_headers, test_db: AsyncSession):
    # 1. Create a device
    dev_res = await async_client.post("/api/devices/", json={
        "device_name": "Firewall Primary",
        "ip_address": "192.168.1.254"
    }, headers=admin_headers)
    assert dev_res.status_code == 200
    device_id = uuid.UUID(dev_res.json()["id"])

    # 2. Add an open incident and a resolved incident
    now = datetime.now(timezone.utc)
    inc_open = Incident(
        id=uuid.uuid4(),
        device_id=device_id,
        status="OPEN",
        detected_at=now,
        down_since=now - timedelta(minutes=10),
        failure_reason="Packet loss 100%"
    )
    inc_resolved = Incident(
        id=uuid.uuid4(),
        device_id=device_id,
        status="RESOLVED",
        detected_at=now - timedelta(hours=2),
        down_since=now - timedelta(hours=2),
        recovered_at=now - timedelta(hours=1),
        duration_seconds=3600,
        failure_reason="Host unreachable"
    )
    test_db.add_all([inc_open, inc_resolved])
    await test_db.commit()

    # 3. List all incidents
    res = await async_client.get("/api/incidents", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2

    # 4. Filter by status=OPEN
    res_open = await async_client.get("/api/incidents?status=OPEN", headers=admin_headers)
    assert res_open.status_code == 200
    data_open = res_open.json()
    assert data_open["total"] == 1
    assert data_open["data"][0]["status"] == "OPEN"

@pytest.mark.asyncio
async def test_acknowledge_incident(async_client, admin_headers, viewer_headers, test_db: AsyncSession):
    dev_res = await async_client.post("/api/devices/", json={
        "device_name": "Access Point 01",
        "ip_address": "192.168.10.15"
    }, headers=admin_headers)
    device_id = uuid.UUID(dev_res.json()["id"])

    now = datetime.now(timezone.utc)
    incident_id = uuid.uuid4()
    incident = Incident(
        id=incident_id,
        device_id=device_id,
        status="OPEN",
        detected_at=now,
        down_since=now,
        failure_reason="No route to host"
    )
    test_db.add(incident)
    await test_db.commit()

    # Viewer cannot acknowledge (RBAC check)
    viewer_ack = await async_client.post(
        f"/api/incidents/{incident_id}/acknowledge",
        json={"notes": "Viewer attempt"},
        headers=viewer_headers
    )
    assert viewer_ack.status_code == 403

    # Admin acknowledges incident
    admin_ack = await async_client.post(
        f"/api/incidents/{incident_id}/acknowledge",
        json={"notes": "Investigating switch port"},
        headers=admin_headers
    )
    assert admin_ack.status_code == 200
    ack_data = admin_ack.json()
    assert ack_data["status"] == "ACKNOWLEDGED"
    assert ack_data["is_acknowledged"] is True
    assert "Investigating switch port" in ack_data["notes"]

@pytest.mark.asyncio
async def test_add_incident_note(async_client, admin_headers, test_db: AsyncSession):
    dev_res = await async_client.post("/api/devices/", json={
        "device_name": "UPS Server Room",
        "ip_address": "192.168.1.50"
    }, headers=admin_headers)
    device_id = uuid.UUID(dev_res.json()["id"])

    incident_id = uuid.uuid4()
    incident = Incident(
        id=incident_id,
        device_id=device_id,
        status="OPEN",
        detected_at=datetime.now(timezone.utc),
        down_since=datetime.now(timezone.utc),
        failure_reason="Battery depleted"
    )
    test_db.add(incident)
    await test_db.commit()

    res = await async_client.post(
        f"/api/incidents/{incident_id}/notes",
        json={"notes": "Battery replacement scheduled for 2 PM"},
        headers=admin_headers
    )
    assert res.status_code == 200
    assert "Battery replacement scheduled" in res.json()["notes"]
