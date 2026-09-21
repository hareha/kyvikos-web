import * as THREE from 'three';
import { Builder, G, T, std, revealable, mountainRing, seeded } from '../../scene/kit.js';
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
    plaza: pbr('asphalt_02', { color: '#6f737a', tile: 5 }),
    stone: pbr('rock_tile_floor_02', { color: '#d4d7dc', tile: 1.4, roughness: 0.85 }),
    mountain: std('#10141c', 1),
    foliage: std('#1d3321', 1),
    trunk: std('#3a2b20', 1),
  };

  const b = new Builder();
  b.withLayer('context', () => {
    site(b, M);
    // 황룡원 둘레 숲 (남서쪽 산책로 너머 · 북서쪽 뒤)
    for (let x = -40; x <= 60; x += 7) roundTree(b, M, x, -60 - (Math.abs(x) % 4), 1 + (Math.abs(x) % 3) * 0.1);
    for (let z = -50; z <= 50; z += 8) roundTree(b, M, 76 + (Math.abs(z) % 3), z, 1.15);
  });

  const root = b.build();
  root.add(cityLights());
  const lights = addLights(root);

  // Blender 에서 베이크한 만찬장·중도타워·한옥
  loadBakedScene(root, 'apec_stage', { context: ['ground', 'pagoda', 'halls', 'garden', 'yeonsu_ne', 'yeonsu_nw', 'pines', 'lanterns'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// ── 대지 / 원경 ───────────────────────────────────────────────
function site(b, M) {
  b.add(G.box(900, 0.2, 900), M.plaza, T(0, -0.1, 0), { outline: false });
  // 잔디 경계석 (잔디 x -25~35, z -33~17 — 남동쪽은 타워 원형 동선)
  for (const [x, z, w, d] of [[5, 17.2, 60.4, 0.4], [5, -33.2, 60.4, 0.4], [35.2, -8, 0.4, 50]]) {
    b.add(G.box(w, 0.22, d), M.stone, T(x, 0.11, z), { outline: false });
  }
  // 경주 분지를 둘러싼 산 능선 (앞산 + 뒷산)
  for (const opts of [
    { radius: 300, depth: 70, height: 34, seed: 11 },
    { radius: 420, depth: 90, height: 70, seed: 29 },
  ]) {
    const { geometry, ridge } = mountainRing(opts);
    b.add(geometry, M.mountain, undefined, { outline: false });
    b.polyline(ridge);
  }
}

/** 멀리 보이는 시내 불빛 (실제 구현 모드) */
function cityLights() {
  const r = seeded(5);
  const n = 2400;
  const pos = new Float32Array(n * 3);
  const col = new Float32Array(n * 3);
  const warm = new THREE.Color('#ffb466');
  const cool = new THREE.Color('#cfe0ff');
  for (let i = 0; i < n; i++) {
    const a = r() * PI * 2;
    const d = 90 + Math.pow(r(), 0.7) * 190;
    pos.set([Math.cos(a) * d, 0.3 + r() * 0.6, Math.sin(a) * d], i * 3);
    const c = r() < 0.75 ? warm : cool;
    const k = 0.5 + r() * 0.8;
    col.set([c.r * k, c.g * k, c.b * k], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const mat = revealable(
    new THREE.PointsMaterial({ size: 1.5, sizeAttenuation: false, vertexColors: true, toneMapped: false, depthWrite: false }),
  );
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  return points;
}

// ── 숲 ─────────────────────────────────────────────────────
function roundTree(b, M, x, z, s = 1) {
  b.group(T(x, 0, z, x, 0, 0, s, s, s), () => {
    b.add(G.cyl(0.25, 0.35, 3, 8), M.trunk, T(0, 1.5, 0), { outline: false });
    b.add(G.ico(1, 1), M.foliage, T(0, 4.6, 0, 0, 0, 0, 2.8, 3.2, 2.8));
  });
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
