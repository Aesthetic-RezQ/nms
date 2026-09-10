"""HTTP client for the Central Authentication Service.

NMS deliberately has no credentials or database connection for CentralAuth.
This module is the only integration boundary for identity and authorization.
"""

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


class CentralAuthError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CentralAuthUnavailable(CentralAuthError):
    pass


@dataclass(frozen=True)
class CentralIdentity:
    id: str
    username: str
    email: str
    full_name: str | None
    status: str
    is_superadmin: bool
    permissions: frozenset[str]

    @property
    def role(self) -> str:
        """Return the NMS role label used by the existing UI and policies."""
        if self.is_superadmin or "nms.config.manage" in self.permissions:
            return "NMS_ADMIN"
        if "nms.alert.manage" in self.permissions or "nms.device.edit" in self.permissions:
            return "NMS_OPERATOR"
        return "NMS_VIEWER"


class CentralAuthClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.CENTRAL_AUTH_URL).rstrip("/")
        self.timeout = timeout or settings.CENTRAL_AUTH_TIMEOUT_SECONDS
        self.application_code = settings.CENTRAL_AUTH_APPLICATION_CODE

    async def _request(self, method: str, path: str, *, token: str | None = None,
                       json: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"X-Application-Code": self.application_code}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, headers=headers, json=json)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise CentralAuthUnavailable("Central Authentication Service is unavailable") from exc

        if response.status_code >= 400:
            detail: str | None = None
            try:
                body = response.json()
                detail = body.get("detail") if isinstance(body, dict) else None
            except ValueError:
                pass
            raise CentralAuthError(detail or "Central Authentication request failed", response.status_code)
        try:
            payload = response.json()
        except ValueError as exc:
            raise CentralAuthError("Central Authentication returned an invalid response", response.status_code) from exc
        return payload

    async def login(self, username: str, password: str) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/auth/login", json={
            "username": username,
            "password": password,
            "application_code": self.application_code,
        })

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    async def logout(self, access_token: str, refresh_token: str) -> None:
        await self._request("POST", "/api/v1/auth/logout", token=access_token, json={"refresh_token": refresh_token})

    async def identity(self, access_token: str) -> CentralIdentity:
        profile = await self._request("GET", "/api/v1/auth/me", token=access_token)
        permission_data = await self._request("GET", "/api/v1/auth/permissions", token=access_token)
        return CentralIdentity(
            id=str(profile["id"]),
            username=profile["username"],
            email=profile.get("email", ""),
            full_name=profile.get("full_name"),
            status=profile.get("status", "active"),
            is_superadmin=bool(profile.get("is_superadmin", False)),
            permissions=frozenset(permission_data.get("permissions", [])),
        )


central_auth = CentralAuthClient()
