<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { BasicLayout } from '@vben/layouts';
import {
  getCustomPreferences,
  updateCustomPreferences,
  updatePreferences,
  usePreferences,
} from '@vben/preferences';
import { Button } from 'ant-design-vue';
import { useRouter } from 'vue-router';
import { useFrameFlowAccountStore } from '#/stores/frameflow/account';
const account = useFrameFlowAccountStore();
const router = useRouter();
const usageFailed = ref(false);
const theme = ref('obsidian');
const { isDark } = usePreferences();
// The built-in toggle and brand buttons share the resolved Vben mode.
watch(isDark, (dark) => {
  const next = dark ? (theme.value === 'cloud' ? 'obsidian' : theme.value) : 'cloud';
  if (next !== theme.value) apply(next);
}, { flush: 'post' });
function apply(value: string) {
  theme.value = value;
  document.documentElement.dataset.frameflowTheme = value;
  updatePreferences({
    theme: {
      mode: value === 'cloud' ? 'light' : 'dark',
      colorPrimary: value === 'oriental' ? '#b84045' : '#6d74ed',
    },
  });
  updateCustomPreferences({ frameflowTheme: value });
}
onMounted(() => {
  updatePreferences({ logo: { enable: true, source: '/frameflow-mark.svg', sourceDark: '/frameflow-mark.svg' } });
  account.loadUsage().catch(() => { usageFailed.value = true; });
  apply(
    getCustomPreferences<{ frameflowTheme: string }>().frameflowTheme ||
      'obsidian',
  );
});
</script>
<template>
  <BasicLayout
    ><template #user-dropdown
      ><div class="ff-header-account"><button class="ff-header-credit" type="button" @click="router.push('/billing')" aria-label="查看可用额度与套餐账单"><span>可用额度</span><strong>{{ account.usage?.availableCredits ?? '—' }}</strong><small>{{ usageFailed ? '查看账单' : account.usage?.plan.name }}</small></button><div class="ff-theme">
        <Button
          v-for="t in [
            { id: 'obsidian', name: '曜石黑' },
            { id: 'cloud', name: '云境白' },
            { id: 'oriental', name: '东方绛' },
          ]"
          :key="t.id"
          size="small"
          :type="theme === t.id ? 'primary' : 'text'"
          @click="apply(t.id)"
          >{{ t.name }}</Button
        >
      </div></div></template
    ></BasicLayout
  >
</template>
<style scoped>
.ff-header-account { display: flex; align-items: center; gap: 16px; min-width: 0; }
.ff-header-credit { display: flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 8px; color: hsl(var(--foreground)); background: hsl(var(--muted)); cursor: pointer; white-space: nowrap; }
.ff-header-credit span, .ff-header-credit small { font-size: 12px; }
.ff-header-credit small { opacity: .7; }
.ff-header-credit strong { font-size: 16px; font-variant-numeric: tabular-nums; }
.ff-header-credit:hover { background: hsl(var(--accent)); }
.ff-header-credit:focus-visible { outline: 2px solid var(--ff-accent); outline-offset: 2px; }
.ff-theme { display: flex; align-items: center; gap: 4px; }
@media (max-width: 760px) { .ff-header-account { gap: 8px; } .ff-header-credit { padding: 4px 8px; } .ff-header-credit span, .ff-header-credit small { display: none; } }
@media (max-width: 480px) { .ff-header-credit { display: none; } }
</style>
