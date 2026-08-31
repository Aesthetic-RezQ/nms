from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
import math
from datetime import datetime, timezone

from app.database import get_db
from app.models.notification_log import NotificationLog
from app.schemas.notification import NotificationLogRead, TestNotificationRequest, NotificationTestResponse
from app.services.notification_service import NotificationService
from app.api.deps import require_admin, get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/logs", response_model=dict)
async def list_notification_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    channel: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List notification logs with pagination and filters."""
    query = select(NotificationLog)
    if channel:
        query = query.where(NotificationLog.channel == channel)
    if status:
        query = query.where(NotificationLog.status == status)

    query = query.order_by(desc(NotificationLog.sent_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(query)
    logs = res.scalars().all()

    return {
        "data": [NotificationLogRead.model_validate(log).model_dump() for log in logs],
        "page": page,
        "page_size": page_size
    }

@router.post("/test", response_model=NotificationTestResponse)
async def test_notification(
    request: TestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Test sending a notification via Telegram or Email SMTP (Admin only).
    """
    settings = await NotificationService.get_settings_map(db)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    custom_msg = request.custom_message or "This is a test notification from the LAN Network Monitoring System."
    
    test_body = (
        f"🧪 NETWORK MONITORING TEST\n\n"
        f"Message: {custom_msg}\n"
        f"Channel: {request.channel}\n"
        f"Timestamp: {now_str}\n"
        f"Status: Configuration Verified"
    )

    channel_upper = request.channel.upper()

    if channel_upper == "TELEGRAM":
        bot_token = settings.get("telegram_bot_token")
        chat_id = request.recipient or settings.get("telegram_chat_id")

        if not bot_token or not chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram bot token and chat ID must be configured in settings."
            )

        success, error = await NotificationService.send_telegram(bot_token, chat_id, test_body)
        
        # Log result
        log = NotificationLog(
            channel="TELEGRAM",
            recipient=chat_id,
            event_type="TEST",
            subject="[TEST] Telegram Notification",
            message_body=test_body,
            status="SENT" if success else "FAILED",
            error_message=error
        )
        db.add(log)
        await db.commit()

        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Telegram test failed: {error}")

        return NotificationTestResponse(
            success=True,
            channel="TELEGRAM",
            recipient=chat_id,
            message="Telegram test message sent successfully!"
        )

    elif channel_upper == "EMAIL":
        smtp_host = settings.get("smtp_host")
        smtp_port = int(settings.get("smtp_port", "587"))
        smtp_user = settings.get("smtp_user")
        smtp_pass = settings.get("smtp_password")
        smtp_from = settings.get("smtp_from_email", "nms-alert@local")
        to_email = request.recipient or settings.get("smtp_to_emails", "").split(",")[0].strip()

        if not smtp_host or not to_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMTP host and recipient email address must be configured."
            )

        subject = "[TEST] LAN Network Monitoring Test Email"
        success, error = await NotificationService.send_email(
            smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, to_email, subject, test_body
        )

        log = NotificationLog(
            channel="EMAIL",
            recipient=to_email,
            event_type="TEST",
            subject=subject,
            message_body=test_body,
            status="SENT" if success else "FAILED",
            error_message=error
        )
        db.add(log)
        await db.commit()

        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Email test failed: {error}")

        return NotificationTestResponse(
            success=True,
            channel="EMAIL",
            recipient=to_email,
            message=f"Test email sent successfully to {to_email}!"
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported notification channel: {request.channel}. Use EMAIL or TELEGRAM."
        )
