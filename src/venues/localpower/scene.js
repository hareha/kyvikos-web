import * as THREE from 'three';
import { Builder } from '../../scene/kit.js';
import { loadBakedScene } from '../../scene/baked.js';
import { plateGrid, plateOutline, sitePlate } from '../../scene/plate.js';

/*
 * 성수동 세원정밀 창고 — LOCAL POWER 2025 홍콩 패션 in 서울
 *
 * 창고·런웨이·전시·중정은 Blender(scripts/blender/localpower_scene.py)에서 현장 사진을 기준으로 만들고
 * 조명을 베이크한 장면(localpower.glb)을 불러온다. 창고 벽·지붕은 안쪽만 보이는 한 겹 면이라
 * 조감에서는 내부가 보인다. 마네킹 의상은 CC BY 의상 모델(CREDITS.md).
 *   좌표: 창고 중심 원점. -x 런웨이 백드롭, +x 전시장·중정, +z 거리(가림막)
 */

export const PLATE = { x0: -40, x1: 54, z0: -18, z1: 26, r: 6, depth: 1.6 };

export function build() {
  const b = new Builder();
  b.withLayer('context', () => {
    b.polyline(plateOutline(PLATE, 0.02));
    for (const line of plateGrid(PLATE, 5, 0.02)) b.polyline(line);
  });
  const root = b.build();
  root.add(sitePlate(PLATE));
  const lights = addLights(root);
  loadBakedScene(root, 'localpower', { context: ['shell', 'floor', 'outer', 'court'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// 동적 물체(의상·트러스)용 실시간 광원
function addLights(root) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    if (light.target) root.add(light.target);
    list.push({ light, base });
    return light;
  };
  add(new THREE.HemisphereLight('#e6e8ee', '#3a3430', 1), 1.0);
  const show = new THREE.PointLight('#ff9a5a', 1, 0, 2);
  show.position.set(-15, 5.5, 0);
  add(show, 260);
  const expo = new THREE.DirectionalLight('#fff6ea', 1);
  expo.position.set(16, 20, 12);
  expo.target.position.set(16, 0, -2);
  add(expo, 1.2);
  for (const { light } of list) light.intensity = 0;
  return list;
}
