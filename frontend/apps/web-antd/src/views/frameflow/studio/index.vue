<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  Alert,
  Button,
  Card,
  Input,
  Select,
  Switch,
  Progress,
  message,
} from 'ant-design-vue';
import type {
  GenerationInput,
  VideoProvider,
  VideoProviders,
} from '#/api/frameflow/contracts';
import { frameflowApi } from '#/api/frameflow';
import { normalizeProviderInput } from '#/api/frameflow/capabilities';
import { useGenerationStore } from '#/stores/frameflow/generation';
import { useFrameFlowAccountStore } from '#/stores/frameflow/account';
const store = useGenerationStore(),
  account = useFrameFlowAccountStore(),
  route = useRoute(),
  busy = ref(false),
  error = ref('');
const input = reactive<GenerationInput>({
  prompt: typeof route.query.prompt === 'string' ? route.query.prompt : '',
  ratio: '9:16',
  duration: 5,
  resolution: '720p',
  quality: 'fast',
  quantity: 1,
  generateAudio: false,
});
const providers = ref<VideoProviders>();
const selected = computed(() =>
  providers.value?.providers.find(
    (p) => p.id === providers.value?.activeProvider,
  ),
);
const caps = computed(() => selected.value?.capabilities);
const ready = computed(() => !!selected.value?.configured && !busy.value);
const parameterNotice = ref('');
function normalize() {
  const c = caps.value;
  if (!c) return;
  const changes = normalizeProviderInput(input, c);
  parameterNotice.value = changes.length
    ? `已按当前平台更新：${changes.join('、')}。`
    : '';
}
async function loadProviders() {
  providers.value = await frameflowApi.videoProviders();
  if (providers.value.activeProvider === 'mock') {
    providers.value.providers.unshift({
      id: 'mock',
      name: '演示模式',
      baseUrl: '',
      configured: true,
      keyHint: '',
      note: '',
      capabilities: {
        ratios: ['9:16', '16:9', '1:1'],
        durations: [5, 8, 10, 15],
        resolutions: ['480p', '720p', '1080p'],
        supportsAudio: true,
        supportsCancel: true,
        maxPromptLength: 1200,
      },
    } satisfies VideoProvider);
  }
  normalize();
}
async function changeProvider(value: unknown) {
  if (typeof value !== 'string') return;
  const id = value;
  if (store.active || store.submitting || busy.value) return;
  clearTimeout(timer);
  store.invalidateEstimate();
  await run(async () => {
    await frameflowApi.activateVideoProvider(id);
    await loadProviders();
  });
  scheduleEstimate();
}
let timer: ReturnType<typeof setTimeout> | undefined;
watch(
  () => input.resolution,
  (value) => {
    input.quality = value === '1080p' ? 'standard' : 'fast';
  },
);
function scheduleEstimate() {
  clearTimeout(timer);
  store.invalidateEstimate();
  timer = setTimeout(async () => {
    if (
      !ready.value ||
      store.active ||
      input.prompt.trim().length < 4 ||
      input.prompt.length > (caps.value?.maxPromptLength ?? 1200)
    )
      return;
    try {
      await store.estimateCost({ ...input });
    } catch (e) {
      error.value = (e as Error).message;
    }
  }, 220);
}
watch(input, scheduleEstimate);
async function run(action: () => Promise<unknown>) {
  error.value = '';
  busy.value = true;
  try {
    await action();
  } catch (e) {
    error.value = (e as Error).message;
    message.error(error.value);
  } finally {
    busy.value = false;
  }
}
async function enhance() {
  await run(async () => {
    const result = await store.enhance({ ...input });
    input.prompt = result.intent.enhancedPrompt;
    message.success('描述已润色');
  });
}
async function submit() {
  if (
    !ready.value ||
    input.prompt.length > (caps.value?.maxPromptLength ?? 1200)
  )
    return;
  await run(() => store.submit({ ...input, prompt: input.prompt.trim() }));
}
onMounted(() => {
  run(async () => {
    await Promise.all([account.loadUsage(), loadProviders()]);
  }).then(scheduleEstimate);
  store.startPolling();
});
onUnmounted(() => {
  clearTimeout(timer);
  store.stopPolling();
});
</script>
<template>
  <main class="ff-page">
    <h1>视频创作</h1>
    <p class="ff-lead">写下画面，交给光影。使用你配置的默认视频平台。</p>
    <Alert v-if="error" :message="error" type="error" show-icon />
    <div class="ff-field">
      <label>视频平台</label
      ><Select
        :value="providers?.activeProvider"
        :disabled="busy || store.active || store.submitting"
        :options="
          providers?.providers.map((p) => ({
            value: p.id,
            label: p.name + (p.configured ? '' : '（未配置）'),
            disabled: !p.configured,
          }))
        "
        style="width: 280px"
        @change="changeProvider"
      /><RouterLink to="/settings/video-providers" style="margin-left: 16px"
        >管理接口配置</RouterLink
      >
    </div>
    <Alert
      v-if="selected?.id === 'mock'"
      message="当前为演示模式，不会调用真实视频生成接口。配置并选择平台后开始真实创作。"
      type="info"
      show-icon
    />
    <Alert
      v-if="selected && !selected.configured"
      message="请先配置当前平台的 API Key，再开始创作。"
      type="warning"
      show-icon
    />
    <Alert
      v-if="parameterNotice"
      :message="parameterNotice"
      type="info"
      show-icon
    />
    <div class="ff-studio">
      <Card
        ><div class="ff-field">
          <label for="prompt">描述你想看见的画面</label
          ><Input.TextArea
            id="prompt"
            v-model:value="input.prompt"
            :maxlength="caps?.maxPromptLength ?? 1200"
            :rows="7"
            show-count
            placeholder="例如：清晨的江南小巷，镜头缓慢前行，晨光穿过薄雾"
          />
          <div class="ff-actions">
            <Button
              :loading="busy"
              :disabled="input.prompt.trim().length < 4 || store.active"
              @click="enhance"
              >智能润色</Button
            ><Button
              @click="
                input.prompt =
                  '一只橘猫坐在窗边，午后阳光洒在毛发上，镜头缓慢推进'
              "
              >试试示例</Button
            >
          </div>
        </div>
        <div class="ff-grid">
          <div class="ff-field">
            <label>画面比例</label
            ><Select
              v-model:value="input.ratio"
              style="width: 100%"
              :options="
                (caps?.ratios ?? []).map((value) => ({
                  value,
                  label: value,
                }))
              "
            />
          </div>
          <div class="ff-field">
            <label>时长</label
            ><Select
              v-model:value="input.duration"
              style="width: 100%"
              :options="
                (caps?.durations ?? []).map((value) => ({
                  value,
                  label: value + ' 秒',
                }))
              "
            />
          </div>
          <div class="ff-field">
            <label>分辨率</label
            ><Select
              v-model:value="input.resolution"
              style="width: 100%"
              :options="
                (caps?.resolutions ?? []).map((value) => ({
                  value,
                  label: value,
                }))
              "
            />
          </div>
          <div class="ff-field">
            <label>生成声音</label
            ><Switch
              v-model:checked="input.generateAudio"
              :disabled="!caps?.supportsAudio || caps?.requiresAudio"
            /><span v-if="caps?.requiresAudio"> 该模型固定生成声音</span
            ><span v-else-if="!caps?.supportsAudio"> 当前平台不支持声音</span>
          </div>
        </div>
        <p>
          {{
            store.estimateLoading
              ? '正在预估…'
              : store.estimate
                ? '预计 ' +
                  store.estimate.credits +
                  ' 额度 · 约 ' +
                  store.estimate.estimatedSeconds +
                  ' 秒'
                : '输入描述后显示费用预估'
          }}
        </p>
        <p>
          可用额度 {{ account.usage?.availableCredits ?? '—' }} ·
          {{ selected?.name ?? '正在读取平台' }}
        </p>
        <div class="ff-actions">
          <Button
            type="primary"
            size="large"
            :loading="store.submitting"
            :disabled="
              busy ||
              !ready ||
              input.prompt.length > (caps?.maxPromptLength ?? 1200) ||
              store.active ||
              input.prompt.trim().length < 4 ||
              (!!store.estimate &&
                !!account.usage &&
                store.estimate.credits > account.usage.availableCredits)
            "
            @click="submit"
            >生成视频</Button
          >
        </div></Card
      ><Card
        ><div class="ff-preview">
          <template v-if="store.task"
            ><video
              v-if="store.task.resultUrl"
              :src="store.task.resultUrl"
              controls
              playsinline
            /><template v-else
              ><h2>{{ store.task.stage }}</h2>
              <Progress :percent="store.task.progress" />
              <p>
                {{ store.task.errorMessage || '你的画面正在抵达。' }}
              </p></template
            ><Alert
              v-if="store.pollError"
              :message="store.pollError + '；正在自动重试'"
              type="warning"
            />
            <div class="ff-actions">
              <Button
                v-if="store.active && caps?.supportsCancel !== false"
                :loading="busy"
                @click="run(() => store.cancel())"
                >取消生成</Button
              ><Button
                v-if="store.task.resultUrl"
                :href="store.task.resultUrl"
                download
                >下载视频</Button
              ><Button
                v-if="!store.active"
                :loading="store.submitting"
                :disabled="
                  !ready ||
                  busy ||
                  store.submitting ||
                  input.prompt.length > (caps?.maxPromptLength ?? 1200)
                "
                @click="submit"
                >再次生成</Button
              ><Button v-if="!store.active" @click="store.reset"
                >新的创作</Button
              ><Button
                v-if="store.task.actionUrl"
                :href="store.task.actionUrl"
                target="_blank"
                >处理建议</Button
              >
            </div></template
          ><template v-else
            ><h2>每个故事，都从一个画面开始。</h2>
            <p class="ff-lead">生成的视频将在这里呈现。</p></template
          >
        </div></Card
      >
    </div>
  </main>
</template>
