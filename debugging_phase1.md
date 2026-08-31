# NMS Debugging Log — Phase 1 Deployment

> **Date:** 2026-08-30  
> **Environment:** Docker Compose on Linux Server  
> **Status:** ✅ All issues resolved

---

## Issue #1: Missing Environment Variables & Obsolete Docker Compose Attribute

### Symptoms

```
WARN[0000] The "POSTGRES_USER" variable is not set. Defaulting to a blank string.
WARN[0000] The "POSTGRES_DB" variable is not set. Defaulting to a blank string.
WARN[0000] /home/applications/nms/application/docker-compose.yml: the attribute `version` is obsolete
env file /home/applications/nms/application/.env not found
```

### Root Cause

1. The `.env` file was never created — only `.env.example` existed in the repository.
2. The `docker-compose.yml` contained the `version: '3.8'` attribute, which is obsolete in Docker Compose v2+.

### Fix

**1. Created `.env` from the example template:**

```bash
cp .env.example .env
```

The `.env` file provides required variables:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=nms
POSTGRES_USER=nms_user
POSTGRES_PASSWORD=change_me_in_production
SECRET_KEY=change-this-to-a-random-secret-key
# ... other settings
```

**2. Removed the obsolete `version` attribute from `docker-compose.yml`:**

```diff
-version: '3.8'
-
 services:
   db:
     image: postgres:16-alpine
```

### Files Modified

- `docker-compose.yml` — removed `version: '3.8'`
- `.env` — created from `.env.example`

---

## Issue #2: Frontend Docker Build Failure — Missing `package-lock.json`

### Symptoms

```
> [frontend build 4/6] RUN npm ci:
npm error code EUSAGE
npm error The `npm ci` command can only install with an existing package-lock.json or
npm error npm-shrinkwrap.json with lockfileVersion >= 1.
```

```
target frontend: failed to solve: process "/bin/sh -c npm ci" did not complete successfully: exit code: 1
```

### Root Cause

The frontend `Dockerfile` used `npm ci` which requires a `package-lock.json` file to exist. This file was not committed to the repository.

### Fix

Changed `npm ci` to `npm install` in `frontend/Dockerfile`:

```diff
 COPY package*.json ./
-RUN npm ci
+RUN npm install
```

`npm install` generates the lock file on the fly and installs dependencies without requiring it to pre-exist.

### Files Modified

- `frontend/Dockerfile` — changed `npm ci` to `npm install`

> **Note:** Once the first successful build produces a `package-lock.json`, it should be committed to the repository. After that, the Dockerfile can be switched back to `npm ci` for faster, deterministic builds.

---

## Issue #3: Database Tables Not Created — Seed Script Failure

### Symptoms

```
asyncpg.exceptions.UndefinedTableError: relation "users" does not exist

sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError)
<class 'asyncpg.exceptions.UndefinedTableError'>: relation "users" does not exist
[SQL: SELECT users.id, users.username, users.email, users.password_hash, ...
FROM users WHERE users.username = $1::VARCHAR]
```

### Root Cause

The `seed.py` script attempted to query and insert data into the `users` table, but no tables had been created in the database. There was no migration or `create_all` step prior to seeding.

### Fix

Added table creation logic to `seed.py` before the seeding step:

```diff
+from app.models.base import Base
+from app.models import User, Device, Category, DeviceGroup, Location, SystemSetting, AuditLog

 async def seed():
     engine = create_async_engine(settings.database_url)
     async_session = async_sessionmaker(engine, expire_on_commit=False)

+    # Create all tables if they don't exist
+    async with engine.begin() as conn:
+        await conn.run_sync(Base.metadata.create_all)

     async with async_session() as db:
```

This ensures `Base.metadata.create_all()` creates all model-defined tables before any queries are executed.

### Files Modified

- `backend/seed.py` — added `Base.metadata.create_all` and consolidated model imports

---

## Issue #4: Passlib + Bcrypt Incompatibility

### Symptoms

```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'

ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

Full traceback pointed to `passlib/handlers/bcrypt.py` failing during backend initialization of the bcrypt hashing backend.

### Root Cause

`passlib==1.7.4` is unmaintained and incompatible with `bcrypt>=4.1`. The `passlib` library tries to access `bcrypt.__about__.__version__`, which no longer exists in newer bcrypt releases. This causes a cascade of errors during password hashing.

### Fix

**1. Replaced `passlib` with direct `bcrypt` usage in `app/core/security.py`:**

```diff
-from passlib.context import CryptContext
+import bcrypt

-pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

 def hash_password(password: str) -> str:
-    return pwd_context.hash(password)
+    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

 def verify_password(plain: str, hashed: str) -> bool:
-    return pwd_context.verify(plain, hashed)
+    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
```

**2. Updated `requirements.txt`:**

```diff
-passlib[bcrypt]==1.7.4
+bcrypt==4.2.1
```

### Files Modified

- `backend/app/core/security.py` — replaced passlib with direct bcrypt
- `backend/requirements.txt` — swapped `passlib[bcrypt]` for `bcrypt`

---

## Issue #5: API Requests Returning 405 (Method Not Allowed)

### Symptoms

```
api/auth/login:1  Failed to load resource: the server responded with a status of 405 (Not Allowed)
```

The login page was accessible, but submitting the login form failed with a 405 error.

### Root Cause

The Nginx reverse proxy configuration in `frontend/nginx.conf` had the `/api/` proxy block **commented out**:

```nginx
# Optional: proxy api requests to backend
# location /api/ {
#     proxy_pass http://backend:8000/;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
# }
```

Without this proxy, all `/api/` requests were served by Nginx's static file handler, which only serves `GET`/`HEAD` for files — hence `POST /api/auth/login` returned 405.

### Fix

Uncommented and corrected the proxy block:

```diff
-    # Optional: proxy api requests to backend
-    # location /api/ {
-    #     proxy_pass http://backend:8000/;
-    #     proxy_set_header Host $host;
-    #     proxy_set_header X-Real-IP $remote_addr;
-    # }
+    location /api/ {
+        proxy_pass http://backend:8000;
+        proxy_set_header Host $host;
+        proxy_set_header X-Real-IP $remote_addr;
+        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
+        proxy_set_header X-Forwarded-Proto $scheme;
+    }
```

> **Important:** `proxy_pass http://backend:8000` (without trailing `/`) preserves the `/api/` prefix in the forwarded request, which matches the backend's route definitions (e.g., `/api/auth/login`).

### Files Modified

- `frontend/nginx.conf` — enabled and corrected the API proxy block

---

## Summary of All Changes

| # | Issue | File(s) Modified | Status |
|---|-------|-------------------|--------|
| 1 | Missing `.env` & obsolete `version` | `docker-compose.yml`, `.env` | ✅ Fixed |
| 2 | Missing `package-lock.json` | `frontend/Dockerfile` | ✅ Fixed |
| 3 | Tables not created before seed | `backend/seed.py` | ✅ Fixed |
| 4 | passlib + bcrypt incompatibility | `backend/app/core/security.py`, `backend/requirements.txt` | ✅ Fixed |
| 5 | Nginx not proxying API requests | `frontend/nginx.conf` | ✅ Fixed |

## Post-Fix Commands

```bash
# Rebuild and restart all services
docker compose up -d --build

# Run the database seed (creates tables + admin user)
docker exec -it nms_backend python seed.py

# Default login credentials
# Username: admin
# Password: admin
```

> ⚠️ **Security Reminder:** Change the default admin password and update `SECRET_KEY` and `POSTGRES_PASSWORD` in `.env` before deploying to production.
