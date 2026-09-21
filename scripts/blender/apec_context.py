"""APEC 황룡원 — 잔디마당을 둘러싼 실제 시설 (apec_stage.py 다음에 실행)

  python3 scripts/blender/apec_site_graphics.py      (표면 텍스처, 한 번)
  python3 scripts/blender/bmcp.py exec scripts/blender/apec_context.py

배치 (황룡원 공식 조감도·현장 사진 기준, 웹 좌표 +x 오른쪽 / -z 뒤쪽(무대))
- 중도타워  잔디마당 왼쪽 뒤 모서리. 황룡사 9층 목탑 재현, 본체 68m + 상륜 → 약 85m.
            1층 약 9.5m, 2~9층 약 7m, 기단 폭 약 30m → 최상층 약 21m.
            주칠 목부, 적갈색 동기와, 층마다 금빛 卍자 난간 발코니, 처마 네 귀 흰 조명, 창마다 호박색 불빛.
            흰 화강석 낮은 기단과 난간, 잔디 쪽 가운데 계단.
- 일주문    타워 옆 길가 입구. 2층 누문, 주칠 기둥, 큰 판문, '皇龍院' 현판.
- 회랑      일주문에서 연수동까지 잔디마당 왼쪽(길 쪽)을 따라 이어지는 회랑.
            둥근 화강석 기둥 + 주칠 서까래 + 짙은 회색 기와 맞배지붕, 가운데에 누각 하나.
- 정원      회랑 바깥(길 쪽)의 연못·괴석·육각 정자와 돌다리.
- 신평루    잔디마당 오른쪽 끝의 2층 누각. 붉은 계자 난간, 팔작지붕.
- 연수동    잔디마당 앞쪽을 가로막는 현대식 4층 건물. 1~3층 밝은 회색 화강석 판 + 긴 창,
            4층 옥상은 한옥 객실(귀빈실·평안재·행복재)과 그 앞의 넓은 석재 테라스
            → APEC 만찬 사진('귀빈동 테라스')을 찍은 자리.
"""
import importlib
import math
import random
import sys

sys.path.insert(0, '/Users/hare/Documents/큐비크스홈페이지/scripts/blender')
import lib  # noqa: E402

importlib.reload(lib)
from lib import (PI, SHOTS, Assembly, T, bevel_box, box, camera, cyl, light, material, plane, sphere, tube)  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

random.seed(11)
C_STATIC = bpy.data.collections['STATIC']
C_EMIT = bpy.data.collections['EMISSIVE']
C_LIGHT = bpy.data.collections['LIGHTS']
C_CAM = bpy.data.collections['CAMERAS']
for name in ('pagoda', 'halls', 'garden', 'yeonsu', 'pines', 'context_emissive'):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
for o in [o for o in C_LIGHT.objects if o.name.startswith(('pagoda_', 'hall_', 'site_'))]:
    bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in C_CAM.objects if o.name == 'cam_terrace']:
    bpy.data.objects.remove(o, do_unlink=True)


def mat(name, *args, **kw):
    return bpy.data.materials.get(name) or material(name, *args, **kw)


M = {
    # 중도타워
    'copper': mat('copperTile', 'ceramic_roof_01', (0.22, 0.13, 0.1), 0.5),          # 적갈색 동기와
    'vermilion': mat('vermilion', 'dark_wooden_planks', (0.95, 0.34, 0.2), 0.65),     # 주칠 기둥·창방
    'bracket': mat('bracket', 'dark_wooden_planks', (0.72, 0.24, 0.13), 0.7),        # 공포
    'wallWood': mat('wallWood', 'dark_wooden_planks', (0.5, 0.2, 0.11), 0.7),
    'goldRail': mat('goldRail', image_base=f'{SHOTS}/apec_rail.png', rough=0.4),
    'deck': mat('deckWood', 'dark_wooden_planks', (0.55, 0.3, 0.18), 0.7),
    'gold': mat('finialGold', None, (0.85, 0.62, 0.25), 0.3, 1.0),
    'windowGlow': mat('windowGlow', emit_image=f'{SHOTS}/apec_windows.png', emit_strength=3.2, rough=0.5),
    'eaveLamp': mat('eaveLamp', None, (1, 1, 1), emit=(1.0, 0.97, 0.9), emit_strength=80),
    # 석재
    'granite': mat('granite', 'rock_tile_floor_02', (0.86, 0.86, 0.84), 0.8),
    'balustrade': mat('balustrade', 'marble_01', (0.92, 0.92, 0.9), 0.6),
    'pillarStone': mat('pillarStone', 'concrete_floor_01', (0.72, 0.72, 0.7), 0.8),
    # 한옥
    'tileGrey': mat('tileGrey', 'ceramic_roof_01', (0.13, 0.14, 0.15), 0.55),
    'rafter': mat('rafter', 'dark_wooden_planks', (0.85, 0.3, 0.17), 0.7),
    'door': mat('gateDoor', 'dark_wooden_planks', (0.62, 0.3, 0.16), 0.7),
    'fret': mat('fretRail', image_base=f'{SHOTS}/apec_fret.png', rough=0.6),
    'hanji': mat('hanji', emit_image=f'{SHOTS}/apec_hanji.png', emit_strength=1.6, rough=0.8),
    'plaque': mat('plaque', None, (0.08, 0.05, 0.04), 0.5),
    # 연수동
    'facade': mat('yeonsuFacade', image_base=f'{SHOTS}/apec_yeonsu.png', rough=0.7),
    'stoneWall': mat('stoneWall', 'painted_plaster_wall', (0.8, 0.8, 0.77), 0.8),
    'terrace': mat('terraceStone', 'rock_tile_floor_02', (0.7, 0.7, 0.68), 0.75),
    'steelRail': mat('steelRail', None, (0.35, 0.36, 0.38), 0.4, 0.8),
    'parasol': mat('parasol', None, (0.9, 0.88, 0.82), 0.8),
    # 정원
    'water': mat('pond', None, (0.02, 0.035, 0.04), 0.08),
    'rock': mat('gardenRock', 'rock_tile_floor_02', (0.45, 0.43, 0.4), 0.9),
    'shrub': mat('shrub', None, (0.03, 0.07, 0.03), 0.95, sheen=0.2),
    'pineNeedle': mat('pineNeedle', None, (0.012, 0.03, 0.015), 0.95, sheen=0.2),
    'pineBark': mat('pineBark', 'dark_wooden_planks', (0.45, 0.25, 0.16), 0.9),
}

glow = Assembly('context_emissive', C_EMIT)


# ── 공통 도형 ─────────────────────────────────────────────────
def hip_roof(hw, hd, h, ridge=0.85, lift=None, curve=1.8, seg_u=12, seg_t=8, thickness=0.22):
    """곡선 우진각(모임) 지붕. 네 귀가 lift 만큼 들린다"""
    lift = h * 0.3 if lift is None else lift
    tz = hd * (1 - ridge)
    tx = max(hw - hd * ridge, tz)
    sides = (
        lambda a, rx, rz: (a * rx, rz),
        lambda a, rx, rz: (rx, -a * rz),
        lambda a, rx, rz: (-a * rx, -rz),
        lambda a, rx, rz: (-rx, a * rz),
    )

    def build(bm):
        for side in sides:
            grid = []
            for j in range(seg_t + 1):
                t = j / seg_t
                rx = tx + (hw - tx) * t
                rz = tz + (hd - tz) * t
                row = []
                for i in range(seg_u + 1):
                    a = i / seg_u * 2 - 1
                    x, z = side(a, rx, rz)
                    y = h * (1 - t) ** curve + lift * t ** 3 * abs(a) ** 4
                    row.append(bm.verts.new((x, y, z)))
                grid.append(row)
            for j in range(seg_t):
                for i in range(seg_u):
                    bm.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]))
        if tz > 0.01:
            bm.faces.new([bm.verts.new(p) for p in ((-tx, h, -tz), (-tx, h, tz), (tx, h, tz), (tx, h, -tz))])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thickness)
    return build


def gable_roof(length, width, h, thickness=0.25, sag=0.25, seg=10):
    """맞배지붕: 가운데가 살짝 처진 두 경사면 (로컬 x = 용마루 방향)"""
    def build(bm):
        for s in (-1, 1):
            grid = []
            for j in range(seg + 1):
                t = j / seg
                z = s * width / 2 * t
                y = h * (1 - t) - sag * math.sin(PI * t)
                grid.append([bm.verts.new((x, y, z)) for x in (-length / 2, length / 2)])
            for j in range(seg):
                a, b = grid[j], grid[j + 1]
                bm.faces.new((a[0], a[1], b[1], b[0]) if s > 0 else (a[0], b[0], b[1], a[1]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thickness)
    return build


def panel_ring(asm, cx, y, cz, half, h, material, seg=4.0, inset=0.0, skip=None):
    """네 면을 따라 그래픽 판(난간·창호)을 앞뒤 두 장씩 세운다"""
    L = half * 2
    n = max(1, round(L / seg))
    w = L / n
    for k in range(n):
        off = -half + w * (k + 0.5)
        for ry, (px, pz) in ((0, (off, half)), (PI, (-off, -half)), (PI / 2, (half, -off)), (-PI / 2, (-half, off))):
            if skip and skip(px, pz):
                continue
            base = T(cx + px, y + h / 2, cz + pz, ry)
            asm.add(plane(w - 0.02, h), base, material, tile=None)
            asm.add(plane(w - 0.02, h), base @ T(0, 0, -0.03, PI), material, tile=None)


def window_band(cx, y, cz, half, h, bay=1.3):
    """네 면에 불 켜진 창호 (텍스처 한 장 = 4칸)"""
    L = half * 2
    n = max(1, round(L / (bay * 4)))
    w = L / n
    for k in range(n):
        off = -half + w * (k + 0.5)
        for ry, (px, pz) in ((0, (off, half)), (PI, (-off, -half)), (PI / 2, (half, -off)), (-PI / 2, (-half, off))):
            glow.add(plane(w - 0.05, h), T(cx + px, y, cz + pz, ry), M['windowGlow'], tile=None)


def balustrade(asm, points, h=1.0, post=2.0):
    """흰 돌난간: 동자기둥 + 난간대 두 줄 + 하방"""
    for a, b in zip(points[:-1], points[1:]):
        a, b = V(a), V(b)
        d = b - a
        n = max(1, round(d.length / post))
        for k in range(n + 1):
            p = a + d * (k / n)
            asm.add(bevel_box(0.26, h + 0.25, 0.26, 0.03), T(p.x, p.y + (h + 0.25) / 2, p.z), M['balustrade'], 1)
        for ry in (h * 0.92, h * 0.5):
            g, m = tube(a + V((0, ry, 0)), b + V((0, ry, 0)), 0.07, 8)
            asm.add(g, m, M['balustrade'])
        g, m = tube(a + V((0, 0.12, 0)), b + V((0, 0.12, 0)), 0.12, 6)
        asm.add(g, m, M['balustrade'])


# ── 중도타워 ──────────────────────────────────────────────────
PX, PZ = -26, -43
BASE_Y = 1.6
pagoda = Assembly('pagoda', C_STATIC)

# 기단: 흰 화강석 2단 + 돌난간 + 잔디 쪽 가운데 계단
PH = 19.0
pagoda.add(bevel_box(PH * 2, BASE_Y, PH * 2, 0.05), T(PX, BASE_Y / 2, PZ), M['granite'], 1.5)
pagoda.add(bevel_box(PH * 2 + 1.2, 0.4, PH * 2 + 1.2, 0.04), T(PX, 0.2, PZ), M['granite'], 1.5)
SW = 5.5  # 계단 반폭
e = PH - 0.3
balustrade(pagoda, [(PX - SW, BASE_Y, PZ + e), (PX - e, BASE_Y, PZ + e), (PX - e, BASE_Y, PZ - e),
                    (PX + e, BASE_Y, PZ - e), (PX + e, BASE_Y, PZ + e), (PX + SW, BASE_Y, PZ + e)])
for k in range(6):
    hstep = BASE_Y - k * BASE_Y / 6
    pagoda.add(box(SW * 2, hstep, 0.42), T(PX, hstep / 2, PZ + PH + 0.21 + k * 0.42), M['granite'], 1.5)
for sx in (-1, 1):  # 계단 옆 소맷돌
    pagoda.add(bevel_box(0.5, BASE_Y + 0.9, 2.8, 0.05), T(PX + sx * (SW + 0.25), (BASE_Y + 0.9) / 2, PZ + PH + 1.2), M['balustrade'], 1)

eave_points = []
y = BASE_Y
for i in range(9):
    w = 30.0 - i * 1.15            # 기둥 열 폭
    H = 9.5 if i == 0 else 7.0
    half = w / 2
    core = half - 0.8               # 창호 벽
    top = i == 8

    # 발코니 마루 + 금빛 卍자 난간 (2층부터: 아래층 지붕 위)
    if i > 0:
        dh = half + 1.3
        pagoda.add(box(dh * 2, 0.32, dh * 2), T(PX, y + 0.16, PZ), M['deck'], 1.5)
        panel_ring(pagoda, PX, y + 0.32, PZ, dh - 0.05, 1.05, M['goldRail'], seg=4.0)
        for (x, z) in ((dh, dh), (-dh, dh), (dh, -dh), (-dh, -dh)):
            pagoda.add(box(0.28, 1.25, 0.28), T(PX + x, y + 0.9, PZ + z), M['goldRail'], 1)
    else:
        pagoda.add(bevel_box(w + 1.6, 0.45, w + 1.6, 0.04), T(PX, y + 0.22, PZ), M['granite'], 1.5)

    wall_h = H - 2.6
    # 벽체 + 창호
    pagoda.add(box(core * 2, H - 0.4, core * 2), T(PX, y + (H - 0.4) / 2, PZ), M['wallWood'], 1.5)
    window_band(PX, y + 0.35 + wall_h * 0.46, PZ, core + 0.02, wall_h * 0.78)
    # 기둥 (주칠)
    bays = 7 if i < 5 else 5
    for k in range(bays + 1):
        t = -half + k * w / bays
        for (x, z) in ((t, half), (t, -half), (half, t), (-half, t)):
            pagoda.add(cyl(0.3, 0.32, wall_h, 12), T(PX + x, y + wall_h / 2, PZ + z), M['vermilion'], 1)
    # 창방·평방
    pagoda.add(box(w + 0.5, 0.55, w + 0.5), T(PX, y + wall_h + 0.28, PZ), M['vermilion'], 1)
    pagoda.add(box(w + 0.9, 0.3, w + 0.9), T(PX, y + wall_h + 0.7, PZ), M['bracket'], 1)
    # 공포 (하앙): 칸마다 밖으로 내민 쇠서
    for k in range(bays + 1):
        t = -half + k * w / bays
        for (x, z, ry) in ((t, half, 0), (t, -half, PI), (half, t, PI / 2), (-half, t, -PI / 2)):
            pagoda.add(box(0.36, 0.34, 2.0), T(PX + x, y + wall_h + 1.05, PZ + z, ry) @ T(0, 0, 0.7), M['bracket'], 1)
            pagoda.add(box(0.3, 0.26, 1.4), T(PX + x, y + wall_h + 1.4, PZ + z, ry) @ T(0, 0, 1.2, 0, -0.35), M['bracket'], 1)
    # 지붕
    eave = y + H - 1.0
    if top:
        rh, hb = 5.2, half + 3.6
        pagoda.add(hip_roof(hb, hb, rh, ridge=0.98, lift=1.1, curve=1.5, thickness=0.3), T(PX, eave, PZ), M['copper'], 1.4)
    else:
        rh, hb = 2.2, half + 3.4
        inner = half - 1.0
        pagoda.add(hip_roof(hb, hb, rh, ridge=1 - inner / hb, lift=0.9, thickness=0.28), T(PX, eave, PZ), M['copper'], 1.4)
    # 처마 네 귀 흰 조명
    for (sx, sz) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        p = (PX + sx * (hb - 0.1), eave + (1.1 if top else 0.9) - 0.1, PZ + sz * (hb - 0.1))
        glow.add(sphere(0.24, 2), T(*p), M['eaveLamp'])
        eave_points.append(p)
    y += H

# 상륜부 (금빛): 노반 → 복발 → 보륜 9개 → 보개 → 수연 → 용차·보주
ty = y + 3.6
pagoda.add(bevel_box(2.6, 1.0, 2.6, 0.08), T(PX, ty + 0.5, PZ), M['gold'], 1)
pagoda.add(sphere(1.2, 3), T(PX, ty + 1.6, PZ, sy=0.6), M['gold'])
pagoda.add(cyl(0.22, 0.32, 14.5, 12), T(PX, ty + 8.4, PZ), M['gold'])
for k in range(9):
    r = 1.05 - k * 0.06
    pagoda.add(cyl(r, r, 0.22, 24), T(PX, ty + 2.8 + k * 0.95, PZ), M['gold'])
pagoda.add(cyl(0.3, 1.3, 0.8, 24), T(PX, ty + 11.8, PZ), M['gold'])
pagoda.add(sphere(0.55, 2), T(PX, ty + 13.2, PZ), M['gold'])
pagoda.add(sphere(0.42, 2), T(PX, ty + 14.6, PZ), M['gold'])
pagoda.add(sphere(0.3, 2), T(PX, ty + 15.8, PZ), M['gold'])
pagoda.build(smooth=False)
TOP = ty + 16.1
print('pagoda top', round(TOP, 1))

# 처마 조명 (광원은 층마다 잔디 쪽 두 귀만 — 베이크 시간)
for n, p in enumerate(eave_points):
    if p[2] > PZ:
        light(C_LIGHT, f'pagoda_lamp_{n}', 'POINT', (p[0], p[1] - 0.3, p[2]), energy=110, color=(1.0, 0.96, 0.9), size=0.2)
# 기단 앞 업라이트 (따뜻한 투광) — 잔디 쪽과 오른쪽 면
for ux in (-10, 0, 10):
    light(C_LIGHT, f'pagoda_up_f{ux}', 'SPOT', (PX + ux, BASE_Y + 0.5, PZ + 18), (PX + ux * 0.6, 28, PZ + 12),
          energy=26000, color=(1.0, 0.72, 0.42), spot=0.55, blend=0.7, size=0.4)
for uz in (-8, 6):
    light(C_LIGHT, f'pagoda_up_r{uz}', 'SPOT', (PX + 18, BASE_Y + 0.5, PZ + uz), (PX + 12, 28, PZ + uz * 0.6),
          energy=18000, color=(1.0, 0.72, 0.42), spot=0.55, blend=0.7, size=0.4)
light(C_LIGHT, 'pagoda_crown', 'SPOT', (PX + 14, 40, PZ + 30), (PX, TOP - 8, PZ),
      energy=30000, color=(1.0, 0.8, 0.5), spot=0.18, blend=0.5, size=0.3)


# ── 한옥 부재 ─────────────────────────────────────────────────
halls = Assembly('halls', C_STATIC)


def ridge(asm, frame, length, y):
    asm.add(bevel_box(length, 0.45, 0.55, 0.06), frame @ T(0, y, 0), M['tileGrey'], 1)
    for sx in (-1, 1):  # 용마루 끝 치미
        asm.add(bevel_box(0.5, 0.9, 0.6, 0.08), frame @ T(sx * length / 2, y + 0.25, 0), M['tileGrey'], 1)


def rafters(asm, frame, length, depth, y, step=0.55):
    """처마 밑 주칠 서까래 (끝만 보이게 짧게)"""
    n = int(length / step)
    for k in range(n + 1):
        x = -length / 2 + k * length / n
        for s in (-1, 1):
            asm.add(box(0.14, 0.14, 1.4), frame @ T(x, y, s * (depth / 2 - 0.5), 0, s * 0.45), M['rafter'], 1)


# ── 일주문 (타워 옆 길가 입구, 길 = -x 방향) ─────────────────────
def iljumun(cx, cz):
    f = T(cx, 0, cz, PI / 2)  # 로컬 x = 월드 z (문의 폭), 로컬 z = 길 방향
    W, D = 12.0, 5.0
    halls.add(bevel_box(W + 2, 0.5, D + 2, 0.04), f @ T(0, 0.25, 0), M['granite'], 1.5)
    xs = (-W / 2, -W / 6, W / 6, W / 2)
    for x in xs:
        for z in (-D / 2, D / 2):
            halls.add(cyl(0.36, 0.4, 6.4, 16), f @ T(x, 0.5 + 3.2, z), M['vermilion'], 1)
    for a, b in zip(xs[:-1], xs[1:]):  # 판문
        halls.add(box(b - a - 0.8, 4.6, 0.18), f @ T((a + b) / 2, 0.5 + 2.3, 0), M['door'], 1.2)
    halls.add(box(W + 0.8, 0.6, D + 0.6), f @ T(0, 6.9 + 0.3, 0), M['vermilion'], 1)
    halls.add(box(W + 1.4, 0.8, D + 1.4), f @ T(0, 7.8, 0), M['bracket'], 1)
    # 아래 지붕(좌우 날개) + 위층 누 + 윗지붕
    halls.add(hip_roof(W / 2 + 2.4, D / 2 + 2.4, 2.2, ridge=0.75, lift=0.9), f @ T(0, 7.8, 0), M['tileGrey'], 1.4)
    halls.add(box(W / 3 + 0.8, 3.0, D - 0.6), f @ T(0, 10.0 + 1.5, 0), M['vermilion'], 1)
    for s in (-1, 1):
        g = f @ T(0, 10.0, s * (D / 2 - 0.1))
        halls.add(plane(W / 3 + 0.6, 1.0), g @ T(0, 0.5, 0.05, 0 if s > 0 else PI), M['goldRail'], tile=None)
        halls.add(box(3.6, 1.0, 0.12), g @ T(0, 2.0, 0.1 * s), M['plaque'], 1)  # 皇龍院 현판
    halls.add(hip_roof(W / 3 / 2 + 3.2, D / 2 + 2.6, 3.0, ridge=0.8, lift=1.1), f @ T(0, 13.0, 0), M['tileGrey'], 1.4)
    ridge(halls, f, W / 3 * 0.9, 16.1)
    light(C_LIGHT, 'site_gate', 'AREA', tuple(f @ V((0, 9.5, D + 4))), tuple(f @ V((0, 4, 0))),
          energy=2400, color=(1.0, 0.78, 0.5), size=8)


# ── 회랑 (일주문 → 연수동, 잔디마당 왼쪽) ──────────────────────
CX = -39.0            # 회랑 중심선 x
CZ0, CZ1 = -11.0, 26.5
CW = 4.2              # 회랑 폭


def corridor():
    L = CZ1 - CZ0
    mid = (CZ0 + CZ1) / 2
    f = T(CX, 0, mid, PI / 2)   # 로컬 x = 회랑 길이 방향
    halls.add(bevel_box(L, 0.4, CW + 1.2, 0.04), f @ T(0, 0.2, 0), M['granite'], 1.5)
    n = round(L / 3.0)
    for k in range(n + 1):
        x = -L / 2 + k * L / n
        for z in (-CW / 2, CW / 2):
            halls.add(cyl(0.27, 0.3, 3.2, 16), f @ T(x, 0.4 + 1.6, z), M['pillarStone'], 1)
            halls.add(box(0.7, 0.35, 0.7), f @ T(x, 0.4 + 0.17, z), M['granite'], 1)
        halls.add(box(0.26, 0.4, CW + 0.4), f @ T(x, 3.8, 0), M['rafter'], 1)                  # 대들보
    for z in (-CW / 2, CW / 2):
        halls.add(box(L + 0.4, 0.5, 0.3), f @ T(0, 3.85, z), M['rafter'], 1)                  # 도리
    rafters(halls, f, L, CW + 2.6, 3.9, step=0.6)
    halls.add(gable_roof(L + 1.2, CW + 3.2, 1.9, sag=0.18), f @ T(0, 4.1, 0), M['tileGrey'], 1.4)
    ridge(halls, f, L + 1.0, 6.1)
    # 가운데 누각: 기둥을 높여 모임지붕을 얹는다
    px = 2.0
    for x in (px - 3, px + 3):
        for z in (-CW / 2 - 0.6, CW / 2 + 0.6):
            halls.add(cyl(0.3, 0.32, 5.4, 16), f @ T(x, 0.4 + 2.7, z), M['vermilion'], 1)
    halls.add(box(7.0, 0.5, CW + 1.8), f @ T(px, 5.9, 0), M['bracket'], 1)
    halls.add(hip_roof(5.2, CW / 2 + 2.6, 2.6, ridge=0.7, lift=1.0), f @ T(px, 6.1, 0), M['tileGrey'], 1.4)
    ridge(halls, f, 3.0, 8.7)
    for k in range(0, n, 3):
        x = -L / 2 + (k + 0.5) * L / n
        light(C_LIGHT, f'site_corr_{k}', 'POINT', tuple(f @ V((x, 3.3, 0))), energy=90, color=(1.0, 0.75, 0.45), size=0.3)


# ── 신평루 (잔디마당 오른쪽 끝 2층 누각) ─────────────────────────
def sinpyeongru(cx, cz):
    f = T(cx, 0, cz, -PI / 2)   # 로컬 +z = 잔디 쪽(-x)
    W, D = 11.4, 7.2
    halls.add(bevel_box(W + 1.6, 1.0, D + 1.6, 0.05), f @ T(0, 0.5, 0), M['granite'], 1.5)
    xs = [-W / 2 + k * W / 3 for k in range(4)]
    zs = [-D / 2, 0, D / 2]
    for x in xs:
        for z in zs:
            halls.add(cyl(0.3, 0.32, 7.2, 14), f @ T(x, 1.0 + 3.6, z), M['vermilion'], 1)
    halls.add(box(W + 1.8, 0.3, D + 1.8), f @ T(0, 3.9, 0), M['deck'], 1.2)                     # 누마루
    halls.add(box(W + 1.8, 0.4, D + 1.8), f @ T(0, 3.55, 0), M['rafter'], 1)
    for (px, pz, ry, ln) in ((0, D / 2 + 0.85, 0, W + 1.7), (0, -D / 2 - 0.85, PI, W + 1.7),
                             (W / 2 + 0.85, 0, PI / 2, D + 1.7), (-W / 2 - 0.85, 0, -PI / 2, D + 1.7)):
        g = f @ T(px, 4.05 + 0.45, pz, ry)
        halls.add(plane(ln, 0.9), g, M['fret'], tile=None)
        halls.add(plane(ln, 0.9), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
    halls.add(box(W + 0.6, 0.55, D + 0.6), f @ T(0, 8.1, 0), M['vermilion'], 1)
    halls.add(box(W + 1.2, 0.6, D + 1.2), f @ T(0, 8.65, 0), M['bracket'], 1)
    rafters(halls, f, W + 2, D + 3.6, 8.8, step=0.55)
    halls.add(hip_roof(W / 2 + 2.6, D / 2 + 2.4, 3.6, ridge=0.8, lift=1.2), f @ T(0, 8.9, 0), M['tileGrey'], 1.4)
    ridge(halls, f, W * 0.55, 12.6)
    for x in (-W / 3, W / 3):
        light(C_LIGHT, f'site_sinpyeong_{x:.0f}', 'POINT', tuple(f @ V((x, 7.2, 0))), energy=70, color=(1.0, 0.72, 0.42), size=0.4)


# ── 정원 (회랑 바깥, 연못 · 괴석 · 육각 정자 · 돌다리) ─────────────
garden = Assembly('garden', C_STATIC)


def rock(px, pz, s):
    def build(bm, s=s):
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        k = [random.uniform(0.75, 1.25) for _ in range(3)]
        for v in bm.verts:
            v.co.x *= s * k[0] * (1 + random.uniform(-0.15, 0.15))
            v.co.y *= s * 0.6 * k[1] * (1 + random.uniform(-0.15, 0.15))
            v.co.z *= s * k[2] * (1 + random.uniform(-0.15, 0.15))
    garden.add(build, T(px, s * 0.2, pz, random.uniform(0, PI)), M['rock'], 1.2)


def shrub(px, pz, s):
    def build(bm, s=s):
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        for v in bm.verts:
            v.co *= s * (1 + random.uniform(-0.1, 0.1))
            v.co.y *= 0.65
    garden.add(build, T(px, s * 0.45, pz), M['shrub'], 1)


def garden_block():
    # 연못 (불규칙한 테두리를 괴석으로)
    pond_c, pond_r = V((-55, 0, 6)), (9.5, 12.0)
    garden.add(cyl(1, 1, 0.1, 40), T(pond_c.x, 0.05, pond_c.z, sx=pond_r[0], sz=pond_r[1]), M['water'], None)
    garden.add(cyl(1, 1, 0.3, 40), T(pond_c.x, -0.1, pond_c.z, sx=pond_r[0] + 1.2, sz=pond_r[1] + 1.2), M['granite'], 1.5)
    for k in range(34):
        a = k / 34 * 2 * PI
        rock(pond_c.x + math.cos(a) * (pond_r[0] + 0.6), pond_c.z + math.sin(a) * (pond_r[1] + 0.6), random.uniform(0.6, 1.2))
    for _ in range(26):
        a = random.uniform(0, 2 * PI)
        d = random.uniform(1.15, 1.6)
        shrub(pond_c.x + math.cos(a) * pond_r[0] * d, pond_c.z + math.sin(a) * pond_r[1] * d, random.uniform(0.7, 1.5))
    # 육각 정자 (연못 가운데 돌기단 위)
    hx, hz = pond_c.x - 1, pond_c.z - 2
    garden.add(cyl(3.6, 3.9, 1.2, 6), T(hx, 0.6, hz), M['granite'], 1.5)
    garden.add(cyl(3.3, 3.3, 0.25, 6), T(hx, 1.32, hz), M['deck'], 1.2)
    for k in range(6):
        a = k / 6 * 2 * PI
        garden.add(cyl(0.2, 0.22, 3.0, 12), T(hx + math.cos(a) * 3.0, 1.45 + 1.5, hz + math.sin(a) * 3.0), M['vermilion'], 1)
        a2 = a + PI / 6
        g = T(hx + math.cos(a2) * 2.6, 1.9, hz + math.sin(a2) * 2.6, PI / 2 - a2)
        garden.add(plane(2.9, 0.7), g, M['fret'], tile=None)
        garden.add(plane(2.9, 0.7), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
    garden.add(cyl(3.1, 3.1, 0.5, 6), T(hx, 4.7, hz), M['bracket'], 1)
    garden.add(cyl(0.3, 5.2, 2.8, 6), T(hx, 6.3, hz), M['tileGrey'], 1.4)
    garden.add(cyl(0.12, 0.3, 1.4, 8), T(hx, 8.3, hz), M['tileGrey'], 1)
    # 돌다리 (회랑 쪽에서 정자로)
    x0, x1 = CX - CW / 2 - 1.0, hx + 3.6
    n = 12
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        xa, xb = x0 + (x1 - x0) * t0, x0 + (x1 - x0) * t1
        ya, yb = 0.9 + 0.8 * math.sin(PI * t0), 0.9 + 0.8 * math.sin(PI * t1)
        garden.add(box(abs(xb - xa) + 0.05, 0.3, 2.2), T((xa + xb) / 2, (ya + yb) / 2, hz, 0, 0, math.atan2(yb - ya, xb - xa)), M['granite'], 1.2)
    for s in (-1, 1):
        balustrade(garden, [(x0 + 0.5, 1.2, hz + s * 1.0), ((x0 + x1) / 2, 1.9, hz + s * 1.0), (x1 - 0.5, 1.2, hz + s * 1.0)], h=0.55, post=1.6)
    # 회랑 따라 괴석·관목
    for z in range(-10, 26, 4):
        rock(CX - CW / 2 - 2.5 + random.uniform(-1, 1), z + random.uniform(-1, 1), random.uniform(0.5, 0.9))
        shrub(CX - CW / 2 - 4.5 + random.uniform(-1, 1), z + 2 + random.uniform(-1, 1), random.uniform(0.8, 1.4))
    light(C_LIGHT, 'site_pavilion', 'POINT', (hx, 4.2, hz), energy=380, color=(1.0, 0.75, 0.45), size=0.4)


# ── 연수동 (잔디마당 앞쪽, 옥상 한옥 + 테라스) ───────────────────
yeonsu = Assembly('yeonsu', C_STATIC)
YX0, YX1 = -43.0, 35.0
YZ0, YZ1 = 27.0, 47.0
FLOOR = 4.0
ROOF_Y = FLOOR * 3


def facade_face(x0, x1, z, facing):
    """외벽 한 면 (가로 방향 x, facing +1: +z 를 바라봄 / -1: -z)"""
    L = x1 - x0
    n = max(1, round(L / 8))
    w = L / n
    for fl in range(3):
        for k in range(n):
            x = x0 + w * (k + 0.5)
            ry = 0 if facing > 0 else PI
            yeonsu.add(plane(w, FLOOR), T(x, fl * FLOOR + FLOOR / 2, z + facing * 0.02, ry), M['facade'], tile=None)


def facade_side(z0, z1, x, facing):
    L = z1 - z0
    n = max(1, round(L / 8))
    w = L / n
    for fl in range(3):
        for k in range(n):
            z = z0 + w * (k + 0.5)
            yeonsu.add(plane(w, FLOOR), T(x + facing * 0.02, fl * FLOOR + FLOOR / 2, z, facing * PI / 2), M['facade'], tile=None)


def hanok_room(cx, cz, w, d, label):
    """옥상 한옥 객실: 주칠 기둥 · 불 켜진 띠살문 · 툇마루 + 계자 난간 · 팔작지붕"""
    y0 = ROOF_Y + 0.3
    f = T(cx, 0, cz, PI)   # 로컬 +z = 잔디 쪽(-z)
    yeonsu.add(bevel_box(w + 2.4, 0.6, d + 2.4, 0.04), f @ T(0, y0 + 0.3, 0), M['granite'], 1.5)   # 기단
    yeonsu.add(box(w, 3.4, d), f @ T(0, y0 + 0.6 + 1.7, 0), M['stoneWall'], 2)                         # 벽
    bays = max(3, round(w / 3))
    for k in range(bays + 1):
        x = -w / 2 + k * w / bays
        for z in (-d / 2 - 0.05, d / 2 + 0.05):
            yeonsu.add(cyl(0.2, 0.22, 3.6, 12), f @ T(x, y0 + 0.6 + 1.8, z), M['vermilion'], 1)
        if k < bays:
            xm = x + w / bays / 2
            glow.add(plane(w / bays - 0.5, 2.6), f @ T(xm, y0 + 0.6 + 1.5, d / 2 + 0.07), M['hanji'], tile=None)
    # 잔디 쪽 툇마루 + 붉은 계자 난간
    yeonsu.add(box(w + 1.2, 0.25, 1.8), f @ T(0, y0 + 0.95, d / 2 + 1.3), M['deck'], 1.2)
    g = f @ T(0, y0 + 1.1 + 0.45, d / 2 + 2.15)
    yeonsu.add(plane(w + 1.2, 0.9), g, M['fret'], tile=None)
    yeonsu.add(plane(w + 1.2, 0.9), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
    for x in (-w / 2 - 0.6, w / 2 + 0.6):
        yeonsu.add(cyl(0.16, 0.18, 3.2, 10), f @ T(x, y0 + 1.1 + 1.6, d / 2 + 2.15), M['vermilion'], 1)
    yeonsu.add(box(w + 0.6, 0.5, d + 0.6), f @ T(0, y0 + 4.2, 0), M['vermilion'], 1)
    rafters(yeonsu, f, w + 2.0, d + 4.6, y0 + 4.45, step=0.55)
    yeonsu.add(hip_roof(w / 2 + 2.6, d / 2 + 2.8, 3.2, ridge=0.8, lift=1.1), f @ T(0, y0 + 4.5, 0), M['tileGrey'], 1.4)
    ridge(yeonsu, f, max(w - d * 0.8, 2), y0 + 7.8)
    light(C_LIGHT, f'site_room_{label}', 'AREA', (cx, y0 + 4.0, cz - d / 2 - 2.0), (cx, y0, cz - d / 2 - 6),
          energy=600, color=(1.0, 0.76, 0.48), size=w * 0.5)


def yeonsu_block():
    # 본체 (지상 3층) + 외벽
    yeonsu.add(box(YX1 - YX0, ROOF_Y, YZ1 - YZ0), T((YX0 + YX1) / 2, ROOF_Y / 2, (YZ0 + YZ1) / 2), M['stoneWall'], 2)
    facade_face(YX0, YX1, YZ0, -1)
    facade_face(YX0, YX1, YZ1, 1)
    facade_side(YZ0, YZ1, YX0, -1)
    facade_side(YZ0, YZ1, YX1, 1)
    for fl in (1, 2):   # 층 사이 돌림띠
        yeonsu.add(box(YX1 - YX0 + 0.4, 0.3, YZ1 - YZ0 + 0.4), T((YX0 + YX1) / 2, fl * FLOOR, (YZ0 + YZ1) / 2), M['stoneWall'], 2)
    # 1층 잔디 쪽 필로티·캐노피
    yeonsu.add(box(22, 0.4, 4.0), T(-4, 4.3, YZ0 - 2.0), M['stoneWall'], 2)
    for x in (-14, -7, 0, 6):
        yeonsu.add(box(0.6, 4.1, 0.6), T(x, 2.05, YZ0 - 3.6), M['stoneWall'], 2)
    # 옥상 테라스: 석재 바닥 + 돌 난간벽 + 철제 난간
    yeonsu.add(box(YX1 - YX0 + 0.6, 0.3, YZ1 - YZ0 + 0.6), T((YX0 + YX1) / 2, ROOF_Y + 0.15, (YZ0 + YZ1) / 2), M['terrace'], 1.6)
    for (x0, z0, x1, z1) in ((YX0, YZ0, YX1, YZ0), (YX0, YZ1, YX1, YZ1), (YX0, YZ0, YX0, YZ1), (YX1, YZ0, YX1, YZ1)):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        L = max(abs(x1 - x0), abs(z1 - z0)) + 0.6
        sx, sz = (L, 0.4) if z0 == z1 else (0.4, L)
        yeonsu.add(box(sx, 0.7, sz), T(cx, ROOF_Y + 0.65, cz), M['stoneWall'], 1.5)
        a, b = V((x0, ROOF_Y + 1.35, z0)), V((x1, ROOF_Y + 1.35, z1))
        g, m = tube(a, b, 0.04, 8)
        yeonsu.add(g, m, M['steelRail'])
        n = max(1, round((b - a).length / 1.6))
        for k in range(n + 1):
            p = a + (b - a) * (k / n)
            yeonsu.add(box(0.05, 0.4, 0.05), T(p.x, ROOF_Y + 1.15, p.z), M['steelRail'], 1)
    # 한옥 객실 세 채 (잔디 쪽 앞줄, 툇마루가 잔디를 본다) — 사이와 뒤는 테라스
    hanok_room(-29, 33.9, 22, 7.5, 'vip')        # 귀빈실
    hanok_room(1, 33.9, 20, 7.5, 'pyeongan')     # 평안재
    hanok_room(25, 33.9, 14, 7.5, 'haengbok')    # 행복재
    # 테라스 가구: 파라솔 테이블 몇 조
    for (x, z) in ((-34, 43.0), (-14, 30.5), (-14, 43.0), (13.5, 30.5), (8, 43.0), (28, 43.0)):
        yeonsu.add(cyl(0.6, 0.6, 0.05, 20), T(x, ROOF_Y + 1.05, z), M['steelRail'], 1)
        yeonsu.add(cyl(0.05, 0.05, 2.4, 8), T(x, ROOF_Y + 1.5, z), M['steelRail'], 1)
        yeonsu.add(cyl(0.05, 1.5, 0.5, 16), T(x, ROOF_Y + 2.7, z), M['parasol'], 1)
        for k in range(4):
            a = k * PI / 2 + PI / 4
            yeonsu.add(box(0.5, 0.8, 0.5), T(x + math.cos(a) * 1.0, ROOF_Y + 0.7, z + math.sin(a) * 1.0), M['steelRail'], 1)
    # 외벽을 비추는 잔디 쪽 투광 (따뜻하게 아래에서 위로)
    for x in range(-38, 34, 12):
        light(C_LIGHT, f'site_wash_{x}', 'SPOT', (x, 0.3, YZ0 - 1.5), (x, 8, YZ0 + 0.6), energy=1400,
              color=(1.0, 0.8, 0.55), spot=0.6, blend=0.8, size=0.3)
    for x in (-14, 13.5):
        light(C_LIGHT, f'site_terrace_{x}', 'POINT', (x, ROOF_Y + 2.4, 30.5), energy=160, color=(1.0, 0.78, 0.5), size=0.3)


iljumun(CX, -17.0)
corridor()
sinpyeongru(40.5, -1.0)
halls.build()
garden_block()
garden.build(smooth=False)
yeonsu_block()
yeonsu.build()


# ── 소나무 ────────────────────────────────────────────────────
pines = Assembly('pines', C_STATIC)


def pine(px, pz, s=1.0):
    pts = [V((px, 0.1, pz))]
    lean = V((random.uniform(-0.5, 0.5), 1, random.uniform(-0.5, 0.5))).normalized()
    for k in range(5):
        prev = pts[-1]
        pts.append(prev + (lean * 1.1 + V((random.uniform(-0.35, 0.35), 0, random.uniform(-0.35, 0.35)))) * s)
    for k in range(len(pts) - 1):
        g, m = tube(pts[k], pts[k + 1], (0.32 - k * 0.04) * s, 10, caps=True)
        pines.add(g, m, M['pineBark'], 0.8)
    top = pts[-1]
    for k in range(9):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.6, 2.6) * s
        c = V((top.x + math.cos(a) * r, top.y - random.uniform(0.2, 2.4) * s, top.z + math.sin(a) * r))
        sx, sy = random.uniform(1.4, 2.2) * s, random.uniform(0.45, 0.7) * s

        def pad(bm, sx=sx, sy=sy):
            bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
            for v in bm.verts:
                v.co.x *= sx * (1 + random.uniform(-0.12, 0.12))
                v.co.z *= sx * (1 + random.uniform(-0.12, 0.12))
                v.co.y *= sy * (1 + random.uniform(-0.1, 0.1))
        pines.add(pad, T(c.x, c.y, c.z, random.uniform(0, PI)), M['pineNeedle'], 1)


# 잔디 앞쪽 큰 소나무 (테라스 사진 전경)
pine(2, 17.5, 1.25)
pine(8.5, 19.5, 1.0)
# 정원·타워 주변·신평루 뒤
for (x, z, s) in ((-62, -6, 1.0), (-48, 20, 0.9), (-64, 18, 1.1), (-47, -8, 0.8),
                  (-4, -30, 1.0), (18, -27, 1.1), (30, -24, 0.9), (48, -12, 1.2), (49, 10, 1.0), (46, 20, 0.9)):
    pine(x, z, s)
pines.build(smooth=True)
glow.build()

# 귀빈동(연수동 옥상 한옥) 테라스 — 실제 만찬 사진을 찍은 자리
camera(C_CAM, 'cam_terrace', (-12, 16.4, 28.6), (-3, 5, -14), 66)
print('context built')
