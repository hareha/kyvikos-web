import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { revealable } from './kit.js';

/*
 * 실사 에셋 (Poly Haven, CC0) — scripts/fetch-assets.mjs 로 public/assets 에 준비된다.
 * 셰이더 부담을 줄이기 위해 표준 재질은 '디퓨즈 + 노멀' 두 장만 쓴다.
 */

const BASE = import.meta.env.BASE_URL;

// ── 로딩 대기 ────────────────────────────────────────────────
// 텍스처가 도착하기 전에는 재질이 검게 그려지므로, 공간을 보여주기 전에 로딩을 기다린다.
const manager = THREE.DefaultLoadingManager;
let pending = 0;
const waiters = new Set();
const flush = () => {
  if (pending > 0) return;
  for (const resolve of waiters) resolve();
  waiters.clear();
};
manager.onStart = (_, loaded, total) => {
  pending = total - loaded;
};
manager.onProgress = (_, loaded, total) => {
  pending = total - loaded;
  flush();
};
manager.onLoad = () => {
  pending = 0;
  flush();
};
manager.onError = (url) => console.warn(`[kyvikos] 에셋 로드 실패: ${url}`);

/** 진행 중인 에셋 로딩이 끝나면(또는 timeout 후) resolve */
export function whenAssetsLoaded(timeout = 8000) {
  return new Promise((resolve) => {
    if (pending <= 0) return resolve();
    waiters.add(resolve);
    setTimeout(() => {
      waiters.delete(resolve);
      resolve();
    }, timeout);
  });
}

const textureLoader = new THREE.TextureLoader();
const gltfLoader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);

const textures = new Map();
function texture(url, srgb) {
  let t = textures.get(url);
  if (!t) {
    t = textureLoader.load(url);
    t.wrapS = THREE.RepeatWrapping;
    t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = 8;
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    textures.set(url, t);
  }
  return t;
}

/**
 * 실사 PBR 재질.
 * tile: 텍스처 한 장이 덮는 크기(m). Builder가 월드 좌표로 UV를 다시 계산해
 *       면의 크기와 상관없이 같은 밀도로 반복된다.
 */
export function pbr(id, { color = '#ffffff', roughness = 0.9, metalness = 0, tile = 2, normalScale = 1, ...extra } = {}) {
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness,
    metalness,
    map: texture(`${BASE}assets/textures/${id}_diff.webp`, true),
    normalMap: texture(`${BASE}assets/textures/${id}_nor.webp`, false),
    normalScale: new THREE.Vector2(normalScale, normalScale),
    ...extra,
  });
  material.userData.worldUV = tile;
  return revealable(material);
}

// ── 3D 모델 ───────────────────────────────────────────────────
const models = new Map();

/** GLB를 불러와 [{ geometry, material, matrix }] 로 정리 (캐시) */
export function loadModel(id) {
  if (!models.has(id)) {
    models.set(
      id,
      gltfLoader.loadAsync(`${BASE}assets/models/${id}.glb`).then(({ scene }) => {
        scene.updateMatrixWorld(true);
        const parts = [];
        scene.traverse((o) => {
          if (!o.isMesh) return;
          parts.push({ geometry: o.geometry, material: o.material, matrix: o.matrixWorld.clone() });
        });
        return parts;
      }),
    );
  }
  return models.get(id);
}

function prepareMaterial(source, { color, roughness } = {}) {
  const m = source.clone();
  // 금속/거칠기/AO 맵은 빼서 텍스처 슬롯과 varying 수를 줄인다
  m.metalnessMap = null;
  m.roughnessMap = null;
  m.aoMap = null;
  m.metalness = 0;
  m.roughness = roughness ?? 0.65;
  if (color) m.color.set(color);
  return revealable(m);
}

const _m = new THREE.Matrix4();

/**
 * 같은 모델을 여러 위치에 인스턴스로 배치한다.
 * matrices: 배치 행렬 배열 (모델 원점 = 바닥 중앙 기준)
 * 로드가 끝나면 root 에 붙고 onReady() 를 부른다. 실패해도 장면은 그대로 둔다.
 */
export function placeModel(root, id, matrices, { onReady, color, roughness } = {}) {
  if (!matrices.length) return;
  loadModel(id)
    .then((parts) => {
      for (const { geometry, material, matrix } of parts) {
        const mesh = new THREE.InstancedMesh(geometry, prepareMaterial(material, { color, roughness }), matrices.length);
        matrices.forEach((m, i) => mesh.setMatrixAt(i, _m.multiplyMatrices(m, matrix)));
        mesh.instanceMatrix.needsUpdate = true;
        mesh.frustumCulled = false;
        root.add(mesh);
      }
      onReady?.();
    })
    .catch((error) => console.warn(`[kyvikos] 모델 로드 실패: ${id}`, error));
}

/** Builder가 만든 병합 메시 중 특정 재질을 쓰는 것을 찾아 숨긴다 (모델로 대체된 임시 형태) */
export function hideProxy(root, material) {
  for (const child of root.children) if (child.material === material) child.visible = false;
}

// ── HDRI 환경광 ───────────────────────────────────────────────
const hdris = new Map();

export function loadHdri(renderer, id) {
  if (!hdris.has(id)) {
    hdris.set(
      id,
      new HDRLoader().loadAsync(`${BASE}assets/hdri/${id}.hdr`).then((hdr) => {
        hdr.mapping = THREE.EquirectangularReflectionMapping;
        const pmrem = new THREE.PMREMGenerator(renderer);
        const env = pmrem.fromEquirectangular(hdr).texture;
        pmrem.dispose();
        hdr.dispose();
        return env;
      }),
    );
  }
  return hdris.get(id);
}
