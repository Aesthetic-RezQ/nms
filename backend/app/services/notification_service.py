import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification_log import NotificationLog
from app.models.system_setting import SystemSetting
from app.services.incident_service import format_duration

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
        down_str = down_since.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(down_since, datetime) else str(down_since or "Now")
        
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
        rec_str = rec_at.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(rec_at, datetime) else str(rec_at or "Now")
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
    async def send_telegram(bot_token: str, chat_id: str, message: str) -> tuple[bool, Optional[str]]:
        """Send message via Telegram Bot API using httpx."""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return True, None
                else:
                    return False, f"Telegram API error ({resp.status_code}): {resp.text}"
        except Exception as e:
            return False, f"Telegram connection error: {str(e)}"

    @staticmethod
    def _send_smtp_sync(
        host: str,
        port: int,
        user: Optional[str],
        password: Optional[str],
        from_email: str,
        to_email: str,
        subject: str,
        body: str
    ) -> tuple[bool, Optional[str]]:
        try:
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(host, port, timeout=10)
            try:
                server.starttls()
            except Exception:
                pass  # Ignore if STARTTLS not supported (e.g. local relay)

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
        Dispatch notification across all enabled channels (Telegram, Email) and log result.
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

        # 1. Telegram Dispatch
        tg_enabled = settings.get("telegram_enabled", "").lower() in ("true", "1", "yes")
        bot_token = settings.get("telegram_bot_token")
        chat_id = settings.get("telegram_chat_id")

        if tg_enabled and bot_token and chat_id:
            success, err = await NotificationService.send_telegram(bot_token, chat_id, message)
            log = NotificationLog(
                incident_id=incident_id,
                device_id=device_id,
                channel="TELEGRAM",
                recipient=chat_id,
                event_type=event_type,
                subject=subject,
                message_body=message,
                status="SENT" if success else "FAILED",
                error_message=err
            )
            db.add(log)

        # 2. Email SMTP Dispatch
        smtp_enabled = settings.get("smtp_enabled", "").lower() in ("true", "1", "yes")
        smtp_host = settings.get("smtp_host")
        smtp_port = int(settings.get("smtp_port", "587"))
        smtp_user = settings.get("smtp_user")
        smtp_pass = settings.get("smtp_password")
        smtp_from = settings.get("smtp_from_email", "nms-alert@local")
        smtp_to = settings.get("smtp_to_emails")

        if smtp_enabled and smtp_host and smtp_to:
            recipients = [r.strip() for r in smtp_to.split(",") if r.strip()]
            for to_addr in recipients:
                success, err = await NotificationService.send_email(
                    smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, to_addr, subject, message
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
