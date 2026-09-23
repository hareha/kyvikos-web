"""LOCAL POWER 외부 입구 그래픽 (현장 사진 real-entrance.jpg 기준, PIL)

  python3 scripts/blender/localpower_graphics.py

- lp_g_exhibit.png   'EXHIBITION IN SEOUL 서울 전시' 주황 벽 (10m × 4.5m, 오른쪽): 흰 제목 + 흰 테두리 설명 박스 3개
- lp_g_vertical.png  세로 'Hong Kong Fashion in Seoul' + 큰 'LOCAL 2025 POWER' 주황 벽 (8m × 4.5m)
- lp_g_red.png       빨간 패널 (왼쪽): 선버스트 + 'LOCAL 2025 POWER' + 상단 흰 후원 띠 (6m × 3.6m)
- lp_g_sponsor.png   입구 위 흰 후원사 로고 판
- lp_g_warning.png   'WARNING 수조 월기 금지' 안내판
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parents[2] / 'assets-src' / 'shots'
DIN = '/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf'
KO = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
random.seed(4)


def grad(w, h, c0, c1, horizontal=True):
    im = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(im)
    n = w if horizontal else h
    for i in range(n):
        t = i / n
        c = tuple(int(c0[k] * (1 - t) + c1[k] * t) for k in range(3))
        d.line([i, 0, i, h] if horizontal else [0, i, w, i], fill=c)
    return im


def lines_of_text(d, x, y, w, rows, col=(255, 255, 255), h=6, gap=13):
    for r in range(rows):
        ww = int(w * random.uniform(0.75, 1.0))
        d.rectangle([x, y + r * gap, x + ww, y + r * gap + h], fill=col)


def logo_row(d, x, y, n, span, col=(90, 90, 90)):
    for i in range(n):
        lx = x + i * span / n
        d.rounded_rectangle([lx, y, lx + span / n * 0.7, y + 22], 6, fill=col)


def exhibit():
    W, H = 2200, 990
    im = grad(W, H, (242, 108, 38), (226, 80, 30))
    d = ImageDraw.Draw(im)
    # 흐린 선 패턴 (사진 오른쪽 위의 가는 도시 선화)
    for _ in range(60):
        x0, y0 = random.randint(1100, W), random.randint(0, 260)
        d.line([x0, y0, x0 + random.randint(-80, 80), y0 + random.randint(10, 80)], fill=(250, 140, 80), width=2)
    d.text((120, 120), 'EXHIBITION IN SEOUL', font=ImageFont.truetype(DIN, 130), fill='white')
    d.text((120, 260), '서울 전시', font=ImageFont.truetype(KO, 100, index=6), fill='white')
    lines_of_text(d, 120, 420, 1900, 2, h=8, gap=22)
    for k, (title, ko) in enumerate((('URBAN JUNGLE', '도시 정글'), ('RUNWAY TO TOMORROW', '내일로 향하는 런웨이'), ('SOUL OF LOCAL POWER', '로컬 파워의 소울'))):
        y = 520 + k * 150
        d.rectangle([120, y, 2080, y + 135], outline='white', width=5)
        d.rectangle([120, y, 2080, y + 34], fill='white')
        d.text((140, y + 4), f'{title}   {ko}', font=ImageFont.truetype(KO, 26, index=6), fill=(226, 80, 30))
        lines_of_text(d, 140, y + 50, 1900, 5, h=6, gap=15)
    im.save(OUT / 'lp_g_exhibit.png')


def vertical():
    W, H = 1760, 990
    im = grad(W, H, (236, 92, 32), (244, 112, 40))
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(DIN, 430)
    d.text((520, 60), 'LOCAL', font=big, fill='white')
    d.text((520, 500), 'POWER', font=big, fill='white')
    d.text((1370, 120), '20', font=ImageFont.truetype(DIN, 210), fill='white')
    d.text((1370, 310), '25', font=ImageFont.truetype(DIN, 210), fill='white')
    side = Image.new('RGBA', (900, 110), (0, 0, 0, 0))
    ImageDraw.Draw(side).text((0, 0), 'Hong Kong Fashion In Seoul', font=ImageFont.truetype(DIN, 100), fill='white')
    im.paste(side.rotate(90, expand=True), (370, 60), side.rotate(90, expand=True))
    d.text((60, 560), 'LOCAL POWER 2025\nHONG KONG\nFASHION IN SEOUL', font=ImageFont.truetype(DIN, 40), fill='white')
    d.text((60, 720), '홍콩 패션 인 서울', font=ImageFont.truetype(KO, 30, index=6), fill='white')
    lines_of_text(d, 60, 780, 250, 12, h=4, gap=13)
    im.save(OUT / 'lp_g_vertical.png')


def red():
    W, H = 1320, 800
    im = grad(W, H, (214, 40, 36), (200, 26, 28))
    d = ImageDraw.Draw(im)
    # 왼쪽 선버스트
    burst = Image.new('RGB', (W, H), (214, 40, 36))
    b = ImageDraw.Draw(burst)
    cx, cy = -60, 520
    for k in range(60):
        a = -1.2 + k * 0.045
        c = random.choice([(255, 210, 60), (255, 140, 40), (255, 90, 120), (255, 240, 200)])
        b.polygon([(cx, cy), (cx + 900 * math.cos(a), cy + 900 * math.sin(a)), (cx + 900 * math.cos(a + 0.02), cy + 900 * math.sin(a + 0.02))], fill=c)
    burst = burst.filter(ImageFilter.GaussianBlur(3))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rectangle([0, 150, 300, H], fill=255)
    im.paste(burst, (0, 0), mask.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 150], fill=(250, 250, 248))
    logo_row(d, 60, 40, 9, 1200, (120, 120, 130))
    logo_row(d, 60, 90, 11, 1200, (160, 160, 170))
    d.text((520, 290), 'LOCAL', font=ImageFont.truetype(DIN, 190), fill='white')
    d.text((520, 480), 'POWER', font=ImageFont.truetype(DIN, 190), fill='white')
    d.text((930, 300), '20\n25', font=ImageFont.truetype(DIN, 95), fill='white', spacing=0)
    side = Image.new('RGBA', (380, 60), (0, 0, 0, 0))
    ImageDraw.Draw(side).text((0, 0), 'Hong Kong Fashion In Seoul', font=ImageFont.truetype(DIN, 44), fill='white')
    im.paste(side.rotate(90, expand=True), (455, 290), side.rotate(90, expand=True))
    im.save(OUT / 'lp_g_red.png')


def sponsor():
    W, H = 1400, 880      # 입구 위 흰 판 3.5m × 2.2m
    im = Image.new('RGB', (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    for r in range(8):
        logo_row(d, 70, 60 + r * 102, random.randint(3, 6), 1260, random.choice([(90, 150, 200), (200, 60, 60), (110, 110, 120), (60, 140, 90)]))
    im.save(OUT / 'lp_g_sponsor.png')


def warning():
    W, H = 400, 560
    im = Image.new('RGB', (W, H), (160, 20, 30))
    d = ImageDraw.Draw(im)
    d.text((95, 20), 'WARNING', font=ImageFont.truetype(DIN, 70), fill='white')
    d.rectangle([30, 110, 370, 530], fill='white')
    d.ellipse([140, 150, 260, 270], outline=(200, 30, 40), width=12)
    d.line([155, 255, 245, 165], fill=(200, 30, 40), width=12)
    d.text((110, 300), '수조 월기 금지', font=ImageFont.truetype(KO, 40, index=6), fill=(30, 30, 30))
    lines_of_text(d, 60, 380, 280, 6, col=(120, 120, 120), h=6, gap=20)
    im.save(OUT / 'lp_g_warning.png')


def street():
    """도로 쪽 박공면 전체 가림막 (소개서 거리 입면 시뮬레이션: 왼쪽 선버스트, 오른쪽 LOCAL 2025 POWER) 20.6m × 6.3m"""
    W, H = 2060, 630
    im = grad(W, H, (232, 84, 30), (205, 40, 28))
    burst = Image.new('RGB', (W, H), (240, 110, 40))
    b = ImageDraw.Draw(burst)
    cx, cy = 560, 330
    for k in range(140):
        a = k / 140 * 2 * math.pi
        c = random.choice([(255, 214, 90), (255, 160, 60), (255, 120, 40), (255, 236, 170), (250, 96, 40)])
        da = random.uniform(0.012, 0.03)
        b.polygon([(cx, cy), (cx + 1400 * math.cos(a), cy + 1400 * math.sin(a)), (cx + 1400 * math.cos(a + da), cy + 1400 * math.sin(a + da))], fill=c)
    burst = burst.filter(ImageFilter.GaussianBlur(2))
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=255)
    burst.paste((255, 250, 225), (0, 0), glow.filter(ImageFilter.GaussianBlur(45)))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - 800, cy - 620, cx + 520, cy + 620], fill=255)
    im.paste(burst, (0, 0), mask.filter(ImageFilter.GaussianBlur(140)))
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(DIN, 270)
    d.text((1250, 80), 'LOCAL', font=big, fill='white')
    d.text((1250, 330), 'POWER', font=big, fill='white')
    lx = 1250 + d.textlength('LOCAL', font=big) + 18
    for k, t in enumerate(('20', '25')):
        d.text((lx, 100 + k * 118), t, font=ImageFont.truetype(DIN, 112), fill='white')
    side = Image.new('RGBA', (500, 70), (0, 0, 0, 0))
    ImageDraw.Draw(side).text((0, 0), 'Hong Kong Fashion In Seoul', font=ImageFont.truetype(DIN, 58), fill='white')
    im.paste(side.rotate(90, expand=True), (1170, 90), side.rotate(90, expand=True))
    im.save(OUT / 'lp_g_street.png')


def signs():
    """홍콩 간판 포토월: 현장 사진(소개서 image41)에서 판 정면만 잘라 원근을 편다"""
    src = Path(__file__).resolve().parents[2] / 'public' / 'images' / 'localpower' / 'real-photowall.jpg'
    im = Image.open(src).convert('RGB')
    quad = (343, 174, 346, 892, 1443, 890, 1441, 170)       # 좌상·좌하·우하·우상
    im.transform((2048, 1330), Image.QUAD, quad, Image.BICUBIC).save(OUT / 'lp_g_signs.png')


for f in (exhibit, vertical, red, sponsor, warning, street, signs):
    f()
print('ok')
