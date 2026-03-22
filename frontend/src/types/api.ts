export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
  meta: Record<string, unknown>;
}

export interface HealthStatus {
  status: string;
  service?: string;
  environment?: string;
  timestamp?: string;
  ports?: {
    backend: number;
    frontend: number;
  };
}

export interface ReadinessStatus {
  status: string;
  dependencies: Record<string, Record<string, string>>;
}
