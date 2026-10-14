"""바스키아 전시 배치 평면도를 PNG 로 그린다 (Blender 없이, 배치 검증용).

  python3 scripts/blender/basquiat_plan.py [출력경로] [--v2]

기본은 `layout_v3.json` 의 **벽 선분 그래프**를 그린다 (벽 = 굵은 선, 색 = 양쪽 면 재질,
굵기 = 벽 높이). `--v2` 를 주면 예전 닫힌-방 배치를 그린다 — 비교용.
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = '/Users/hare/Documents/큐비크스홈페이지'
REFS = f'{ROOT}/assets-src/refs/basquiat'
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
V2 = '--v2' in sys.argv
OUT = ARGS[0] if ARGS else f'{ROOT}/assets-src/renders/basquiat_plan.png'
PX, MARGIN = 34.0, 70

LAY = json.load(open(f'{REFS}/layout_v2.json' if V2 else f'{REFS}/layout_v3.json', encoding='utf-8'))
COL = LAY['palette']
SHELL = LAY.get('shell') or json.load(open(f'{REFS}/hall1_outline_v2.json', encoding='utf-8'))['outline']
FLOOR = {'carpetRed': '#7d4a4a', 'carpetGrey': '#55584f', 'floorPale': '#cfc8bb',
         'epoxy': '#e4e4e4', 'floorWhite': '#f4f4f4'}

xs = [p[0] for p in SHELL]
zs = [p[1] for p in SHELL]
X0, X1, Z0, Z1 = min(xs) - 1, max(xs) + 1, min(zs) - 1, max(zs) + 1
W = int((X1 - X0) * PX) + MARGIN * 2
H = int((Z1 - Z0) * PX) + MARGIN * 2 + 40


def P(x, z):
    return (MARGIN + (x - X0) * PX, MARGIN + (z - Z0) * PX)


im = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 12)
    fs = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 10)
    fb = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 17)
except OSError:
    f = fs = fb = ImageFont.load_default()

for m in range(int(X0) - 1, int(X1) + 2, 5):
    d.line([P(m, Z0), P(m, Z1)], fill='#ececec')
    d.text((P(m, Z0)[0] + 2, MARGIN - 16), str(m), font=fs, fill='#aaa')
for m in range(int(Z0) - 1, int(Z1) + 2, 5):
    d.line([P(X0, m), P(X1, m)], fill='#ececec')
    d.text((8, P(X0, m)[1] - 7), str(m), font=fs, fill='#aaa')

# 바닥
for z in LAY['zones']:
    x0, x1, z0, z1 = z['rect']
    col = FLOOR.get(z.get('floor'), '#eeeeee')
    d.rectangle([P(x0, z0), P(x1, z1)], fill=col)

d.line([P(*p) for p in SHELL] + [P(*SHELL[0])], fill='black', width=4)

if V2:
    for z in LAY['zones']:
        x0, x1, z0, z1 = z['rect']
        d.rectangle([P(x0, z0), P(x1, z1)], outline='#555', width=2)
else:
    for w in LAY['walls']:                      # 벽 = 굵은 선, 굵기 ∝ 높이
        (ax, az), (bx, bz) = w['p'], w['q']
        lw = 3 if w['h'] <= 3.1 else (6 if w['h'] <= 3.6 else 9)
        d.line([P(ax, az), P(bx, bz)], fill='#111', width=lw)

for z in LAY['zones']:
    if z.get('merged_into'):
        continue
    x0, x1, z0, z1 = z['rect']
    cx, cz = P((x0 + x1) / 2, (z0 + z1) / 2)
    tc = '#fff' if z.get('floor') in ('carpetRed', 'carpetGrey') else '#111'
    d.text((cx, cz - 13), z['id'], font=f, fill=tc, anchor='mm')
    d.text((cx, cz + 1), f'{abs(x1 - x0):.1f}x{abs(z1 - z0):.1f}', font=fs, fill=tc, anchor='mm')
    d.text((cx, cz + 14), f"h{z.get('wall_h', '')}", font=fs, fill=tc, anchor='mm')

ck = LAY.get('check', {})
sub = (f"v2 closed rooms — {len(LAY['zones'])} zones" if V2 else
       f"v3 wall graph — {ck.get('wall_count')} walls / {ck.get('wall_run_m')} m run, "
       f"public {ck.get('public_m2')} m2 + service {ck.get('service_m2')} m2")
d.text((MARGIN, H - 32), f'DDP Hall 1 / Basquiat  -  {sub}  -  hall 1220 m2  -  +x east, +z south',
       font=fb, fill='#111')
im.save(OUT)
print('wrote', OUT, '|', W, 'x', H)
