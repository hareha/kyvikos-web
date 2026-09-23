"""바스키아 전시 배치 평면도를 PNG 로 그린다 (Blender 없이, 배치 검증용).

  python3 scripts/blender/basquiat_plan.py [출력경로]

basquiat_scene.py 에서 ROOMS·DOORS 리터럴만 ast 로 뽑아 hall1_outline_v2 윤곽 위에 얹는다.
"""
import ast
import json
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = '/Users/hare/Documents/큐비크스홈페이지'
REFS = f'{ROOT}/assets-src/refs/basquiat'
SRC = f'{ROOT}/scripts/blender/basquiat_scene.py'
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/assets-src/renders/basquiat_plan.png'
PX, MARGIN = 34.0, 70                       # 1m = 34px

LAY = json.load(open(f'{REFS}/layout_v2.json'))
ROOMS = {z['id']: {'rect': tuple(z['rect']), 'col': z['walls']['n'], 'h': z['wall_h'], 'floor': z['floor']} for z in LAY['zones']}
COL = LAY['palette'] if isinstance(LAY.get('palette'), dict) else {}
DOORS = []
for d in LAY['doors']:
    z = ROOMS.get(d['zone'])
    if not z:
        continue
    x0, x1, z0, z1 = z['rect']
    u0, u1, sd = d['u0'], d['u1'], d['face']
    if sd == 'n':
        DOORS.append((x0 + u0, x0 + u1, z0, z0))
    elif sd == 's':
        DOORS.append((x1 - u1, x1 - u0, z1, z1))
    elif sd == 'e':
        DOORS.append((x1, x1, z0 + u0, z0 + u1))
    else:
        DOORS.append((x0, x0, z1 - u1, z1 - u0))
outline = json.load(open(f'{REFS}/hall1_outline_v2.json'))['outline']

xs = [p[0] for p in outline] + [v for r in ROOMS.values() for v in r['rect'][:2]]
zs = [p[1] for p in outline] + [v for r in ROOMS.values() for v in r['rect'][2:]]
X0, X1, Z0, Z1 = min(xs), max(xs), min(zs), max(zs)
W = int((X1 - X0) * PX) + MARGIN * 2
H = int((Z1 - Z0) * PX) + MARGIN * 2 + 40


def P(x, z):
    return (MARGIN + (x - X0) * PX, MARGIN + (z - Z0) * PX)


im = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 12)
    fb = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 17)
except OSError:
    f = fb = ImageFont.load_default()

for m in range(int(X0) - 1, int(X1) + 2, 5):            # 5m 격자
    d.line([P(m, Z0), P(m, Z1)], fill='#e6e6e6')
    d.text((P(m, Z0)[0] + 2, MARGIN - 16), str(m), font=f, fill='#999')
for m in range(int(Z0) - 1, int(Z1) + 2, 5):
    d.line([P(X0, m), P(X1, m)], fill='#e6e6e6')
    d.text((8, P(X0, m)[1] - 7), str(m), font=f, fill='#999')

for rid, r in ROOMS.items():
    x0, x1, z0, z1 = r['rect']
    col = COL.get(r.get('col', ''), '#dddddd') if isinstance(COL, dict) else '#dddddd'
    if not (isinstance(col, str) and col.startswith('#')):
        col = '#dddddd'
    d.rectangle([P(min(x0, x1), min(z0, z1)), P(max(x0, x1), max(z0, z1))], fill=col, outline='#555', width=2)
    cx, cz = P((x0 + x1) / 2, (z0 + z1) / 2)
    d.text((cx, cz - 14), rid, font=f, fill='#111', anchor='mm')
    d.text((cx, cz), f'{abs(x1 - x0):.1f}x{abs(z1 - z0):.1f}', font=f, fill='#444', anchor='mm')
    d.text((cx, cz + 14), f"h{r['h']} {r['floor'][2:]}", font=f, fill='#666', anchor='mm')

d.line([P(*p) for p in outline] + [P(*outline[0])], fill='black', width=4)
for dr in DOORS:                                    # DOORS = (x0, x1, z0, z1) 납작한 사각형
    if isinstance(dr, (list, tuple)) and len(dr) >= 4 and all(isinstance(v, (int, float)) for v in dr[:4]):
        x0, x1, z0, z1 = dr[:4]
        d.line([P(x0, z0), P(x1, z1)], fill='#d02020', width=7)

d.text((MARGIN, H - 32), f'DDP Hall 1 / Basquiat (layout_v2)  -  {len(ROOMS)} zones, {len(DOORS)} doors  '
                         f'-  outline 1220 m2 (official 1216)  -  +x east, +z south', font=fb, fill='#111')
im.save(OUT)
print('wrote', OUT, '| rooms', len(ROOMS), '| doors', len(DOORS), '|', W, 'x', H)
