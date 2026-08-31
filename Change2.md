Implement an enhancement in the existing Network Monitoring System (NMS) to introduce a **NON-CRITICAL status/behavior specifically for devices categorized as Workstation**.

The purpose of this enhancement is to ensure that Workstations can still be monitored for UP/DOWN availability, but a DOWN Workstation must not be treated as a network incident because Workstations are not expected to stay online 24/7.

## Required Behavior

For any device with:

```text
Category = Workstation
```

apply the following monitoring behavior:

```text
Monitoring Status  : Enabled
Availability Check : Enabled
UP/DOWN Detection  : Enabled
Incident Trigger   : Disabled
Down Alert         : Disabled
Recovery Alert     : Disabled
SLA Impact         : Disabled
Criticality        : NON-CRITICAL
```

The workstation must still appear on the dashboard and device list.

When the Workstation is reachable:

```text
Status      = UP
Criticality = NON-CRITICAL
Last Seen   = current timestamp
```

When the Workstation becomes unreachable after the configured failure threshold:

```text
Status      = DOWN
Criticality = NON-CRITICAL
Incident    = NONE
Alert       = NONE
SLA Impact  = NONE
```

A Workstation DOWN event must NOT:

- Create an incident
- Appear in Active Incidents
- Trigger critical alerts
- Trigger email/Telegram/WhatsApp/other notification channels
- Increase infrastructure incident counters
- Affect SLA calculations
- Be displayed as a critical infrastructure outage

However, the system must still:

- Record the DOWN status
- Record the status change timestamp
- Preserve `last_seen_at`
- Display the workstation as offline
- Record status history if the existing NMS supports it
- Calculate/display offline duration if available

## Status / Criticality Model

Do not replace the normal availability status.

Keep availability and criticality separate.

Recommended model:

```text
availability_status:
UP
DOWN

criticality:
CRITICAL
NON_CRITICAL
```

For Workstation:

```text
availability_status = UP or DOWN
criticality = NON_CRITICAL
```

Example:

```text
Hostname    : WS-FINANCE-001
IP Address  : 172.16.20.51
Category    : Workstation
Status      : DOWN
Criticality : NON-CRITICAL
Incident    : N/A
Last Seen   : 31 Aug 2026 17:15
```

## Important Architecture Rule

Do NOT implement logic throughout the application using repeated hardcoded checks such as:

```pseudo
if category == "Workstation":
    ...
```

Prefer using the existing category configuration, monitoring policy, severity, criticality, or device profile architecture if available.

If the existing application does not support this, implement the smallest reusable solution possible.

Example:

```text
Device Category
      ↓
Criticality
      ↓
Incident Rule
```

Suggested configuration:

```text
Workstation:
criticality = NON_CRITICAL
incident_enabled = false
alert_enabled = false
sla_enabled = false
```

Infrastructure categories should keep their existing behavior.

For example:

```text
Server
Firewall
Core Switch
Access Switch
Access Point
Network Device
```

must continue triggering incidents normally when their existing rules require it.

## Monitoring Engine Logic

Modify the existing monitoring flow approximately as follows:

```pseudo
result = check_device(device)

if result.success:

    device.status = "UP"
    device.last_seen_at = NOW()

    save_status(device)

    if device.category != NON_CRITICAL:
        process_existing_recovery_logic()

else:

    if failure_threshold_reached(device):

        device.status = "DOWN"

        save_status(device)

        if device.criticality == "NON_CRITICAL":

            // Workstation behavior

            DO NOT create incident
            DO NOT send alert
            DO NOT affect SLA

            only record availability status

        else:

            process_existing_incident_logic()
```

Prefer checking configuration rather than category names, for example:

```pseudo
if device.incident_enabled:
    create_or_update_incident(device)
```

instead of:

```pseudo
if device.category != "Workstation":
    create_incident(device)
```

## Dashboard Enhancement

Workstations that are DOWN should visually indicate that they are non-critical.

Recommended display:

```text
DOWN · NON-CRITICAL
```

or:

```text
Offline
Non-Critical
```

Do not use the same critical alarm presentation used for failed servers, switches, firewalls, or other infrastructure.

If the dashboard contains counters such as:

```text
Active Incidents
Critical Devices Down
Network Problems
```

DOWN Workstations must be excluded.

A separate informational counter may be used:

```text
Workstations Online
Workstations Offline
```

Example:

```text
WORKSTATIONS

Total      : 200
Online     : 85
Offline    : 115
Incidents  : 0
```

## Database

First inspect the existing database structure.

Reuse existing fields if there is already support for:

```text
severity
priority
criticality
monitoring_policy
incident_enabled
alert_enabled
```

Do NOT create duplicate concepts unnecessarily.

If no suitable field exists, add a reusable field such as:

```text
criticality
```

with possible values:

```text
CRITICAL
NON_CRITICAL
```

or preferably add configurable policy flags:

```text
incident_enabled
alert_enabled
sla_enabled
```

Use proper database migration scripts.

Do NOT manually modify production tables.

Do NOT delete or reset existing data.

## Default Workstation Configuration

Existing and newly created devices categorized as Workstation should default to:

```text
criticality      = NON_CRITICAL
incident_enabled = FALSE
alert_enabled    = FALSE
sla_enabled      = FALSE
```

Do not modify existing infrastructure categories.

## Backward Compatibility

The enhancement must not break existing:

- Device monitoring
- ICMP polling
- Status history
- Incident generation
- Alerting
- Dashboard
- Authentication
- API
- Background workers/schedulers
- Existing infrastructure monitoring rules

Existing infrastructure devices must retain their current monitoring behavior.

## Acceptance Tests

### Test 1 — Workstation UP

Input:

```text
Category = Workstation
Ping = Success
```

Expected:

```text
Status = UP
Criticality = NON-CRITICAL
Last Seen = Updated
Incident = None
```

### Test 2 — Workstation DOWN

Input:

```text
Category = Workstation
Ping fails beyond configured failure threshold
```

Expected:

```text
Status = DOWN
Criticality = NON-CRITICAL
Incident = None
Alert = None
SLA Impact = None
```

The device must remain visible as offline.

### Test 3 — Workstation Recovery

Input:

```text
Previous Status = DOWN
Current Ping = Success
```

Expected:

```text
Status = UP
Last Seen = Updated
Recovery Incident = None
Recovery Alert = None
```

### Test 4 — Server DOWN

Input:

```text
Category = Server
Ping fails beyond configured threshold
```

Expected:

The existing server incident and alert workflow must continue working exactly as before.

### Test 5 — Dashboard

If:

```text
Infrastructure Down = 2
Workstations Down = 100
```

the critical infrastructure dashboard must still show:

```text
Critical / Infrastructure Problems = 2
```

not:

```text
102
```

Workstation offline count may be displayed separately.

## Implementation Instructions

Before modifying code:

1. Inspect the existing project architecture.
2. Locate the device/category model.
3. Locate the monitoring/polling service.
4. Locate incident creation logic.
5. Locate notification logic.
6. Locate SLA calculation.
7. Locate dashboard counters/API.
8. Locate frontend status rendering.

Then provide a brief impact analysis identifying which files/modules need modification.

After the impact analysis, implement the enhancement with minimal changes to the existing architecture.

Do not rebuild existing modules unnecessarily.

Do not change unrelated functionality.

After implementation:

1. Run existing tests.
2. Add tests for Workstation NON-CRITICAL behavior.
3. Run regression tests for infrastructure devices.
4. Report all modified files.
5. Report database migrations.
6. Explain the final monitoring flow.

The final expected design principle is:

```text
DOWN does not automatically mean INCIDENT.
```

For Workstations:

```text
DOWN
  ↓
NON-CRITICAL
  ↓
Record Status
  ↓
Show Offline
  ↓
NO INCIDENT
NO ALERT
NO SLA IMPACT
```