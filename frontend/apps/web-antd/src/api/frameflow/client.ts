export class FrameFlowApiError extends Error {
  constructor(
    message: string,
    public readonly code = 'HTTP_ERROR',
    public readonly retryable = false,
    public readonly status = 500,
  ) {
    super(message);
    this.name = 'FrameFlowApiError';
  }
}
export async function frameflowRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type'))
    headers.set('Content-Type', 'application/json');
  const response = await fetch(path, { ...init, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new FrameFlowApiError(
      payload?.error?.message ?? '请求失败，请重试',
      payload?.error?.code,
      payload?.error?.retryable,
      response.status,
    );
  return payload as T;
}
