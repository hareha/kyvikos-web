import { canvasTexture, seeded, FONT } from '../../scene/kit.js';

const ORANGE = ['#ff6a1a', '#e8401c', '#c42a18'];

/** 방사형 빛줄기 (키 비주얼 공통 모티프) */
function sunburst(g, cx, cy, r, count, seed) {
  const rnd = seeded(seed);
  g.save();
  g.globalCompositeOperation = 'lighter';
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2 + rnd() * 0.05;
    const w = 0.01 + rnd() * 0.035;
    g.fillStyle = `rgba(255,${190 + rnd() * 60},${80 + rnd() * 90},${0.08 + rnd() * 0.22})`;
    g.beginPath();
    g.moveTo(cx, cy);
    g.lineTo(cx + Math.cos(a - w) * r, cy + Math.sin(a - w) * r);
    g.lineTo(cx + Math.cos(a + w) * r, cy + Math.sin(a + w) * r);
    g.fill();
  }
  const core = g.createRadialGradient(cx, cy, 0, cx, cy, r * 0.35);
  core.addColorStop(0, 'rgba(255,250,220,1)');
  core.addColorStop(0.3, 'rgba(255,200,110,.7)');
  core.addColorStop(1, 'rgba(255,120,40,0)');
  g.fillStyle = core;
  g.fillRect(cx - r, cy - r, r * 2, r * 2);
  g.restore();
}

function orangeBg(g, w, h) {
  const bg = g.createLinearGradient(0, 0, w, h);
  bg.addColorStop(0, ORANGE[0]);
  bg.addColorStop(0.6, ORANGE[1]);
  bg.addColorStop(1, ORANGE[2]);
  g.fillStyle = bg;
  g.fillRect(0, 0, w, h);
}

/** LOCAL / POWER 2025 로고 블록. (x, y)는 좌상단, s는 글자 높이 */
function logo(g, x, y, s, color = '#fff') {
  g.save();
  g.fillStyle = color;
  g.textBaseline = 'top';
  g.font = `900 ${s}px ${FONT}`;
  g.fillText('LOCAL', x, y);
  g.fillText('POWER', x, y + s * 0.92);
  const lw = g.measureText('LOCAL').width;
  g.font = `900 ${s * 0.45}px ${FONT}`;
  g.fillText('20', x + lw + s * 0.06, y + s * 0.02);
  g.fillText('25', x + lw + s * 0.06, y + s * 0.44);
  g.restore();
}

/** 런웨이 뒤 중앙 LED (7.2 × 4m) — 빛줄기 + 붉은 그래픽 + 로고 */
export const ledTexture = () =>
  canvasTexture(1440, 800, (g, w, h) => {
    g.fillStyle = '#5a0c08';
    g.fillRect(0, 0, w, h);
    const r = seeded(41);
    g.strokeStyle = 'rgba(255,90,60,.55)';
    g.lineWidth = 3;
    for (let i = 0; i < 70; i++) {
      const x = w * 0.45 + r() * w * 0.55;
      const y = r() * h;
      g.beginPath();
      g.moveTo(x, y);
      g.lineTo(x + (r() - 0.5) * 160, y);
      g.lineTo(x + (r() - 0.5) * 160, y + (r() - 0.5) * 120);
      g.stroke();
    }
    sunburst(g, w * 0.14, h * 0.5, w * 0.8, 90, 5);
    g.fillStyle = 'rgba(20,6,6,.55)';
    g.fillRect(w * 0.56, h * 0.26, w * 0.3, h * 0.42);
    logo(g, w * 0.585, h * 0.3, 118);
  });

/** 중앙 LED 양옆 세로 패널 (3 × 4m) */
export const panelTexture = () =>
  canvasTexture(600, 800, (g, w, h) => {
    orangeBg(g, w, h);
    sunburst(g, w * 0.5, h * 1.05, h, 50, 9);
    logo(g, 70, 190, 150);
    g.save();
    g.translate(48, h * 0.78);
    g.rotate(-Math.PI / 2);
    g.fillStyle = '#fff';
    g.font = `700 34px ${FONT}`;
    g.fillText('Hong Kong Fashion In Seoul', 0, 0);
    g.restore();
  });

/** 거리 쪽 가림막 키 비주얼 (24 × 4.2m) */
export const hoardingTexture = () =>
  canvasTexture(2048, 358, (g, w, h) => {
    orangeBg(g, w, h);
    sunburst(g, w * 0.2, h * 0.55, w * 0.32, 110, 13);
    g.fillStyle = '#fff';
    g.textBaseline = 'middle';
    g.font = `800 30px ${FONT}`;
    g.fillText('Hong Kong Fashion In Seoul', w * 0.47, h * 0.5);
    logo(g, w * 0.64, h * 0.12, 150);
    g.font = `800 64px ${FONT}`;
    g.fillText('28 SEP — 11 OCT', w * 0.84, h * 0.5);
  });

/** 가림막 후원 로고 패널 (4 × 4.2m) */
export const sponsorTexture = () =>
  canvasTexture(400, 420, (g, w, h) => {
    g.fillStyle = '#f4f3f0';
    g.fillRect(0, 0, w, h);
    const r = seeded(23);
    for (let row = 0; row < 7; row++) {
      for (let col = 0; col < 3; col++) {
        g.fillStyle = r() < 0.4 ? '#c7352a' : r() < 0.5 ? '#3a6aa8' : '#8a8a8a';
        g.fillRect(40 + col * 115, 60 + row * 48, 60 + r() * 30, 16);
      }
    }
  });

/** EXHIBITION IN SEOUL 패널 (14 × 4.2m) */
export const exhibitionTexture = () =>
  canvasTexture(2048, 614, (g, w, h) => {
    orangeBg(g, w, h);
    g.fillStyle = '#fff';
    g.textBaseline = 'top';
    logo(g, 90, 150, 170);
    g.font = `800 64px ${FONT}`;
    g.fillText('EXHIBITION IN SEOUL', w * 0.52, 80);
    g.font = `700 60px ${FONT}`;
    g.fillText('서울 전시', w * 0.52, 160);
    for (let i = 0; i < 3; i++) {
      g.fillStyle = 'rgba(255,255,255,.9)';
      g.fillRect(w * 0.52, 270 + i * 105, w * 0.42, 6);
      g.fillStyle = 'rgba(255,235,220,.55)';
      for (let l = 0; l < 4; l++) g.fillRect(w * 0.52, 292 + i * 105 + l * 16, w * (0.3 + ((l * 7 + i) % 5) * 0.025), 7);
    }
  });

/** 라이트박스 — 0: 홍콩 야경, 1: 컬러풀한 식당 풍경 */
export const lightboxTexture = (variant = 0) =>
  canvasTexture(512, 320, (g, w, h) => {
    const r = seeded(31 + variant);
    if (variant === 0) {
      const sky = g.createLinearGradient(0, 0, 0, h);
      sky.addColorStop(0, '#3c5aa8');
      sky.addColorStop(0.55, '#c68ab8');
      sky.addColorStop(1, '#1a2448');
      g.fillStyle = sky;
      g.fillRect(0, 0, w, h);
      for (let i = 0; i < 26; i++) {
        const bw = 14 + r() * 26;
        const bh = 40 + r() * 150 * (i === 17 ? 1.6 : 1);
        const x = r() * w;
        g.fillStyle = `rgba(${40 + r() * 40},${60 + r() * 50},${110 + r() * 60},.95)`;
        g.fillRect(x, h * 0.66 - bh, bw, bh);
        g.fillStyle = 'rgba(255,230,170,.8)';
        for (let k = 0; k < bh / 9; k++) if (r() < 0.35) g.fillRect(x + 2 + r() * (bw - 5), h * 0.66 - bh + k * 9, 3, 3);
      }
      g.globalAlpha = 0.35;
      g.scale(1, -1);
      g.drawImage(g.canvas, 0, h * 0.34, w, h * 0.66, 0, -h * 1.32, w, h * 0.66);
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.globalAlpha = 1;
    } else {
      g.fillStyle = '#e4502c';
      g.fillRect(0, 0, w, h);
      g.fillStyle = '#f7c66a';
      g.fillRect(0, 0, w, h * 0.25);
      for (let i = 0; i < 9; i++) {
        g.fillStyle = ['#2a6bd8', '#ffffff', '#ffd23f', '#1a8a6a'][i % 4];
        g.fillRect(20 + i * 54, h * 0.55 + r() * 30, 34, 60);
      }
      g.fillStyle = '#fff';
      g.font = `800 36px ${FONT}`;
      g.fillText('URBAN JUNGLE', w * 0.3, h * 0.42);
    }
  });
