import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { Builder, G, T, canvasTexture, reveal, revealable } from '../../scene/kit.js';
import { pbr } from '../../scene/assets.js';
import { loadBakedScene } from '../../scene/baked.js';
import { plateGrid, plateOutline, sitePlate } from '../../scene/plate.js';

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
    b.polyline(plateOutline(PLATE, 0.02));
    for (const line of plateGrid(PLATE, 5, 0.02)) b.polyline(line);
  });

  const root = b.build();
  root.add(sitePlate(PLATE));
  const lights = addLights(root);

  // Blender 에서 베이크한 만찬장·황룡원 시설·수목
  loadBakedScene(root, 'apec_stage', { context: ['ground', 'pagoda', 'halls', 'garden', 'yeonsu_ne', 'yeonsu_nw', 'pines', 'lanterns'] }).catch((error) =>
    console.warn('[kyvikos] 베이크 장면 로드 실패', error),
  );
  return { root, lights };
}

// ── 부지 받침판 (src/scene/plate.js) ─────────────────────────────
export const PLATE = { x0: -84, x1: 94, z0: -66, z1: 70, r: 10, depth: 2.4 };

// ── 실시간 광원 (베이크되지 않은 트러스·의자·유리·주변부용) ─────────
function addLights(root) {
  const list = [];
  const add = (light, base) => {
    root.add(light);
    if (light.target) root.add(light.target);
    list.push({ light, base });
    return light;
  };

  add(new THREE.HemisphereLight('#6d7896', '#1b160c', 1), 0.3);
  add(new THREE.DirectionalLight('#a9bbff', 1), 0.15).position.set(-80, 120, 60);

  const spot = (pos, target, base, color = '#ffe2b0', angle = 0.55, dist = 0) => {
    const l = new THREE.SpotLight(color, 1, dist, angle, 0.7, 2);
    l.position.set(...pos);
    l.target.position.set(...target);
    add(l, base);
  };
  // Blender 장면과 같은 위치·색의 노란 투광
  spot([40, 19, -4], [4, 0, -2], 5200, '#ffc27a');
  spot([22, 19, 17], [0, 0, 0], 3800, '#ffc680');
  spot([6, 8.2, -15], [6, 1.2, -15], 900, '#d8e4ff', 0.9);
  // 무대 정면 키라이트 1대. distance 를 무대 깊이로 끊어 **객석 식기·금속까지 닿지 않게** 한다.
  spot([6, 7.6, -10.4], [6, 0.7, -16.5], 1400, '#ffe9c4', 0.52, 14);

  const led = new THREE.RectAreaLight('#4a78ff', 1, 14.4, 6.2);
  led.position.set(6, 4.3, -19.6);
  led.lookAt(6, 4.3, 0);
  add(led, 8);

  list.push(stageBeams(root));
  for (const { light } of list) light.intensity = 0;
  return list;
}

// ── 무대 조명 ──────────────────────────────────────────────────────
// 기구 26 대에 실제 광원을 26 개 거는 건 틀린 방법이다. (1) 전방 렌더러는 재질
// 셰이더마다 광원 전체를 순회하므로 눈에 띄게 느려지고, (2) 그 빛이 무대와 무관한
// 테이블 식기·금속에까지 반사되어 전부 번쩍인다.
// 야경 사진에서 실제로 보이는 건 **빛줄기와 바닥 광반**이므로, 그 둘을 가산혼합
// 지오메트리로 그린다. 드로우콜 2 개, 광원 0 개.
//   apec_stage.py: X0 -5.2 / X1 17.2 / ZF -10.6 / HT 7.5 / LT 5.95 / CX 6 / TOP 0.55
const BEAM_V = `
attribute float fade;
attribute vec3 beamColor;
varying float vFade;
varying vec3 vColor;
varying vec3 vNrm;
varying float vY;
void main() {
  vFade = fade;
  vColor = beamColor;
  vNrm = normalize(normalMatrix * normal);
  vec4 world = modelMatrix * vec4(position, 1.0);
  vY = world.y;
  gl_Position = projectionMatrix * viewMatrix * world;
}`;

const BEAM_F = `
uniform float uOpacity;
uniform float uReveal;
varying float vFade;
varying vec3 vColor;
varying vec3 vNrm;
varying float vY;
void main() {
  if (vY > uReveal) discard;
  // 원뿔 가운데(법선이 카메라를 향하는 쪽)를 지날 때 시선이 가장 긴 거리를
  // 통과하므로 그만큼 밝다. 실루엣 쪽은 옅어져 테두리 선이 생기지 않는다.
  float a = pow(abs(vNrm.z), 1.7);
  a *= 1.0 - vFade * 0.88;                     // 기구에서 멀어질수록 옅게
  gl_FragColor = vec4(vColor, a * uOpacity);
}`;

function beamGeometry(from, to, r0, r1, color, segs = 12) {
  const a = new THREE.Vector3(...from);
  const dir = new THREE.Vector3(...to).sub(a);
  const len = dir.length();
  const g = new THREE.CylinderGeometry(r0, r1, len, segs, 1, true);
  const pos = g.attributes.position;
  const fade = new Float32Array(pos.count);
  const col = new Float32Array(pos.count * 3);
  const c = new THREE.Color(color);
  for (let i = 0; i < pos.count; i += 1) {
    fade[i] = (len / 2 - pos.getY(i)) / len;    // 기구 쪽(+y) 0 → 바닥 1
    col[i * 3] = c.r;
    col[i * 3 + 1] = c.g;
    col[i * 3 + 2] = c.b;
  }
  g.setAttribute('fade', new THREE.BufferAttribute(fade, 1));
  g.setAttribute('beamColor', new THREE.BufferAttribute(col, 3));
  g.applyMatrix4(new THREE.Matrix4().compose(
    a.clone().addScaledVector(dir, 0.5),
    new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, -1, 0), dir.clone().normalize()),
    new THREE.Vector3(1, 1, 1),
  ));
  return g;
}

function stageBeams(root) {
  const beams = [];
  const pools = [];
  const pool = (x, z, r) => {
    const g = G.plane(r * 2, r * 2.4).clone();
    g.applyMatrix4(new THREE.Matrix4().makeRotationX(-PI / 2));
    g.applyMatrix4(new THREE.Matrix4().makeTranslation(x, 0.03, z));
    pools.push(g);
  };

  for (let i = 0; i < 12; i += 1) {                         // 지붕 트러스 위 흰 블라인더
    // 객석을 정면으로 쏘는 기구라 빛줄기가 카메라를 그대로 향한다. 길고 밝게 그리면
    // 화면 전체가 흰 덩어리로 뭉개지므로, **짧고 어둡게** 기구 앞 번짐만 남긴다.
    const lx = -3.8 + (i * 19.6) / 11;
    const o = new THREE.Vector3(lx, 7.84, -10.35);
    const d = new THREE.Vector3(1.2 - lx * 0.2, -7.84, 18.35).normalize();
    beams.push(beamGeometry(o.toArray(), o.clone().addScaledVector(d, 3.2).toArray(), 0.15, 0.62, '#2e2415'));
  }
  for (let i = 0; i < 14; i += 1) {                         // 그 아래 파란 무빙헤드 (apec_stage.py 와 같은 식)
    const lx = -4.1 + (i * 20.2) / 13;
    const t = (i - 6.5) / 6.5;
    const yoke = new THREE.Vector3(lx, 5.67, -10.4);
    const tgt = new THREE.Vector3(6 + t * 13, 0.1, -4.5 + Math.abs(t) * 3);
    const d = tgt.clone().sub(yoke).normalize();
    beams.push(beamGeometry(yoke.clone().addScaledVector(d, 0.54).toArray(), tgt.toArray(), 0.075, 0.52, '#2f55b4'));
    pool(tgt.x, tgt.z, 0.95);
  }

  const mat = new THREE.ShaderMaterial({
    uniforms: { uOpacity: { value: 0 }, uReveal: reveal },
    vertexShader: BEAM_V,
    fragmentShader: BEAM_F,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const cones = new THREE.Mesh(mergeGeometries(beams, false), mat);
  cones.frustumCulled = false;
  root.add(cones);

  const poolTex = canvasTexture(128, 128, (ctx) => {
    const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.3, 'rgba(255,255,255,0.4)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 128, 128);
  });
  const poolMat = revealable(new THREE.MeshBasicMaterial({
    map: poolTex,
    color: '#2b4fa8',
    toneMapped: false,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    opacity: 0,
  }));
  root.add(new THREE.Mesh(mergeGeometries(pools, false), poolMat));

  // 전환(reveal) 진행도에 맞춰 같이 밝아지도록 light 목록에 끼워 넣는다
  return {
    base: 1,
    light: {
      set intensity(v) {
        mat.uniforms.uOpacity.value = v;
        poolMat.opacity = v * 0.85;
      },
    },
  };
}
