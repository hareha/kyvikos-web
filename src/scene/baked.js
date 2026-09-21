import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { revealable, lineMaterials } from './kit.js';

/*
 * Blender 에서 조명을 베이크한 장면(scripts/blender/*) 을 불러온다.
 *
 * - 정적 구조물: MeshBasicMaterial(색·텍스처 × 라이트맵). 실시간 광원 계산이 없어 가볍고,
 *                Cycles 로 계산한 간접광·그림자가 그대로 보인다.
 * - 발광체:     톤매핑 없는 MeshBasicMaterial (블룸)
 * - 동적 요소:  금속 트러스·의자·유리 — MeshStandardMaterial (환경광·실시간 광원)
 *
 * 재질 정보는 Blender 재질의 web 속성(glTF extras)에서, 라이트맵 매칭은 매니페스트의
 * objects(오브젝트 → 라이트맵 그룹)에서 가져온다.
 */

const BASE = import.meta.env.BASE_URL;
const V = `?v=${__BUILD__}`; // 배포 버전 (캐시 무효화)
const gltfLoader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const textureLoader = new THREE.TextureLoader();
const fileLoader = new THREE.FileLoader().setResponseType('json');

const cache = new Map();
function texture(url, { srgb = true, repeat = false } = {}) {
  const key = `${url}|${srgb}|${repeat}`;
  let t = cache.get(key);
  if (!t) {
    t = textureLoader.load(url);
    t.flipY = false; // glTF(Blender) UV 규약
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.anisotropy = 8;
    if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
    cache.set(key, t);
  }
  return t;
}

const library = (id) => texture(`${BASE}assets/textures/${id}_diff.webp`, { repeat: true });
const graphic = (file) => texture(`${BASE}assets/graphics/${file.replace(/\.png$/, '.webp')}${V}`);

/** Blender 발광 세기 → 웹 밝기 배율 (블룸 임계값 0.85 기준) */
const glowFactor = (strength, isImage) =>
  isImage ? 1 + Math.log10(Math.max(strength, 1)) * 0.15 : 1 + Math.log10(Math.max(strength, 1)) * 1.2;

/** 부모를 거슬러 올라가 매니페스트에 있는 오브젝트 이름을 찾는다 */
function ownerName(object, names) {
  for (let o = object; o; o = o.parent) if (o.name in names) return o.name;
  return object.parent?.name ?? object.name;
}

/**
 * @param root      공간 루트 (여기에 붙는다)
 * @param name      public/assets/models/<name>.glb, lightmaps/<name>.json
 * @param context   와이어프레임에서 흐리게 그릴 오브젝트 이름들 (원래 있던 공간)
 */
export async function loadBakedScene(root, name, { context = [] } = {}) {
  const [gltf, manifest] = await Promise.all([
    gltfLoader.loadAsync(`${BASE}assets/models/${name}.glb${V}`),
    fileLoader.loadAsync(`${BASE}assets/lightmaps/${name}.json${V}`),
  ]);

  const lightmaps = {};
  for (const [group, info] of Object.entries(manifest.groups)) {
    const base = texture(`${BASE}assets/lightmaps/${info.file}${V}`);
    // 라이트맵은 8비트에 1/scale 로 담겨 있다. MeshBasicMaterial 은 라이트맵에 1/π 를 곱하므로 π 를 되돌린다
    lightmaps[group] = { base, intensity: info.scale * Math.PI, byChannel: {} };
  }
  const lightmapFor = (group, channel) => {
    const lm = lightmaps[group];
    if (!lm.byChannel[channel]) {
      const t = lm.base.clone();
      t.channel = channel;
      lm.byChannel[channel] = t;
    }
    return lm.byChannel[channel];
  };

  const objects = manifest.objects ?? {};
  const contextSet = new Set(context);
  const edges = { event: [], context: [] };

  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse((mesh) => {
    if (!mesh.isMesh) return;
    const source = mesh.material;
    const web = source.userData?.web ?? {};
    const owner = ownerName(mesh, objects);
    const group = objects[owner];
    const color = new THREE.Color().fromArray(web.color ?? [1, 1, 1]);
    let material;

    const hasUv1 = Boolean(mesh.geometry.attributes.uv1);
    if (web.keep) {
      // 불러온 모델(외부 에셋): 모델 원래의 재질·텍스처 + 베이크된 조명
      material = group && hasUv1
        ? new THREE.MeshBasicMaterial({
            color: source.color,
            map: source.map,
            lightMap: lightmapFor(group, 1),
            lightMapIntensity: lightmaps[group].intensity,
            side: source.side,
          })
        : source;
    } else if (group && !hasUv1) {
      // 모델을 고친 뒤 아직 베이크 전: 라이트맵 UV 가 없으므로 실시간 조명으로 그린다
      material = new THREE.MeshStandardMaterial({
        color: web.image ? new THREE.Color('#ffffff') : color,
        roughness: web.rough ?? 0.7,
        metalness: web.metal ?? 0,
        map: web.image ? graphic(web.image) : web.tex ? library(web.tex) : null,
        side: source.side,
      });
    } else if (group) {
      // 정적 구조물: 색·텍스처 × 베이크된 조명
      material = new THREE.MeshBasicMaterial({
        color,
        lightMap: lightmapFor(group, hasUv1 ? 1 : 0),
        lightMapIntensity: lightmaps[group].intensity,
      });
      if (hasUv1 && web.tex) material.map = library(web.tex);
      if (hasUv1 && web.image) {
        material.map = graphic(web.image);
        material.color.set('#ffffff');
      }
      if (source.side === THREE.DoubleSide) material.side = THREE.DoubleSide;
    } else if (web.emit) {
      const k = glowFactor(web.emitStrength ?? 1, Boolean(web.image));
      material = new THREE.MeshBasicMaterial({
        color: web.image ? new THREE.Color(k, k, k) : new THREE.Color().fromArray(web.emitColor ?? [1, 1, 1]).multiplyScalar(k),
        map: web.image ? graphic(web.image) : null,
        toneMapped: false,
      });
    } else if (web.alpha && web.image) {
      // 솔잎 같은 알파 카드: 투명 부분을 잘라내고 양면으로
      material = new THREE.MeshStandardMaterial({
        color,
        map: graphic(web.image),
        alphaTest: 0.5,
        side: THREE.DoubleSide,
        roughness: web.rough ?? 0.8,
        metalness: 0,
      });
    } else if (web.transmission) {
      material = new THREE.MeshStandardMaterial({
        color,
        roughness: 0.05,
        metalness: 0,
        transparent: true,
        opacity: 0.22,
        depthWrite: false,
        envMapIntensity: 1.6,
      });
    } else {
      material = new THREE.MeshStandardMaterial({
        color,
        roughness: web.rough ?? 0.6,
        metalness: web.metal ?? 0,
        map: web.tex ? library(web.tex) : null,
      });
    }
    mesh.material = revealable(material);

    // 와이어프레임 선 (발광체·유리는 제외)
    if (web.emit || web.transmission || web.alpha) return;
    const layer = contextSet.has(owner) ? 'context' : 'event';
    if (mesh.isInstancedMesh) {
      // 인스턴스(의자)는 외곽 상자만
      mesh.geometry.computeBoundingBox();
      const boxEdges = new THREE.EdgesGeometry(new THREE.BoxGeometry(...mesh.geometry.boundingBox.getSize(new THREE.Vector3()).toArray()));
      const center = mesh.geometry.boundingBox.getCenter(new THREE.Vector3());
      const m = new THREE.Matrix4();
      for (let i = 0; i < mesh.count; i++) {
        mesh.getMatrixAt(i, m);
        edges[layer].push(boxEdges.clone().translate(center.x, center.y, center.z).applyMatrix4(m.premultiply(mesh.matrixWorld)));
      }
    } else {
      const threshold = ['tables', 'pines', 'garden'].includes(owner) ? 50 : 30;
      edges[layer].push(new THREE.EdgesGeometry(mesh.geometry, threshold).applyMatrix4(mesh.matrixWorld));
    }
  });

  for (const [layer, geometries] of Object.entries(edges)) {
    if (!geometries.length) continue;
    const merged = mergeLines(geometries);
    const lines = new THREE.LineSegments(merged, lineMaterials[layer]);
    lines.frustumCulled = false;
    root.add(lines);
  }
  root.add(gltf.scene);
  return gltf.scene;
}

function mergeLines(geometries) {
  let count = 0;
  for (const g of geometries) count += g.attributes.position.count;
  const out = new Float32Array(count * 3);
  let offset = 0;
  for (const g of geometries) {
    out.set(g.attributes.position.array, offset);
    offset += g.attributes.position.array.length;
    g.dispose();
  }
  const merged = new THREE.BufferGeometry();
  merged.setAttribute('position', new THREE.BufferAttribute(out, 3));
  return merged;
}
