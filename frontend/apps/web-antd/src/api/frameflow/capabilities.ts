import type { GenerationInput, VideoProvider } from './contracts';

export function normalizeProviderInput(
  input: GenerationInput,
  c: VideoProvider['capabilities'],
) {
  const changes: string[] = [];
  if (!c.ratios.includes(input.ratio) && c.ratios[0]) {
    input.ratio = c.ratios[0];
    changes.push('比例');
  }
  if (!c.durations.includes(input.duration) && c.durations[0]) {
    input.duration = c.durations[0];
    changes.push('时长');
  }
  if (!c.resolutions.includes(input.resolution) && c.resolutions[0]) {
    input.resolution = c.resolutions[0];
    changes.push('分辨率');
  }
  const audio = c.requiresAudio
    ? true
    : c.supportsAudio
      ? input.generateAudio
      : false;
  if (audio !== input.generateAudio) {
    input.generateAudio = audio;
    changes.push('声音');
  }
  return changes;
}
