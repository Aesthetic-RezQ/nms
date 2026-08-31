from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead
from app.schemas.common import MessageResponse
from app.services.category_service import CategoryService
from app.api.deps import get_current_user, require_admin
from typing import List

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryRead])
@router.get("/", response_model=List[CategoryRead], include_in_schema=False)
async def list_categories(db: AsyncSession = Depends(get_db), _ = Depends(get_current_user)):
    return await CategoryService.get_all(db)

@router.post("", response_model=CategoryRead)
@router.post("/", response_model=CategoryRead, include_in_schema=False)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await CategoryService.create(db, data)

@router.put("/{id}", response_model=CategoryRead)
async def update_category(id: int, data: CategoryUpdate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await CategoryService.update(db, id, data)

@router.delete("/{id}", response_model=MessageResponse)
async def delete_category(id: int, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    await CategoryService.delete(db, id)
    return MessageResponse(message="Category deleted successfully")

