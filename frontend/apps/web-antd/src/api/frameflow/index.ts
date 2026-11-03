import type {
  Billing,
  CostEstimate,
  GenerationInput,
  Usage,
  VideoTask,
  Work,
  VideoProviders,
} from './contracts';
import { frameflowRequest as request } from './client';
const post = (body?: unknown): RequestInit => ({
  method: 'POST',
  ...(body ? { body: JSON.stringify(body) } : {}),
});
export const frameflowApi = {
  videoProviders: () => request<VideoProviders>('/api/video-providers'),
  saveVideoProvider: (id: string, apiKey: string) =>
    request(`/api/video-providers/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify({ apiKey }),
    }),
  activateVideoProvider: (id: string) =>
    request(`/api/video-providers/${encodeURIComponent(id)}/activate`, post()),
  testVideoProvider: (id: string) =>
    request<{ ok: boolean; message: string }>(
      `/api/video-providers/${encodeURIComponent(id)}/test`,
      post(),
    ),
  deleteVideoProvider: (id: string) =>
    request(`/api/video-providers/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),
  health: () => request<{ status: string; provider: string }>('/api/health'),
  capabilities: () => request<Record<string, unknown>>('/api/capabilities'),
  enhance: (input: GenerationInput) =>
    request<{ intent: { enhancedPrompt: string } }>(
      '/api/intent/parse',
      post(input),
    ),
  estimate: (input: GenerationInput) =>
    request<CostEstimate>('/api/generations/estimate', post(input)),
  createGeneration: (input: GenerationInput, key = crypto.randomUUID()) =>
    request<{ task: VideoTask; estimate: CostEstimate }>('/api/generations', {
      ...post(input),
      headers: { 'Idempotency-Key': key },
    }),
  getGeneration: (id: string) =>
    request<{ task: VideoTask }>(`/api/generations/${encodeURIComponent(id)}`),
  cancelGeneration: (id: string) =>
    request<{ task: VideoTask }>(
      `/api/generations/${encodeURIComponent(id)}/cancel`,
      post(),
    ),
  usage: () => request<Usage>('/api/account/usage'),
  billing: () => request<Billing>('/api/billing'),
  changePlan: (planId: string) =>
    request<Billing>('/api/billing/plan', post({ planId })),
  works: () => request<{ works: Work[] }>('/api/works'),
  deleteWork: (id: string) =>
    request<{ deleted: boolean }>(`/api/works/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),
};
