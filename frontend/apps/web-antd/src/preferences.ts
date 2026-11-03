import {
  defineOverridesPreferences,
  definePreferencesExtension,
} from '@vben/preferences';
export const overridesPreferences = defineOverridesPreferences({
  app: {
    name: 'FrameFlow',
    defaultHomePath: '/dashboard',
    accessMode: 'frontend',
  },
  theme: { mode: 'dark', colorPrimary: '#6d74ed' },
  logo: { enable: true, source: '/frameflow-mark.svg', sourceDark: '/frameflow-mark.svg' },
  copyright: { enable: false },
  widget: { notification: false, lockScreen: false },
});
export const preferencesExtension = definePreferencesExtension({
  tabLabel: 'FrameFlow',
  title: 'FrameFlow',
  fields: [
    {
      component: 'select',
      key: 'frameflowTheme',
      label: '品牌主题',
      defaultValue: 'obsidian',
      options: [
        { value: 'obsidian', label: '曜石黑' },
        { value: 'cloud', label: '云境白' },
        { value: 'oriental', label: '东方绛' },
      ],
    },
  ],
});
