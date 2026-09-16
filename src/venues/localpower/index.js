export { project, views } from './data.js';
export { build } from './scene.js';

// 실내 창고 — 하늘 없음, 어두운 배경
export const env = {
  height: 12,
  sky: null,
  stars: false,
  builtBg: '#07080c',
  fog: 0.006,
  exposure: 1.1,
  fill: 1.5,
  hdri: 'art_studio',
  envIntensity: 0.55,
};
