# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## LAN Network Monitoring System

**Project Name:** LAN Network Monitoring System  
**Product Type:** Internal Web Application  
**Version:** 1.0 – MVP  
**Primary Purpose:** Real-time LAN Device Availability Monitoring  
**Target Environment:** Internal Corporate Local Area Network  
**Target Scale:** 200–500+ Devices

---

# 1. PRODUCT OVERVIEW

Develop a centralized web-based Network Monitoring System for monitoring devices connected to a corporate Local Area Network (LAN).

The application must continuously monitor registered network devices and determine whether each device is UP, DOWN, WARNING, or UNKNOWN.

The system must provide near-real-time visibility through a centralized dashboard, maintain historical availability and incident records, and automatically notify administrators when devices become unavailable and when they recover.

The initial version must focus on reliable ICMP/Ping-based availability monitoring.

The architecture must be designed so that additional monitoring methods such as TCP Port Monitoring, SNMP, bandwidth monitoring, and network topology can be added later without major architectural changes.

---

# 2. BUSINESS OBJECTIVES

The system must help the IT team:

- Quickly identify unavailable network devices.
- Determine exactly when a device became unavailable.
- Track device recovery time.
- Calculate device downtime.
- Maintain historical incident information.
- Reduce manual network checking.
- Provide centralized visibility of network infrastructure.
- Categorize devices based on type, location, IP range, VLAN, and group.
- Automatically notify administrators of outages.
- Reduce unnecessary alerts caused by upstream network failures.
- Provide historical availability information for troubleshooting and reporting.

---

# 3. PRODUCT SCOPE

## 3.1 MVP – Phase 1

The first production version must include:

1. User Authentication
2. Device Management
3. Device Categories
4. Device Groups
5. Location Management
6. ICMP/Ping Monitoring
7. Concurrent Monitoring Engine
8. UP/DOWN State Management
9. Device Status Dashboard
10. Latency Monitoring
11. Incident Management
12. Downtime Calculation
13. Recovery Detection
14. Notification System
15. Device Filtering and Search
16. Monitoring Configuration
17. Maintenance Mode
18. Basic Device Dependency
19. Audit Logging
20. Historical Availability Data

---

# 4. OUT OF SCOPE FOR MVP

The following features must NOT be implemented in the initial MVP unless required for architectural preparation:

- SNMP Monitoring
- Bandwidth Monitoring
- Network Interface Monitoring
- CPU Monitoring
- RAM Monitoring
- Temperature Monitoring
- Automatic Network Discovery
- Network Topology Visualization
- Syslog Server
- NetFlow
- Configuration Backup
- AI-based anomaly detection
- Mobile application

The architecture should nevertheless allow these features to be added later.

---

# 5. RECOMMENDED TECHNOLOGY STACK

## Backend

Use:

**Python + FastAPI**

Responsibilities:

- REST API
- Authentication
- Device management
- Incident management
- Dashboard data
- Configuration management
- Notification configuration

---

## Monitoring Engine

Use:

**Python AsyncIO-based Worker**

The monitoring worker must operate independently from the web application.

It must NEVER depend on a user opening the dashboard.

Responsibilities:

- Schedule device checks.
- Perform concurrent ICMP checks.
- Measure latency.
- Detect consecutive failures.
- Detect recovery.
- Update current device state.
- Create incidents.
- Close incidents.
- Trigger notification events.

---

## Database

Preferred:

**PostgreSQL**

Alternative:

MySQL/MariaDB.

Use SQLAlchemy ORM and Alembic for database migrations.

---

## Frontend

Recommended:

**React**

with:

- Bootstrap or equivalent responsive UI framework
- Chart.js for charts
- REST API integration
- WebSocket or Server-Sent Events for live status updates

The UI must be desktop-first but responsive.

---

## Deployment

The application should support:

**Docker Compose**

Minimum containers:

- frontend
- backend
- monitoring-worker
- database

Optional:

- Redis
- reverse proxy

The system must also be designed so that it can later be deployed on a Linux VM without Docker if required.

---

# 6. HIGH-LEVEL ARCHITECTURE

```text
                   CORPORATE LAN
                         |
       +-----------------+-----------------+
       |                 |                 |
    Servers           Switches           OT/IoT
       |                 |                 |
       +-----------------+-----------------+
                         |
                         |
                  ICMP Monitoring
                         |
                         v
              +----------------------+
              | Monitoring Worker    |
              | Python / AsyncIO     |
              +----------+-----------+
                         |
                         v
                +----------------+
                | PostgreSQL     |
                +-------+--------+
                        |
                        v
                +----------------+
                | FastAPI        |
                | REST API       |
                +-------+--------+
                        |
                +-------+-------+
                |               |
                v               v
            Dashboard       Notification
```

IMPORTANT:

The dashboard must NEVER directly ping network devices.

Monitoring must always be performed by the monitoring worker.

The dashboard only reads monitoring results from the API/database.

---

# 7. DEVICE MANAGEMENT

Administrators must be able to:

- Add device
- Edit device
- Delete device
- Disable monitoring
- Enable monitoring
- Search device
- Filter device
- Bulk import devices using CSV
- Export device list
- Assign device category
- Assign device group
- Assign location
- Define parent/upstream device
- Enable maintenance mode

Each device should contain at minimum:

```text
ID
Device Name
Hostname
IP Address
Description
Category
Group
Location
VLAN
Parent Device
Monitoring Enabled
Monitoring Interval
Timeout
Failure Threshold
Recovery Threshold
Current Status
Last Check
Last Seen
Last UP
Last DOWN
Current Latency
Created At
Updated At
```

IP address must be unique unless future architecture explicitly supports multiple monitoring targets using the same address.

Validate IPv4 addresses before saving.

Prepare architecture for IPv6 support later.

---

# 8. DEVICE CATEGORIES

Administrators must be able to create custom categories.

Default categories:

```text
Firewall
Router
Core Switch
Distribution Switch
Access Switch
Server
Virtual Machine
Access Point
CCTV
NVR
Printer
PLC
UPS
Storage
IoT
Other
```

Each device belongs to one category.

---

# 9. DEVICE GROUPS

Devices must support logical grouping.

Examples:

```text
Network Infrastructure
Servers
CCTV System
WiFi Infrastructure
OT Network
Office Equipment
```

Groups must be user configurable.

---

# 10. LOCATION MANAGEMENT

Devices must support physical location information.

Example:

```text
Main Office
Data Center
Building A
Building B
Factory
Warehouse
Remote Site
```

Allow administrators to create and modify locations.

---

# 11. VLAN AND IP INFORMATION

Each device should optionally store:

```text
VLAN ID
VLAN Name
Subnet
IP Address
```

Example:

```text
VLAN ID: 20
VLAN Name: Server
Subnet: 172.16.20.0/24
IP: 172.16.20.15
```

VLAN information in the MVP is informational and used for filtering/reporting.

---

# 12. MONITORING ENGINE

The monitoring engine is the core component.

It must run independently as a background service.

Example:

```text
monitoring-worker
```

The worker continuously loads enabled devices and performs ICMP checks.

---

# 13. CONCURRENT MONITORING

Do NOT monitor devices sequentially.

Incorrect:

```text
Device 1
wait
Device 2
wait
Device 3
wait
```

Use asynchronous/concurrent monitoring.

Example:

```text
Worker
 |
 +-- Device 1
 +-- Device 2
 +-- Device 3
 +-- Device 4
 +-- Device 5
 |
 +-- Device N
```

The system must comfortably support at least:

**500 monitored devices**

without requiring one process/thread per device.

---

# 14. DEFAULT MONITORING PARAMETERS

Default values:

```text
Monitoring Interval: 15 seconds
Ping Timeout: 2 seconds
Failure Threshold: 3
Recovery Threshold: 2
```

All values must be configurable.

They may be configured globally and optionally overridden per device.

---

# 15. DEVICE STATE MACHINE

Possible states:

```text
UP
WARNING
DOWN
UNKNOWN
MAINTENANCE
```

---

# 16. FAILURE DETECTION

One failed ping must NOT immediately mark a device DOWN.

Example:

```text
10:00:00 SUCCESS
10:00:15 SUCCESS
10:00:30 FAILED
10:00:45 FAILED
10:01:00 FAILED
```

With:

```text
Failure Threshold = 3
```

Device becomes:

```text
DOWN
```

The outage start time should reference the first failure of the confirmed failure sequence where appropriate.

---

# 17. RECOVERY DETECTION

Recovery should also require consecutive successful checks.

Example:

```text
Recovery Threshold = 2
```

Sequence:

```text
FAILED
FAILED
FAILED
SUCCESS
SUCCESS
```

After two consecutive successful checks:

```text
Status = UP
```

Close the active incident.

Record:

```text
Recovered At
Total Downtime
```

Send recovery notification.

---

# 18. WARNING STATE

WARNING can be triggered when:

- latency exceeds configured threshold;
- intermittent packet loss occurs;
- a device is approaching failure threshold but has not yet reached DOWN state.

Example default:

```text
Latency Warning > 100 ms
Latency Critical > 250 ms
```

These values must be configurable.

---

# 19. UNKNOWN STATE

UNKNOWN should be used when:

- device has never been checked;
- monitoring engine cannot determine status;
- monitoring configuration is invalid;
- monitoring worker experiences an internal monitoring error.

UNKNOWN must not automatically be treated as DOWN.

---

# 20. MAINTENANCE MODE

Administrators must be able to place devices into maintenance mode.

Example:

```text
Maintenance Start:
2026-08-30 22:00

Maintenance End:
2026-08-30 23:30
```

During maintenance:

- Continue monitoring if technically possible.
- Suppress DOWN notifications.
- Clearly display MAINTENANCE status.
- Do not count planned maintenance as unplanned downtime in availability calculations.

Support both:

```text
Manual maintenance
Scheduled maintenance
```

---

# 21. INCIDENT MANAGEMENT

When a device reaches DOWN state, create an incident.

Incident structure:

```text
Incident ID
Device ID
Detected At
Down Since
Recovered At
Duration
Status
Failure Reason
Notification Status
Acknowledged
Acknowledged By
Acknowledged At
Notes
```

Incident status:

```text
OPEN
ACKNOWLEDGED
RESOLVED
```

---

# 22. INCIDENT TIMELINE

Example:

```text
Access Switch 01

DOWN:
30 Aug 2026 10:15:23

Acknowledged:
30 Aug 2026 10:18:10

Recovered:
30 Aug 2026 10:27:42

Downtime:
12m 19s
```

---

# 23. DEVICE DEPENDENCY

Devices may have a parent/upstream device.

Example:

```text
Core Switch
   |
   +-- Access Switch 01
          |
          +-- AP01
          +-- AP02
          +-- CCTV01
          +-- Printer01
```

If Access Switch 01 is DOWN, downstream devices may become unreachable.

The system should identify that their outage may be caused by the parent.

---

# 24. ALERT SUPPRESSION

When an upstream device is confirmed DOWN:

Suppress repeated DOWN notifications for dependent devices.

Example:

Instead of:

```text
Access Switch DOWN
AP01 DOWN
AP02 DOWN
CCTV01 DOWN
Printer01 DOWN
```

Generate primary notification:

```text
Access Switch 01 DOWN

Affected dependent devices:
AP01
AP02
CCTV01
Printer01
```

Dependent devices may still display as unreachable, but notification status must indicate:

```text
SUPPRESSED_BY_DEPENDENCY
```

---

# 25. NOTIFICATION SYSTEM

Initial notification channels:

1. Email
2. Telegram

Prepare architecture for:

- Microsoft Teams
- Webhook
- SMS
- WhatsApp

---

# 26. DOWN NOTIFICATION

Example:

```text
NETWORK ALERT

Device: Access Switch 01
IP: 172.16.10.10
Location: Building A
Category: Access Switch

Status: DOWN

Down Since:
30-Aug-2026 10:15:23

Failed Checks:
3

Last Successful Response:
30-Aug-2026 10:14:45
```

---

# 27. RECOVERY NOTIFICATION

Example:

```text
NETWORK RECOVERY

Device: Access Switch 01
IP: 172.16.10.10

Status: UP

Recovered:
30-Aug-2026 10:27:42

Total Downtime:
12 minutes 19 seconds
```

---

# 28. NOTIFICATION ANTI-SPAM

Do not repeatedly send the same DOWN notification every monitoring cycle.

Default logic:

```text
UP → DOWN
Send DOWN notification once.

DOWN → DOWN
Do not resend.

DOWN → UP
Send RECOVERY notification once.
```

Future versions may support escalation.

---

# 29. DASHBOARD

Main dashboard must show:

```text
TOTAL DEVICES
UP
DOWN
WARNING
UNKNOWN
MAINTENANCE
```

Example:

```text
Total        246
UP           237
DOWN           5
WARNING        2
UNKNOWN        1
MAINTENANCE    1
```

---

# 30. DASHBOARD DEVICE TABLE

Required columns:

```text
Status
Device Name
IP Address
Hostname
Category
Group
Location
VLAN
Latency
Last Check
Down Since
```

Status should be visually obvious.

Example:

```text
UP          Green
WARNING     Yellow/Amber
DOWN        Red
UNKNOWN     Gray
MAINTENANCE Blue
```

Do not rely exclusively on color; include text/icons for accessibility.

---

# 31. DASHBOARD FILTERS

Support filtering by:

```text
Status
Category
Group
Location
VLAN
Subnet
IP Address
Device Name
```

Allow combined filters.

Example:

```text
Location = Building A
Category = Access Point
Status = DOWN
```

---

# 32. SEARCH

Global device search must support:

```text
Device Name
Hostname
IP Address
Description
```

Search results should update quickly without full page reload.

---

# 33. DEVICE DETAIL PAGE

Clicking a device opens a detailed page.

Show:

```text
Device Name
IP
Hostname
Category
Location
VLAN
Current Status
Current Latency
Last Check
Last Seen
Last Down
Last Recovery
Availability
Parent Device
Monitoring Configuration
```

Also show historical information.

---

# 34. LATENCY HISTORY

Store latency data.

Provide charts for:

```text
Last Hour
Last 24 Hours
Last 7 Days
Last 30 Days
```

Avoid unlimited raw ping history retention.

Implement configurable retention/downsampling strategy.

Example:

```text
Raw checks: 7 days
5-minute aggregate: 30 days
Hourly aggregate: 1 year
```

Retention must be configurable.

---

# 35. AVAILABILITY

Calculate:

```text
Availability =
Available Time /
Total Eligible Monitoring Time
× 100
```

Example:

```text
Device Availability
Last 24 Hours: 99.92%
Last 7 Days:   99.81%
Last 30 Days:  99.76%
```

Exclude scheduled maintenance where configured.

---

# 36. RECENT INCIDENTS

Dashboard must display recent incidents.

Example:

```text
Device            Status       Time          Duration

Switch-01         Resolved     10:15         12m
AP-05             Open         09:43         1h 2m
Server-02         Resolved     Yesterday     4m
```

---

# 37. DATABASE DESIGN

Minimum tables:

```text
users
devices
categories
device_groups
locations
monitoring_results
incidents
notification_logs
maintenance_windows
audit_logs
system_settings
```

Optional/future:

```text
device_dependencies
monitoring_profiles
notification_channels
notification_rules
availability_daily
latency_aggregates
```

Use proper:

- primary keys;
- foreign keys;
- indexes;
- unique constraints;
- timestamps.

Indexes are especially required for:

```text
devices.ip_address
devices.current_status
monitoring_results.device_id
monitoring_results.checked_at
incidents.device_id
incidents.status
```

---

# 38. API DESIGN

Use REST API.

Example endpoints:

```text
POST   /api/auth/login
POST   /api/auth/logout

GET    /api/dashboard

GET    /api/devices
POST   /api/devices
GET    /api/devices/{id}
PUT    /api/devices/{id}
DELETE /api/devices/{id}

GET    /api/devices/{id}/history
GET    /api/devices/{id}/incidents

GET    /api/incidents
GET    /api/incidents/{id}
POST   /api/incidents/{id}/acknowledge

GET    /api/categories
POST   /api/categories

GET    /api/groups
POST   /api/groups

GET    /api/locations
POST   /api/locations

GET    /api/settings
PUT    /api/settings
```

Follow consistent API response structures and HTTP status codes.

---

# 39. REAL-TIME DASHBOARD

Dashboard should update without manual browser refresh.

Preferred:

```text
WebSocket
```

Alternative:

```text
Server-Sent Events
```

Fallback:

```text
REST polling every 5–15 seconds
```

Example:

```text
Device changes:
UP → DOWN

Worker
  ↓
Database
  ↓
Backend
  ↓
WebSocket
  ↓
Browser

Dashboard immediately changes status.
```

---

# 40. AUTHENTICATION

Require authentication.

Initial roles:

```text
Administrator
Operator
Viewer
```

---

# 41. RBAC

## Administrator

Can:

- manage users;
- manage devices;
- manage monitoring configuration;
- manage notifications;
- manage categories/groups;
- manage maintenance;
- view reports;
- acknowledge incidents.

## Operator

Can:

- view dashboard;
- view devices;
- view incidents;
- acknowledge incidents;
- add incident notes.

## Viewer

Read-only access.

---

# 42. AUDIT LOG

Important administrative actions must be logged.

Example:

```text
User
Action
Object
Old Value
New Value
Timestamp
Source IP
```

Track at minimum:

```text
Device Added
Device Deleted
Device Modified
Monitoring Disabled
Maintenance Enabled
Incident Acknowledged
System Setting Changed
User Modified
```

---

# 43. SECURITY REQUIREMENTS

Minimum security requirements:

- Secure password hashing using Argon2 or bcrypt.
- Never store plain-text passwords.
- Secure session/JWT handling.
- RBAC enforcement at backend level.
- Input validation.
- SQL injection protection.
- XSS protection.
- CSRF protection where applicable.
- Rate limiting for authentication endpoints.
- Secrets stored through environment variables.
- Do not expose database directly to LAN clients.
- Do not store notification credentials in frontend code.
- Audit sensitive administrative operations.

---

# 44. LOGGING

Application components must use structured logging.

Components:

```text
Backend
Monitoring Worker
Notification Worker
Authentication
Database
```

Logs should contain useful context without exposing passwords or secrets.

---

# 45. HEALTH CHECK

Provide application health endpoints.

Example:

```text
GET /health
GET /health/database
GET /health/monitoring-worker
```

Dashboard should warn administrators if the monitoring engine itself is unavailable.

This is important because:

```text
Monitoring Worker DOWN
```

must not cause administrators to incorrectly assume that every monitored device is healthy.

---

# 46. MONITORING ENGINE SAFETY

If the monitoring worker stops:

Do NOT automatically change all devices to DOWN.

Instead, after an appropriate stale-data threshold, display:

```text
MONITORING DATA STALE
```

or:

```text
MONITORING ENGINE OFFLINE
```

This condition must be distinguishable from actual device failure.

---

# 47. BULK DEVICE IMPORT

Support CSV import.

Example:

```csv
device_name,ip_address,category,group,location,vlan
Core-SW01,172.16.1.2,Core Switch,Network,Data Center,10
AP-01,172.16.10.20,Access Point,WiFi,Building A,20
PLC-01,172.16.5.10,PLC,OT,Factory,50
```

Before committing import:

- validate rows;
- detect duplicate IP addresses;
- display validation errors;
- show import preview.

---

# 48. SYSTEM SETTINGS

Administrators must be able to configure:

```text
Default Monitoring Interval
Ping Timeout
Failure Threshold
Recovery Threshold
Latency Warning Threshold
Latency Critical Threshold
History Retention
Timezone
Email Settings
Telegram Settings
Notification Rules
```

---

# 49. TIMEZONE

All timestamps should be stored internally in UTC.

Display timestamps according to configured application timezone.

Timezone must be configurable.

---

# 50. PERFORMANCE REQUIREMENTS

MVP target:

```text
Devices: 500 minimum
Default interval: 15 seconds
Dashboard users: 10 concurrent
```

Monitoring cycle should not block API requests.

Database writes should be optimized to avoid unnecessary growth.

Do not create one operating-system process per monitored device.

---

# 51. ERROR HANDLING

Application must gracefully handle:

```text
Invalid IP
Duplicate IP
Database unavailable
Monitoring worker unavailable
ICMP permission error
Notification service unavailable
Timeout
Invalid configuration
```

Errors must not crash the entire monitoring engine.

A failure monitoring one device must not stop monitoring other devices.

---

# 52. UI REQUIREMENTS

Design style:

```text
Professional
Modern
Clean
Infrastructure-oriented
Enterprise dashboard
```

Desktop dashboard is the priority.

Suggested layout:

```text
+------------------------------------------------+
| Network Monitoring                            |
+------------------------------------------------+
| Total | UP | DOWN | Warning | Maintenance     |
+------------------------------------------------+
| Availability / Incident Summary               |
+------------------------------------------------+
| Filters                                       |
+------------------------------------------------+
| Device Status Table                           |
|                                                |
| Device | IP | Category | Status | Latency     |
|                                                |
+------------------------------------------------+
| Recent Incidents                              |
+------------------------------------------------+
```

Use a left sidebar for:

```text
Dashboard
Devices
Incidents
Categories
Groups
Locations
Maintenance
Reports
Users
Settings
```

---

# 53. MVP ACCEPTANCE CRITERIA

The MVP is considered functional when:

1. Administrator can log in.
2. Administrator can create devices.
3. Devices can be categorized and grouped.
4. Monitoring worker automatically pings enabled devices.
5. At least 500 devices can be monitored.
6. Dashboard displays current device status.
7. Single ping failure does not immediately cause DOWN.
8. Consecutive failure threshold works.
9. Recovery threshold works.
10. DOWN event creates an incident.
11. Recovery closes the incident.
12. Downtime is calculated.
13. DOWN notification is sent once.
14. Recovery notification is sent once.
15. Device status updates without manual page refresh.
16. Device history can be viewed.
17. Device can be placed in maintenance mode.
18. Maintenance suppresses outage notifications.
19. Device dependency can suppress downstream alerts.
20. Dashboard can filter by status/category/group/location/VLAN.
21. Monitoring worker failure does not mark all devices DOWN.
22. Important administrative actions are audited.

---

# 54. TESTING REQUIREMENTS

Create automated tests for critical logic.

Especially test:

```text
UP → failed once → remains UP/WARNING

UP → 3 failures → DOWN

DOWN → 1 success → remains DOWN

DOWN → 2 successes → UP

UP → DOWN → incident created

DOWN → UP → incident closed

Maintenance + ping failure → no normal outage alert

Parent DOWN → child alert suppressed

Worker failure → devices not incorrectly marked DOWN
```

Also implement:

- API unit tests;
- database tests;
- authentication tests;
- monitoring engine tests.

---

# 55. DEVELOPMENT PHASES

## Phase 1A – Foundation

Build:

```text
Project structure
Docker Compose
Database
Authentication
RBAC
Device CRUD
Category CRUD
Group CRUD
Location CRUD
```

## Phase 1B – Monitoring Core

Build:

```text
Async ICMP worker
Monitoring scheduler
Ping timeout
Latency collection
Failure counter
Recovery counter
Device state machine
```

## Phase 1C – Incident Engine

Build:

```text
Incident creation
Recovery detection
Downtime calculation
Acknowledgement
Incident history
```

## Phase 1D – Dashboard

Build:

```text
Status summary
Device table
Filtering
Search
Device detail
Latency history
Incident list
Live updates
```

## Phase 1E – Notifications

Build:

```text
Email notification
Telegram notification
DOWN alert
Recovery alert
Anti-spam logic
Notification logging
```

## Phase 1F – Operational Features

Build:

```text
Maintenance mode
Dependency monitoring
Alert suppression
CSV import
Audit logs
Health checks
Data retention
```

---

# 56. FUTURE PHASE 2 – SERVICE MONITORING

Add TCP service checks.

Examples:

```text
HTTP      TCP/80
HTTPS     TCP/443
SSH       TCP/22
RDP       TCP/3389
SQL       TCP/1433
MySQL     TCP/3306
Custom TCP Port
```

Allow multiple monitoring checks per device.

---

# 57. FUTURE PHASE 3 – SNMP

Add SNMP v2c and SNMPv3 support.

Monitor:

```text
Device uptime
CPU
Memory
Interface status
Interface traffic
Interface errors
Temperature
Hardware health
```

SNMP credentials must be securely stored.

Prefer SNMPv3 for production environments.

---

# 58. FUTURE PHASE 4 – NETWORK TOPOLOGY

Implement network topology.

Example:

```text
Internet
   |
Firewall
   |
Core Switch
   |
+-- Distribution SW
|       |
|       +-- Access SW
|             |
|             +-- AP
|             +-- CCTV
|
+-- Server VLAN
|
+-- OT Network
```

Topology should use dependency relationships and eventually SNMP/LLDP information.

---

# 59. FUTURE PHASE 5 – REPORTING

Add:

```text
Daily Availability Report
Weekly Report
Monthly SLA Report
Top Downtime Devices
Most Frequent Incidents
Average Latency
Availability by Location
Availability by Category
```

Support:

```text
CSV
Excel
PDF
```

---

# 60. FUTURE PHASE 6 – ADVANCED MONITORING

Potential future capabilities:

```text
SNMP Auto Discovery
LLDP/CDP Discovery
Network Maps
Bandwidth Graphs
Syslog
Webhook Integration
Microsoft Teams Integration
Escalation Policies
SLA Management
Scheduled Reports
Multi-Site Monitoring
Distributed Monitoring Probes
Anomaly Detection
```

---

# 61. DEVELOPMENT PRINCIPLES

Follow these principles:

1. Reliability is more important than visual complexity.
2. Monitoring must operate independently from the dashboard.
3. Never mark a device DOWN based on one failed ping.
4. Avoid false positive alerts.
5. Do not allow one failed device check to crash the monitoring worker.
6. Keep monitoring engine, API, and frontend logically separated.
7. Design database structures for future expansion.
8. Keep the MVP simple.
9. Do not prematurely implement SNMP.
10. Prioritize accurate incident detection.
11. Use asynchronous monitoring.
12. Implement structured logging.
13. Use database migrations.
14. Write tests for state transitions.
15. Keep secrets outside source code.
16. Ensure the application can be maintained by another developer.

---

# 62. REQUIRED PROJECT STRUCTURE

Use a clean modular structure similar to:

```text
network-monitor/
|
+-- backend/
|   +-- app/
|   |   +-- api/
|   |   +-- models/
|   |   +-- schemas/
|   |   +-- services/
|   |   +-- repositories/
|   |   +-- auth/
|   |   +-- notifications/
|   |   +-- core/
|   |   +-- main.py
|   |
|   +-- tests/
|   +-- alembic/
|   +-- requirements.txt
|
+-- worker/
|   +-- monitoring/
|   |   +-- scheduler.py
|   |   +-- icmp.py
|   |   +-- state_machine.py
|   |   +-- incident_manager.py
|   |   +-- dependency.py
|   |
|   +-- main.py
|
+-- frontend/
|   +-- src/
|   +-- public/
|   +-- package.json
|
+-- docker/
|
+-- docker-compose.yml
+-- .env.example
+-- README.md
```

The AI coding tool may improve the internal structure if there is a technically superior approach, but separation of frontend, backend API, and monitoring worker must remain.

---

# 63. INSTRUCTIONS TO AI DEVELOPMENT TOOL

You are acting as the senior software architect and developer responsible for implementing this project.

Do not attempt to generate the entire application in one step.

Implement the system incrementally.

For every development phase:

1. Review this PRD.
2. Explain the component being implemented.
3. Identify dependencies.
4. Design database changes if required.
5. Implement backend functionality.
6. Implement frontend functionality where applicable.
7. Implement validation.
8. Implement error handling.
9. Write automated tests.
10. Provide commands required to run/test the component.
11. Verify the component before continuing.
12. Do not remove working functionality from previous phases.

Do not use mock functionality for core monitoring features in the production implementation.

Use actual ICMP monitoring.

Keep configuration in environment variables where appropriate.

Generate `.env.example` but never commit real credentials.

Use migrations rather than manually modifying production database schemas.

Document important architectural decisions.

---

# 64. INITIAL AI TASK

Start with **Phase 1A – Foundation only**.

Do NOT implement the entire PRD immediately.

First:

1. Analyze the PRD.
2. Propose the final technical architecture.
3. Propose the database schema.
4. Propose the project directory structure.
5. Define Docker Compose architecture.
6. Identify Python and JavaScript dependencies.
7. Define API architecture.
8. Define authentication/RBAC approach.
9. Identify potential technical risks.
10. Present the implementation plan.

After the architecture is established, implement:

```text
Backend project
Frontend project
PostgreSQL
Docker Compose
Database migrations
Authentication
RBAC
Device CRUD
Category CRUD
Group CRUD
Location CRUD
```

Create a README containing exact installation and startup instructions.

Do not begin ICMP monitoring until Phase 1A has been tested successfully.

---

# 65. FINAL PRODUCT GOAL

The final application should evolve into an internal Network Monitoring System capable of providing a centralized operational view similar in concept to basic functionality found in:

```text
PRTG
Zabbix
Uptime Kuma
LibreNMS
```

However, the application must remain focused on the organization's actual requirements rather than attempting to clone all functionality of these products.

The priority order is:

```text
Reliability
    ↓
Accurate Monitoring
    ↓
Accurate Incident Detection
    ↓
Useful Notifications
    ↓
Operational Visibility
    ↓
Historical Analysis
    ↓
Advanced Monitoring
```

A visually attractive dashboard must never take priority over reliable monitoring behavior.