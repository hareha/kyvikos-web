import * as THREE from 'three';
import { Builder } from '../../scene/kit.js';
import { loadBakedScene } from '../../scene/baked.js';
import { plateGrid, plateOutline, sitePlate } from '../../scene/plate.js';

/*
 * 현대 모터스튜디오 서울 — 현대자동차 1억 대 생산 기념 전시 〈다시, 첫걸음〉
 *
 * 건물·전시물은 Blender(scripts/blender/hyundai_scene.py)에서 서아키텍스 층별 평면·단면(축척 0.035m/px,
 * 건축물대장·정사영상으로 교차 확인)과 블로그·공식 사진 약 170장을 기준으로 만든다:
 * 45° 모따기 유리 커튼월·점 프릿 띠, 강관 루버 천장·기둥, 1~2층 보이드의 대형 스크린과 컨베이어(노란 걸이 1:4 차체),
 * 1F 코티나·포니 택시·1억대 아치 / 2F 파울바셋 카페·어두운 전시실 / 3F 쏘나타 Y1·스쿠프·엘란트라·설계실
 * / 4F 싼타페·코나·캐스퍼 / 5F 아이오닉 5·5 N라인·6, 층마다 로테이터 3대(거리 쪽 차 그림 패널).
 *   좌표: 기준층 윤곽 중심 원점, 1F 바닥 0. -z 도산대로, -x 언주로. 층: 1F 0 · 2F 3.75 · 3F 7.65 · 4F 12.63 · 5F 17.61
 */

export const PLATE = { x0: -34, x1: 30, z0: -40, z1: 30, r: 6, depth: 1.6 };

export function build() {
  const b = new Builder();
  b.withLayer('context', () => {
    b.polyline(plateOutline(PLATE, 0.02));
    for (const line of plateGrid(PLATE, 5, 0.02)) b.polyline(line);
  });
  const root = b.build();
  root.add(sitePlate(PLATE));
  const lights = addLights(root);
  loadBakedScene(root, 'hyundai', { context: ['building', 'site', 'ceilings'] }).catch((error) =>
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
  // 1F 두 차 (보이드 천장), 3~5F 조명 박스 아래 차량 (exhibition_layout.json 좌표)
  spot([-4.3, 7.0, -6.2], [-4.3, 0, -6.2], 420);
  spot([-4.3, 7.0, -2.9], [-4.3, 0, -2.9], 420);
  for (const [x, z, y] of [[-6.3, 6.2, 7.65], [-2.6, -0.9, 7.65], [7.2, -6.4, 7.65],
    [-1.9, -2.2, 12.63], [6.2, -6.7, 12.63], [-7.1, 5.5, 12.63],
    [-1.9, -2.2, 17.61], [6.2, -6.7, 17.61], [-7.1, 5.5, 17.61]]) {
    spot([x, y + 3.5, z], [x, y, z], 260, '#f4f7ff', 0.9);
  }
  const rail = new THREE.PointLight('#ffffff', 1, 0, 2);
  rail.position.set(-4.5, 6.2, -4.5);
  add(rail, 160);
  for (const { light } of list) light.intensity = 0;
  return list;
}
