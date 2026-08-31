from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.group import GroupCreate, GroupUpdate, GroupRead
from app.schemas.common import MessageResponse
from app.services.group_service import GroupService
from app.api.deps import get_current_user, require_admin
from typing import List

router = APIRouter(prefix="/api/groups", tags=["Groups"])

@router.get("", response_model=List[GroupRead])
@router.get("/", response_model=List[GroupRead], include_in_schema=False)
async def list_groups(db: AsyncSession = Depends(get_db), _ = Depends(get_current_user)):
    return await GroupService.get_all(db)

@router.post("", response_model=GroupRead)
@router.post("/", response_model=GroupRead, include_in_schema=False)
async def create_group(data: GroupCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await GroupService.create(db, data)

@router.put("/{id}", response_model=GroupRead)
async def update_group(id: int, data: GroupUpdate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await GroupService.update(db, id, data)

@router.delete("/{id}", response_model=MessageResponse)
async def delete_group(id: int, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    await GroupService.delete(db, id)
    return MessageResponse(message="Group deleted successfully")
