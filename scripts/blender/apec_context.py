"""APEC 황룡원 — 잔디마당을 둘러싼 실제 시설 + 무대 뒤 운영 공간 (apec_stage.py 다음에 실행)

  python3 scripts/blender/apec_site_graphics.py      (표면 텍스처, 한 번)
  python3 scripts/blender/bmcp.py exec scripts/blender/apec_context.py

배치는 위성사진 실측값(scripts/blender/site_survey.md)을 그대로 쓴다.
웹 좌표: MED(무대 앞 원형 디딤돌) = (6, -7.6), -x = 동남쪽(중도타워), +z = 북동쪽(회랑·길)
- 중도타워  중심 (-43, -11). 기단 30m·9층·약 85m. 주칠 목부, 적갈색 동기와, 층마다 금빛 卍자 난간,
            처마 네 귀 흰 조명. 흰 화강석 기단·돌난간, 잔디(+x) 쪽 계단. 흰 원형 동선(반지름 27)이 둘러쌈
- 일주문    회랑 동쪽 끝 (-41.5, 26). 2층 누문, 주칠 기둥, 판문, 皇龍院 현판
- 회랑      잔디 북동쪽 z 17~23. 둥근 화강석 기둥 + 주칠 서까래 + 회색 기와 맞배지붕, 가운데 누각
- 수공간    회랑과 도로 사이 연못·육각정·돌다리·곡선 산책로
- 신평루    무대 뒤 (11, -41) 2층 누각. 아래층에 콘솔 부스(초록 칸막이, 조명·음향·영상 콘솔, 모니터)
- 무대 뒤   대기용 흰 천막 두 동 (무대 바로 뒤)
- 연수동    북동동(x 23~69, z 20~51, 옥상 서쪽 테라스 = 귀빈동 테라스) + 북서동(x 46~66, z -35~13).
            옥상 한옥 A·B·B1·B2·B3 의 용마루 방향을 위성사진대로
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
for name in ('pagoda', 'halls', 'garden', 'yeonsu', 'yeonsu_ne', 'yeonsu_nw', 'pines', 'pine_needles', 'tree_leaves', 'backstage', 'context_emissive', 'context_glass'):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
for o in [o for o in C_LIGHT.objects if o.name.startswith(('pagoda_', 'hall_', 'site_'))]:
    bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in C_CAM.objects if o.name in ('cam_terrace', 'cam_console')]:
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
    'stoneWall': mat('stoneWall', 'painted_plaster_wall', (0.8, 0.8, 0.77), 0.8),
    'terrace': mat('terraceStone', 'rock_tile_floor_02', (0.7, 0.7, 0.68), 0.75),
    'steelRail': mat('steelRail', None, (0.35, 0.36, 0.38), 0.4, 0.8),
    'parasol': mat('parasol', None, (0.9, 0.88, 0.82), 0.8),
    # 정원
    'water': mat('pond', None, (0.02, 0.035, 0.04), 0.08),
    'rock': mat('gardenRock', 'rock_tile_floor_02', (0.45, 0.43, 0.4), 0.9),
    'shrub': mat('shrub', None, (0.03, 0.07, 0.03), 0.95, sheen=0.2),
    'pineNeedle': mat('pineNeedle', None, (0.012, 0.03, 0.015), 0.95, sheen=0.2),
    'pineBark': mat('pineBark', 'dark_wooden_planks', (0.42, 0.22, 0.14), 0.9),
    'pineLeaf': mat('pineLeaf', 'leafy_grass', (0.16, 0.26, 0.12), 0.9, normal=1.4),
    'needles': mat('pineNeedles', image_base=f'{SHOTS}/apec_pine_needles.png', color=(0.55, 0.66, 0.52), rough=0.8, alpha=True),
    'pineBarkRed': mat('pineBarkRed', 'dark_wooden_planks', (0.72, 0.36, 0.22), 0.85),
    'leaves': mat('treeLeaves', image_base=f'{SHOTS}/apec_leaves.png', color=(0.62, 0.7, 0.58), rough=0.8, alpha=True),
    'treeBark': mat('treeBark', 'dark_wooden_planks', (0.3, 0.26, 0.22), 0.9),
    'path': mat('pathStone', 'rock_tile_floor_02', (0.8, 0.79, 0.76), 0.8),
    'skylight': mat('skylight', None, (0.55, 0.75, 0.8), 0.05, transmission=1.0),
    # 무대 뒤 · 콘솔
    'tank': mat('ballastTank', 'cotton_jersey', (0.03, 0.03, 0.035), 0.7, normal=0.6),
    'tent': mat('tentWhite', 'cotton_jersey', (0.9, 0.9, 0.88), 0.8, normal=0.4),
    'drape': mat('drapeGreen', 'cotton_jersey', (0.28, 0.34, 0.12), 0.9, normal=0.6),
    'case': mat('roadCase', None, (0.03, 0.03, 0.035), 0.5),
    'alu': mat('tentAlu', None, (0.8, 0.8, 0.82), 0.35, 1.0),
    'uiLight': mat('uiLight', emit_image=f'{SHOTS}/apec_ui_light.png', emit_strength=2.0, rough=0.3),
    'uiAudio': mat('uiAudio', emit_image=f'{SHOTS}/apec_ui_audio.png', emit_strength=2.0, rough=0.3),
    'uiVideo': mat('uiVideo', emit_image=f'{SHOTS}/apec_ui_video.png', emit_strength=2.0, rough=0.3),
    'clipLamp': mat('clipLamp', None, (1, 1, 1), emit=(1.0, 0.92, 0.78), emit_strength=40),
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
PX, PZ = -43, -11
BASE_Y = 1.6
pagoda = Assembly('pagoda', C_STATIC)

# 흰 원형 동선 (위성사진의 흰 고리, 반지름 27.5) + 기단 주변 포장
pagoda.add(cyl(27.5, 27.5, 0.16, 96), T(PX, 0.08, PZ), M['granite'], 1.5)
# 기단: 흰 화강석 2단 + 돌난간 + 잔디(+x) 쪽 가운데 계단
PH = 19.0
pagoda.add(bevel_box(PH * 2, BASE_Y, PH * 2, 0.05), T(PX, BASE_Y / 2, PZ), M['granite'], 1.5)
pagoda.add(bevel_box(PH * 2 + 1.2, 0.4, PH * 2 + 1.2, 0.04), T(PX, 0.36, PZ), M['granite'], 1.5)
SW = 5.5  # 계단 반폭
e = PH - 0.3
balustrade(pagoda, [(PX + e, BASE_Y, PZ + SW), (PX + e, BASE_Y, PZ + e), (PX - e, BASE_Y, PZ + e),
                    (PX - e, BASE_Y, PZ - e), (PX + e, BASE_Y, PZ - e), (PX + e, BASE_Y, PZ - SW)])
for k in range(6):
    hstep = BASE_Y - k * BASE_Y / 6
    pagoda.add(box(0.42, hstep, SW * 2), T(PX + PH + 0.21 + k * 0.42, hstep / 2, PZ), M['granite'], 1.5)
for sz in (-1, 1):  # 계단 옆 소맷돌
    pagoda.add(bevel_box(2.8, BASE_Y + 0.9, 0.5, 0.05), T(PX + PH + 1.2, (BASE_Y + 0.9) / 2, PZ + sz * (SW + 0.25)), M['balustrade'], 1)

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

# 처마 조명 (광원은 잔디 쪽 두 귀만 — 베이크 시간)
for n, p in enumerate(eave_points):
    if p[0] > PX:
        light(C_LIGHT, f'pagoda_lamp_{n}', 'POINT', (p[0], p[1] - 0.3, p[2]), energy=110, color=(1.0, 0.96, 0.9), size=0.2)
# 기단 앞 업라이트 (따뜻한 투광) — 잔디(+x) 면과 회랑(+z) 면
for u in (-10, 0, 10):
    light(C_LIGHT, f'pagoda_up_x{u}', 'SPOT', (PX + 18, BASE_Y + 0.5, PZ + u), (PX + 12, 28, PZ + u * 0.6),
          energy=26000, color=(1.0, 0.72, 0.42), spot=0.55, blend=0.7, size=0.4)
for u in (-8, 6):
    light(C_LIGHT, f'pagoda_up_z{u}', 'SPOT', (PX + u, BASE_Y + 0.5, PZ + 18), (PX + u * 0.6, 28, PZ + 12),
          energy=18000, color=(1.0, 0.72, 0.42), spot=0.55, blend=0.7, size=0.4)
light(C_LIGHT, 'pagoda_crown', 'SPOT', (PX + 30, 40, PZ + 14), (PX, TOP - 8, PZ),
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


def hanok(asm, cx, cz, w, d, ry=0.0, y0=0.0, wall_h=3.4, veranda=True, base_h=0.6, label='', lamp=600):
    """한옥 한 채. 로컬 x = 용마루 방향(길이 w), 로컬 +z = 정면(툇마루·계자 난간)
    주칠 기둥 · 흰 회벽 · 불 켜진 띠살문(앞뒤) · 팔작지붕(우진각 + 용마루)"""
    f = T(cx, 0, cz, ry)
    asm.add(bevel_box(w + 2.4, base_h, d + 2.4, 0.04), f @ T(0, y0 + base_h / 2, 0), M['granite'], 1.5)
    yb = y0 + base_h
    asm.add(box(w, wall_h, d), f @ T(0, yb + wall_h / 2, 0), M['stoneWall'], 2)
    bays = max(3, round(w / 3))
    for k in range(bays + 1):
        x = -w / 2 + k * w / bays
        for z in (-d / 2 - 0.05, d / 2 + 0.05):
            asm.add(cyl(0.2, 0.22, wall_h + 0.2, 12), f @ T(x, yb + (wall_h + 0.2) / 2, z), M['vermilion'], 1)
        if k < bays:
            xm = x + w / bays / 2
            for sz, rot in ((1, 0), (-1, PI)):
                glow.add(plane(w / bays - 0.5, wall_h * 0.76), f @ T(xm, yb + wall_h * 0.44, sz * (d / 2 + 0.07), rot), M['hanji'], tile=None)
    if veranda:
        asm.add(box(w + 1.2, 0.25, 1.8), f @ T(0, yb + 0.35, d / 2 + 1.3), M['deck'], 1.2)
        g = f @ T(0, yb + 0.5 + 0.45, d / 2 + 2.15)
        asm.add(plane(w + 1.2, 0.9), g, M['fret'], tile=None)
        asm.add(plane(w + 1.2, 0.9), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
        for x in (-w / 2 - 0.6, w / 2 + 0.6):
            asm.add(cyl(0.16, 0.18, wall_h, 10), f @ T(x, yb + 0.5 + wall_h / 2, d / 2 + 2.15), M['vermilion'], 1)
    top = yb + wall_h
    asm.add(box(w + 0.6, 0.5, d + 0.6), f @ T(0, top + 0.1, 0), M['vermilion'], 1)
    rafters(asm, f, w + 2.0, d + 4.6, top + 0.35, step=0.55)
    rh = min(3.4, 1.4 + d * 0.3)
    asm.add(hip_roof(w / 2 + 2.6, d / 2 + 2.8, rh, ridge=0.8, lift=1.1), f @ T(0, top + 0.4, 0), M['tileGrey'], 1.4)
    ridge(asm, f, max(w - d * 0.8, 2), top + 0.4 + rh)
    if lamp:
        p = f @ V((0, top - 0.2, d / 2 + 2.0))
        t = f @ V((0, y0, d / 2 + 6))
        light(C_LIGHT, f'site_room_{label}', 'AREA', tuple(p), tuple(t), energy=lamp, color=(1.0, 0.76, 0.48), size=w * 0.5)


# ── 일주문 (회랑 동쪽 끝, 길 = -x 쪽에서 들어온다) ─────────────────
def iljumun(cx, cz):
    f = T(cx, 0, cz, PI / 2)  # 로컬 x = 월드 -z (문 폭), 로컬 +z = 월드 +x (안쪽)
    W, D = 16.0, 6.0
    halls.add(bevel_box(W + 2, 0.5, D + 2, 0.04), f @ T(0, 0.25, 0), M['granite'], 1.5)
    xs = (-W / 2, -W / 6, W / 6, W / 2)
    for x in xs:
        for z in (-D / 2, D / 2):
            halls.add(cyl(0.36, 0.4, 6.4, 16), f @ T(x, 0.5 + 3.2, z), M['vermilion'], 1)
    for a, b in zip(xs[:-1], xs[1:]):  # 판문
        halls.add(box(b - a - 0.8, 4.6, 0.18), f @ T((a + b) / 2, 0.5 + 2.3, 0), M['door'], 1.2)
    halls.add(box(W + 0.8, 0.6, D + 0.6), f @ T(0, 7.2, 0), M['vermilion'], 1)
    halls.add(box(W + 1.4, 0.8, D + 1.4), f @ T(0, 7.8, 0), M['bracket'], 1)
    rafters(halls, f, W + 3, D + 4.2, 8.1, step=0.55)
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


# ── 회랑 (일주문 → 연수동, 잔디 북동쪽 z 17~23) ───────────────────
CZ_ = 20.0
CX0, CX1 = -38.0, 23.0
CW = 4.2


def corridor():
    L = CX1 - CX0
    mid = (CX0 + CX1) / 2
    f = T(mid, 0, CZ_)   # 로컬 x = 월드 x
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
    # 가운데 누각 (위성사진의 밝은 지붕 칸, x -10 ~ -1)
    px = -5.5 - mid
    for x in (px - 3.5, px + 3.5):
        for z in (-CW / 2 - 0.6, CW / 2 + 0.6):
            halls.add(cyl(0.3, 0.32, 5.4, 16), f @ T(x, 0.4 + 2.7, z), M['vermilion'], 1)
    halls.add(box(8.0, 0.5, CW + 1.8), f @ T(px, 5.9, 0), M['bracket'], 1)
    halls.add(hip_roof(5.6, CW / 2 + 2.6, 2.6, ridge=0.7, lift=1.0), f @ T(px, 6.1, 0), M['tileGrey'], 1.4)
    ridge(halls, f, 3.4, 8.7)
    for k in range(0, n, 3):
        x = -L / 2 + (k + 0.5) * L / n
        light(C_LIGHT, f'site_corr_{k}', 'POINT', tuple(f @ V((x, 3.3, 0))), energy=90, color=(1.0, 0.75, 0.45), size=0.3)


# ── 신평루 (무대 뒤 2층 누각) ─────────────────────────────────────
SP = (11.0, -41.0)
SP_W, SP_D, SP_BASE = 11.0, 7.2, 1.0


def sinpyeongru(cx, cz):
    f = T(cx, 0, cz)          # 로컬 +z = 잔디·무대 쪽
    W, D = SP_W, SP_D
    halls.add(bevel_box(W + 1.6, SP_BASE, D + 1.6, 0.05), f @ T(0, SP_BASE / 2, 0), M['granite'], 1.5)
    for k in range(3):        # 앞 계단
        h = SP_BASE - k * SP_BASE / 3
        halls.add(box(4.0, h, 0.4), f @ T(0, h / 2, D / 2 + 0.8 + 0.2 + k * 0.4), M['granite'], 1.5)
    xs = [-W / 2 + k * W / 3 for k in range(4)]
    zs = [-D / 2, 0, D / 2]
    for x in xs:
        for z in zs:
            halls.add(cyl(0.32, 0.34, 7.2, 14), f @ T(x, SP_BASE + 3.6, z), M['vermilion'], 1)
    halls.add(box(W + 1.8, 0.3, D + 1.8), f @ T(0, 3.9 + SP_BASE, 0), M['deck'], 1.2)            # 누마루
    halls.add(box(W + 1.8, 0.4, D + 1.8), f @ T(0, 3.55 + SP_BASE, 0), M['rafter'], 1)
    for (px, pz, ry, ln) in ((0, D / 2 + 0.85, 0, W + 1.7), (0, -D / 2 - 0.85, PI, W + 1.7),
                             (W / 2 + 0.85, 0, PI / 2, D + 1.7), (-W / 2 - 0.85, 0, -PI / 2, D + 1.7)):
        g = f @ T(px, 4.05 + SP_BASE + 0.45, pz, ry)
        halls.add(plane(ln, 0.9), g, M['fret'], tile=None)
        halls.add(plane(ln, 0.9), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
    halls.add(box(W + 0.6, 0.55, D + 0.6), f @ T(0, 8.1 + SP_BASE, 0), M['vermilion'], 1)
    halls.add(box(W + 1.2, 0.6, D + 1.2), f @ T(0, 8.65 + SP_BASE, 0), M['bracket'], 1)
    rafters(halls, f, W + 2, D + 3.6, 8.8 + SP_BASE, step=0.55)
    halls.add(hip_roof(W / 2 + 2.6, D / 2 + 2.4, 3.6, ridge=0.8, lift=1.2), f @ T(0, 8.9 + SP_BASE, 0), M['tileGrey'], 1.4)
    ridge(halls, f, W * 0.55, 12.6 + SP_BASE)
    for x in (-W / 3, W / 3):
        light(C_LIGHT, f'site_sinpyeong_{x:.0f}', 'POINT', tuple(f @ V((x, 7.4 + SP_BASE, 0))), energy=70, color=(1.0, 0.72, 0.42), size=0.4)


def south_row():
    """무대 뒤 남쪽 줄: 흰 돌길 + 낮은 돌난간, 원형 광장, 한옥 별채"""
    halls.add(box(48, 0.14, 1.8), T(1, 0.07, -34.0), M['path'], 1.2)
    for (x0, x1) in ((-24, 4.5), (17.5, 25)):
        balustrade(halls, [(x0, 0.14, -34.9), (x1, 0.14, -34.9)], h=0.6, post=2.4)
    # 원형 광장 (방사형 포장)
    cx, cz, r = -17.0, -42.0, 5.5
    halls.add(cyl(r, r, 0.16, 64), T(cx, 0.08, cz), M['path'], 1.2)
    for k in range(24):
        a = k / 24 * 2 * PI
        halls.add(box(0.5, 0.05, 1.1), T(cx + math.cos(a) * (r - 0.8), 0.18, cz + math.sin(a) * (r - 0.8), PI / 2 - a), M['granite'], 1)
    halls.add(cyl(0.9, 0.9, 0.3, 24), T(cx, 0.3, cz), M['balustrade'], 1)
    # 한옥 별채 (용마루 x 방향)
    hanok(halls, -32.0, -41.0, 14.0, 6.0, ry=0.0, y0=0.0, wall_h=3.4, veranda=False, base_h=0.8, label='annex', lamp=300)


# ── 정원 (수공간: 연못 · 육각정 · 돌다리 · 곡선 산책로) ─────────────
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
            v.co *= s * (1 + random.uniform(-0.12, 0.12))
            v.co.y *= 0.65
    garden.add(build, T(px, s * 0.45, pz), M['shrub'], 1)


def garden_block():
    pond_c, pond_r = V((6, 0, 33)), (14.5, 8.5)
    garden.add(cyl(1, 1, 0.1, 48), T(pond_c.x, 0.05, pond_c.z, sx=pond_r[0], sz=pond_r[1]), M['water'], None)
    garden.add(cyl(1, 1, 0.3, 48), T(pond_c.x, -0.1, pond_c.z, sx=pond_r[0] + 1.0, sz=pond_r[1] + 1.0), M['granite'], 1.5)
    for k in range(40):
        a = k / 40 * 2 * PI
        rock(pond_c.x + math.cos(a) * (pond_r[0] + 0.5), pond_c.z + math.sin(a) * (pond_r[1] + 0.5), random.uniform(0.5, 1.1))
    for _ in range(22):
        a = random.uniform(0, 2 * PI)
        dd = random.uniform(1.12, 1.35)
        x, z = pond_c.x + math.cos(a) * pond_r[0] * dd, pond_c.z + math.sin(a) * pond_r[1] * dd
        if 23.5 < z and x < 22:
            shrub(x, z, random.uniform(0.7, 1.4))
    # 육각정 (연못 북쪽 가)
    hx, hz = 14.0, 41.0
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
    light(C_LIGHT, 'site_pavilion', 'POINT', (hx, 4.2, hz), energy=380, color=(1.0, 0.75, 0.45), size=0.4)
    # 돌다리 (회랑 누각 앞에서 연못 서쪽을 건너 산책로로)
    bx, z0, z1 = -3.5, 23.6, 42.5
    n = 14
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        za, zb = z0 + (z1 - z0) * t0, z0 + (z1 - z0) * t1
        ya, yb = 0.5 + 0.9 * math.sin(PI * t0), 0.5 + 0.9 * math.sin(PI * t1)
        garden.add(box(2.0, 0.3, abs(zb - za) + 0.05), T(bx, (ya + yb) / 2, (za + zb) / 2, 0, -math.atan2(yb - ya, zb - za)), M['granite'], 1.2)
    for s in (-1, 1):
        balustrade(garden, [(bx + s * 0.95, 0.8, z0 + 0.8), (bx + s * 0.95, 1.4, (z0 + z1) / 2), (bx + s * 0.95, 0.8, z1 - 0.8)], h=0.5, post=1.6)
    # 곡선 산책로 (위성사진의 흰 길)
    pts = [(-31, 26), (-28, 33), (-20, 38), (-10, 40), (-3.5, 43), (4, 46), (14, 48.5), (24, 50)]
    for (ax, az), (bx2, bz) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx2 - ax, bz - az)
        garden.add(box(L + 0.4, 0.1, 1.6), T((ax + bx2) / 2, 0.05, (az + bz) / 2, -math.atan2(bz - az, bx2 - ax)), M['path'], 1.2)
    # 회랑 따라 괴석·관목
    for x in range(-34, 22, 4):
        if -12 < x < 22:
            continue
        rock(x + random.uniform(-1, 1), CZ_ + CW / 2 + 2.5 + random.uniform(-0.5, 0.5), random.uniform(0.5, 0.9))
        shrub(x + 2 + random.uniform(-1, 1), CZ_ + CW / 2 + 4.5 + random.uniform(-1, 1), random.uniform(0.8, 1.4))


# ── 연수동 ─────────────────────────────────────────────────────
# 외벽은 판을 겹쳐 붙이지 않고 실제 깊이로 만든다: 화강석 모서리 기둥·칸 기둥·층 띠가 바깥면(0)까지 나오고
# 유리(방 안 불빛)는 0.3m 안쪽, 그 뒤에 몸체. 같은 평면에 두 면이 겹치는 곳이 없어 z-fighting 이 없다.
ye_ne = Assembly('yeonsu_ne', C_STATIC)
ye_nw = Assembly('yeonsu_nw', C_STATIC)
FLOOR = 4.0
ROOF_Y = FLOOR * 3
DEPTH = 0.45        # 기둥·띠가 몸체에서 나온 깊이
M['granite_clad'] = mat('graniteClad', 'granite_tile_03', (0.86, 0.86, 0.84), 0.7)
ROOMS = [mat(f'roomGlass_{t}', emit_image=f'{SHOTS}/apec_room_{t}.png', emit_strength=1.1, rough=0.1) for t in 'abc']


def wall(asm, sx, sz, L, ry, h, floors, parapet=1.3):
    """한 면: 로컬 x = 벽 방향(0~L), 로컬 +z = 바깥. 바깥면이 z=0"""
    f = T(sx, 0, sz, ry)
    fh = h / floors
    n = max(1, round((L - 1.8) / 7.6))
    w = (L - 1.8) / n
    xs = [0.9 + k * w for k in range(n + 1)]
    # 층 띠 (바닥 띠 + 층 사이 띠 + 난간벽)
    bands = [(0.0, 0.8)] + [(k * fh - 0.45, k * fh + 0.85) for k in range(1, floors)] + [(h - 0.45, h + parapet)]
    for y0, y1 in bands:
        asm.add(box(L - 1.8, y1 - y0, DEPTH), f @ T(L / 2, (y0 + y1) / 2, -DEPTH / 2), M['granite_clad'], 1.2)
    # 창: 기둥·띠 사이 구멍마다 안쪽 유리(방 불빛) + 창살
    for fl in range(floors):
        ya = 0.8 if fl == 0 else fl * fh + 0.85
        yb = (fl + 1) * fh - 0.45 if fl < floors - 1 else h - 0.45
        # 칸 기둥은 띠와 띠 사이 구간에만 (띠와 같은 바깥면에서 겹치지 않게 → z-fighting 없음)
        for x in xs[1:-1]:
            asm.add(box(0.8, yb - ya, DEPTH), f @ T(x, (ya + yb) / 2, -DEPTH / 2), M['granite_clad'], 1.2)
        for k in range(n):
            xa = xs[k] + (0.4 if k > 0 else 0)
            xb = xs[k + 1] - (0.4 if k < n - 1 else 0)
            glow.add(plane(xb - xa, yb - ya), f @ T((xa + xb) / 2, (ya + yb) / 2, -0.3), random.choice(ROOMS), tile=None)
            asm.add(box(xb - xa, 0.08, 0.3), f @ T((xa + xb) / 2, ya + 0.04, -0.15), M['granite_clad'], 1.2)   # 창대


def block(asm, x0, x1, z0, z1, h, floors, parapet=1.3, terrace=True):
    """모서리 기둥 4개 + 네 벽 + 안쪽 몸체 + 옥상"""
    asm.add(box(x1 - x0 - 0.7, h, z1 - z0 - 0.7), T((x0 + x1) / 2, h / 2, (z0 + z1) / 2), M['stoneWall'], 2)
    for (cx, cz) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
        ox = 0.45 if cx == x0 else -0.45
        oz = 0.45 if cz == z0 else -0.45
        asm.add(box(0.9, h + parapet, 0.9), T(cx + ox, (h + parapet) / 2, cz + oz), M['granite_clad'], 1.2)
    wall(asm, x1, z0, x1 - x0, PI, h, floors, parapet)          # -z 면
    wall(asm, x1, z1, z1 - z0, PI / 2, h, floors, parapet)      # +x 면
    wall(asm, x0, z1, x1 - x0, 0.0, h, floors, parapet)         # +z 면
    wall(asm, x0, z0, z1 - z0, -PI / 2, h, floors, parapet)     # -x 면
    if terrace:
        asm.add(box(x1 - x0 - 0.9, 0.3, z1 - z0 - 0.9), T((x0 + x1) / 2, h + 0.15, (z0 + z1) / 2), M['terrace'], 1.6)
        for (ax, az, bx, bz) in ((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
            a, b = V((ax, h + parapet + 0.25, az)), V((bx, h + parapet + 0.25, bz))
            g, m = tube(a, b, 0.035, 8)
            asm.add(g, m, M['steelRail'])


def yeonsu_block():
    Y = ROOF_Y + 0.3
    # 북동동 (옥상 서쪽 x 23~38 = 귀빈동 테라스)
    block(ye_ne, 23, 69, 20, 51, ROOF_Y, 3)
    hanok(ye_ne, 51.5, 41.0, 21.5, 8.4, ry=PI, y0=Y, label='A', lamp=500)             # 한옥 A: 용마루 x
    hanok(ye_ne, 44.5, 29.3, 11.8, 7.4, ry=-PI / 2, y0=Y, label='B', lamp=700)        # 한옥 B: 용마루 z, 테라스 쪽 정면
    # 연결동 + 천창 (유리)
    block(ye_ne, 40, 55, 12, 20, 8.0, 2)
    glass_roof.add(box(8, 1.0, 18), T(59, ROOF_Y + 0.8, 24), M['skylight'])
    # 귀빈동 테라스 가구 (파라솔 테이블)
    for (x, z) in ((27, 26), (27, 34), (27, 42), (31, 47)):
        ye_ne.add(cyl(0.6, 0.6, 0.05, 20), T(x, Y + 0.75, z), M['steelRail'], 1)
        ye_ne.add(cyl(0.05, 0.05, 2.4, 8), T(x, Y + 1.2, z), M['steelRail'], 1)
        ye_ne.add(cyl(0.05, 1.5, 0.5, 16), T(x, Y + 2.4, z), M['parasol'], 1)
        for k in range(4):
            a = k * PI / 2 + PI / 4
            ye_ne.add(box(0.5, 0.8, 0.5), T(x + math.cos(a) * 1.0, Y + 0.4, z + math.sin(a) * 1.0), M['steelRail'], 1)
    light(C_LIGHT, 'site_terrace', 'POINT', (27, Y + 2.6, 30), energy=160, color=(1.0, 0.78, 0.5), size=0.3)

    # 북서동 + 잔디 쪽 저층부(화분 줄)
    block(ye_nw, 46, 66, -35, 13, ROOF_Y, 3)
    block(ye_nw, 42, 46.4, -30, 2, 4.5, 1, parapet=0.9)
    for z in range(-28, 1, 4):
        ye_nw.add(cyl(0.55, 0.45, 0.6, 16), T(44, 5.1, z), M['granite_clad'], 1)
        ye_nw.add(sphere(0.6, 2), T(44, 5.6, z, sy=0.7), M['shrub'], 1)
    hanok(ye_nw, 55.5, 9.0, 11.8, 6.4, ry=PI, y0=Y, label='B1', lamp=0)              # 용마루 x
    hanok(ye_nw, 57.5, -12.0, 14.8, 6.2, ry=-PI / 2, y0=Y, label='B2', lamp=500)     # 용마루 z, 잔디 쪽 정면
    hanok(ye_nw, 53.0, -29.0, 8.0, 6.4, ry=PI, y0=Y, label='B3', lamp=0)             # 용마루 x
    ye_nw.add(box(5, 4.5, 14), T(62.5, ROOF_Y + 2.25, -27), M['granite_clad'], 1.5)  # 계단실
    # 잔디와 연수동 사이 광장 + 계단
    ye_nw.add(box(6.8, 0.45, 50), T(38.6, 0.22, -8), M['terrace'], 1.6)
    for k in range(3):
        ye_nw.add(box(0.4, 0.15 * (k + 1), 50), T(35.0 - k * 0.4 + 0.2, 0.075 * (k + 1), -8), M['terrace'], 1.6)
    for z in range(-30, 12, 10):
        light(C_LIGHT, f'site_wash_w{z}', 'SPOT', (39.5, 0.6, z), (42.5, 6, z), energy=900,
              color=(1.0, 0.8, 0.55), spot=0.6, blend=0.8, size=0.3)


# ── 무대 뒤: 물탱크 · 대기 천막 · 신평루 콘솔 부스 ────────────────────
backstage = Assembly('backstage', C_STATIC)
glass_roof = Assembly('context_glass', bpy.data.collections['DYNAMIC'])


def tank(x, z, ry=0.0):
    """레이허 무게용 물주머니 (검은 PVC, 위를 묶은 자루 모양 — 콘솔 사진)"""
    f = T(x, 0.12, z, ry)

    def bag(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            y = v.co.y
            k = 1.0 - 0.55 * max(0.0, y) ** 2          # 위로 갈수록 좁아짐
            v.co.x *= 0.5 * k
            v.co.z *= 0.42 * k
            v.co.y = (y + 1) * 0.36 if y < 0.6 else 0.576 + (y - 0.6) * 0.5
            if v.co.y < 0.08:
                v.co.y = 0.08 * (v.co.y / 0.08) ** 0.5   # 바닥은 평평
    backstage.add(bag, f, M['tank'], 0.8)
    backstage.add(cyl(0.05, 0.09, 0.2, 12), f @ T(0, 0.83, 0), M['tank'], 0.8)


def tent(x, z, ry=0.0):
    """5×5 팝업 천막: 네 기둥, 피라미드 지붕, 세 면 벽 (무대 쪽 +z 는 열림)"""
    f = T(x, 0.12, z, ry)
    for sx in (-2.45, 2.45):
        for sz in (-2.45, 2.45):
            backstage.add(box(0.06, 2.5, 0.06), f @ T(sx, 1.25, sz), M['alu'], 1)
    backstage.add(box(5.0, 0.25, 5.0), f @ T(0, 2.4, 0), M['tent'], 1)
    backstage.add(cyl(0.12, 3.54, 1.2, 4), f @ T(0, 3.12, 0, PI / 4), M['tent'], 1)
    for (px, pz, ry2) in ((0, -2.47, PI), (2.47, 0, PI / 2), (-2.47, 0, -PI / 2)):
        g = f @ T(px, 1.2, pz, ry2)
        backstage.add(plane(4.9, 2.3), g, M['tent'], 1.5)
        backstage.add(plane(4.9, 2.3), g @ T(0, 0, -0.02, PI), M['tent'], 1.5)
    backstage.add(box(1.8, 0.05, 0.75), f @ T(0, 0.74, -1.3), M['tent'], 1)          # 접이식 테이블
    for sx in (-0.7, 0.7):
        backstage.add(box(0.05, 0.72, 0.6), f @ T(sx, 0.36, -1.3), M['alu'], 1)
        backstage.add(box(0.45, 0.45, 0.45), f @ T(sx, 0.23, -0.4), M['case'], 1)       # 의자


def console_booth():
    """신평루 아래층: 초록 칸막이 + 조명·음향·영상 콘솔, 55인치 프로그램 모니터"""
    cx, cz = SP
    y0 = SP_BASE
    zf = cz + SP_D / 2 + 0.45          # 칸막이 선 (앞 기둥 바로 바깥)
    # 파이프 앤 드레이프: 흰 프레임 + 올리브 초록 천 (높이 1.8, 1m 칸) — 앞면과 오른쪽 옆면
    DH = 1.8
    runs = [((cx - 5.6, zf), (cx + 5.6, zf)), ((cx + 5.6, zf), (cx + 5.6, zf - 5.0))]
    for (ax, az), (bx, bz) in runs:
        L = math.hypot(bx - ax, bz - az)
        ang = -math.atan2(bz - az, bx - ax)
        n = max(1, round(L))
        for k in range(n):
            t = (k + 0.5) / n
            g = T(ax + (bx - ax) * t, y0 + DH / 2, az + (bz - az) * t, ang)
            backstage.add(plane(L / n - 0.05, DH - 0.06), g, M['drape'], 1.5)
            backstage.add(plane(L / n - 0.05, DH - 0.06), g @ T(0, 0, -0.02, PI), M['drape'], 1.5)
        for k in range(n + 1):
            t = k / n
            backstage.add(box(0.04, DH, 0.04), T(ax + (bx - ax) * t, y0 + DH / 2, az + (bz - az) * t, ang), M['tent'], 1)
        for yy in (0.02, DH):
            gg, m = tube(V((ax, y0 + yy, az)), V((bx, y0 + yy, bz)), 0.02, 6)
            backstage.add(gg, m, M['tent'])
    # 콘솔 테이블 (로드 케이스)
    zt = zf - 0.9
    rows = ((cx - 3.2, 1.7, 'light'), (cx - 0.6, 1.5, 'audio'), (cx + 2.6, 2.2, 'video'))
    for (x, w, kind) in rows:
        backstage.add(box(w, 0.82, 0.85), T(x, y0 + 0.41, zt), M['case'], 1)
        if kind == 'light':          # 조명 콘솔: 경사진 본체 + 화면 두 개 + 페이더 줄 + 실행 버튼
            backstage.add(box(1.4, 0.14, 0.7), T(x, y0 + 0.89, zt, 0, -0.1), M['case'], 1)
            backstage.add(box(1.36, 0.42, 0.06), T(x, y0 + 1.15, zt + 0.3, 0, -0.35), M['case'], 1)
            for sx in (-0.34, 0.34):
                glow.add(plane(0.62, 0.38), T(x + sx, y0 + 1.16, zt + 0.265, PI, -0.35), M['uiLight'], tile=None)
            for k in range(15):
                fx = x - 0.6 + k * 0.085
                backstage.add(box(0.03, 0.025, 0.06), T(fx, y0 + 0.975, zt - 0.2), M['alu'], 1)          # 페이더 캡
                glow.add(box(0.05, 0.008, 0.025), T(fx, y0 + 0.965, zt - 0.05), M['clipLamp'] if k % 3 else M['uiAudio'])
        elif kind == 'audio':        # 음향 콘솔: 채널 스트립 + 화면
            backstage.add(box(1.3, 0.1, 0.7), T(x, y0 + 0.87, zt, 0, -0.12), M['case'], 1)
            glow.add(plane(0.5, 0.32), T(x, y0 + 1.15, zt + 0.28, PI, -0.3), M['uiAudio'], tile=None)
            for k in range(16):
                fx = x - 0.56 + k * 0.075
                backstage.add(box(0.028, 0.022, 0.05), T(fx, y0 + 0.935, zt - 0.18), M['alu'], 1)
                for r in range(3):
                    backstage.add(cyl(0.012, 0.012, 0.02, 8), T(fx, y0 + 0.935, zt + 0.02 + r * 0.07), M['alu'], 1)
        else:                        # 영상 스위처 + 노트북 + 멀티뷰 모니터
            backstage.add(box(0.9, 0.08, 0.45), T(x - 0.4, y0 + 0.86, zt), M['case'], 1)
            glow.add(plane(0.62, 0.36), T(x + 0.5, y0 + 1.1, zt + 0.25, PI), M['uiVideo'], tile=None)
            glow.add(plane(0.34, 0.22), T(x - 0.4, y0 + 1.0, zt + 0.1, PI, -0.3), M['uiVideo'], tile=None)
    for (x, _, _) in rows:           # 운영 의자
        backstage.add(box(0.5, 0.48, 0.5), T(x, y0 + 0.24, zt - 1.0), M['case'], 1)
        backstage.add(box(0.5, 0.5, 0.06), T(x, y0 + 0.72, zt - 1.25), M['case'], 1)
    # 55인치 프로그램 모니터 (칸막이 밖, 운영석 쪽을 봄) + 스탠드
    tvx = cx - 2.0
    backstage.add(box(0.06, 2.2, 0.06), T(tvx, y0 + 1.1, zf + 0.45), M['alu'], 1)
    backstage.add(box(0.9, 0.04, 0.6), T(tvx, y0 + 0.02, zf + 0.45), M['alu'], 1)
    backstage.add(box(1.26, 0.74, 0.06), T(tvx, y0 + 2.45, zf + 0.42), M['case'], 1)
    glow.add(plane(1.22, 0.69), T(tvx, y0 + 2.45, zf + 0.38, PI), bpy.data.materials['led'], tile=None)
    # 보조 모니터
    backstage.add(box(0.05, 1.6, 0.05), T(cx + 3.6, y0 + 0.8, zf + 0.35), M['alu'], 1)
    backstage.add(box(0.62, 0.4, 0.05), T(cx + 3.6, y0 + 1.7, zf + 0.32), M['case'], 1)
    glow.add(plane(0.58, 0.36), T(cx + 3.6, y0 + 1.7, zf + 0.29, PI), M['uiVideo'], tile=None)
    # 칸막이 위 클립 조명
    for x in (cx - 4.6, cx - 1.2, cx + 1.8, cx + 4.8):
        glow.add(sphere(0.07, 2), T(x, y0 + 1.72, zf - 0.1), M['clipLamp'])
        light(C_LIGHT, f'site_clip_{x:.1f}', 'POINT', (x, y0 + 1.66, zf - 0.22), energy=70, color=(1.0, 0.9, 0.75), size=0.05)
    # 오른쪽 옆 줄: 영상·중계 테이블 (칸막이 안쪽을 따라)
    for k, zz in enumerate((zf - 1.2, zf - 2.6)):
        backstage.add(box(0.75, 0.74, 1.3), T(cx + 4.9, y0 + 0.37, zz), M['case'], 1)
        glow.add(plane(0.36, 0.24), T(cx + 4.75, y0 + 0.95, zz, -PI / 2, 0, 0), M['uiVideo'], tile=None)
    # 2층 마루 밑 작업등
    light(C_LIGHT, 'site_booth_work', 'AREA', (cx, y0 + 3.3, cz), (cx, y0, cz), energy=160, color=(1.0, 0.85, 0.65), size=6)
    # 바닥의 케이스
    for (x, z) in ((cx - 5.0, cz - 2.5), (cx - 4.2, cz - 2.6), (cx + 4.5, cz - 2.2)):
        backstage.add(bevel_box(0.8, 0.6, 0.6, 0.03), T(x, y0 + 0.3, z), M['case'], 1)


def backstage_block():
    # 대기용 천막: 무대 바로 뒤 (무대 뒤 계단과 신평루 사이)
    tent(3.2, -26.8)
    tent(8.8, -26.8)
    console_booth()


iljumun(-41.5, 26.0)
corridor()
sinpyeongru(*SP)
south_row()
halls.build()
garden_block()
garden.build(smooth=False)
yeonsu_block()
ye_ne.build()
ye_nw.build()
glass_roof.build()
backstage_block()
backstage.build()


# ── 소나무 (우산처럼 퍼지는 한국 소나무) ─────────────────────────────
pines = Assembly('pines', C_STATIC)


needles = Assembly('pine_needles', bpy.data.collections['DYNAMIC'])
leaves = Assembly('tree_leaves', bpy.data.collections['DYNAMIC'])


def needle_cluster(cx, cy, cz, sx, sy, rnd):
    """솔잎 뭉치: 솔잎 알파 카드를 여러 장 교차 (위·옆 어디서 봐도 풍성하게)"""
    count = int(10 + sx * 8)
    for _ in range(count):
        ox, oy, oz = rnd.uniform(-sx, sx) * 0.6, rnd.uniform(-sy, sy) * 0.5, rnd.uniform(-sx, sx) * 0.6
        size = rnd.uniform(0.9, 1.4) * max(sx, 0.6)
        m = T(cx + ox, cy + oy, cz + oz, rnd.uniform(0, 2 * PI), -PI / 2 + rnd.uniform(-0.7, 0.7), rnd.uniform(-0.4, 0.4))
        needles.add(plane(size, size), m, M['needles'], tile=None)


def needle_pad(sx, sy, seed):
    """솔잎 뭉치: 납작한 구에 프랙탈 노이즈로 잔 뭉치 요철을 주고, 아래는 평평하게"""
    from mathutils import noise

    def build(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        off = V((seed, seed * 0.37, seed * 0.71))
        for v in bm.verts:
            d = v.co.normalized()
            n = noise.fractal(d * 2.6 + off, 0.6, 2.2, 4)
            spike = noise.noise(d * 9.0 + off) * 0.12
            r = 1 + 0.38 * n + spike
            v.co = V((d.x * sx * r, d.y * sy * r, d.z * sx * r))
            if v.co.y < 0:
                v.co.y *= 0.35
    return build


def pine(px, pz, s=1.0, seed=0):
    rnd = random.Random(seed or int(px * 13 + pz * 7))
    # 줄기: 한쪽으로 휘며 올라간다
    lean = V((rnd.uniform(-0.45, 0.45), 1, rnd.uniform(-0.45, 0.45))).normalized()
    pts = [V((px, 0.1, pz))]
    drift = V((0, 0, 0))
    for k in range(10):
        drift = drift * 0.7 + V((rnd.uniform(-0.12, 0.12), 0, rnd.uniform(-0.12, 0.12)))
        pts.append(pts[-1] + (lean * 0.53 + drift) * s)
    for k in range(len(pts) - 1):
        r = (0.24 - k * 0.016) * s
        g, m = tube(pts[k], pts[k + 1] + (pts[k + 1] - pts[k]) * 0.04, r, 12, caps=True)
        pines.add(g, m, M['pineBark'] if k < 4 else M['pineBarkRed'], 0.8)
    pts = pts[::2]
    top = pts[-1]
    # 가지: 줄기 위쪽에서 사방으로 뻗고, 끝마다 납작한 잎 뭉치(층층이)
    branches = 7
    for b in range(branches):
        a = b / branches * 2 * PI + rnd.uniform(-0.3, 0.3)
        base = pts[2 + b % 3]
        reach = rnd.uniform(1.8, 3.2) * s
        tip = base + V((math.cos(a) * reach, rnd.uniform(0.3, 1.2) * s, math.sin(a) * reach))
        mid = (base + tip) / 2 + V((0, rnd.uniform(0.1, 0.4) * s, 0))
        for a_, b_, r_ in ((base, mid, 0.08), (mid, tip, 0.055)):
            g, m = tube(a_, b_, r_ * s, 8, caps=True)
            pines.add(g, m, M['pineBarkRed'], 0.8)
        for c in range(5):
            cc = tip + V((rnd.uniform(-0.9, 0.9) * s, rnd.uniform(-0.15, 0.35) * s, rnd.uniform(-0.9, 0.9) * s))
            sx, sy = rnd.uniform(0.7, 1.15) * s, rnd.uniform(0.3, 0.45) * s
            needle_cluster(cc.x, cc.y, cc.z, sx, sy, rnd)
    # 꼭대기 뭉치
    for c in range(4):
        cc = top + V((rnd.uniform(-0.8, 0.8) * s, rnd.uniform(0.0, 0.5) * s, rnd.uniform(-0.8, 0.8) * s))
        needle_cluster(cc.x, cc.y, cc.z, 1.2 * s, 0.45 * s, rnd)


def tree(px, pz, s=1.0):
    """활엽수 (느티·벚나무류): 줄기에서 갈라진 가지 끝마다 잎 카드 뭉치, 전체는 둥근 수관"""
    rnd = random.Random(int(px * 31 + pz * 17))
    top = V((px + rnd.uniform(-0.3, 0.3), 3.0 * s, pz + rnd.uniform(-0.3, 0.3)))
    g, m = tube(V((px, 0, pz)), top, 0.22 * s, 10, caps=True)
    pines.add(g, m, M['treeBark'], 0.8)
    crown_r, crown_h = rnd.uniform(3.0, 4.2) * s, rnd.uniform(3.2, 4.4) * s
    center = top + V((0, crown_h * 0.55, 0))
    for b in range(5):
        a = b / 5 * 2 * PI + rnd.uniform(-0.3, 0.3)
        tip = center + V((math.cos(a) * crown_r * 0.55, rnd.uniform(-0.4, 0.8) * s, math.sin(a) * crown_r * 0.55))
        g, m = tube(top, tip, 0.1 * s, 8, caps=True)
        pines.add(g, m, M['treeBark'], 0.8)
    for _ in range(int(26 * s)):
        # 수관 겉면 가까이에 뭉치 (속은 비워 카드 수를 아낌)
        u, v = rnd.uniform(0, 2 * PI), rnd.uniform(-0.55, 1.0)
        rr = rnd.uniform(0.7, 1.0)
        c = center + V((math.cos(u) * math.sqrt(1 - v * v) * crown_r * rr, v * crown_h * 0.5,
                        math.sin(u) * math.sqrt(1 - v * v) * crown_r * rr))
        size = rnd.uniform(1.8, 2.6) * s
        for _k in range(3):
            leaves.add(plane(size, size), T(c.x, c.y, c.z, rnd.uniform(0, 2 * PI), rnd.uniform(-1.2, 1.2), rnd.uniform(-0.6, 0.6)),
                       M['leaves'], tile=None)


# 잔디 위 소나무 (위성사진 · 테라스 사진의 큰 소나무)
pine(22, 8, 1.35, seed=3)
pine(14.5, 14.5, 0.8, seed=5)
# 위성사진에서 검출한 수관 위치 (scripts/blender/site_trees.json): 수공간·회랑 주변은 소나무, 나머지는 활엽수
import json  # noqa: E402
with open('/Users/hare/Documents/큐비크스홈페이지/scripts/blender/site_trees.json') as fp:
    SITE_TREES = json.load(fp)
for k, (x, z, dens) in enumerate(SITE_TREES):
    rs = random.Random(k)
    size = 0.85 + 0.35 * dens + rs.uniform(-0.1, 0.15)
    in_garden = -32 <= x <= 24 and 24 <= z <= 52
    if in_garden or rs.random() < 0.18:
        pine(x, z, size * 0.95, seed=k + 100)
    else:
        tree(x, z, size)
pines.build(smooth=True)
needles.build()
leaves.build()
glow.build()

# 귀빈동(연수동 북동동 옥상) 테라스 — 실제 만찬 사진을 찍은 자리
camera(C_CAM, 'cam_terrace', (24.4, 15.7, 21.2), (-10, 0.5, -16), 64)
# 신평루 콘솔 부스 — 콘솔 뒤에서 무대 쪽 (소개서 18p 사진)
camera(C_CAM, 'cam_console', (SP[0] + 4.2, SP_BASE + 2.9, SP[1] - 0.8), (SP[0] - 6, 0.4, -24), 66)
print('context built')
