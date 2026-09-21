"""황룡원 건물 표면 텍스처 (PIL) — assets-src/shots 에 PNG 로 저장

  python3 scripts/blender/apec_site_graphics.py

- apec_rail.png      중도타워 층마다 두른 금빛 卍자 난간 (1칸 = 가로 4m × 세로 1.1m)
- apec_yeonsu.png    연수동 외벽 한 칸: 밝은 회색 화강석 판 + 층마다 긴 창 (가로 8m × 세로 4m)
- apec_hanji.png     한옥 창호(띠살문): 붉은 목재 틀 + 불 켜진 한지
- apec_fret.png      신평루·연수동 한옥 난간의 붉은 계자 난간 (구름 무늬 풍혈)
- apec_stage_floor.png  무대 바닥: 흰 무대면 + 파란 고보 원 (드론 사진)
- apec_ui_*.png        콘솔 화면: 조명 콘솔(보라 격자) / 음향 콘솔(채널 미터) / 영상 스위처(멀티뷰)
"""
import math
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


# ── 무대 바닥 (18m × 9m) ─────────────────────────────────────
def stage_floor():
    W, H = 2048, 1024
    im = Image.new('RGB', (W, H), (150, 160, 178))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 114):                       # 무대 판 이음새 (1m)
        d.line([x, 0, x, H], fill=(128, 136, 152), width=2)
    for y in range(0, H, 228):
        d.line([0, y, W, y], fill=(128, 136, 152), width=2)
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    random.seed(8)
    for _ in range(26):                               # 파란 무빙라이트 고보
        cx, cy, r = random.randint(80, W - 80), random.randint(200, H - 60), random.randint(50, 95)
        g.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=(40, 90, 230))
        g.ellipse([cx - r * 0.45, cy - r * 0.35, cx + r * 0.45, cy + r * 0.35], fill=(90, 140, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    im = Image.blend(im, Image.eval(glow, lambda v: min(255, v)), 0.0)
    px, gp = im.load(), glow.load()
    for y in range(H):
        for x in range(W):
            a, b = px[x, y], gp[x, y]
            px[x, y] = tuple(int(min(255, a[i] * (1 - 0.0035 * b[2]) + b[i] * 0.95)) for i in range(3))
    noise(im, 4).save(OUT / 'apec_stage_floor.png')


# ── 콘솔 화면 (3칸: 조명 / 음향 / 영상) ─────────────────────────
def console_ui():
    W, H = 1536, 512
    im = Image.new('RGB', (W, H), (8, 8, 14))
    d = ImageDraw.Draw(im)
    # 조명 콘솔: 보라 배경에 실행 버튼 격자 + 파란 큐 리스트
    d.rectangle([0, 0, 511, H], fill=(70, 40, 150))
    for gx in range(8):
        for gy in range(6):
            c = random.choice([(150, 110, 230), (90, 160, 250), (230, 200, 90), (60, 40, 120)])
            d.rectangle([14 + gx * 62, 60 + gy * 72, 66 + gx * 62, 120 + gy * 72], fill=c)
    d.rectangle([0, 0, 511, 44], fill=(30, 30, 60))
    # 음향 콘솔: 채널 미터
    d.rectangle([512, 0, 1023, H], fill=(20, 26, 40))
    for ch in range(24):
        x = 530 + ch * 20
        lvl = random.randint(80, 380)
        d.rectangle([x, H - 40 - lvl, x + 12, H - 40], fill=(60, 220, 110))
        d.rectangle([x, H - 40 - lvl, x + 12, H - 40 - lvl + 20], fill=(240, 210, 60))
    d.rectangle([512, 0, 1023, 40], fill=(50, 70, 110))
    # 영상 스위처: 멀티뷰 4분할
    d.rectangle([1024, 0, W, H], fill=(10, 10, 16))
    for i, c in enumerate([(210, 60, 90), (60, 90, 220), (120, 60, 200), (40, 40, 60)]):
        x0, y0 = 1034 + (i % 2) * 252, 10 + (i // 2) * 250
        d.rectangle([x0, y0, x0 + 240, y0 + 240], fill=c)
        d.rectangle([x0 + 60, y0 + 70, x0 + 180, y0 + 150], fill=(250, 220, 200))
    im = im.filter(ImageFilter.GaussianBlur(1.0))
    for i, name in enumerate(('light', 'audio', 'video')):
        im.crop((i * 512, 0, i * 512 + 512, H)).save(OUT / f'apec_ui_{name}.png')


# ── 연수동 창 안쪽 (창 하나 = 가로 7m × 세로 2.7m, 4칸) ─────────────
def room_glass(tag, seed):
    W, H = 1024, 400
    im = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    random.seed(seed)
    for k in range(4):
        x0 = k * 256
        lit = random.random() < 0.65
        top, bot = ((236, 176, 104), (170, 110, 58)) if lit else ((40, 46, 56), (22, 26, 32))
        for y in range(H):
            t = y / H
            d.line([x0, y, x0 + 255, y], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
        if lit:   # 반쯤 친 커튼 주름
            cw = random.randint(40, 90)
            for side in (0, 1):
                for x in range(cw):
                    xx = x0 + (x if side == 0 else 255 - x)
                    v = 0.75 + 0.25 * math.sin(x * 0.45)
                    d.line([xx, 0, xx, H], fill=(int(250 * v), int(226 * v), int(186 * v)))
    for k in range(5):   # 창틀·창살
        x = min(W - 7, k * 256)
        d.rectangle([x - 6, 0, x + 6, H], fill=(70, 72, 76))
    d.rectangle([0, 0, W, 10], fill=(70, 72, 76))
    d.rectangle([0, H - 10, W, H], fill=(70, 72, 76))
    d.rectangle([0, 96, W, 104], fill=(70, 72, 76))
    im.filter(ImageFilter.GaussianBlur(0.8)).save(OUT / f'apec_room_{tag}.png')


# ── 솔잎 카드 (투명 배경, 잔가지에서 사방으로 뻗은 솔잎) ─────────────
def pine_needles():
    W = H = 512
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    random.seed(21)
    twig = [(40 + t * 430, 300 - t * 90 + math.sin(t * 5) * 10) for t in [k / 20 for k in range(21)]]
    d.line(twig, fill=(92, 58, 34, 255), width=6)
    for k in range(420):
        t = random.random()
        i = min(19, int(t * 20))
        bx = twig[i][0] + (twig[i + 1][0] - twig[i][0]) * (t * 20 - i)
        by = twig[i][1] + (twig[i + 1][1] - twig[i][1]) * (t * 20 - i)
        a = random.uniform(-math.pi, math.pi)
        L = random.uniform(40, 95) * (0.6 + 0.4 * math.sin(t * math.pi))
        ex, ey = bx + math.cos(a) * L, by + math.sin(a) * L * 0.8
        g = random.randint(70, 118)
        d.line([(bx, by), (ex, ey)], fill=(int(g * 0.38), g, int(g * 0.42), 255), width=2)
    im.save(OUT / 'apec_pine_needles.png')


# ── 활엽수 잎 카드 (투명 배경, 잔가지에 달린 잎들) ────────────────
def leaves():
    W = H = 512
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    random.seed(33)
    for _ in range(6):   # 잔가지
        x0, y0 = random.randint(60, 450), random.randint(60, 450)
        d.line([(256, 470), (x0, y0)], fill=(70, 52, 36, 255), width=4)
    for _ in range(520):
        cx, cy = random.gauss(256, 105), random.gauss(240, 100)
        if not (12 < cx < 500 and 12 < cy < 500):
            continue
        a = random.uniform(0, math.pi)
        L, w = random.uniform(16, 30), random.uniform(7, 12)
        g = random.randint(62, 120)
        col = (int(g * random.uniform(0.45, 0.62)), g, int(g * random.uniform(0.3, 0.45)), 255)
        pts = []
        for k in range(12):
            t = k / 12 * 2 * math.pi
            px, py = math.cos(t) * L, math.sin(t) * w * (1 - 0.3 * math.cos(t))
            pts.append((cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)))
        d.polygon(pts, fill=col)
    im.save(OUT / 'apec_leaves.png')


pine_needles()
leaves()
rail()
for tag, seed in (('a', 12), ('b', 29), ('c', 41)):
    room_glass(tag, seed)
stage_floor()
console_ui()
yeonsu()
hanji()
fret()
print('graphics ->', OUT)
