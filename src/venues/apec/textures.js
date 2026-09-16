import { canvasTexture, seeded, FONT } from '../../scene/kit.js';

/** 무대 LED월 (14 × 5.5m) */
export const ledTexture = () =>
  canvasTexture(2048, 806, (g, w, h) => {
    const r = seeded(7);
    const bg = g.createLinearGradient(0, 0, w, h);
    bg.addColorStop(0, '#06123a');
    bg.addColorStop(0.55, '#0c2a78');
    bg.addColorStop(1, '#050d2b');
    g.fillStyle = bg;
    g.fillRect(0, 0, w, h);

    for (let i = 0; i < 900; i++) {
      g.fillStyle = `rgba(200,220,255,${0.2 + r() * 0.8})`;
      const s = r() * 2.4;
      g.fillRect(r() * w, r() * h, s, s);
    }

    g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 5; i++) {
      const x = 1250 + i * 120;
      const grd = g.createLinearGradient(x, 0, x + 260, h);
      grd.addColorStop(0, 'rgba(120,80,255,0)');
      grd.addColorStop(0.5, i % 2 ? 'rgba(255,90,200,.28)' : 'rgba(90,160,255,.3)');
      grd.addColorStop(1, 'rgba(120,80,255,0)');
      g.fillStyle = grd;
      g.beginPath();
      g.moveTo(x, 0);
      g.lineTo(x + 60, 0);
      g.lineTo(x - 240, h);
      g.lineTo(x - 300, h);
      g.fill();
    }
    g.globalCompositeOperation = 'source-over';

    g.fillStyle = '#fff';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.font = `800 190px ${FONT}`;
    g.fillText('APEC', w / 2, h * 0.38);
    g.font = `500 64px ${FONT}`;
    g.fillText('CEO SUMMIT KOREA 2025', w / 2, h * 0.58);
    g.font = `600 44px ${FONT}`;
    g.fillStyle = 'rgba(210,225,255,.85)';
    g.fillText('SPECIAL DINNER  ·  GYEONGJU', w / 2, h * 0.74);
  });

/** 무대 전면 스커트 배너 (18 × 0.9m) */
export const bannerTexture = () =>
  canvasTexture(2048, 102, (g, w, h) => {
    g.fillStyle = '#0a1446';
    g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(230,238,255,.9)';
    g.font = `600 40px ${FONT}`;
    g.textBaseline = 'middle';
    for (let x = 30; x < w; x += 680) g.fillText('APEC CEO SUMMIT KOREA 2025  ·', x, h / 2);
  });

/** 중도타워 창호 (발광 맵) */
export const windowTexture = () =>
  canvasTexture(256, 128, (g, w, h) => {
    const r = seeded(3);
    g.fillStyle = '#0b0704';
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 4; i++) {
      const x = i * 64 + 6;
      const a = 0.55 + r() * 0.45;
      const grd = g.createLinearGradient(0, 10, 0, h - 10);
      grd.addColorStop(0, `rgba(255,214,150,${a})`);
      grd.addColorStop(1, `rgba(255,150,70,${a})`);
      g.fillStyle = grd;
      g.fillRect(x, 12, 52, h - 24);
      g.fillStyle = '#1b120c';
      for (let m = 1; m < 4; m++) g.fillRect(x + m * 13 - 1, 12, 2, h - 24);
      g.fillRect(x, h / 2 - 1, 52, 3);
    }
  });

/** 입구 토템 사이니지 (1.5 × 4.4m) */
export const totemTexture = () =>
  canvasTexture(256, 751, (g, w, h) => {
    const bg = g.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, '#1a2a7a');
    bg.addColorStop(1, '#0a103a');
    g.fillStyle = bg;
    g.fillRect(0, 0, w, h);
    g.fillStyle = '#fff';
    g.textAlign = 'center';
    g.font = `800 64px ${FONT}`;
    g.fillText('APEC', w / 2, h * 0.3);
    g.font = `500 24px ${FONT}`;
    g.fillText('CEO SUMMIT', w / 2, h * 0.36);
    g.fillText('KOREA 2025', w / 2, h * 0.4);
    g.font = `600 22px ${FONT}`;
    g.fillStyle = 'rgba(210,225,255,.8)';
    g.fillText('SPECIAL DINNER', w / 2, h * 0.8);
  });
