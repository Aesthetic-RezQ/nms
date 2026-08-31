from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.schemas.incident import (
    IncidentRead, IncidentAcknowledgeRequest, IncidentNoteRequest, IncidentListFilter
)
from app.schemas.common import PaginatedResponse
from app.services.incident_service import IncidentService
from app.api.deps import get_current_user, require_operator_or_admin

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])
device_incidents_router = APIRouter(prefix="/api/devices", tags=["Device Incidents"])

@router.get("", response_model=dict)
@router.get("/", response_model=dict, include_in_schema=False)
async def list_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: Optional[str] = Query(default=None, regex="^(OPEN|ACKNOWLEDGED|RESOLVED)$"),
    device_id: Optional[UUID] = Query(default=None),
    is_acknowledged: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List incidents with filtering and pagination."""
    filters = IncidentListFilter(
        status=status,
        device_id=device_id,
        is_acknowledged=is_acknowledged,
        search=search
    )
    return await IncidentService.get_all(db=db, page=page, page_size=page_size, filters=filters)

@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get single incident details."""
    return await IncidentService.get_by_id(db=db, incident_id=incident_id)

@router.post("/{incident_id}/acknowledge", response_model=IncidentRead)
async def acknowledge_incident(
    incident_id: UUID,
    request: IncidentAcknowledgeRequest = IncidentAcknowledgeRequest(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_operator_or_admin)
):
    """Acknowledge an open incident (Requires Operator or Admin role)."""
    return await IncidentService.acknowledge(
        db=db,
        incident_id=incident_id,
        user_id=current_user.id,
        username=current_user.username,
        notes=request.notes
    )

@router.post("/{incident_id}/notes", response_model=IncidentRead)
async def add_incident_note(
    incident_id: UUID,
    request: IncidentNoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_operator_or_admin)
):
    """Add a troubleshooting note to an incident."""
    return await IncidentService.add_note(
        db=db,
        incident_id=incident_id,
        user_id=current_user.id,
        username=current_user.username,
        notes=request.notes
    )

@device_incidents_router.get("/{device_id}/incidents", response_model=dict)
async def get_device_incidents(
    device_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get incidents for a specific device."""
    filters = IncidentListFilter(device_id=device_id, status=status)
    return await IncidentService.get_all(db=db, page=page, page_size=page_size, filters=filters)
