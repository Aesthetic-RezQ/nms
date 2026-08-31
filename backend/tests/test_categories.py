import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_category(async_client: AsyncClient, admin_headers):
    response = await async_client.post("/api/categories/", json={"name": "New Category"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "New Category"

@pytest.mark.asyncio
async def test_create_duplicate_category(async_client: AsyncClient, admin_headers, test_category):
    response = await async_client.post("/api/categories/", json={"name": "Test Category"}, headers=admin_headers)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_list_categories(async_client: AsyncClient, admin_headers, test_category):
    response = await async_client.get("/api/categories/", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_update_category(async_client: AsyncClient, admin_headers, test_category):
    response = await async_client.put(f"/api/categories/{test_category.id}", json={"name": "Updated Category"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Category"

@pytest.mark.asyncio
async def test_delete_category(async_client: AsyncClient, admin_headers, test_category):
    response = await async_client.delete(f"/api/categories/{test_category.id}", headers=admin_headers)
    assert response.status_code == 200
    
    # Try fetching list to see it's gone
    list_response = await async_client.get("/api/categories/", headers=admin_headers)
    names = [c["name"] for c in list_response.json()]
    assert "Test Category" not in names

@pytest.mark.asyncio
async def test_delete_category_with_devices(async_client: AsyncClient, admin_headers, test_category):
    # Create device in category
    await async_client.post("/api/devices/", json={"device_name": "Dev", "ip_address": "10.0.0.1", "category_id": test_category.id}, headers=admin_headers)
    # Attempt to delete
    response = await async_client.delete(f"/api/categories/{test_category.id}", headers=admin_headers)
    assert response.status_code == 422
