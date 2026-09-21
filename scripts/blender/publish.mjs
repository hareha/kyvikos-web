/**
 * Blender 에서 내보낸 베이크 결과를 웹용으로 압축해 public/assets 에 둔다.
 *   node scripts/blender/publish.mjs apec_stage
 *
 * - GLB: meshopt 압축 + 텍스처 WebP(1024). 재질 이름을 웹에서 쓰므로 재질 병합(palette/join)은 끈다.
 * - 라이트맵: PNG → WebP
 * - 매니페스트(JSON): 재질별 라이트맵 그룹, 밝기 scale
 */
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import sharp from 'sharp';

const ROOT = path.resolve(import.meta.dirname, '../..');
const SRC = path.join(ROOT, 'assets-src/blender');
const OUT = path.join(ROOT, 'public/assets');
const name = process.argv[2] ?? 'apec_stage';

await mkdir(path.join(OUT, 'models'), { recursive: true });
await mkdir(path.join(OUT, 'lightmaps'), { recursive: true });

execFileSync(
  'npx',
  [
    'gltf-transform', 'optimize',
    path.join(SRC, `${name}.glb`),
    path.join(OUT, 'models', `${name}.glb`),
    '--compress', 'meshopt',
    '--texture-compress', 'webp',
    '--texture-size', '1024',
    '--simplify', 'false',
    '--palette', 'false',
    '--join', 'false',
  ],
  { cwd: ROOT, stdio: 'inherit' },
);

const manifest = JSON.parse(await readFile(path.join(SRC, `${name}.json`), 'utf8'));
for (const group of Object.keys(manifest.groups)) {
  const file = `${name}_${group}.webp`;
  await sharp(path.join(SRC, `lightmap_${group}.png`)).webp({ quality: 88 }).toFile(path.join(OUT, 'lightmaps', file));
  manifest.groups[group].file = file;
}

// 화면 그래픽(LED·배너·사인·창호)은 GLB 와 별도로 WebP 로 배포
await mkdir(path.join(OUT, 'graphics'), { recursive: true });
const shots = path.join(ROOT, 'assets-src/shots');
for (const file of ['apec_real_led.png', 'apec_real_fascia.png', 'apec_real_sign.png', 'apec_windows.png']) {
  await sharp(path.join(shots, file)).webp({ quality: 90 }).toFile(path.join(OUT, 'graphics', file.replace('.png', '.webp')));
}
await writeFile(path.join(OUT, 'lightmaps', `${name}.json`), JSON.stringify(manifest, null, 2));
console.log('published', name);
