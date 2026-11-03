<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { Alert, Button, Empty, Spin, message } from 'ant-design-vue';
import { useWorksStore } from '#/stores/frameflow/works';
import WorkCard from '#/components/frameflow/WorkCard.vue';
const store = useWorksStore(),
  error = ref(''),
  deleting = ref('');
async function load() {
  try {
    error.value = '';
    await store.load();
  } catch (e) {
    error.value = (e as Error).message;
  }
}
async function remove(id: string) {
  deleting.value = id;
  try {
    await store.remove(id);
    message.success('作品已删除');
  } catch (e) {
    message.error((e as Error).message);
  } finally {
    deleting.value = '';
  }
}
onMounted(load);
</script>
<template>
  <main class="ff-page">
    <h1>我的作品</h1>
    <p class="ff-lead">收藏每一帧灵感。</p>
    <Button @click="load">刷新作品</Button
    ><Alert v-if="error" :message="error" type="error" /><Spin
      :spinning="store.loading"
      ><div class="ff-grid">
        <WorkCard
          v-for="w in store.items"
          :key="w.id"
          :work="w"
          :deleting="deleting === w.id"
          @remove="remove"
        />
      </div>
      <Empty
        v-if="!store.loading && !store.items.length"
        description="还没有作品，去创作第一部视频吧"
    /></Spin>
  </main>
</template>
