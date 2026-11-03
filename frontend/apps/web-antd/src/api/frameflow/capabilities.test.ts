import { describe, expect, it } from 'vitest';
import { normalizeProviderInput } from './capabilities';
import type { GenerationInput, VideoProvider } from './contracts';
const capabilities: VideoProvider['capabilities'] = {
  ratios: ['16:9'],
  durations: [5],
  resolutions: ['720p'],
  supportsAudio: true,
  requiresAudio: true,
  maxPromptLength: 1000,
};
const input = (): GenerationInput => ({
  prompt: '测试画面',
  ratio: '9:16',
  duration: 10,
  resolution: '1080p',
  quality: 'fast',
  generateAudio: false,
  quantity: 1,
});
describe('provider parameter normalization', () => {
  it('forces mandatory audio and updates unsupported video parameters', () => {
    const value = input();
    expect(normalizeProviderInput(value, capabilities)).toEqual([
      '比例',
      '时长',
      '分辨率',
      '声音',
    ]);
    expect(value).toMatchObject({
      ratio: '16:9',
      duration: 5,
      resolution: '720p',
      generateAudio: true,
    });
  });
  it('turns off audio when switching to a silent provider', () => {
    const value = { ...input(), generateAudio: true };
    normalizeProviderInput(value, {
      ...capabilities,
      requiresAudio: false,
      supportsAudio: false,
    });
    expect(value.generateAudio).toBe(false);
  });
  it('preserves the user choice when audio is optional', () => {
    const value = input();
    normalizeProviderInput(value, { ...capabilities, requiresAudio: false });
    expect(value.generateAudio).toBe(false);
  });
});
