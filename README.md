# LAN Network Monitoring System

## Overview
A comprehensive LAN Network Monitoring System designed to track network devices, monitor uptime and latency, and provide alerts. 

## Current implementation

The repository contains the current NMS application, including:

- CentralAuth-backed login, session refresh, logout, and permission-based RBAC.
- FastAPI device, category, group, location, incident, maintenance, settings, and audit APIs.
- Async ICMP monitoring with failure/recovery thresholds, dependency-aware alert suppression, and email notifications.
- Dashboard category filtering: no selection shows the overall device summary; selecting a category scopes the summary and status cards.
- Device CSV import/export and administrator-only bulk deletion of selected devices.
- Uptime and latency history with selectable time ranges.
- Raw ICMP timeout evidence, incident correlation, per-device summaries, and a Ping Timeout Audit page.
- Configurable raw monitoring-data and timeout-log retention cleanup performed by the worker.

The latest implementation notes and release history are in [CHANGELOG.md](CHANGELOG.md). The product requirements remain in [NMS.md](NMS.md), and the CentralAuth migration requirements are in [PRD — NMS Migration to Central Authentication.md](PRD%20%E2%80%94%20NMS%20Migration%20to%20Central%20Authentication.md).

## Tech Stack
- **Backend:** FastAPI (Python)
- **Frontend:** React (JavaScript), BIC Internal IT Web UI Framework: v1.0.0
- **Database:** PostgreSQL
- **Worker:** Python asyncio
- **Deployment:** Docker & Docker Compose

## Prerequisites
- Docker
- Docker Compose
- Git

## Quick Start
1. Clone the repository.
2. Copy the environment variables example:
   ```bash
   cp .env.example .env
   ```
3. Update `.env` with your secure credentials.
4. Start the application:
   ```bash
   docker compose up --build
   ```

## Development Setup

### Backend
1. Navigate to `./backend`
2. Create virtual environment and install dependencies: `pip install -r requirements.txt`
3. Run with uvicorn: `uvicorn app.main:app --reload --port 8000`

### Frontend
1. Navigate to `./frontend`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`

The frontend imports the shared `/css/bic-*.css` files in framework order. Follow
`DESIGN_SYSTEM.md` for all UI changes. React bindings live in
`frontend/src/components/bic`; reusable styles belong in `css/bic-components.css`
and design constants in `css/bic-tokens.css`. There is no page-specific stylesheet.
The frontend Docker build uses the repository root as its context to include the
same shared framework files: `docker build -f frontend/Dockerfile .`.

Before shipping UI changes, run `npm run check:design` and `npm run build` from
`frontend`. Verify layouts at 1366×768 and 768px wide, including keyboard navigation
and form dialogs.

### Database migrations and tests

Apply migrations from the repository root with:

```bash
docker compose exec backend alembic upgrade head
```

Run backend tests from `backend` and frontend checks from `frontend`:

```bash
pytest
npm run check:design
npm run build
```

## Default Login
NMS no longer authenticates local passwords. Create or use an account in the
Central Authentication Service, grant it access to application code `NMS`, and
sign in with that CentralAuth username and password.

Set `CENTRAL_AUTH_URL` in `.env` to the CentralAuth web/API URL. The NMS backend
calls only `/api/v1/auth/login`, `/refresh`, `/logout`, `/me`, and
`/permissions`; it never connects to the CentralAuth database. Session tokens
are held in Secure/HttpOnly cookies (set `AUTH_COOKIE_SECURE=true` behind TLS).

### CentralAuth application setup

CentralAuth seeds the `NMS` application registration. In the CentralAuth admin
portal, create these NMS roles and assign the matching permissions:

- `NMS_ADMIN`: all `nms.*` permissions
- `NMS_OPERATOR`: `nms.dashboard.view`, `nms.device.view`,
  `nms.device.edit`, `nms.alert.view`, `nms.alert.manage`,
  `nms.config.view`
- `NMS_VIEWER`: `nms.dashboard.view`, `nms.device.view`, `nms.alert.view`,
  `nms.config.view`

Grant each user application access to `NMS` and assign one of those roles.
NMS derives the displayed role from the CentralAuth permission response and
enforces the same policy on every protected backend endpoint.

## Project Structure
- `/backend`: FastAPI backend application
- `/backend/alembic`: database migrations
- `/backend/tests`: backend and API tests
- `/frontend`: React SPA frontend
- `/worker`: Python background worker for network monitoring
- `/docker`: Miscellaneous docker config files

## API Documentation
Once running, the API documentation is available at:

- Local backend: [http://localhost:8000/docs](http://localhost:8000/docs)
- Docker Compose backend: [http://localhost:8090/docs](http://localhost:8090/docs)

Important operational endpoints include:

- `GET /api/dashboard/summary?category_id=<id>` for overall or category-scoped dashboard data.
- `DELETE /api/devices/bulk` for administrator-only deletion of selected device IDs.
- `GET /api/ping-timeouts` for filtered timeout audit records.
- `GET /api/devices/{id}/ping-timeouts` and `/summary` for device-level timeout evidence.

## Development Phases
- **Phase 1A:** Core Infrastructure & Authentication
- **Phase 1B:** Network Monitoring Engine
- **Phase 1C:** Device Management API
- **Phase 1D:** Dashboard & Analytics
- **Phase 1E:** Alerting & Notifications
- **Phase 1F:** Operational features, timeout auditing, retention cleanup, and CentralAuth hardening
