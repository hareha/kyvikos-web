import { canvasTexture, seeded, FONT } from '../../scene/kit.js';

const PAINTS = ['#c9302c', '#e8e6df', '#2b54b8', '#d9a21c', '#3d8f86', '#d8612b'];

function carSide(g, x, y, w, color) {
  const h = w * 0.32;
  g.fillStyle = color;
  g.beginPath();
  g.moveTo(x, y);
  g.lineTo(x + w, y);
  g.lineTo(x + w, y - h * 0.5);
  g.lineTo(x + w * 0.78, y - h * 0.58);
  g.lineTo(x + w * 0.62, y - h);
  g.lineTo(x + w * 0.3, y - h);
  g.lineTo(x + w * 0.16, y - h * 0.56);
  g.lineTo(x, y - h * 0.5);
  g.closePath();
  g.fill();
  g.fillStyle = 'rgba(20,30,40,.7)';
  g.fillRect(x + w * 0.34, y - h * 0.9, w * 0.26, h * 0.3);
}

/** 미디어월: 1970~80년대 생산라인 사진 느낌 (22 × 6m) */
export const muralTexture = () =>
  canvasTexture(2048, 560, (g, w, h) => {
    const r = seeded(21);
    const bg = g.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, '#2f4a50');
    bg.addColorStop(0.45, '#6f8c8a');
    bg.addColorStop(1, '#b9c4bc');
    g.fillStyle = bg;
    g.fillRect(0, 0, w, h);

    // 천장 트러스와 조명
    g.strokeStyle = 'rgba(30,45,50,.7)';
    g.lineWidth = 3;
    for (let x = -200; x < w + 200; x += 70) {
      g.beginPath();
      g.moveTo(x, 0);
      g.lineTo(w / 2 + (x - w / 2) * 0.55, h * 0.36);
      g.stroke();
    }
    for (let y = 20; y < h * 0.36; y += 26) {
      g.beginPath();
      g.moveTo(0, y);
      g.lineTo(w, y);
      g.stroke();
    }
    g.fillStyle = 'rgba(255,250,230,.8)';
    for (let i = 0; i < 40; i++) g.fillRect(r() * w, 10 + r() * h * 0.3, 40, 6);

    // 생산라인: 원근 3줄
    for (let row = 0; row < 3; row++) {
      const y = h * (0.52 + row * 0.2);
      const cw = 150 + row * 110;
      g.fillStyle = 'rgba(60,70,70,.6)';
      g.fillRect(0, y + 4, w, 10 + row * 6);
      for (let x = -cw * r(); x < w; x += cw * 1.25) {
        // 로봇 팔
        g.strokeStyle = '#e0701f';
        g.lineWidth = 6 + row * 4;
        g.beginPath();
        g.moveTo(x + cw * 1.12, y + 8);
        g.lineTo(x + cw * 1.05, y - cw * 0.45);
        g.lineTo(x + cw * 0.8, y - cw * 0.3);
        g.stroke();
        carSide(g, x, y, cw, PAINTS[Math.floor(r() * PAINTS.length)]);
      }
    }
    // 사진 톤
    g.fillStyle = 'rgba(40,80,90,.18)';
    g.fillRect(0, 0, w, h);
    const vig = g.createRadialGradient(w / 2, h / 2, h * 0.2, w / 2, h / 2, w * 0.6);
    vig.addColorStop(0, 'rgba(0,0,0,0)');
    vig.addColorStop(1, 'rgba(0,0,0,.35)');
    g.fillStyle = vig;
    g.fillRect(0, 0, w, h);
  });

/** 게이트 상단 헤더 (10.6 × 0.6m) */
export const gateHeaderTexture = () =>
  canvasTexture(2048, 116, (g, w, h) => {
    g.fillStyle = '#0c0d10';
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#ffffff';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.font = `800 64px ${FONT}`;
    g.fillText('100 MILLION AND ONE STEP FURTHER', w / 2, h / 2 + 2);
    g.font = `600 34px ${FONT}`;
    g.fillStyle = 'rgba(255,255,255,.75)';
    g.fillText('1968', 140, h / 2);
    g.fillText('2024', w - 140, h / 2);
  });

/** 게이트 좌측 패널: 흑백 도시 사진 */
export const cityTexture = () =>
  canvasTexture(1024, 740, (g, w, h) => {
    const r = seeded(4);
    const bg = g.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, '#d8d8d8');
    bg.addColorStop(1, '#7a7a7a');
    g.fillStyle = bg;
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 70; i++) {
      const bw = 40 + r() * 110;
      const bh = 120 + r() * 480;
      const x = r() * w;
      const shade = 60 + Math.floor(r() * 120);
      g.fillStyle = `rgb(${shade},${shade},${shade})`;
      g.fillRect(x, h - bh, bw, bh);
      g.fillStyle = 'rgba(230,230,230,.35)';
      for (let y = h - bh + 10; y < h - 10; y += 18) for (let wx = x + 6; wx < x + bw - 8; wx += 14) g.fillRect(wx, y, 7, 9);
    }
  });

/** 게이트 우측 패널: 네온 미래 도시 */
export const neonTexture = () =>
  canvasTexture(1024, 740, (g, w, h) => {
    const r = seeded(9);
    const bg = g.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, '#0a1a5a');
    bg.addColorStop(1, '#1b0f3a');
    g.fillStyle = bg;
    g.fillRect(0, 0, w, h);
    const neon = ['#39c6ff', '#ff4fb0', '#8a6bff', '#ffd25a', '#4fffd2'];
    for (let i = 0; i < 60; i++) {
      const bw = 40 + r() * 120;
      const bh = 150 + r() * 520;
      const x = r() * w;
      g.fillStyle = `rgba(20,30,90,${0.6 + r() * 0.4})`;
      g.fillRect(x, h - bh, bw, bh);
      g.fillStyle = neon[i % neon.length];
      for (let y = h - bh + 8; y < h - 8; y += 16) {
        if (r() < 0.5) g.fillRect(x + 4 + r() * (bw - 20), y, 8 + r() * 12, 4);
      }
    }
  });

/** Pony 아치: 텍스처 좌표는 아치 형상 좌표(m)에 맞춤 — R=2.4, 다리 2.4 */
export const archTexture = (R, L, r) =>
  canvasTexture(1024, Math.round((1024 * (L + R)) / (2 * R)), (g, w, h) => {
    const s = w / (2 * R);
    const cx = w / 2;
    const cy = h - L * s;
    g.fillStyle = '#353a78';
    g.fillRect(0, 0, w, h);
    // 흰 테두리
    g.strokeStyle = '#f4f1ea';
    g.lineWidth = 22;
    g.beginPath();
    g.moveTo(11, h);
    g.lineTo(11, cy);
    g.arc(cx, cy, R * s - 11, Math.PI, 0);
    g.lineTo(w - 11, h);
    g.stroke();
    g.lineWidth = 12;
    g.beginPath();
    g.moveTo(cx - r * s - 6, h);
    g.lineTo(cx - r * s - 6, cy);
    g.arc(cx, cy, r * s + 6, Math.PI, 0);
    g.lineTo(cx + r * s + 6, h);
    g.stroke();

    // 아치를 따라 문구
    const text = '100,000,001대 생산';
    const rad = ((R + r) / 2) * s;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.font = `800 86px ${FONT}`;
    const a0 = Math.PI * 0.8;
    const a1 = Math.PI * 0.2;
    [...text].forEach((ch, i) => {
      const a = a0 + ((a1 - a0) * i) / (text.length - 1);
      g.save();
      g.translate(cx + Math.cos(a) * rad, cy - Math.sin(a) * rad);
      g.rotate(Math.PI / 2 - a);
      g.fillStyle = /[0-9,]/.test(ch) ? '#e0493f' : '#ffffff';
      g.fillText(ch, 0, 0);
      g.restore();
    });
    // 경·축 원형 마크
    for (const [sx, ch] of [[-1, '경'], [1, '축']]) {
      const x = cx + sx * rad;
      const y = cy + 10;
      g.fillStyle = '#c94a3f';
      g.beginPath();
      g.arc(x, y, 74, 0, Math.PI * 2);
      g.fill();
      g.strokeStyle = '#f4f1ea';
      g.lineWidth = 6;
      g.stroke();
      g.fillStyle = '#fff';
      g.font = `800 76px ${FONT}`;
      g.fillText(ch, x, y + 4);
    }
    // 다리 세로 문구
    g.font = `700 58px ${FONT}`;
    g.fillStyle = '#f4f1ea';
    const vertical = (str, x, y0) => [...str].forEach((ch, i) => g.fillText(ch, x, y0 + i * 66));
    vertical('우리손', cx - rad, cy + 130);
    vertical('품질향상', cx + rad, cy + 130);
  });

/** 곡면 파티션 (콘크리트 톤 + 작은 캡션) */
export const partitionTexture = (caption) =>
  canvasTexture(512, 640, (g, w, h) => {
    const r = seeded(caption.length * 13);
    g.fillStyle = '#6d6b68';
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 1400; i++) {
      const v = 80 + Math.floor(r() * 50);
      g.fillStyle = `rgba(${v},${v},${v - 4},.35)`;
      g.fillRect(r() * w, r() * h, 3 + r() * 10, 2 + r() * 6);
    }
    g.fillStyle = '#f4f4f2';
    g.font = `italic 500 30px ${FONT}`;
    g.textAlign = 'center';
    g.fillText(caption, w / 2, h * 0.36);
  });

/** 아카이브 월: 사진·문서 액자와 텍스트 블록 */
export const archiveTexture = (light = false) =>
  canvasTexture(2048, 512, (g, w, h) => {
    const r = seeded(light ? 17 : 31);
    g.fillStyle = light ? '#c9ccce' : '#45474b';
    g.fillRect(0, 0, w, h);
    if (!light) {
      const top = g.createLinearGradient(0, 0, 0, 60);
      top.addColorStop(0, 'rgba(255,255,255,.35)');
      top.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = top;
      g.fillRect(0, 0, w, 60);
    }
    const tones = ['#7f9c7a', '#b06a3a', '#6d86a8', '#c9b58a', '#8b8f96', '#a24f45', '#d7d2c4'];
    let x = 60;
    while (x < w - 160) {
      const fw = 90 + r() * 170;
      const fh = 70 + r() * 110;
      const y = 70 + r() * 90;
      g.fillStyle = '#f2f0ea';
      g.fillRect(x - 6, y - 6, fw + 12, fh + 12);
      g.fillStyle = tones[Math.floor(r() * tones.length)];
      g.fillRect(x, y, fw, fh);
      g.fillStyle = 'rgba(255,255,255,.25)';
      g.fillRect(x + fw * 0.1, y + fh * 0.2, fw * 0.5, fh * 0.35);
      g.fillStyle = light ? 'rgba(40,40,40,.55)' : 'rgba(230,230,230,.6)';
      for (let l = 0; l < 3; l++) g.fillRect(x, y + fh + 22 + l * 14, fw * (0.5 + r() * 0.5), 5);
      x += fw + 40 + r() * 60;
    }
  });

/** 제도실 뒷벽 도면 */
export const blueprintTexture = () =>
  canvasTexture(1024, 400, (g, w, h) => {
    g.fillStyle = '#eceae4';
    g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(40,50,70,.55)';
    g.lineWidth = 2;
    for (const [ox, oy, sc] of [[120, 300, 1], [560, 280, 0.8]]) {
      g.beginPath();
      g.moveTo(ox, oy);
      g.lineTo(ox + 360 * sc, oy);
      g.lineTo(ox + 360 * sc, oy - 60 * sc);
      g.lineTo(ox + 270 * sc, oy - 70 * sc);
      g.lineTo(ox + 220 * sc, oy - 120 * sc);
      g.lineTo(ox + 110 * sc, oy - 120 * sc);
      g.lineTo(ox + 60 * sc, oy - 65 * sc);
      g.lineTo(ox, oy - 55 * sc);
      g.closePath();
      g.stroke();
      for (const wx of [80, 280]) {
        g.beginPath();
        g.arc(ox + wx * sc, oy, 32 * sc, 0, Math.PI * 2);
        g.stroke();
      }
    }
    g.strokeStyle = 'rgba(40,50,70,.2)';
    for (let x = 0; x < w; x += 40) {
      g.beginPath();
      g.moveTo(x, 0);
      g.lineTo(x, h);
      g.stroke();
    }
  });

/** 제도실 안내 사인 */
export const signTexture = () =>
  canvasTexture(512, 720, (g, w, h) => {
    g.fillStyle = '#f1efe9';
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#1b1b1b';
    g.font = `700 34px ${FONT}`;
    g.fillText('1980년 현대자동차', 40, 90);
    g.fillText('제도공의 방', 40, 136);
    g.fillStyle = 'rgba(30,30,30,.45)';
    for (let i = 0; i < 18; i++) g.fillRect(40, 200 + i * 24, 360 + ((i * 53) % 70), 7);
  });
