# ServiceFlow: REST API Specification & Contract

> **API Version:** v1  
> **Base Path:** `/api/v1`  
> **Protocol:** HTTPS / JSON  
> **Authentication:** Bearer Token (JWT in `Authorization` header)  

---

## 1. Global Conventions & Standards

### 1.1 Content Negotiation
* Requests with a JSON body must include header: `Content-Type: application/json`.
* Responses return `Content-Type: application/json`.

### 1.2 Authentication Header
All protected endpoints require the HTTP Authorization header:
```http
Authorization: Bearer <access_token>
```

### 1.3 Standard Response Formats

#### Single Resource Response
```json
{
  "data": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "title": "Database Optimization",
    "status": "QUEUED"
  }
}
```

#### Paginated Collection Response
```json
{
  "data": [
    { "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7", "title": "Database Optimization", "status": "PROCESSING" }
  ],
  "meta": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "total_pages": 3,
    "current_page": 1
  }
}
```

#### Error Envelope
```json
{
  "error": {
    "code": "resource_conflict",
    "message": "Request is not in QUEUED state and cannot be cancelled",
    "details": []
  }
}
```

---

## 2. Health & Diagnostics Endpoints

### 2.1 Liveness Probe
Checks if the web server process is alive.

* **Endpoint:** `GET /health`
* **Authentication:** None (Public)
* **Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-11-20T19:50:00Z"
}
```

### 2.2 Readiness Probe
Checks if the application dependencies (PostgreSQL and Redis) are connected and ready to accept traffic.

* **Endpoint:** `GET /ready`
* **Authentication:** None (Public)
* **Response (Healthy):** `200 OK`
```json
{
  "status": "ready",
  "dependencies": {
    "database": "connected",
    "redis": "connected"
  },
  "timestamp": "2026-11-20T19:50:00Z"
}
```
* **Response (Degraded):** `503 Service Unavailable`
```json
{
  "status": "not_ready",
  "dependencies": {
    "database": "connected",
    "redis": "connection_failed"
  },
  "timestamp": "2026-11-20T19:50:00Z"
}
```

---

## 3. Authentication Endpoints

### 3.1 User Login
Authenticates user credentials and issues an access token.

* **Endpoint:** `POST /api/v1/auth/login`
* **Authentication:** None (Public)
* **Request Body:**
```json
{
  "username": "operator_jane",
  "password": "SecurePassword123!"
}
```
* **Validation Rules:**
  * `username`: String, 3–50 characters, required.
  * `password`: String, 8–100 characters, required.
* **Success Response:** `200 OK`
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "username": "operator_jane",
      "email": "jane@serviceflow.internal",
      "role": "OPERATOR"
    }
  }
}
```
* **Error Responses:**
  * `401 Unauthorized` (`invalid_credentials`): Username or password incorrect.
  * `422 Unprocessable Entity` (`validation_error`): Missing or malformed fields.

---

### 3.2 Current User Context
Resolves the currently authenticated user's profile and permissions.

* **Endpoint:** `GET /api/v1/auth/me`
* **Authentication:** Required (Any authenticated role)
* **Success Response:** `200 OK`
```json
{
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "username": "operator_jane",
    "email": "jane@serviceflow.internal",
    "role": "OPERATOR",
    "is_active": true,
    "created_at": "2026-11-20T10:00:00Z"
  }
}
```
* **Error Responses:**
  * `401 Unauthorized` (`invalid_token`): Token expired, invalid signature, or missing.

---

### 3.3 User Logout
Invalidates the client-side session.

* **Endpoint:** `POST /api/v1/auth/logout`
* **Authentication:** Required
* **Success Response:** `200 OK`
```json
{
  "data": {
    "message": "Successfully logged out"
  }
}
```

---

## 4. Service Request Endpoints

### 4.1 Create Service Request
Submits a new service request and enqueues background processing.

* **Endpoint:** `POST /api/v1/service-requests`
* **Authentication:** Required (Roles: `OPERATOR`, `SUPERVISOR`, `ADMIN`)
* **Headers:** `Location: /api/v1/service-requests/{id}` on creation
* **Request Body:**
```json
{
  "title": "Customer Data Sync Pipeline",
  "description": "Trigger full synchronization of customer orders and billing history across secondary systems."
}
```
* **Validation Rules:**
  * `title`: String, min 3, max 100 characters.
  * `description`: String, min 10, max 1000 characters.
* **Success Response:** `201 Created`
```json
{
  "data": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "title": "Customer Data Sync Pipeline",
    "description": "Trigger full synchronization of customer orders and billing history across secondary systems.",
    "status": "QUEUED",
    "progress_percent": 0,
    "current_step": null,
    "error_message": null,
    "created_by_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created_at": "2026-11-20T19:50:30Z",
    "updated_at": "2026-11-20T19:50:30Z",
    "started_at": null,
    "completed_at": null,
    "cancelled_at": null
  }
}
```
* **Error Responses:**
  * `422 Unprocessable Entity` (`validation_error`): Title or description constraint violation.
  * `401 Unauthorized` (`unauthorized`): Missing or invalid token.

---

### 4.2 List Service Requests
Retrieves paginated service requests with filtering. Operators receive only their own requests; Supervisors and Admins receive all requests.

* **Endpoint:** `GET /api/v1/service-requests`
* **Authentication:** Required (Roles: `OPERATOR`, `SUPERVISOR`, `ADMIN`)
* **Query Parameters:**
  | Parameter | Type | Required | Default | Description |
  | :--- | :--- | :---: | :---: | :--- |
  | `status` | string | No | - | Filter by exact state: `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED` |
  | `search` | string | No | - | Substring match against `title` or `description` |
  | `limit` | integer | No | `20` | Number of items per page (min 1, max 100) |
  | `offset` | integer | No | `0` | Number of records to skip for pagination |
* **Success Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "title": "Customer Data Sync Pipeline",
      "description": "Trigger full synchronization of customer orders...",
      "status": "PROCESSING",
      "progress_percent": 40,
      "current_step": "Step 2: Data Extraction",
      "error_message": null,
      "created_by_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2026-11-20T19:50:30Z",
      "updated_at": "2026-11-20T19:50:36Z",
      "started_at": "2026-11-20T19:50:32Z",
      "completed_at": null,
      "cancelled_at": null
    }
  ],
  "meta": {
    "total": 1,
    "limit": 20,
    "offset": 0,
    "total_pages": 1,
    "current_page": 1
  }
}
```

---

### 4.3 Get Service Request Detail
Retrieves the complete state of a specific service request.

* **Endpoint:** `GET /api/v1/service-requests/{id}`
* **Authentication:** Required
* **Path Parameters:**
  * `id`: UUID of the service request.
* **Access Rules:**
  * Operators may only query requests where `created_by_id == current_user.id`.
  * Supervisors and Admins may query any valid request.
* **Success Response:** `200 OK`
```json
{
  "data": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "title": "Customer Data Sync Pipeline",
    "description": "Trigger full synchronization of customer orders...",
    "status": "COMPLETED",
    "progress_percent": 100,
    "current_step": "Step 5: Finalization",
    "error_message": null,
    "created_by_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created_at": "2026-11-20T19:50:30Z",
    "updated_at": "2026-11-20T19:50:50Z",
    "started_at": "2026-11-20T19:50:32Z",
    "completed_at": "2026-11-20T19:50:50Z",
    "cancelled_at": null
  }
}
```
* **Error Responses:**
  * `403 Forbidden` (`forbidden`): Operator attempting to access another user's request.
  * `404 Not Found` (`not_found`): Request UUID does not exist.

---

### 4.4 Cancel Service Request
Cancels an unstarted request. Strictly restricted to requests currently in `QUEUED` state.

* **Endpoint:** `POST /api/v1/service-requests/{id}/cancel`
* **Authentication:** Required
* **Access Rules:**
  * Operators may cancel only their own `QUEUED` requests.
  * Supervisors and Admins may cancel any `QUEUED` request.
* **Success Response:** `200 OK`
```json
{
  "data": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "status": "CANCELLED",
    "progress_percent": 0,
    "cancelled_at": "2026-11-20T19:51:10Z",
    "message": "Service request cancelled successfully"
  }
}
```
* **Error Responses:**
  * `409 Conflict` (`resource_conflict`): The request is already in `PROCESSING`, `COMPLETED`, `FAILED`, or `CANCELLED`.
  * `403 Forbidden` (`forbidden`): Operator attempting to cancel another user's request.
  * `404 Not Found` (`not_found`): Request UUID does not exist.

---

## 5. HTTP Status Code Reference

| Status Code | Meaning | Context of Usage |
| :--- | :--- | :--- |
| **`200 OK`** | Request succeeded | `GET` queries, `POST /login`, `POST /cancel` |
| **`201 Created`** | Resource created | `POST /service-requests` (with `Location` header) |
| **`400 Bad Request`** | Malformed request | Bad JSON formatting or unparseable payload |
| **`401 Unauthorized`** | Authentication required | Missing, invalid, or expired JWT token |
| **`403 Forbidden`** | Authorization denied | Authenticated, but lacking permission or ownership |
| **`404 Not Found`** | Resource missing | Request UUID not found in PostgreSQL |
| **`409 Conflict`** | State transition conflict | Attempting to cancel a non-QUEUED request |
| **`422 Unprocessable`** | Semantic validation failure | Field lengths, missing required fields (Pydantic) |
| **`500 Internal Error`**| Unexpected server failure | Sanitized error response; stack traces concealed |
