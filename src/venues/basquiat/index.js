export { project, views } from './data.js';
export { build } from './scene.js';

// 어두운 실내 전시 — 작품만 스포트로 밝음
export const env = {
  height: 9,
  sky: null,
  stars: false,
  builtBg: '#0b0c10',
  fog: 0.004,
  exposure: 1.1,
  hdri: 'art_studio',
  envIntensity: 0.4,
  // Blender(AgX)에서 베이크한 장면
  toneMapping: 'agx',
  bloomThreshold: 2.6,
  bloomStrength: 0.35,
};
