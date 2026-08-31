from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime, timezone
from uuid import UUID
import logging
from monitoring.icmp import PingResult

logger = logging.getLogger("nms.worker.state_machine")

@dataclass
class DeviceStateRecord:
    device_id: UUID
    current_status: str = "UNKNOWN"          # UP, WARNING, DOWN, UNKNOWN, MAINTENANCE
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    first_failure_at: Optional[datetime] = None
    last_status_change_at: Optional[datetime] = None

@dataclass
class StateTransitionResult:
    previous_status: str
    new_status: str
    status_changed: bool
    event_type: Optional[str] = None          # 'DOWN', 'RECOVERED', 'WARNING_LATENCY', None
    first_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0

class DeviceStateMachine:
    def __init__(self):
        self._states: Dict[UUID, DeviceStateRecord] = {}

    def get_or_create_state(self, device_id: UUID, initial_status: str = "UNKNOWN") -> DeviceStateRecord:
        if device_id not in self._states:
            self._states[device_id] = DeviceStateRecord(
                device_id=device_id,
                current_status=initial_status,
                last_status_change_at=datetime.now(timezone.utc)
            )
        return self._states[device_id]

    def evaluate(
        self,
        device_id: UUID,
        ping_result: PingResult,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
        latency_warning_threshold: float = 100.0,
        latency_critical_threshold: float = 250.0,
        is_in_maintenance: bool = False,
        initial_status: str = "UNKNOWN"
    ) -> StateTransitionResult:
        """
        Evaluate a single ping result against device state thresholds.
        """
        state = self.get_or_create_state(device_id, initial_status)
        now = datetime.now(timezone.utc)
        previous_status = state.current_status
        new_status = previous_status
        event_type = None

        if is_in_maintenance:
            # Under maintenance: suppress alert states
            new_status = "MAINTENANCE"
            if previous_status != "MAINTENANCE":
                state.last_status_change_at = now
            state.current_status = new_status
            return StateTransitionResult(
                previous_status=previous_status,
                new_status=new_status,
                status_changed=(previous_status != new_status),
                event_type=None,
                first_failure_at=state.first_failure_at,
                consecutive_failures=state.consecutive_failures,
                consecutive_successes=state.consecutive_successes
            )

        if ping_result.is_alive:
            # --- SUCCESSFUL CHECK ---
            state.consecutive_successes += 1
            state.consecutive_failures = 0
            state.first_failure_at = None

            if previous_status == "DOWN":
                # Check if recovery threshold reached
                if state.consecutive_successes >= recovery_threshold:
                    new_status = "UP"
                    event_type = "RECOVERED"
                    state.last_status_change_at = now
                else:
                    # Not yet recovered enough
                    new_status = "DOWN"
            elif previous_status in ("UP", "WARNING", "UNKNOWN", "MAINTENANCE"):
                # Evaluate Latency Warning vs UP
                latency = ping_result.latency or 0.0
                if latency >= latency_critical_threshold:
                    new_status = "WARNING"
                    if previous_status != "WARNING":
                        event_type = "WARNING_LATENCY"
                elif latency >= latency_warning_threshold:
                    new_status = "WARNING"
                    if previous_status != "WARNING":
                        event_type = "WARNING_LATENCY"
                else:
                    new_status = "UP"
                    if previous_status != "UP":
                        state.last_status_change_at = now
        else:
            # --- FAILED CHECK ---
            state.consecutive_failures += 1
            state.consecutive_successes = 0

            if state.first_failure_at is None:
                state.first_failure_at = now

            if previous_status in ("UP", "WARNING", "UNKNOWN"):
                if state.consecutive_failures >= failure_threshold:
                    new_status = "DOWN"
                    event_type = "DOWN"
                    state.last_status_change_at = now
                else:
                    # Intermediate failure before threshold reached -> WARNING
                    new_status = "WARNING"
            elif previous_status == "DOWN":
                new_status = "DOWN"

        status_changed = (previous_status != new_status)
        state.current_status = new_status

        return StateTransitionResult(
            previous_status=previous_status,
            new_status=new_status,
            status_changed=status_changed,
            event_type=event_type,
            first_failure_at=state.first_failure_at,
            consecutive_failures=state.consecutive_failures,
            consecutive_successes=state.consecutive_successes
        )
