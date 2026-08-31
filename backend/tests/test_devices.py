import pytest
from httpx import AsyncClient
from app.models.device import Device
from sqlalchemy import select

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
async def test_viewer_cannot_create_device(async_client: AsyncClient, viewer_headers):
    response = await async_client.post("/api/devices/", json={"device_name": "Dev 1", "ip_address": "10.0.0.1"}, headers=viewer_headers)
    assert response.status_code == 403
