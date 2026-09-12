import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification_log import NotificationLog
from app.models.system_setting import SystemSetting
from app.services.incident_service import format_duration
from app.core.time import format_app_datetime

logger = logging.getLogger("nms.notifications")

class NotificationService:
    @staticmethod
    async def get_settings_map(db: AsyncSession) -> Dict[str, str]:
        res = await db.execute(select(SystemSetting))
        rows = res.scalars().all()
        return {row.key: row.value for row in rows}

    @staticmethod
    def format_down_message(device_dict: dict, incident_dict: dict) -> str:
        down_since = incident_dict.get("down_since")
        down_str = format_app_datetime(down_since) if isinstance(down_since, datetime) else str(down_since or "Now")
        
        return (
            f"🚨 NETWORK ALERT: Device DOWN\n\n"
            f"Device: {device_dict.get('device_name', 'Unknown')}\n"
            f"IP Address: {device_dict.get('ip_address', 'Unknown')}\n"
            f"Location: {device_dict.get('location_name', 'Unassigned')}\n"
            f"Category: {device_dict.get('category_name', 'Unassigned')}\n\n"
            f"Status: DOWN\n"
            f"Down Since: {down_str}\n"
            f"Reason: {incident_dict.get('failure_reason', 'Consecutive ping failures')}\n"
        )

    @staticmethod
    def format_recovery_message(device_dict: dict, incident_dict: dict) -> str:
        rec_at = incident_dict.get("recovered_at")
        rec_str = format_app_datetime(rec_at) if isinstance(rec_at, datetime) else str(rec_at or "Now")
        duration_sec = incident_dict.get("duration_seconds")
        duration_str = format_duration(duration_sec) or "0s"

        return (
            f"✅ NETWORK RECOVERY: Device UP\n\n"
            f"Device: {device_dict.get('device_name', 'Unknown')}\n"
            f"IP Address: {device_dict.get('ip_address', 'Unknown')}\n"
            f"Location: {device_dict.get('location_name', 'Unassigned')}\n\n"
            f"Status: UP (Recovered)\n"
            f"Recovered At: {rec_str}\n"
            f"Total Downtime: {duration_str}\n"
        )

    @staticmethod
    @staticmethod
    def _send_smtp_sync(
        host: str,
        port: int,
        user: Optional[str],
        password: Optional[str],
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        encryption: str = "TLS",
        sender_name: str = "NMS",
        reply_to: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{sender_name} <{from_email}>" if sender_name else from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to
            msg.attach(MIMEText(body, "plain"))

            if str(encryption).upper() == "SSL":
                server = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
                if str(encryption).upper() in ("TLS", "STARTTLS"):
                    server.starttls()

            if user and password:
                server.login(user, password)

            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()
            return True, None
        except Exception as e:
            return False, f"SMTP Error: {str(e)}"

    @staticmethod
    async def send_email(
        host: str,
        port: int,
        user: Optional[str],
        password: Optional[str],
        from_email: str,
        to_email: str,
        subject: str,
        body: str
    ) -> tuple[bool, Optional[str]]:
        """Send email asynchronously using thread executor."""
        return await asyncio.to_thread(
            NotificationService._send_smtp_sync,
            host, port, user, password, from_email, to_email, subject, body
        )

    @staticmethod
    async def dispatch_alert(
        db: AsyncSession,
        event_type: str,  # DOWN or RECOVERY
        device_dict: dict,
        incident_dict: dict
    ):
        """
        Dispatch an email notification and log the result. Email is the only supported channel.
        """
        settings = await NotificationService.get_settings_map(db)
        
        # Message content
        if event_type == "DOWN":
            subject = f"[NMS ALERT] {device_dict.get('device_name')} is DOWN"
            message = NotificationService.format_down_message(device_dict, incident_dict)
        else:
            subject = f"[NMS RECOVERY] {device_dict.get('device_name')} has RECOVERED"
            message = NotificationService.format_recovery_message(device_dict, incident_dict)

        incident_id = incident_dict.get("id")
        device_id = device_dict.get("id")

        # Email SMTP Dispatch
        email_enabled = settings.get("email_notifications_enabled", settings.get("smtp_enabled", "false")).lower() in ("true", "1", "yes")
        smtp_enabled = settings.get("smtp_enabled", "").lower() in ("true", "1", "yes")
        if event_type == "DOWN":
            email_enabled = email_enabled and settings.get("down_notifications_enabled", "true").lower() in ("true", "1", "yes")
        elif event_type == "RECOVERY":
            email_enabled = email_enabled and settings.get("recovery_notifications_enabled", "true").lower() in ("true", "1", "yes")
        smtp_host = settings.get("smtp_host")
        smtp_port = int(settings.get("smtp_port", "587"))
        smtp_user = settings.get("smtp_user")
        smtp_pass = settings.get("smtp_password")
        smtp_from = settings.get("smtp_from_email", "nms-alert@local")
        smtp_to = settings.get("smtp_to_emails")
        smtp_encryption = settings.get("smtp_encryption", "TLS")
        sender_name = settings.get("smtp_sender_name", "NMS")
        reply_to = settings.get("smtp_reply_to") or None

        if email_enabled and smtp_enabled and smtp_host and smtp_to:
            recipients = [r.strip() for r in smtp_to.split(",") if r.strip()]
            for to_addr in recipients:
                success, err = await NotificationService.send_email(
                    smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, to_addr, subject, message,
                    smtp_encryption, sender_name, reply_to
                )
                log = NotificationLog(
                    incident_id=incident_id,
                    device_id=device_id,
                    channel="EMAIL",
                    recipient=to_addr,
                    event_type=event_type,
                    subject=subject,
                    message_body=message,
                    status="SENT" if success else "FAILED",
                    error_message=err
                )
                db.add(log)

        await db.commit()
