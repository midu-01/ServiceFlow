# Engineering Journal: ServiceFlow

> **Author:** Lead Engineer  
> **Project:** ServiceFlow — Real-Time Service Request Management System  
> **Purpose:** Technical documentation, architectural design rationale, engineering decisions, and implementation progress log.

---

## 1. System Vision & Architecture

ServiceFlow is a distributed, event-driven web platform designed to streamline asynchronous service request workflows with real-time operational visibility.

### 1.1 The Core Problem
In conventional service architectures, long-running operations block HTTP threads or rely on inefficient client-side polling. This causes high server load, poor responsiveness, and delayed status visibility for operations teams and supervisors.

### 1.2 Architectural Foundation
To ensure responsiveness, fault-tolerance, and real-time streaming, I selected an event-driven architecture with clear separation of concerns:
- **FastAPI (ASGI):** Handles high-throughput non-blocking HTTP requests and native WebSocket connections.
- **Celery + Redis:** Asynchronous background task queue decoupling workload execution from the HTTP lifecycle.
- **Redis Pub/Sub:** Low-latency event bus propagating background worker progress to active WebSocket connections.
- **PostgreSQL + SQLAlchemy 2.0:** Relational persistence with ACID compliance, strong constraints, and schema versioning via Alembic.
- **Next.js (App Router) + TypeScript + TanStack Query:** Modern reactive frontend with optimistic updates and type safety.

---

## 2. Technology Stack & Design Decisions

### 2.1 Backend: Python (FastAPI)
* **Decision:** Python 3.11+ with FastAPI.
* **Why:** Native ASGI async/await event loop for I/O bound operations, Pydantic v2 data validation, and automated OpenAPI documentation.

### 2.2 Concurrency: Celery with Redis Broker
* **Decision:** Dedicated Celery worker pool using Redis as task broker.
* **Why:** In-process threads (or background tasks tied to web processes) are fragile and do not survive application restarts. Celery provides horizontal scaling, retry mechanisms, and task isolation.

### 2.3 Real-Time Communication: Native WebSockets via Redis Pub/Sub
* **Decision:** Full-duplex WebSocket connections backed by a Redis Pub/Sub event bus.
* **Why:** Eliminates polling overhead and minimizes frame size. Redis Pub/Sub allows multiple API server instances to broadcast worker events to connected clients seamlessly.

### 2.4 Persistence: PostgreSQL with SQLAlchemy Async
* **Decision:** PostgreSQL with SQLAlchemy 2.0 (asyncpg) and Alembic migrations.
* **Why:** Service requests demand strict transactional integrity, foreign key relations, and deterministic status state machines.

### 2.5 Frontend: Next.js + TanStack Query + Tailwind CSS
* **Decision:** Next.js (App Router), TypeScript, and TanStack Query.
* **Why:** TanStack Query allows cache invalidation and surgical updates upon receiving WebSocket events, preventing full page re-fetching.

---

## 3. Implementation Log & Phase Progress

### Phase 1: Project Initialization & Repository Setup
- [x] Initialized Git repository on `main` branch.
- [x] Configured `.gitignore` for Python, Node.js, Next.js, Docker, and environment files.
- [x] Excluded internal planning documents from Git tracking.
- [x] Established project baseline with `README.md` and initial `engineering.md` journal.
- [x] Created core directory layout: `frontend/`, `backend/`, and `docs/`.
- [x] Added `docs/progress.md` tracking the 18-phase implementation roadmap.
- [x] Connected and synchronized with remote repository: `https://github.com/midu-01/ServiceFlow.git`.

### Phase 2: Requirements Analysis & Business Workflow
- [x] Formalized system problem statement and core business objectives in `docs/requirements.md`.
- [x] Defined granular user personas and complete Permission Matrix for **Operator**, **Supervisor**, and **Admin**.
- [x] Designed the finite state machine (FSM) for service request lifecycles (`QUEUED` $\to$ `PROCESSING` $\to$ `COMPLETED` / `FAILED` / `CANCELLED`).
- [x] Codified strict state transition invariants:
  - Cancellation is restricted exclusively to requests in `QUEUED` state.
  - Transitioning from `PROCESSING` to `CANCELLED` is blocked with `409 Conflict`.
  - Worker tasks enforce idempotency before beginning workload execution.
- [x] Specified testable functional requirements (`REQ-001` through `REQ-012`) with explicit Given-When-Then acceptance criteria.
- [x] Defined measurable non-functional targets (`NFR-001` through `NFR-007`) for latency ($< 100\text{ ms}$ REST, $< 250\text{ ms}$ WS event distribution), concurrency, reliability, and security.
- [x] Created a full Requirements Traceability Matrix mapping each requirement to its delivery phase.
