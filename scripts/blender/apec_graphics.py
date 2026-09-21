"""APEC 현장 그래픽 (실제 사진 기준) — LED월, 무대 전면 판, 사인월
  python3 scripts/blender/apec_graphics.py  →  assets-src/shots/apec_real_*.png

공식 로고는 재현하지 않고, 사진 속 배치(좌우 중계 화면 + 가운데 로고 + 하단 로고 띠)와 색만 맞춘다.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets-src', 'shots')
os.makedirs(OUT, exist_ok=True)
FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
random.seed(3)


def font(size, bold=True):
    return ImageFont.truetype(FONT, size, index=6 if bold else 2)


def logo_mark(d, cx, cy, s):
    """사진 속 다색 로고 자리 — 둥근 사각 조각 네 개로 대체"""
    colors = ['#2fb6a3', '#f2c230', '#e8453c', '#7b5fd6']
    offsets = [(-0.55, -0.45), (0.1, -0.6), (0.45, 0.05), (-0.25, 0.35)]
    for c, (ox, oy) in zip(colors, offsets):
        x, y = cx + ox * s, cy + oy * s
        d.rounded_rectangle((x - 0.36 * s, y - 0.3 * s, x + 0.36 * s, y + 0.3 * s), radius=0.12 * s, fill=c)


def starfield(img, count, max_r=2.2):
    d = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(count):
        x, y = random.random() * w, random.random() * h
        r = random.random() ** 3 * max_r + 0.4
        a = int(120 + random.random() * 135)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(220, 232, 255, a))


def led():
    w, h = 2048, 882
    img = Image.new('RGBA', (w, h), '#081238')
    # 위→아래로 밝아지는 남색 그라데이션
    grad = Image.linear_gradient('L').resize((w, h))
    img.paste(Image.new('RGBA', (w, h), '#16308a'), mask=grad.point(lambda v: int(v * 0.6)))
    starfield(img, 1400)
    glow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for _ in range(40):
        x, y = random.random() * w, random.random() * h * 0.8
        r = random.uniform(6, 22)
        gd.ellipse((x - r, y - r, x + r, y + r), fill=(160, 200, 255, 90))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)

    band = int(h * 0.82)
    # 좌우 중계 화면
    for x0 in (int(w * 0.07), int(w * 0.62)):
        x1, y0, y1 = x0 + int(w * 0.31), int(h * 0.1), int(h * 0.64)
        d.rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), fill='#dfe8ff')
        panel = Image.linear_gradient('L').resize((x1 - x0, y1 - y0))
        blue = Image.new('RGBA', (x1 - x0, y1 - y0), '#1c3fa0')
        blue.paste(Image.new('RGBA', blue.size, '#3c7be0'), mask=panel)
        img.paste(blue, (x0, y0))
        cx = (x0 + x1) // 2
        d.ellipse((cx - 55, y0 + 70, cx + 55, y0 + 190), fill='#1a2238')  # 연사 실루엣
        d.rounded_rectangle((cx - 150, y0 + 180, cx + 150, y1 - 60), radius=60, fill='#141b30')
        d.rectangle((x0 + 40, y1 - 95, x1 - 40, y1 - 35), fill='#f4f6fb')  # 자막 바
        d.rectangle((cx - 60, y1 - 30, cx + 60, y1 - 10), fill='#f4f6fb')
    # 가운데 로고
    logo_mark(d, w // 2, int(h * 0.22), 70)
    d.text((w // 2, int(h * 0.42)), 'APEC', font=font(96), fill='white', anchor='mm')
    d.text((w // 2, int(h * 0.52)), 'CEO SUMMIT KOREA 2025', font=font(34), fill='white', anchor='mm')
    d.text((w // 2, int(h * 0.62)), 'SPECIAL DINNER', font=font(40), fill='white', anchor='mm')
    d.text((w // 2, int(h * 0.69)), 'By Gyeongsangbuk-do', font=font(30, False), fill='#d8e2ff', anchor='mm')
    # 하단 로고 띠
    d.rectangle((0, band, w, h), fill='#0b1a55')
    x = 60
    while x < w:
        logo_mark(d, x + 30, band + 60, 16)
        d.text((x + 64, band + 60), 'APEC  CEO SUMMIT KOREA 2025', font=font(24), fill='white', anchor='lm')
        d.text((x + 470, band + 60), '경상북도  GYEONGSANGBUK-DO', font=font(24), fill='white', anchor='lm')
        x += 900
    for x0 in range(40, w, 240):
        d.rectangle((x0, h - 18, x0 + 150, h - 8), fill='#cfe4ff')  # 바닥 라인 조명
    img.convert('RGB').save(os.path.join(OUT, 'apec_real_led.png'))


def fascia():
    """무대 전면 판 (파란 바탕 + 로고)"""
    w, h = 2048, 128
    img = Image.new('RGB', (w, h), '#1732a8')
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 6), fill='#9fc2ff')
    for x in range(120, w, 700):
        logo_mark(d, x, h // 2, 18)
        d.text((x + 36, h // 2), 'APEC', font=font(40), fill='white', anchor='lm')
        d.text((x + 190, h // 2), '경상북도', font=font(36), fill='white', anchor='lm')
    img.save(os.path.join(OUT, 'apec_real_fascia.png'))


def sign():
    """타워 계단 앞 보라색 사인월 (4.5 × 3.2 m)"""
    w, h = 1024, 728
    img = Image.new('RGB', (w, h), '#3a2e7c')
    grad = Image.linear_gradient('L').resize((w, h))
    img.paste(Image.new('RGB', (w, h), '#2a2160'), mask=grad)
    d = ImageDraw.Draw(img)
    logo_mark(d, int(w * 0.34), int(h * 0.44), 34)
    d.text((int(w * 0.44), int(h * 0.4)), 'APEC', font=font(84), fill='white', anchor='lm')
    d.text((int(w * 0.44), int(h * 0.5)), 'CEO SUMMIT KOREA 2025', font=font(26), fill='#e4e0ff', anchor='lm')
    d.text((int(w * 0.5), int(h * 0.64)), '경상북도', font=font(58), fill='white', anchor='mm')
    img.save(os.path.join(OUT, 'apec_real_sign.png'))


led()
fascia()
sign()
print('graphics written to', OUT)
