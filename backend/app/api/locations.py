from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.location import LocationCreate, LocationUpdate, LocationRead
from app.schemas.common import MessageResponse
from app.services.location_service import LocationService
from app.api.deps import get_current_user, require_admin
from typing import List

router = APIRouter(prefix="/api/locations", tags=["Locations"])

@router.get("", response_model=List[LocationRead])
@router.get("/", response_model=List[LocationRead], include_in_schema=False)
async def list_locations(db: AsyncSession = Depends(get_db), _ = Depends(get_current_user)):
    return await LocationService.get_all(db)

@router.post("", response_model=LocationRead)
@router.post("/", response_model=LocationRead, include_in_schema=False)
async def create_location(data: LocationCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await LocationService.create(db, data)

@router.put("/{id}", response_model=LocationRead)
async def update_location(id: int, data: LocationUpdate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    return await LocationService.update(db, id, data)

@router.delete("/{id}", response_model=MessageResponse)
async def delete_location(id: int, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    await LocationService.delete(db, id)
    return MessageResponse(message="Location deleted successfully")
