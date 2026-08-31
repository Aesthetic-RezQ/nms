from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.schemas.auth import TokenResponse
from uuid import UUID

class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username, User.is_active == True))
        user = result.scalars().first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_tokens(user_id: UUID, username: str, role: str) -> TokenResponse:
        access_token = create_access_token(data={"sub": str(user_id), "username": username, "role": role})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
        return result.scalars().first()
