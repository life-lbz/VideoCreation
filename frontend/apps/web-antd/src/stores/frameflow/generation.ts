import { defineStore } from 'pinia';
import { computed, onScopeDispose, ref } from 'vue';
import { frameflowApi } from '#/api/frameflow';
import type {
  CostEstimate,
  GenerationInput,
  VideoTask,
} from '#/api/frameflow/contracts';
import { useFrameFlowAccountStore } from './account';
import { useWorksStore } from './works';
export const useGenerationStore = defineStore('ff-generation', () => {
  const task = ref<VideoTask | null>(null),
    estimate = ref<CostEstimate | null>(null),
    estimateLoading = ref(false),
    submitting = ref(false),
    isPolling = ref(false),
    pollError = ref('');
  let timer: ReturnType<typeof setTimeout> | undefined;
  let epoch = 0;
  let estimateSequence = 0;
  const active = computed(
    () =>
      !!task.value &&
      ['queued', 'generating', 'post_processing'].includes(task.value.status),
  );
  function stopPolling() {
    isPolling.value = false;
    clearTimeout(timer);
    epoch++;
  }
  async function estimateCost(input: GenerationInput) {
    const sequence = ++estimateSequence;
    estimateLoading.value = true;
    try {
      const result = await frameflowApi.estimate(input);
      if (sequence === estimateSequence) estimate.value = result;
    } finally {
      if (sequence === estimateSequence) estimateLoading.value = false;
    }
  }
  function invalidateEstimate() {
    estimateSequence++;
    estimate.value = null;
    estimateLoading.value = false;
  }
  async function enhance(input: GenerationInput) {
    return frameflowApi.enhance(input);
  }
  async function pollOnce() {
    if (!task.value) return;
    const current = epoch;
    const id = task.value.id;
    const result = await frameflowApi.getGeneration(id);
    if (current !== epoch || task.value?.id !== id) return;
    task.value = result.task;
    if (!active.value) {
      stopPolling();
      await Promise.allSettled([
        useFrameFlowAccountStore().loadUsage(),
        useWorksStore().load(),
      ]);
    }
  }
  function startPolling() {
    stopPolling();
    if (!active.value) return;
    isPolling.value = true;
    const current = epoch;
    const tick = async () => {
      let delay = 900;
      try {
        await pollOnce();
        pollError.value = '';
      } catch (e) {
        pollError.value = e instanceof Error ? e.message : '网络中断，正在重试';
        delay = 2200;
      }
      if (isPolling.value && epoch === current) timer = setTimeout(tick, delay);
    };
    timer = setTimeout(tick, 700);
  }
  async function submit(input: GenerationInput) {
    if (submitting.value || active.value) return;
    submitting.value = true;
    try {
      const result = await frameflowApi.createGeneration(input);
      task.value = result.task;
      estimate.value = result.estimate;
      startPolling();
      await Promise.allSettled([useFrameFlowAccountStore().loadUsage()]);
    } finally {
      submitting.value = false;
    }
  }
  async function cancel() {
    if (!task.value) return;
    const id = task.value.id;
    stopPolling();
    try {
      task.value = (await frameflowApi.cancelGeneration(id)).task;
    } catch (error) {
      startPolling();
      throw error;
    }
    await useFrameFlowAccountStore().loadUsage();
  }
  function reset() {
    stopPolling();
    task.value = null;
    pollError.value = '';
  }
  onScopeDispose(stopPolling);
  return {
    task,
    estimate,
    estimateLoading,
    submitting,
    isPolling,
    pollError,
    active,
    estimateCost,
    invalidateEstimate,
    enhance,
    submit,
    pollOnce,
    startPolling,
    stopPolling,
    cancel,
    reset,
  };
});
