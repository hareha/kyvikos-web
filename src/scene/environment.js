import * as THREE from 'three';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

/** 밤하늘 돔: 와이어프레임에서는 거의 검정, 실제 구현에서는 지평선 빛 + 달 */
export function createSky() {
  const material = new THREE.ShaderMaterial({
    uniforms: {
      uBuilt: { value: 0 },
      uWire: { value: new THREE.Color('#03060c') },
      uZenith: { value: new THREE.Color('#02040b') },
      uHorizon: { value: new THREE.Color('#1b2644') },
      uMoonDir: { value: new THREE.Vector3(-0.45, 0.32, -0.83).normalize() },
      uMoonLimb: { value: new THREE.Vector3(1, 0, 0) },   // 밝은 가장자리 방향 (달 방향과 직교)
      uMoonK: { value: 0.58 },                            // 조명률 0~1
      uMoonR: { value: 0.030 },                           // 화면상 반지름(rad) — 아래 주석 참고
      uMoon: { value: 1 },
    },
    vertexShader: /* glsl */ `
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_Position = p.xyww;
      }`,
    fragmentShader: /* glsl */ `
      uniform float uBuilt;
      uniform vec3 uWire, uZenith, uHorizon, uMoonDir, uMoonLimb;
      uniform float uMoon, uMoonK, uMoonR;
      varying vec3 vDir;
      float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      void main() {
        vec3 dir = normalize(vDir);
        float h = clamp(dir.y, 0.0, 1.0);
        vec3 sky = mix(uHorizon, uZenith, pow(h, 0.45));

        // ── 달 ──────────────────────────────────────────────
        // 실제 겉보기 반지름은 0.258°(0.0045rad) 인데, 그대로 그리면 1080p 60° 화각에서
        // 지름 10px 짜리 점이라 아무것도 안 보인다. 사진·영화가 늘 그러듯 키워 그린다 —
        // uMoonR 기본 0.030rad(지름 3.4°, 실제의 약 6.7배). 위치·위상·기울기는 실측 그대로.
        // dot(dir, moon) 은 1 에 붙어 float 정밀도가 날아가므로 각거리를 **현(chord)** 으로 잰다.
        float R = uMoonR;
        vec3 off = dir - uMoonDir;
        float a = length(off);
        vec3 up2 = normalize(cross(uMoonDir, uMoonLimb));
        float px = dot(off, uMoonLimb) / R;      // 밝은 가장자리 쪽이 +
        float py = dot(off, up2) / R;
        float r = length(vec2(px, py));

        float disc = 1.0 - smoothstep(0.97, 1.04, r);
        // 위상: 명암경계선은 타원 x = (1-2k)·sqrt(1-y²)
        float term = (1.0 - 2.0 * uMoonK) * sqrt(max(0.0, 1.0 - py * py));
        float lit = smoothstep(-0.05, 0.05, px - term);
        float mu = sqrt(max(0.0, 1.0 - min(r, 1.0) * min(r, 1.0)));
        float ld = 0.74 + 0.26 * pow(mu, 0.45);                      // 가장자리 감광

        // 바다(어두운 현무암 평원) — 지구에서 보는 앞면 배치 그대로.
        // 전에는 본체를 1.9 로 띄워 놔서 톤매핑에서 전부 흰색으로 뭉개져 민 원으로 보였다.
        // 밝기를 1.08 로 내리고 바다 대비를 키워야 무늬가 산다.
        float sea = 1.0;
        sea -= 0.34 * (1.0 - smoothstep(0.180, 0.40, length(vec2(px + 0.30, py - 0.34))));  // 비의 바다
        sea -= 0.30 * (1.0 - smoothstep(0.117, 0.26, length(vec2(px - 0.04, py - 0.30))));  // 맑음의 바다
        sea -= 0.32 * (1.0 - smoothstep(0.135, 0.30, length(vec2(px - 0.22, py - 0.02))));  // 고요의 바다
        sea -= 0.26 * (1.0 - smoothstep(0.077, 0.17, length(vec2(px - 0.52, py + 0.16))));  // 풍요·감로
        sea -= 0.24 * (1.0 - smoothstep(0.059, 0.13, length(vec2(px - 0.62, py - 0.34))));  // 위난의 바다
        sea -= 0.34 * (1.0 - smoothstep(0.198, 0.44, length(vec2(px + 0.56, py + 0.06))));  // 폭풍의 대양
        sea -= 0.26 * (1.0 - smoothstep(0.117, 0.26, length(vec2(px + 0.26, py + 0.36))));  // 구름·습기의 바다
        sea = clamp(sea, 0.30, 1.0);
        // 잔 크레이터 얼룩 + 티코 광조
        float n = hash21(vec2(px, py) * 7.3) * 0.5 + hash21(vec2(py, px) * 19.7) * 0.5;
        sea *= 0.92 + 0.16 * n;
        float td = length(vec2(px + 0.10, py + 0.62));
        sea += 0.26 * (1.0 - smoothstep(0.0, 0.07, td))
             + 0.12 * max(0.0, 1.0 - abs(td - 0.32) / 0.32) * 0.5;

        // 본체 밝기 — 전에 1.9 로 띄워 놔서 톤매핑 어깨에서 전부 흰색으로 뭉개졌다.
        // 0.72 로 내리면 톤매핑 뒤 밝은 면이 0.56~0.91 로 퍼져 바다 무늬가 그대로 산다.
        vec3 body = vec3(0.72, 0.70, 0.655) * ld * sea * (lit + 0.030);  // 0.030 = 지구조(어두운 쪽)
        float halo = exp(-a / (R * 1.9)) * 0.16 + exp(-a / (R * 7.5)) * 0.035;   // 달무리
        sky += uMoon * (disc * body + halo * vec3(0.72, 0.78, 1.0));

        gl_FragColor = vec4(mix(uWire, sky, uBuilt), 1.0);
      }`,
    side: THREE.BackSide,
    depthWrite: false,
  });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(1000, 32, 16), material);
  mesh.frustumCulled = false;
  mesh.renderOrder = -1;
  return mesh;
}

/**
 * 환경광 맵: 하늘/바닥 색을 담은 그라데이션을 IBL로 구워
 * 금속·유리·젖은 바닥에 은은한 반사를 만든다.
 */
export function createEnvTexture(renderer, { zenith = '#02040b', horizon = '#1b2644', ground = '#0a0c12' } = {}) {
  const canvas = document.createElement('canvas');
  canvas.width = 16;
  canvas.height = 128;
  const g = canvas.getContext('2d');
  const grd = g.createLinearGradient(0, 0, 0, canvas.height);
  grd.addColorStop(0, zenith);
  grd.addColorStop(0.46, horizon);
  grd.addColorStop(0.54, ground);
  grd.addColorStop(1, '#000000');
  g.fillStyle = grd;
  g.fillRect(0, 0, canvas.width, canvas.height);

  const tex = new THREE.CanvasTexture(canvas);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;

  const pmrem = new THREE.PMREMGenerator(renderer);
  const target = pmrem.fromEquirectangular(tex);
  pmrem.dispose();
  tex.dispose();
  return target.texture;
}

/** 비네팅 + 미세한 필름 그레인 (사진처럼 보이게) */
export function createGrainPass() {
  return new ShaderPass({
    uniforms: {
      tDiffuse: { value: null },
      uTime: { value: 0 },
      uGrain: { value: 0 }, // 필름 그레인은 어두운 면에서 노이즈로 보여 끔
      uVignette: { value: 0.8 },
    },
    vertexShader: /* glsl */ `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */ `
      uniform sampler2D tDiffuse;
      uniform float uTime, uGrain, uVignette;
      varying vec2 vUv;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      void main() {
        vec4 c = texture2D(tDiffuse, vUv);
        float d = length(vUv - 0.5) * uVignette;
        c.rgb *= mix(1.0, 0.82, smoothstep(0.42, 0.9, d));
        c.rgb += (hash(vUv * 1024.0 + uTime) - 0.5) * uGrain;
        gl_FragColor = c;
      }`,
  });
}

export function createStars() {
  const n = 1800;
  const positions = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const u = Math.random() * Math.PI * 2;
    const y = 0.06 + Math.random() * 0.94;
    const r = Math.sqrt(1 - y * y);
    positions.set([Math.cos(u) * r * 900, y * 900, Math.sin(u) * r * 900], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const mat = new THREE.PointsMaterial({
    color: '#bcd3ff',
    size: 1.4,
    sizeAttenuation: false,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
    fog: false,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  return points;
}
