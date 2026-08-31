# LAN Network Monitoring System

## Overview
A comprehensive LAN Network Monitoring System designed to track network devices, monitor uptime and latency, and provide alerts. 

## Tech Stack
- **Backend:** FastAPI (Python)
- **Frontend:** React (TypeScript)
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
   docker-compose up --build
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

## Default Login
- **Username:** admin
- **Password:** admin

## Project Structure
- `/backend`: FastAPI backend application
- `/frontend`: React SPA frontend
- `/worker`: Python background worker for network monitoring
- `/docker`: Miscellaneous docker config files

## API Documentation
Once running, the API documentation is available at:
[http://localhost:8000/docs](http://localhost:8000/docs)

## Development Phases
- **Phase 1A:** Core Infrastructure & Authentication
- **Phase 1B:** Network Monitoring Engine
- **Phase 1C:** Device Management API
- **Phase 1D:** Dashboard & Analytics
- **Phase 1E:** Alerting & Notifications
