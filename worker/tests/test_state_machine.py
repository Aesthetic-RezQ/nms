import pytest
import uuid
from monitoring.state_machine import DeviceStateMachine
from monitoring.icmp import PingResult

@pytest.fixture
def state_machine():
    return DeviceStateMachine()

@pytest.fixture
def device_id():
    return uuid.uuid4()

def test_initial_state_and_first_success(state_machine, device_id):
    success_ping = PingResult(is_alive=True, latency=15.0, packet_loss=0.0)
    result = state_machine.evaluate(
        device_id=device_id,
        ping_result=success_ping,
        failure_threshold=3,
        recovery_threshold=2,
        initial_status="UNKNOWN"
    )
    assert result.new_status == "UP"
    assert result.status_changed is True
    assert result.consecutive_successes == 1
    assert result.consecutive_failures == 0

def test_single_failure_does_not_mark_down(state_machine, device_id):
    # Establish UP state first
    state_machine.evaluate(
        device_id=device_id,
        ping_result=PingResult(is_alive=True, latency=10.0),
        initial_status="UP"
    )

    # 1st Failure
    fail_ping = PingResult(is_alive=False, error_message="Timeout")
    res1 = state_machine.evaluate(
        device_id=device_id,
        ping_result=fail_ping,
        failure_threshold=3,
        recovery_threshold=2
    )
    assert res1.new_status == "WARNING"
    assert res1.consecutive_failures == 1
    assert res1.event_type is None  # Not yet DOWN event

    # 2nd Failure
    res2 = state_machine.evaluate(
        device_id=device_id,
        ping_result=fail_ping,
        failure_threshold=3,
        recovery_threshold=2
    )
    assert res2.new_status == "WARNING"
    assert res2.consecutive_failures == 2
    assert res2.event_type is None

    # 3rd Failure -> Reaches threshold -> DOWN
    res3 = state_machine.evaluate(
        device_id=device_id,
        ping_result=fail_ping,
        failure_threshold=3,
        recovery_threshold=2
    )
    assert res3.new_status == "DOWN"
    assert res3.consecutive_failures == 3
    assert res3.event_type == "DOWN"
    assert res3.status_changed is True

def test_recovery_threshold_from_down(state_machine, device_id):
    # Set device to DOWN
    state = state_machine.get_or_create_state(device_id, initial_status="DOWN")
    state.consecutive_failures = 3

    # 1st Success while DOWN -> Remains DOWN
    success_ping = PingResult(is_alive=True, latency=20.0, packet_loss=0.0)
    res1 = state_machine.evaluate(
        device_id=device_id,
        ping_result=success_ping,
        failure_threshold=3,
        recovery_threshold=2
    )
    assert res1.new_status == "DOWN"
    assert res1.consecutive_successes == 1
    assert res1.event_type is None

    # 2nd Success while DOWN -> Reaches recovery threshold -> UP
    res2 = state_machine.evaluate(
        device_id=device_id,
        ping_result=success_ping,
        failure_threshold=3,
        recovery_threshold=2
    )
    assert res2.new_status == "UP"
    assert res2.consecutive_successes == 2
    assert res2.event_type == "RECOVERED"
    assert res2.status_changed is True

def test_latency_warning_threshold(state_machine, device_id):
    # Latency exceeding 100ms warning threshold
    high_latency_ping = PingResult(is_alive=True, latency=150.0, packet_loss=0.0)
    res = state_machine.evaluate(
        device_id=device_id,
        ping_result=high_latency_ping,
        latency_warning_threshold=100.0,
        latency_critical_threshold=250.0,
        initial_status="UP"
    )
    assert res.new_status == "WARNING"
    assert res.event_type == "WARNING_LATENCY"

def test_maintenance_mode_suppression(state_machine, device_id):
    fail_ping = PingResult(is_alive=False, error_message="Timeout")
    res = state_machine.evaluate(
        device_id=device_id,
        ping_result=fail_ping,
        is_in_maintenance=True,
        initial_status="UP"
    )
    assert res.new_status == "MAINTENANCE"
    assert res.event_type is None
