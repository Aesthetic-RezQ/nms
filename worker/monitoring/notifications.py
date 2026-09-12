"""
Worker-side email notification dispatcher.
Self-contained: does NOT import any FastAPI backend modules.
Email is the only supported notification channel.
"""
import asyncio
import logging
import smtplib
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger("nms.worker.notifications")


def _app_timezone():
    try:
        return ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Jakarta"))
    except Exception:
        return ZoneInfo("UTC")


def _format_app_datetime(value: Optional[datetime]) -> str:
    if not isinstance(value, datetime):
        return str(value or "Now")
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    return value.astimezone(_app_timezone()).strftime("%Y-%m-%d %H:%M:%S %Z")


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
    down_str = _format_app_datetime(down_since)
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
    rec_str = _format_app_datetime(rec_at)
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


def _format_warning_message(device_dict: dict, incident_dict: dict) -> str:
    return (
        f"⚠️ NETWORK WARNING: Device performance degraded\n\n"
        f"Device: {device_dict.get('device_name', 'Unknown')}\n"
        f"IP Address: {device_dict.get('ip_address', 'Unknown')}\n"
        f"Location: {device_dict.get('location_name', 'Unassigned')}\n"
        f"Category: {device_dict.get('category_name', 'Unassigned')}\n\n"
        f"Status: DEGRADED\n"
        f"Latency: {device_dict.get('current_latency', 'n/a')} ms\n"
        f"Reason: {incident_dict.get('failure_reason', 'Latency or packet loss threshold exceeded')}\n"
    )


def _format_reminder_message(device_dict: dict, incident_dict: dict) -> str:
    return (
        f"⏰ NETWORK REMINDER: Device remains DOWN\n\n"
        f"Device: {device_dict.get('device_name', 'Unknown')}\n"
        f"IP Address: {device_dict.get('ip_address', 'Unknown')}\n"
        f"Location: {device_dict.get('location_name', 'Unassigned')}\n\n"
        f"Status: DOWN\n"
        f"Down Since: {_format_app_datetime(incident_dict.get('down_since'))}\n"
        f"Reminder: {incident_dict.get('reminder_number', 1)}\n"
    )


async def _get_settings(db: AsyncSession) -> Dict[str, str]:
    # Import here to avoid circular imports at module load time
    from app.models.system_setting import SystemSetting
    res = await db.execute(select(SystemSetting))
    return {row.key: row.value for row in res.scalars().all()}


def _send_smtp_sync(host, port, user, password, from_email, to_email, subject, body,
                    encryption="TLS", sender_name="NMS", reply_to=None) -> tuple[bool, Optional[str]]:
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
    elif event_type == "WARNING":
        subject = f"[NMS WARNING] {device_dict.get('device_name')} is DEGRADED"
        message = _format_warning_message(device_dict, incident_dict)
    elif event_type == "REMINDER":
        subject = f"[NMS REMINDER] {device_dict.get('device_name')} remains DOWN"
        message = _format_reminder_message(device_dict, incident_dict)
    else:
        subject = f"[NMS RECOVERY] {device_dict.get('device_name')} has RECOVERED"
        message = _format_recovery_message(device_dict, incident_dict)

    incident_id = incident_dict.get("id")
    device_id = device_dict.get("id")

    # Email SMTP is the only supported channel.
    email_enabled = settings.get("email_notifications_enabled", settings.get("smtp_enabled", "false")).lower() in ("true", "1", "yes")
    if event_type == "DOWN" and settings.get("down_notifications_enabled", "true").lower() not in ("true", "1", "yes"):
        email_enabled = False
    if event_type == "RECOVERY" and settings.get("recovery_notifications_enabled", "true").lower() not in ("true", "1", "yes"):
        email_enabled = False
    if event_type == "WARNING" and settings.get("degraded_notifications_enabled", "true").lower() not in ("true", "1", "yes"):
        email_enabled = False
    if event_type == "REMINDER" and settings.get("reminder_notifications_enabled", "true").lower() not in ("true", "1", "yes"):
        email_enabled = False
    smtp_enabled = settings.get("smtp_enabled", "").lower() in ("true", "1", "yes")
    smtp_host = settings.get("smtp_host")
    smtp_to = settings.get("smtp_to_emails")
    if email_enabled and smtp_enabled and smtp_host and smtp_to:
        smtp_port = int(settings.get("smtp_port", "587"))
        smtp_user = settings.get("smtp_user")
        smtp_pass = settings.get("smtp_password")
        smtp_from = settings.get("smtp_from_email", "nms-alert@local")
        smtp_encryption = settings.get("smtp_encryption", "TLS")
        sender_name = settings.get("smtp_sender_name", "NMS")
        reply_to = settings.get("smtp_reply_to") or None
        for to_addr in [r.strip() for r in smtp_to.split(",") if r.strip()]:
            success, err = await asyncio.to_thread(
                _send_smtp_sync, smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, to_addr, subject, message,
                smtp_encryption, sender_name, reply_to
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

    @staticmethod
    async def trigger_warning_notification(db: AsyncSession, device_data: dict, incident_data: dict):
        try:
            await _dispatch_alert(db, "WARNING", device_data, incident_data)
        except Exception as e:
            logger.error(f"Failed to dispatch WARNING notification: {e}")

    @staticmethod
    async def trigger_reminder_notification(db: AsyncSession, device_data: dict, incident_data: dict):
        try:
            await _dispatch_alert(db, "REMINDER", device_data, incident_data)
        except Exception as e:
            logger.error(f"Failed to dispatch REMINDER notification: {e}")
