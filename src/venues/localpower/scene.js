import * as THREE from 'three';
import { Builder, G, T, truss, member, beam, std, glow, revealable } from '../../scene/kit.js';
import { ledTexture, panelTexture, hoardingTexture, sponsorTexture, exhibitionTexture, lightboxTexture } from './textures.js';

/*
 * 성수동 세원정밀 창고 — LOCAL POWER 2025 홍콩 패션 in 서울
 * 소개서 렌더·현장 사진을 참고해 단순화한 공간 모델. 단위 m, 창고 바닥 중심이 원점.
 *   -x: 패션쇼장 (백드롭)   +x: 전시장 → 네트워킹 중정   +z: 거리 쪽 (가림막)
 * 창고 벽·지붕은 안쪽 면만 그려서(BackSide) 밖에서는 내부가 들여다보이는 컷어웨이.
 */

const PI = Math.PI;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

// 창고 치수
const HX = 32; // 길이 방향 반폭
const HZ = 10; // 폭 방향 반폭
const EAVE = 6.6;
const RIDGE = 9.4;

export function build() {
  const tex = {
    led: ledTexture(),
    panel: panelTexture(),
    hoarding: hoardingTexture(),
    sponsor: sponsorTexture(),
    exhibition: exhibitionTexture(),
    city: lightboxTexture(0),
    diner: lightboxTexture(1),
  };
  const M = {
    ground: std('#17181b', 0.95),
    street: std('#222327', 0.9),
    walk: std('#4a4a4c', 0.9),
    slab: std('#4b4843', 0.85),
    court: std('#5e5b56', 0.9),
    neighbor: std('#34363b', 0.9),
    shell: std('#cfc9bf', 0.92, 0, { side: THREE.BackSide }),
    roofIn: std('#2e2a26', 0.9, 0, { side: THREE.BackSide }),
    steel: std('#2a2c30', 0.55, 0.6),
    black: std('#0c0c0f', 0.6, 0.2),
    runwayTop: std('#0a0a0d', 0.18, 0.4),
    white: std('#ecebe8', 0.6),
    plinth: std('#f2f1ee', 0.45),
    curtain: std('#bdbcb8', 0.95, 0, { side: THREE.DoubleSide }),
    bench: std('#bcbab5', 0.85),
    edge: glow('#ffffff', 1.2),
    truss: std('#1b1c20', 0.45, 0.7),
    silver: std('#b9bec6', 0.35, 0.85),
    paper: std('#f5efe6', 0.7),
    carpet: std('#a8161b', 0.95),
    wood: std('#6b4a30', 0.8),
    foliage: std('#2c4a26', 1),
    trunk: std('#3a2b20', 1),
    skin: std('#e9e7e3', 0.4),
    car: std('#6f7a86', 0.4, 0.5),
    garments: ['#1f4a38', '#b8281e', '#18191d', '#a87b55', '#e0662a', '#3a4d74', '#7a7a50'].map((c) => std(c, 0.85)),
    led: glow('#ffffff', 1.05, { map: tex.led }),
    panel: glow('#ffffff', 1.0, { map: tex.panel }),
    hoarding: std('#ffffff', 0.8, 0, { map: tex.hoarding, emissive: '#ffffff', emissiveMap: tex.hoarding, emissiveIntensity: 0.35 }),
    sponsor: std('#ffffff', 0.8, 0, { map: tex.sponsor, emissive: '#ffffff', emissiveMap: tex.sponsor, emissiveIntensity: 0.25 }),
    exhibition: std('#ffffff', 0.8, 0, { map: tex.exhibition, emissive: '#ffffff', emissiveMap: tex.exhibition, emissiveIntensity: 0.35 }),
    city: glow('#ffffff', 1.0, { map: tex.city }),
    diner: glow('#ffffff', 1.0, { map: tex.diner }),
    pink: glow('#ff3fd2', 3),
    lens: glow('#fff1d8', 4),
    down: glow('#ffffff', 3),
    lantern: glow('#ff3322', 2.2),
    warm: glow('#ffb070', 2.5),
    beamPink: beamMat('#ff4fd8'),
    beamCyan: beamMat('#5fd8ff'),
    beamGreen: beamMat('#6dff8a'),
    beamWhite: beamMat('#fff2dc', 0.05),
  };

  const b = new Builder();

  b.withLayer('context', () => {
    site(b, M);
    warehouse(b, M);
  });

  showHall(b, M);
  exhibitionHall(b, M);
  hoarding(b, M);
  courtyard(b, M);

  const root = b.build();
  const lights = addLights(root);
  return { root, lights };
}

const beamMat = (color, opacity = 0.07) =>
  revealable(
    new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    }),
  );

// ── 지오메트리 헬퍼 ───────────────────────────────────────────
const cache = new Map();
const memo = (key, make) => {
  if (!cache.has(key)) cache.set(key, make());
  return cache.get(key);
};

/** 수평 평면 도형을 높이 h로 돌출 (points: [x, z] 배열, 바닥이 y=0) */
function slabGeometry(key, points, h) {
  return memo(`slab:${key}`, () => {
    const shape = new THREE.Shape(points.map(([x, z]) => new THREE.Vector2(x, -z)));
    const g = new THREE.ExtrudeGeometry(shape, { depth: h, bevelEnabled: false });
    g.rotateX(-PI / 2);
    return g;
  });
}

/** 주름진 커튼 띠: 경로(points [x,z])를 따라 높이 h, 주름 진폭 amp */
function curtainGeometry(key, points, h, amp = 0.05, closed = false) {
  return memo(`curtain:${key}`, () => {
    const pts = points.map(([x, z]) => new THREE.Vector2(x, z));
    if (closed) pts.push(pts[0].clone());
    // 0.08m 간격으로 재샘플
    const dense = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const n = Math.max(1, Math.ceil(pts[i].distanceTo(pts[i + 1]) / 0.08));
      for (let k = 0; k < n; k++) dense.push(pts[i].clone().lerp(pts[i + 1], k / n));
    }
    dense.push(pts[pts.length - 1].clone());
    const pos = [];
    const idx = [];
    dense.forEach((p, i) => {
      const a = dense[Math.max(0, i - 1)];
      const c = dense[Math.min(dense.length - 1, i + 1)];
      const t = c.clone().sub(a).normalize();
      const off = Math.sin(i * 1.9) * amp;
      const x = p.x - t.y * off;
      const z = p.y + t.x * off;
      pos.push(x, 0, z, x, h, z);
      if (i > 0) {
        const s = (i - 1) * 2;
        idx.push(s, s + 2, s + 1, s + 1, s + 2, s + 3);
      }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    return g;
  });
}

/** 좌우 반폭 hw, 높이 h 인 박공 삼각형 (밑변 y=0) */
const gableGeometry = (hw, h) =>
  memo(`gable:${hw}:${h}`, () => new THREE.ShapeGeometry(new THREE.Shape([new THREE.Vector2(-hw, 0), new THREE.Vector2(hw, 0), new THREE.Vector2(0, h)])));

const ring = (cx, cz, r, n = 40) =>
  Array.from({ length: n }, (_, i) => [cx + Math.cos((i / n) * PI * 2) * r, cz + Math.sin((i / n) * PI * 2) * r]);

// ── 대지 / 주변 ──────────────────────────────────────────────
function site(b, M) {
  b.add(G.box(420, 0.1, 420), M.ground, T(0, -0.1, 0), { outline: false });
  b.add(G.box(180, 0.04, 10), M.street, T(0, -0.03, 20.5), { outline: false });
  b.add(G.box(180, 0.12, 4.5), M.walk, T(0, -0.02, 13.2));
  for (let x = -88; x < 90; x += 6) b.line(V(x, 0.02, 20.5), V(x + 3, 0.02, 20.5));

  // 이웃 창고·건물
  b.add(G.box(36, 7.5, 22), M.neighbor, T(-53, 3.75, -1));
  b.add(G.box(14, 9, 20), M.neighbor, T(56, 4.5, -2));
  b.add(G.box(12, 11, 24), M.neighbor, T(70, 5.5, -4));
  b.add(G.box(16, 8, 18), M.neighbor, T(-42, 4, -24));

  // 전신주와 전선
  const poles = [-38, -10, 20, 48];
  for (const x of poles) {
    b.add(G.cyl(0.14, 0.18, 9, 8), M.steel, T(x, 4.5, 15));
    b.add(G.box(1.6, 0.12, 0.12), M.steel, T(x, 8.4, 15), { outline: false });
  }
  for (let i = 0; i < poles.length - 1; i++) {
    for (const dz of [-0.7, 0.7]) {
      const a = V(poles[i], 8.4, 15 + dz);
      const c = V(poles[i + 1], 8.4, 15 + dz);
      const mid = a.clone().lerp(c, 0.5).setY(7.6);
      b.polyline([a, a.clone().lerp(mid, 0.5).setY(7.9), mid, mid.clone().lerp(c, 0.5).setY(7.9), c]);
    }
  }

  // 길가 주차 차량
  for (const [x, len, h] of [[-50, 6.5, 2.6], [-43, 4.4, 1.5], [-37.5, 4.2, 1.4]]) {
    b.add(G.box(len, h * 0.55, 1.9), M.car, T(x, h * 0.35, 17));
    b.add(G.box(len * 0.55, h * 0.4, 1.7), M.car, T(x - len * 0.1, h * 0.8, 17), { outline: false });
  }
}

// ── 창고 외피 (컷어웨이) ───────────────────────────────────────
function warehouse(b, M) {
  b.add(G.box(HX * 2 + 0.6, 0.12, HZ * 2 + 0.6), M.slab, T(0, 0, 0));

  // 벽: 안쪽을 향하는 면만 렌더 (BackSide) → 밖에서는 투시
  const wallH = EAVE;
  b.add(G.plane(HX * 2, wallH), M.shell, T(0, wallH / 2, -HZ, PI)); // 뒷벽 (법선 -z)
  b.add(G.plane(HX * 2, wallH), M.shell, T(0, wallH / 2, HZ)); // 앞벽 (법선 +z)
  b.add(G.plane(HZ * 2, wallH), M.shell, T(-HX, wallH / 2, 0, -PI / 2)); // 백드롭 쪽 끝벽
  b.add(G.plane(HZ * 2, wallH), M.shell, T(HX, wallH / 2, 0, PI / 2)); // 중정 쪽 끝벽
  b.add(gableGeometry(HZ, RIDGE - EAVE), M.shell, T(-HX, EAVE, 0, -PI / 2));
  b.add(gableGeometry(HZ, RIDGE - EAVE), M.shell, T(HX, EAVE, 0, PI / 2));

  // 지붕 두 경사면
  const theta = Math.atan2(RIDGE - EAVE, HZ);
  const slope = Math.hypot(RIDGE - EAVE, HZ);
  const yMid = (EAVE + RIDGE) / 2;
  b.add(G.plane(HX * 2, slope), M.roofIn, T(0, yMid, -HZ / 2, 0, -(PI / 2 + theta)));
  b.add(G.plane(HX * 2, slope), M.roofIn, T(0, yMid, HZ / 2, 0, -PI / 2 + theta));

  // 고창 (선만) + 앞벽 출입구
  for (let x = -HX + 4; x < HX; x += 8) {
    for (const z of [-HZ, HZ]) b.add(G.box(4.2, 1.2, 0.05), null, T(x, 4.9, z));
  }
  b.add(G.box(3.2, 3.2, 0.05), null, T(HX, 1.6, 2, PI / 2)); // 중정 쪽 출입구
  b.add(G.box(2.4, 2.8, 0.05), null, T(-6, 1.4, HZ)); // 쇼장 측면 출입구

  // 기둥 + 지붕 트러스 (8m 간격)
  for (let x = -HX; x <= HX; x += 8) {
    for (const z of [-HZ + 0.2, HZ - 0.2]) b.add(G.box(0.3, EAVE, 0.3), M.steel, T(x, EAVE / 2, z), { outline: false });
    b.group(T(x, 0, 0), () => roofTruss(b, M));
  }
  // 도리(퍼린)와 하현 연결재
  for (let i = 0; i <= 4; i++) {
    const t = i / 4;
    for (const s of [-1, 1]) {
      const z = s * HZ * (1 - t);
      const y = EAVE + (RIDGE - EAVE) * t + 0.12;
      if (i === 4 && s === 1) continue;
      member(b, V(-HX, y, z), V(HX, y, z), 0.12, M.steel);
    }
  }
  member(b, V(-HX, EAVE - 0.9, 0), V(HX, EAVE - 0.9, 0), 0.1, M.steel);
  // 끝 칸 지붕 가새
  for (const [x0, x1] of [[-HX, -HX + 8], [HX - 8, HX]]) {
    for (const s of [-1, 1]) {
      b.line(V(x0, EAVE, s * HZ), V(x1, RIDGE, 0));
      b.line(V(x1, EAVE, s * HZ), V(x0, RIDGE, 0));
    }
  }
}

/** 한 개 트러스 프레임 (x=0 평면, z축 방향 스팬) */
function roofTruss(b, M) {
  const bottom = EAVE - 0.9;
  const n = 8;
  const topY = (z) => EAVE + (RIDGE - EAVE) * (1 - Math.abs(z) / HZ);
  member(b, V(0, bottom, -HZ), V(0, bottom, HZ), 0.12, M.steel);
  member(b, V(0, EAVE, -HZ), V(0, RIDGE, 0), 0.14, M.steel);
  member(b, V(0, EAVE, HZ), V(0, RIDGE, 0), 0.14, M.steel);
  for (let i = 0; i <= n; i++) {
    const z = -HZ + (i * HZ * 2) / n;
    member(b, V(0, bottom, z), V(0, topY(z), z), 0.07, M.steel);
    if (i < n) {
      const z1 = z + (HZ * 2) / n;
      const up = z < 0;
      member(b, V(0, bottom, up ? z : z1), V(0, topY(up ? z1 : z), up ? z1 : z), 0.06, M.steel);
    }
  }
}

// ── 패션쇼장 ─────────────────────────────────────────────────
const RUNWAY = { x0: -25, x1: -4.2, w: 3.2, h: 0.5 };

function showHall(b, M) {
  const { x0, x1, w, h } = RUNWAY;
  const len = x1 - x0;
  const cx = (x0 + x1) / 2;

  // 런웨이: 흰 스커트 + 유광 블랙 상판 + 핑크 LED 라인
  b.add(G.box(len, h - 0.04, w), M.white, T(cx, (h - 0.04) / 2, 0));
  b.add(G.box(len, 0.04, w), M.runwayTop, T(cx, h - 0.02, 0), { outline: false });
  for (const s of [-1, 1]) b.add(G.box(len, 0.035, 0.05), M.pink, T(cx, h + 0.005, s * (w / 2 - 0.03)), { outline: false });
  b.add(G.box(0.05, 0.035, w), M.pink, T(x1 - 0.03, h + 0.005, 0), { outline: false });

  // 백스테이지 무대 + LED 백드롭
  b.add(G.box(4, h, 15), M.black, T(-27.2, h / 2, 0));
  b.add(G.box(0.5, 5.2, 15.4), M.black, T(-29.5, 2.6 + h, 0));
  b.add(G.plane(7.2, 4), M.led, T(-29.2, h + 2.5, 0, PI / 2), { outline: false });
  for (const s of [-1, 1]) b.add(G.plane(3, 4), M.panel, T(-29.2, h + 2.5, s * 5.5, PI / 2), { outline: false });
  b.add(G.box(0.06, 4, 7.2), null, T(-29.2, h + 2.5, 0));

  // 좌석: 흰색 박스 벤치 3열 (뒤로 갈수록 높게) + 앞줄 기념품 백
  const rows = [
    [2.55, 0.45],
    [3.55, 0.6],
    [4.55, 0.75],
  ];
  for (const s of [-1, 1]) {
    rows.forEach(([z, bh], row) => {
      for (let sx = -23.5; sx < -5; sx += 4.8) {
        const segX = sx + 2;
        b.add(G.box(4, bh, 0.55), M.bench, T(segX, bh / 2, s * z));
        if (row === 0) {
          for (let k = -1.6; k <= 1.6; k += 0.8) {
            b.add(G.box(0.26, 0.32, 0.1), M.paper, T(segX + k, bh + 0.16, s * (z + 0.05)), { outline: false });
          }
        }
      }
    });
  }

  // 벽면 흰 필라스터
  for (let x = -28; x <= -2; x += 4.5) {
    for (const s of [-1, 1]) b.add(G.box(1, 5.2, 0.5), M.white, T(x, 2.6, s * (HZ - 0.5)));
  }

  // 트러스: 런웨이 양옆 사이드 트러스 + 입구 쪽 포털
  const s = 0.3;
  const top = 5.6;
  const tz = 6.6;
  for (const z of [-tz, tz]) {
    for (const x of [-24, -16, -8]) {
      b.add(G.box(0.8, 0.08, 0.8), M.truss, T(x, 0.04, z), { outline: false });
      truss(b, V(x, 0.08, z), V(x, top, z), s, M.truss);
    }
    truss(b, V(-24, top, z), V(-8, top, z), s, M.truss);
  }
  const px = -2.6;
  for (const z of [-tz, tz]) truss(b, V(px, 0.08, z), V(px, top, z), s, M.truss);
  truss(b, V(px, top, -tz), V(px, top, tz), s, M.truss);

  // 무빙라이트
  const heads = [];
  for (const z of [-tz, tz]) for (let x = -23; x <= -9; x += 2.8) heads.push([x, z]);
  for (let z = -5; z <= 5; z += 2.5) heads.push([px, z]);
  for (const [x, z] of heads) movingHead(b, M, x, top - 0.35, z);

  // 컬러 빔
  const beamColors = [M.beamPink, M.beamCyan, M.beamGreen, M.beamWhite];
  let i = 0;
  for (const z of [-tz, tz]) {
    for (const x of [-21.4, -15.8]) {
      beam(b, V(x, top - 0.6, z), V(x - 2 + (i % 3) * 1.5, h, -z * 0.12), beamColors[i % 4], 0.8);
      i++;
    }
  }

  // 포토 라이저 (런웨이 끝)
  b.add(G.box(1.6, 0.6, 5), M.black, T(-2.2, 0.3, 0));
  b.add(G.box(0.8, 0.4, 5), M.black, T(-1.8, 0.8, 0));

  // 런웨이 위 모델
  mannequin(b, M, -21.5, h, 0, PI / 2, M.garments[4], 'dress');
}

function movingHead(b, M, x, y, z) {
  b.group(T(x, y, z), () => {
    b.add(G.box(0.36, 0.14, 0.36), M.black, T(0, 0.12, 0), { outline: false });
    b.add(G.box(0.34, 0.3, 0.06), M.black, T(0, -0.05, 0), { outline: false });
    b.add(G.sphere(0.17, 10), M.black, T(0, -0.16, 0), { outline: false });
    b.add(G.cyl(0.1, 0.1, 0.03, 12), M.lens, T(0, -0.33, 0), { outline: false });
  });
}

/** 마네킹: kind = 'suit' | 'dress' | 'coat' */
function mannequin(b, M, x, y, z, ry, cloth, kind = 'suit') {
  b.group(T(x, y, z, ry), () => {
    b.add(G.cyl(0.2, 0.2, 0.02, 16), M.silver, T(0, 0.01, 0), { outline: false });
    b.add(G.sphere(0.11, 12), M.skin, T(0, 1.72, 0), { outline: false });
    b.add(G.cyl(0.04, 0.05, 0.12, 8), M.skin, T(0, 1.58, 0), { outline: false });
    b.add(G.box(0.42, 0.62, 0.24), cloth, T(0, 1.2, 0));
    for (const s of [-1, 1]) b.add(G.box(0.1, 0.62, 0.12), cloth, T(s * 0.26, 1.18, 0, 0, 0, s * 0.08), { outline: false });
    if (kind === 'dress') {
      b.add(G.cyl(0.2, 0.34, 0.95, 12), cloth, T(0, 0.45, 0), { outline: false });
    } else if (kind === 'coat') {
      b.add(G.cyl(0.24, 0.3, 1.0, 10), cloth, T(0, 0.42, 0), { outline: false });
    } else {
      for (const s of [-1, 1]) b.add(G.box(0.15, 0.9, 0.16), M.garments[2], T(s * 0.1, 0.45, 0), { outline: false });
    }
  });
}

// ── 전시장 ───────────────────────────────────────────────────
function exhibitionHall(b, M) {
  // 쇼장과 전시장 사이 가벽 (출입 통로 남김)
  b.add(G.box(0.3, 5, 14), M.white, T(0, 2.5, -3));
  b.add(G.box(0.3, 5, 1.5), M.white, T(0, 2.5, HZ - 0.75));

  // 뒷벽 흰 가벽 + 긴 전시대 + 마네킹·도자 조형
  b.add(G.box(27, 4.2, 0.3), M.white, T(16.5, 2.1, -9.3));
  b.add(G.box(26, 0.22, 1.3), M.plinth, T(16.5, 0.11, -8.4));
  let k = 0;
  for (let x = 4.3; x <= 28.8; x += 1.4, k++) {
    if (k % 4 === 0) {
      for (let j = 0; j < 5; j++) b.add(G.cyl(0.14 - (j % 2) * 0.04, 0.14, 0.34, 12), M.plinth, T(x, 0.39 + j * 0.34, -8.4), { outline: false });
    } else {
      mannequin(b, M, x, 0.22, -8.4, 0, M.garments[k % M.garments.length], k % 3 === 0 ? 'coat' : 'suit');
    }
  }

  // 독립 가벽 + 벽면 라이트박스
  b.add(G.box(0.3, 3.8, 8), M.white, T(3.6, 1.9, -1));
  b.add(G.box(0.08, 1.8, 3.2), M.white, T(3.8, 2.1, -1));
  b.add(G.plane(3, 1.65), M.diner, T(3.85, 2.1, -1, PI / 2), { outline: false });

  // 원형 커튼 기둥 전시대
  column(b, M, 10.5, -1.5, 2.2, 1.15, 4.6, 3);
  column(b, M, 25.5, -4.5, 1.6, 0.85, 4.2, 2);

  // 물결 커튼 전시대
  wave(b, M, 20, 3);

  // 스탠드형 라이트박스
  lightbox(b, M, 14.8, -5.6, 0.3, M.city);
  lightbox(b, M, 28.6, 3.8, -PI / 2, M.city);

  // 천장 냉난방기·레일 조명 (전시장)
  for (let x = 8; x <= 24; x += 8) {
    b.add(G.box(1, 0.3, 1), M.white, T(x + 4, EAVE - 1.1, -4), { outline: false });
    for (let z = -7; z <= 7; z += 3.5) b.add(G.cyl(0.08, 0.08, 0.12, 10), M.down, T(x, EAVE - 1.02, z), { outline: false });
  }
}

function column(b, M, x, z, rPlat, rCurtain, h, count) {
  b.group(T(x, 0, z), () => {
    b.add(slabGeometry(`plat:${rPlat}`, ring(0, 0, rPlat, 48), 0.3), M.plinth);
    b.add(G.torus(rPlat, 0.015, 48), M.edge, T(0, 0.3, 0, 0, PI / 2), { outline: false });
    b.add(curtainGeometry(`col:${rCurtain}:${h}`, ring(0, 0, rCurtain, 36), h, 0.05, true), M.curtain, T(0, 0.3, 0), { outline: false });
    // 커튼 윤곽선
    const top = ring(0, 0, rCurtain, 24).map(([px, pz]) => V(px, 0.3 + h, pz));
    b.polyline(top, true);
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * PI * 2;
      b.line(V(Math.cos(a) * rCurtain, 0.3, Math.sin(a) * rCurtain), V(Math.cos(a) * rCurtain, 0.3 + h, Math.sin(a) * rCurtain));
    }
    for (let i = 0; i < count; i++) {
      const a = PI / 2 + (i - (count - 1) / 2) * 0.9;
      const r = (rPlat + rCurtain) / 2 + 0.05;
      mannequin(b, M, Math.cos(a) * r, 0.3, Math.sin(a) * r, PI / 2 - a, M.garments[(i * 3 + count) % M.garments.length]);
    }
  });
}

function wave(b, M, cx, cz) {
  const half = 4.6;
  const back = (x) => -1.0 + 0.45 * Math.sin(x * 0.85);
  const front = (x) => 1.15 + 0.35 * Math.sin(x * 0.85 + 0.9);
  const pts = [];
  const N = 30;
  for (let i = 0; i <= N; i++) {
    const x = -half + (i / N) * half * 2;
    pts.push([x, back(x)]);
  }
  const endArc = (x, dir) => {
    const b0 = back(x);
    const f0 = front(x);
    const c = (b0 + f0) / 2;
    const r = (f0 - b0) / 2;
    for (let i = 1; i < 12; i++) {
      const a = (i / 12) * PI;
      pts.push(dir > 0 ? [x + r * Math.sin(a), c - r * Math.cos(a)] : [x - r * Math.sin(a), c + r * Math.cos(a)]);
    }
  };
  endArc(half, 1);
  for (let i = N; i >= 0; i--) {
    const x = -half + (i / N) * half * 2;
    pts.push([x, front(x)]);
  }
  endArc(-half, -1);

  b.group(T(cx, 0, cz), () => {
    b.add(slabGeometry('wave', pts, 0.3), M.plinth);
    const curtainPath = [];
    for (let i = 0; i <= 24; i++) {
      const x = -half + 0.5 + (i / 24) * (half - 0.5) * 2;
      curtainPath.push([x, back(x) + 0.3]);
    }
    b.add(curtainGeometry('wave', curtainPath, 4.1, 0.06), M.curtain, T(0, 0.3, 0), { outline: false });
    b.polyline(curtainPath.map(([x, z]) => V(x, 4.4, z)));
    for (let i = 0; i <= 24; i += 4) b.line(V(curtainPath[i][0], 0.3, curtainPath[i][1]), V(curtainPath[i][0], 4.4, curtainPath[i][1]));
    // 전시대 가장자리 조명
    for (let i = 0; i < pts.length; i += 2) {
      const [x, z] = pts[i];
      b.add(G.box(0.18, 0.02, 0.02), M.edge, T(x, 0.29, z), { outline: false });
    }
    [-3.6, -1.8, 0, 1.8, 3.6].forEach((x, i) => {
      mannequin(b, M, x, 0.3, (back(x) + front(x)) / 2 + 0.25, 0, M.garments[i], i === 3 ? 'coat' : 'suit');
    });
  });
}

function lightbox(b, M, x, z, ry, mat) {
  b.group(T(x, 0, z, ry), () => {
    b.add(G.box(1.25, 2.1, 0.22), M.white, T(0, 1.05, 0));
    b.add(G.plane(1.05, 1.9), mat, T(0, 1.07, 0.115), { outline: false });
  });
}

// ── 거리 쪽 가림막 (키 비주얼) ─────────────────────────────────
function hoarding(b, M) {
  const z = HZ + 0.9;
  const h = 4.2;
  const panels = [
    [-31.5, 24, M.hoarding],
    [-7.5, 4, M.sponsor],
    [-3.5, 14, M.exhibition],
  ];
  for (const [x0, w, mat] of panels) {
    const cx = x0 + w / 2;
    b.add(G.box(w, h, 0.2), M.black, T(cx, h / 2, z));
    b.add(G.plane(w, h), mat, T(cx, h / 2, z + 0.11), { outline: false });
  }
  // 뒤쪽 비계 (선)
  b.withLayer('context', () => {
    for (let x = -31; x <= 10; x += 3) b.line(V(x, 0, z - 0.6), V(x, h, z - 0.6));
    for (const y of [0.6, 2.1, 3.6]) b.line(V(-31.5, y, z - 0.6), V(10.5, y, z - 0.6));
  });

  // 레드카펫 + 차단봉
  b.add(G.box(3, 0.03, 13), M.carpet, T(38, 0.02, 6.5), { outline: false });
  b.add(G.box(6.5, 0.03, 2.6), M.carpet, T(35.2, 0.025, 1.5), { outline: false });
  b.add(G.box(3, 0.03, 13), null, T(38, 0.02, 6.5));
  for (let zz = 4; zz <= 12; zz += 2) {
    for (const sx of [36.2, 39.8]) b.add(G.cyl(0.04, 0.04, 0.95, 8), M.silver, T(sx, 0.48, zz), { outline: false });
  }
}

// ── 네트워킹 중정 ─────────────────────────────────────────────
function courtyard(b, M) {
  const x0 = HX;
  const x1 = 47;
  const z0 = -7;
  const z1 = HZ + 1.5;
  const wh = 2.6;
  b.add(G.box(x1 - x0, 0.08, z1 - z0), M.court, T((x0 + x1) / 2, 0.04, (z0 + z1) / 2), { outline: false });

  // 흰색 담장 (정문 36.5~39.5 개방)
  b.add(G.box(x1 - x0, wh, 0.25), M.white, T((x0 + x1) / 2, wh / 2, z0));
  b.add(G.box(0.25, wh, z1 - z0), M.white, T(x1, wh / 2, (z0 + z1) / 2));
  b.add(G.box(36.5 - x0, wh, 0.25), M.white, T((x0 + 36.5) / 2, wh / 2, z1));
  b.add(G.box(x1 - 39.5, wh, 0.25), M.white, T((39.5 + x1) / 2, wh / 2, z1));
  for (const gx of [36.5, 39.5]) b.add(G.box(0.6, 3.6, 0.6), M.white, T(gx, 1.8, z1));

  // 흰 파고다 텐트
  for (const tx of [35.5, 39.5, 43.5]) {
    b.group(T(tx, 0, -4.4), () => {
      for (const [px, pz] of [[-1.5, -1.5], [1.5, -1.5], [1.5, 1.5], [-1.5, 1.5]]) {
        b.add(G.box(0.08, 2.5, 0.08), M.silver, T(px, 1.25, pz), { outline: false });
      }
      b.add(G.box(3.1, 0.25, 3.1), M.white, T(0, 2.5, 0));
      b.add(G.cyl(0.02, 2.2, 1.6, 4), M.white, T(0, 3.42, 0, PI / 4));
    });
  }

  // 바 카운터
  b.add(G.box(0.8, 1.05, 5), M.white, T(45.6, 0.525, 3));
  b.add(G.box(0.05, 0.8, 4.6), M.carpet, T(45.18, 0.55, 3), { outline: false });

  // 하이테이블 + 스툴
  for (const [x, z] of [[35, 3.5], [41.5, 2.5], [35.2, 8], [42.5, 7.5], [40.5, -0.8]]) {
    b.add(G.cyl(0.38, 0.38, 0.04, 20), M.white, T(x, 1.08, z));
    b.add(G.cyl(0.04, 0.04, 1.05, 8), M.silver, T(x, 0.53, z), { outline: false });
    b.add(G.cyl(0.25, 0.25, 0.02, 16), M.silver, T(x, 0.02, z), { outline: false });
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * PI * 2 + x;
      b.add(G.cyl(0.18, 0.18, 0.72, 10), M.wood, T(x + Math.cos(a) * 0.75, 0.36, z + Math.sin(a) * 0.75), { outline: false });
    }
  }

  // 홍등 줄 조명
  for (const z of [0.5, 4.5, 8.5]) {
    const a = V(x0 + 0.3, 3.4, z);
    const c = V(x1 - 0.3, 3.4, z);
    const pts = [];
    for (let i = 0; i <= 10; i++) {
      const t = i / 10;
      pts.push(a.clone().lerp(c, t).setY(3.4 - Math.sin(t * PI) * 0.45));
    }
    b.polyline(pts);
    for (let i = 1; i < 10; i++) {
      b.add(G.sphere(0.2, 10), M.lantern, T(pts[i].x, pts[i].y - 0.3, z, 0, 0, 0, 1, 1.15, 1), { outline: false });
    }
  }

  // 조경 나무
  b.withLayer('context', () => {
    for (const [x, z, s] of [[45.5, -5.2, 1.1], [33.2, -5.6, 0.9]]) {
      b.group(T(x, 0, z, 0, 0, 0, s, s, s), () => {
        b.add(G.cyl(0.15, 0.22, 3, 8), M.trunk, T(0, 1.5, 0), { outline: false });
        b.add(G.ico(1, 1), M.foliage, T(0, 4.2, 0, 0, 0, 0, 1.8, 2.4, 1.8));
      });
    }
  });
}

// ── 조명 (실제 구현 모드에서만 켜짐) ─────────────────────────────
function addLights(root) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    if (light.target) root.add(light.target);
    list.push({ light, base });
    light.intensity = 0;
    return light;
  };

  add(new THREE.HemisphereLight('#8a96b8', '#2a2016', 1), 0.45);
  add(new THREE.DirectionalLight('#aab8dc', 1), 0.7).position.set(40, 60, 50);

  const spot = (pos, target, base, color, angle = 0.5, penumbra = 0.6) => {
    const l = new THREE.SpotLight(color, 1, 0, angle, penumbra, 2);
    l.position.set(...pos);
    l.target.position.set(...target);
    add(l, base);
  };
  // 런웨이 키 라이트 (포털 트러스)
  spot([-2.6, 5.3, 0], [-15, 0.5, 0], 110, '#fff0dc', 0.3, 0.7);
  spot([-8, 5.3, 6.6], [-20, 0.5, 0], 50, '#ff5ad8', 0.35);
  spot([-8, 5.3, -6.6], [-24, 0.5, 0], 50, '#63d4ff', 0.35);
  // 벽면 주황 워시 (현장 사진의 따뜻한 톤)
  spot([-14, 5.8, 3], [-14, 3.2, -HZ], 150, '#ff6a24', 0.85, 0.9);
  spot([-14, 5.8, -3], [-14, 3.2, HZ], 150, '#ff6a24', 0.85, 0.9);
  const hallWarm = new THREE.PointLight('#ff7a3a', 1, 0, 2);
  hallWarm.position.set(-16, 5.5, 0);
  add(hallWarm, 25);

  const led = new THREE.RectAreaLight('#ff7a3c', 1, 7.2, 4);
  led.position.set(-29.1, 3, 0);
  led.lookAt(0, 3, 0);
  add(led, 3);

  // 전시장: 중성 백색 다운라이트
  spot([10.5, 5.6, 4], [10.5, 1.5, -1.5], 30, '#f4f6ff', 0.5, 0.8);
  spot([20, 5.6, 8], [20, 1.2, 2.5], 40, '#f4f6ff', 0.55, 0.8);
  spot([16, 5.6, -2], [16, 1.6, -9.3], 60, '#eef2ff', 1.0, 0.8);
  const fill = new THREE.PointLight('#dfe6ff', 1, 0, 2);
  fill.position.set(16, 5.2, 1);
  add(fill, 18);

  // 중정 홍등 불빛
  const court = new THREE.PointLight('#ff8a5a', 1, 0, 2);
  court.position.set(39.5, 3, 4.5);
  add(court, 110);

  return list;
}
