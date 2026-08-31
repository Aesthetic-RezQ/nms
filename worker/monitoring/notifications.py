"""
Worker-side notification dispatcher.
Self-contained: does NOT import any FastAPI backend modules.
Sends Telegram and Email alerts directly using httpx and smtplib.
"""
import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger("nms.worker.notifications")


def _format_duration(seconds: Optional[int]) -> str:
    if seconds is None or seconds < 0:
        return "0s"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def _format_down_message(device_dict: dict, incident_dict: dict) -> str:
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


def _format_recovery_message(device_dict: dict, incident_dict: dict) -> str:
    rec_at = incident_dict.get("recovered_at")
    rec_str = rec_at.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(rec_at, datetime) else str(rec_at or "Now")
    duration_str = _format_duration(incident_dict.get("duration_seconds"))
    return (
        f"✅ NETWORK RECOVERY: Device UP\n\n"
        f"Device: {device_dict.get('device_name', 'Unknown')}\n"
        f"IP Address: {device_dict.get('ip_address', 'Unknown')}\n"
        f"Location: {device_dict.get('location_name', 'Unassigned')}\n\n"
        f"Status: UP (Recovered)\n"
        f"Recovered At: {rec_str}\n"
        f"Total Downtime: {duration_str}\n"
    )


async def _get_settings(db: AsyncSession) -> Dict[str, str]:
    # Import here to avoid circular imports at module load time
    from app.models.system_setting import SystemSetting
    res = await db.execute(select(SystemSetting))
    return {row.key: row.value for row in res.scalars().all()}


async def _send_telegram(bot_token: str, chat_id: str, message: str) -> tuple[bool, Optional[str]]:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": message})
            if resp.status_code == 200:
                return True, None
            return False, f"Telegram API error ({resp.status_code}): {resp.text}"
    except Exception as e:
        return False, f"Telegram connection error: {str(e)}"


def _send_smtp_sync(host, port, user, password, from_email, to_email, subject, body) -> tuple[bool, Optional[str]]:
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
            pass
        if user and password:
            server.login(user, password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        return False, f"SMTP Error: {str(e)}"


async def _dispatch_alert(db: AsyncSession, event_type: str, device_dict: dict, incident_dict: dict):
    """Core dispatcher — sends notifications and logs results without importing FastAPI."""
    try:
        from app.models.notification_log import NotificationLog
        settings = await _get_settings(db)
    except Exception as e:
        logger.warning(f"Could not load settings for notification dispatch: {e}")
        return

    if event_type == "DOWN":
        subject = f"[NMS ALERT] {device_dict.get('device_name')} is DOWN"
        message = _format_down_message(device_dict, incident_dict)
    else:
        subject = f"[NMS RECOVERY] {device_dict.get('device_name')} has RECOVERED"
        message = _format_recovery_message(device_dict, incident_dict)

    incident_id = incident_dict.get("id")
    device_id = device_dict.get("id")

    # Telegram
    tg_enabled = settings.get("telegram_enabled", "").lower() in ("true", "1", "yes")
    bot_token = settings.get("telegram_bot_token")
    chat_id = settings.get("telegram_chat_id")
    if tg_enabled and bot_token and chat_id:
        success, err = await _send_telegram(bot_token, chat_id, message)
        db.add(NotificationLog(
            incident_id=incident_id, device_id=device_id,
            channel="TELEGRAM", recipient=chat_id,
            event_type=event_type, subject=subject, message_body=message,
            status="SENT" if success else "FAILED", error_message=err
        ))
        logger.info(f"Telegram notification {'sent' if success else 'FAILED'}: {err or ''}")

    # Email SMTP
    smtp_enabled = settings.get("smtp_enabled", "").lower() in ("true", "1", "yes")
    smtp_host = settings.get("smtp_host")
    smtp_to = settings.get("smtp_to_emails")
    if smtp_enabled and smtp_host and smtp_to:
        smtp_port = int(settings.get("smtp_port", "587"))
        smtp_user = settings.get("smtp_user")
        smtp_pass = settings.get("smtp_password")
        smtp_from = settings.get("smtp_from_email", "nms-alert@local")
        for to_addr in [r.strip() for r in smtp_to.split(",") if r.strip()]:
            success, err = await asyncio.to_thread(
                _send_smtp_sync, smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, to_addr, subject, message
            )
            db.add(NotificationLog(
                incident_id=incident_id, device_id=device_id,
                channel="EMAIL", recipient=to_addr,
                event_type=event_type, subject=subject, message_body=message,
                status="SENT" if success else "FAILED", error_message=err
            ))

    await db.commit()


class WorkerNotifier:
    @staticmethod
    async def trigger_down_notification(db: AsyncSession, device_data: dict, incident_data: dict):
        try:
            await _dispatch_alert(db, "DOWN", device_data, incident_data)
        except Exception as e:
            logger.error(f"Failed to dispatch DOWN notification: {e}")

    @staticmethod
    async def trigger_recovery_notification(db: AsyncSession, device_data: dict, incident_data: dict):
        try:
            await _dispatch_alert(db, "RECOVERY", device_data, incident_data)
        except Exception as e:
            logger.error(f"Failed to dispatch RECOVERY notification: {e}")
