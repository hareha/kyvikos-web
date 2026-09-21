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
    b.polyline(plateOutline(0.02));
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
// 건축 모형처럼 황룡원 부지만 잘라낸 판. 윗면은 위성사진(웹 좌표로 정렬, 야간 톤)을 깔아
// 주변 도로·주차장·하천 산책로가 실제대로 보이고, 가장자리는 두께 있는 석재 옆면으로 마감한다.
const PLATE = { x0: -98, x1: 112, z0: -100, z1: 104, r: 26, depth: 3 };
const AERIAL = { x0: -105, x1: 115, z0: -112, z1: 108 };   // apec_site_aerial 이 덮는 범위

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

function sitePlate() {
  const geo = new THREE.ExtrudeGeometry(plateShape(), { depth: PLATE.depth, bevelEnabled: false, curveSegments: 16 });
  geo.rotateX(-PI / 2);
  geo.translate(0, -PLATE.depth - 0.02, 0);
  // 윗면 UV = 위성사진 범위
  const pos = geo.attributes.position;
  const nor = geo.attributes.normal;
  const uv = geo.attributes.uv;
  const w = AERIAL.x1 - AERIAL.x0;
  const d = AERIAL.z1 - AERIAL.z0;
  for (let i = 0; i < pos.count; i++) {
    if (Math.abs(nor.getY(i)) > 0.9) uv.setXY(i, (pos.getX(i) - AERIAL.x0) / w, (pos.getZ(i) - AERIAL.z0) / d);
  }
  const map = new THREE.TextureLoader().load(`${import.meta.env.BASE_URL}assets/graphics/apec_site_aerial.webp`);
  map.colorSpace = THREE.SRGBColorSpace;
  map.anisotropy = 8;
  const top = revealable(new THREE.MeshBasicMaterial({ map }));
  const side = revealable(new THREE.MeshStandardMaterial({ color: '#15181f', roughness: 0.85 }));
  const plate = new THREE.Mesh(geo, [top, side]);
  // 윗 모서리의 가는 금빛 선 (모형 받침 마감)
  const rim = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(plateOutline(0.0)),
    revealable(new THREE.LineBasicMaterial({ color: '#8a7550', transparent: true, opacity: 0.8 })),
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
