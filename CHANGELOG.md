# Changelog

## 2026-09-22 — Current workspace release

This release records the latest NMS implementation committed from the working
tree.

### Authentication and authorization

- Integrated NMS login, refresh, logout, current-user, and permission checks with
  CentralAuth.
- Kept the NMS database focused on monitoring data while retaining CentralAuth
  identity references for audit and ownership fields.
- Applied administrator/operator/viewer access rules across protected routes and
  navigation.

### Monitoring and incidents

- Added timezone-aware incident timestamps and notification content.
- Completed email-only DOWN, recovery, degraded, and reminder notification
  lifecycle handling with persisted settings and notification logs.
- Added raw ICMP timeout records, incident timeout counts, timeout correlation,
  per-device summaries, and the Ping Timeout Audit page.
- Added worker cleanup for expired raw monitoring results and timeout evidence.
- Preserved failure/recovery thresholds, maintenance suppression, and parent-down
  alert suppression.

### Dashboard and device management

- Added the dashboard category dropdown. The default view summarizes all devices;
  selecting a category scopes the overview to that category.
- Added uptime history charts and selectable history ranges while excluding outage
  samples from latency history.
- Improved device CSV import/export validation and category/group/location mapping.
- Added administrator-only selection, confirmation, audit logging, and bulk
  deletion of up to 100 devices at a time, including dependent monitoring and
  incident records.

### UI and operations

- Refined the BIC internal IT design-system components, responsive layout, focus
  behavior, dialogs, tables, and navigation.
- Added migration `003_add_ping_timeout_logs` for timeout evidence storage.
- Added test coverage for dashboard category filtering and device bulk deletion.

See [README.md](README.md) for setup, testing, API endpoints, and deployment
notes.
