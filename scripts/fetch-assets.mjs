/**
 * Poly Haven(CC0) 에셋을 받아 웹용으로 최적화한다.
 *   node scripts/fetch-assets.mjs
 *
 * - 텍스처: 디퓨즈 + 노멀(OpenGL) → 지정 해상도 WebP
 * - 모델:   glTF 1k → 폴리곤 축소 + 텍스처 512 WebP + meshopt 압축 GLB
 * - HDRI:   1k .hdr
 * 원본은 assets-src/ (git 제외), 결과물은 public/assets/ 에 저장된다.
 */
import { mkdir, writeFile, access } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import sharp from 'sharp';

const ROOT = path.resolve(import.meta.dirname, '..');
const SRC = path.join(ROOT, 'assets-src');
const OUT = path.join(ROOT, 'public/assets');
const HEADERS = { 'User-Agent': 'kyvikos-web asset fetch' };

// 텍스처 id → 출력 해상도
const TEXTURES = {
  leafy_grass: 1024,
  rock_tile_floor_02: 512,
  ceramic_roof_01: 512,
  beige_wall_001: 512,
  asphalt_02: 1024,
  dark_wooden_planks: 512,
  cotton_jersey: 512,
  marble_01: 512,
  brushed_concrete: 1024,
  painted_plaster_wall: 512,
  brick_wall_005: 1024,
  concrete_floor_01: 1024,
  corrugated_iron_02: 512,
};

// 모델 id → 폴리곤 유지 비율 (1 = 축소 안 함)
const MODELS = {
  dining_chair_02: 0.07,
  potted_plant_02: 0.12,
  outdoor_table_chair_set_01: 0.5,
  caged_hanging_light: 0.2,
  ceramic_vase_01: 1,
};

const HDRIS = ['moonless_golf', 'art_studio'];

const exists = (p) => access(p).then(() => true, () => false);

async function json(url) {
  const res = await fetch(url, { headers: HEADERS });
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return res.json();
}

async function download(url, dest) {
  if (await exists(dest)) return;
  await mkdir(path.dirname(dest), { recursive: true });
  const res = await fetch(url, { headers: HEADERS });
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  await writeFile(dest, Buffer.from(await res.arrayBuffer()));
}

async function textures() {
  await mkdir(path.join(OUT, 'textures'), { recursive: true });
  for (const [id, size] of Object.entries(TEXTURES)) {
    const files = await json(`https://api.polyhaven.com/files/${id}`);
    const maps = { diff: files.Diffuse['1k'].jpg.url, nor: files.nor_gl['1k'].jpg.url };
    for (const [kind, url] of Object.entries(maps)) {
      const raw = path.join(SRC, 'textures', `${id}_${kind}.jpg`);
      await download(url, raw);
      await sharp(raw)
        .resize(size, size)
        .webp({ quality: kind === 'nor' ? 90 : 82 })
        .toFile(path.join(OUT, 'textures', `${id}_${kind}.webp`));
    }
    console.log('texture', id);
  }
}

async function models() {
  await mkdir(path.join(OUT, 'models'), { recursive: true });
  for (const [id, ratio] of Object.entries(MODELS)) {
    const files = await json(`https://api.polyhaven.com/files/${id}`);
    const gltf = files.gltf['1k'].gltf;
    const dir = path.join(SRC, 'models', id);
    const main = path.join(dir, path.basename(new URL(gltf.url).pathname));
    await download(gltf.url, main);
    for (const [rel, file] of Object.entries(gltf.include ?? {})) await download(file.url, path.join(dir, rel));

    const args = [
      'gltf-transform', 'optimize', main, path.join(OUT, 'models', `${id}.glb`),
      '--compress', 'meshopt',
      '--texture-compress', 'webp',
      '--texture-size', '512',
    ];
    if (ratio < 1) args.push('--simplify-ratio', String(ratio), '--simplify-error', '0.01');
    else args.push('--simplify', 'false');
    execFileSync('npx', args, { cwd: ROOT, stdio: 'inherit' });
    console.log('model', id);
  }
}

async function hdris() {
  await mkdir(path.join(OUT, 'hdri'), { recursive: true });
  for (const id of HDRIS) {
    const files = await json(`https://api.polyhaven.com/files/${id}`);
    const raw = path.join(SRC, 'hdri', `${id}_1k.hdr`);
    await download(files.hdri['1k'].hdr.url, raw);
    const { copyFile } = await import('node:fs/promises');
    await copyFile(raw, path.join(OUT, 'hdri', `${id}.hdr`));
    console.log('hdri', id);
  }
}

await textures();
await models();
await hdris();
console.log('done');
