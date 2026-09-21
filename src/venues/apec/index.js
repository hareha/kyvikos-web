export { project, views } from './data.js';
export { build } from './scene.js';

export const env = {
  height: 90,
  sky: { zenith: '#000000', horizon: '#04050a' },   // 현장 사진: 달·별 없는 검은 하늘
  stars: false,
  fog: 0.0026,
  exposure: 1,
  hdri: 'moonless_golf',
  envIntensity: 0.35,
  // Blender(AgX)에서 베이크한 장면
  toneMapping: 'agx',
  bloomThreshold: 2.6,
  bloomStrength: 0.55,
};
