import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

/**
 * 공유 유니폼 — 월드 높이(m) 기준 전환선.
 * 이 높이 아래는 실제 구현(솔리드), 위는 와이어프레임으로 그려집니다.
 * -2 = 전부 와이어프레임, env.height + 4 = 전부 실제 구현.
 */
export const reveal = { value: -2 };

const SCAN_COLOR = 'vec3(0.45, 0.85, 1.0)';

/** 카메라의 matrixWorld — 뷰 좌표를 월드 좌표로 되돌릴 때 쓴다 (main.js가 매 프레임 갱신) */
export const viewInverse = { value: new THREE.Matrix4() };

/**
 * 솔리드 재질: 전환선 위쪽은 버리고, 전환선 부근은 스캔 라인처럼 빛나게.
 *
 * 표준 재질은 three가 이미 넘겨주는 vViewPosition 으로 월드 높이를 역산한다.
 * varying 을 새로 추가하면 GPU 한계(varying 개수)에 걸려 셰이더 링크가 실패하고
 * 화면이 전부 검게 나오는 기기가 있어서, 추가 varying 없이 처리한다.
 */
export function revealable(material) {
  const hasViewPosition = Boolean(material.isMeshStandardMaterial || material.isMeshPhysicalMaterial);
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uReveal = reveal;
    if (hasViewPosition) {
      shader.uniforms.uViewInv = viewInverse;
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform float uReveal;\nuniform mat4 uViewInv;')
        .replace(
          '#include <clipping_planes_fragment>',
          '#include <clipping_planes_fragment>\n\tfloat revealY = (uViewInv * vec4(-vViewPosition, 1.0)).y;\n\tif (revealY > uReveal) discard;',
        )
        .replace(
          '#include <dithering_fragment>',
          `#include <dithering_fragment>
\tfloat scan = 1.0 - smoothstep(0.0, 0.9, uReveal - revealY);
\tgl_FragColor.rgb += ${SCAN_COLOR} * scan * 1.6;`,
        );
      return;
    }
    // Basic/Points 등 vViewPosition 이 없는 재질만 월드 좌표를 따로 넘긴다
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vRevealPos;')
      .replace(
        '#include <project_vertex>',
        '#include <project_vertex>\n\tvRevealPos = (modelMatrix * vec4(transformed, 1.0)).xyz;',
      );
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uReveal;\nvarying vec3 vRevealPos;')
      .replace(
        '#include <clipping_planes_fragment>',
        '#include <clipping_planes_fragment>\n\tif (vRevealPos.y > uReveal) discard;',
      );
  };
  material.customProgramCacheKey = () => (hasViewPosition ? 'reveal-view' : 'reveal-world');
  return material;
}

/** 자주 쓰는 재질 생성기 */
export const std = (color, roughness = 0.8, metalness = 0, extra = {}) =>
  revealable(new THREE.MeshStandardMaterial({ color, roughness, metalness, ...extra }));

/** 발광 재질 (톤매핑 제외 → 블룸에 걸림). k > 1 이면 더 밝게 */
export const glow = (color, k = 1, extra = {}) =>
  revealable(new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k), toneMapped: false, ...extra }));

/** 와이어프레임 선 재질: 전환선 위쪽에서만 보이고, 멀어질수록 흐려짐 */
function lineMaterial(color, opacity) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uReveal: reveal,
      uColor: { value: new THREE.Color(color) },
      uOpacity: { value: opacity },
    },
    vertexShader: /* glsl */ `
      varying float vY;
      varying float vDepth;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vec4 mv = viewMatrix * wp;
        vY = wp.y;
        vDepth = -mv.z;
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */ `
      uniform float uReveal;
      uniform vec3 uColor;
      uniform float uOpacity;
      varying float vY;
      varying float vDepth;
      void main() {
        float wire = step(uReveal, vY);
        float band = 1.0 - smoothstep(0.0, 1.5, abs(vY - uReveal));
        float fade = 1.0 - smoothstep(180.0, 520.0, vDepth);
        float a = (uOpacity * wire + band) * fade;
        if (a < 0.002) discard;
        gl_FragColor = vec4(uColor * (1.0 + band * 1.5), clamp(a, 0.0, 1.0));
      }`,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
}

/** event: 큐비크스가 설치한 것(무대·전시물 등), context: 원래 있던 공간(건물·지형) */
export const lineMaterials = {
  event: lineMaterial('#86e6ff', 0.9),
  context: lineMaterial('#5d86b3', 0.34),
};

// ── 캔버스 텍스처 ─────────────────────────────────────────────
export const FONT = '"Pretendard Variable", Pretendard, "Helvetica Neue", Arial, sans-serif';

export function canvasTexture(w, h, draw) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

/** 결정적 난수 (매번 같은 배치가 나오도록) */
export function seeded(seed) {
  return () => (seed = (seed * 16807) % 2147483647) / 2147483647;
}

const rgba = (hex, a) => {
  const c = new THREE.Color(hex);
  return `rgba(${Math.round(c.r * 255)}, ${Math.round(c.g * 255)}, ${Math.round(c.b * 255)}, ${a})`;
};

/**
 * 얼룩덜룩한 표면 텍스처 — 잔디, 아스팔트, 석재처럼 단색이면 플라스틱처럼 보이는 면에 사용.
 * repeat 은 면 크기에 맞춰 넉넉히 준다.
 */
export function mottleTexture(base, variant, { size = 256, blobs = 260, alpha = 0.5, repeat = 1, seed = 3 } = {}) {
  const r = seeded(seed);
  const tex = canvasTexture(size, size, (g) => {
    g.fillStyle = base;
    g.fillRect(0, 0, size, size);
    for (let i = 0; i < blobs; i++) {
      const x = r() * size;
      const y = r() * size;
      const rad = size * (0.015 + r() * 0.07);
      const color = r() < 0.5 ? variant : base;
      const grd = g.createRadialGradient(x, y, 0, x, y, rad);
      grd.addColorStop(0, rgba(color, alpha * (0.35 + r() * 0.65)));
      grd.addColorStop(1, rgba(color, 0));
      g.fillStyle = grd;
      g.beginPath();
      g.arc(x, y, rad, 0, Math.PI * 2);
      g.fill();
    }
    for (let i = 0; i < size * size * 0.06; i++) {
      g.fillStyle = `rgba(0,0,0,${r() * 0.07})`;
      g.fillRect(r() * size, r() * size, 1, 1);
    }
  });
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeat, repeat);
  return tex;
}

// ── 지오메트리 ────────────────────────────────────────────────
const geoms = new Map();
const memo = (key, make) => {
  let g = geoms.get(key);
  if (!g) geoms.set(key, (g = make()));
  return g;
};

export const G = {
  box: (w, h, d) => memo(`box:${w}:${h}:${d}`, () => new THREE.BoxGeometry(w, h, d)),
  cyl: (rt, rb, h, seg = 24, open = false) =>
    memo(`cyl:${rt}:${rb}:${h}:${seg}:${open}`, () => new THREE.CylinderGeometry(rt, rb, h, seg, 1, open)),
  ico: (r, detail = 1) => memo(`ico:${r}:${detail}`, () => new THREE.IcosahedronGeometry(r, detail)),
  sphere: (r, seg = 12) => memo(`sph:${r}:${seg}`, () => new THREE.SphereGeometry(r, seg, Math.ceil(seg * 0.66))),
  plane: (w, h) => memo(`pl:${w}:${h}`, () => new THREE.PlaneGeometry(w, h)),
  torus: (r, tube, seg = 32) => memo(`tor:${r}:${tube}:${seg}`, () => new THREE.TorusGeometry(r, tube, 8, seg)),
  /** 한옥식 우진각 지붕: 오목한 곡면 + 추녀 끝 들림. 밑면(처마)이 y=0, 꼭대기가 y=h */
  roof: (hw, hd, h, opts = {}) => memo(`roof:${hw}:${hd}:${h}:${JSON.stringify(opts)}`, () => roofGeometry(hw, hd, h, opts)),
};

function roofGeometry(hw, hd, h, { ridge = 0.85, lift = h * 0.3, curve = 1.8, segU = 8, segT = 6 } = {}) {
  const tz = hd * (1 - ridge);
  const tx = Math.max(hw - hd * ridge, tz);
  const sides = [
    (a, rx, rz) => [a * rx, rz],
    (a, rx, rz) => [rx, -a * rz],
    (a, rx, rz) => [-a * rx, -rz],
    (a, rx, rz) => [-rx, a * rz],
  ];
  const pos = [];
  const uv = [];
  const idx = [];
  for (const side of sides) {
    const start = pos.length / 3;
    for (let j = 0; j <= segT; j++) {
      const t = j / segT;
      const rx = tx + (hw - tx) * t;
      const rz = tz + (hd - tz) * t;
      for (let i = 0; i <= segU; i++) {
        const a = (i / segU) * 2 - 1;
        const [x, z] = side(a, rx, rz);
        const y = h * Math.pow(1 - t, curve) + lift * t * t * t * Math.pow(Math.abs(a), 4);
        pos.push(x, y, z);
        uv.push(i / segU, t);
      }
    }
    const row = segU + 1;
    for (let j = 0; j < segT; j++) {
      for (let i = 0; i < segU; i++) {
        const v00 = start + j * row + i;
        const v10 = v00 + 1;
        const v01 = v00 + row;
        const v11 = v01 + 1;
        idx.push(v00, v01, v10, v10, v01, v11);
      }
    }
  }
  if (tz > 0.01) {
    const s = pos.length / 3;
    pos.push(-tx, h, -tz, tx, h, -tz, tx, h, tz, -tx, h, tz);
    uv.push(0, 0, 1, 0, 1, 1, 0, 1);
    idx.push(s, s + 3, s + 2, s, s + 2, s + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/** 원형으로 둘러싼 산 능선. 반환: { geometry, ridge: Vector3[] } */
export function mountainRing({ radius = 340, depth = 60, segments = 180, height = 40, base = -2, seed = 1 } = {}) {
  const r = seeded(seed);
  const ph = [r() * 6.28, r() * 6.28, r() * 6.28, r() * 6.28];
  const peak = (t) =>
    Math.max(
      4,
      height *
        (0.5 + 0.28 * Math.sin(2 * t + ph[0]) + 0.16 * Math.sin(5 * t + ph[1]) + 0.08 * Math.sin(13 * t + ph[2]) + 0.04 * Math.sin(29 * t + ph[3])),
    );
  const ridge = [];
  const bottom = [];
  for (let i = 0; i <= segments; i++) {
    const t = (i / segments) * Math.PI * 2;
    const c = Math.cos(t);
    const s = Math.sin(t);
    ridge.push(new THREE.Vector3(c * (radius + depth), peak(t), s * (radius + depth)));
    bottom.push(new THREE.Vector3(c * radius, base, s * radius));
  }
  const pos = [];
  const uv = [];
  for (let i = 0; i < segments; i++) {
    const [b0, b1, t0, t1] = [bottom[i], bottom[i + 1], ridge[i], ridge[i + 1]];
    pos.push(...b0.toArray(), ...b1.toArray(), ...t0.toArray(), ...t0.toArray(), ...b1.toArray(), ...t1.toArray());
    uv.push(0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geometry.computeVertexNormals();
  return { geometry, ridge };
}

// ── 변환 행렬 ─────────────────────────────────────────────────
const _p = new THREE.Vector3();
const _q = new THREE.Quaternion();
const _e = new THREE.Euler();
const _s = new THREE.Vector3();

/** 이동·회전(라디안)·스케일 */
export function T(x = 0, y = 0, z = 0, ry = 0, rx = 0, rz = 0, sx = 1, sy = 1, sz = 1) {
  return new THREE.Matrix4().compose(_p.set(x, y, z), _q.setFromEuler(_e.set(rx, ry, rz)), _s.set(sx, sy, sz));
}

/** 회전 → 스케일 → 이동 순서 (회전된 도형을 축 방향으로 늘릴 때) */
export function TSR(x, y, z, sx, sy, sz, ry) {
  return new THREE.Matrix4()
    .makeTranslation(x, y, z)
    .multiply(new THREE.Matrix4().makeScale(sx, sy, sz))
    .multiply(new THREE.Matrix4().makeRotationY(ry));
}

// ── Builder: 수천 개 오브젝트를 재질별로 병합해 드로우콜을 줄임 ──────
const IDENTITY = new THREE.Matrix4();
const flatCache = new WeakMap();
const edgeCache = new WeakMap();

function flat(geo) {
  let g = flatCache.get(geo);
  if (!g) {
    g = geo.index ? geo.toNonIndexed() : geo.clone();
    for (const name of Object.keys(g.attributes)) {
      if (!['position', 'normal', 'uv'].includes(name)) g.deleteAttribute(name);
    }
    flatCache.set(geo, g);
  }
  return g;
}

function edges(geo) {
  let e = edgeCache.get(geo);
  if (!e) edgeCache.set(geo, (e = new THREE.EdgesGeometry(geo, 28).attributes.position.array));
  return e;
}

/**
 * 월드 좌표 기준 박스 투영 UV. 삼각형마다 면 방향의 주축을 골라 투영하므로
 * 벽·바닥 크기와 상관없이 텍스처가 같은 밀도로 깔린다. tile = 텍스처 한 장의 크기(m).
 */
const _a = new THREE.Vector3();
const _b = new THREE.Vector3();
const _c = new THREE.Vector3();
const _n = new THREE.Vector3();
function worldUV(geometry, tile) {
  const pos = geometry.attributes.position;
  const uv = geometry.attributes.uv;
  for (let i = 0; i < pos.count; i += 3) {
    _a.fromBufferAttribute(pos, i);
    _b.fromBufferAttribute(pos, i + 1);
    _c.fromBufferAttribute(pos, i + 2);
    _n.subVectors(_c, _b).cross(_a.clone().sub(_b));
    const nx = Math.abs(_n.x);
    const ny = Math.abs(_n.y);
    const nz = Math.abs(_n.z);
    for (let k = 0; k < 3; k++) {
      const x = pos.getX(i + k);
      const y = pos.getY(i + k);
      const z = pos.getZ(i + k);
      if (ny >= nx && ny >= nz) uv.setXY(i + k, x / tile, z / tile);
      else if (nx >= nz) uv.setXY(i + k, z / tile, y / tile);
      else uv.setXY(i + k, x / tile, y / tile);
    }
  }
  uv.needsUpdate = true;
}

export class Builder {
  constructor() {
    this.stack = [new THREE.Matrix4()];
    this.solids = new Map();
    this.lines = { event: [], context: [] };
    this.layer = 'event';
  }

  get current() {
    return this.stack[this.stack.length - 1];
  }

  /** local 변환 안에서 fn 실행 (중첩 가능) */
  group(local, fn) {
    this.stack.push(this.current.clone().multiply(local));
    fn();
    this.stack.pop();
  }

  /** 'event' | 'context' 선 레이어로 fn 실행 */
  withLayer(layer, fn) {
    const prev = this.layer;
    this.layer = layer;
    fn();
    this.layer = prev;
  }

  /** 솔리드(mat) + 외곽선(outline). mat이 null이면 선만 */
  add(geo, mat, local = IDENTITY, { outline = true } = {}) {
    const world = this.current.clone().multiply(local);
    if (mat) {
      if (!this.solids.has(mat)) this.solids.set(mat, []);
      this.solids.get(mat).push([geo, world]);
    }
    if (outline) this.lines[this.layer].push([edges(geo), world]);
  }

  /** 선 하나 (현재 group 좌표계) */
  line(a, b) {
    this.lines[this.layer].push([new Float32Array([a.x, a.y, a.z, b.x, b.y, b.z]), this.current]);
  }

  /** 점 배열을 잇는 폴리라인 */
  polyline(points, closed = false) {
    for (let i = 0; i < points.length - 1; i++) this.line(points[i], points[i + 1]);
    if (closed) this.line(points[points.length - 1], points[0]);
  }

  build() {
    const root = new THREE.Group();
    for (const [mat, items] of this.solids) {
      const merged = mergeGeometries(items.map(([geo, world]) => flat(geo).clone().applyMatrix4(world)));
      if (mat.userData.worldUV) worldUV(merged, mat.userData.worldUV);
      root.add(new THREE.Mesh(merged, mat));
    }
    const v = new THREE.Vector3();
    for (const [layer, items] of Object.entries(this.lines)) {
      let count = 0;
      for (const [arr] of items) count += arr.length;
      if (!count) continue;
      const out = new Float32Array(count);
      let o = 0;
      for (const [arr, world] of items) {
        for (let i = 0; i < arr.length; i += 3, o += 3) v.fromArray(arr, i).applyMatrix4(world).toArray(out, o);
      }
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(out, 3));
      const segments = new THREE.LineSegments(g, lineMaterials[layer]);
      segments.frustumCulled = false;
      root.add(segments);
    }
    return root;
  }
}

// ── 선형 부재 / 트러스 ─────────────────────────────────────────
const UP = new THREE.Vector3(0, 1, 0);

/** a→c 를 잇는 가는 각재 (솔리드) + 중심선 (와이어) */
export function member(b, a, c, t, mat) {
  const d = new THREE.Vector3().subVectors(c, a);
  const len = d.length();
  const q = new THREE.Quaternion().setFromUnitVectors(UP, d.divideScalar(len));
  const m = new THREE.Matrix4().compose(a.clone().add(c).multiplyScalar(0.5), q, new THREE.Vector3(1, len, 1));
  b.add(G.box(t, 1, t), mat, m, { outline: false });
  b.line(a, c);
}

/** 사각 박스 트러스: 4개의 주재 + 면마다 지그재그 사재 */
export function truss(b, a, c, s, mat) {
  const d = new THREE.Vector3().subVectors(c, a);
  const len = d.length();
  d.normalize();
  const ref = Math.abs(d.y) > 0.9 ? new THREE.Vector3(1, 0, 0) : UP;
  const u = new THREE.Vector3().crossVectors(d, ref).normalize().multiplyScalar(s / 2);
  const v = new THREE.Vector3().crossVectors(u, d).normalize().multiplyScalar(s / 2);
  const corners = [u.clone().add(v), u.clone().sub(v), u.clone().negate().sub(v), u.clone().negate().add(v)];
  for (const k of corners) member(b, a.clone().add(k), c.clone().add(k), 0.05, mat);

  const bays = Math.max(1, Math.round(len / (s * 1.5)));
  for (let i = 0; i < bays; i++) {
    const p0 = a.clone().addScaledVector(d, (len * i) / bays);
    const p1 = a.clone().addScaledVector(d, (len * (i + 1)) / bays);
    for (let k = 0; k < 4; k++) {
      const [s0, s1] = i % 2 ? [corners[k], corners[(k + 1) % 4]] : [corners[(k + 1) % 4], corners[k]];
      member(b, p0.clone().add(s0), p1.clone().add(s1), 0.025, mat);
    }
  }
}

/** 원기둥 조명 빔 (from=광원, to=바닥) */
export function beam(b, from, to, mat, radius = 1.4) {
  const d = new THREE.Vector3().subVectors(from, to);
  const len = d.length();
  const q = new THREE.Quaternion().setFromUnitVectors(UP, d.normalize());
  const m = new THREE.Matrix4().compose(from.clone().add(to).multiplyScalar(0.5), q, new THREE.Vector3(1, len, 1));
  b.add(G.cyl(0.12, radius, 1, 20, true), mat, m, { outline: false });
}

/** 씬 해제 (씬 전환 시 GPU 메모리 반환) */
export function disposeTree(root) {
  const mats = new Set();
  root.traverse((o) => {
    o.geometry?.dispose();
    if (o.material) [].concat(o.material).forEach((m) => mats.add(m));
    if (o.isLight) o.dispose?.();
  });
  for (const m of mats) {
    for (const value of Object.values(m)) if (value?.isTexture) value.dispose();
    m.dispose();
  }
}
