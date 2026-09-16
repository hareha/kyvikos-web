import './style.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import gsap from 'gsap';
import { reveal, disposeTree } from './scene/kit.js';
import { createSky, createStars } from './scene/environment.js';
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
renderer.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth < 768 ? 1.5 : 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;

const scene = new THREE.Scene();
scene.background = WIRE_BG.clone();
scene.fog = new THREE.FogExp2('#000000', 0);

const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.1, 3000);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.autoRotateSpeed = 0.35;
controls.enabled = false;

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth / 2, window.innerHeight / 2), 0.55, 0.3, 0.55);
composer.addPass(bloom);
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
  gsap.killTweensOf(reveal);
  reveal.value = state.mode === 'built' ? builtLevel() : REVEAL_WIRE;

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

  loader.classList.add('done');
  state.loading = false;
  goTo(overview.id, { duration: 3.2 });
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
      enableZoom: true,
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
      enableZoom: false,
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
    });
  }
  refreshCard();
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
  const w = window.innerWidth;
  const h = window.innerHeight;
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
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
  });
}

// ── 루프 ─────────────────────────────────────────────────────
function frame() {
  if (venue) {
    const { env } = venue;
    const k = smoothstep(reveal.value, 0, Math.min(30, env.height * 0.6));
    for (const { light, base } of venue.lights) light.intensity = base * k;
    sky.material.uniforms.uBuilt.value = k;
    scene.background.lerpColors(WIRE_BG, venue.builtBg, env.sky ? 0 : k);
    scene.fog.density = env.fog * k;
    grid.material.opacity = 0.35 * (1 - smoothstep(reveal.value, -1, 4));
    grid.visible = grid.material.opacity > 0.001;
    bloom.strength = lerp(0.55, 0.7, k);
    bloom.threshold = lerp(0.55, 0.85, k);
    bloom.radius = lerp(0.3, 0.5, k);
  }
  sky.position.copy(camera.position);

  if (controls.enabled) controls.update();
  updateHotspots();
  composer.render();
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
  camera,
  controls,
  reveal,
  get venue() {
    return venue;
  },
};
