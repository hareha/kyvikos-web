import * as THREE from 'three';
import { revealable } from './kit.js';

/*
 * 행사장 부지를 건축 모형처럼 잘라낸 받침판 (모든 행사장 공통)
 * 실제 구현: 짙은 차콜 무광 판 + 옅은 5m 모눈 + 두께 있는 옆면 + 가는 금빛 테두리
 * 와이어프레임: 판 윤곽 + 5m 바둑판 모눈 (plateOutline / plateGrid 를 Builder.polyline 으로)
 */

export function plateShape({ x0, x1, z0, z1, r }) {
  // 셰이프 좌표: (x, -z)
  const s = new THREE.Shape();
  s.moveTo(x0 + r, -z1);
  s.lineTo(x1 - r, -z1);
  s.quadraticCurveTo(x1, -z1, x1, -z1 + r);
  s.lineTo(x1, -z0 - r);
  s.quadraticCurveTo(x1, -z0, x1 - r, -z0);
  s.lineTo(x0 + r, -z0);
  s.quadraticCurveTo(x0, -z0, x0, -z0 - r);
  s.lineTo(x0, -z1 + r);
  s.quadraticCurveTo(x0, -z1, x0 + r, -z1);
  return s;
}

export function plateOutline(P, y) {
  return plateShape(P)
    .getSpacedPoints(160)
    .map((p) => new THREE.Vector3(p.x, y, -p.y));
}

/** 둥근 모서리 안쪽으로 잘린 모눈 선들 */
export function plateGrid(P, step, y) {
  const { x0, x1, z0, z1, r } = P;
  const inset = (d) => (d >= r ? 0 : r - Math.sqrt(Math.max(0, r * r - (r - d) * (r - d))));
  const lines = [];
  for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) {
    const d = Math.min(x - x0, x1 - x);
    lines.push([new THREE.Vector3(x, y, z0 + inset(d)), new THREE.Vector3(x, y, z1 - inset(d))]);
  }
  for (let z = Math.ceil(z0 / step) * step; z <= z1; z += step) {
    const d = Math.min(z - z0, z1 - z);
    lines.push([new THREE.Vector3(x0 + inset(d), y, z), new THREE.Vector3(x1 - inset(d), y, z)]);
  }
  return lines;
}

/** 5m 한 칸 모눈 (판 윗면 UV = 월드 좌표 m 이므로 repeat 1/5) */
function gridTexture() {
  const size = 256;
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = c.getContext('2d');
  g.fillStyle = '#2a2c30';
  g.fillRect(0, 0, size, size);
  for (let i = 0; i < 900; i++) {
    g.fillStyle = `rgba(255,255,255,${Math.random() * 0.018})`;
    g.fillRect(Math.random() * size, Math.random() * size, 2, 2);
  }
  g.fillStyle = '#383b41';
  g.fillRect(0, 0, size, 2);
  g.fillRect(0, 0, 2, size);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(1 / 5, 1 / 5);
  t.anisotropy = 8;
  return t;
}

/** P: { x0, x1, z0, z1, r, depth, top } — top 은 판 윗면 높이 (기본 -0.01) */
export function sitePlate(P) {
  const top = P.top ?? -0.01;
  const geo = new THREE.ExtrudeGeometry(plateShape(P), { depth: P.depth, bevelEnabled: false, curveSegments: 16 });
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, top - P.depth, 0);
  const topMat = revealable(new THREE.MeshStandardMaterial({ color: '#ffffff', map: gridTexture(), roughness: 0.88, metalness: 0 }));
  const side = revealable(new THREE.MeshStandardMaterial({ color: '#141518', roughness: 0.6 }));
  const plate = new THREE.Mesh(geo, [topMat, side]);
  const rim = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(plateOutline(P, top + 0.01)),
    revealable(new THREE.LineBasicMaterial({ color: '#9a8662' })),
  );
  const group = new THREE.Group();
  group.add(plate, rim);
  return group;
}
