from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.schemas.incident import (
    IncidentRead, IncidentAcknowledgeRequest, IncidentNoteRequest, IncidentListFilter
)
from app.schemas.notification import IncidentEmailResponse
from app.schemas.common import PaginatedResponse
from app.services.incident_service import IncidentService
from app.services.notification_service import NotificationService
from app.models.notification_log import NotificationLog
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

@router.post("/{incident_id}/email", response_model=IncidentEmailResponse)
async def email_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_operator_or_admin)
):
    """Send the configured SMTP alert recipients an email for one incident."""
    incident = await IncidentService.get_by_id(db=db, incident_id=incident_id)
    settings = await NotificationService.get_settings_map(db)

    smtp_enabled = settings.get("smtp_enabled", "").lower() in ("true", "1", "yes")
    smtp_host = settings.get("smtp_host")
    smtp_to = settings.get("smtp_to_emails", "")
    recipients = [address.strip() for address in smtp_to.split(",") if address.strip()]
    if not smtp_enabled or not smtp_host or not recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enable SMTP and configure an SMTP host and recipient email address first."
        )

    smtp_port = int(settings.get("smtp_port", "587"))
    smtp_user = settings.get("smtp_user")
    smtp_password = settings.get("smtp_password")
    smtp_from = settings.get("smtp_from_email", "nms-alert@local")
    device = {
        "id": incident["device_id"],
        "device_name": incident["device_name"],
        "ip_address": incident["ip_address"],
        "location_name": incident["location_name"],
        "category_name": incident["category_name"],
    }
    is_resolved = incident["status"] == "RESOLVED"
    event_type = "MANUAL_RECOVERY" if is_resolved else "MANUAL_ALERT"
    subject = (
        f"[NMS RECOVERY] {incident['device_name']} has recovered"
        if is_resolved else
        f"[NMS ALERT] {incident['device_name']} incident notification"
    )
    message_body = (
        NotificationService.format_recovery_message(device, incident)
        if is_resolved else
        NotificationService.format_down_message(device, incident)
    )

    sent_to = []
    failed = []
    for recipient in recipients:
        success, error = await NotificationService.send_email(
            smtp_host, smtp_port, smtp_user, smtp_password,
            smtp_from, recipient, subject, message_body
        )
        db.add(NotificationLog(
            incident_id=incident_id,
            device_id=incident["device_id"],
            channel="EMAIL",
            recipient=recipient,
            event_type=event_type,
            subject=subject,
            message_body=message_body,
            status="SENT" if success else "FAILED",
            error_message=error,
        ))
        (sent_to if success else failed).append(recipient)

    await db.commit()
    if not sent_to:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Email alert could not be sent.")

    return IncidentEmailResponse(
        success=not failed,
        incident_id=incident_id,
        sent_to=sent_to,
        failed=failed,
        message=f"Incident email sent to {', '.join(sent_to)}."
        if not failed else
        f"Incident email sent to {', '.join(sent_to)}; {len(failed)} recipient(s) failed."
    )

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
