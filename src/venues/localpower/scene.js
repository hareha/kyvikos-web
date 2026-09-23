import * as THREE from 'three';
import { Builder } from '../../scene/kit.js';
import { loadBakedScene } from '../../scene/baked.js';
import { plateGrid, plateOutline, sitePlate } from '../../scene/plate.js';

/*
 * 성수동 세원정밀 창고 — LOCAL POWER 2025 Hong Kong Fashion in Seoul
 *
 * 창고(34 × 12.2m, 처마 3.7m)·입구 마당·성수이로18길은 Blender(scripts/blender/localpower_scene.py)에서
 * 카카오 스카이뷰 측량(site_layout)과 현장 사진 약 145장(hall_layout·yard_layout)을 기준으로 만든다.
 * 창고 외피는 안쪽 면(안을 봄)과 바깥 면(밖을 봄)이 따로 있어 안에서는 내부, 밖에서는 벽돌·푸른 골강판 지붕이 보인다.
 * 전시(9.28~10.11)와 쇼 당일(9.27) 구성이 한 창고에 겹쳐 있어, 시점에 따라 한쪽만 보인다 (onView).
 * 마네킹 의상·전봇대는 CC BY 모델(CREDITS.md).
 *   좌표: 창고 중심 원점. +x 도로(박공), -z 서쪽 입구 마당, -x 뮤직 월·런웨이 LED 쪽
 */

export const PLATE = { x0: -34, x1: 40, z0: -46, z1: 44, r: 6, depth: 1.6 };

export function build() {
  const b = new Builder();
  b.withLayer('context', () => {
    b.polyline(plateOutline(PLATE, 0.02));
    for (const line of plateGrid(PLATE, 5, 0.02)) b.polyline(line);
  });
  const root = b.build();
  root.add(sitePlate(PLATE));
  const lights = addLights(root);
  loadBakedScene(root, 'localpower', { context: ['shell', 'shellOut', 'truss', 'floor', 'outer', 'court', 'nbrs'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// 동적 물체(의상·트러스·차량·잎)용 실시간 광원
function addLights(root) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    if (light.target) root.add(light.target);
    list.push({ light, base });
    return light;
  };
  add(new THREE.HemisphereLight('#e6e8ee', '#3a3430', 1), 1.0);
  // 쇼 당일 오렌지 무빙 조명 (런웨이 위), 전시장 흰 트랙 조명, 바깥 해
  const show = new THREE.PointLight('#ff8a45', 1, 0, 2);
  show.position.set(-6, 3.4, 0);
  add(show, 120);
  const expo = new THREE.PointLight('#fff4e6', 1, 0, 2);
  expo.position.set(4, 3.4, 0);
  add(expo, 90);
  const sun = new THREE.DirectionalLight('#fff4e6', 1);
  sun.position.set(60, 50, -20);
  sun.target.position.set(0, 0, 0);
  add(sun, 1.6);
  for (const { light } of list) light.intensity = 0;
  return list;
}

/** 쇼 당일 시점(phase: 'show')에서는 런웨이·벤치·LED 를, 그 밖에는 전시 가벽·마네킹을 보여 준다 */
export function onView(view, root) {
  const show = view.phase === 'show';
  root.traverse((o) => {
    const n = o.name || '';
    if (n.startsWith('showday')) o.visible = show;
    else if (n === 'expo' || n === 'expo_emit' || n.startsWith('outfit_')) o.visible = !show;
  });
}
