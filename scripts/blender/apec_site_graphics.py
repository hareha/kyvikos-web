"""황룡원 건물 표면 텍스처 (PIL) — assets-src/shots 에 PNG 로 저장

  python3 scripts/blender/apec_site_graphics.py

- apec_rail.png      중도타워 층마다 두른 금빛 卍자 난간 (1칸 = 가로 4m × 세로 1.1m)
- apec_yeonsu.png    연수동 외벽 한 칸: 밝은 회색 화강석 판 + 층마다 긴 창 (가로 8m × 세로 4m)
- apec_hanji.png     한옥 창호(띠살문): 붉은 목재 틀 + 불 켜진 한지
- apec_fret.png      신평루·연수동 한옥 난간의 붉은 계자 난간 (구름 무늬 풍혈)
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / 'assets-src' / 'shots'
random.seed(3)


def noise(img, amount=10):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = px[x, y][:3]
            n = random.randint(-amount, amount)
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


# ── 금빛 卍자 난간 ───────────────────────────────────────────
def rail():
    W, H = 1024, 280
    gold, dark_gold, bg = (226, 176, 72), (150, 104, 36), (58, 22, 14)
    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 26], fill=gold)                  # 난간 두겁대
    d.rectangle([0, 26, W, 32], fill=dark_gold)
    d.rectangle([0, H - 30, W, H], fill=gold)              # 하방
    d.rectangle([0, H - 36, W, H - 30], fill=dark_gold)
    for x in range(0, W + 1, 256):                         # 난간 동자
        d.rectangle([x - 12, 0, x + 12, H], fill=gold)
    # 卍자 살: 칸마다 卍 무늬를 이어 붙인 격자
    s, c = 9, 64
    for cx in range(12, W, 256):
        for gx in range(4):
            for gy in range(3):
                x0, y0 = cx + 18 + gx * 57, 44 + gy * 67
                m, h = x0 + 24, y0 + 28
                d.rectangle([x0, h - s // 2, x0 + 48, h + s // 2], fill=gold)      # 가로
                d.rectangle([m - s // 2, y0, m + s // 2, y0 + 56], fill=gold)      # 세로
                d.rectangle([m, y0, x0 + 48, y0 + s], fill=gold)                   # 네 팔
                d.rectangle([x0 + 48 - s, h, x0 + 48, y0 + 56], fill=gold)
                d.rectangle([x0, y0 + 56 - s, m, y0 + 56], fill=gold)
                d.rectangle([x0, y0, x0 + s, h], fill=gold)
    im = noise(im, 6).filter(ImageFilter.GaussianBlur(0.6))
    im.save(OUT / 'apec_rail.png')


# ── 연수동 외벽 (화강석 판 + 창) ─────────────────────────────────
def yeonsu():
    W, H = 1024, 512            # 8m × 4m → 1m = 128px
    im = Image.new('RGB', (W, H), (205, 204, 198))
    d = ImageDraw.Draw(im)
    # 판석 줄눈: 가로 1.2m × 세로 0.6m
    for row, y in enumerate(range(0, H, 77)):
        shift = 0 if row % 2 == 0 else 77
        for x in range(-shift, W, 154):
            tone = random.randint(-14, 10)
            d.rectangle([x + 2, y + 2, x + 152, y + 75], fill=(205 + tone, 204 + tone, 197 + tone))
    im = noise(im, 7)
    d = ImageDraw.Draw(im)
    # 창: 폭 6.4m, 높이 2.3m, 세로 창살 1.6m 간격
    x0, x1, y0, y1 = 102, 922, 118, 412
    d.rectangle([x0 - 10, y0 - 10, x1 + 10, y1 + 10], fill=(150, 150, 146))
    lit = random.random() < 0.7
    glass_top = (212, 150, 78) if lit else (52, 60, 70)
    glass_bot = (160, 98, 46) if lit else (28, 34, 42)
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0)
        c = tuple(int(glass_top[i] * (1 - t) + glass_bot[i] * t) for i in range(3))
        d.line([x0, y, x1, y], fill=c)
    for x in range(x0, x1 + 1, 205):
        d.rectangle([x - 6, y0, x + 6, y1], fill=(96, 98, 100))
    d.rectangle([x0, y0 + 60, x1, y0 + 68], fill=(96, 98, 100))
    d.rectangle([x0 - 12, y1 + 6, x1 + 12, y1 + 22], fill=(226, 225, 220))   # 창대
    im.filter(ImageFilter.GaussianBlur(0.5)).save(OUT / 'apec_yeonsu.png')


# ── 띠살 창호 (불 켜진 한지) ────────────────────────────────────
def hanji():
    W, H = 512, 512
    im = Image.new('RGB', (W, H), (255, 214, 150))
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = 0.85 + 0.15 * (1 - abs(y - H * 0.45) / H)
        d.line([0, y, W, y], fill=(int(255 * k), int(206 * k), int(140 * k)))
    frame = (120, 38, 22)
    # 문 두 짝
    for i in range(2):
        x0 = i * 256
        d.rectangle([x0, 0, x0 + 255, 18], fill=frame)
        d.rectangle([x0, H - 60, x0 + 255, H], fill=frame)        # 궁판
        d.rectangle([x0, 0, x0 + 14, H], fill=frame)
        d.rectangle([x0 + 241, 0, x0 + 255, H], fill=frame)
        for x in range(x0 + 14, x0 + 241, 28):                   # 세로 살
            d.rectangle([x, 18, x + 3, H - 60], fill=frame)
        for y in (80, 200, 320, 420):                            # 띠
            d.rectangle([x0, y, x0 + 255, y + 14], fill=frame)
            for yy in range(y - 16, y + 30, 11):
                d.rectangle([x0 + 14, yy, x0 + 241, yy + 2], fill=frame)
    im.filter(ImageFilter.GaussianBlur(0.4)).save(OUT / 'apec_hanji.png')


# ── 붉은 계자 난간 (풍혈) ─────────────────────────────────────
def fret():
    W, H = 1024, 256
    red, dark = (176, 58, 34), (80, 22, 12)
    im = Image.new('RGB', (W, H), dark)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 34], fill=red)
    d.rectangle([0, H - 40, W, H], fill=red)
    for x in range(0, W + 1, 256):
        d.rectangle([x - 16, 0, x + 16, H], fill=red)
    for x in range(16, W, 256):
        d.rectangle([x, 34, x + 224, H - 40], fill=red)
        # 구름 모양 풍혈
        cx, cy = x + 112, 128
        d.ellipse([cx - 76, cy - 30, cx - 4, cy + 30], fill=dark)
        d.ellipse([cx + 4, cy - 30, cx + 76, cy + 30], fill=dark)
        d.ellipse([cx - 30, cy - 38, cx + 30, cy + 8], fill=dark)
    noise(im, 6).filter(ImageFilter.GaussianBlur(0.6)).save(OUT / 'apec_fret.png')


rail()
yeonsu()
hanji()
fret()
print('graphics ->', OUT)
