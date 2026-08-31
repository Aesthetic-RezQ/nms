from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from app.core.exceptions import DuplicateException, ValidationException, NotFoundException, ForbiddenException
from uuid import UUID
import math

class UserService:
    @staticmethod
    async def get_all(db: AsyncSession, page: int = 1, page_size: int = 10):
        count_query = select(func.count(User.id))
        result = await db.execute(count_query)
        total = result.scalar() or 0
        
        query = select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        users = result.scalars().all()
        
        return {
            "data": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise NotFoundException("User not found")
        return user

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate):
        result = await db.execute(select(User).where(or_(User.username == user_data.username, User.email == user_data.email)))
        if result.scalars().first():
            raise DuplicateException("Username or email already exists")
            
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user_id: UUID, user_data: UserUpdate):
        user = await UserService.get_by_id(db, user_id)
        
        if user_data.email and user_data.email != user.email:
            result = await db.execute(select(User).where(User.email == user_data.email))
            if result.scalars().first():
                raise DuplicateException("Email already exists")
            user.email = user_data.email
            
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
            
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID):
        user = await UserService.get_by_id(db, user_id)
        if user.role == "admin":
            result = await db.execute(select(func.count(User.id)).where(User.role == "admin"))
            if result.scalar() <= 1:
                raise ForbiddenException("Cannot delete the last admin user")
        
        await db.delete(user)
        await db.commit()
        
    @staticmethod
    async def change_password(db: AsyncSession, user_id: UUID, current_password: str, new_password: str):
        user = await UserService.get_by_id(db, user_id)
        if not verify_password(current_password, user.password_hash):
            raise ValidationException("Incorrect current password")
            
        user.password_hash = hash_password(new_password)
        await db.commit()
