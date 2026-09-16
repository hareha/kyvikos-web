import * as THREE from 'three';
import { Builder, G, T, member, std, glow, revealable } from '../../scene/kit.js';
import { pbr, placeModel } from '../../scene/assets.js';
import {
  artAtlas, introTexture, logoTexture, posterTexture, projectionTexture,
  screenTexture, shopWallTexture, photoWallTexture, totemTexture,
} from './textures.js';

/*
 * 동대문디자인플라자(DDP) 전시홀 — 장미셸 바스키아 SEOUL 전시
 * 소개서 렌더·현장 사진을 참고해 단순화한 공간 모델. 단위 m, 전시홀 중심이 원점.
 *   +z: 앞쪽(로비·입구·아트샵)   -z: 안쪽(영상 복도)   -x: 입구 쪽   +x: 미디어룸·아트샵 쪽
 * 조감 카메라(+x, +z 위)를 향한 외벽과 천장은 선만 그려 내부가 보이게 합니다(컷어웨이).
 */

const PI = Math.PI;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

/** DDP 전시홀 외곽: 슈퍼타원(모서리가 둥근 사각형) */
const SHELL = { a: 26, c: 17, e: 0.5, h: 6.5, seg: 72 };
/** 조감 카메라의 수평 방향 (data.js overview.pos 와 맞춤) */
const CAM_DIR = new THREE.Vector2(34, 46).normalize();
const WALL_H = 4.2;
const RIG_Y = 5.3;

const shellPoint = (t) => {
  const c = Math.cos(t);
  const s = Math.sin(t);
  return [SHELL.a * Math.sign(c) * Math.abs(c) ** SHELL.e, SHELL.c * Math.sign(s) * Math.abs(s) ** SHELL.e];
};

// 아틀라스 칸(4×2)을 쓰는 평면
const cellGeoms = new Map();
function cellPlane(w, h, col, row, cols = 4, rows = 2, colSpan = 1) {
  const key = `${w}:${h}:${col}:${row}:${cols}:${rows}:${colSpan}`;
  let g = cellGeoms.get(key);
  if (!g) {
    g = new THREE.PlaneGeometry(w, h);
    const uv = g.attributes.uv;
    for (let i = 0; i < uv.count; i++) {
      uv.setXY(i, (col + uv.getX(i) * colSpan) / cols, 1 - (row + 1) / rows + uv.getY(i) / rows);
    }
    cellGeoms.set(key, g);
  }
  return g;
}

/** 사다리꼴 등 다각형 판재 (두께 depth, 중심 z=0) */
function slab(pts, depth, holes = []) {
  const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)));
  for (const hole of holes) shape.holes.push(new THREE.Path(hole.map(([x, y]) => new THREE.Vector2(x, y))));
  const g = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false });
  g.translate(0, 0, -depth / 2);
  return g;
}

export function build() {
  const tex = {
    art: artAtlas(),
    intro: introTexture(),
    logo: logoTexture(),
    poster: posterTexture(),
    projection: projectionTexture(),
    screen: screenTexture(),
    shop: shopWallTexture(),
    photo: photoWallTexture(),
    totem: totemTexture(),
  };
  const printed = (map, k = 0.35) => std('#ffffff', 0.85, 0, { map, emissive: '#ffffff', emissiveMap: map, emissiveIntensity: k });
  const M = {
    // 실사 재질 (Poly Haven CC0) — DDP 전시홀의 콘크리트 바닥과 도장 벽
    carpet: pbr('brushed_concrete', { color: '#8e9197', tile: 4, roughness: 0.55 }),
    lobby: pbr('marble_01', { color: '#e2e3e5', tile: 2.5, roughness: 0.35 }),
    shell: pbr('painted_plaster_wall', { color: '#a3a6ac', tile: 3 }),
    skirting: std('#1c1e22', 0.9),
    white: pbr('painted_plaster_wall', { color: '#f4f2ed', tile: 3 }),
    grey: pbr('painted_plaster_wall', { color: '#dbd9d3', tile: 3 }),
    navy: pbr('painted_plaster_wall', { color: '#34466e', tile: 3 }),
    black: std('#141416', 0.8),
    dark: std('#0c0c0d', 0.5, 0.3),
    maroon: std('#7a1f27', 0.7),
    frame: std('#2a2520', 0.6),
    woodFrame: std('#6b4a2c', 0.6),
    vase: std('#3d8fa3', 0.25, 0.1),
    rig: std('#0b0b0c', 0.5, 0.4),
    art: printed(tex.art, 0.28),
    intro: printed(tex.intro, 0.3),
    logo: printed(tex.logo, 0.25),
    poster: printed(tex.poster, 0.3),
    shopWall: printed(tex.shop, 0.18),
    photo: printed(tex.photo, 0.35),
    totem: printed(tex.totem, 0.4),
    projection: glow('#ffffff', 1.0, { map: tex.projection }),
    screen: glow('#dfe6f2', 0.75, { map: tex.screen }),
    lamp: glow('#fff1d6', 3),
    beam: revealable(
      new THREE.MeshBasicMaterial({
        color: '#ffe9c4',
        transparent: true,
        opacity: 0.035,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide,
      }),
    ),
  };

  const b = new Builder();
  const spots = [];

  b.withLayer('context', () => {
    hall(b, M);
    lobby(b, M);
    ceilingTracks(b, M);
  });

  entrance(b, M);
  intro(b, M, spots);
  galleryA(b, M, spots);
  galleryB(b, M, spots);
  corridor(b, M, spots);
  mediaRoom(b, M);
  artShop(b, M);
  totem(b, M, -3.5, 21.5, -0.5);

  const root = b.build();
  const lights = addLights(root, spots);
  // 로비 화분
  placeModel(root, 'potted_plant_02', [T(-19, 0.1, 16, 0.6, 0, 0, 1.3, 1.3, 1.3), T(-6, 0.1, 17, 2, 0, 0, 1.3, 1.3, 1.3)], {
    roughness: 0.7,
  });
  return { root, lights };
}

// ── DDP 전시홀 (context) ──────────────────────────────────────
function hall(b, M) {
  const pts = [];
  for (let i = 0; i < SHELL.seg; i++) pts.push(shellPoint((i / SHELL.seg) * PI * 2));

  // 바닥: 슈퍼타원 판
  const shape = new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, -z)));
  const floor = new THREE.ShapeGeometry(shape);
  floor.rotateX(-PI / 2);
  b.add(floor, M.carpet);

  const { h } = SHELL;
  for (let i = 0; i < SHELL.seg; i++) {
    const [x1, z1] = pts[i];
    const [x2, z2] = pts[(i + 1) % SHELL.seg];
    const dx = x2 - x1;
    const dz = z2 - z1;
    const len = Math.hypot(dx, dz);
    const nx = dz / len;
    const nz = -dx / len;
    const ry = Math.atan2(-dz, dx);
    const mx = (x1 + x2) / 2;
    const mz = (z1 + z2) / 2;
    const facing = nx * CAM_DIR.x + nz * CAM_DIR.y;

    if (facing < -0.12) {
      // 조감 카메라 반대편 벽: 솔리드
      b.add(G.box(len + 0.08, h, 0.4), M.shell, T(mx, h / 2, mz, ry), { outline: false });
      b.line(V(x1, h, z1), V(x2, h, z2));
      if (i % 3 === 0) b.line(V(x1, 0, z1), V(x1, h, z1));
    } else {
      // 컷어웨이: 윤곽선 + 낮은 걸레받이 (입구 개구부 제외)
      const inEntrance = mz > 10 && mx > -23 && mx < -6;
      if (!inEntrance) b.add(G.box(len + 0.08, 0.25, 0.4), M.skirting, T(mx, 0.125, mz, ry), { outline: false });
      b.line(V(x1, h, z1), V(x2, h, z2));
      b.line(V(x1, 0.02, z1), V(x2, 0.02, z2));
      if (i % 4 === 0 && !inEntrance) b.line(V(x1, 0, z1), V(x1, h, z1));
    }
  }

  // 천장: 선만 (DDP 특유의 곡선 슬롯)
  for (let k = -3; k <= 3; k++) {
    const line = [];
    for (let x = -24; x <= 24; x += 2) {
      const z = k * 4.2 + Math.sin(x * 0.12 + k) * 1.6;
      const [, zMax] = shellPoint(Math.acos(Math.min(1, Math.abs(x) / SHELL.a) ** 2));
      if (Math.abs(z) < zMax - 0.6) line.push(V(x, h, z));
    }
    if (line.length > 1) b.polyline(line);
  }
}

function lobby(b, M) {
  // 전시홀 앞 로비 (DDP의 흰 곡면 공간)
  b.add(G.box(30, 0.1, 12), M.lobby, T(-10, -0.07, 21));
  const curve = [];
  for (let i = 0; i <= 16; i++) {
    const t = i / 16;
    curve.push(V(-25 + t * 30, 0, 27 - Math.sin(t * PI) * 1.2));
  }
  for (let i = 0; i < 16; i++) {
    const a = curve[i];
    const c = curve[i + 1];
    const len = a.distanceTo(c);
    const ry = Math.atan2(-(c.z - a.z), c.x - a.x);
    b.add(G.box(len + 0.05, 0.9, 0.5), M.lobby, T((a.x + c.x) / 2, 0.45, (a.z + c.z) / 2, ry), { outline: false });
    b.line(V(a.x, 0.9, a.z), V(c.x, 0.9, c.z));
  }
}

/** 천장에 매달린 곡선 조명 트랙 */
function ceilingTracks(b, M) {
  for (const [z0, amp, x0, x1] of [[4, 2.2, -20, 6], [-9, 1.6, -22, 20], [10, 1.4, 6, 22]]) {
    let prev = null;
    for (let x = x0; x <= x1; x += 2) {
      const p = V(x, RIG_Y + 0.4, z0 + Math.sin(x * 0.18) * amp);
      if (prev) member(b, prev, p, 0.05, M.rig);
      prev = p;
    }
  }
}

// ── 가벽 / 작품 ───────────────────────────────────────────────
function wall(b, M, x1, z1, x2, z2, { h = WALL_H, t = 0.3, mat = M.white, outlineOnly = false } = {}) {
  const dx = x2 - x1;
  const dz = z2 - z1;
  const len = Math.hypot(dx, dz);
  b.add(G.box(len, h, t), outlineOnly ? null : mat, T((x1 + x2) / 2, h / 2, (z1 + z2) / 2, Math.atan2(-dz, dx)));
}

/**
 * 작품: (x, z) 벽면 위치, ry 는 작품 앞면이 바라보는 방향(0 = +z).
 * spots 에 조명 위치를 기록하고 천장 레일·조명기구를 함께 설치.
 */
function art(b, M, spots, x, z, ry, w, h, cell, { y = 2, frame = M.frame, spot = true, tile } = {}) {
  const local = T(x, 0, z, ry);
  b.group(local, () => {
    if (frame) b.add(G.box(w + 0.14, h + 0.14, 0.07), frame, T(0, y, 0.035));
    if (tile) {
      const [cols, rows] = tile;
      const cw = w / cols;
      const chh = h / rows;
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          b.add(cellPlane(cw * 0.98, chh * 0.98, (i + j * 2) % 4, j % 2), M.art, T(-w / 2 + cw * (i + 0.5), y + h / 2 - chh * (j + 0.5), 0.08), { outline: false });
          b.line(V(-w / 2 + cw * i, y - h / 2, 0.09), V(-w / 2 + cw * i, y + h / 2, 0.09));
        }
      }
    } else {
      b.add(cellPlane(w, h, cell % 4, Math.floor(cell / 4) % 2), M.art, T(0, y, 0.08), { outline: false });
    }
    if (spot) {
      b.withLayer('context', () => {
        member(b, V(0, SHELL.h, 2.2), V(0, RIG_Y, 2.2), 0.04, M.rig);
        member(b, V(-0.9, RIG_Y, 2.2), V(0.9, RIG_Y, 2.2), 0.05, M.rig);
      });
      b.add(G.cyl(0.07, 0.09, 0.26, 10), M.rig, T(0, RIG_Y - 0.15, 2.2, 0, 0.6), { outline: false });
      b.add(G.cyl(0.06, 0.06, 0.02, 10), M.lamp, T(0, RIG_Y - 0.26, 2.12, 0, 0.6), { outline: false });
    }
  });
  if (spot) {
    spots.push({
      pos: V(0, RIG_Y - 0.3, 2.1).applyMatrix4(local),
      target: V(0, y, 0).applyMatrix4(local),
      w,
    });
  }
}

function stanchions(b, M, pts) {
  for (const [x, z] of pts) {
    b.add(G.cyl(0.18, 0.18, 0.03, 14), M.rig, T(x, 0.015, z), { outline: false });
    b.add(G.cyl(0.025, 0.025, 0.9, 6), M.rig, T(x, 0.47, z), { outline: false });
  }
}

function plinth(b, M, x, z, w, d, h = 0.3, ry = 0) {
  b.add(G.box(w, h, d), M.white, T(x, h / 2, z, ry));
}

// ── 입구 (외부 그래픽) ─────────────────────────────────────────
function entrance(b, M) {
  const z = 13.6;
  const H = 4.4;
  b.group(T(0, 0, z), () => {
    // 좌측 로고 패널
    b.add(slab([[-21.3, 0], [-17.9, 0], [-17.6, H], [-21.3, H]], 0.3), M.black);
    b.add(G.plane(3.3, 4.1), M.logo, T(-19.55, 2.3, 0.16), { outline: false });

    // 기울어진 포털 프레임
    const po = [[-17.5, 0], [-14.1, 0], [-13.7, H], [-17.1, H]];
    const hole = [[-17.0, 0.001], [-14.6, 0.001], [-14.3, 3.7], [-16.7, 3.7]];
    b.add(slab(po, 0.7, [hole]), M.white);
    b.add(G.box(2.6, 0.02, 0.7), M.maroon, T(-15.8, 0.01, 0), { outline: false });

    // 우측 포스터 패널 (사다리꼴)
    b.add(slab([[-13.6, 0], [-6.8, 0], [-6.8, H], [-13.2, H]], 0.3), M.black);
    b.add(G.plane(6.3, 4.0), M.poster, T(-10.05, 2.2, 0.16), { outline: false });

    // 안내 데스크
    b.group(T(-18.7, 0, 1.0), () => {
      b.add(G.box(1.1, 0.95, 0.65), M.maroon, T(0, 0.475, 0));
      b.add(G.box(1.1, 0.2, 0.65), M.white, T(0, 1.05, 0));
    });
  });
}

function intro(b, M, spots) {
  const z = 8.5;
  wall(b, M, -22.5, z, -9.6, z, { mat: M.grey });
  b.add(G.plane(12.8, 3.9), M.intro, T(-16.05, 2.1, z + 0.16), { outline: false });
  art(b, M, spots, -11.4, z + 0.15, 0, 1.0, 1.25, 4, { y: 2.0 });
  spots.push({ pos: V(-17, SHELL.h - 0.3, z + 4), target: V(-18.5, 2.2, z), w: 5 });
  stanchions(b, M, [[-19, z + 1.3], [-15, z + 1.3], [-12.5, z + 1.3]]);
}

function galleryA(b, M, spots) {
  // 좌측 네이비 벽, 안쪽 흰 벽, 우측 긴 흰 벽
  wall(b, M, -8, 0, -8, 11, { mat: M.navy });
  art(b, M, spots, -7.84, 5.2, PI / 2, 1.6, 2.0, 1);
  wall(b, M, -6, -2, 5, -2);
  art(b, M, spots, -0.5, -1.84, 0, 2.6, 1.7, 3);
  wall(b, M, 6, -2, 6, 11);
  art(b, M, spots, 5.84, 5.5, -PI / 2, 2.4, 3.0, 6, { y: 2.2 });
  art(b, M, spots, 5.84, 1.2, -PI / 2, 1.2, 1.6, 2, { spot: false });

  // 좌대: 조형물 박스 + 도자기
  plinth(b, M, 2.3, 4.8, 3.2, 1.5);
  b.add(G.box(0.8, 1.3, 0.8), M.art, T(1.5, 0.95, 4.8, 0.3));
  b.add(G.sphere(0.36, 16), M.vase, T(3.1, 0.62, 5.0, 0, 0, 0, 1, 1.15, 1), { outline: false });
  b.add(G.cyl(0.18, 0.2, 0.16, 16), M.vase, T(3.1, 1.02, 5.0), { outline: false });
  spots.push({ pos: V(2.3, RIG_Y, 7), target: V(2.3, 0.8, 4.8), w: 2 });
  stanchions(b, M, [[0.2, 6.3], [4.4, 6.3], [-3.5, 8.5], [-5.5, 3], [-2.5, 0]]);
}

function galleryB(b, M, spots) {
  wall(b, M, -17, -12.5, -6, -12.5, { mat: M.black, h: 4.6 });
  art(b, M, spots, -11.5, -12.34, 0, 2.6, 2.0, 5, { y: 2.1 });
  wall(b, M, -18, -12.5, -18, -3);
  art(b, M, spots, -17.84, -8, PI / 2, 2.0, 2.6, 7, { y: 2.2 });
  wall(b, M, -3, -12.5, -3, -3);
  art(b, M, spots, -3.16, -8, -PI / 2, 3.4, 1.3, 0, { frame: M.dark });

  // 좌대 위 이젤 작품
  plinth(b, M, -14.8, -5.2, 2.6, 1.6, 0.35);
  b.group(T(-14.8, 0.35, -5.2, 0.4), () => {
    const legs = [[-0.5, 0.35], [0.5, 0.35], [0, -0.45]];
    for (const [lx, lz] of legs) member(b, V(lx, 0, lz), V(0, 1.7, 0), 0.05, M.dark);
    b.add(cellPlane(1.1, 0.9, 1, 1), M.art, T(0, 1.2, 0.2, 0, -0.15), { outline: false });
    b.add(G.box(1.1, 0.9, 0.03), M.woodFrame, T(0, 1.2, 0.18, 0, -0.15));
  });
  spots.push({ pos: V(-14.8, RIG_Y, -2.5), target: V(-14.8, 1.2, -5.2), w: 1.5 });
  stanchions(b, M, [[-13, -3.8], [-9, -9.5], [-6, -9.5], [-5.5, -6]]);
}

/** 영상 복도: 대형 연작 + 낮은 좌대, 끝에 프로젝션 */
function corridor(b, M, spots) {
  const zN = -13.5;
  wall(b, M, 1, zN, 18.5, zN, { mat: M.black, h: 4.8 });
  art(b, M, spots, 9.2, zN + 0.16, 0, 13, 3.4, 0, { y: 2.4, frame: null, tile: [4, 2] });
  spots.push({ pos: V(4.5, RIG_Y, zN + 2.5), target: V(4.5, 2.4, zN), w: 4 });
  spots.push({ pos: V(14, RIG_Y, zN + 2.5), target: V(14, 2.4, zN), w: 4 });
  b.add(G.box(16, 0.22, 0.9), M.white, T(9.5, 0.11, zN + 0.8));

  wall(b, M, 4, -6.5, 10.5, -6.5);
  art(b, M, spots, 5.8, -6.66, PI, 1.1, 1.6, 2, { spot: false, frame: M.woodFrame });
  art(b, M, spots, 8.6, -6.66, PI, 2.0, 2.6, 7, { frame: M.woodFrame });

  // 프로젝션 벽
  wall(b, M, 19.5, zN, 19.5, -6.5, { mat: M.grey });
  b.add(G.plane(4.2, 2.4), M.projection, T(19.33, 2.1, -10.4, -PI / 2), { outline: false });
  b.add(G.box(0.03, 2.44, 4.24), null, T(19.34, 2.1, -10.4));
  stanchions(b, M, [[3, -9.5], [8, -8.5], [13, -9.5], [16, -8]]);
}

/** 미디어아트 룸 */
function mediaRoom(b, M) {
  const [x0, x1, z0, z1] = [11, 21, -4.5, 4];
  const opts = { mat: M.grey };
  wall(b, M, x0, z0, x1, z0, opts);
  wall(b, M, x1, z0, x1, z1, { ...opts, outlineOnly: true });
  wall(b, M, x0, z0, x0, -1.2, opts);
  wall(b, M, x0, 1.6, x0, z1, opts);
  wall(b, M, x0, z1, x1, z1, { ...opts, outlineOnly: true });
  b.add(G.box(10, 0.25, 0.3), M.skirting, T(16, 0.125, z1), { outline: false });
  b.add(G.box(0.3, 0.25, 8.5), M.skirting, T(x1, 0.125, 0), { outline: false });

  // 스크린 + 베젤
  b.add(G.box(3.9, 2.3, 0.12), M.dark, T(16, 2.05, z0 + 0.22));
  b.add(G.plane(3.7, 2.1), M.screen, T(16, 2.05, z0 + 0.29), { outline: false });
  // 프로젝터·CCTV
  b.add(G.box(0.3, 0.2, 0.4), M.dark, T(14.2, WALL_H + 0.1, z0 + 0.1));
}

/** 아트샵: 곡면 굿즈 벽 + 카운터 + 사진 월 */
function artShop(b, M) {
  // 곡면 벽 (앞면 텍스처를 구간별 UV로 이어 붙임)
  const n = 10;
  const x0 = 9.2;
  const x1 = 23.2;
  const curveZ = (x) => 6.2 + 1.4 * ((x - 16) / 7) ** 2;
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const x = x0 + ((x1 - x0) * i) / n;
    pts.push(V(x, 0, curveZ(x)));
  }
  const WH = 3.6;
  for (let i = 0; i < n; i++) {
    const a = pts[i];
    const c = pts[i + 1];
    const len = a.distanceTo(c);
    const ry = Math.atan2(-(c.z - a.z), c.x - a.x);
    const mx = (a.x + c.x) / 2;
    const mz = (a.z + c.z) / 2;
    b.add(G.box(len + 0.04, WH, 0.3), M.white, T(mx, WH / 2, mz, ry), { outline: false });
    b.add(cellPlane(len + 0.04, WH, i, 0, n, 1), M.shopWall, T(mx, WH / 2, mz, ry).multiply(T(0, 0, 0.16)), { outline: false });
    b.line(V(a.x, WH, a.z), V(c.x, WH, c.z));
    b.line(V(a.x, WH * 0.3, a.z + 0.17), V(c.x, WH * 0.3, c.z + 0.17));
  }
  b.line(V(x0, 0, pts[0].z), V(x0, WH, pts[0].z));
  b.line(V(x1, 0, pts[n].z), V(x1, WH, pts[n].z));

  // 카운터 (마룬 + 흰 상판)
  const counter = (x, z, w, d, ry = 0) => {
    b.group(T(x, 0, z, ry), () => {
      b.add(G.box(w, 0.85, d), M.maroon, T(0, 0.425, 0));
      b.add(G.box(w + 0.04, 0.08, d + 0.04), M.white, T(0, 0.89, 0));
    });
  };
  counter(10.8, 11.8, 1.1, 0.7);
  counter(12.6, 8.1, 2.8, 0.8, -0.05);
  counter(16.5, 11.2, 2.2, 1.0);
  // 옷걸이 랙
  b.group(T(19.6, 0, 9.4), () => {
    member(b, V(-0.8, 0, 0), V(-0.8, 1.6, 0), 0.04, M.rig);
    member(b, V(0.8, 0, 0), V(0.8, 1.6, 0), 0.04, M.rig);
    member(b, V(-0.8, 1.6, 0), V(0.8, 1.6, 0), 0.04, M.rig);
    for (let i = 0; i < 7; i++) b.add(G.box(0.05, 0.75, 0.5), M.black, T(-0.6 + i * 0.2, 1.15, 0), { outline: false });
  });

  // 사진 월 (샵 입구 쪽 가벽)
  wall(b, M, 8.2, 7, 8.2, 14, { h: 4 });
  b.add(G.plane(6.6, 3.8), M.photo, T(8.36, 2.05, 10.5, PI / 2), { outline: false });
}

function totem(b, M, x, z, ry) {
  b.group(T(x, 0, z, ry), () => {
    b.add(G.box(1.6, 0.06, 1.2), M.black, T(0, 0.03, 0));
    b.add(G.box(1.5, 3.0, 0.25), M.black, T(0, 1.56, 0));
    b.add(G.plane(1.4, 2.8), M.totem, T(0, 1.56, 0.13), { outline: false });
  });
}

// ── 조명 (실제 구현 모드에서만 켜짐) ─────────────────────────────
function addLights(root, spots) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    if (light.target) root.add(light.target);
    list.push({ light, base });
    return light;
  };

  add(new THREE.HemisphereLight('#aeb8cc', '#1a1612', 1), 0.28);
  // 로비·입구 쪽 넓은 빛
  const lobbyKey = add(new THREE.DirectionalLight('#f3f1ea', 1), 0.9);
  lobbyKey.position.set(-6, 20, 40);
  lobbyKey.target.position.set(-12, 0, 14);
  root.add(lobbyKey.target);

  // 작품 스포트라이트 (최대 12개)
  for (const s of spots.slice(0, 12)) {
    const l = new THREE.SpotLight('#ffe6c2', 1, 0, Math.min(0.55, 0.22 + s.w * 0.08), 0.6, 2);
    l.position.copy(s.pos);
    l.target.position.copy(s.target);
    add(l, 32);
  }

  // 아트샵은 밝게
  for (const [x, z] of [[12, 10.5], [19, 10]]) {
    const p = new THREE.PointLight('#fff4e6', 1, 0, 2);
    p.position.set(x, 4.6, z);
    add(p, 12);
  }

  // 미디어 스크린·프로젝션의 빛
  const screen = new THREE.RectAreaLight('#cfe0ff', 1, 3.7, 2.1);
  screen.position.set(16, 2.05, -4.2);
  screen.lookAt(16, 2.05, 10);
  add(screen, 2.5);
  const proj = new THREE.RectAreaLight('#b9e39a', 1, 4.2, 2.4);
  proj.position.set(19.3, 2.1, -10.4);
  proj.lookAt(0, 2.1, -10.4);
  add(proj, 5);

  for (const { light } of list) light.intensity = 0;
  return list;
}
