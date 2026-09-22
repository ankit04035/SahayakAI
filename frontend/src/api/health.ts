import { apiRequest } from './client';
import { HealthResponse } from '../types/api';

export async function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health');
}
