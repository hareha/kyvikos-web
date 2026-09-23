export { project, views } from './data.js';
export { build, onView } from './scene.js';

// 실내 창고 — 쇼장은 오렌지 조명, 전시장은 밝은 흰 조명
export const env = {
  height: 12,
  sky: null,
  stars: false,
  builtBg: '#07080c',
  fog: 0.004,
  exposure: 1.05,
  hdri: 'art_studio',
  envIntensity: 0.45,
  // Blender(AgX)에서 베이크한 장면
  toneMapping: 'agx',
  bloomThreshold: 2.6,
  bloomStrength: 0.4,
};
