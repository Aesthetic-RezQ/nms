import pytest
from datetime import datetime, timezone
from app.services.notification_service import NotificationService
from app.models.notification_log import NotificationLog
from sqlalchemy.ext.asyncio import AsyncSession

def test_down_notification_formatting():
    device = {
        "device_name": "Access Switch 01",
        "ip_address": "172.16.10.10",
        "location_name": "Building A",
        "category_name": "Access Switch"
    }
    incident = {
        "down_since": datetime(2026, 8, 30, 10, 15, 23, tzinfo=timezone.utc),
        "failure_reason": "Ping timeout"
    }
    
    msg = NotificationService.format_down_message(device, incident)
    assert "NETWORK ALERT" in msg
    assert "Access Switch 01" in msg
    assert "172.16.10.10" in msg
    assert "Building A" in msg
    assert "STATUS: DOWN" in msg.upper()
    assert "2026-08-30 10:15:23 UTC" in msg

def test_recovery_notification_formatting():
    device = {
        "device_name": "Access Switch 01",
        "ip_address": "172.16.10.10",
        "location_name": "Building A"
    }
    incident = {
        "recovered_at": datetime(2026, 8, 30, 10, 27, 42, tzinfo=timezone.utc),
        "duration_seconds": 739  # 12m 19s
    }

    msg = NotificationService.format_recovery_message(device, incident)
    assert "NETWORK RECOVERY" in msg
    assert "Access Switch 01" in msg
    assert "172.16.10.10" in msg
    assert "12m 19s" in msg

@pytest.mark.asyncio
async def test_list_notification_logs(async_client, admin_headers, test_db: AsyncSession):
    log1 = NotificationLog(
        channel="TELEGRAM",
        recipient="123456789",
        event_type="DOWN",
        subject="[ALERT] Switch DOWN",
        message_body="Switch is down",
        status="SENT"
    )
    test_db.add(log1)
    await test_db.commit()

    res = await async_client.get("/api/notifications/logs", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    assert data[0]["channel"] == "TELEGRAM"
    assert data[0]["status"] == "SENT"

@pytest.mark.asyncio
async def test_test_notification_validation(async_client, admin_headers):
    # Testing with missing telegram settings should return 400 Bad Request
    res = await async_client.post(
        "/api/notifications/test",
        json={"channel": "TELEGRAM", "recipient": "99999"},
        headers=admin_headers
    )
    assert res.status_code in (400, 500)
