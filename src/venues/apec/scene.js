import * as THREE from 'three';
import { Builder, G, T, std, revealable, mountainRing, seeded } from '../../scene/kit.js';
import { pbr } from '../../scene/assets.js';
import { loadBakedScene } from '../../scene/baked.js';

/*
 * 경주 황룡원 — APEC CEO Summit 특별만찬
 *
 * 만찬장(잔디·무대·테이블·히터·사인월)과 황룡원 시설(중도타워·일주문·회랑·정원·신평루·연수동)은
 * Blender 에서 현장 사진·공식 조감도를 기준으로 만들고 조명을 베이크한 장면(apec_stage.glb)을 불러온다.
 * 이 파일은 그 바깥의 주변부(광장·산 능선·숲·도시 불빛)와 실시간 광원만 담당한다.
 *   -x: 회랑·정원(길 쪽)   +x: 신평루   -z: 중도타워·무대   +z: 연수동(옥상 귀빈동 테라스)
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
    for (let x = 6; x <= 36; x += 6) roundTree(b, M, x, -34 - (x % 3), 0.9 + (x % 4) * 0.08);
    for (let z = -26; z <= 24; z += 7) roundTree(b, M, 54 + (z % 3), z, 1.1);
  });

  const root = b.build();
  root.add(cityLights());
  const lights = addLights(root);

  // Blender 에서 베이크한 만찬장·중도타워·한옥
  loadBakedScene(root, 'apec_stage', { context: ['ground', 'pagoda', 'halls', 'garden', 'yeonsu', 'pines', 'lanterns'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// ── 대지 / 원경 ───────────────────────────────────────────────
function site(b, M) {
  b.add(G.box(900, 0.2, 900), M.plaza, T(0, -0.1, 0), { outline: false });
  // 잔디 경계석 (잔디 자체는 베이크 장면)
  for (const [x, z, w, d] of [[0, 22.1, 64.4, 0.4], [0, -24.1, 64.4, 0.4], [32.1, -1, 0.4, 46], [-32.1, -1, 0.4, 46]]) {
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
  spot([-16, 25, 22.5], [-6, 0, 0], 5200, '#ffc27a');
  spot([22, 24, 22.5], [6, 0, 0], 3800, '#ffc680');
  spot([6, 8.2, -15], [6, 1.2, -15], 900, '#d8e4ff', 0.9);

  const led = new THREE.RectAreaLight('#4a78ff', 1, 14.4, 6.2);
  led.position.set(6, 4.3, -19.6);
  led.lookAt(6, 4.3, 0);
  add(led, 8);

  for (const { light } of list) light.intensity = 0;
  return list;
}
