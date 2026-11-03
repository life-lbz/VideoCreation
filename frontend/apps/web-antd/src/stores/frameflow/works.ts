import { defineStore } from 'pinia';
import { ref } from 'vue';
import { frameflowApi } from '#/api/frameflow';
import type { Work } from '#/api/frameflow/contracts';
export const useWorksStore = defineStore('ff-works', () => {
  const items = ref<Work[]>([]),
    loading = ref(false);
  async function load() {
    loading.value = true;
    try {
      items.value = (await frameflowApi.works()).works;
    } finally {
      loading.value = false;
    }
  }
  async function remove(id: string) {
    await frameflowApi.deleteWork(id);
    items.value = items.value.filter((w) => w.id !== id);
  }
  return { items, loading, load, remove };
});
