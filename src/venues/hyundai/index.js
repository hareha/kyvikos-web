export { project, views } from './data.js';
export { build } from './scene.js';

// 실내 전시 — 하늘/별 없음, 어두운 배경. 가장 높은 오브젝트 = 지붕선(16.8m)
export const env = {
  height: 19,
  sky: null,
  stars: false,
  builtBg: '#07090d',
  fog: 0.006,
  exposure: 1,
};
