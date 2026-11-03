import { afterEach, describe, expect, it, vi } from 'vitest';
import { frameflowRequest } from './client';
describe('FrameFlow transport', () => {
  afterEach(() => vi.restoreAllMocks());
  it('reads JSON', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('{"status":"ok"}'),
    );
    expect(await frameflowRequest('/api/health')).toEqual({ status: 'ok' });
  });
  it('normalizes actionable errors', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: 'NO_CREDIT', message: '额度不足', retryable: false },
        }),
        { status: 402 },
      ),
    );
    await expect(frameflowRequest('/api/generations')).rejects.toMatchObject({
      code: 'NO_CREDIT',
      message: '额度不足',
      status: 402,
      retryable: false,
    });
  });
  it('preserves the idempotency header and adds JSON content type', async () => {
    const fetch = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response('{}'));
    await frameflowRequest('/api/generations', {
      method: 'POST',
      body: '{}',
      headers: { 'Idempotency-Key': 'test' },
    });
    const headers = fetch.mock.calls[0]?.[1]?.headers as Headers;
    expect(headers.get('Idempotency-Key')).toBe('test');
    expect(headers.get('Content-Type')).toBe('application/json');
  });
  it('reports non-JSON errors', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('unavailable', { status: 503 }),
    );
    await expect(frameflowRequest('/api/health')).rejects.toMatchObject({
      status: 503,
      code: 'HTTP_ERROR',
    });
  });
});
