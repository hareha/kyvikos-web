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
      uniform vec3 uWire, uZenith, uHorizon, uMoonDir;
      uniform float uMoon;
      varying vec3 vDir;
      void main() {
        vec3 dir = normalize(vDir);
        float h = clamp(dir.y, 0.0, 1.0);
        vec3 sky = mix(uHorizon, uZenith, pow(h, 0.45));
        float md = max(dot(dir, uMoonDir), 0.0);
        sky += uMoon * (smoothstep(0.9992, 0.9995, md) * vec3(1.7, 1.65, 1.5) + pow(md, 300.0) * vec3(0.22, 0.26, 0.36));
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
      uGrain: { value: 0.03 },
      uVignette: { value: 1 },
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
        c.rgb *= mix(1.0, 0.68, smoothstep(0.35, 0.82, d));
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
