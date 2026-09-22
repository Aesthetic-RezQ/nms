import pytest
from httpx import AsyncClient
from app.models.device import Device
from app.models.category import Category
from app.models.group import DeviceGroup
from app.models.location import Location
from app.models.incident import Incident
from app.services.device_service import DeviceService
from sqlalchemy import select
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_create_device(async_client: AsyncClient, admin_headers, test_category):
    response = await async_client.post("/api/devices/", json={
        "device_name": "Test Router",
        "ip_address": "192.168.1.1",
        "category_id": test_category.id
    }, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["device_name"] == "Test Router"

@pytest.mark.asyncio
async def test_create_device_duplicate_ip(async_client: AsyncClient, admin_headers):
    await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "192.168.1.2"}, headers=admin_headers)
    response = await async_client.post("/api/devices/", json={"device_name": "Dev 2", "ip_address": "192.168.1.2"}, headers=admin_headers)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_create_device_invalid_ip(async_client: AsyncClient, admin_headers):
    response = await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "invalid_ip"}, headers=admin_headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_list_devices(async_client: AsyncClient, admin_headers):
    await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "10.0.0.1"}, headers=admin_headers)
    response = await async_client.get("/api/devices/", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0

@pytest.mark.asyncio
async def test_list_devices_with_filters(async_client: AsyncClient, admin_headers):
    await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "10.0.0.1"}, headers=admin_headers)
    response = await async_client.get("/api/devices/?search=Dev", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1

@pytest.mark.asyncio
async def test_get_device(async_client: AsyncClient, admin_headers):
    create_response = await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "10.0.0.1"}, headers=admin_headers)
    device_id = create_response.json()["id"]
    response = await async_client.get(f"/api/devices/{device_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == device_id

@pytest.mark.asyncio
async def test_update_device(async_client: AsyncClient, admin_headers):
    create_response = await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "10.0.0.1"}, headers=admin_headers)
    device_id = create_response.json()["id"]
    response = await async_client.put(f"/api/devices/{device_id}", json={"device_name": "Dev Updated"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["device_name"] == "Dev Updated"

@pytest.mark.asyncio
async def test_delete_device(async_client: AsyncClient, admin_headers):
    create_response = await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "10.0.0.1"}, headers=admin_headers)
    device_id = create_response.json()["id"]
    response = await async_client.delete(f"/api/devices/{device_id}", headers=admin_headers)
    assert response.status_code == 200
    
    get_response = await async_client.get(f"/api/devices/{device_id}", headers=admin_headers)
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_bulk_delete_devices(async_client: AsyncClient, admin_headers):
    device_ids = []
    for index in range(2):
        create_response = await async_client.post(
            "/api/devices/",
            json={"device_name": f"Bulk Device {index}", "ip_address": f"10.0.0.{40 + index}"},
            headers=admin_headers,
        )
        assert create_response.status_code == 200
        device_ids.append(create_response.json()["id"])

    response = await async_client.request(
        "DELETE",
        "/api/devices/bulk",
        json={"device_ids": device_ids},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    for device_id in device_ids:
        get_response = await async_client.get(f"/api/devices/{device_id}", headers=admin_headers)
        assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_device_with_incidents(test_db):
    device = Device(device_name="Incident Device", ip_address="10.0.0.31", current_status="UNKNOWN")
    test_db.add(device)
    await test_db.commit()
    incident = Incident(
        device_id=device.id,
        detected_at=datetime.now(timezone.utc),
        down_since=datetime.now(timezone.utc),
    )
    test_db.add(incident)
    await test_db.commit()

    await DeviceService.delete(test_db, device.id)

    incidents = await test_db.execute(select(Incident).where(Incident.device_id == device.id))
    assert incidents.scalars().all() == []

@pytest.mark.asyncio
async def test_import_assigns_category_group_and_location(test_db):
    category = Category(name="Network")
    group = DeviceGroup(name="Core")
    location = Location(name="Jakarta")
    test_db.add_all([category, group, location])
    await test_db.commit()

    result = await DeviceService.bulk_import(
        test_db,
        "device_name,ip_address,category,group,location,vlan_id,subnet\n"
        "Core Router,10.0.0.32,network,core,jakarta,100,10.0.0.0/24\n"
        "Access Switch,10.0.0.33,Switching,Access,Surabaya,200,10.0.1.0/24\n",
    )

    assert result["created"] == 2
    devices = (await test_db.execute(select(Device).order_by(Device.ip_address))).scalars().all()
    assert devices[0].category_id == category.id
    assert devices[0].group_id == group.id
    assert devices[0].location_id == location.id
    assert devices[1].vlan_id == 200
    created_category = await test_db.execute(select(Category).where(Category.name == "Switching"))
    assert created_category.scalars().one()
    exported_csv = await DeviceService.export(test_db)
    assert exported_csv.splitlines()[0] == "device_name,ip_address,hostname,category,group,location,vlan_id,vlan_name,subnet,description,current_status"

@pytest.mark.asyncio
async def test_viewer_cannot_create_device(async_client: AsyncClient, viewer_headers):
    response = await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "10.0.0.1"}, headers=viewer_headers)
    assert response.status_code == 403
