from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import _sync_identity, get_current_user
from app.config import settings
from app.database import get_db
from app.schemas.auth import AuthSessionResponse, LoginRequest, RefreshRequest, UserProfile
from app.services.audit_service import AuditService
from app.services.central_auth_service import CentralAuthError, CentralAuthUnavailable, central_auth

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _set_session_cookies(response: Response, tokens: dict):
    common = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "domain": settings.AUTH_COOKIE_DOMAIN,
        "path": "/",
    }
    response.set_cookie("nms_access_token", tokens["access_token"], max_age=int(tokens.get("expires_in", 600)), **common)
    response.set_cookie("nms_refresh_token", tokens["refresh_token"], max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **common)


def _clear_session_cookies(response: Response):
    response.delete_cookie("nms_access_token", path="/", domain=settings.AUTH_COOKIE_DOMAIN)
    response.delete_cookie("nms_refresh_token", path="/", domain=settings.AUTH_COOKIE_DOMAIN)


def _profile(user) -> UserProfile:
    return UserProfile(
        id=user.id,
        central_user_id=UUID(user.central_user_id) if user.central_user_id else None,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        permissions=sorted(getattr(user, "permissions", ())),
    )


def _central_error(error: CentralAuthError) -> HTTPException:
    if isinstance(error, CentralAuthUnavailable):
        return HTTPException(status_code=503, detail="Central Authentication Service is unavailable")
    if error.status_code == 403:
        return HTTPException(status_code=403, detail="NMS application access denied")
    return HTTPException(status_code=401, detail="Incorrect username or password")


@router.post("/login", response_model=AuthSessionResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    try:
        tokens = await central_auth.login(payload.username, payload.password)
        identity = await central_auth.identity(tokens["access_token"])
        user = await _sync_identity(db, identity)
    except CentralAuthError as error:
        raise _central_error(error)
    _set_session_cookies(response, tokens)
    await AuditService.create_log(db, user_id=user.id, username=user.username, action="USER_LOGIN")
    return AuthSessionResponse(user=_profile(user))


@router.post("/refresh", response_model=AuthSessionResponse)
async def refresh_token(request: Request, response: Response, payload: RefreshRequest | None = None, db: AsyncSession = Depends(get_db)):
    refresh = (payload.refresh_token if payload else None) or request.cookies.get("nms_refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="Session refresh required")
    try:
        tokens = await central_auth.refresh(refresh)
        identity = await central_auth.identity(tokens["access_token"])
        user = await _sync_identity(db, identity)
    except CentralAuthError as error:
        _clear_session_cookies(response)
        raise _central_error(error)
    _set_session_cookies(response, tokens)
    return AuthSessionResponse(user=_profile(user))


@router.get("/me", response_model=UserProfile)
async def get_me(current_user=Depends(get_current_user)):
    return _profile(current_user)


@router.post("/logout")
async def logout(request: Request, response: Response):
    access = request.cookies.get("nms_access_token")
    refresh = request.cookies.get("nms_refresh_token")
    if access and refresh:
        try:
            await central_auth.logout(access, refresh)
        except CentralAuthError:
            # Clear NMS cookies even if CentralAuth has already revoked the
            # token or is temporarily unavailable.
            pass
    _clear_session_cookies(response)
    return {"message": "Logged out"}
