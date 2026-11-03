<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import {
  Alert,
  Button,
  Card,
  Input,
  Modal,
  Spin,
  Tag,
  message,
} from 'ant-design-vue';
import { frameflowApi } from '#/api/frameflow';
import type { VideoProvider, VideoProviders } from '#/api/frameflow/contracts';
import { useGenerationStore } from '#/stores/frameflow/generation';
const generation = useGenerationStore();
const data = ref<VideoProviders>();
const loading = ref(false),
  pending = ref(''),
  error = ref('');
const keys = reactive<Record<string, string>>({});
const results = reactive<Record<string, { ok: boolean; message: string }>>({});
async function load() {
  loading.value = true;
  error.value = '';
  try {
    data.value = await frameflowApi.videoProviders();
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
async function action(provider: VideoProvider, kind: string) {
  if (
    pending.value ||
    ((generation.active || generation.submitting) && kind !== 'test')
  )
    return;
  pending.value = `${provider.id}:${kind}`;
  error.value = '';
  try {
    if (kind === 'test')
      results[provider.id] = await frameflowApi.testVideoProvider(provider.id);
    else {
      if (kind === 'save') {
        await frameflowApi.saveVideoProvider(
          provider.id,
          keys[provider.id]?.trim() || '',
        );
        keys[provider.id] = '';
      } else if (kind === 'activate')
        await frameflowApi.activateVideoProvider(provider.id);
      else await frameflowApi.deleteVideoProvider(provider.id);
      delete results[provider.id];
      generation.invalidateEstimate();
      await load();
      message.success(
        kind === 'activate'
          ? '默认平台已更新'
          : kind === 'save'
            ? '密钥已保存'
            : '配置已移除',
      );
    }
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    pending.value = '';
  }
}
function remove(provider: VideoProvider) {
  Modal.confirm({
    title: `移除 ${provider.name} 的密钥？`,
    content:
      '移除后，该平台需要重新配置才能生成视频。环境变量提供的配置可能仍然生效。默认平台请先切换后移除。',
    okText: '移除配置',
    cancelText: '保留',
    okButtonProps: { danger: true },
    onOk: () => action(provider, 'delete'),
  });
}
onMounted(load);
</script>
<template>
  <main class="ff-page">
    <div class="ff-actions" style="justify-content: space-between">
      <div>
        <h1>视频接口配置</h1>
        <p class="ff-lead">连接你的创作引擎，让每个想法找到合适的平台。</p>
      </div>
      <RouterLink to="/studio"><Button>返回视频创作</Button></RouterLink>
    </div>
    <Alert v-if="error" type="error" :message="error" show-icon
      ><template #action
        ><Button size="small" @click="load">重新加载</Button></template
      ></Alert
    >
    <Alert
      v-if="generation.active"
      type="info"
      message="视频生成中，完成后可修改平台配置。连接测试仍可使用。"
      show-icon
    />
    <Spin :spinning="loading">
      <div class="provider-grid">
        <Card
          v-for="provider in data?.providers"
          :key="provider.id"
          :title="provider.name"
        >
          <template #extra
            ><Tag
              :color="
                data?.activeProvider === provider.id ? 'green' : 'default'
              "
              >{{
                data?.activeProvider === provider.id ? '默认平台' : '可选平台'
              }}</Tag
            ></template
          >
          <p class="endpoint">{{ provider.baseUrl }}</p>
          <p>
            <Tag :color="provider.configured ? 'blue' : 'default'">{{
              provider.configured ? '已配置' : '待配置'
            }}</Tag
            ><span>{{ provider.keyHint }}</span>
          </p>
          <p class="provider-note">{{ provider.note }}</p>
          <p>
            {{ provider.capabilities.resolutions.join(' / ') }} ·
            {{ provider.capabilities.durations.join(' / ') }} 秒 ·
            {{ provider.capabilities.supportsAudio ? '支持声音' : '无声音' }}
          </p>
          <label :for="`key-${provider.id}`">API Key</label>
          <Input.Password
            :id="`key-${provider.id}`"
            v-model:value="keys[provider.id]"
            autocomplete="new-password"
            :disabled="generation.active || !!pending"
            :placeholder="
              provider.configured
                ? '留空保留现有密钥，输入新密钥可替换'
                : '输入该平台的 API Key'
            "
          />
          <div class="ff-actions" style="margin-top: 16px">
            <Button
              type="primary"
              :loading="pending === `${provider.id}:save`"
              :disabled="
                generation.active || !!pending || !keys[provider.id]?.trim()
              "
              @click="action(provider, 'save')"
              >保存密钥</Button
            >
            <Button
              :disabled="!!pending || !provider.configured"
              :loading="pending === `${provider.id}:test`"
              @click="action(provider, 'test')"
              >测试连接</Button
            >
            <Button
              :disabled="
                generation.active ||
                !!pending ||
                !provider.configured ||
                data?.activeProvider === provider.id
              "
              @click="action(provider, 'activate')"
              >设为默认</Button
            >
            <Button
              danger
              :disabled="generation.active || !!pending || !provider.configured"
              @click="remove(provider)"
              >移除</Button
            >
          </div>
          <Alert
            v-if="results[provider.id]"
            style="margin-top: 16px"
            :type="results[provider.id]?.ok ? 'success' : 'warning'"
            :message="results[provider.id]?.message"
            show-icon
          />
        </Card>
      </div>
    </Spin>
  </main>
</template>
<style scoped>
.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr));
  gap: 24px;
  margin-top: 24px;
}
.endpoint {
  overflow-wrap: anywhere;
  font-family: monospace;
  opacity: 0.7;
}
.provider-note {
  min-height: 44px;
  opacity: 0.75;
}
label {
  display: block;
  margin-bottom: 8px;
}
</style>
