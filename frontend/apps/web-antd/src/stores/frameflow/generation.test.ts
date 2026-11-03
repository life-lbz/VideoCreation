import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import type {
  GenerationInput,
  VideoTask,
  CostEstimate,
} from '../../api/frameflow/contracts';
import { frameflowApi } from '../../api/frameflow';
import { useGenerationStore } from './generation';
vi.mock('../../api/frameflow', () => ({
  frameflowApi: {
    estimate: vi.fn(),
    createGeneration: vi.fn(),
    getGeneration: vi.fn(),
    cancelGeneration: vi.fn(),
    usage: vi.fn(),
    works: vi.fn(),
  },
}));
const input: GenerationInput = {
  prompt: '测试画面',
  ratio: '9:16',
  duration: 5,
  quality: 'fast',
  resolution: '720p',
  generateAudio: false,
  quantity: 1,
};
const estimate: CostEstimate = {
  credits: 3,
  currency: 'credits',
  estimatedSeconds: 10,
  priceVersion: 'v1',
};
const queued: VideoTask = {
  id: 'task1',
  status: 'queued',
  progress: 0,
  stage: '排队',
  input,
  createdAt: 1,
  completedAt: null,
  cancelledAt: null,
  resultUrl: null,
  errorCode: null,
  errorMessage: null,
  actionUrl: null,
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
describe('generation lifecycle', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();
    vi.mocked(frameflowApi.works).mockResolvedValue({ works: [] });
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.resetAllMocks();
  });
  it('prevents concurrent and active duplicate submissions', async () => {
    const pending = deferred<{ task: VideoTask; estimate: CostEstimate }>();
    vi.mocked(frameflowApi.createGeneration).mockReturnValue(pending.promise);
    const store = useGenerationStore();
    const first = store.submit(input);
    await store.submit(input);
    expect(frameflowApi.createGeneration).toHaveBeenCalledTimes(1);
    pending.resolve({ task: queued, estimate });
    await first;
    await store.submit(input);
    expect(frameflowApi.createGeneration).toHaveBeenCalledTimes(1);
    store.$dispose();
  });
  it('stops at success and refreshes works', async () => {
    vi.mocked(frameflowApi.createGeneration).mockResolvedValue({
      task: queued,
      estimate,
    });
    vi.mocked(frameflowApi.getGeneration).mockResolvedValue({
      task: { ...queued, status: 'succeeded', progress: 100 },
    });
    const store = useGenerationStore();
    await store.submit(input);
    await store.pollOnce();
    expect(store.task?.status).toBe('succeeded');
    expect(store.isPolling).toBe(false);
    expect(frameflowApi.works).toHaveBeenCalled();
    store.$dispose();
  });
  it('ignores poll responses after reset', async () => {
    const pending = deferred<{ task: VideoTask }>();
    vi.mocked(frameflowApi.createGeneration).mockResolvedValue({
      task: queued,
      estimate,
    });
    vi.mocked(frameflowApi.getGeneration).mockReturnValue(pending.promise);
    const store = useGenerationStore();
    await store.submit(input);
    const polling = store.pollOnce();
    store.reset();
    pending.resolve({ task: { ...queued, status: 'succeeded' } });
    await polling;
    expect(store.task).toBeNull();
    store.$dispose();
  });
  it('keeps newest estimate when older response arrives later', async () => {
    const older = deferred<CostEstimate>();
    vi.mocked(frameflowApi.estimate)
      .mockReturnValueOnce(older.promise)
      .mockResolvedValueOnce({ ...estimate, credits: 7 });
    const store = useGenerationStore();
    const first = store.estimateCost(input);
    await store.estimateCost({ ...input, duration: 10 });
    older.resolve(estimate);
    await first;
    expect(store.estimate?.credits).toBe(7);
    store.$dispose();
  });
  it('cancels and clears polling', async () => {
    vi.mocked(frameflowApi.createGeneration).mockResolvedValue({
      task: queued,
      estimate,
    });
    vi.mocked(frameflowApi.cancelGeneration).mockResolvedValue({
      task: { ...queued, status: 'cancelled' },
    });
    const store = useGenerationStore();
    await store.submit(input);
    await store.cancel();
    expect(store.task?.status).toBe('cancelled');
    expect(store.isPolling).toBe(false);
    store.$dispose();
  });
  it('discards an estimate requested before a provider configuration change', async () => {
    const pending = deferred<CostEstimate>();
    vi.mocked(frameflowApi.estimate).mockReturnValue(pending.promise);
    const store = useGenerationStore();
    const request = store.estimateCost(input);
    store.invalidateEstimate();
    pending.resolve(estimate);
    await request;
    expect(store.estimate).toBeNull();
    expect(store.estimateLoading).toBe(false);
    store.$dispose();
  });
});
