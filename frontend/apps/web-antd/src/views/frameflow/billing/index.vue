<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { Alert, Button, Card, Popconfirm, Spin, message } from 'ant-design-vue';
import { useFrameFlowAccountStore } from '#/stores/frameflow/account';
const store = useFrameFlowAccountStore(),
  error = ref('');
async function load() {
  try {
    error.value = '';
    await store.loadBilling();
  } catch (e) {
    error.value = (e as Error).message;
  }
}
async function change(id: string) {
  try {
    await store.changePlan(id);
    message.success('套餐已更新');
  } catch (e) {
    message.error((e as Error).message);
  }
}
onMounted(load);
</script>
<template>
  <main class="ff-page">
    <h1>套餐与账单</h1>
    <p class="ff-lead">掌握创作额度，让每一份灵感都有预算。</p>
    <Alert v-if="error" :message="error" type="error" /><Button
      v-if="error"
      @click="load"
      >重试</Button
    ><Spin :spinning="store.loading"
      ><div class="ff-grid">
        <Card
          v-for="plan in store.billing?.plans"
          :key="plan.id"
          :title="plan.name"
          ><div class="ff-metric">{{ plan.monthlyCredits }}</div>
          <p>平台额度 / 月 · 套餐参考价 ¥{{ plan.price }}</p>
          <Popconfirm
            title="确认切换套餐？"
            ok-text="确认"
            cancel-text="取消"
            @confirm="change(plan.id)"
            ><Button
              :disabled="plan.id === store.usage?.plan.id"
              :loading="store.loading"
              >{{
                plan.id === store.usage?.plan.id ? '当前套餐' : '切换套餐'
              }}</Button
            ></Popconfirm
          ></Card
        >
      </div>
      <h2>本月生成账单</h2>
      <table>
        <thead>
          <tr>
            <th>创作</th>
            <th>平台额度</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in store.billing?.records" :key="i">
            <td>
              {{ r.title }}<br />{{ new Date(r.createdAt).toLocaleString() }}
            </td>
            <td>{{ r.credits }}</td>
            <td>{{ r.status }}</td>
          </tr>
          <tr v-if="!store.billing?.records.length">
            <td colspan="3">本月暂无账单</td>
          </tr>
        </tbody>
      </table>
      <h2>套餐变更记录</h2>
      <p v-for="(e, i) in store.billing?.events" :key="i">
        {{ new Date(e.createdAt).toLocaleString() }} · {{ e.description }}
      </p>
      <p v-if="!store.billing?.events.length">暂无变更记录</p>
      <div class="ff-actions">
        <Button
          href="https://console.volcengine.com/ark"
          target="_blank"
          rel="noopener noreferrer"
          >供应商成本核对（独立费用参考）</Button
        >
      </div></Spin
    >
  </main>
</template>
