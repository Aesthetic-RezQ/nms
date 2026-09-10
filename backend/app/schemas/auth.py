from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None

class UserProfile(BaseModel):
    id: UUID
    central_user_id: Optional[UUID] = None
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    permissions: list[str] = []

class AuthSessionResponse(BaseModel):
    authenticated: bool = True
    user: Optional[UserProfile] = None
