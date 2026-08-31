import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models.device import Device
from app.models.maintenance import MaintenanceWindow
from app.services.maintenance_service import MaintenanceService
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_maintenance_window_crud(async_client, admin_headers, test_db: AsyncSession):
    # 1. Create test device
    dev_res = await async_client.post("/api/devices/", json={
        "device_name": "Switch Core 10G",
        "ip_address": "10.0.0.10"
    }, headers=admin_headers)
    assert dev_res.status_code == 200
    device_id = dev_res.json()["id"]

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(minutes=10)
    end_time = now + timedelta(hours=2)

    # 2. Create maintenance window via API
    create_payload = {
        "name": "Emergency Firmware Patch",
        "description": "Upgrading firmware on core switches",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "is_active": True,
        "device_ids": [device_id]
    }
    res = await async_client.post("/api/maintenance", json=create_payload, headers=admin_headers)
    assert res.status_code == 200
    win_data = res.json()
    assert win_data["name"] == "Emergency Firmware Patch"
    assert win_data["is_currently_active"] is True
    assert win_data["devices_count"] == 1
    window_id = win_data["id"]

    # 3. Verify active device maintenance helper
    active_ids = await MaintenanceService.get_active_maintenance_device_ids(test_db)
    assert uuid.UUID(device_id) in active_ids

    # 4. List maintenance windows
    list_res = await async_client.get("/api/maintenance", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 5. Delete window
    del_res = await async_client.delete(f"/api/maintenance/{window_id}", headers=admin_headers)
    assert del_res.status_code == 200
