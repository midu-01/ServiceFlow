# ServiceFlow

A real-time, resilient service request management system designed for concurrent processing and live operational visibility.

## Overview

ServiceFlow addresses operational bottlenecks in manual service request management by enabling:
- **Operators** to submit and monitor service requests with instantaneous feedback.
- **Supervisors & Admins** to oversee lifecycle transitions, inspect processing details, and track live progress across concurrent background workers.

## Tech Stack

- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy 2.0 (Async), Alembic, Pydantic
- **Data & Caching:** PostgreSQL, Redis
- **Background Tasks:** Celery with Redis broker
- **Real-Time Communication:** Native WebSockets backed by Redis Pub/Sub
- **Authentication & Security:** JWT (Argon2id), Role-Based Access Control (RBAC)
- **Infrastructure:** Docker Compose

## Documentation

- [Engineering Journal](engineering.md)
