import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, admin_user):
    response = await async_client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, admin_user):
    response = await async_client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    response = await async_client.post("/api/auth/login", json={"username": "nobody", "password": "password"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me_authenticated(async_client: AsyncClient, admin_headers):
    response = await async_client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"

@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client: AsyncClient):
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient, admin_user):
    login_response = await async_client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    refresh_token = login_response.json()["refresh_token"]
    
    response = await async_client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()
