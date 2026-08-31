from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserProfile
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user
from app.core.security import decode_token
from uuid import UUID

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await AuthService.authenticate(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        
    await AuditService.create_log(db, user_id=user.id, username=user.username, action="USER_LOGIN")
    return AuthService.create_tokens(user.id, user.username, user.role)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    user_id = UUID(payload.get("sub"))
    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    return AuthService.create_tokens(user.id, user.username, user.role)

@router.get("/me", response_model=UserProfile)
async def get_me(current_user = Depends(get_current_user)):
    return current_user
