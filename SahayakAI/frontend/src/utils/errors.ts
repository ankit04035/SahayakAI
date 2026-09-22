import { ApiErrorEnvelope } from '../types/api';

export function getErrorMessage(error: unknown): string {
  if (!error) return 'An unexpected error occurred.';
  if (typeof error === 'string') return error;

  // Handle parsed ApiErrorEnvelope
  if (typeof error === 'object' && 'message' in error && typeof (error as any).message === 'string') {
    return (error as ApiErrorEnvelope).message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
}
