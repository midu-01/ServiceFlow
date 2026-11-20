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

### Phase 3: Architecture & Technical Contracts
- [x] Authored `docs/architecture.md` detailing system topology, component boundaries, and asynchronous execution pipeline.
- [x] Engineered decoupled messaging architecture using Redis:
  - **DB 0** allocated as Celery task queue broker.
  - **DB 1** allocated as dedicated real-time event Pub/Sub transport.
- [x] Specified worker concurrency rules: `worker_prefetch_multiplier = 1` for fair dispatch and `acks_late = True` for crash resilience.
- [x] Formulated relational data model with PostgreSQL ERD, explicit B-tree indexing on `(created_by_id, status)` and `created_at DESC`.
- [x] Authored `docs/api.md` establishing REST conventions, semantic HTTP status codes, standard response envelopes (`data`, `meta`, `error`), and complete schema contracts for Auth, Service Requests, and Health probes.
- [x] Authored `docs/websocket-events.md` standardizing real-time event envelope (`event_id`, `event_type`, `occurred_at`, `request_id`, `data`), 6-event catalog, ping/pong keepalive, and client auto-reconnection state rehydration.
- [x] Verified and reinforced `.gitignore` to prevent any internal configuration or scratch files from being exposed on GitHub.

### Phase 4: Frontend and Backend Project Skeletons
- [x] **Backend Architecture Scaffolded (FastAPI + Python 3.12):**
  - Designed clean layered modular structure: `core/`, `api/v1/endpoints/`, `db/models/`, `schemas/`, `services/`, `repositories/`, `workers/`, `realtime/`.
  - Configured environment-driven configuration via `pydantic-settings` with validated defaults.
  - Implemented structured logging format (`app/core/logging.py`) with date/time, log levels, and line numbers.
  - Established unified error handling hierarchy (`AppError`, `NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`) mapping directly to HTTP semantic status codes and standard JSON error envelopes.
  - Built root liveness (`GET /health`) and readiness (`GET /ready`) probes verifying PostgreSQL and Redis dependencies.
  - Configured Celery worker application configuration (`worker_prefetch_multiplier=1`, `acks_late=True`, `CELERY_WORKER_CONCURRENCY`).
  - Implemented asynchronous Redis Pub/Sub listener lifespan task in `app/main.py`.
  - Authored automated tests in `backend/tests/unit/test_health.py` and validated passing test suite.
- [x] **Frontend Architecture Scaffolded (Next.js 15 App Router + TypeScript):**
  - Initialized Next.js with TypeScript, React 19, and Tailwind CSS.
  - Configured `tsconfig.json` with `@/*` path aliases.
  - Configured TanStack Query provider (`Providers`) for surgical cache mutation on WebSocket events.
  - Engineered strongly-typed client API abstraction (`frontend/src/lib/api/client.ts`) with custom `ApiClientError` and automated bearer token injection.
  - Built responsive base layout (`frontend/src/app/layout.tsx`) and operational verification view (`frontend/src/app/page.tsx`).
  - Verified static compilation with `next build` and strict type checks with `tsc --noEmit` (zero errors).

### Phase 5: Docker Compose and Local Infrastructure
- [x] **Containerized Backend (`backend/Dockerfile`):**
  - Multi-stage build on `python:3.12-slim`.
  - Enforced security best practice by provisioning a non-root `appuser` (UID 10001).
  - Pre-installed runtime system dependencies (`curl` for healthcheck, `libpq` for PostgreSQL).
  - Can serve both API server (`uvicorn`) and background worker (`celery`) from a single container image.
- [x] **Containerized Frontend (`frontend/Dockerfile`):**
  - Built on `node:20-alpine` with deterministic `npm ci`.
  - Configured for hot-reloading in containerized local environments.
- [x] **Orchestration Topology (`docker-compose.yml`):**
  - Declared 5 coordinated services: `postgres` (16-alpine), `redis` (7-alpine), `api` (FastAPI), `worker` (Celery), and `frontend` (Next.js).
  - Established deterministic dependency chains using active health checks:
    - `api` and `worker` depend on `postgres` (`service_healthy`) and `redis` (`service_healthy`).
    - `frontend` depends on `api` (`service_healthy`).
  - Isolated database persistence via named Docker volume `serviceflow_postgres_data` and Redis state via `serviceflow_redis_data`.
  - Dedicated bridge network `serviceflow_network`.
- [x] **Environment Configuration Baseline:**
  - Consolidated root `.env.example` defining all application, database, broker, security, and port settings.
  - Validated compose syntax and variable resolution with `docker compose config`.

### Phase 6: Database Design and Migrations
- [x] **SQLAlchemy 2.0 Async ORM Models (`backend/app/db/models/`):**
  - Designed `User` entity (`users` table) with UUID primary key, unique constraints on `username` and `email`, index on `role`, and cascading one-to-many relationship with `ServiceRequest`.
  - Designed `ServiceRequest` entity (`service_requests` table) with:
    - UUID primary key, required `title` ($\le 100$) and `description` ($\le 1000$).
    - `status` enum (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`) with database-level check constraint.
    - `progress_percent` with check constraint enforcing $0 \le \text{progress} \le 100$.
    - Foreign key relationship to `users.id` with `ON DELETE CASCADE`.
    - Lifecycle timestamps: `created_at`, `updated_at`, `started_at`, `completed_at`, `cancelled_at`.
- [x] **Relational Indexing Architecture:**
  - `idx_service_requests_status`: Speeds up queue state queries.
  - `idx_service_requests_created_by_id`: Scopes queries for operator self-service.
  - `idx_service_requests_created_at_desc`: Accelerates default chronological dashboard listings.
  - Composite `idx_service_requests_creator_status`: Enhances compound filtering on creator + status.
- [x] **Alembic Version-Controlled Migrations (`backend/alembic/`):**
  - Initialized Alembic with async driver template (`asyncpg`).
  - Dynamically linked `alembic/env.py` to `settings.DATABASE_URL` and `Base.metadata`.
  - Authored reversible initial schema revision `0001_initial_schema.py` (`upgrade` and `downgrade`).
  - Validated offline SQL generation (`alembic upgrade --sql base:0001_initial_schema`).
- [x] **Automated Testing (`backend/tests/unit/test_models.py`):**
  - Tested table metadata registration and async database persistence with in-memory SQLite (`aiosqlite`).
  - Verified relationship back-population and foreign key integrity.

### Phase 7: Backend Core, Configuration and Error Handling
- [x] **Production-Safe Configuration Validation:**
  - Strengthened `Settings` in `app/core/config.py` with Pydantic model validator enforcing strong 32+ character secrets and disabling debug mode when running in production.
- [x] **Request Correlation & Structured Logging:**
  - Implemented `request_correlation_middleware` in `app/main.py` utilizing Python `contextvars`.
  - Injected `X-Request-ID` across HTTP response headers and into every structured log line (`CorrelationIdFilter`).
  - Added request execution duration instrumentation (`time.perf_counter()`).
- [x] **Robust Global Error Handling Strategy:**
  - Extended exception hierarchy in `app/core/errors.py`: `AppError`, `NotFoundError` (404), `ConflictError` (409), `UnauthorizedError` (401), `ForbiddenError` (403), `ValidationError` (422).
  - Implemented `generic_exception_handler` capturing unhandled 500 exceptions, logging full diagnostic tracebacks server-side, and returning sanitized error envelopes to clients without stack trace leakage.
- [x] **Asynchronous Repository Pattern:**
  - Built generic `BaseRepository[ModelType]` providing type-safe CRUD operations, pagination, and session management.
  - Implemented `UserRepository` with optimized `get_by_username` and `get_by_email` queries.
  - Implemented `ServiceRequestRepository` with multi-dimensional filtering (`created_by_id`, `status`, text search) and atomic cancellation (`UPDATE ... WHERE status = 'QUEUED'`).
  - Created dedicated `get_worker_session()` context manager in `app/db/session.py` to isolate Celery task database sessions from HTTP request loops.
- [x] **Comprehensive Unit Testing:**
  - Added `backend/tests/unit/test_errors.py` (error envelopes, 500 sanitization, correlation ID retention).
  - Added `backend/tests/unit/test_repositories.py` (user lookup, filtered listing, atomic cancellation, progress updates).
  - Verified 100% passing test suite across all 10 unit tests.

### Phase 8: JWT Authentication and Role-Based Access Control
- [x] **Argon2id Password Security:**
  - Configured memory-hard password hashing via `argon2-cffi` (`time_cost=2`, `memory_cost=19MiB`, `parallelism=1`).
  - Implemented constant-time password verification preventing timing attack vectors.
  - Implemented generic credential failure error handling ("Invalid username or password") to avoid user enumeration.
- [x] **Stateless JWT Tokens with Dual Transport:**
  - Authored token generation and validation in `app/core/security.py` using HMAC-SHA256 (`HS256`).
  - Built support for both standard `Authorization: Bearer <token>` headers and secure `serviceflow_access_token` cookies (`HttpOnly`, `SameSite=Lax`, `Secure` in non-dev).
- [x] **Server-Side Role-Based Access Control (RBAC):**
  - Engineered `CurrentUserDep` (`get_current_user`) resolving user entity dynamically from PostgreSQL by token `sub` (UUID).
  - Enforced account status check (`user.is_active` rejects inactive accounts with HTTP 403 Forbidden).
  - Implemented `require_role(*allowed_roles)` dependency inspecting authoritative database role rather than client claims.
- [x] **Authentication Endpoints (`app/api/v1/endpoints/auth.py`):**
  - `POST /api/v1/auth/login`: Authenticates credentials, sets HttpOnly cookie, returns `TokenData` response.
  - `GET /api/v1/auth/me`: Resolves profile of authenticated caller.
  - `POST /api/v1/auth/logout`: Clears session cookie.
- [x] **Idempotent User Seeding Script (`scripts/seed_users.py`):**
  - Created executable script generating default `admin`, `supervisor`, and `operator` credentials safely from environment variables or secure defaults.
- [x] **Automated Authentication Test Suite (`backend/tests/unit/test_auth.py`):**
  - Verified login success, invalid password rejection, non-existent user handling, inactive user blocking.
  - Verified `/me` profile endpoint with both Bearer header and HttpOnly cookie.
  - Verified role-based authorization: operator access denied (403) on supervisor endpoint, supervisor allowed (200).
  - Total test count expanded to 16 unit tests, all passing cleanly.

### Phase 9: Service Request REST API
- [x] **Service Request Schemas & Contracts (`app/schemas/service_request.py`):**
  - Designed `ServiceRequestCreate` with strict field validation (`title` 3–100 chars, `description` 10–1000 chars).
  - Designed `ServiceRequestResponse` exposing entity state, progress, and lifecycle milestones.
  - Designed `ServiceRequestCancelResponse` indicating termination status and timestamp.
- [x] **Business Service Layer (`app/services/service_request_service.py`):**
  - Encapsulated business rules outside of HTTP route handlers.
  - Controlled request submission: server sets initial `QUEUED` state, 0% progress, creator ID from session token, and timestamps.
  - Dispatches background Celery task `process_service_request.delay(request_id)` upon commit.
  - Emits real-time `service_request.created` event via Redis Pub/Sub.
  - Enforced strict role-scoping: Operators only receive their own requests; Supervisors and Admins view global queue.
  - Enforced ownership verification on detail inspection: non-owners receive `403 Forbidden`.
  - Implemented atomic cancellation guard: only requests in `QUEUED` state can be cancelled; in-flight (`PROCESSING`) or terminal requests reject with `409 Conflict`.
- [x] **REST Endpoints (`app/api/v1/endpoints/service_requests.py`):**
  - `POST /api/v1/service-requests`: 201 Created with `Location` header.
  - `GET /api/v1/service-requests`: Paginated response (`meta` with `total`, `limit`, `offset`, `total_pages`, `current_page`) with `status` and `search` query filters.
  - `GET /api/v1/service-requests/{id}`: Detail view with ownership checks.
  - `POST /api/v1/service-requests/{id}/cancel`: Atomic state cancellation.
- [x] **Automated Test Suite Expansion (`backend/tests/unit/test_service_requests.py`):**
  - Validated submission (201 Created), validation errors (422), role scoping in listings, query filtering, detail view permissions (403), 404 handling, and atomic cancellation (409 on processing).
  - Test suite grew to 22 unit tests passing in $< 22\text{ s}$.

### Phase 10: Background Processing and Concurrency with Celery
- [x] **Asynchronous Celery Architecture & Worker Tuning:**
  - Configured Celery worker with `worker_prefetch_multiplier = 1` for fair dispatch across long-running workloads, preventing task starvation.
  - Enabled late task acknowledgment (`task_acks_late = True`) guaranteeing that crashed or terminated worker tasks are re-queued rather than lost.
  - Enabled task auto-discovery (`celery_app.autodiscover_tasks(["app.workers.tasks"])`).
- [x] **Multi-Step Processing Simulation Pipeline (`app/workers/tasks/request_tasks.py`):**
  - Implemented 5-step discrete workflow:
    1. Precondition validation (20%)
    2. Environment preparation (40%)
    3. Multi-stage service workload (60%)
    4. Operational constraint verification (80%)
    5. Final result commitment (100%)
  - Parameterized discrete step delays via `settings.PROCESSING_STEP_DELAY_SECONDS`.
  - Transactionally commits step progress to PostgreSQL and broadcasts `service_request.progress_updated` events via Redis Pub/Sub.
- [x] **Concurrency & Race-Condition Guards:**
  - **Pre-Execution Check:** Verifies request status before starting. If pre-cancelled, the task exits cleanly without transitioning to `PROCESSING`.
  - **In-Flight Cancellation Detection:** Polls database state at each step; if an operator/supervisor cancels the request while the worker is between steps, the pipeline aborts immediately.
  - **Worker Session Scoping:** Instantiates independent database sessions per task via `get_worker_session()`, strictly avoiding cross-coroutine transaction collisions.
- [x] **Resilience & Sanitized Failure Handling:**
  - Traps step exceptions, records sanitized user-facing error message in PostgreSQL, sets status to `FAILED`, and broadcasts `service_request.failed` event while preserving full debug stack traces server-side.
- [x] **Automated Concurrency Testing (`backend/tests/unit/test_worker_tasks.py`):**
  - Tested normal pipeline completion (`QUEUED` $\to$ `PROCESSING` $\to$ `COMPLETED`, 100% progress).
  - Tested pre-cancellation idempotency guard.
  - Tested non-existent ID handling.
  - Tested concurrent execution of 4 simultaneous requests running in parallel with isolated sessions without deadlocks.
  - Total unit tests grew to 26 tests, all passing cleanly.

### Phase 11: Redis Pub/Sub and Native WebSocket Communication
- [x] **Native WebSocket Endpoint (`app/api/v1/endpoints/websocket.py`):**
  - Implemented `/api/v1/ws/service-requests` with full-duplex communication.
  - Handshake security: validates client `Origin` against allowed frontend whitelist.
  - Authenticates connection before acceptance: decodes JWT token from query parameter (`?token=...`) or HttpOnly cookie (`serviceflow_access_token`) and validates user account active status in PostgreSQL.
  - Rejects unauthorized or forged attempts with WebSocket policy violation code `1008`.
  - Dispatches `connection.ready` handshake frame upon successful registration.
  - Listens for client keepalive `ping` text frames and responds with `pong`.
- [x] **Server-Side Authorization & Permission Filtering (`app/realtime/manager.py`):**
  - Enhanced `ConnectionManager` with structured `ClientConnection` tracking `user_id` and authoritative `UserRole`.
  - Implemented zero-overhead permission filtering:
    - Supervisors and Admins receive all service request events across the entire organization.
    - Operators receive only events matching their own `created_by_id`.
  - Dead socket pruning: automatically purges broken or abruptly dropped sockets without blocking other active connections.
- [x] **Resilient Redis Pub/Sub Subscriber (`app/realtime/subscriber.py`):**
  - Long-running async task managed via FastAPI lifespan context.
  - Subscribes to channel `service_flow:events`.
  - Implemented exponential reconnection backoff (up to 30s) handling Redis broker restarts or network interruptions gracefully.
- [x] **Automated WebSocket Test Suite (`backend/tests/unit/test_websocket.py`):**
  - Tested connection handshake, `connection.ready` reception, and ping/pong heartbeat.
  - Tested rejection of invalid token (code 1008).
  - Tested rejection of unauthorized origin (code 1008).
  - Tested role-filtered event distribution: verified supervisor receives all events while operators are strictly shielded from other operators' events.
  - Entire backend test suite grew to 30 unit tests passing cleanly.

### Phase 12: Frontend Foundation and Design System
- [x] **Accessible UI Component Library (`frontend/src/components/ui/`):**
  - Engineered component suite following shadcn/Tailwind design tokens:
    - `Button`: Multiple variants (`default`, `destructive`, `outline`, `secondary`, `ghost`, `link`), sizes, and accessible loading spinner state (`isLoading`).
    - `Input` & `Textarea`: Form controls with field validation error messaging and focus ring styling.
    - `Card`: Composable structural primitives (`Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`).
    - `Badge`: Semantic pill badges.
    - `StatusBadge`: Purpose-built component mapping `RequestStatus` (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`) with matching Lucide icons, status-specific palettes, and animated spinners.
    - `Progress`: Smoothly animated progress bar indicator with percentage readouts.
    - `Alert`: Accessible notification banners (`default`, `success`, `warning`, `destructive`).
    - `Dialog`: Accessible modal dialog with focus management, backdrop blur, escape-key listener, and action buttons.
- [x] **Application Layout & Navigation (`frontend/src/components/layout/navbar.tsx`):**
  - Built sticky navigation header with brand iconography, live WebSocket sync beacon, role badge display, and dynamic navigation links (`Dashboard`, `Service Requests`, `New Request`).
  - Integrated into root `layout.tsx`.
- [x] **TanStack Query Key Factory (`frontend/src/lib/api/query-keys.ts`):**
  - Centralized hierarchical query keys for auth (`authKeys`) and service requests (`requestKeys.all`, `requestKeys.list(filters)`, `requestKeys.detail(id)`).
- [x] **Static Compilation & Type Verification:**
  - Verified Next.js 15 production build (`next build`) and strict TypeScript checks (`tsc --noEmit`) with 0 errors.
