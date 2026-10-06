export { project, views } from './data.js';
export { build } from './scene.js';

// 행사 당일 하늘 — 사진 EXIF 로 날짜·시각을 확인했다.
//   결과물 폴더 233장 중 야간 컷이 **2025-10-30 18:00~20:00 KST** 에 몰려 있다.
// 황룡원(35.846N, 129.278E) 2025-10-30 19:00 KST 의 달 (Meeus 저정밀 해로 계산):
//   고도 35.5° / 방위 178.9° (정남) / 거리 386,118km / 겉보기지름 0.516° / 위상 58% 상현 지나 밤
// 씬 축: +x = 북서(315°), +z = 북동(45°) 이므로
//   x = cos h · 0.7071 · (cosA - sinA) = -0.587
//   z = cos h · 0.7071 · (cosA + sinA) = -0.565
//   y = sin h = 0.581
export const env = {
  height: 90,
  // 달의 밝은 가장자리는 태양 쪽 — 같은 시각 태양은 고도 -18.8° / 방위 266.1° 라
  // 달 방향에 직교하는 성분이 [0.541, -0.238, -0.807] (오른쪽 아래, 서쪽).
  sky: {
    zenith: '#010207', horizon: '#060911',
    moon: [-0.587, 0.581, -0.565], moonLimb: [0.541, -0.238, -0.807], moonPhase: 0.58,
  },
  stars: true,
  fog: 0.0026,
  exposure: 1.15,
  hdri: 'moonless_golf',
  envIntensity: 0.5,
  // Blender(AgX)에서 베이크한 장면
  toneMapping: 'agx',
  bloomThreshold: 2.6,
  bloomStrength: 0.55,
};
