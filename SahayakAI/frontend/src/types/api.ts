export interface ApiErrorEnvelope {
  status: 'error';
  error_code: string;
  message: string;
  details?: Array<{ loc: string[]; msg: string; type: string }> | Record<string, any> | null;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  database: 'ok' | 'error';
  ai_provider: string;
  version: string;
  demo_mode?: boolean;
}
