<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { Button, Card, Progress, Alert, Spin, message } from 'ant-design-vue';
import { useRouter } from 'vue-router';
import { frameflowApi } from '#/api/frameflow';
import { useFrameFlowAccountStore } from '#/stores/frameflow/account';
import { useWorksStore } from '#/stores/frameflow/works';
import WorkCard from '#/components/frameflow/WorkCard.vue';
const account = useFrameFlowAccountStore(),
  works = useWorksStore(),
  router = useRouter(),
  error = ref(''),
  loading = ref(false),
  health = ref(''),
  deleting = ref('');
async function remove(id: string) {
  deleting.value = id;
  try {
    await works.remove(id);
    message.success('作品已删除');
  } catch (e) {
    message.error((e as Error).message);
  } finally {
    deleting.value = '';
  }
}
async function load() {
  error.value = '';
  loading.value = true;
  try {
    const result = await Promise.all([
      account.loadUsage(),
      works.load(),
      frameflowApi.health(),
    ]);
    health.value = result[2].status === 'ok' ? '服务运行正常' : '服务异常';
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <main class="ff-page">
    <h1>让灵感，成为下一帧。</h1>
    <p class="ff-lead">FrameFlow 创作工作台</p>
    <Alert v-if="error" type="error" :message="error" /><Button
      v-if="error"
      @click="load"
      >重试</Button
    ><Spin :spinning="loading"
      ><div class="ff-grid">
        <Card title="可用额度"
          ><div class="ff-metric">
            {{ account.usage?.availableCredits ?? '—' }}
          </div>
          <p>平台创作额度</p></Card
        ><Card title="本月创作额度"
          ><div class="ff-metric">
            {{ account.usage?.usedCredits ?? 0 }} /
            {{ account.usage?.monthlyLimit ?? '—' }}
          </div>
          <Progress
            :percent="
              account.usage
                ? Math.round(
                    (account.usage.usedCredits / account.usage.monthlyLimit) *
                      100,
                  )
                : 0
            " /></Card
        ><Card title="当前套餐"
          ><div class="ff-metric">{{ account.usage?.plan.name ?? '—' }}</div>
          <p>{{ health }}</p></Card
        >
      </div>
      <div class="ff-actions">
        <Button type="primary" size="large" @click="router.push('/studio')"
          >开始创作</Button
        >
      </div>
      <h2>最近创作</h2>
      <div class="ff-grid">
        <WorkCard
          v-for="w in works.items.slice(0, 6)"
          :key="w.id"
          :work="w"
          :deleting="deleting === w.id"
          @remove="remove"
        /><Card v-if="!works.items.length"
          >你的第一部作品，从一个想法开始。</Card
        >
      </div></Spin
    >
  </main>
</template>
