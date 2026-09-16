import { canvasTexture, seeded, FONT } from '../../scene/kit.js';

/*
 * 캔버스 텍스처. 실제 작품·사진을 복제하지 않고, 분위기만 따온 추상 그래픽으로 그립니다.
 */

const INK = '#141312';

/** 거친 붓질 선 */
function scribble(g, r, x, y, w, h, n, color, width) {
  g.strokeStyle = color;
  g.lineWidth = width;
  g.lineCap = 'round';
  g.lineJoin = 'round';
  g.beginPath();
  g.moveTo(x + r() * w, y + r() * h);
  for (let i = 0; i < n; i++) g.lineTo(x + r() * w, y + r() * h);
  g.stroke();
}

/** 왕관 모티프 (단순 지그재그) */
function crown(g, x, y, s, color, fill) {
  g.beginPath();
  g.moveTo(x - s, y);
  g.lineTo(x - s, y - s * 0.9);
  g.lineTo(x - s * 0.5, y - s * 0.35);
  g.lineTo(x, y - s * 1.1);
  g.lineTo(x + s * 0.5, y - s * 0.35);
  g.lineTo(x + s, y - s * 0.9);
  g.lineTo(x + s, y);
  g.closePath();
  if (fill) {
    g.fillStyle = fill;
    g.fill();
  }
  g.strokeStyle = color;
  g.lineWidth = s * 0.12;
  g.stroke();
}

/** 가면 같은 얼굴 (원 + 이빨 격자) */
function mask(g, r, x, y, s) {
  g.strokeStyle = INK;
  g.lineWidth = s * 0.08;
  g.beginPath();
  g.ellipse(x, y, s * 0.8, s, 0, 0, Math.PI * 2);
  g.stroke();
  g.fillStyle = INK;
  g.beginPath();
  g.arc(x - s * 0.3, y - s * 0.25, s * 0.14, 0, Math.PI * 2);
  g.arc(x + s * 0.3, y - s * 0.25, s * 0.14, 0, Math.PI * 2);
  g.fill();
  g.fillStyle = '#f4efe0';
  g.fillRect(x - s * 0.5, y + s * 0.3, s, s * 0.3);
  g.lineWidth = s * 0.04;
  g.strokeRect(x - s * 0.5, y + s * 0.3, s, s * 0.3);
  for (let i = 1; i < 6; i++) {
    g.beginPath();
    g.moveTo(x - s * 0.5 + (i * s) / 6, y + s * 0.3);
    g.lineTo(x - s * 0.5 + (i * s) / 6, y + s * 0.6);
    g.stroke();
  }
  scribble(g, r, x - s, y - s * 1.4, s * 2, s * 0.5, 8, INK, s * 0.06);
}

const BGS = ['#efe4c8', '#e9b23a', '#1c1b19', '#2f5fb8', '#f4f1e8', '#d9d2bf', '#c7412f', '#e3cfa3'];
const WORDS = ['ABC', '©', 'XIII', '100', 'TAR', 'OIL', 'KING', '≠', 'AAA', 'PER', '1982'];

/** 표현주의풍 추상 캔버스 한 칸 */
function paintCell(g, r, x0, y0, w, h, i) {
  g.save();
  g.beginPath();
  g.rect(x0, y0, w, h);
  g.clip();
  const dark = i === 2;
  g.fillStyle = BGS[i % BGS.length];
  g.fillRect(x0, y0, w, h);

  // 색면
  const colors = ['#f2c230', '#d8342c', '#2b64c6', '#f3ead2', '#6db36a', '#e98a2a', '#ffffff', '#111'];
  for (let k = 0; k < 7; k++) {
    g.fillStyle = colors[Math.floor(r() * colors.length)];
    g.globalAlpha = 0.65 + r() * 0.35;
    const bw = w * (0.12 + r() * 0.35);
    const bh = h * (0.1 + r() * 0.3);
    g.fillRect(x0 + r() * (w - bw), y0 + r() * (h - bh), bw, bh);
  }
  g.globalAlpha = 1;

  // 긁힌 선·붓질
  for (let k = 0; k < 10; k++) scribble(g, r, x0, y0, w, h, 3 + Math.floor(r() * 4), dark ? '#f1ece0' : INK, 2 + r() * 7);
  for (let k = 0; k < 4; k++) scribble(g, r, x0, y0, w, h, 4, ['#ffffff', '#d8342c', '#2b64c6'][k % 3], 5 + r() * 10);

  // 모티프
  if (i % 3 === 0) mask(g, r, x0 + w * (0.3 + r() * 0.4), y0 + h * 0.5, Math.min(w, h) * 0.22);
  if (i % 2 === 1) crown(g, x0 + w * (0.25 + r() * 0.5), y0 + h * 0.32, Math.min(w, h) * 0.12, dark ? '#f2c230' : INK, i % 4 === 1 ? '#f2c230' : null);

  // 글자
  g.fillStyle = dark ? '#f4efe0' : INK;
  for (let k = 0; k < 5; k++) {
    g.save();
    g.translate(x0 + r() * w * 0.8, y0 + h * 0.15 + r() * h * 0.8);
    g.rotate((r() - 0.5) * 0.3);
    g.font = `800 ${20 + Math.floor(r() * 34)}px ${FONT}`;
    g.fillText(WORDS[Math.floor(r() * WORDS.length)], 0, 0);
    g.restore();
  }
  g.restore();
}

/** 작품 아틀라스: 4열 × 2행 (칸 번호 0~7) */
export const artAtlas = () =>
  canvasTexture(2048, 1024, (g) => {
    const r = seeded(41);
    for (let i = 0; i < 8; i++) paintCell(g, r, (i % 4) * 512, Math.floor(i / 4) * 512, 512, 512, i);
  });

/** 추상화한 인물 실루엣 (사진을 옮기지 않고 형태만) */
function figure(g, x, y, s, { skin, hair, shirt, bg0, bg1, w, h, x0, y0 }) {
  const bg = g.createLinearGradient(x0, y0, x0 + w, y0 + h);
  bg.addColorStop(0, bg0);
  bg.addColorStop(1, bg1);
  g.fillStyle = bg;
  g.fillRect(x0, y0, w, h);
  // 어깨
  g.fillStyle = shirt;
  g.beginPath();
  g.moveTo(x - s * 1.6, y + s * 2.6);
  g.quadraticCurveTo(x - s * 1.4, y + s * 1.1, x, y + s * 1.05);
  g.quadraticCurveTo(x + s * 1.4, y + s * 1.1, x + s * 1.6, y + s * 2.6);
  g.fill();
  // 목·얼굴
  g.fillStyle = skin;
  g.fillRect(x - s * 0.22, y + s * 0.5, s * 0.44, s * 0.65);
  g.beginPath();
  g.ellipse(x, y, s * 0.55, s * 0.72, 0, 0, Math.PI * 2);
  g.fill();
  // 머리카락
  g.fillStyle = hair;
  const r = seeded(9);
  for (let i = 0; i < 70; i++) {
    const a = Math.PI * (1.05 + r() * 0.9);
    const d = s * (0.55 + r() * 0.3);
    g.beginPath();
    g.arc(x + Math.cos(a) * d, y - s * 0.1 + Math.sin(a) * d * 1.05, s * (0.08 + r() * 0.1), 0, Math.PI * 2);
    g.fill();
  }
}

/** 인트로 월 (13 × 3.9m): 세피아 인물 그래픽 + 섹션 텍스트 */
export const introTexture = () =>
  canvasTexture(2048, 614, (g, w, h) => {
    g.fillStyle = '#b89572';
    g.fillRect(0, 0, w, h);
    figure(g, 360, 250, 150, {
      skin: '#6b4a33', hair: '#1f160f', shirt: '#9a8166', bg0: '#efe3cf', bg1: '#b99c7c', x0: 0, y0: 0, w: 760, h,
    });
    const fade = g.createLinearGradient(640, 0, 780, 0);
    fade.addColorStop(0, 'rgba(184,149,114,0)');
    fade.addColorStop(1, 'rgba(184,149,114,1)');
    g.fillStyle = fade;
    g.fillRect(640, 0, 140, h);
    g.fillStyle = '#2a1d12';
    g.font = `700 30px ${FONT}`;
    g.fillText('SECTION 01', 1000, 150);
    g.fillStyle = 'rgba(42,29,18,.55)';
    for (let i = 0; i < 12; i++) g.fillRect(1000, 190 + i * 22, 320 - (i % 4) * 24, 7);
  });

/** 입구 좌측 패널 (3.5 × 4.4m) */
export const logoTexture = () =>
  canvasTexture(512, 640, (g, w, h) => {
    g.fillStyle = '#121212';
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#f2f2f2';
    g.textAlign = 'center';
    g.font = `800 50px ${FONT}`;
    g.fillText('JEAN-MICHEL', w / 2, h * 0.24);
    g.font = `900 84px ${FONT}`;
    g.fillText('BASQUIAT', w / 2, h * 0.37);
    g.fillStyle = '#e9b23a';
    g.font = `600 22px ${FONT}`;
    g.fillText('장 미셸 바스키아', w / 2, h * 0.44);
  });

/** 입구 우측 포스터 패널 (6.6 × 4.2m) */
export const posterTexture = () =>
  canvasTexture(1400, 890, (g, w, h) => {
    g.fillStyle = '#141414';
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#e8e8e8';
    g.font = `800 62px ${FONT}`;
    g.fillText('JEAN-MICHEL BASQUIAT', 150, 120);
    g.fillStyle = '#e9b23a';
    g.font = `700 26px ${FONT}`;
    g.fillText('장 미셸 바스키아', 950, 92);
    g.fillStyle = '#f2f2f2';
    g.fillText('SEOUL EXHIBITION', 950, 126);

    // 중앙 사진 영역 (스튜디오 벽 + 앉은 인물 실루엣)
    const px = 400, py = 170, pw = 600, ph = 520;
    g.fillStyle = '#a9aaa6';
    g.fillRect(px, py, pw, ph);
    for (let i = 0; i < 6; i++) {
      g.fillStyle = i % 2 ? '#9a9b97' : '#b8b9b4';
      g.fillRect(px + i * 100, py, 60, ph * 0.72);
    }
    g.fillStyle = '#6d6a63';
    g.fillRect(px, py + ph * 0.72, pw, ph * 0.28);
    g.fillStyle = '#b3261e';
    g.fillRect(px + 110, py + 290, 110, 90); // 의자
    g.fillRect(px + 420, py + 380, 110, 120); // 가방
    g.fillStyle = '#18181a';
    g.beginPath();
    g.ellipse(px + 190, py + 210, 34, 42, 0, 0, Math.PI * 2);
    g.fill();
    g.fillRect(px + 140, py + 250, 110, 150);
    g.fillRect(px + 220, py + 360, 200, 44);
    g.fillStyle = '#0d0d0d';
    g.beginPath();
    g.ellipse(px + 430, py + 170, 55, 60, 0, 0, Math.PI * 2);
    g.fill();
    g.fillRect(px + 395, py + 220, 70, 150);
    g.fillStyle = '#f3efe4';
    g.fillRect(px + 400, py + 175, 60, 14);

    // 후원사 로고 자리
    g.fillStyle = 'rgba(230,230,230,.75)';
    for (let i = 0; i < 9; i++) g.fillRect(150 + i * 125, 790, 80, 16);
    g.font = `700 22px ${FONT}`;
    g.fillText('KYVIKOS', 150, 760);
  });

/** 전시 동선 끝 프로젝션 (4.2 × 2.4m) */
export const projectionTexture = () =>
  canvasTexture(1024, 585, (g, w, h) => {
    figure(g, 540, 250, 120, {
      skin: '#5a3b28', hair: '#16100b', shirt: '#c9302c', bg0: '#9fcf6a', bg1: '#6aa24a', x0: 0, y0: 0, w, h,
    });
    g.fillStyle = '#d9c9a4';
    g.fillRect(0, 0, 300, h);
    g.fillStyle = 'rgba(140,110,70,.5)';
    for (let y = 0; y < h; y += 40) for (let x = (y / 40) % 2 ? 20 : 0; x < 300; x += 40) g.fillRect(x, y, 18, 18);
    g.fillStyle = 'rgba(0,0,0,.55)';
    g.fillRect(260, h - 70, 520, 40);
    g.fillStyle = '#fff';
    g.fillRect(290, h - 55, 460, 10);
  });

/** 미디어아트 룸 스크린 (3.6 × 2.1m) */
export const screenTexture = () =>
  canvasTexture(1024, 600, (g, w, h) => {
    const bg = g.createLinearGradient(0, 0, w, h);
    bg.addColorStop(0, '#f4f8ff');
    bg.addColorStop(1, '#c9dcff');
    g.fillStyle = bg;
    g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(120,140,170,.35)';
    g.fillRect(w * 0.47, 0, 6, h);
    for (let y = 30; y < h; y += 28) g.fillRect(0, y, w, 1);
    g.fillStyle = '#1c2230';
    g.font = `600 22px ${FONT}`;
    g.fillText('MEDIA ART', w * 0.6, h * 0.42);
  });

/** 아트샵 곡면 벽 (14.5 × 3.6m): 흰 벽 + 마룬 띠 + 굿즈 */
export const shopWallTexture = () =>
  canvasTexture(4096, 1017, (g, w, h) => {
    const r = seeded(17);
    g.fillStyle = '#f3f2ef';
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#7d1f26';
    g.fillRect(0, h * 0.7, w, h * 0.3);

    // 포스터 썸네일 + 타이틀
    for (let i = 0; i < 6; i++) {
      g.fillStyle = ['#e9b23a', '#2f5fb8', '#efe4c8', '#c7412f', '#1c1b19', '#d9d2bf'][i];
      g.fillRect(260 + i * 120, 190, 96, 130);
      scribble(g, r, 260 + i * 120, 190, 96, 130, 5, i === 4 ? '#fff' : INK, 4);
    }
    g.fillStyle = '#1a1a1a';
    g.font = `800 60px ${FONT}`;
    g.fillText('JEAN-MICHEL', 1180, 220);
    g.font = `900 120px ${FONT}`;
    g.fillText('BASQUIAT', 1180, 335);
    g.fillStyle = '#7d1f26';
    g.font = `600 34px ${FONT}`;
    g.fillText('ART SHOP', 1190, 390);

    // 티셔츠·후디
    const shirt = (x, y, s, hood) => {
      g.fillStyle = '#1b1b1d';
      g.beginPath();
      if (hood) {
        g.moveTo(x - s * 0.3, y - s * 0.55);
        g.quadraticCurveTo(x, y - s * 0.95, x + s * 0.3, y - s * 0.55);
      } else g.moveTo(x - s * 0.18, y - s * 0.5);
      g.lineTo(x + s * 0.5, y - s * 0.45);
      g.lineTo(x + s * 0.62, y - s * 0.1);
      g.lineTo(x + s * 0.38, y - s * 0.05);
      g.lineTo(x + s * 0.38, y + s * 0.55);
      g.lineTo(x - s * 0.38, y + s * 0.55);
      g.lineTo(x - s * 0.38, y - s * 0.05);
      g.lineTo(x - s * 0.62, y - s * 0.1);
      g.lineTo(x - s * 0.5, y - s * 0.45);
      g.closePath();
      g.fill();
      scribble(g, r, x - s * 0.25, y - s * 0.25, s * 0.5, s * 0.55, 6, '#f1ece0', 4);
      if (r() > 0.5) crown(g, x, y - s * 0.1, s * 0.12, '#f2c230');
    };
    for (let i = 0; i < 6; i++) shirt(2150 + i * 190, 610, 200, false);
    for (let i = 0; i < 4; i++) shirt(3300 + i * 200, 690, 240, true);
    // 스케이트 데크
    for (let i = 0; i < 3; i++) {
      g.fillStyle = '#222';
      g.beginPath();
      g.roundRect(3450 + i * 80, 120, 66, 300, 33);
      g.fill();
      scribble(g, r, 3455 + i * 80, 140, 56, 260, 6, '#eee', 3);
    }
    // 모니터
    g.fillStyle = '#18191c';
    g.fillRect(1850, 250, 230, 150);
  });

/** 아트샵 입구 대형 사진 월 (6 × 3.8m) */
export const photoWallTexture = () =>
  canvasTexture(1024, 648, (g, w, h) => {
    g.fillStyle = '#6a5140';
    g.fillRect(0, 0, w, h);
    const r = seeded(23);
    for (let x = 0; x < w; x += 46) {
      g.fillStyle = `rgb(${90 + r() * 40},${66 + r() * 30},${50 + r() * 25})`;
      g.fillRect(x, 0, 42, h);
      g.fillStyle = 'rgba(30,20,12,.35)';
      for (let k = 0; k < 6; k++) g.fillRect(x + r() * 40, r() * h, 2, 30 + r() * 80);
    }
    g.save();
    g.translate(560, 0);
    figure(g, 0, 200, 110, {
      skin: '#5a3b28', hair: '#1a120c', shirt: '#4fae6a', bg0: 'rgba(0,0,0,0)', bg1: 'rgba(0,0,0,0)', x0: 0, y0: 0, w: 0, h: 0,
    });
    g.fillStyle = '#4fae6a';
    g.fillRect(-176, 486, 352, 170);
    g.restore();
  });

/** 로비 토템 (1.5 × 3m) */
export const totemTexture = () =>
  canvasTexture(300, 600, (g, w, h) => {
    const r = seeded(31);
    g.fillStyle = '#121212';
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#eee';
    g.textAlign = 'center';
    g.font = `800 24px ${FONT}`;
    g.fillText('JEAN-MICHEL', w / 2, 60);
    g.font = `900 40px ${FONT}`;
    g.fillText('BASQUIAT', w / 2, 100);
    g.fillStyle = '#e9c24a';
    g.fillRect(30, 130, w - 60, 380);
    crown(g, 100, 220, 34, INK);
    crown(g, 200, 220, 34, INK);
    g.fillStyle = '#c7412f';
    g.fillRect(60, 260, 80, 120);
    g.fillRect(160, 260, 80, 120);
    scribble(g, r, 40, 400, w - 80, 100, 10, INK, 4);
    g.fillStyle = '#eee';
    g.font = `600 16px ${FONT}`;
    g.fillText('DDP · SEOUL', w / 2, 555);
  });
