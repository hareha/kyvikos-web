import * as THREE from 'three';
import { Builder } from '../../scene/kit.js';
import { loadBakedScene } from '../../scene/baked.js';
import { plateGrid, plateOutline, sitePlate } from '../../scene/plate.js';

/*
 * 동대문디자인플라자(DDP) 전시홀 — 장미셸 바스키아 SEOUL
 *
 * DDP 뮤지엄 전시1관(39.7×35.4m, 층고 8.8m)과 17개 구역의 가벽·작품 약 70점·진열장은 Blender
 * (scripts/blender/basquiat_scene.py)에서 DDP 대관 안내서 평면과 현장 사진(블로그·설치 사진 약 150장)을 기준으로 만든다.
 * 작품 이미지는 현장 사진에서 잘라 원근을 편 것.
 *   좌표: 전시홀 중심 원점. +x 동쪽 B2 로비(입구), +z 남쪽 디자인둘레길(아트샵)
 */

export const PLATE = { x0: -24, x1: 34, z0: -22, z1: 26, r: 6, depth: 1.6 };

export function build() {
  const b = new Builder();
  b.withLayer('context', () => {
    b.polyline(plateOutline(PLATE, 0.02));
    for (const line of plateGrid(PLATE, 5, 0.02)) b.polyline(line);
  });
  const root = b.build();
  root.add(sitePlate(PLATE));
  const lights = addLights(root);
  loadBakedScene(root, 'basquiat', { context: ['hall', 'ceiling', 'floor', 'foyer'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// 동적 물체(조명 트랙)용 약한 실시간 광원
function addLights(root) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    list.push({ light, base });
    return light;
  };
  add(new THREE.HemisphereLight('#c9cfda', '#221e1a', 1), 0.5);
  for (const { light } of list) light.intensity = 0;
  return list;
}
