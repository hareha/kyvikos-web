import * as THREE from 'three';
import { Builder, G, T, member, std, glow } from '../../scene/kit.js';
import {
  muralTexture,
  gateHeaderTexture,
  cityTexture,
  neonTexture,
  archTexture,
  partitionTexture,
  archiveTexture,
  blueprintTexture,
  signTexture,
} from './textures.js';

/*
 * 현대 모터스튜디오 도산 — 현대자동차 1억대 생산기념 전시
 * 소개서 렌더·현장 사진을 참고해 단순화한 실내 모델. 단위 m, 건물 중심이 원점.
 *   -x: 미디어월이 걸린 유리벽   +z: 정면 파사드(입구)   아트리움은 -x 쪽 3개 층 오픈
 * 조감 카메라(+x, +z, 위)를 향한 벽·지붕은 선만 그려 내부가 보이게(컷어웨이).
 */

const PI = Math.PI;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const NO = { outline: false };

const F2 = 6;
const F3 = 11.5;
const ROOF = 16.8;
const X0 = -20;
const X1 = 20;
const Z0 = -14;
const Z1 = 14;

// 사다리꼴 캐빈 (밑변 1×1, 윗면 0.62배, 높이 1, 밑면 y=-0.5)
let cabin;
const cabinGeo = () => (cabin ??= new THREE.CylinderGeometry(0.62 * Math.SQRT1_2, Math.SQRT1_2, 1, 4, 1).rotateY(PI / 4));
let arc;
// 곡면 파티션: 원점이 곡면 중앙에 오도록 이동
const arcGeo = () => (arc ??= new THREE.CylinderGeometry(3, 3, 3.8, 14, 1, true, -0.5, 1.0).translate(0, 0, -3));

export function build() {
  const tex = {
    mural: muralTexture(),
    header: gateHeaderTexture(),
    city: cityTexture(),
    neon: neonTexture(),
    archive: archiveTexture(),
    screen: archiveTexture(true),
    blueprint: blueprintTexture(),
    sign: signTexture(),
    p92: partitionTexture('1992, Ulsan Plant'),
    p90: partitionTexture('1990, Ulsan Plant'),
  };
  const M = {
    ground: std('#121418', 0.95),
    floor: std('#6c6f74', 0.35, 0.05),
    floorUp: std('#6f7277', 0.4, 0.05),
    slabEdge: std('#2a2d33', 0.7, 0.2),
    concrete: std('#34373c', 0.9),
    wallDark: std('#141518', 0.6, 0.2),
    wallWhite: std('#d9d8d3', 0.85),
    column: std('#5b5f66', 0.45, 0.7),
    steel: std('#c9ced6', 0.3, 0.85),
    mullion: std('#23262c', 0.5, 0.6),
    glassFar: std('#3a5068', 0.1, 0.5, { transparent: true, opacity: 0.35, depthWrite: false }),
    glassNear: glow('#4a6a8a', 0.5, { transparent: true, opacity: 0.05, depthWrite: false }),
    rail: std('#dfe3e8', 0.25, 0.9),
    cradle: std('#f2c21a', 0.45, 0.2),
    tire: std('#111214', 0.8),
    carGlass: std('#1a2230', 0.4, 0.3),
    chrome: std('#d9dde2', 0.2, 1),
    teal: std('#3fb7b4', 0.35, 0.2),
    taxi: std('#f0b21c', 0.35, 0.2),
    yellow: std('#e9c21f', 0.35, 0.2),
    silver: std('#8d8b86', 0.35, 0.5),
    blue: std('#3c6ea6', 0.3, 0.4),
    maroon: std('#5a1a2a', 0.6, 0.15),
    bodies: ['#d62a2f', '#2140c0', '#f2c318', '#1aa39a', '#e6e6e6', '#e0662a', '#2a2f3d'].map((c) => std(c, 0.35, 0.25)),
    mural: glow('#ffffff', 0.95, { map: tex.mural }),
    header: glow('#ffffff', 1, { map: tex.header }),
    city: glow('#ffffff', 0.9, { map: tex.city }),
    neon: glow('#ffffff', 1, { map: tex.neon }),
    archive: std('#ffffff', 0.85, 0, { map: tex.archive }),
    screen: std('#ffffff', 0.7, 0, { map: tex.screen, transparent: true, opacity: 0.85, side: THREE.DoubleSide }),
    blueprint: std('#ffffff', 0.9, 0, { map: tex.blueprint }),
    sign: std('#ffffff', 0.8, 0, { map: tex.sign }),
    p92: std('#ffffff', 0.9, 0, { map: tex.p92, side: THREE.DoubleSide }),
    p90: std('#ffffff', 0.9, 0, { map: tex.p90, side: THREE.DoubleSide }),
    mat: std('#55585c', 0.95),
    pallet: std('#a07a4a', 0.9),
    carton: std('#c9a878', 0.9),
    desk: std('#b9b4a8', 0.7),
    rope: std('#8a1c24', 0.7),
    strip: glow('#fff6e6', 0.8),
    stripCool: glow('#e8f2ff', 0.7),
    head: glow('#fff4d6', 0.95),
    tail: glow('#ff2a2a', 0.9),
    lightbox: glow('#fffaf0', 0.45),
  };

  const b = new Builder();

  b.withLayer('context', () => {
    building(b, M);
    stairs(b, M);
  });

  mural(b, M);
  conveyor(b, M);
  groundFloor(b, M, tex);
  drafting(b, M);
  gate(b, M);
  heritage(b, M);
  lighting(b, M);

  const root = b.build();
  const lights = addLights(root);
  return { root, lights };
}

// ── 건물 ─────────────────────────────────────────────────────
function building(b, M) {
  b.add(G.box(140, 0.2, 110), M.ground, T(0, -0.25, 0), NO);
  b.add(G.box(40, 0.3, 28), M.floor, T(0, -0.15, 0));

  // 슬래브: 아트리움(x < 4 / 8) 부분을 비우고 뒤쪽 띠만 이어짐
  const slab = (x0, x1, z0, z1, y, mat) => b.add(G.box(x1 - x0, 0.5, z1 - z0), mat, T((x0 + x1) / 2, y - 0.25, (z0 + z1) / 2));
  slab(4, X1, Z0, Z1, F2, M.floorUp);
  slab(X0, 4, Z0, -8, F2, M.floorUp);
  slab(1.4, 4, -1, 1, F2, M.floorUp); // 계단 참
  slab(8, X1, Z0, Z1, F3, M.floorUp);
  slab(X0, 8, Z0, -10, F3, M.floorUp);

  // 지붕: 선만 (컷어웨이)
  b.add(G.box(40, 0.6, 28), null, T(0, ROOF, 0));

  // 기둥 (세로 슬랫 마감)
  for (const [x, z] of [[-12, -8], [0, -8], [8, -8], [8, 3], [8, 13], [16, -8], [16, 3], [-2, 13]]) {
    b.add(G.cyl(0.55, 0.55, ROOF, 20), M.column, T(x, ROOF / 2, z));
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * PI * 2;
      b.line(V(x + Math.cos(a) * 0.56, 0, z + Math.sin(a) * 0.56), V(x + Math.cos(a) * 0.56, ROOF, z + Math.sin(a) * 0.56));
    }
  }

  // 뒷벽 (콘크리트)
  b.add(G.box(40, ROOF, 0.4), M.concrete, T(0, ROOF / 2, Z0 - 0.2));

  // -x 유리벽 (미디어월 뒤)
  b.add(G.box(0.08, ROOF, 28), M.glassFar, T(X0, ROOF / 2, 0));
  for (let z = Z0; z <= Z1 + 0.01; z += 2.8) b.add(G.box(0.2, ROOF, 0.14), M.mullion, T(X0, ROOF / 2, z));
  for (const y of [F2, F3]) b.add(G.box(0.4, 0.6, 28), M.slabEdge, T(X0, y - 0.3, 0));

  // 조감 카메라 쪽 파사드 (+z, +x): 거의 투명한 유리 + 멀리언 선
  b.add(G.box(40, ROOF, 0.05), M.glassNear, T(0, ROOF / 2, Z1), NO);
  b.add(G.box(0.05, ROOF, 28), M.glassNear, T(X1, ROOF / 2, 0), NO);
  for (const y of [0, F2, F3, ROOF]) {
    b.line(V(X0, y, Z1), V(X1, y, Z1));
    b.line(V(X1, y, Z0), V(X1, y, Z1));
  }
  for (let x = X0; x <= X1 + 0.01; x += 2.8) {
    if (x > 6 && x < 12) continue; // 입구
    b.line(V(x, 0, Z1), V(x, ROOF, Z1));
  }
  b.line(V(6, 3.2, Z1), V(12, 3.2, Z1));
  for (let z = Z0; z <= Z1 + 0.01; z += 2.8) b.line(V(X1, 0, z), V(X1, ROOF, z));

  // 난간: 2F / 3F 아트리움 가장자리
  railing(b, M, V(4, F2, -8), V(4, F2, -1));
  railing(b, M, V(4, F2, 1), V(4, F2, Z1 - 0.3));
  railing(b, M, V(X0 + 0.3, F2, -8), V(1.4, F2, -8));
  railing(b, M, V(1.4, F2, -8), V(1.4, F2, -1));
  railing(b, M, V(8, F3, -10), V(8, F3, Z1 - 0.3));
  railing(b, M, V(X0 + 0.3, F3, -10), V(8, F3, -10));
}

function railing(b, M, a, c, h = 1.1) {
  const d = c.clone().sub(a);
  const len = d.length();
  b.group(T(a.x, a.y, a.z, Math.atan2(-d.z, d.x)), () => {
    for (const y of [h, h * 0.68, h * 0.36]) b.add(G.box(len, 0.045, 0.045), M.steel, T(len / 2, y, 0), NO);
    for (let x = 0; x <= len + 0.01; x += 1.4) b.add(G.box(0.05, h, 0.05), M.steel, T(x, h / 2, 0), NO);
    b.line(V(0, h, 0), V(len, h, 0));
    b.line(V(0, h * 0.5, 0), V(len, h * 0.5, 0));
  });
}

function stairs(b, M) {
  // x 1.4~3.4, z 13(1F) → z 1(2F)
  const x = 2.4;
  const run = 12;
  const n = 20;
  const slope = Math.atan2(F2, run);
  const len = Math.hypot(F2, run);
  for (let i = 0; i < n; i++) {
    const y = ((i + 1) * F2) / n;
    const z = 13 - ((i + 0.5) * run) / n;
    b.add(G.box(2, 0.06, 0.62), M.steel, T(x, y - 0.03, z), NO);
  }
  for (const sx of [-1.05, 1.05]) {
    b.add(G.box(0.08, 0.38, len), M.column, T(x + sx, F2 / 2 - 0.1, 7, 0, slope));
    const a = V(x + sx, 1.05, 13);
    const c = V(x + sx, F2 + 1.05, 1);
    b.add(G.box(0.05, 0.05, len), M.steel, T(x + sx, F2 / 2 + 1.05, 7, 0, slope), NO);
    b.add(G.box(0.05, 0.05, len), M.steel, T(x + sx, F2 / 2 + 0.55, 7, 0, slope), NO);
    b.line(a, c);
    b.line(V(a.x, 0.55, 13), V(a.x, F2 + 0.55, 1));
    for (let t = 0; t <= 1.001; t += 0.1) {
      b.add(G.box(0.045, 1.05, 0.045), M.steel, T(x + sx, t * F2 + 0.525, 13 - t * run), NO);
    }
  }
}

// ── 미디어월 (-x 유리벽 상부, 2개 층 높이) ─────────────────────
function mural(b, M) {
  const y = 9.6;
  b.add(G.box(0.3, 6.4, 22.4), M.wallDark, T(X0 + 0.45, y, 1));
  b.add(G.plane(22, 6), M.mural, T(X0 + 0.62, y, 1, PI / 2), NO);
  for (const z of [-8, 1, 10]) member(b, V(X0 + 0.45, y + 3.2, z), V(X0 + 0.45, ROOF, z), 0.06, M.steel);
}

// ── 천장 컨베이어 레일 + 차체 크래들 ──────────────────────────
function conveyor(b, M) {
  const Y = 14.2;
  const cx = -9;
  const cz = 1.5;
  const R = 4.6;
  const L = 5;
  const pts = [];
  for (let i = 0; i <= 11; i++) {
    const a = (i / 11) * PI;
    pts.push(V(cx + R * Math.cos(a), Y + 0.5 * Math.sin(a * 2), cz + L + R * Math.sin(a)));
  }
  for (let i = 0; i <= 11; i++) {
    const a = PI + (i / 11) * PI;
    pts.push(V(cx + R * Math.cos(a), Y - 0.5 * Math.sin(a * 2), cz - L + R * Math.sin(a)));
  }
  const loop = new THREE.CatmullRomCurve3(pts, true, 'centripetal');

  // 레일에서 갈라져 나선형으로 내려오는 가지
  const drop = new THREE.CatmullRomCurve3(
    [V(-4.4, Y, -1), V(-2.6, Y - 0.8, -4.2), V(-0.8, Y - 2.2, -2.4), V(-1.6, Y - 3.6, 0.8), V(-4.2, Y - 4.8, 0.2), V(-4.6, Y - 6, -3), V(-2.4, Y - 7, -4.4)],
    false,
    'centripetal',
  );

  for (const [curve, seg, closed] of [[loop, 180, true], [drop, 90, false]]) {
    b.add(new THREE.TubeGeometry(curve, seg, 0.11, 6, closed), M.rail, undefined, NO);
    b.polyline(curve.getPoints(seg / 2));
  }

  // 행거
  for (let i = 0; i < 10; i++) {
    const p = loop.getPointAt(i / 10);
    member(b, p, V(p.x, ROOF - 0.3, p.z), 0.04, M.steel);
  }
  for (const u of [0.35, 0.65, 1]) {
    const p = drop.getPointAt(u);
    member(b, p, V(p.x, ROOF - 0.3, p.z), 0.03, M.steel);
  }

  let k = 0;
  const place = (curve, n, s, u0 = 0, u1 = 1) => {
    for (let i = 0; i < n; i++) {
      const u = u0 + ((u1 - u0) * (i + 0.5)) / n;
      const p = curve.getPointAt(u);
      const t = curve.getTangentAt(u);
      cradle(b, M, p, Math.atan2(-t.z, t.x), s, M.bodies[k++ % M.bodies.length]);
    }
  };
  place(loop, 14, 0.62);
  place(drop, 7, 0.4, 0.12, 1);
}

function cradle(b, M, p, ry, s, paint) {
  const w = 4.9 * s;
  const d = 2.3 * s;
  const h = 2.1 * s;
  const t = 0.07;
  b.group(T(p.x, p.y - 0.25 - h, p.z, ry), () => {
    // 노란 프레임
    for (const y of [0, h]) {
      for (const z of [-d / 2, d / 2]) b.add(G.box(w, t, t), M.cradle, T(0, y, z), NO);
      for (const x of [-w / 2, w / 2]) b.add(G.box(t, t, d), M.cradle, T(x, y, 0), NO);
    }
    for (const x of [-w / 2, w / 2]) for (const z of [-d / 2, d / 2]) b.add(G.box(t, h, t), M.cradle, T(x, h / 2, z), NO);
    b.add(G.box(w, h, d), null, T(0, h / 2, 0));
    b.add(G.box(0.1, 0.25, 0.1), M.steel, T(0, h + 0.12, 0), NO);
    // 차체 (바퀴 없음)
    car(b, M, paint, 0, 0.05 - 0.28 * s, 0, 0, s, { wheels: false, lamps: false });
  });
}

// ── 차량 ─────────────────────────────────────────────────────
function car(b, M, paint, x, y, z, ry, s = 1, { wheels = true, lamps = true, outline = true } = {}) {
  b.group(T(x, y, z, ry, 0, 0, s, s, s), () => {
    const o = { outline };
    b.add(G.box(4.2, 0.62, 1.7), paint, T(0, 0.62, 0), o);
    b.add(cabinGeo(), paint, T(-0.25, 1.22, 0, 0, 0, 0, 2.3, 0.58, 1.5), o);
    b.add(cabinGeo(), M.carGlass, T(-0.25, 1.17, 0, 0, 0, 0, 2.36, 0.44, 1.56), NO);
    b.add(G.box(0.08, 0.14, 1.72), M.chrome, T(2.1, 0.42, 0), NO);
    b.add(G.box(0.08, 0.14, 1.72), M.chrome, T(-2.1, 0.42, 0), NO);
    if (wheels) {
      for (const wx of [-1.35, 1.35]) for (const wz of [-0.78, 0.78]) b.add(G.cyl(0.33, 0.33, 0.24, 14), M.tire, T(wx, 0.33, wz, 0, PI / 2), NO);
    }
    if (lamps) {
      for (const wz of [-0.6, 0.6]) {
        b.add(G.box(0.05, 0.14, 0.28), M.head, T(2.12, 0.7, wz), NO);
        b.add(G.box(0.05, 0.12, 0.3), M.tail, T(-2.12, 0.7, wz), NO);
      }
    }
  });
}

function stanchions(b, M, pts) {
  for (const p of pts) {
    b.add(G.cyl(0.18, 0.18, 0.03, 12), M.chrome, T(p.x, 0.015, p.z), NO);
    b.add(G.cyl(0.025, 0.025, 0.9, 6), M.chrome, T(p.x, 0.45, p.z), NO);
  }
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i];
    const c = pts[(i + 1) % pts.length];
    member(b, V(a.x, 0.82, a.z), V(c.x, 0.72, c.z), 0.025, M.rope);
  }
}

// ── 1층: 클래식카 + 1억대 아치 ───────────────────────────────
function groundFloor(b, M) {
  // Pony 택시 + 아치
  car(b, M, M.taxi, -6, 0, 7.6, -PI / 2);
  b.add(G.box(0.7, 0.25, 0.35), M.lightbox, T(-6, 1.62, 7.4), NO);
  arch(b, M, -6, 8.4);
  stanchions(b, M, [V(-8, 0, 4.6), V(-4, 0, 4.6), V(-4, 0, 10.8), V(-8, 0, 10.8)].map((p) => p));

  // 청록 클래식카, 노란 세단
  car(b, M, M.teal, -13.5, 0, 4.5, -PI / 2 + 0.35);
  car(b, M, M.yellow, -15, 0, -3, -PI / 2 + 0.15);
  stanchions(b, M, [V(-16.5, 0, 1.4), V(-11, 0, 1.4), V(-11, 0, 7.8), V(-16.5, 0, 7.8)]);
}

function arch(b, M, x, z) {
  const R = 2.4;
  const L = 2.4;
  const r = 1.65;
  const shape = new THREE.Shape();
  shape.moveTo(-R, 0);
  shape.lineTo(-R, L);
  shape.absarc(0, L, R, PI, 0, true);
  shape.lineTo(R, 0);
  shape.lineTo(r, 0);
  shape.lineTo(r, L);
  shape.absarc(0, L, r, 0, PI, false);
  shape.lineTo(-r, 0);
  shape.closePath();
  const geo = new THREE.ExtrudeGeometry(shape, { depth: 0.45, bevelEnabled: false, curveSegments: 20 });
  const tex = archTexture(R, L, r);
  tex.repeat.set(1 / (2 * R), 1 / (L + R));
  tex.offset.set(0.5, 0);
  b.add(geo, std('#ffffff', 0.7, 0, { map: tex }), T(x, 0, z - 0.225));
  b.add(G.box(2 * R + 0.3, 0.12, 0.7), M.wallWhite, T(x, 0.06, z), NO);
}

// ── 2층: 1980년대 제도실 ─────────────────────────────────────
function drafting(b, M) {
  const y = F2;
  b.group(T(0, y, 0), () => {
    b.add(G.box(0.4, 5, 5), M.wallDark, T(10.2, 2.5, -11.3)); // 검은 입구벽
    b.add(G.box(9.4, 5, 0.2), M.wallWhite, T(15.1, 2.5, -13.5));
    b.add(G.plane(6, 2.3), M.blueprint, T(15.3, 1.9, -13.38), NO);
    for (const [dx, dz, rot] of [[12.6, -9.5, 0], [15.8, -10.2, 0.1], [18, -7.4, -0.2]]) {
      b.group(T(dx, 0, dz, rot), () => {
        b.add(G.box(2.2, 0.06, 1.1), M.desk, T(0, 0.78, 0));
        for (const lx of [-1, 1]) for (const lz of [-0.48, 0.48]) b.add(G.box(0.05, 0.78, 0.05), M.wallDark, T(lx, 0.39, lz), NO);
        b.add(G.box(1.6, 0.04, 1.1), M.wallWhite, T(0.2, 1.25, -0.2, 0, -0.9), { outline: true });
      });
    }
    // 안내 사인
    b.add(G.box(1.6, 2.3, 0.08), M.wallWhite, T(9.6, 1.55, -5.2, -0.3));
    b.add(G.plane(1.5, 2.1), M.sign, T(9.62, 1.55, -5.15, -0.3), NO);
  });
}

// ── 3층: 1억대 게이트 ────────────────────────────────────────
function gate(b, M) {
  const cx = 14;
  const z = -4.6;
  b.group(T(0, F3, 0), () => {
    b.add(G.box(11.6, 0.03, 8.4), M.floor, T(cx, 0.015, -6.4), NO);
    for (const px of [8.9, 19.1]) b.add(G.box(0.8, 4.6, 0.8), M.wallDark, T(px, 2.3, z));
    b.add(G.box(11, 0.7, 0.8), M.wallDark, T(cx, 4.3, z));
    b.add(G.plane(10.6, 0.6), M.header, T(cx, 4.3, z + 0.41), NO);
    b.add(G.box(10.2, 0.06, 0.3), M.stripCool, T(cx, 3.9, z + 0.2), NO);

    // 좌우 영상 패널 (V자로 안쪽을 향함)
    for (const [ax, az, ry, mat] of [[9.3, z - 0.4, PI / 4, M.city], [15.2, z - 3.9, -PI / 4, M.neon]]) {
      b.group(T(ax, 0, az, ry), () => {
        b.add(G.box(4.95, 3.6, 0.1), M.wallDark, T(2.475, 1.9, -0.06));
        b.add(G.plane(4.95, 3.6), mat, T(2.475, 1.9, 0.01), NO);
      });
    }

    // 중앙 팔레트 적재 박스
    for (const px of [13.3, 14.7]) {
      b.add(G.box(1.2, 0.15, 1.0), M.pallet, T(px, 0.08, z - 3.9));
      for (let i = 0; i < 3; i++) b.add(G.box(1.1, 0.6, 0.9), M.carton, T(px, 0.45 + i * 0.6, z - 3.9));
    }

    // 전시 차량 (정면 향함)
    for (const [px, mat] of [[11.2, M.silver], [16.8, M.blue]]) {
      b.add(G.box(2.4, 0.05, 4.8), M.wallDark, T(px, 0.03, z - 1.8, 0), NO);
      car(b, M, mat, px, 0.05, z - 1.8, -PI / 2, 0.9);
    }
  });
}

// ── 3층: 헤리티지 존 (엘란트라 + 곡면 파티션 + 아카이브) ─────────
function heritage(b, M) {
  b.group(T(0, F3, 0), () => {
    b.add(G.box(3, 0.03, 5.4), M.mat, T(16.5, 0.015, 8.4, 0.25), NO);
    car(b, M, M.maroon, 16.5, 0.03, 8.4, -PI / 2 + 0.25, 1);

    b.add(arcGeo(), M.p92, T(10.4, 1.9, 9.2, 1.2));
    b.add(arcGeo(), M.p90, T(19.2, 1.9, 5.4, -0.8));

    // 반투명 사진 스크린 (창가)
    b.add(G.box(8, 2.6, 0.04), M.screen, T(13.6, 1.7, 12.9));
    for (const px of [9.6, 17.6]) b.add(G.box(0.05, 3, 0.05), M.steel, T(px, 1.5, 12.9), NO);

    // 뒤쪽 아카이브 월 + 진열대
    b.add(G.plane(15, 2.2), M.archive, T(-3, 2.2, -13.78), NO);
    b.add(G.box(15.2, 0.1, 0.25), M.strip, T(-3, 3.35, -13.7), NO);
    b.add(G.box(15, 0.9, 1.1), M.concrete, T(-3, 0.45, -12.8));
    for (let i = 0; i < 8; i++) b.add(G.box(0.9, 0.08, 0.6), M.wallWhite, T(-9.5 + i * 1.8, 0.94, -12.8, i * 0.2), NO);
  });
}

// ── 조명 기구 (발광 스트립) ────────────────────────────────────
function lighting(b, M) {
  // 층 아래 선형 조명
  for (let z = -12; z <= 12; z += 3) {
    b.add(G.box(7, 0.05, 0.12), M.strip, T(12, F2 - 0.52, z), NO);
    b.add(G.box(6, 0.05, 0.12), M.strip, T(14, F3 - 0.52, z), NO);
  }
  for (let x = -18; x <= 2; x += 3) b.add(G.box(0.12, 0.05, 4), M.strip, T(x, F2 - 0.52, -11), NO);
  // 3층 / 아트리움 천장
  for (let z = -11; z <= 12; z += 4.6) b.add(G.box(5, 0.05, 0.1), M.stripCool, T(14, ROOF - 0.35, z), NO);
  // 헤리티지 존 라이트박스 (사진 속 사각 조명)
  b.add(G.box(3.2, 0.25, 2.2), M.lightbox, T(15, F3 + 4.2, 6.5));
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

  add(new THREE.HemisphereLight('#c4d0e6', '#3a342c', 1), 0.55);
  add(new THREE.DirectionalLight('#dfe8ff', 1), 0.35).position.set(30, 60, 40);

  const spot = (pos, target, base, color = '#fff1dc', angle = 0.6) => {
    const l = new THREE.SpotLight(color, 1, 0, angle, 0.6, 2);
    l.position.set(...pos);
    l.target.position.set(...target);
    add(l, base);
  };
  spot([-7, 16.3, 10], [-8, 0, 4], 700, '#fff1dc', 0.75); // 1층 클래식카
  spot([-9, 5, 2], [-9, 14, 1.5], 140, '#ffffff', 1.0); // 레일 업라이트
  spot([14, 16.3, 3], [14, F3, -6], 450, '#f4f7ff', 0.8); // 게이트
  spot([13.5, 16.3, 4], [16.5, F3, 8.4], 220, '#fff1dc', 0.5); // 엘란트라

  const point = (pos, base, color = '#ffe9cc') => {
    const l = new THREE.PointLight(color, 1, 0, 2);
    l.position.set(...pos);
    add(l, base);
  };
  point([15, F3 - 1.2, -9.5], 120); // 제도실
  point([12, F2 - 1.2, 4], 160); // 1층 안쪽
  point([-3, F3 + 3, -11.5], 120); // 아카이브

  const wall = new THREE.RectAreaLight('#a9d4ff', 1, 22, 6);
  wall.position.set(X0 + 0.7, 9.6, 1);
  wall.lookAt(0, 9.6, 1);
  add(wall, 5);

  for (const { light } of list) light.intensity = 0;
  return list;
}
