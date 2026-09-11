from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import settings


def app_timezone() -> ZoneInfo:
    """Return the configured application timezone with a safe UTC fallback."""
    try:
        return ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def format_app_datetime(value: datetime | None) -> str:
    """Format a timestamp in the configured application timezone."""
    if value is None:
        return "Now"
    aware_value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    local_value = aware_value.astimezone(app_timezone())
    return f"{local_value:%Y-%m-%d %H:%M:%S} {settings.APP_TIMEZONE}"
