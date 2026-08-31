from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.maintenance import MaintenanceWindowCreate, MaintenanceWindowUpdate, MaintenanceWindowRead
from app.services.maintenance_service import MaintenanceService
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance Windows"])

@router.get("", response_model=List[MaintenanceWindowRead])
@router.get("/", response_model=List[MaintenanceWindowRead], include_in_schema=False)
async def list_maintenance_windows(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all scheduled and manual maintenance windows."""
    return await MaintenanceService.get_all(db)

@router.get("/{window_id}", response_model=MaintenanceWindowRead)
async def get_maintenance_window(
    window_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get single maintenance window details."""
    return await MaintenanceService.get_by_id(db, window_id)

@router.post("", response_model=MaintenanceWindowRead)
@router.post("/", response_model=MaintenanceWindowRead, include_in_schema=False)
async def create_maintenance_window(
    request: MaintenanceWindowCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Create a new maintenance window (Admin only)."""
    return await MaintenanceService.create(
        db=db,
        data=request,
        user_id=current_user.id,
        username=current_user.username
    )

@router.put("/{window_id}", response_model=MaintenanceWindowRead)
async def update_maintenance_window(
    window_id: UUID,
    request: MaintenanceWindowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update an existing maintenance window (Admin only)."""
    return await MaintenanceService.update(
        db=db,
        window_id=window_id,
        data=request,
        user_id=current_user.id,
        username=current_user.username
    )

@router.delete("/{window_id}")
async def delete_maintenance_window(
    window_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Delete a maintenance window (Admin only)."""
    await MaintenanceService.delete(
        db=db,
        window_id=window_id,
        user_id=current_user.id,
        username=current_user.username
    )
    return {"message": "Maintenance window deleted successfully"}
