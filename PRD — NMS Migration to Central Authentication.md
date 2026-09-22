# Product Requirements Document
## NMS Authentication Migration to Central Auth

**Version:** 1.0

---

## 1. Objective

Mengubah authentication NMS yang saat ini menggunakan authentication/database lokal agar menggunakan Central Authentication Service.

NMS database tetap menjadi database khusus monitoring.

## Current implementation status — 2026-09

The migration is implemented in the current repository. NMS delegates login,
refresh, logout, current-user lookup, application access, and permission checks
to CentralAuth through the documented API. The NMS database retains only the
identity references needed for audit and ownership metadata; it does not store
or validate CentralAuth passwords. The legacy secret settings remain only as
rollback compatibility and must not be treated as an alternate production login
path.

See [README.md](README.md) for CentralAuth configuration and
[CHANGELOG.md](CHANGELOG.md) for the implementation scope.

---

## 2. Mandatory Pre-Development Assessment

Sebelum melakukan coding, AI/developer WAJIB melakukan audit terhadap existing NMS.

Identifikasi:

- Programming language/framework
- Existing login flow
- User table
- Password hashing
- Session mechanism
- Authentication middleware
- Authorization mechanism
- Existing roles
- Login/logout routes
- Protected API routes
- Frontend authentication state
- Docker configuration
- Environment variables

Jangan langsung mengubah source code sebelum dependency authentication dipetakan.

---

## 3. Target Architecture

```text
User
 │
 ▼
NMS Frontend
 │
 ▼
NMS Backend
 │
 │ Authentication
 ▼
Central Auth Service
 │
 ▼
Auth Database


NMS Backend
 │
 ▼
NMS Database
 │
 ├─ devices
 ├─ monitoring
 ├─ alerts
 └─ configuration
```

NMS MUST NOT query Central Auth database directly.

---

## 4. Application Registration

Register:

```text
Application Code: NMS
Application Name: Network Monitoring System
```

Suggested roles:

```text
NMS_ADMIN
NMS_OPERATOR
NMS_VIEWER
```

Example permissions:

```text
nms.dashboard.view
nms.device.view
nms.device.create
nms.device.edit
nms.device.delete

nms.alert.view
nms.alert.manage

nms.config.view
nms.config.manage
```

---

## 5. New Authentication Flow

```text
NMS Login
   │
   ▼
NMS Backend
   │
   ▼
Central Auth
   │
   ├── Valid?
   │
   ├── Active?
   │
   └── NMS access?
   │
   ▼
Authenticated Session
```

---

## 6. Remove Authentication Dependency

Existing local authentication must be deprecated.

Do NOT immediately delete legacy user data.

Migration phases:

### Phase 1 — Analysis

Document existing authentication.

### Phase 2 — Integration

Implement Central Auth while retaining rollback capability.

### Phase 3 — User Mapping

Map legacy NMS users to Central Auth identities.

Prefer immutable Central Auth `user_id`/UUID rather than username.

### Phase 4 — Testing

Test authentication and authorization.

### Phase 5 — Cutover

Disable legacy login.

### Phase 6 — Cleanup

Remove obsolete password/authentication code after successful stabilization.

---

## 7. Local User References

NMS may retain identity references required for:

```text
created_by
updated_by
acknowledged_by
```

Use:

```text
central_user_id
```

instead of maintaining another authentication password.

Where useful, cache display information such as name, but Central Auth remains authoritative.

---

## 8. Frontend Requirements

Replace existing login integration.

After authentication, frontend should obtain current user information from a trusted backend/auth endpoint.

Display:

```text
Full Name
Username
Role
```

Navigation may be adjusted based on permissions for usability.

However, backend MUST independently enforce permissions.

---

## 9. Token Handling

Avoid insecure persistent storage of long-lived credentials.

Preferred browser architecture:

```text
Browser
   │
 secure HttpOnly cookie/session
   ▼
NMS Backend
   │
   ▼
Central Auth
```

If bearer tokens must be used, document the threat model and storage mechanism.

---

## 10. Failure Handling

NMS must properly handle:

```text
401 Unauthorized
403 Forbidden
Central Auth unavailable
Expired token
Revoked session
Disabled user
Application access removed
```

Do not automatically fall back to legacy authentication after production cutover.

---

## 11. Migration Safety

Before modification:

- Backup NMS database.
- Backup source code/configuration.
- Create rollback point.
- Export existing user-role mapping.
- Document authentication dependencies.

Migration must not modify:

- Device monitoring
- Polling
- Availability calculation
- Latency monitoring
- Alert engine
- Existing historical monitoring data

unless technically required.

---

## 12. Acceptance Criteria

Migration succeeds when:

- NMS login uses Central Auth.
- Existing NMS passwords are no longer required.
- Disabled Central Auth user cannot access NMS.
- User without NMS access receives 403.
- Role/permission restrictions work.
- Monitoring functions remain operational.
- Existing NMS data remains intact.
- Logout terminates the appropriate authentication session.
- Central Auth downtime is handled safely.
- Legacy login is disabled after cutover.
