export type UserRole = "ADMIN" | "SUPERVISOR" | "OPERATOR";

export type RequestStatus =
  | "QUEUED"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface ServiceRequest {
  id: string;
  title: string;
  description: string;
  status: RequestStatus;
  progress_percent: number;
  current_step: string | null;
  error_message: string | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
}

export interface ApiResponse<T> {
  data: T;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    total_pages: number;
    current_page: number;
  };
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Array<{ field: string; message: string; code: string }>;
  };
}

export interface WebSocketEventEnvelope<T = Record<string, unknown>> {
  event_id: string;
  event_type: string;
  occurred_at: string;
  request_id: string;
  data: T;
}
