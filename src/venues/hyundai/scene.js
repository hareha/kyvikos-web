import * as THREE from 'three';
import { Builder } from '../../scene/kit.js';
import { loadBakedScene } from '../../scene/baked.js';
import { plateGrid, plateOutline, sitePlate } from '../../scene/plate.js';

/*
 * 현대 모터스튜디오 서울 — 현대자동차 1억 대 생산 기념 전시 〈다시, 첫걸음〉
 *
 * 건물·전시물은 Blender(scripts/blender/hyundai_scene.py)에서 현장 사진과 소개서 렌더를 기준으로 만들고
 * 조명을 베이크한 장면(hyundai.glb)을 불러온다: 노출 강관 천장·기둥, 유리 커튼월과 파사드 로테이터,
 * 아트리움 컨베이어(차체 크래들), 생산라인 미디어월, 1층 포니 택시·100,000,001대 아치·코티나,
 * 2층 제도실·아카이브, 3층 1억 대 게이트·엘란트라 헤리티지 존.
 * 이 파일은 부지 받침판과 실시간 광원(동적 물체용)만 담당한다.
 *   좌표: 건물 중심 원점, -x 미디어월 유리벽, +z 정면 파사드. 층: 1F 0 · 2F 6 · 3F 11.5 · 지붕 16.8
 */

export const PLATE = { x0: -30, x1: 44, z0: -24, z1: 36, r: 6, depth: 1.6 };

export function build() {
  const b = new Builder();
  b.withLayer('context', () => {
    b.polyline(plateOutline(PLATE, 0.02));
    for (const line of plateGrid(PLATE, 5, 0.02)) b.polyline(line);
  });
  const root = b.build();
  root.add(sitePlate(PLATE));
  const lights = addLights(root);
  loadBakedScene(root, 'hyundai', { context: ['building', 'floors', 'outer'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// 베이크되지 않은 동적 물체(차량·컨베이어·로테이터·유리)용 실시간 광원
function addLights(root) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    if (light.target) root.add(light.target);
    list.push({ light, base });
    return light;
  };
  add(new THREE.HemisphereLight('#dde6f2', '#4a4640', 1), 1.1);
  add(new THREE.DirectionalLight('#f2f5ff', 1), 0.9).position.set(20, 40, 60);
  const spot = (pos, target, base, color = '#fff4e2', angle = 0.55) => {
    const l = new THREE.SpotLight(color, 1, 0, angle, 0.6, 2);
    l.position.set(...pos);
    l.target.position.set(...target);
    add(l, base);
  };
  spot([-5, 16.3, 9.6], [-6, 0, 7.6], 600);
  spot([-12.5, 16.3, 6.5], [-13.5, 0, 4.5], 500);
  spot([-14, 16.3, -1], [-15, 0, -3], 500);
  spot([14, 16.3, 1], [14, 11.5, -6.4], 500, '#f4f7ff', 0.8);
  spot([15.2, 15.3, 6.8], [16.5, 11.5, 8.4], 300, '#fff4e2', 0.9);
  const rail = new THREE.PointLight('#ffffff', 1, 0, 2);
  rail.position.set(-9, 8, 1.5);
  add(rail, 160);
  for (const { light } of list) light.intensity = 0;
  return list;
}
