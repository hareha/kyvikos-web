"""현대 모터스튜디오 서울 — 현대자동차 1억 대 생산 기념 전시 〈다시, 첫걸음〉 (2024.10)

  python3 scripts/blender/bmcp.py exec scripts/blender/hyundai_scene.py

자료: 소개서 7~10p 사진·렌더, 현대차 보도자료·관람기(층별 구성), Suh Architects 건축 개요
- 건물: 강남 언주로 738, 도산사거리 모서리. 유리 커튼월 + '쇳물에서 자동차까지'를 뜻하는 노출 강관(파이프) 마감.
        천장은 가로 강관 루버, 기둥은 세로 강봉으로 감쌈. 파사드 안쪽에 노란 프레임에 차를 건 로테이터(3층 × 3대).
- 1층 '더 퍼스트 스텝': 포니 에콰도르 택시(노란) + '100,000,001대 생산' 아치, 코티나 Mk2, 포니. 차단봉·빨간 로프.
        아트리움(-x 쪽 3개 층 오픈) 천장에 컨베이어 레일 — 색색의 차체 크래들이 매달려 돌고 나선으로 내려옴.
        -x 유리벽 위쪽에 생산라인 영상 미디어월.
- 2층 '100밀리언': 1980년대 제도실(제도판·스탠드), 아카이브 진열대.
- 3층 '원 스텝 퍼더': '100 MILLION AND ONE STEP FURTHER' 게이트(좌우 LED, 팔레트), 엘란트라(1992, 와인색)와
        '1992, Ulsan Plant' 곡면 파티션, 둥근 라이트박스 천장.
좌표: 건물 중심 원점, 웹과 같은 Y-up. -x 미디어월 유리벽, +z 정면 파사드(입구). 층: 1F 0 · 2F 6 · 3F 11.5 · 지붕 16.8
차량 모델(CC BY, CREDITS.md): 포니 ← 골프 Mk1(같은 주지아로 디자인·비례), 코티나 ← VAZ-2101, 엘란트라 ← 코롤라 KE80
"""
import importlib
import math
import random
import sys

sys.path.insert(0, '/Users/hare/Documents/큐비크스홈페이지/scripts/blender')
import lib  # noqa: E402

importlib.reload(lib)
from lib import (PI, SHOTS, HDRI, Assembly, T, bevel_box, box, camera, collection, cyl, instance, light, material,  # noqa: E402
                 mesh_source, plane, reset, sphere, tube, world_hdri)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

import gear  # noqa: E402
import props  # noqa: E402
importlib.reload(gear)
importlib.reload(props)

random.seed(3)
reset()
scene = bpy.context.scene
C_STATIC = collection('STATIC')
C_DYNAMIC = collection('DYNAMIC')
C_EMIT = collection('EMISSIVE')
C_LIGHT = collection('LIGHTS')
C_CAM = collection('CAMERAS')
C_RENDER_ONLY = collection('RENDER_ONLY')
C_SRC = collection('SOURCES')
C_SRC.hide_render = True
C_SRC.hide_viewport = True

F2, F3, ROOF = 6.0, 11.5, 16.8
X0, X1, Z0, Z1 = -20.0, 20.0, -14.0, 14.0

M = {
    'floor': material('hyFloor', None, (0.5, 0.51, 0.53), 0.22, coat=0.4),          # 매끈한 폴리싱 콘크리트
    'floorUp': material('hyFloorUp', None, (0.55, 0.56, 0.58), 0.28, coat=0.3),
    'slab': material('hySlab', None, (0.05, 0.055, 0.06), 0.7),
    'concrete': material('hyConcrete', 'painted_plaster_wall', (0.46, 0.47, 0.49), 0.85),
    'wallDark': material('hyWallDark', 'painted_plaster_wall', (0.12, 0.125, 0.135), 0.7),
    'wallWhite': material('hyWallWhite', 'painted_plaster_wall', (0.88, 0.87, 0.84), 0.8),
    'pipe': material('hyPipe', None, (0.62, 0.64, 0.67), 0.35, 0.9),
    'pipeDark': material('hyPipeDark', None, (0.2, 0.21, 0.23), 0.4, 0.8),
    'column': material('hyColumn', None, (0.16, 0.17, 0.19), 0.45, 0.7),
    'mullion': material('hyMullion', None, (0.08, 0.085, 0.095), 0.4, 0.6),
    'glass': material('hyGlass', None, (0.85, 0.9, 0.95), 0.03, transmission=1.0),
    'rail': material('hyRail', None, (0.86, 0.88, 0.9), 0.25, 0.9),
    'cradle': material('hyCradle', None, (0.95, 0.72, 0.06), 0.45),
    'steel': material('hySteel', None, (0.78, 0.8, 0.83), 0.3, 1.0),
    'chrome': material('hyChrome', None, (0.9, 0.9, 0.92), 0.12, 1.0),
    'black': material('hyBlack', None, (0.012, 0.012, 0.015), 0.5),
    'rope': material('hyRope', 'cotton_jersey', (0.45, 0.04, 0.06), 0.7, normal=0.5, sheen=0.4),
    'mat': material('hyMat', 'cotton_jersey', (0.22, 0.23, 0.24), 0.95, normal=0.6),
    'desk': material('hyDesk', None, (0.72, 0.7, 0.64), 0.6),
    'board': material('hyBoard', None, (0.93, 0.93, 0.9), 0.7),
    'pallet': material('hyPallet', 'dark_wooden_planks', (0.9, 0.7, 0.48), 0.8),
    'carton': material('hyCarton', None, (0.66, 0.52, 0.34), 0.9),
    'archiveTop': material('hyArchiveTop', None, (0.2, 0.21, 0.22), 0.5),
    'mural': material('hyMural', emit_image=f'{SHOTS}/hy_mural_real.png', emit_strength=2.2, rough=0.3),   # 현장 사진 속 생산라인 영상
    'header': material('hyHeader', emit_image=f'{SHOTS}/hy_header.png', emit_strength=2.0, rough=0.4),
    'city': material('hyCity', emit_image=f'{SHOTS}/hy_city.png', emit_strength=2.2, rough=0.3),
    'neon': material('hyNeon', emit_image=f'{SHOTS}/hy_neon.png', emit_strength=2.2, rough=0.3),
    'arch': material('hyArch', image_base=f'{SHOTS}/hy_arch.png', rough=0.6),
    'p92': material('hyP92', image_base=f'{SHOTS}/hy_p92.png', rough=0.8),
    'p90': material('hyP90', image_base=f'{SHOTS}/hy_p90.png', rough=0.8),
    'archive': material('hyArchive', emit_image=f'{SHOTS}/hy_archive.png', emit_strength=0.9, rough=0.7),
    'blueprint': material('hyBlueprint', image_base=f'{SHOTS}/hy_blueprint.png', rough=0.8),
    'sign': material('hySign', image_base=f'{SHOTS}/hy_sign.png', rough=0.7),
    'strip': material('hyStrip', None, (1, 1, 1), emit=(1.0, 0.95, 0.86), emit_strength=18),
    'stripCool': material('hyStripCool', None, (1, 1, 1), emit=(0.9, 0.95, 1.0), emit_strength=16),
    'lightbox': material('hyLightbox', None, (1, 1, 1), emit=(1.0, 0.97, 0.9), emit_strength=6),
    'lampHead': material('hyLampHead', None, (1, 1, 1), emit=(1.0, 0.93, 0.8), emit_strength=25),
    'taxiSign': material('hyTaxiSign', None, (1, 0.9, 0.5), emit=(1.0, 0.85, 0.4), emit_strength=3),
    'street': material('hyStreet', 'asphalt_02', (0.3, 0.31, 0.33), 0.9),
    'sidewalk': material('hySidewalk', 'rock_tile_floor_02', (0.6, 0.6, 0.58), 0.8),
}

# ── 차량 모델 (불러온 모델 + 도색) ───────────────────────────────
GOLF = props.load('02b14f8dfb494cc28a982fd54a26827a', 'src_golf', width=3.97, coll=C_SRC)       # 포니 1975: 전장 3.97m
VAZ = props.load('31200fbcff0c4f2d80c24f81a786b594', 'src_vaz', width=4.1, coll=C_SRC)          # 코티나 Mk2: 4.27m
COROLLA = props.load('2b30faa611e64177a94a69098d27d1fb', 'src_corolla', width=4.37, decimate=0.25, coll=C_SRC)   # 엘란트라 1992: 4.37m
PONY_TAXI = props.retint(GOLF, (0.93, 0.62, 0.05), 'taxi')
PONY_BLUE = props.retint(GOLF, (0.12, 0.36, 0.62), 'blue')
CORTINA = props.set_material_color(VAZ, 'auto', (0.16, 0.62, 0.6), 'teal')
VAZ_GREEN = props.set_material_color(VAZ, 'auto', (0.12, 0.24, 0.2), 'green')
ELANTRA = props.set_material_color(COROLLA, 'body', (0.26, 0.04, 0.08), 'wine')
MODERN = props.set_material_color(COROLLA, 'body', (0.1, 0.22, 0.45), 'blue')
BODY_COLORS = [(0.8, 0.06, 0.08), (0.08, 0.16, 0.7), (0.93, 0.72, 0.05), (0.05, 0.6, 0.56), (0.9, 0.9, 0.9), (0.9, 0.38, 0.1)]
BODIES = [props.set_material_color(VAZ, 'auto', c, f'body{k}') for k, c in enumerate(BODY_COLORS)]
for o in [PONY_TAXI, PONY_BLUE, CORTINA, VAZ_GREEN, ELANTRA, MODERN] + BODIES:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    C_SRC.objects.link(o)
PLANT = props.load('potted_plant_02', 'src_plant', height=1.7, decimate=0.2, coll=C_SRC)

car_spots = []   # (소스, 웹 변환)


def place_car(src, x, y, z, ry, s=1.0, dynamic=True):
    car_spots.append((src, T(x, y, z, ry, 0, 0, s, s, s)))


# ── 건물 ──────────────────────────────────────────────────────
shell = Assembly('building', C_STATIC)
floors = Assembly('floors', C_STATIC)
glass = Assembly('glass', C_DYNAMIC)
emit = Assembly('emissive', C_EMIT)

floors.add(box(X1 - X0, 0.3, Z1 - Z0), T(0, -0.15, 0), M['floor'], 3)


def slab(x0, x1, z0, z1, y):
    floors.add(box(x1 - x0, 0.06, z1 - z0), T((x0 + x1) / 2, y - 0.03, (z0 + z1) / 2), M['floorUp'], 3)       # 바닥 마감
    shell.add(box(x1 - x0, 0.5, z1 - z0), T((x0 + x1) / 2, y - 0.31, (z0 + z1) / 2), M['slab'], 3)         # 구조 슬래브
    # 슬래브 밑 가로 강관 루버 (천장) — 사진의 촘촘한 파이프 천장
    y_p = y - 0.62
    z = z0 + 0.09
    while z < z1 - 0.05:
        g, m = tube(V((x0 + 0.05, y_p, z)), V((x1 - 0.05, y_p, z)), 0.032, 8)
        shell.add(g, m, M['pipe'])
        z += 0.2
    for x in range(int(x0) + 2, int(x1), 3):             # 루버 걸이: 파이프를 꿰는 가로대 + 슬래브에 박힌 달대
        shell.add(box(0.06, 0.1, z1 - z0 - 0.1), T(x, y - 0.6, (z0 + z1) / 2), M['pipeDark'], 1)
        for zz in (z0 + 1, (z0 + z1) / 2, z1 - 1):
            shell.add(box(0.03, 0.12, 0.03), T(x, y - 0.5, zz), M['pipeDark'], 1)


# 2F: 아트리움(x < 4) 비우고 뒤쪽 띠만 / 3F: x < 8 비움
slab(4, X1, Z0, Z1, F2)
slab(X0, 4, Z0, -8, F2)
slab(1.4, 4, -1.2, 1.2, F2)          # 계단 참
slab(8, X1, Z0, Z1, F3)
slab(X0, 8, Z0, -10, F3)
# 지붕 슬래브 + 천장 강관
shell.add(box(X1 - X0, 0.6, Z1 - Z0), T(0, ROOF + 0.3, 0), M['slab'], 3)
z = Z0 + 0.09
while z < Z1 - 0.05:
    g, m = tube(V((X0 + 0.05, ROOF - 0.35, z)), V((X1 - 0.05, ROOF - 0.35, z)), 0.032, 8)
    shell.add(g, m, M['pipe'])
    z += 0.2
for x in range(int(X0) + 2, int(X1), 3):                 # 지붕 루버 걸이
    shell.add(box(0.06, 0.1, Z1 - Z0 - 0.1), T(x, ROOF - 0.33, 0), M['pipeDark'], 1)
    for zz in (Z0 + 1, 0, Z1 - 1):
        shell.add(box(0.03, 0.34, 0.03), T(x, ROOF - 0.15, zz), M['pipeDark'], 1)

# 기둥: 원형 강관 + 세로 강봉 12개로 감쌈
COLS = [(-12, -8), (0, -8), (8, -8), (8, 3), (8, 13), (16, -8), (16, 3), (-2, 13)]
for (cx, cz) in COLS:
    shell.add(cyl(0.45, 0.45, ROOF, 24), T(cx, ROOF / 2, cz), M['column'], 1)
    for k in range(14):
        a = k / 14 * 2 * PI
        shell.add(cyl(0.035, 0.035, ROOF, 8), T(cx + math.cos(a) * 0.5, ROOF / 2, cz + math.sin(a) * 0.5), M['pipe'], 1)

# 뒷벽 (콘크리트) + 옆벽(+x, 아래 1/3 은 벽, 위는 유리)
shell.add(box(X1 - X0, ROOF, 0.4), T(0, ROOF / 2, Z0 - 0.2), M['concrete'], 2)


def curtain(axis, fixed, a0, a1, y0, y1, step=2.8, outward=1):
    """유리 커튼월: 판유리(동적) + 멀리언·트랜섬(정적)"""
    L = a1 - a0
    n = max(1, round(L / step))
    for k in range(n + 1):
        a = a0 + L * k / n
        p = (fixed, (y0 + y1) / 2, a) if axis == 'z' else (a, (y0 + y1) / 2, fixed)
        shell.add(box(0.12, y1 - y0, 0.22) if axis == 'z' else box(0.22, y1 - y0, 0.12), T(*p), M['mullion'], 1)
    for y in (y0, F2 - 0.3, F3 - 0.3, y1):
        if y < y0 or y > y1:
            continue
        p = (fixed, y, (a0 + a1) / 2) if axis == 'z' else ((a0 + a1) / 2, y, fixed)
        shell.add(box(0.2, 0.14, L) if axis == 'z' else box(L, 0.14, 0.2), T(*p), M['mullion'], 1)
    p = (fixed, (y0 + y1) / 2, (a0 + a1) / 2) if axis == 'z' else ((a0 + a1) / 2, (y0 + y1) / 2, fixed)
    glass.add(box(0.03, y1 - y0, L) if axis == 'z' else box(L, y1 - y0, 0.03), T(*p), M['glass'])


curtain('z', X0, Z0, Z1, 0, ROOF)          # -x 미디어월 뒤 유리벽
curtain('x', Z1, X0, X1, 0, ROOF)          # +z 정면 파사드
curtain('z', X1, Z0, Z1, 0, ROOF)          # +x 옆 파사드
for y in (F2, F3):                          # 층 슬래브 끝선 (파사드 쪽)
    shell.add(box(X1 - X0, 0.55, 0.25), T(0, y - 0.28, Z1 - 0.15), M['slab'], 2)
    shell.add(box(0.25, 0.55, Z1 - Z0), T(X1 - 0.15, y - 0.28, 0), M['slab'], 2)
    shell.add(box(0.25, 0.55, Z1 - Z0), T(X0 + 0.15, y - 0.28, 0), M['slab'], 2)

# 바깥: 보도 + 도로 (도산대로·언주로 모서리)
outer = Assembly('outer', C_STATIC)
outer.add(box(64, 0.15, 12), T(2, -0.075, Z1 + 6), M['sidewalk'], 1.2)
outer.add(box(12, 0.15, 40), T(X1 + 6, -0.075, 2), M['sidewalk'], 1.2)
outer.add(box(90, 0.1, 30), T(10, -0.2, Z1 + 27), M['street'], 4)
outer.add(box(30, 0.1, 60), T(X1 + 27, -0.2, 0), M['street'], 4)
outer.build()


# ── 난간 · 계단 ─────────────────────────────────────────────────
def railing(a, c, h=1.1):
    a, c = V(a), V(c)
    d = c - a
    L = d.length
    for y in (h, h * 0.55, 0.12):
        g, m = tube(a + V((0, y, 0)), c + V((0, y, 0)), 0.024 if y == h else 0.016, 8)
        shell.add(g, m, M['steel'])
    n = max(1, round(L / 1.2))
    for k in range(n + 1):
        p = a + d * (k / n)
        shell.add(cyl(0.022, 0.022, h, 8), T(p.x, p.y + h / 2, p.z), M['steel'], 1)


railing((4, F2, -8), (4, F2, -1.2))
railing((4, F2, 1.2), (4, F2, Z1 - 0.4))
railing((X0 + 0.3, F2, -8), (1.4, F2, -8))
railing((1.4, F2, -8), (1.4, F2, -1.2))
railing((8, F3, -10), (8, F3, Z1 - 0.4))
railing((X0 + 0.3, F3, -10), (8, F3, -10))

# 강철 계단: 1F(z 13) → 2F 참(z 1.2), 폭 2m, 디딤판 + 옆판 + 난간
SX, RUN, N = 2.4, 11.8, 20
slope = math.atan2(F2, RUN)
for i in range(N):
    y = (i + 1) * F2 / N
    z = 13 - (i + 0.5) * RUN / N
    shell.add(bevel_box(2.0, 0.05, RUN / N + 0.02, 0.008), T(SX, y - 0.025, z), M['steel'], 1)
for sx in (-1.03, 1.03):
    shell.add(box(0.05, 0.36, math.hypot(F2, RUN) + 0.3), T(SX + sx, F2 / 2 - 0.12, 13 - RUN / 2, 0, slope), M['column'], 1)
    railing((SX + sx, 0.0, 13.0), (SX + sx, F2, 1.2))

# ── 미디어월 (-x 유리벽 상부, 생산라인 영상) ─────────────────────
MY = 9.6
shell.add(box(0.35, 6.5, 22.6), T(X0 + 0.5, MY, 1), M['wallDark'], 1)
emit.add(plane(22.2, 6.1), T(X0 + 0.69, MY, 1, PI / 2), M['mural'], tile=None)
for zz in (-8, 1, 10):
    g, m = tube(V((X0 + 0.5, MY + 3.25, zz)), V((X0 + 0.5, ROOF - 0.35, zz)), 0.05, 8)
    shell.add(g, m, M['steel'])

# ── 천장 컨베이어 레일 + 차체 크래들 ─────────────────────────────
conv = Assembly('conveyor', C_DYNAMIC)
RY, CXc, CZc, R, Lc = 14.2, -9.0, 1.5, 4.6, 5.0


def loop_pt(t):
    """닫힌 트랙: 두 반원 + 두 직선 (t 0~1)"""
    per = 2 * PI * R + 4 * Lc
    s = (t % 1) * per
    if s < 2 * Lc:
        return V((CXc + R, RY, CZc - Lc + s))
    s -= 2 * Lc
    if s < PI * R:
        a = s / R
        return V((CXc + R * math.cos(a), RY + 0.35 * math.sin(a), CZc + Lc + R * math.sin(a)))
    s -= PI * R
    if s < 2 * Lc:
        return V((CXc - R, RY, CZc + Lc - s))
    s -= 2 * Lc
    a = PI + s / R
    return V((CXc + R * math.cos(a), RY - 0.35 * math.sin(a), CZc - Lc + R * math.sin(a)))


def drop_pt(t):
    """레일에서 갈라져 나선으로 내려오는 가지"""
    a = t * 2.2 * PI
    r = 2.6 - 0.6 * t
    return V((-2.6 + r * math.cos(a), RY - 7.2 * t, -1.6 + r * math.sin(a)))


for f, n, closed in ((loop_pt, 160, True), (drop_pt, 90, False)):
    pts = [f(k / n) for k in range(n + (0 if closed else 1))]
    for a, b in zip(pts, pts[1:] + ([pts[0]] if closed else [])):
        g, m = tube(a, b, 0.1, 10)
        conv.add(g, m, M['rail'])
        # 레일 아래 I형 플랜지
        g, m = tube(a + V((0, -0.16, 0)), b + V((0, -0.16, 0)), 0.035, 6)
        conv.add(g, m, M['rail'])
for k in range(12):                                          # 천장 행거
    p = loop_pt(k / 12)
    g, m = tube(p, V((p.x, ROOF - 0.35, p.z)), 0.03, 8)
    conv.add(g, m, M['steel'])
for t in (0.3, 0.6, 0.9):
    p = drop_pt(t)
    g, m = tube(p, V((p.x, ROOF - 0.35, p.z)), 0.025, 8)
    conv.add(g, m, M['steel'])

cradle_spots = []


def cradle(p, tangent, s, k):
    """노란 행거 + 차체를 감싼 색 프레임(차체 골격), 안에 축소 차체"""
    ry = math.atan2(-tangent.z, tangent.x)
    w, d, h = 4.4 * s, 1.9 * s, 1.55 * s
    f = T(p.x, p.y - 0.28, p.z, ry)
    g, m = tube(f @ V((0, 0.26, 0)), f @ V((0, 0.0, 0)), 0.04, 8)
    conv.add(g, m, M['steel'])
    col = M[f'frame{k % len(BODY_COLORS)}']
    g, m = tube(f @ V((-w / 2, 0, 0)), f @ V((w / 2, 0, 0)), 0.035 * s / 0.45, 8)      # 행거가 걸리는 가운데 가로대
    conv.add(g, m, col)
    for (a, b) in ((V((-w / 2, 0, -d / 2)), V((w / 2, 0, -d / 2))), (V((-w / 2, 0, d / 2)), V((w / 2, 0, d / 2))),
                   (V((-w / 2, 0, -d / 2)), V((-w / 2, 0, d / 2))), (V((w / 2, 0, -d / 2)), V((w / 2, 0, d / 2)))):
        g, m = tube(f @ a, f @ b, 0.035 * s / 0.45, 8)
        conv.add(g, m, col)
    for sx in (-w / 2, w / 2):
        for sz in (-d / 2, d / 2):
            g, m = tube(f @ V((sx, 0, sz)), f @ V((sx * 0.8, -h, sz)), 0.03 * s / 0.45, 8)
            conv.add(g, m, col)
    cradle_spots.append((BODIES[k % len(BODIES)], f @ T(0, -h + 0.05 * s, 0, 0, 0, 0, s, s, s)))


for k, c in enumerate(BODY_COLORS):
    M[f'frame{k}'] = material(f'hyFrame{k}', None, c, 0.4, 0.2)
for i in range(14):
    t = (i + 0.5) / 14
    p = loop_pt(t)
    tg = (loop_pt(t + 0.002) - loop_pt(t - 0.002)).normalized()
    cradle(p, tg, 0.45, i)
for i in range(7):
    t = 0.12 + 0.88 * (i + 0.5) / 7
    p = drop_pt(t)
    tg = (drop_pt(t + 0.003) - drop_pt(t - 0.003)).normalized()
    cradle(p, tg, 0.32, i + 3)

# ── 파사드 로테이터 (정면 유리 안쪽, 3층 × 3대: 노란 프레임에 건 차량) ──────
rot = Assembly('rotators', C_DYNAMIC)
for fy, yb in ((0, 0.0), (1, F2), (2, F3)):
    for k, x in enumerate((-17.5, -13.2, -8.9)):
        cx, cz = x, Z1 - 1.3
        y = yb + 0.9 + (0.8 if fy else 0.3)
        f = T(cx, y, cz, 0.12 * (k - 1))
        for (a, b) in ((V((-2.4, 0, -1.05)), V((2.4, 0, -1.05))), (V((-2.4, 0, 1.05)), V((2.4, 0, 1.05))),
                       (V((-2.4, 0, -1.05)), V((-2.4, 0, 1.05))), (V((2.4, 0, -1.05)), V((2.4, 0, 1.05))),
                       (V((-2.4, 1.75, 0)), V((2.4, 1.75, 0))), (V((-2.4, 0, 0)), V((2.4, 0, 0)))):
            g, m = tube(f @ a, f @ b, 0.07, 10)
            rot.add(g, m, M['cradle'])
        for sx in (-2.4, 2.4):
            g, m = tube(f @ V((sx, 0, -1.05)), f @ V((sx, 1.75, 0)), 0.07, 10)
            rot.add(g, m, M['cradle'])
            g, m = tube(f @ V((sx, 0, 1.05)), f @ V((sx, 1.75, 0)), 0.07, 10)
            rot.add(g, m, M['cradle'])
        # 로테이터 축 (바닥 받침 또는 천장 행거)
        if fy == 0:
            rot.add(cyl(0.18, 0.28, y, 16), f @ T(0, -y / 2, 0), M['column'])
        else:
            g, m = tube(f @ V((0, 1.75, 0)), V((cx, yb + 5.3, cz)), 0.06, 8)
            rot.add(g, m, M['steel'])
        src = [BODIES[4], BODIES[0], BODIES[1]][k] if fy != 1 else [BODIES[2], BODIES[5], BODIES[3]][k]
        car_spots.append((src, f @ T(0, 0.02, 0)))

# ── 1층 '더 퍼스트 스텝' ─────────────────────────────────────────
props1 = Assembly('exhibit1', C_STATIC)


def stanchions(pts):
    for p in pts:
        props1.add(cyl(0.17, 0.17, 0.03, 20), T(p[0], 0.015, p[1]), M['chrome'], 1)
        props1.add(cyl(0.025, 0.025, 0.95, 10), T(p[0], 0.49, p[1]), M['chrome'], 1)
        props1.add(sphere(0.035, 2), T(p[0], 0.98, p[1]), M['chrome'])
    for a, b in zip(pts, pts[1:] + pts[:1]):
        mid = V(((a[0] + b[0]) / 2, 0.72, (a[1] + b[1]) / 2))
        pa, pb = V((a[0], 0.9, a[1])), V((b[0], 0.9, b[1]))
        for u, v in ((pa, mid), (mid, pb)):
            g, m = tube(u, v, 0.02, 8)
            props1.add(g, m, M['rope'])


def arch(x, z):
    """'100,000,001대 생산' 아치 (앞면 그래픽, 두께 0.45)"""
    R, L, r = 2.4, 2.4, 1.65

    def build(bm):
        outline = [(-R, 0), (-R, L)] + [(-R * math.cos(t * PI / 24), L + R * math.sin(t * PI / 24)) for t in range(1, 24)] + \
                  [(R, L), (R, 0), (r, 0), (r, L)] + [(r * math.cos(t * PI / 24), L + r * math.sin(t * PI / 24)) for t in range(1, 24)] + \
                  [(-r, L), (-r, 0)]
        front = [bm.verts.new((px, py, 0.225)) for px, py in outline]
        back = [bm.verts.new((px, py, -0.225)) for px, py in outline]
        n = len(outline)
        # 앞·뒤 면: 띠를 사다리꼴 조각으로 (바깥 원호 i ↔ 안쪽 원호 대응)
        outer = list(range(0, 26))                 # -R,0 … R,0 까지 (바깥)
        inner = list(range(n - 1, 25, -1))          # -r,0 … r,0 까지 (안쪽, 역순)
        for vs in (front, back):
            for k in range(len(outer) - 1):
                a0, a1 = vs[outer[k]], vs[outer[k + 1]]
                b0, b1 = vs[inner[min(k, len(inner) - 1)]], vs[inner[min(k + 1, len(inner) - 1)]]
                q = (a0, a1, b1, b0) if vs is front else (b0, b1, a1, a0)
                if len({id(v) for v in q}) == 4:
                    bm.faces.new(q)
        for k in range(n):
            bm.faces.new((front[k], back[k], back[(k + 1) % n], front[(k + 1) % n]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        uv = bm.loops.layers.uv.active
        for fc in bm.faces:
            for lp in fc.loops:
                lp[uv].uv = ((lp.vert.co.x + R) / (2 * R), lp.vert.co.y / (L + R))
    props1.add(build, T(x, 0.12, z), M['arch'], tile=None)
    props1.add(bevel_box(2 * R + 0.3, 0.12, 0.8, 0.02), T(x, 0.06, z), M['wallWhite'], 1)


place_car(PONY_TAXI, -6, 0, 7.6, -PI / 2)
props1.add(bevel_box(0.62, 0.2, 0.3, 0.03), T(-6, 1.43, 7.55), M['black'], 1)                 # 택시 지붕 표시등 받침
emit.add(box(0.58, 0.14, 0.26), T(-6, 1.6, 7.55), M['taxiSign'])
arch(-6, 9.4)
stanchions([(-8.3, 5.0), (-3.7, 5.0), (-3.7, 10.4), (-8.3, 10.4)])
place_car(CORTINA, -13.5, 0, 4.5, -PI / 2 + 0.35)
place_car(PONY_BLUE, -15.0, 0, -3.0, -PI / 2 + 0.15)
stanchions([(-17.2, 1.2), (-11.0, 1.2), (-11.0, 7.8), (-17.2, 7.8)])
for (px, pz) in ((-17.5, 12.2), (17.5, 12.2)):
    props1.add(mesh_source(PLANT), T(px, 0, pz, random.uniform(0, PI)), list(PLANT.data.materials))
props1.build()

# ── 2층: 1980년대 제도실 + 아카이브 ──────────────────────────────
ex2 = Assembly('exhibit2', C_STATIC)
Y2 = F2
ex2.add(box(0.4, 5.2, 5), T(10.2, Y2 + 2.6, -11.3), M['wallDark'], 1)
ex2.add(box(9.4, 5.2, 0.2), T(15.1, Y2 + 2.6, -13.55), M['wallWhite'], 2)
ex2.add(plane(6, 2.3), T(15.3, Y2 + 1.9, -13.44), M['blueprint'], tile=None)
for (dx, dz, rot_) in ((12.6, -9.5, 0), (15.8, -10.2, 0.1), (18.0, -7.4, -0.2)):
    f = T(dx, Y2, dz, rot_)
    ex2.add(bevel_box(2.2, 0.05, 1.1, 0.01), f @ T(0, 0.78, 0), M['desk'], 1)
    for lx in (-1.0, 1.0):
        for lz in (-0.48, 0.48):
            ex2.add(box(0.05, 0.76, 0.05), f @ T(lx, 0.38, lz), M['black'], 1)
    bd = f @ T(0.2, 0.795 + 0.55 * math.sin(0.55), -0.1, 0, 0.55)                                   # 제도판 (앞 모서리가 책상에 닿고 뒤가 들림)
    ex2.add(bevel_box(1.6, 0.03, 1.1, 0.005), bd, M['board'], 1)
    ex2.add(box(1.5, 0.02, 0.05), bd @ T(0, 0.025, 0.3), M['steel'], 1)                              # 평행자 (판 위)
    for lx in (-0.6, 0.6):                                                                           # 뒤 받침
        g, m = tube(f @ V((0.2 + lx, 0.8, -0.5)), bd @ V((lx, -0.01, -0.5)), 0.012, 6)
        ex2.add(g, m, M['black'])
    g, m = tube(f @ V((-0.9, 0.8, -0.4)), f @ V((-0.9, 1.5, -0.3)), 0.012, 8)                      # 스탠드
    ex2.add(g, m, M['black'])
    g, m = tube(f @ V((-0.9, 1.5, -0.3)), f @ V((-0.5, 1.45, 0.0)), 0.012, 8)
    ex2.add(g, m, M['black'])
    ex2.add(cyl(0.02, 0.1, 0.12, 16), f @ T(-0.5, 1.39, 0.0), M['black'], 1)
    emit.add(cyl(0.085, 0.085, 0.01, 16), f @ T(-0.5, 1.33, 0.0), M['lampHead'])
    ex2.add(bevel_box(0.45, 0.45, 0.45, 0.02), f @ T(0.1, 0.23, 0.85), M['black'], 1)                 # 의자
ex2.add(bevel_box(1.6, 2.3, 0.08, 0.01), T(9.6, Y2 + 1.21, -5.2, -0.3), M['wallWhite'], 1)
ex2.add(bevel_box(1.8, 0.06, 0.5, 0.01), T(9.6, Y2 + 0.03, -5.2, -0.3), M['black'], 1)                      # 받침
ex2.add(plane(1.5, 2.1), T(9.6, Y2 + 1.21, -5.2, -0.3) @ T(0, 0, 0.042), M['sign'], tile=None)   # 판 앞면에 붙은 그래픽
# 아카이브: 어두운 벽 + 불 켜진 패널 + 긴 진열대 (소개서 사진)
ex2.add(box(15.4, 3.2, 0.3), T(-7.5, Y2 + 1.6, -13.65), M['wallDark'], 1)
emit.add(plane(12.5, 1.9), T(-7.5, Y2 + 2.0, -13.49), M['archive'], tile=None)
ex2.add(bevel_box(12.6, 0.86, 1.0, 0.02), T(-7.5, Y2 + 0.43, -12.6), M['archiveTop'], 1)
ex2.add(bevel_box(12.8, 0.05, 1.2, 0.01), T(-7.5, Y2 + 0.884, -12.6), M['archiveTop'], 1)
for i in range(9):
    ex2.add(bevel_box(0.55, 0.03, 0.4, 0.005), T(-13 + i * 1.35, Y2 + 0.918, -12.6, random.uniform(-0.2, 0.2)), M['board'], 1)
emit.add(box(12.6, 0.05, 0.06), T(-7.5, Y2 + 3.1, -13.45), M['strip'])
ex2.build()

# ── 3층: 1억 대 게이트 + 헤리티지 존 ────────────────────────────
ex3 = Assembly('exhibit3', C_STATIC)
Y3 = F3
GZ = -4.6
ex3.add(box(11.6, 0.02, 8.4), T(14, Y3 + 0.01, -6.4), M['wallDark'], 2)                          # 검은 전시 바닥
for px in (8.9, 19.1):
    ex3.add(bevel_box(0.8, 4.6, 0.8, 0.02), T(px, Y3 + 2.3, GZ), M['wallDark'], 1)
ex3.add(bevel_box(11, 0.7, 0.72, 0.02), T(14, Y3 + 4.25, GZ), M['wallDark'], 1)
emit.add(plane(10.6, 0.58), T(14, Y3 + 4.25, GZ + 0.47), M['header'], tile=None)
emit.add(box(10.2, 0.05, 0.1), T(14, Y3 + 3.87, GZ + 0.25), M['stripCool'])
for (ax, az, ry_, mat_) in ((9.3, GZ - 0.4, PI / 4, 'city'), (15.2, GZ - 3.9, -PI / 4, 'neon')):
    f = T(ax, Y3, az, ry_)
    ex3.add(box(4.95, 3.6, 0.12), f @ T(2.475, 1.9, -0.07), M['wallDark'], 1)
    emit.add(plane(4.9, 3.55), f @ T(2.475, 1.9, 0.01), M[mat_], tile=None)
for px in (13.3, 14.7):
    ex3.add(box(1.2, 0.14, 1.0), T(px, Y3 + 0.07, GZ - 3.9), M['pallet'], 1)
    for i in range(3):
        ex3.add(bevel_box(1.08, 0.58, 0.88, 0.01), T(px, Y3 + 0.44 + i * 0.6, GZ - 3.9), M['carton'], 1)
for (px, src) in ((11.2, VAZ_GREEN), (16.8, MODERN)):
    ex3.add(bevel_box(2.4, 0.06, 4.9, 0.01), T(px, Y3 + 0.03, GZ - 1.8), M['black'], 1)
    place_car(src, px, Y3 + 0.06, GZ - 1.8, -PI / 2, 0.95)
# 헤리티지: 엘란트라 + 곡면 파티션 + 라이트박스
ex3.add(box(3.2, 0.02, 5.6), T(16.5, Y3 + 0.01, 8.4, 0.25), M['mat'], 1)
place_car(ELANTRA, 16.5, Y3 + 0.02, 8.4, -PI / 2 + 0.25)


def curved_partition(x, z, ry, mat):
    """곡면 파티션 (반지름 3, 높이 3.8, 두께 0.08) — 볼록면에 사진 그래픽"""
    def build(bm):
        n = 16
        rows = []
        for i in range(n + 1):
            a = -0.5 + i / n
            for rr in (3.0, 3.08):
                pass
        outer = [(3.0 * math.sin(-0.5 + i / n), 3.0 * math.cos(-0.5 + i / n) - 3.0) for i in range(n + 1)]
        inner = [(2.92 * math.sin(-0.5 + i / n), 2.92 * math.cos(-0.5 + i / n) - 3.0) for i in range(n + 1)]
        uv = bm.loops.layers.uv.active
        for ring, flip in ((outer, False), (inner, True)):
            vb = [bm.verts.new((px, 0, pz)) for px, pz in ring]
            vt = [bm.verts.new((px, 3.8, pz)) for px, pz in ring]
            for i in range(n):
                q = (vb[i], vb[i + 1], vt[i + 1], vt[i])
                fc = bm.faces.new(tuple(reversed(q)) if flip else q)
                for lp in fc.loops:
                    k = (vb + vt).index(lp.vert)
                    lp[uv].uv = ((k % (n + 1)) / n, 1.0 if k > n else 0.0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ex3.add(build, T(x, Y3, z, ry), mat, tile=None)


curved_partition(10.4, 9.2, 1.2, M['p92'])
curved_partition(19.2, 5.4, -0.8, M['p90'])
# 둥근 라이트박스 (천장, 소개서 사진의 큰 원형 조명)
ex3.add(bevel_box(3.6, 0.2, 2.6, 0.08, 4), T(15.2, ROOF - 1.3, 6.8), M['wallWhite'], 1)
emit.add(bevel_box(3.4, 0.04, 2.4, 0.015, 2), T(15.2, ROOF - 1.46, 6.8), M['lightbox'])
for (sx, sz) in ((-1.4, -0.9), (1.4, -0.9), (-1.4, 0.9), (1.4, 0.9)):
    g, m = tube(V((15.2 + sx, ROOF - 1.2, 6.8 + sz)), V((15.2 + sx, ROOF + 0.05, 6.8 + sz)), 0.012, 6)
    ex3.add(g, m, M['steel'])
ex3.build()

# ── 선형 조명 (천장 강관 사이) ──────────────────────────────────
for (y, x0_, x1_) in ((F2, 4.5, 19.5), (F3, 8.5, 19.5), (ROOF + 0.12, -19.5, 19.5)):
    for zz in range(-12, 13, 3):
        emit.add(box(x1_ - x0_ - 1, 0.04, 0.08), T((x0_ + x1_) / 2, y - 0.7, zz + 0.1), M['strip'])
        light(C_LIGHT, f'lin_{y:.0f}_{zz}', 'AREA', ((x0_ + x1_) / 2, y - 0.75, zz + 0.1), ((x0_ + x1_) / 2, y - 3, zz + 0.1),
              energy=(x1_ - x0_) * 25, color=(1.0, 0.95, 0.88), size=1)
for zz in range(-12, 13, 3):                                  # 2F 뒤쪽 띠 아래 (x<4)
    pass
for x in range(-18, 3, 4):
    emit.add(box(0.08, 0.04, 5), T(x, F2 - 0.7, -11), M['strip'])

emit.build()
glass.build()
conv.build(smooth=True)
rot.build(smooth=True)
floors.build()
shell.build()

# 차량·차체 인스턴스
for i, (src, mtx) in enumerate(car_spots):
    instance(src, C_DYNAMIC, f'car_{i:02d}', mtx)
for i, (src, mtx) in enumerate(cradle_spots):
    instance(src, C_DYNAMIC, f'body_{i:02d}', mtx)

# ── 조명 ──────────────────────────────────────────────────────
# 낮: 유리벽으로 들어오는 흐린 하늘빛 + 실내 선형 조명 + 전시물 스폿
world = bpy.data.worlds.new('hy_world')   # 흐린 낮 하늘 (단색) — 유리 밖이 스튜디오 사진으로 보이지 않게
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.62, 0.68, 0.76, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
scene.world = world
for (x, z) in ((-6, 7.6), (-13.5, 4.5), (-15, -3)):
    light(C_LIGHT, f'car_spot_{x}', 'SPOT', (x + 1, ROOF - 0.5, z + 2), (x, 0.4, z), energy=2600, color=(1.0, 0.95, 0.88),
          spot=0.5, blend=0.6, size=0.2)
light(C_LIGHT, 'gate_spot', 'SPOT', (14, ROOF - 0.5, 1), (14, F3, GZ - 2), energy=3500, color=(0.95, 0.97, 1.0), spot=0.9, blend=0.6)
light(C_LIGHT, 'elantra_spot', 'SPOT', (15.2, ROOF - 1.5, 6.8), (16.5, F3, 8.4), energy=1500, color=(1.0, 0.96, 0.9), spot=1.1, blend=0.7)
light(C_LIGHT, 'rail_up', 'AREA', (-9, 6.5, 1.5), (-9, 14, 1.5), energy=900, color=(1.0, 1.0, 1.0), size=6)
light(C_LIGHT, 'sky_front', 'AREA', (0, 9, Z1 + 6), (0, 4, 0), energy=18000, color=(0.85, 0.9, 1.0), size=30)
light(C_LIGHT, 'sky_side', 'AREA', (X1 + 6, 9, 0), (0, 4, 0), energy=12000, color=(0.85, 0.9, 1.0), size=26)
light(C_LIGHT, 'sky_back', 'AREA', (X0 - 6, 9, 0), (0, 6, 0), energy=9000, color=(0.85, 0.9, 1.0), size=26)

# ── 카메라 (웹 시점과 같은 위치) ─────────────────────────────────
camera(C_CAM, 'cam_overview', (42, 34, 44), (-1, 6, -1), 42)
camera(C_CAM, 'cam_atrium', (5.2, 7.7, 12.4), (-12, 7.5, -3), 62)
camera(C_CAM, 'cam_conveyor', (-5, 1.6, 9), (-9, 13.5, -1), 64)
camera(C_CAM, 'cam_lobby', (0.5, 1.65, 13), (-12, 3.2, 2), 58)
camera(C_CAM, 'cam_gate', (14, F3 + 1.7, 7.5), (14, F3 + 2, -6), 58)
camera(C_CAM, 'cam_heritage', (11, F3 + 1.7, 1.5), (17, F3 + 1, 9), 58)
scene.camera = bpy.data.objects['cam_lobby']
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
print('hyundai built:', {c.name: len(c.objects) for c in (C_STATIC, C_DYNAMIC, C_EMIT, C_LIGHT, C_CAM)})
