from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.user_service import UserService
from app.api.deps import require_admin
from uuid import UUID

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("", response_model=PaginatedResponse[UserRead])
@router.get("/", response_model=PaginatedResponse[UserRead], include_in_schema=False)
async def list_users(page: int = 1, page_size: int = 10, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await UserService.get_all(db, page, page_size)

@router.post("", response_model=UserRead)
@router.post("/", response_model=UserRead, include_in_schema=False)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    raise HTTPException(status_code=410, detail="User administration is managed in CentralAuth")

@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await UserService.get_by_id(db, user_id)

@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: UUID, user_data: UserUpdate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    raise HTTPException(status_code=410, detail="User administration is managed in CentralAuth")

@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    raise HTTPException(status_code=410, detail="User administration is managed in CentralAuth")
