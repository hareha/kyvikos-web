import * as THREE from 'three';
import { Builder, G, T, revealable } from '../../scene/kit.js';
import { pbr } from '../../scene/assets.js';
import { loadBakedScene } from '../../scene/baked.js';

/*
 * 경주 황룡원 — APEC CEO Summit 특별만찬
 *
 * 만찬장(잔디·무대·테이블·히터·사인월)과 황룡원 시설(중도타워·일주문·회랑·수공간·신평루·연수동)은
 * Blender 에서 위성사진 실측 배치(scripts/blender/site_survey.md)와 현장 사진으로 만들고
 * 조명을 베이크한 장면(apec_stage.glb)을 불러온다. 이 파일은 바깥 주변부와 실시간 광원만 담당한다.
 *   -x: 동남(중도타워·일주문)  +x: 북서(연수동 북서동)  -z: 남서(무대·신평루)  +z: 북동(회랑·수공간·길)
 */

const PI = Math.PI;

export function build() {
  const M = {
    stone: pbr('rock_tile_floor_02', { color: '#d4d7dc', tile: 1.4, roughness: 0.85 }),
  };

  const b = new Builder();
  b.withLayer('context', () => {
    // 잔디 경계석 (잔디 x -25~35, z -33~17 — 남동쪽은 타워 원형 동선)
    for (const [x, z, w, d] of [[5, 17.2, 60.4, 0.4], [5, -33.2, 60.4, 0.4], [35.2, -8, 0.4, 50]]) {
      b.add(G.box(w, 0.22, d), M.stone, T(x, 0.11, z), { outline: false });
    }
    // 와이어프레임: 받침판 윤곽 + 5m 바둑판 모눈
    b.polyline(plateOutline(0.02));
    for (const line of plateGrid(5, 0.02)) b.polyline(line);
  });

  const root = b.build();
  root.add(sitePlate());
  const lights = addLights(root);

  // Blender 에서 베이크한 만찬장·황룡원 시설·수목
  loadBakedScene(root, 'apec_stage', { context: ['ground', 'pagoda', 'halls', 'garden', 'yeonsu_ne', 'yeonsu_nw', 'pines', 'lanterns'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// ── 부지 받침판 ────────────────────────────────────────────────
// 황룡원 부지만 잘라낸 미니어처 받침판. 실제 구현에서는 무광 단색 판 + 두께 있는 옆면 + 가는 테두리,
// 와이어프레임에서는 판 위 5m 바둑판 모눈.
export const PLATE = { x0: -84, x1: 94, z0: -66, z1: 70, r: 10, depth: 2.4 };

function plateShape() {
  const { x0, x1, z0, z1, r } = PLATE;
  // 셰이프 좌표: (x, -z)
  const s = new THREE.Shape();
  s.moveTo(x0 + r, -z1);
  s.lineTo(x1 - r, -z1);
  s.quadraticCurveTo(x1, -z1, x1, -z1 + r);
  s.lineTo(x1, -z0 - r);
  s.quadraticCurveTo(x1, -z0, x1 - r, -z0);
  s.lineTo(x0 + r, -z0);
  s.quadraticCurveTo(x0, -z0, x0, -z0 - r);
  s.lineTo(x0, -z1 + r);
  s.quadraticCurveTo(x0, -z1, x0 + r, -z1);
  return s;
}

function plateOutline(y) {
  return plateShape()
    .getSpacedPoints(160)
    .map((p) => new THREE.Vector3(p.x, y, -p.y));
}

/** 둥근 모서리 안쪽으로 잘린 모눈 선들 */
function plateGrid(step, y) {
  const { x0, x1, z0, z1, r } = PLATE;
  // 모서리 원호 때문에 줄어드는 길이
  const inset = (d) => (d >= r ? 0 : r - Math.sqrt(Math.max(0, r * r - (r - d) * (r - d))));
  const lines = [];
  for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) {
    const d = Math.min(x - x0, x1 - x);
    lines.push([new THREE.Vector3(x, y, z0 + inset(d)), new THREE.Vector3(x, y, z1 - inset(d))]);
  }
  for (let z = Math.ceil(z0 / step) * step; z <= z1; z += step) {
    const d = Math.min(z - z0, z1 - z);
    lines.push([new THREE.Vector3(x0 + inset(d), y, z), new THREE.Vector3(x1 - inset(d), y, z)]);
  }
  return lines;
}

function sitePlate() {
  const geo = new THREE.ExtrudeGeometry(plateShape(), { depth: PLATE.depth, bevelEnabled: false, curveSegments: 16 });
  geo.rotateX(-PI / 2);
  geo.translate(0, -PLATE.depth - 0.06, 0);   // 윗면 -0.06 (지면에 놓인 것들의 윗면과 6cm 이상)
  // 모형 받침: 윤이 나는 흰 판 (HDRI 반사로 은은한 광택) + 짙은 옆면
  const top = revealable(new THREE.MeshPhysicalMaterial({ color: '#eceae4', roughness: 0.32, metalness: 0, clearcoat: 0.6, clearcoatRoughness: 0.2 }));
  const side = revealable(new THREE.MeshStandardMaterial({ color: '#2a2c31', roughness: 0.45 }));
  const plate = new THREE.Mesh(geo, [top, side]);
  // 윗 모서리 마감선
  const rim = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(plateOutline(0.0)),
    revealable(new THREE.LineBasicMaterial({ color: '#9a8662' })),
  );
  const group = new THREE.Group();
  group.add(plate, rim);
  return group;
}

// ── 실시간 광원 (베이크되지 않은 트러스·의자·유리·주변부용) ─────────
function addLights(root) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    if (light.target) root.add(light.target);
    list.push({ light, base });
    return light;
  };

  add(new THREE.HemisphereLight('#7c8fc4', '#1b160c', 1), 0.55);
  add(new THREE.DirectionalLight('#a9bbff', 1), 0.5).position.set(-80, 120, 60);

  const spot = (pos, target, base, color = '#ffe2b0', angle = 0.55) => {
    const l = new THREE.SpotLight(color, 1, 0, angle, 0.7, 2);
    l.position.set(...pos);
    l.target.position.set(...target);
    add(l, base);
  };
  // Blender 장면과 같은 위치·색의 노란 투광
  spot([40, 19, -4], [4, 0, -2], 5200, '#ffc27a');
  spot([22, 19, 17], [0, 0, 0], 3800, '#ffc680');
  spot([6, 8.2, -15], [6, 1.2, -15], 900, '#d8e4ff', 0.9);

  const led = new THREE.RectAreaLight('#4a78ff', 1, 14.4, 6.2);
  led.position.set(6, 4.3, -19.6);
  led.lookAt(6, 4.3, 0);
  add(led, 8);

  for (const { light } of list) light.intensity = 0;
  return list;
}
