import { defineStore } from 'pinia';
import { ref } from 'vue';
import { frameflowApi } from '#/api/frameflow';
import type { Usage, Billing } from '#/api/frameflow/contracts';
export const useFrameFlowAccountStore = defineStore('ff-account', () => {
  const usage = ref<Usage | null>(null),
    billing = ref<Billing | null>(null),
    loading = ref(false);
  async function loadUsage() {
    usage.value = await frameflowApi.usage();
  }
  async function loadBilling() {
    loading.value = true;
    try {
      billing.value = await frameflowApi.billing();
      usage.value = billing.value;
    } finally {
      loading.value = false;
    }
  }
  async function changePlan(id: string) {
    loading.value = true;
    try {
      billing.value = await frameflowApi.changePlan(id);
      usage.value = billing.value;
    } finally {
      loading.value = false;
    }
  }
  return { usage, billing, loading, loadUsage, loadBilling, changePlan };
});
