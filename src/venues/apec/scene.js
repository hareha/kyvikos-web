import * as THREE from 'three';
import { Builder, G, T, truss, beam, std, glow, revealable, mountainRing, seeded } from '../../scene/kit.js';
import { pbr, placeModel, hideProxy } from '../../scene/assets.js';
import { ledTexture, bannerTexture, windowTexture, totemTexture } from './textures.js';

/*
 * 경주 황룡원 — APEC CEO Summit 특별만찬
 * 소개서 사진·렌더를 참고해 단순화한 공간 모델. 단위는 m, 잔디광장 중심이 원점.
 *   +x: 오른쪽(무대 쪽)   -z: 뒤쪽(중도타워·무대)   +z: 앞쪽(귀빈동 테라스·콘솔 부스)
 */

const PI = Math.PI;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function build() {
  const tex = { led: ledTexture(), banner: bannerTexture(), windows: windowTexture(), totem: totemTexture() };
  const M = {
    // 실사 재질 (Poly Haven CC0). tile = 텍스처 한 장이 덮는 크기(m)
    plaza: pbr('asphalt_02', { color: '#6f737a', tile: 5 }),
    lawn: pbr('leafy_grass', { color: '#b9d68c', tile: 2.5 }),
    stone: pbr('rock_tile_floor_02', { color: '#d4d7dc', tile: 1.4, roughness: 0.85 }),
    stoneDark: pbr('rock_tile_floor_02', { color: '#8e939a', tile: 1.4, roughness: 0.85 }),
    mountain: std('#10141c', 1),
    deck: pbr('cotton_jersey', { color: '#2a3566', tile: 0.8 }),
    metal: std('#b4bac3', 0.5, 0.55),
    dark: std('#16181d', 0.6, 0.3),
    white: std('#eef0f3', 0.5),
    cloth: pbr('cotton_jersey', { color: '#ffffff', tile: 0.6, roughness: 1 }),
    chair: std('#121215', 0.45, 0.4), // 의자 모델이 로드되기 전 임시 형태
    gold: std('#b8914c', 0.35, 0.9),
    flower: std('#e3e6ef', 0.9),
    tent: std('#e8ebf0', 0.7, 0, { transparent: true, opacity: 0.88, side: THREE.DoubleSide }),
    glass: std('#2a3342', 0.15, 0.6, { transparent: true, opacity: 0.55 }),
    navy: std('#131a3a', 0.5, 0.2),
    wood: pbr('dark_wooden_planks', { color: '#9a6a48', tile: 1.5, roughness: 0.8 }),
    woodRed: pbr('dark_wooden_planks', { color: '#c0503a', tile: 1.5, roughness: 0.8 }),
    tile: pbr('ceramic_roof_01', { color: '#6a7078', tile: 1.6, roughness: 0.7, side: THREE.DoubleSide }),
    plaster: pbr('beige_wall_001', { color: '#f4f1ea', tile: 3 }),
    foliage: std('#1d3321', 1),
    pine: std('#1a2c1c', 1),
    trunk: std('#3a2b20', 1),
    core: std('#1a120b', 0.8, 0, { emissive: '#ffffff', emissiveMap: tex.windows, emissiveIntensity: 1.5 }),
    window: std('#20160e', 0.8, 0, { emissive: '#ffb468', emissiveIntensity: 0.7 }),
    led: glow('#ffffff', 1.1, { map: tex.led }),
    banner: glow('#ffffff', 1.0, { map: tex.banner }),
    totemScreen: glow('#ffffff', 1.0, { map: tex.totem }),
    warm: glow('#ffb45e', 3),
    lamp: glow('#ffffff', 4),
    lens: glow('#9fd2ff', 4),
    stripBlue: glow('#2f6bff', 3),
    screen: glow('#5aa0ff', 1.5),
    beam: revealable(
      new THREE.MeshBasicMaterial({
        color: '#6aa8ff',
        transparent: true,
        opacity: 0.06,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide,
      }),
    ),
    chairSpots: [],
  };

  const b = new Builder();

  b.withLayer('context', () => {
    site(b, M);
    pagoda(b, M, -30, -38);
    hall(b, M, { x: -22, z: 37, w: 34, d: 10, h: 6.5, roofH: 3.8 }); // 귀빈동 (테라스)
    hall(b, M, { x: -41, z: 2, w: 36, d: 8, h: 5, ry: PI / 2 }); // 좌측 회랑
    eastWing(b, M);
    for (let x = 2; x <= 34; x += 5.5) roundTree(b, M, x, -30 - (x % 3), 0.9 + (x % 4) * 0.08);
    for (let z = -20; z <= 16; z += 6) roundTree(b, M, -52, z + (z % 4), 1.1);
    pine(b, M, 14, 18, 1.1);
    pine(b, M, 19.5, 20.5, 0.9);
    pine(b, M, -30, 22, 0.8);
    b.add(G.ico(1, 0), M.stoneDark, T(17, 0.5, 23.5, 0.4, 0, 0, 2.6, 0.9, 1.8));
    for (const [x, z] of [[-12, -15], [26, -15], [-27, 18], [30, 20]]) lantern(b, M, x, z);
  });

  stage(b, M);
  banquet(b, M);
  totem(b, M, -16, -20, 0.35);
  totem(b, M, 20, -9, -0.95);
  foh(b, M);

  const root = b.build();
  root.add(cityLights());
  const lights = addLights(root);

  // 연회 의자: 상자 형태로 먼저 보여주고, 실제 모델이 로드되면 교체
  placeModel(root, 'dining_chair_02', M.chairSpots, {
    color: '#9a9a9a',
    roughness: 0.55,
    onReady: () => {
      hideProxy(root, M.chair);
      hideProxy(root, M.gold);
    },
  });
  return { root, lights };
}

// ── 대지 / 원경 ───────────────────────────────────────────────
function site(b, M) {
  b.add(G.box(900, 0.2, 900), M.plaza, T(0, -0.1, 0), { outline: false });
  b.add(G.box(64, 0.12, 46), M.lawn, T(0, 0.06, -1));
  for (const [x, z, w, d] of [[0, 22.1, 64.4, 0.4], [0, -24.1, 64.4, 0.4], [32.1, -1, 0.4, 46], [-32.1, -1, 0.4, 46]]) {
    b.add(G.box(w, 0.22, d), M.stone, T(x, 0.11, z), { outline: false });
  }

  // 무대 앞을 가로지르는 디딤돌
  for (let x = -31; x <= 31; x += 1.3) {
    if (Math.abs(x - 6) < 3.4) continue;
    b.add(G.box(1.1, 0.06, 0.55), M.stone, T(x, 0.14, -8.35));
    b.add(G.box(1.1, 0.06, 0.55), M.stone, T(x + 0.65, 0.14, -7.65));
  }
  // 원형 메달리온
  b.add(G.cyl(3, 3, 0.08, 48), M.stone, T(6, 0.15, -8));
  b.add(G.cyl(1.1, 1.1, 0.1, 32), M.stoneDark, T(6, 0.17, -8));
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * PI * 2;
    b.add(G.box(0.25, 0.1, 1.1), M.stoneDark, T(6 + Math.sin(a) * 2.1, 0.17, -8 + Math.cos(a) * 2.1, a));
  }
  // 앞쪽 동선
  for (let z = -4.5; z <= 22; z += 1.1) b.add(G.box(1.8, 0.06, 0.8), M.stone, T(6, 0.14, z));

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
    // 원경 쪽으로 몰리게
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

// ── 중도타워 (9층 목탑) ────────────────────────────────────────
function pagoda(b, M, cx, cz) {
  b.group(T(cx, 0, cz), () => {
    b.add(G.box(28, 2.2, 28), M.stone, T(0, 1.1, 0));
    for (const [x, z, w, d] of [[0, 13.8, 28, 0.2], [0, -13.8, 28, 0.2], [13.8, 0, 0.2, 28], [-13.8, 0, 0.2, 28]]) {
      b.add(G.box(w, 0.9, d), M.stone, T(x, 2.65, z));
    }

    let y = 2.2;
    for (let i = 0; i < 9; i++) {
      const w = 17 - i * 1.15;
      const h = i === 0 ? 6.5 : 4.2;
      const half = w / 2;
      b.add(G.box(w - 1.6, h, w - 1.6), M.core, T(0, y + h / 2, 0));
      b.add(G.box(w + 0.6, 0.35, w + 0.6), M.wood, T(0, y + 0.17, 0));
      for (let k = 0; k <= 4; k++) {
        const t = -half + (k * w) / 4;
        for (const [px, pz] of [[t, half], [t, -half], [half, t], [-half, t]]) {
          b.add(G.box(0.35, h, 0.35), M.wood, T(px, y + h / 2, pz), { outline: false });
        }
      }
      for (const [x, z, bw, bd] of [[0, half, w, 0.1], [0, -half, w, 0.1], [half, 0, 0.1, w], [-half, 0, 0.1, w]]) {
        b.add(G.box(bw, 0.12, bd), M.wood, T(x, y + 1.1, z), { outline: false });
      }

      // 처마: 오목한 기와지붕 + 들린 추녀, 추녀 끝마다 조명
      const rh = 1.7;
      const hb = half + 2.4;
      const ht = half - 0.6;
      const lift = 0.9;
      const eave = y + h - 0.3;
      b.add(G.roof(hb, hb, rh, { ridge: 1 - ht / hb, lift }), M.tile, T(0, eave, 0));
      for (const [lx, lz] of [[hb, hb], [-hb, hb], [hb, -hb], [-hb, -hb]]) {
        b.add(G.sphere(0.28, 8), M.lamp, T(lx, eave + lift - 0.1, lz), { outline: false });
      }
      y += h + rh - 0.3;
    }
    b.add(G.cyl(0.2, 0.9, 9, 8), M.metal, T(0, y + 4.5, 0));
    for (let i = 0; i < 5; i++) b.add(G.cyl(0.9 - i * 0.1, 0.9 - i * 0.1, 0.18, 12), M.metal, T(0, y + 2 + i * 1.2, 0));
  });
}

// ── 한옥 지붕 / 건물 ───────────────────────────────────────────
function roof(b, M, x, y, z, hw, hd, h) {
  const ridge = 0.85;
  b.add(G.roof(hw, hd, h, { ridge, lift: h * 0.35 }), M.tile, T(x, y, z));
  const ridgeLen = Math.max(hw - hd * ridge, hd * (1 - ridge)) * 2 + 0.6;
  b.add(G.box(1, 1, 1), M.tile, T(x, y + h + 0.12, z, 0, 0, 0, ridgeLen, 0.32, 0.4));
}

function hall(b, M, { x, z, w, d, h, ry = 0, y = 0, roofH = 3 }) {
  b.group(T(x, y, z, ry), () => {
    b.add(G.box(w, h, d), M.plaster, T(0, h / 2, 0));
    // 창호: 기둥 간격마다 따뜻한 불빛
    for (let px = -w / 2 + 2; px <= w / 2 - 1.5; px += 3) {
      b.add(G.box(1.8, h * 0.42, d + 0.06), M.window, T(px, h * 0.45, 0), { outline: false });
      b.add(G.box(0.3, h, d + 0.12), M.wood, T(px - 1.5, h / 2, 0), { outline: false });
    }
    b.add(G.box(w + 0.4, 0.5, d + 0.4), M.woodRed, T(0, h - 0.25, 0), { outline: false });
    roof(b, M, 0, h - 0.1, 0, w / 2 + 1.8, d / 2 + 1.8, roofH);
  });
}

function eastWing(b, M) {
  b.group(T(41, 0, -3), () => {
    b.add(G.box(10, 9, 44), M.plaster, T(0, 4.5, 0));
    for (let z = -19; z <= 19; z += 6.3) b.add(G.box(0.1, 3.6, 2.6), M.window, T(-5.02, 2.2, z));
    for (let z = -19; z <= 19; z += 3.15) b.add(G.box(0.1, 1.0, 1.4), M.window, T(-5.02, 6.6, z), { outline: false });
    for (const z of [-14, 0, 14]) {
      b.add(G.box(6, 2.4, 5), M.woodRed, T(0, 10.2, z));
      roof(b, M, 0, 11.3, z, 4.8, 4, 2.2);
    }
  });
}

function pavilion(b, M, x, z, w, d) {
  b.group(T(x, 0, z), () => {
    b.add(G.box(w + 1, 0.6, d + 1), M.stone, T(0, 0.3, 0));
    for (const px of [-w / 2, w / 2]) for (const pz of [-d / 2, d / 2]) b.add(G.cyl(0.25, 0.25, 3.4, 12), M.wood, T(px, 2.3, pz));
    b.add(G.box(w + 0.6, 0.5, d + 0.6), M.woodRed, T(0, 4.25, 0));
    roof(b, M, 0, 4.4, 0, w / 2 + 2, d / 2 + 2, 2.6);
  });
}

// ── 조경 ─────────────────────────────────────────────────────
function pine(b, M, x, z, s = 1) {
  b.group(T(x, 0.12, z, x, 0, 0, s, s, s), () => {
    b.add(G.cyl(0.18, 0.3, 3, 8), M.trunk, T(0, 1.5, 0, 0, 0, 0.15), { outline: false });
    for (const [px, py, pz, r] of [[0, 3.2, 0, 1.7], [1.4, 2.6, 0.6, 1.3], [-1.2, 2.9, -0.5, 1.2], [0.3, 4.0, -0.4, 1.1]]) {
      b.add(G.ico(1, 1), M.pine, T(px, py, pz, 0, 0, 0, r * 1.5, r * 0.55, r * 1.5));
    }
  });
}

function roundTree(b, M, x, z, s = 1) {
  b.group(T(x, 0, z, x, 0, 0, s, s, s), () => {
    b.add(G.cyl(0.25, 0.35, 3, 8), M.trunk, T(0, 1.5, 0), { outline: false });
    b.add(G.ico(1, 1), M.foliage, T(0, 4.6, 0, 0, 0, 0, 2.8, 3.2, 2.8));
  });
}

function lantern(b, M, x, z) {
  b.group(T(x, 0.12, z), () => {
    b.add(G.box(0.8, 0.3, 0.8), M.stone, T(0, 0.15, 0));
    b.add(G.cyl(0.18, 0.18, 1, 8), M.stone, T(0, 0.8, 0));
    b.add(G.box(0.7, 0.6, 0.7), M.window, T(0, 1.6, 0));
    b.add(G.roof(0.6, 0.6, 0.4, { ridge: 0.9, lift: 0.12 }), M.stone, T(0, 1.88, 0));
  });
}

// ── 무대 ─────────────────────────────────────────────────────
function stage(b, M) {
  const cx = 6;
  const cz = -16;
  const top = 1.2;

  b.add(G.box(18, top, 9), M.deck, T(cx, top / 2, cz));
  b.add(G.plane(18, 0.9), M.banner, T(cx, 0.55, cz + 4.52), { outline: false });
  b.add(G.box(18, 0.06, 0.06), M.stripBlue, T(cx, top + 0.02, cz + 4.5), { outline: false });
  b.add(G.box(6, 0.8, 0.6), M.deck, T(cx, 0.4, cz + 4.8));
  b.add(G.box(6, 0.4, 0.6), M.deck, T(cx, 0.2, cz + 5.4));

  // LED월
  b.add(G.box(14.6, 6.1, 0.4), M.dark, T(cx, top + 3.35, cz - 3.9));
  b.add(G.plane(14, 5.5), M.led, T(cx, top + 3.35, cz - 3.68), { outline: false });

  // 포디움, 스피커
  b.add(G.box(0.75, 1.15, 0.5), M.white, T(cx, top + 0.575, cz + 1.4));
  for (const sx of [-4.4, 16.4]) b.add(G.box(1.1, 2.8, 1), M.dark, T(sx, 1.4, cz + 4));

  // 트러스 구조 + 박공 지붕
  const x0 = -5;
  const x1 = 17;
  const zb = -21.8;
  const zf = -10.2;
  const hTop = 10;
  const hRidge = 13.5;
  const zr = -16;
  const s = 0.42;

  for (const x of [x0, x1]) {
    for (const z of [zb, zf]) {
      b.add(G.box(1.2, 0.12, 1.2), M.dark, T(x, 0.06, z));
      truss(b, V(x, 0.12, z), V(x, hTop, z), s, M.metal);
    }
  }
  truss(b, V(x0, hTop, zf), V(x1, hTop, zf), s, M.metal);
  truss(b, V(x0, hTop, zb), V(x1, hTop, zb), s, M.metal);
  truss(b, V(x0, hTop, zb), V(x0, hTop, zf), s, M.metal);
  truss(b, V(x1, hTop, zb), V(x1, hTop, zf), s, M.metal);
  truss(b, V(x0, hRidge, zr), V(x1, hRidge, zr), s, M.metal);
  for (const x of [x0, cx, x1]) {
    truss(b, V(x, hTop, zb), V(x, hRidge, zr), s * 0.8, M.metal);
    truss(b, V(x, hTop, zf), V(x, hRidge, zr), s * 0.8, M.metal);
  }

  const theta = Math.atan2(hRidge - hTop, zr - zb);
  const slope = Math.hypot(hRidge - hTop, zr - zb) + 0.4;
  const skin = G.box(x1 - x0 + 0.8, 0.04, slope);
  b.add(skin, M.tent, T(cx, (hTop + hRidge) / 2 + 0.3, (zb + zr) / 2, 0, -theta));
  b.add(skin, M.tent, T(cx, (hTop + hRidge) / 2 + 0.3, (zf + zr) / 2, 0, theta));

  // 조명기구
  for (let x = -3; x <= 15; x += 2) {
    for (const z of [zf, zb]) {
      b.add(G.box(0.36, 0.42, 0.36), M.dark, T(x, hTop - 0.5, z), { outline: false });
      b.add(G.cyl(0.13, 0.13, 0.04, 12), M.lens, T(x, hTop - 0.72, z), { outline: false });
    }
  }
  for (const x of [-1, 3, 9, 13]) beam(b, V(x, hTop - 0.75, zf), V(x + (cx - x) * 0.3, top, cz + 1), M.beam);
}

// ── 만찬 테이블 ────────────────────────────────────────────────
const HEATERS = [
  [-20.5, -5.5], [-6.5, -5.5], [10, -5.5], [24, -5.5], [-27, 5], [-13.5, 5], [-0.5, 5.2], [17, 5.5],
  [-20.5, 10.8], [-6.5, 10.8], [10.5, 11], [-27, 16.5], [-13.5, 16.5], [0, 16.5], [24, 11], [28, -1],
];

function banquet(b, M) {
  [-3, 2.5, 8, 13.5, 19].forEach((z, row) => {
    for (const x of [-24, -17, -10, -3]) table(b, M, x + (row % 2 ? 3 : 0), z);
  });
  for (const z of [-3, 2.5, 8]) for (const x of [13.5, 20.5]) table(b, M, x, z);
  for (const [x, z] of HEATERS) heater(b, M, x, z);
}

function table(b, M, x, z) {
  b.group(T(x, 0.12, z), () => {
    b.add(G.cyl(0.95, 1.08, 0.76, 32), M.cloth, T(0, 0.38, 0));
    b.add(G.cyl(0.08, 0.11, 0.22, 10), M.glass, T(0, 0.87, 0), { outline: false });
    b.add(G.ico(0.26, 1), M.flower, T(0, 1.08, 0), { outline: false });
    for (let i = 0; i < 3; i++) {
      const a = i * 2.1 + 0.4;
      b.add(G.cyl(0.03, 0.03, 0.09, 6), M.warm, T(Math.sin(a) * 0.5, 0.81, Math.cos(a) * 0.5), { outline: false });
    }
    for (let i = 0; i < 10; i++) {
      const a = (i / 10) * PI * 2 + 0.16;
      b.group(T(Math.sin(a) * 1.38, 0, Math.cos(a) * 1.38, a), () => {
        b.add(G.box(0.46, 0.46, 0.46), M.chair, T(0, 0.23, 0));
        b.add(G.box(0.46, 0.64, 0.07), M.chair, T(0, 0.78, 0.2));
        b.add(G.box(0.48, 0.05, 0.09), M.gold, T(0, 1.1, 0.2), { outline: false });
        // 모델은 +z를 정면으로 보므로 테이블 쪽(-z)을 보게 뒤집는다
        M.chairSpots.push(b.current.clone().multiply(T(0, 0, 0, PI)));
      });
    }
  });
}

function heater(b, M, x, z) {
  b.group(T(x, 0.12, z, PI / 4), () => {
    b.add(G.cyl(0.32, 0.38, 0.1, 4), M.dark, T(0, 0.05, 0));
    b.add(G.cyl(0.24, 0.36, 2.1, 4, true), M.glass, T(0, 1.15, 0));
    b.add(G.cyl(0.06, 0.06, 1.7, 8), M.warm, T(0, 1.15, 0), { outline: false });
    b.add(G.cyl(0.18, 0.56, 0.3, 4), M.metal, T(0, 2.35, 0));
  });
}

function totem(b, M, x, z, ry) {
  b.group(T(x, 0.12, z, ry), () => {
    b.add(G.box(1.8, 5.2, 0.9), M.navy, T(0, 2.6, 0));
    b.add(G.plane(1.5, 4.4), M.totemScreen, T(0, 2.8, 0.46), { outline: false });
    b.add(G.box(1.9, 0.35, 1), M.dark, T(0, 5.35, 0));
    b.add(G.box(1.6, 0.18, 0.3), M.lamp, T(0, 5.6, 0.2), { outline: false });
  });
}

// ── 콘솔 부스 (FOH) ────────────────────────────────────────────
function foh(b, M) {
  b.withLayer('context', () => pavilion(b, M, 6, 28.5, 10, 6));
  b.group(T(6, 0.6, 26.8), () => {
    b.add(G.box(3.4, 0.9, 0.9), M.dark, T(0, 0.45, 0));
    for (const x of [-0.9, 0.9]) b.add(G.box(0.9, 0.55, 0.04), M.screen, T(x, 1.2, -0.15, 0, -0.25), { outline: false });
    b.add(G.box(1.2, 0.9, 0.7), M.dark, T(-2.8, 0.45, 0.2));
  });
}

// ── 조명 (실제 구현 모드에서만 켜짐) ─────────────────────────────
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
  spot([-14, 24, 34], [-8, 0, 4], 4200);
  spot([26, 22, 26], [4, 0, 0], 3200);
  spot([6, 9.4, -9.5], [6, 1.2, -15.5], 900, '#a8c6ff', 0.7);

  const pagodaGlow = new THREE.PointLight('#ffae62', 1, 0, 2);
  pagodaGlow.position.set(-30, 4, -20);
  add(pagodaGlow, 900);

  const led = new THREE.RectAreaLight('#4a78ff', 1, 14, 5.5);
  led.position.set(6, 4.55, -19.6);
  led.lookAt(6, 4.55, 0);
  add(led, 8);

  for (const { light } of list) light.intensity = 0;
  return list;
}
