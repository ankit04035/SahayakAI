import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiRequest, getBaseUrl, ApiError, setCsrfToken } from '../api/client';

describe('API Client Unit Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    setCsrfToken(null);
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('resolves and normalizes base URL correctly', () => {
    const url = getBaseUrl();
    expect(url).toBeDefined();
    expect(url.endsWith('/api')).toBe(true);
  });

  it('does not derive account identity from localStorage and includes session cookies', async () => {
    localStorage.setItem('sahayakai_user_id', '42');

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({ status: 'ok' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await apiRequest('/health');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = fetchMock.mock.calls[0][0];
    const calledOptions = fetchMock.mock.calls[0][1];

    expect(calledUrl).toContain('/api/health');
    expect(calledOptions.headers['X-User-Id']).toBeUndefined();
    expect(calledOptions.headers['Content-Type']).toBe('application/json');
    expect(calledOptions.credentials).toBe('include');
  });

  it('does not send an identity header when no account is selected', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({ status: 'ok' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await apiRequest('/health');

    const calledOptions = fetchMock.mock.calls[0][1];
    expect(calledOptions.headers['X-User-Id']).toBeUndefined();
  });

  it('allows explicit userId override in RequestOptions', async () => {
    localStorage.setItem('sahayakai_user_id', '1');

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({ status: 'ok' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await apiRequest('/documents', { userId: 99 });

    const calledOptions = fetchMock.mock.calls[0][1];
    expect(calledOptions.headers['X-User-Id']).toBe('99');
  });

  it('does not set Content-Type header when body is FormData', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({ id: 1, title: 'Uploaded' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const formData = new FormData();
    formData.append('key', 'value');

    await apiRequest('/documents/upload', {
      method: 'POST',
      body: formData,
    });

    const calledOptions = fetchMock.mock.calls[0][1];
    expect(calledOptions.headers['Content-Type']).toBeUndefined();
    expect(calledOptions.headers['X-User-Id']).toBeUndefined();
  });

  it('sends the in-memory CSRF token on state-changing requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({ ok: true }),
    });
    vi.stubGlobal('fetch', fetchMock);
    setCsrfToken('csrf-test-token');

    await apiRequest('/documents', { method: 'POST', body: JSON.stringify({ title: 'notes' }), userId: 7 });

    const calledOptions = fetchMock.mock.calls[0][1];
    expect(calledOptions.headers['X-User-Id']).toBe('7');
    expect(calledOptions.headers['X-CSRF-Token']).toBe('csrf-test-token');
  });

  it('parses structured backend error envelope correctly on 404', async () => {
    const errorEnvelope = {
      status: 'error',
      error_code: 'DOCUMENT_NOT_FOUND',
      message: 'Document with id 999 does not exist.',
      details: null,
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: vi.fn().mockResolvedValue(errorEnvelope),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiRequest('/documents/999')).rejects.toThrow(
      'Document with id 999 does not exist.'
    );

    try {
      await apiRequest('/documents/999');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(404);
      expect(err.errorCode).toBe('DOCUMENT_NOT_FOUND');
      expect(err.message).toBe('Document with id 999 does not exist.');
    }
  });

  it('parses validation error envelope on 422', async () => {
    const errorEnvelope = {
      status: 'error',
      error_code: 'VALIDATION_ERROR',
      message: 'Target role must be at least 2 characters long.',
      details: [{ loc: ['body', 'target_role'], msg: 'Too short', type: 'value_error' }],
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: vi.fn().mockResolvedValue(errorEnvelope),
    });
    vi.stubGlobal('fetch', fetchMock);

    try {
      await apiRequest('/career/profile', { method: 'POST', body: JSON.stringify({ target_role: 'X' }) });
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(422);
      expect(err.errorCode).toBe('VALIDATION_ERROR');
      expect(err.details).toHaveLength(1);
    }
  });

  it('handles network failure by throwing ApiError with NETWORK_ERROR code', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('Failed to fetch'));
    vi.stubGlobal('fetch', fetchMock);

    try {
      await apiRequest('/health');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(500);
      expect(err.errorCode).toBe('NETWORK_ERROR');
      expect(err.message).toContain('Failed to fetch');
    }
  });
});
