import './style.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import gsap from 'gsap';
import { reveal, disposeTree, std, viewInverse } from './scene/kit.js';
import { createSky, createStars, createEnvTexture, createGrainPass } from './scene/environment.js';
import { loadHdri, whenAssetsLoaded } from './scene/assets.js';
import { venues } from './venues/registry.js';
import { initSite, isSectionHash } from './site.js';

RectAreaLightUniformsLib.init();

const REVEAL_WIRE = -2;
const WIRE_BG = new THREE.Color('#03060c');
const ENV_DEFAULTS = { height: 30, sky: null, stars: false, builtBg: '#0a0c12', fog: 0.003, exposure: 1 };
const { clamp, lerp, smoothstep } = THREE.MathUtils;

const $ = (s) => document.querySelector(s);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const state = { mode: 'wire', view: null, flying: false, cardSource: null, loading: false };
/** 현재 공간: { id, project, views, viewById, env, root, lights, builtBg } */
let venue = null;

const builtLevel = () => venue.env.height + 4;
const imageUrl = (name) => `${import.meta.env.BASE_URL}images/${venue.id}/${name}.jpg`;

// ── 렌더러 / 씬 ───────────────────────────────────────────────
const canvas = $('#scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
const MOBILE = window.innerWidth < 768;
/** ?safe=1 — 후처리·환경광을 모두 끄는 최소 그래픽 모드 (호환성 문제 진단·회피용) */
const SAFE_MODE = new URLSearchParams(location.search).has('safe');
renderer.setPixelRatio(Math.min(window.devicePixelRatio, MOBILE ? 1.5 : 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
// 그림자는 기본 비활성. 일부 GPU에서 그림자를 켜면 셰이더가 한계에 걸려
// 벽·바닥 같은 일반 재질이 전부 검게 렌더링되는 문제가 있었다.
renderer.shadowMap.enabled = false;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
// 장면이 정지해 있으므로 그림자는 필요할 때 한 번만 굽는다
renderer.shadowMap.autoUpdate = false;

/** 캔버스는 '3D 투어' 섹션 안에 들어 있으므로 창이 아니라 캔버스 크기에 맞춘다 */
const stageSize = () => ({
  w: canvas.clientWidth || window.innerWidth,
  h: canvas.clientHeight || window.innerHeight,
});

const scene = new THREE.Scene();
scene.background = WIRE_BG.clone();
scene.fog = new THREE.FogExp2('#000000', 0);

const camera = new THREE.PerspectiveCamera(42, stageSize().w / stageSize().h, 0.1, 3000);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.autoRotateSpeed = 0.35;
controls.enabled = false;
// 휠은 페이지 스크롤에 양보하고, 세로 스와이프도 페이지가 가져간다
controls.enableZoom = false;
canvas.style.touchAction = 'pan-y';

// MSAA(멀티샘플) 렌더 타깃 — 후처리를 쓰면 기본 안티에일리어싱이 꺼지므로 직접 지정
const composer = new EffectComposer(
  renderer,
  new THREE.WebGLRenderTarget(stageSize().w, stageSize().h, {
    type: THREE.HalfFloatType,
    samples: MOBILE ? 0 : 4,
  }),
);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(stageSize().w / 2, stageSize().h / 2), 0.55, 0.3, 0.55);
composer.addPass(bloom);
const grain = createGrainPass();
composer.addPass(grain);
composer.addPass(new OutputPass());

const sky = createSky();
scene.add(sky);
const stars = createStars();
scene.add(stars);

const grid = new THREE.GridHelper(600, 150, '#2a5a86', '#16324d');
grid.material.transparent = true;
grid.material.depthWrite = false;
grid.position.y = 0.01;
scene.add(grid);

// ── 공간 불러오기 ─────────────────────────────────────────────
async function loadVenue(id) {
  const entry = venues.find((v) => v.id === id) ?? venues[0];
  if (state.loading || venue?.id === entry.id) return;
  state.loading = true;

  const loader = $('#loader');
  loader.classList.remove('done');
  flight?.kill();
  state.flying = false;
  controls.enabled = false;
  hideCard();
  hint.classList.remove('show');

  const [mod] = await Promise.all([entry.load(), wait(venue ? 650 : 0)]);
  if (venue) {
    scene.remove(venue.root);
    disposeTree(venue.root);
  }

  const { root, lights } = mod.build();
  scene.add(root);
  const env = { ...ENV_DEFAULTS, ...mod.env };
  if (!env.sky) {
    // 실내 공간은 스포트라이트 위주라 벽·천장·바닥이 검게 죽는다. 부드러운 채움광을 더한다.
    const fill = new THREE.AmbientLight('#b9c6dd', 1);
    root.add(fill);
    lights.push({ light: fill, base: env.fill ?? 2 });
    addGroundPlane(root);
  }
  venue = {
    id: entry.id,
    project: mod.project,
    views: mod.views,
    viewById: Object.fromEntries(mod.views.map((v) => [v.id, v])),
    env,
    root,
    lights,
    builtBg: new THREE.Color(env.builtBg),
  };
  applyEnv(env);
  setupShadows(root, lights, env);
  gsap.killTweensOf(reveal);
  reveal.value = state.mode === 'built' ? builtLevel() : REVEAL_WIRE;
  applyRevealState();

  renderProject();
  renderViews();
  buildHotspots();
  if (location.hash.slice(1) !== entry.id) history.replaceState(null, '', `#${entry.id}`);

  // 개요 시점보다 멀리서 시작해 날아 들어오기
  const overview = venue.views[0];
  const target = new THREE.Vector3(...overview.target);
  camera.position.set(...overview.pos).sub(target).multiplyScalar(1.9).add(target);
  camera.lookAt(target);
  camera.fov = overview.fov;
  camera.updateProjectionMatrix();
  state.view = null;

  // 텍스처·모델이 도착한 뒤에 보여준다 (그 전에는 재질이 검게 그려짐)
  await whenAssetsLoaded();
  loader.classList.add('done');
  state.loading = false;
  goTo(overview.id, { duration: 3.2 });
}

/** 실내 공간이 허공에 떠 보이지 않도록 건물 바깥까지 깔리는 바닥 */
function addGroundPlane(root) {
  const box = new THREE.Box3().setFromObject(root);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(Math.max(size.x, size.z) * 3, Math.max(size.x, size.z) * 3),
    std('#101318', 1),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(center.x, box.min.y - 0.35, center.z);
  ground.receiveShadow = true;
  root.add(ground);
}

function applyEnv(env) {
  sky.visible = Boolean(env.sky);
  if (env.sky) {
    const u = sky.material.uniforms;
    u.uZenith.value.set(env.sky.zenith);
    u.uHorizon.value.set(env.sky.horizon);
    u.uMoon.value = env.sky.moon ? 1 : 0;
    if (env.sky.moon) u.uMoonDir.value.set(...env.sky.moon).normalize();
    scene.fog.color.set(env.sky.horizon);
  } else {
    scene.fog.color.set(env.builtBg);
  }
  stars.visible = env.stars;
  renderer.toneMappingExposure = env.exposure;
  // Blender 에서 베이크한 공간은 Blender 와 같은 AgX 톤매핑으로 맞춘다
  renderer.toneMapping = env.toneMapping === 'agx' ? THREE.AgXToneMapping : THREE.ACESFilmicToneMapping;

  gradientEnv?.dispose();
  gradientEnv = null;
  scene.environment = null;
  scene.environmentIntensity = 0;
  if (SAFE_MODE) return;

  // 우선 그라데이션 환경광을 쓰고, HDRI가 있으면 로드되는 대로 교체한다
  gradientEnv = createEnvTexture(
    renderer,
    env.sky
      ? { zenith: env.sky.zenith, horizon: env.sky.horizon }
      : // 실내: 천장에서 바닥으로 떨어지는 중성 회색 — 벽면이 검게 죽지 않게 한다
        { zenith: '#4a5464', horizon: '#333b47', ground: '#171a20' },
  );
  scene.environment = gradientEnv;
  if (env.hdri) {
    loadHdri(renderer, env.hdri)
      .then((texture) => {
        if (venue?.env === env) scene.environment = texture;
      })
      .catch((error) => console.warn('[kyvikos] HDRI 로드 실패', error));
  }
}
let gradientEnv = null;

/** 정지된 장면이라 그림자는 '실제 구현'이 완성된 순간 한 번만 굽는다 */
let shadowsBaked = false;
function setupShadows(root, lights, env) {
  shadowsBaked = false;
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true;
    o.receiveShadow = true;
  });

  const radius = env.shadowRadius ?? Math.max(24, env.height * 0.9);
  // 그림자는 주광(디렉셔널) 1개만. 여러 개를 켜면 일부 GPU에서 셰이더 한계에 걸려
  // 표면이 전부 검게 렌더링되는 문제가 있어 보수적으로 제한한다.
  for (const { light } of lights) {
    if (light.isDirectionalLight && renderer.shadowMap.enabled) {
      light.castShadow = true;
      light.shadow.mapSize.set(2048, 2048);
      light.shadow.bias = -0.0006;
      light.shadow.normalBias = 0.05;
      const c = light.shadow.camera;
      Object.assign(c, { left: -radius, right: radius, top: radius, bottom: -radius, near: 1, far: radius * 8 });
      c.updateProjectionMatrix();
    } else if (light.shadow) {
      light.castShadow = false;
    }
  }
}

// ── 카메라 이동 ───────────────────────────────────────────────
const lookCam = new THREE.PerspectiveCamera();
let flight = null;

function goTo(id, { duration } = {}) {
  const view = venue.viewById[id];
  state.view = id;
  state.flying = true;
  controls.enabled = false;
  controls.autoRotate = false;
  hideCard();
  updateChips();

  const fromPos = camera.position.clone();
  const fromQuat = camera.quaternion.clone();
  const fromFov = camera.fov;
  const toPos = new THREE.Vector3(...view.pos);
  lookCam.position.copy(toPos);
  lookCam.lookAt(...view.target);
  const toQuat = lookCam.quaternion.clone();

  const dist = fromPos.distanceTo(toPos);
  const arc = Math.min(18, dist * 0.2);
  const p = { k: 0 };

  flight?.kill();
  flight = gsap.to(p, {
    k: 1,
    duration: duration ?? clamp(1.2 + dist / 50, 1.4, 3.2),
    ease: 'power2.inOut',
    onUpdate: () => {
      camera.position.lerpVectors(fromPos, toPos, p.k);
      camera.position.y += Math.sin(Math.PI * p.k) * arc;
      camera.quaternion.slerpQuaternions(fromQuat, toQuat, p.k);
      camera.fov = lerp(fromFov, view.fov, p.k);
      camera.updateProjectionMatrix();
    },
    onComplete: () => {
      state.flying = false;
      settle(view);
      showCard(view);
    },
  });
}

/** 도착 후 컨트롤 설정: 궤도 시점은 대상 주위 회전, 1인칭 시점은 제자리 둘러보기 */
function settle(view) {
  const dir = camera.getWorldDirection(new THREE.Vector3());
  if (view.orbit) {
    controls.target.set(...view.target);
    Object.assign(controls, {
      enablePan: true,
      rotateSpeed: 0.55,
      minDistance: 4,
      maxDistance: 260,
      minPolarAngle: 0.05,
      maxPolarAngle: Math.PI * 0.47,
    });
  } else {
    controls.target.copy(camera.position).addScaledVector(dir, 0.05);
    Object.assign(controls, {
      enablePan: false,
      rotateSpeed: -0.28,
      minDistance: 0.05,
      maxDistance: 0.05,
      minPolarAngle: Math.PI * 0.2,
      maxPolarAngle: Math.PI * 0.75,
    });
  }
  controls.autoRotate = view.id === 'overview';
  controls.enabled = true;
  controls.update();
}

// ── 모드 전환 ─────────────────────────────────────────────────
function setMode(mode) {
  if (state.mode === mode) return;
  state.mode = mode;
  state.cardSource = null;
  document.body.dataset.mode = mode;
  document.querySelectorAll('.mode button').forEach((btn) => {
    btn.setAttribute('aria-pressed', String(btn.dataset.mode === mode));
  });
  if (venue) {
    gsap.to(reveal, {
      value: mode === 'built' ? builtLevel() : REVEAL_WIRE,
      duration: mode === 'built' ? 3 : 2,
      ease: mode === 'built' ? 'power1.inOut' : 'power2.inOut',
      overwrite: true,
      // 렌더 루프와 별개로 조명·배경을 따라가게 한다
      onUpdate: applyRevealState,
      onComplete: applyRevealState,
    });
  }
  refreshCard();
}

/** 확대 / 축소 — 궤도 시점은 거리로, 1인칭 시점은 화각으로 */
function zoom(direction) {
  const view = venue?.viewById[state.view];
  if (!view || state.flying) return;
  if (view.orbit) {
    const offset = camera.position.clone().sub(controls.target);
    const distance = clamp(offset.length() * (direction > 0 ? 0.78 : 1.28), controls.minDistance, controls.maxDistance);
    const to = controls.target.clone().add(offset.setLength(distance));
    gsap.to(camera.position, { x: to.x, y: to.y, z: to.z, duration: 0.5, ease: 'power2.out', overwrite: true });
  } else {
    gsap.to(camera, {
      fov: clamp(camera.fov + (direction > 0 ? -8 : 8), 24, 78),
      duration: 0.45,
      ease: 'power2.out',
      overwrite: true,
      onUpdate: () => camera.updateProjectionMatrix(),
    });
  }
}

// ── UI ──────────────────────────────────────────────────────
const hint = $('#hint');
const card = $('#card');
const cardImg = card.querySelector('img');

function renderProject() {
  const { project } = venue;
  $('#project-eyebrow').textContent = project.eyebrow;
  $('#project-title').innerHTML = project.title;
  $('#project-meta').innerHTML = project.meta.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
  $('#project-tech').innerHTML = project.tech;
  $('#venues').innerHTML = venues
    .map((v) => `<button data-venue="${v.id}" class="${v.id === venue.id ? 'active' : ''}">${v.label}</button>`)
    .join('');
}

function renderViews() {
  $('#views').innerHTML = venue.views.map((v) => `<button data-view="${v.id}">${v.label}</button>`).join('');
}

function updateChips() {
  document.querySelectorAll('#views button').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === state.view);
  });
}

let hotspots = [];

function buildHotspots() {
  $('#hotspots').replaceChildren();
  hotspots = venue.views
    .filter((v) => v.anchor)
    .map((view) => {
      const el = document.createElement('button');
      el.className = 'hotspot is-hidden';
      el.innerHTML = `<span class="hs-dot"></span><span class="hs-label">${view.label}</span>`;
      el.addEventListener('click', () => goTo(view.id));
      $('#hotspots').append(el);
      return { view, el, world: new THREE.Vector3(...view.anchor) };
    });
}

const projected = new THREE.Vector3();
function updateHotspots() {
  const { w, h } = stageSize();
  for (const hs of hotspots) {
    projected.copy(hs.world).project(camera);
    const visible =
      !state.flying &&
      hs.view.id !== state.view &&
      projected.z < 1 &&
      Math.abs(projected.x) < 1.02 &&
      Math.abs(projected.y) < 1.02 &&
      camera.position.distanceTo(hs.world) > 3;
    hs.el.classList.toggle('is-hidden', !visible);
    if (visible) {
      hs.el.style.transform = `translate3d(${(projected.x * 0.5 + 0.5) * w}px, ${(-projected.y * 0.5 + 0.5) * h}px, 0)`;
    }
  }
}

function showCard(view) {
  if (!view.sim && !view.real) return;
  card.querySelector('.card-title').textContent = view.label;
  card.querySelector('.card-desc').textContent = view.desc ?? '';
  state.cardSource = null;
  refreshCard();
  card.hidden = false;
  requestAnimationFrame(() => card.classList.add('show'));
}

function hideCard() {
  card.classList.remove('show');
  card.hidden = true;
}

function refreshCard() {
  const view = venue?.viewById[state.view];
  if (!view || (!view.sim && !view.real)) return;
  const preferred = state.mode === 'built' ? 'real' : 'sim';
  const source = state.cardSource ?? (view[preferred] ? preferred : preferred === 'real' ? 'sim' : 'real');
  const src = imageUrl(view[source]);
  if (cardImg.getAttribute('src') !== src) cardImg.src = src;
  card.querySelectorAll('.card-tabs button').forEach((btn) => {
    btn.disabled = !view[btn.dataset.source];
    btn.classList.toggle('active', btn.dataset.source === source);
  });
}

function initUi() {
  const panel = $('#project');
  const toggle = panel.querySelector('.project-toggle');
  const setOpen = (open) => {
    panel.classList.toggle('collapsed', !open);
    toggle.setAttribute('aria-expanded', String(open));
  };
  setOpen(window.innerWidth > 1100);
  toggle.addEventListener('click', () => setOpen(panel.classList.contains('collapsed')));

  $('#venues').addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-venue]');
    if (btn) loadVenue(btn.dataset.venue);
  });
  $('#views').addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-view]');
    if (btn && venue && !state.loading) goTo(btn.dataset.view);
  });
  document.querySelectorAll('.mode button').forEach((btn) => {
    btn.addEventListener('click', () => setMode(btn.dataset.mode));
  });
  $('.zoom').addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-zoom]');
    if (btn) zoom(btn.dataset.zoom === 'in' ? 1 : -1);
  });

  card.querySelector('.card-tabs').addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn || btn.disabled) return;
    e.stopPropagation();
    state.cardSource = btn.dataset.source;
    refreshCard();
  });
  card.querySelector('.card-close').addEventListener('click', hideCard);
  card.querySelector('.card-media').addEventListener('click', () => {
    const lb = $('#lightbox');
    lb.querySelector('img').src = cardImg.src;
    lb.hidden = false;
  });
  $('#lightbox').addEventListener('click', (e) => {
    e.currentTarget.hidden = true;
  });

  controls.addEventListener('start', () => {
    controls.autoRotate = false;
    hint.classList.remove('show');
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') $('#lightbox').hidden = true;
  });
  window.addEventListener('hashchange', () => {
    const hash = location.hash.slice(1);
    if (!isSectionHash(hash)) loadVenue(hash);
  });
  const resize = () => {
    const { w, h } = stageSize();
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
    composer.setSize(w, h);
  };
  resize();
  new ResizeObserver(resize).observe(canvas);
}

// ── 루프 ─────────────────────────────────────────────────────
/**
 * 전환 진행도(reveal)에 맞춰 조명·배경·후처리 값을 맞춘다.
 * 렌더 루프가 멈춰 있어도 값이 어긋나지 않도록 루프 밖에서도 호출한다.
 */
function applyRevealState() {
  if (!venue) return;
  const { env } = venue;
  const k = smoothstep(reveal.value, 0, Math.min(30, env.height * 0.6));
  for (const { light, base } of venue.lights) light.intensity = base * k;
  sky.material.uniforms.uBuilt.value = k;
  scene.background.lerpColors(WIRE_BG, venue.builtBg, env.sky ? 0 : k);
  scene.fog.density = env.fog * k;
  grid.material.opacity = 0.35 * (1 - smoothstep(reveal.value, -1, 4));
  grid.visible = grid.material.opacity > 0.001;
  bloom.strength = lerp(0.55, env.bloomStrength ?? 0.7, k);
  // 번짐은 실제 조명기구(밝기 1 이상)에만 — 흰 바닥·접시가 번지지 않게
  bloom.threshold = lerp(0.55, env.bloomThreshold ?? 0.85, k);
  bloom.radius = lerp(0.3, 0.5, k);
  scene.environmentIntensity = k * (env.envIntensity ?? (env.sky ? 0.6 : 1.6));

  // 완성된 뒤에 한 번만 그림자를 굽는다 (전환 중에는 형태가 계속 바뀌므로)
  if (k > 0.995 && !shadowsBaked) {
    shadowsBaked = true;
    renderer.shadowMap.needsUpdate = true;
  } else if (k < 0.9 && shadowsBaked) {
    shadowsBaked = false;
  }
}

function frame() {
  try {
    applyRevealState();
    viewInverse.value.copy(camera.matrixWorld);
    grain.uniforms.uTime.value = performance.now() * 0.001;
    sky.position.copy(camera.position);
    if (controls.enabled) controls.update();
    updateHotspots();
    if (SAFE_MODE) {
      renderer.setRenderTarget(null);
      renderer.render(scene, camera);
    } else {
      composer.render();
    }
  } catch (error) {
    // 한 프레임이 실패해도 루프가 멈추지 않도록 (멈추면 조명이 꺼진 화면으로 남는다)
    console.error('[kyvikos] 렌더 오류', error);
  }
}

let rendering = false;
/** 3D가 화면 밖이면 렌더링 정지 */
function setRendering(on) {
  if (on === rendering) return;
  rendering = on;
  renderer.setAnimationLoop(on ? frame : null);
}
setRendering(true);

// ── 시작 ─────────────────────────────────────────────────────
initUi();
initSite({ loadVenue, setRendering });
Promise.race([document.fonts.ready, wait(1500)]).then(async () => {
  await loadVenue(location.hash.slice(1));
  setTimeout(() => hint.classList.add('show'), 3400);
  setTimeout(() => hint.classList.remove('show'), 11000);
});

// 디버그용
window.__kyvikos = {
  goTo,
  setMode,
  loadVenue,
  zoom,
  setRendering,
  frame,
  camera,
  controls,
  reveal,
  renderer,
  scene,
  composer,
  bloom,
  grain,
  gsap,
  get venue() {
    return venue;
  },
};
