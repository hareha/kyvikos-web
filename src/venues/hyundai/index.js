export { project, views } from './data.js';
export { build } from './scene.js';

// 낮의 실내 전시 — 유리벽 밖은 흐린 하늘빛. 가장 높은 오브젝트 = 지붕선(16.8m)
export const env = {
  height: 19,
  sky: null,
  stars: false,
  builtBg: '#9aa6b3',
  fog: 0.004,
  exposure: 1,
  hdri: 'art_studio',
  envIntensity: 0.55,
  // Blender(AgX)에서 베이크한 장면
  toneMapping: 'agx',
  bloomThreshold: 2.6,
  bloomStrength: 0.35,
};
