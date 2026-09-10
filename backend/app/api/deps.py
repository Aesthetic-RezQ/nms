from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import secrets

from app.core.security import hash_password
from app.database import get_db
from app.models.user import User
from app.services.central_auth_service import CentralAuthError, CentralAuthUnavailable, CentralIdentity, central_auth

bearer = HTTPBearer(auto_error=False)


def _auth_error(error: CentralAuthError) -> HTTPException:
    if isinstance(error, CentralAuthUnavailable):
        return HTTPException(status_code=503, detail="Central Authentication Service is unavailable")
    if error.status_code == 403:
        return HTTPException(status_code=403, detail="NMS application access denied")
    return HTTPException(status_code=401, detail="Invalid or expired CentralAuth session")


async def _sync_identity(db: AsyncSession, identity: CentralIdentity) -> User:
    """Cache display data and preserve a stable CentralAuth UUID mapping."""
    try:
        UUID(identity.id)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="CentralAuth returned an invalid user id") from exc

    result = await db.execute(select(User).where(User.central_user_id == identity.id))
    user = result.scalars().first()
    if user is None:
        result = await db.execute(select(User).where(User.username == identity.username))
        user = result.scalars().first()
        if user is not None and user.central_user_id not in (None, identity.id):
            raise HTTPException(status_code=409, detail="NMS identity mapping conflict")

    email = identity.email
    if email:
        email_result = await db.execute(select(User).where(User.email == email))
        email_owner = email_result.scalars().first()
        if email_owner is not None and (user is None or email_owner.id != user.id):
            # Preserve the cached identity even if a legacy row already owns
            # the address; CentralAuth remains authoritative for the email.
            email = None

    if user is None:
        user = User(
            username=identity.username,
            email=email or f"{identity.username}@central-auth.invalid",
            password_hash=hash_password(secrets.token_urlsafe(32)),
            full_name=identity.full_name,
            role=identity.role,
            is_active=identity.status == "active",
            central_user_id=identity.id,
        )
        db.add(user)
    else:
        user.central_user_id = identity.id
        user.username = identity.username
        user.email = email or user.email
        user.full_name = identity.full_name
        user.role = identity.role
        user.is_active = identity.status == "active"

    user.permissions = identity.permissions
    await db.commit()
    return user


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("nms_access_token") or (credentials.credentials if credentials else None)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        identity = await central_auth.identity(token)
        if identity.status != "active":
            raise HTTPException(status_code=401, detail="CentralAuth user is disabled")
        return await _sync_identity(db, identity)
    except HTTPException:
        raise
    except CentralAuthError as error:
        raise _auth_error(error)


class RoleChecker:
    def __init__(self, allowed_roles: List[str], permissions: tuple[str, ...] = ()):
        self.allowed_roles = allowed_roles
        self.permissions = permissions

    async def __call__(self, user: User = Depends(get_current_user)):
        user_permissions = set(getattr(user, "permissions", ()))
        if user.role in self.allowed_roles or user_permissions.intersection(self.permissions):
            return user
        raise HTTPException(status_code=403, detail="Operation not permitted for this NMS role")


require_admin = RoleChecker(["NMS_ADMIN", "admin"], ("nms.config.manage", "nms.device.delete"))
require_operator_or_admin = RoleChecker(
    ["NMS_ADMIN", "NMS_OPERATOR", "admin", "operator"],
    ("nms.alert.manage", "nms.device.edit"),
)
