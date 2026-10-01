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
from lib import (PI, SHOTS, Assembly, T, bevel_box, box, camera, cyl, light, material, plane, ring_segment, sphere, tube)  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402

import gear  # noqa: E402
import props  # noqa: E402
importlib.reload(gear)
importlib.reload(props)
from lib import mesh_source  # noqa: E402
from mathutils import Vector as V  # noqa: E402

random.seed(11)
C_STATIC = bpy.data.collections['STATIC']
C_EMIT = bpy.data.collections['EMISSIVE']
C_LIGHT = bpy.data.collections['LIGHTS']
C_CAM = bpy.data.collections['CAMERAS']
# 이 목록에서 빠진 어셈블리는 실행할 때마다 .001 .002 로 중복 생성돼 쌓인다
# (site_stones / foh_corridor 가 그랬다 — 파일 용량도 같이 불었다).
for name in ('pagoda', 'halls', 'garden', 'yeonsu', 'yeonsu_ne', 'yeonsu_nw', 'pines', 'pine_needles',
             'tree_leaves', 'backstage', 'context_emissive', 'context_glass',
             'foh_corridor', 'foh_emissive', 'site_stones', 'site_stones_emissive'):
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
    'vermilion': mat('vermilion', 'dark_wooden_planks', (0.115, 0.048, 0.028), 0.72),  # 어두운 갈색 기둥·창방
    'bracket': mat('bracket', 'dark_wooden_planks', (0.095, 0.042, 0.026), 0.75),     # 공포
    'wallWood': mat('wallWood', 'dark_wooden_planks', (0.058, 0.030, 0.021), 0.78),
    'goldRail': mat('goldRail', image_base=f'{SHOTS}/apec_rail.png', rough=0.4),
    'deck': mat('deckWood', 'dark_wooden_planks', (0.085, 0.048, 0.030), 0.75),
    'gold': mat('finialGold', None, (0.85, 0.62, 0.25), 0.3, 1.0),
    'windowGlow': mat('windowGlow', emit_image=f'{SHOTS}/apec_windows.png', emit_strength=2.2, rough=0.5),
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
    'consoleBody': mat('consoleBody', None, (0.035, 0.037, 0.042), 0.45, 0.2),
    'keyGrey': mat('keyGrey', None, (0.12, 0.12, 0.13), 0.5),
    'keyAmber': mat('keyAmber', None, (1, 0.6, 0.2), emit=(1.0, 0.55, 0.15), emit_strength=6),
    'keyWhite': mat('keyWhite', None, (1, 1, 1), emit=(0.9, 0.92, 1.0), emit_strength=5),
    'keyRed': mat('keyRed', None, (1, 0.2, 0.15), emit=(1.0, 0.15, 0.1), emit_strength=6),
    'keyGreen': mat('keyGreen', None, (0.2, 1, 0.3), emit=(0.15, 1.0, 0.3), emit_strength=6),
    'black': mat('black', None, (0.012, 0.012, 0.015), 0.5),
    'stainless': mat('stainless', None, (0.8, 0.81, 0.82), 0.22, 1.0),
    'glass': mat('glass', None, (0.9, 0.93, 0.95), 0.03, transmission=1.0),
    'flame': mat('flame', None, (1, 0.45, 0.1), emit=(1.0, 0.42, 0.1), emit_strength=35),
}
C_SRC = bpy.data.collections['SOURCES']
SRC_MIXER = props.load('d3995c11393d439da2fe205db7caeb44', 'src_mixer', width=0.95, decimate=0.25, coll=C_SRC)
SRC_LAPTOP = props.load('7d870e900889481395b4a575b9fa8c3e', 'src_laptop', width=0.33, coll=C_SRC)
SRC_PARASOL = props.load('d6c9705a4f8e421ea473196ab9910088', 'src_parasol', height=2.6, coll=C_SRC, materials=M['parasol'])   # 원래 천 무늬 대신 흰 캔버스
SRC_TABLESET = props.load('outdoor_table_chair_set_01', 'src_tableset', width=1.9, coll=C_SRC)

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


def seat(beam_top, hd, ridge, rh, overhang, thickness=0.22, curve=1.8):
    """지붕 밑면이 벽선(처마 끝에서 overhang 안쪽)의 보 윗면에 얹히도록 하는 지붕 바닥 높이.
    hip_roof 곡면(= 밑면): 처마(t=1)→용마루(t=0) 높이 rh·(1-t)^curve, 두께는 곡면 위로 (광선으로 확인)"""
    run = hd * ridge
    y = rh * min(1.0, overhang / run) ** curve
    return beam_top - y - 0.04   # 4cm 겹치게 (틈 없음)


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
    for si, (a, b) in enumerate(zip(points[:-1], points[1:])):
        a, b = V(a), V(b)
        d = b - a
        n = max(1, round(d.length / post))
        for k in range(0 if si == 0 else 1, n + 1):   # 이음부 기둥은 한 번만
            p = a + d * (k / n)
            asm.add(bevel_box(0.26, h + 0.25, 0.26, 0.03), T(p.x, p.y + (h + 0.25) / 2, p.z), M['balustrade'], 1)
        for ry in (h * 0.92, h * 0.5):
            g, m = tube(a + V((0, ry, 0)), b + V((0, ry, 0)), 0.07, 8)
            asm.add(g, m, M['balustrade'])
        g, m = tube(a + V((0, 0.12, 0)), b + V((0, 0.12, 0)), 0.08, 6)   # 하방 (동자기둥 면과 6cm 이상)
        asm.add(g, m, M['balustrade'])


# ── 중도타워 ──────────────────────────────────────────────────
PX, PZ = -43, -11
BASE_Y = 1.6
pagoda = Assembly('pagoda', C_STATIC)

# 흰 원형 동선 (위성사진의 흰 고리, 반지름 27.5) + 기단 주변 포장
pagoda.add(cyl(27.5, 27.5, 0.2, 96), T(PX, 0.1, PZ), M['granite'], 1.5)   # 윗면 0.2 (잔디 0.12, 계단 첫 단 0.27)
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
for sz in (-1, 1):  # 계단 옆 소맷돌 + 그 위 돌난간 (사진에서 제일 눈에 띄는 디테일)
    pagoda.add(bevel_box(2.8, BASE_Y + 0.55, 0.42, 0.05), T(PX + PH + 1.2, (BASE_Y + 0.55) / 2, PZ + sz * (SW + 0.25)), M['balustrade'], 1)
    balustrade(pagoda, [(PX + PH + 2.6, BASE_Y * 0.18, PZ + sz * (SW + 0.25)),
                        (PX + PH - 0.1, BASE_Y + 0.55, PZ + sz * (SW + 0.25))], h=0.78, post=0.9)
    pagoda.add(bevel_box(0.62, 0.7, 0.62, 0.05), T(PX + PH + 2.75, 0.35, PZ + sz * (SW + 0.25)), M['balustrade'], 1)   # 계단 끝 법수


def stone_lamp(x, z, s_=1.0):
    """석재 등불 (장명등) — 기단 가장자리에 줄지어 선다"""
    f = T(x, 0, z) @ T(0, 0, 0, 0, 0, 0, s_, s_, s_)
    OCT = PI / 8
    pagoda.add(cyl(0.40, 0.40, 0.14, 8), f @ T(0, 0.07, 0, OCT), M['granite'], 1.2)
    pagoda.add(cyl(0.22, 0.30, 0.22, 8), f @ T(0, 0.25, 0, OCT), M['granite'], 1.2)
    pagoda.add(cyl(0.11, 0.13, 0.78, 8), f @ T(0, 0.75, 0, OCT), M['granite'], 1.2)      # 간주석
    pagoda.add(cyl(0.30, 0.20, 0.16, 8), f @ T(0, 1.22, 0, OCT), M['granite'], 1.2)
    for i in range(8):                                                                   # 화사석 (기둥 여덟)
        a = OCT + i * PI / 4
        pagoda.add(box(0.06, 0.40, 0.06), f @ T(0.25 * math.sin(a), 1.50, 0.25 * math.cos(a), a), M['granite'], 1.2)
    for i in range(4):
        a = OCT + i * PI / 2
        pagoda.add(box(0.20, 0.40, 0.05), f @ T(0.24 * math.sin(a), 1.50, 0.24 * math.cos(a), a), M['granite'], 1.2)
    glow.add(cyl(0.18, 0.18, 0.34, 8), f @ T(0, 1.50, 0, OCT), M['lanternGlow'] if 'lanternGlow' in M else M['hanji'], 1)
    pagoda.add(cyl(0.52, 0.50, 0.07, 8), f @ T(0, 1.74, 0, OCT), M['granite'], 1.2)      # 옥개석 처마
    pagoda.add(cyl(0.16, 0.50, 0.20, 8), f @ T(0, 1.87, 0, OCT), M['granite'], 1.2)
    pagoda.add(sphere(0.09, 3), f @ T(0, 2.02, 0), M['granite'])
    light(C_LIGHT, f'pagoda_lamp_s{round(x)}_{round(z)}', 'POINT', (x, 1.5 * s_, z),
          energy=60, color=(1.0, 0.80, 0.52), size=0.16)


for lz in (-14.5, -8.0, 8.0, 14.5):                     # 기단 잔디 쪽 가장자리를 따라
    stone_lamp(PX + PH + 2.2, PZ + lz)

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
    pagoda.add(box(core * 2, H + 0.1, core * 2), T(PX, y + (H + 0.1) / 2, PZ), M['wallWood'], 1.5)   # 다음 층 마루 속까지
    window_band(PX, y + 0.35 + wall_h * 0.46, PZ, core + 0.08, wall_h * 0.78)
    # 기둥 (주칠)
    bays = 7 if i < 5 else 5
    placed = set()
    for k in range(bays + 1):
        t = -half + k * w / bays
        for (x, z) in ((t, half), (t, -half), (half, t), (-half, t)):
            if (round(x, 3), round(z, 3)) in placed:   # 모서리 기둥은 한 번만
                continue
            placed.add((round(x, 3), round(z, 3)))
            pagoda.add(cyl(0.3, 0.32, wall_h, 12), T(PX + x, y + wall_h / 2, PZ + z), M['vermilion'], 1)
    # 창방·평방
    pagoda.add(box(w + 0.5, 0.55, w + 0.5), T(PX, y + wall_h + 0.28, PZ), M['vermilion'], 1)
    pagoda.add(box(w + 0.9, 0.3, w + 0.9), T(PX, y + wall_h + 0.7, PZ), M['bracket'], 1)
    # 공포 (하앙): 칸마다 밖으로 내민 쇠서
    for k in range(bays + 1):
        t = -half + k * w / bays
        for (x, z, ry) in ((t, half, 0), (t, -half, PI), (half, t, PI / 2), (-half, t, -PI / 2)):
            if abs(abs(x) - half) < 1e-3 and abs(abs(z) - half) < 1e-3 and ry in (PI / 2, -PI / 2):
                continue   # 모서리는 앞뒤 방향 공포 하나만 (두 방향이 겹치면 윗면이 같은 높이)
            pagoda.add(box(0.36, 0.34, 2.0), T(PX + x, y + wall_h + 1.0, PZ + z, ry) @ T(0, 0, 0.7), M['bracket'], 1)   # 평방(윗면 +0.85) 위에
            pagoda.add(box(0.22, 0.26, 1.4), T(PX + x, y + wall_h + 1.4, PZ + z, ry) @ T(0, 0, 1.2, 0, -0.35), M['bracket'], 1)   # 아래 쇠서(0.36)보다 좁게
    # 지붕
    if top:
        eave = seat(y + wall_h + 1.77, half + 3.6, 0.98, 5.2, overhang=3.6 - 1.86, thickness=0.3, curve=1.5)
    else:
        eave = seat(y + wall_h + 1.77, half + 3.4, 1 - (half - 1.0) / (half + 3.4), 2.2, overhang=3.4 - 1.86, thickness=0.28)
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
# 현장 사진: 타워를 비추는 업라이트는 없다. 불 켜진 창(발광 창호)과 처마 네 귀 점조명만으로 보이고,
# 지붕·몸체는 거의 검은 실루엣. 1층만 실내 조명으로 따뜻하게 밝다.
light(C_LIGHT, 'pagoda_1f', 'AREA', (PX + 17.2, BASE_Y + 4.5, PZ), (PX + 30, BASE_Y, PZ), energy=2500,
      color=(1.0, 0.74, 0.45), size=24)


# ── 한옥 부재 ─────────────────────────────────────────────────
halls = Assembly('halls', C_STATIC)


def ridge(asm, frame, length, y):
    asm.add(bevel_box(length, 0.45, 0.55, 0.06), frame @ T(0, y, 0), M['tileGrey'], 1)
    for sx in (-1, 1):  # 용마루 끝 치미
        asm.add(bevel_box(0.5, 0.9, 0.72, 0.08), frame @ T(sx * length / 2, y + 0.25, 0), M['tileGrey'], 1)


def hip_under(base, hd, ridge, rh, thickness=0.22, curve=1.8):
    """hip_roof 밑면 높이 (처마 끝에서 안쪽으로 r 위치, 모서리 들림 제외)"""
    return lambda r: base + rh * min(1.0, max(0.0, (hd - r) / (hd * ridge))) ** curve


def rafters(asm, frame, length, r0, r1, under, step=0.55, radius=0.07):
    """둥근 주칠 서까래: 벽선(보 위, r0)에서 처마 끝 가까이(r1)까지 지붕 밑면 바로 아래를 따라 (앞뒤 두 면)"""
    n = int(length / step)
    for k in range(n + 1):
        x = -length / 2 + k * length / n
        for s in (-1, 1):
            a = V((x, under(r0) - radius + 0.02, s * r0))
            b = V((x, under(r1) - radius + 0.02, s * r1))
            g, m = tube(frame @ a, frame @ b, radius, 8, caps=True)
            asm.add(g, m, M['rafter'], 1)


def hanok(asm, cx, cz, w, d, ry=0.0, y0=0.0, wall_h=3.4, veranda=True, base_h=0.6, label='', lamp=600, eave=2.6,
          open_front=False, open_end=0):
    """한옥 한 채. 로컬 x = 용마루 방향(길이 w), 로컬 +z = 정면(툇마루·계자 난간)
    주칠 기둥 · 흰 회벽 · 불 켜진 띠살문(앞뒤) · 팔작지붕(우진각 + 용마루)

    open_front : 로컬 +z 면(용마루와 나란한 긴 면)을 열어 대청마루로 만든다.
    open_end   : -1 / +1 — 로컬 ∓x **박공(측면) 끝칸**을 열어 대청마루로 만든다.
                 용마루가 잔디와 직각인 채(연수동 양옆 두 채)가 이 경우다. 실사
                 사진에서 그 채들도 잔디 쪽은 흰 회벽이 아니라 기둥만 선 열린
                 마루이고, 추녀 끝이 잔디를 향해 있다."""
    f = T(cx, 0, cz, ry)
    asm.add(bevel_box(w + 2.4, base_h, d + 2.4, 0.04), f @ T(0, y0 + base_h / 2, 0), M['granite'], 1.5)
    yb = y0 + base_h
    # open_front: 잔디 쪽 면이 막힌 벽이 아니라 **기둥만 선 열린 대청마루**다 (실사 사진).
    # 몸체를 뒤쪽으로 물려 앞을 비우고, 앞 칸에는 창호 대신 마룻바닥과 난간만 둔다.
    bd = d * 0.52 if open_front else d
    bw = w * 0.62 if open_end else w                 # 몸체 길이 (열린 끝칸을 뺀 나머지)
    bx = -open_end * (w - bw) / 2                    # 몸체를 열린 쪽 반대로 민다
    asm.add(box(bw, wall_h, bd), f @ T(bx, yb + wall_h / 2, -(d - bd) / 2), M['stoneWall'], 2)
    if open_front:
        asm.add(box(w, 0.22, d - bd), f @ T(0, yb + 0.11, bd / 2), M['deck'], 1.2)        # 대청 마룻바닥
    if open_end:
        asm.add(box(w - bw, 0.22, d), f @ T(open_end * bw / 2, yb + 0.11, 0), M['deck'], 1.2)   # 측면 대청마루
    bays = max(3, round(w / 3))
    bx0, bx1 = bx - bw / 2, bx + bw / 2
    for k in range(bays + 1):
        x = -w / 2 + k * w / bays
        for z in (-d / 2 - 0.05, d / 2 + 0.05):
            asm.add(cyl(0.2, 0.22, wall_h + 0.2, 12), f @ T(x, yb + (wall_h + 0.2) / 2, z), M['vermilion'], 1)
        if k < bays:
            xm = x + w / bays / 2
            if open_end and not bx0 < xm < bx1:
                continue                   # 열린 끝칸 — 창호 없이 기둥만 선다
            faces = ((-1, PI),) if open_front else ((1, 0), (-1, PI))
            for sz, rot in faces:
                zz = -(d - bd) / 2 + sz * (bd / 2 + 0.07) if open_front else sz * (d / 2 + 0.07)
                glow.add(plane(w / bays - 0.5, wall_h * 0.76), f @ T(xm, yb + wall_h * 0.44, zz, rot), M['hanji'], tile=None)
            if open_front:     # 열린 앞칸 안쪽에서 새어 나오는 빛
                glow.add(plane(w / bays - 0.5, wall_h * 0.70), f @ T(xm, yb + wall_h * 0.42, -(d - bd) / 2 + bd / 2 + 0.07), M['hanji'], tile=None)
    if open_end:
        xe = bx0 if open_end < 0 else bx1                              # 몸체의 열린 쪽 끝면
        for z in (-d / 6, d / 6):                                      # 열린 끝을 가로지르는 기둥 (사진에서 4개)
            asm.add(cyl(0.2, 0.22, wall_h + 0.2, 12),
                    f @ T(open_end * (w / 2), yb + (wall_h + 0.2) / 2, z), M['vermilion'], 1)
        glow.add(plane(d - 0.6, wall_h * 0.76),
                 f @ T(xe + open_end * 0.07, yb + wall_h * 0.44, 0, open_end * PI / 2), M['hanji'], tile=None)
    if veranda:
        asm.add(box(w + 1.2, 0.25, 1.8), f @ T(0, yb + 0.125, d / 2 + 1.3), M['deck'], 1.2)            # 툇마루 (기단 위)
        asm.add(box(w + 1.0, base_h, 0.9), f @ T(0, y0 + base_h / 2, d / 2 + 1.75), M['granite'], 1.5)   # 기단 밖 마루 받침 (기단과 5cm 띄움)
        g = f @ T(0, yb + 0.25 + 0.45, d / 2 + 2.15)
        asm.add(plane(w + 1.2, 0.9), g, M['fret'], tile=None)
        asm.add(plane(w + 1.2, 0.9), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
        for x in (-w / 2 - 0.6, w / 2 + 0.6):
            asm.add(cyl(0.16, 0.18, wall_h + 0.1, 10), f @ T(x, yb + 0.25 + (wall_h + 0.1) / 2, d / 2 + 2.15), M['vermilion'], 1)
    top = yb + wall_h
    asm.add(box(w + 0.6, 0.5, d + 0.6), f @ T(0, top + 0.1, 0), M['vermilion'], 1)
    rh = min(3.4, 1.4 + d * 0.3)
    ed = eave + 0.2
    base = seat(top + 0.35, d / 2 + ed, 0.8, rh, overhang=eave - 0.1)   # 창방(폭 d+0.6) 위에 얹힘
    rafters(asm, f, w + 0.4, d / 2 + 0.3, d / 2 + ed - 0.35, hip_under(base, d / 2 + ed, 0.8, rh))
    asm.add(hip_roof(w / 2 + eave, d / 2 + ed, rh, ridge=0.8, lift=1.1), f @ T(0, base, 0), M['tileGrey'], 1.4)
    ridge(asm, f, max(w - d * 0.8, 2), base + rh)
    if lamp:
        if open_end:   # 열린 쪽이 측면이면 등도 그쪽에 둔다
            p = f @ V((open_end * (w / 2 + 2.0), top - 0.2, 0))
            t = f @ V((open_end * (w / 2 + 6), y0, 0))
        else:
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
    # 아래 지붕(좌우 날개) + 위층 누 + 윗지붕
    lb = seat(8.2, D / 2 + 2.4, 0.75, 2.2, overhang=1.7)
    halls.add(hip_roof(W / 2 + 2.4, D / 2 + 2.4, 2.2, ridge=0.75, lift=0.9), f @ T(0, lb, 0), M['tileGrey'], 1.4)
    rafters(halls, f, W + 1.2, D / 2 + 0.7, D / 2 + 2.05, hip_under(lb, D / 2 + 2.4, 0.75, 2.2))
    halls.add(box(W / 3 + 0.8, 3.0, D - 0.6), f @ T(0, 10.0 + 1.5, 0), M['vermilion'], 1)
    for s in (-1, 1):
        g = f @ T(0, 10.0, s * (D - 0.6) / 2)                                  # 누 몸체 벽면
        halls.add(box(W / 3 + 0.6, 1.0, 0.03), g @ T(0, 0.5, s * 0.015, 0 if s > 0 else PI), M['goldRail'], tile=None)   # 벽에 붙은 난간판
        halls.add(box(3.6, 1.0, 0.12), g @ T(0, 2.0, s * 0.05), M['plaque'], 1)  # 皇龍院 현판 (벽에 붙음)
    ub = seat(13.0, D / 2 + 2.6, 0.8, 3.0, overhang=2.9)                  # 누 몸체(깊이 D-0.6) 위
    halls.add(hip_roof(W / 3 / 2 + 3.2, D / 2 + 2.6, 3.0, ridge=0.8, lift=1.1), f @ T(0, ub, 0), M['tileGrey'], 1.4)
    ridge(halls, f, W / 3 * 0.9, ub + 3.0)
    light(C_LIGHT, 'site_gate', 'AREA', tuple(f @ V((0, 9.5, D + 4))), tuple(f @ V((0, 4, 0))),
          energy=2400, color=(1.0, 0.78, 0.5), size=8)


# ── 회랑 (일주문 → 연수동, 잔디 북동쪽 z 17~23) ───────────────────
CZ_ = 20.0
CX0, CX1 = -38.0, 22.4   # 동쪽 끝은 연수동 벽(23) 앞에서 멈춤
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
    t_ = (CW / 2) / ((CW + 3.2) / 2)
    gb = 4.1 - (1.9 * (1 - t_) - 0.18 * math.sin(PI * t_)) - 0.04               # 밑면이 도리 위에 얹힘
    half_w = (CW + 3.2) / 2
    # 가운데 누각 (위성사진의 밝은 지붕 칸, x -10 ~ -1)
    px = -5.5 - mid
    # 누각 기둥(z ±2.7)이 회랑 지붕 폭(±3.7) 안에 있어서 지붕을 뚫고 올라와 있었다.
    # 실제 한옥 회랑은 누각 자리에서 지붕이 끊기고 누각 지붕이 그 위를 덮는다.
    slope = lambda r: gb + 1.9 * (1 - r / half_w) - 0.18 * math.sin(PI * r / half_w)
    GAP = 5.9
    for (a_, b_) in ((-L / 2 - 0.6, px - GAP), (px + GAP, L / 2 + 0.6)):
        if b_ - a_ < 1.0:
            continue
        sf = f @ T((a_ + b_) / 2, 0, 0)
        rafters(halls, sf, b_ - a_, CW / 2, half_w - 0.3, slope, step=0.6)
        halls.add(gable_roof(b_ - a_, CW + 3.2, 1.9, sag=0.18), sf @ T(0, gb, 0), M['tileGrey'], 1.4)
        ridge(halls, sf, b_ - a_ - 0.2, gb + 1.9)
    def gable_board(bm):                                      # 끊긴 자리를 막는 박공 마구리 (삼각 판)
        vs = [bm.verts.new(p) for p in ((-half_w, 0, -0.06), (half_w, 0, -0.06), (0, 1.9, -0.06),
                                        (-half_w, 0, 0.06), (half_w, 0, 0.06), (0, 1.9, 0.06))]
        bm.faces.new([vs[i] for i in (0, 1, 2)])
        bm.faces.new([vs[i] for i in (5, 4, 3)])
        for q in ((0, 3, 4, 1), (1, 4, 5, 2), (0, 2, 5, 3)):
            bm.faces.new([vs[i] for i in q])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    for s_ in (-1, 1):
        halls.add(gable_board, f @ T(px + s_ * GAP, gb, 0, PI / 2), M['rafter'], 1.2)
    for x in (px - 3.5, px + 3.5):
        for z in (-CW / 2 - 0.6, CW / 2 + 0.6):
            halls.add(cyl(0.3, 0.32, 5.4, 16), f @ T(x, 0.4 + 2.7, z), M['vermilion'], 1)
    halls.add(box(8.0, 0.5, CW + 1.8), f @ T(px, 5.9, 0), M['bracket'], 1)
    pb = seat(6.15, CW / 2 + 2.6, 0.7, 2.6, overhang=1.7)
    halls.add(hip_roof(5.6, CW / 2 + 2.6, 2.6, ridge=0.7, lift=1.0), f @ T(px, pb, 0), M['tileGrey'], 1.4)
    ridge(halls, f, 3.4, pb + 2.6)
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
            halls.add(cyl(0.32, 0.34, 7.85, 14), f @ T(x, SP_BASE + 3.925, z), M['vermilion'], 1)   # 기단 위 → 창방 밑(8.825)
    halls.add(box(W + 1.8, 0.3, D + 1.8), f @ T(0, 3.9 + SP_BASE, 0), M['deck'], 1.2)            # 누마루
    halls.add(box(W + 1.8, 0.4, D + 1.8), f @ T(0, 3.55 + SP_BASE, 0), M['rafter'], 1)
    for (px, pz, ry, ln) in ((0, D / 2 + 0.85, 0, W + 1.7), (0, -D / 2 - 0.85, PI, W + 1.7),
                             (W / 2 + 0.85, 0, PI / 2, D + 1.7), (-W / 2 - 0.85, 0, -PI / 2, D + 1.7)):
        g = f @ T(px, 4.05 + SP_BASE + 0.45, pz, ry)
        halls.add(plane(ln, 0.9), g, M['fret'], tile=None)
        halls.add(plane(ln, 0.9), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
    halls.add(box(W + 0.6, 0.55, D + 0.6), f @ T(0, 8.1 + SP_BASE, 0), M['vermilion'], 1)
    halls.add(box(W + 1.2, 0.6, D + 1.2), f @ T(0, 8.65 + SP_BASE, 0), M['bracket'], 1)
    sb = seat(8.95 + SP_BASE, D / 2 + 2.4, 0.8, 3.6, overhang=1.8)          # 평방(깊이 D+1.2) 위
    rafters(halls, f, W + 1.0, D / 2 + 0.6, D / 2 + 2.05, hip_under(sb, D / 2 + 2.4, 0.8, 3.6))
    halls.add(hip_roof(W / 2 + 2.6, D / 2 + 2.4, 3.6, ridge=0.8, lift=1.2), f @ T(0, sb, 0), M['tileGrey'], 1.4)
    ridge(halls, f, W * 0.55, sb + 3.6)
    for x in (-W / 3, W / 3):
        light(C_LIGHT, f'site_sinpyeong_{x:.0f}', 'POINT', tuple(f @ V((x, 7.4 + SP_BASE, 0))), energy=70, color=(1.0, 0.72, 0.42), size=0.4)


def south_row():
    """무대 뒤 남쪽 줄: 흰 돌길 + 낮은 돌난간, 원형 광장, 한옥 별채"""
    halls.add(box(48, 0.14, 1.8), T(1, 0.07, -34.0), M['path'], 1.2)
    for (x0, x1) in ((-24, 4.5), (17.5, 25)):
        balustrade(halls, [(x0, 0.14, -34.9), (x1, 0.14, -34.9)], h=0.6, post=2.4)
    # 원형 광장 (방사형 포장)
    cx, cz, r = -17.0, -42.0, 5.5
    halls.add(cyl(r, r, 0.3, 64), T(cx, 0.15, cz), M['path'], 1.2)   # 윗면 0.3 (남쪽 돌길 0.14 보다 높게)
    for k in range(24):
        a = k / 24 * 2 * PI
        halls.add(box(0.5, 0.05, 1.1), T(cx + math.cos(a) * (r - 0.8), 0.32, cz + math.sin(a) * (r - 0.8), PI / 2 - a), M['granite'], 1)   # 광장에 박힘
    # 광장 가운데 원형 좌대는 석불관이 앉는 자리라 여기서는 그리지 않는다
    # 한옥 별채 (용마루 x 방향)
    # 여기 한옥 별채는 내가 임의로 넣은 것이다. 실제로는 비어 있다 (클라이언트 사진) -> 뺀다


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


def strip(pts, width, h):
    """점들을 잇는 폭 width, 두께 h 의 띠 (바닥 y=0) — 조각 상자를 이어 붙이면 이음부가 겹친다"""
    def build(bm):
        P = [V((x, 0, z)) for x, z in pts]
        rows = []
        for i, p in enumerate(P):
            d = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
            side = V((-d.z, 0, d.x)) * (width / 2)
            rows.append([bm.verts.new(p + side + V((0, y, 0))) for y in (0, h)] +
                        [bm.verts.new(p - side + V((0, y, 0))) for y in (0, h)])
        for a, b in zip(rows[:-1], rows[1:]):
            for q in ((a[1], b[1], b[3], a[3]), (a[0], a[2], b[2], b[0]), (a[0], b[0], b[1], a[1]), (a[2], a[3], b[3], b[2])):
                bm.faces.new(q)
        bm.faces.new((rows[0][0], rows[0][1], rows[0][3], rows[0][2]))
        bm.faces.new((rows[-1][0], rows[-1][2], rows[-1][3], rows[-1][1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return build


def garden_block():
    pond_c, pond_r = V((6, 0, 33)), (14.5, 8.5)
    garden.add(cyl(1, 1, 0.1, 48), T(pond_c.x, 0.05, pond_c.z, sx=pond_r[0], sz=pond_r[1]), M['water'], None)
    garden.add(cyl(1, 1, 0.1, 48), T(pond_c.x, -0.02, pond_c.z, sx=pond_r[0] + 1.0, sz=pond_r[1] + 1.0), M['granite'], 1.5)   # 윗면 0.03 (수면 0.1)
    for k in range(40):
        a = k / 40 * 2 * PI
        rock(pond_c.x + math.cos(a) * (pond_r[0] + 0.5), pond_c.z + math.sin(a) * (pond_r[1] + 0.5), random.uniform(0.5, 1.1))
    for _ in range(22):
        a = random.uniform(0, 2 * PI)
        dd = random.uniform(1.12, 1.35)
        x, z = pond_c.x + math.cos(a) * pond_r[0] * dd, pond_c.z + math.sin(a) * pond_r[1] * dd
        if 23.5 < z and x < 22:
            shrub(x, z, random.uniform(0.7, 1.4))
    # 사모정 (연못 가). 위성사진: 지붕이 육각이 아니라 **사각 모임지붕**이고,
    # 물 위 기둥이 아니라 못 가장자리 땅 위에 앉아 있다.
    hx, hz = 14.0, 41.0
    PW = 3.6                                                   # 한 변의 절반
    garden.add(bevel_box(PW * 2 + 0.8, 0.55, PW * 2 + 0.8, 0.05), T(hx, 0.275, hz), M['granite'], 1.5)   # 기단
    garden.add(box(PW * 2 - 0.4, 0.22, PW * 2 - 0.4), T(hx, 0.66, hz), M['deck'], 1.2)                   # 마루
    for (sx_, sz_) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        garden.add(cyl(0.2, 0.22, 2.9, 12), T(hx + sx_ * (PW - 0.35), 0.77 + 1.45, hz + sz_ * (PW - 0.35)), M['vermilion'], 1)
    for (dx_, dz_, ry_) in ((0, PW - 0.35, 0.0), (0, -(PW - 0.35), PI), (PW - 0.35, 0, PI / 2), (-(PW - 0.35), 0, -PI / 2)):
        g = T(hx + dx_, 1.32, hz + dz_, ry_)
        garden.add(plane(PW * 2 - 0.9, 0.85), g, M['fret'], tile=None)
        garden.add(plane(PW * 2 - 0.9, 0.85), g @ T(0, 0, -0.03, PI), M['fret'], tile=None)
    garden.add(box(PW * 2 + 0.3, 0.45, PW * 2 + 0.3), T(hx, 3.89, hz), M['bracket'], 1)                  # 창방·평방
    pb = seat(4.12, PW + 1.6, 0.98, 2.5, overhang=1.5)
    garden.add(hip_roof(PW + 1.6, PW + 1.6, 2.5, ridge=0.98, lift=0.9), T(hx, pb, hz), M['tileGrey'], 1.4)   # 사모지붕
    garden.add(cyl(0.12, 0.34, 0.9, 8), T(hx, pb + 2.5 + 0.35, hz), M['tileGrey'], 1)                    # 절병통
    light(C_LIGHT, 'site_pavilion', 'POINT', (hx, 3.4, hz), energy=380, color=(1.0, 0.75, 0.45), size=0.4)
    # 돌다리는 내가 임의로 넣은 것이다 — 위성사진에 연못을 건너는 다리는 없다. 뺀다.
    # 곡선 산책로 (위성사진의 흰 길)
    pts = [(-31, 26), (-28, 33), (-20, 38), (-10, 40), (-3.5, 43), (4, 46), (14, 48.5), (24, 50)]
    garden.add(strip(pts, 1.6, 0.1), T(), M['path'], 1.2)   # 이음부가 겹치지 않는 한 장의 띠
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
M['winFrame'] = mat('winFrame', None, (0.030, 0.031, 0.034), 0.35, 0.75)      # 짙은 아노다이즈 알루미늄 창틀
M['winGlass'] = mat('winGlass', None, (0.021, 0.026, 0.033), 0.08, 0.15)      # 짙은 복층유리
ROOMS = [mat(f'roomGlass_{t}', emit_image=f'{SHOTS}/apec_room_{t}.png', emit_strength=1.1, rough=0.1) for t in 'abc']


def wall(asm, sx, sz, L, ry, h, floors, parapet=1.3, arcade=False, ribbon=False, recess=0.0, win=None):
    """한 면: 로컬 x = 벽 방향(0~L), 로컬 +z = 바깥. 바깥면이 z=0

    ribbon : 맨 윗층을 돌기둥 없이 **한 줄로 쭉 이어지는 통창**으로 (귀빈동 2층).
    recess : 그 통창을 벽면에서 안으로 물린 깊이 — 그 앞이 발코니가 된다.
    win    : {층: (아래, 위)} — 그 층 창의 실제 높이. 나머지는 돌벽으로 메운다."""
    f = T(sx, 0, sz, ry)
    fh = h / floors
    n = max(1, round((L - 1.8) / 7.6))
    w = (L - 1.8) / n
    xs = [0.9 + k * w for k in range(n + 1)]
    # 층 띠 (바닥 띠 + 층 사이 띠 + 난간벽)
    bands = [(0.0, 0.8)] + [(k * fh - 0.45, k * fh + 0.85) for k in range(1, floors)] + [(h - 0.45, h + parapet)]
    for y0, y1 in bands:
        asm.add(box(L - 1.8, y1 - y0, DEPTH), f @ T(L / 2, (y0 + y1) / 2, -DEPTH / 2), M['granite_clad'], 1.2)
    # 1층은 창이 아니라 둥근 아치 열이다 (클라이언트 사진: 연수동 잔디 쪽 1층이 아케이드).
    # 아치 베이는 창 베이(7.6m)와 다르다 — 그 폭을 그대로 쓰면 반지름 3.2m 아치가
    # 저층부(4.6m)보다 높아져 도형이 벽 밖으로 나가 버린다. 3.6m 피치로 따로 나눈다.
    if arcade:
        hb = bands[1][0]                                                 # 저층부 벽 상단
        na = max(1, round((L - 1.6) / 3.6))
        wa = (L - 1.6) / na
        ow = min(wa - 0.95, 2.9)                                         # 아치 개구 폭
        r = ow / 2
        spr = min(2.30, hb - r - 0.55)                                   # 아치 꼭대기가 벽 위로 안 나가게
        top = spr + r
        for k in range(na):
            cx_ = 0.8 + (k + 0.5) * wa
            glow.add(plane(ow, spr - 0.18), f @ T(cx_, (spr + 0.18) / 2, -0.40), random.choice(ROOMS), tile=None)
            glow.add(ring_segment(0, r, 0, PI, 0.04), f @ T(cx_, spr, -0.40, 0, -PI / 2), random.choice(ROOMS), tile=None)
            asm.add(ring_segment(r, r + 0.45, 0, PI, DEPTH), f @ T(cx_, spr, -DEPTH, 0, -PI / 2), M['granite_clad'], 1.2)
            asm.add(box(wa - 0.02, hb - top - 0.45, DEPTH),               # 아치 위 벽
                    f @ T(cx_, (top + 0.45 + hb) / 2, -DEPTH / 2), M['granite_clad'], 1.2)
            for sx_ in (-1, 1):                                          # 아치 옆 스팬드럴 (반원 밖 모서리)
                asm.add(box((wa - ow) / 2 - 0.01, top - spr + 0.45, DEPTH),
                        f @ T(cx_ + sx_ * (ow + wa) / 4, (spr + top + 0.45) / 2, -DEPTH / 2), M['granite_clad'], 1.2)
                asm.add(box((wa - ow) / 2 - 0.01, spr, DEPTH),            # 아치 사이 피어
                        f @ T(cx_ + sx_ * (ow + wa) / 4, spr / 2, -DEPTH / 2), M['granite_clad'], 1.2)
            asm.add(box(ow + 0.55, 0.12, DEPTH + 0.16), f @ T(cx_, spr, -DEPTH / 2 - 0.08), M['granite_clad'], 1.2)   # 기공선 돌띠
            asm.add(box(ow, 0.22, 0.55), f @ T(cx_, 0.11, -0.28), M['granite'], 1.5)                                 # 아치 아래 디딤돌
        for sx_ in (0.8, 0.8 + na * wa):                                 # 양 끝 마구리 벽
            asm.add(box(0.8, hb, DEPTH), f @ T(sx_ - 0.4 if sx_ > L / 2 else sx_ - 0.4, hb / 2, -DEPTH / 2), M['granite_clad'], 1.2)
    # 창: 기둥·띠 사이 구멍마다 안쪽 유리(방 불빛) + 창살
    for fl in range(1 if arcade else 0, floors):
        ya = 0.8 if fl == 0 else fl * fh + 0.85
        yb = (fl + 1) * fh - 0.45 if fl < floors - 1 else h - 0.45
        if win and fl in win:        # 창을 실측 높이로 줄이고 남는 데는 돌벽
            wa_, wb_ = win[fl]
            for (fa, fb) in ((ya, wa_), (wb_, yb)):
                if fb - fa > 0.02:
                    asm.add(box(L - 1.8, fb - fa, DEPTH), f @ T(L / 2, (fa + fb) / 2, -DEPTH / 2), M['granite_clad'], 1.2)
            ya, yb = wa_, wb_
        if ribbon and fl == floors - 1:
            # 귀빈동 2층: 돌기둥이 중간에 하나도 없고 가는 멀리언만 선 통창이다
            # (실사 008-59-55 007 — 천장 다운라이트가 유리 뒤로 줄줄이 보인다).
            xa, xb = 0.9, L - 0.9
            ow, oh = xb - xa, yb - ya
            cx_, cy_, zz = (xa + xb) / 2, (ya + yb) / 2, -recess
            glow.add(plane(ow, oh), f @ T(cx_, cy_, zz - 0.34), random.choice(ROOMS), tile=None)
            asm.add(box(ow, oh, 0.012), f @ T(cx_, cy_, zz - 0.20), M['winGlass'], 1)
            for by_ in (ya - 0.03, yb + 0.03):
                asm.add(box(ow + 0.12, 0.11, 0.11), f @ T(cx_, by_, zz - 0.15), M['winFrame'], 1)
            nm = max(2, round(ow / 2.3))
            for j in range(1, nm):
                asm.add(box(0.08, oh, 0.12), f @ T(xa + j * ow / nm, cy_, zz - 0.155), M['winFrame'], 1)
            if recess:
                # 패인 자리 양옆·윗면의 속벽. **벽면(z=0)까지 끌고 나오면 안 된다** —
                # 거기엔 이미 띠·모서리 기둥의 면이 있어서 그대로 z-fighting 이 난다.
                # 옆은 모서리 기둥 뒤(0.9)부터, 윗면은 벽 두께(DEPTH) 뒤부터 시작한다.
                d1 = recess + 0.30
                for sx_ in (xa - 0.45, xb + 0.45):
                    asm.add(box(0.9, oh + 0.9, d1 - 0.9), f @ T(sx_, cy_ + 0.45, -(0.9 + d1) / 2), M['granite_clad'], 1.2)
                asm.add(box(ow + 0.9, 0.45, d1 - DEPTH), f @ T(cx_, yb + 0.22, -(DEPTH + d1) / 2), M['granite_clad'], 1.2)
            else:   # 창대는 벽면보다 2cm 나오게 (벽면과 같은 평면이면 z-fighting)
                asm.add(box(ow + 0.2, 0.09, 0.38), f @ T(cx_, ya - 0.10, -0.17), M['granite_clad'], 1.2)
            continue
        # 칸 기둥은 띠와 띠 사이 구간에만 (띠와 같은 바깥면에서 겹치지 않게 → z-fighting 없음)
        for x in xs[1:-1]:
            asm.add(box(0.8, yb - ya, DEPTH), f @ T(x, (ya + yb) / 2, -DEPTH / 2), M['granite_clad'], 1.2)
        for k in range(n):
            xa = xs[k] + (0.4 if k > 0 else 0)
            xb = xs[k + 1] - (0.4 if k < n - 1 else 0)
            ow, oh = xb - xa, yb - ya
            cx_, cy_ = (xa + xb) / 2, (ya + yb) / 2
            glow.add(plane(ow, oh), f @ T(cx_, cy_, -0.34), random.choice(ROOMS), tile=None)
            # 전에는 발광 판 하나 + 창대뿐이라 멀리서 보면 납작한 네모 불빛이었다.
            # 실제 연수동은 짙은 알루미늄 창틀에 중간 멀리언·가로 창틀이 들어간 커튼월이다.
            asm.add(box(ow, oh, 0.012), f @ T(cx_, cy_, -0.20), M['winGlass'], 1)          # 유리면
            for (bw, bh, by) in ((ow + 0.12, 0.11, ya - 0.03), (ow + 0.12, 0.11, yb + 0.03)):
                asm.add(box(bw, bh, 0.11), f @ T(cx_, by, -0.15), M['winFrame'], 1)        # 상·하 창틀
            for sx_ in (xa - 0.05, xb + 0.05):
                asm.add(box(0.1, oh + 0.16, 0.11), f @ T(sx_, cy_, -0.15), M['winFrame'], 1)   # 좌·우 선틀
            for j in range(1, max(2, round(ow / 1.35))):                                   # 세로 멀리언
                asm.add(box(0.07, oh, 0.10), f @ T(xa + j * ow / max(2, round(ow / 1.35)), cy_, -0.155), M['winFrame'], 1)
            asm.add(box(ow, 0.07, 0.10), f @ T(cx_, ya + oh * 0.62, -0.155), M['winFrame'], 1)   # 가로 창틀
            asm.add(box(ow + 0.2, 0.09, 0.34), f @ T(cx_, ya - 0.10, -0.17), M['granite_clad'], 1.2)   # 석재 창대


def block(asm, x0, x1, z0, z1, h, floors, parapet=1.3, terrace=True, arcade=None, ribbon=False, body_w=0.0,
          win=None, rail=True):
    """모서리 기둥 4개 + 네 벽 + 안쪽 몸체 + 옥상

    body_w : 안쪽 몸체의 -x 쪽을 이만큼 더 물린다 (그 면 유리를 안으로 넣을 때)
    rail   : 옥상 가장자리 쇠난간 (흰 돌난간을 따로 두는 동은 끈다)"""
    bx0 = x0 + 0.7 + body_w
    asm.add(box(x1 - 0.7 - bx0, h, z1 - z0 - 1.4), T((bx0 + x1 - 0.7) / 2, h / 2, (z0 + z1) / 2), M['stoneWall'], 2)   # 몸체는 유리(0.3) 보다 안쪽
    for (cx, cz) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
        ox = 0.45 if cx == x0 else -0.45
        oz = 0.45 if cz == z0 else -0.45
        asm.add(box(0.9, h + parapet, 0.9), T(cx + ox, (h + parapet) / 2, cz + oz), M['granite_clad'], 1.2)
    arc = set(arcade or ())     # 아케이드를 둘 면 ('n' = -z, 'e' = +x, 's' = +z, 'w' = -x)
    if 'N' not in arc:          # 대문자 N = 그 면은 따로 그린다 (연수동 정면)
        wall(asm, x1, z0, x1 - x0, PI, h, floors, parapet, 'n' in arc, ribbon, 0.0, win)      # -z 면
    wall(asm, x1, z1, z1 - z0, PI / 2, h, floors, parapet, 'e' in arc, ribbon, 0.0, win)      # +x 면
    wall(asm, x0, z1, x1 - x0, 0.0, h, floors, parapet, 's' in arc, ribbon, 0.0, win)         # +z 면
    if 'W' not in arc:          # 대문자 W = 그 면은 따로 그린다 (연수동 정면)
        wall(asm, x0, z0, z1 - z0, -PI / 2, h, floors, parapet, 'w' in arc, ribbon, 0.0, win)  # -x 면
    if terrace:
        asm.add(box(x1 - x0 - 0.9, 0.3, z1 - z0 - 0.9), T((x0 + x1) / 2, h + 0.15, (z0 + z1) / 2), M['terrace'], 1.6)
        for (ax, az, bx, bz) in () if not rail else ((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
            a, b = V((ax, h + parapet + 0.25, az)), V((bx, h + parapet + 0.25, bz))
            g, m = tube(a, b, 0.035, 8)
            asm.add(g, m, M['steelRail'])
            n = max(1, round((b - a).length / 1.6))
            for k in range(n + 1):   # 난간 기둥 (난간벽 위에 박힘)
                p = a + (b - a) * (k / n)
                asm.add(box(0.04, 0.3, 0.04), T(p.x, h + parapet + 0.1, p.z), M['steelRail'], 1)


def _spandrel(cx, spr, rr, h1, half_w, depth, n=40):
    """아치 바깥선 위쪽 벽면을 한 장의 면으로 (아치 곡선을 그대로 따라간다)"""
    def build(bm):
        pts = [(cx + math.cos(PI * i / n) * rr, spr + math.sin(PI * i / n) * rr) for i in range(n + 1)]
        pts += [(cx - half_w, spr), (cx - half_w, h1), (cx + half_w, h1), (cx + half_w, spr)]
        vs = [bm.verts.new((x, y, 0.0)) for (x, y) in pts]
        bm.faces.new(vs)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=depth)
    return build


def yeonsu_front(asm, f, L, h1, arc0, pitch=4.6, ow_wide=2.54, ow_narrow=1.85, spr=2.46):
    """연수동 잔디 쪽 아치 정면 — 결과물 09-00-43 013 에서 **사람(1.75m)을 자로 써서** 실측.

    아케이드 앞에 선 사람 키 210px = 1.75m -> 120 px/m. 그 자로 잰 값:
      개구 폭 305px = 2.54m / 기공선 295px = 2.46m / 꼭대기 435px = 3.63m (반지름 1.27)
      개구 비례 1 : 1.43  (사진 49 만 보고 잰 '정사각형 0.97' 은 원근 때문에 틀린 값이었다)
      베이 피치 550px = 4.6m -> 개구/피치 0.55, 피어 2.06m. 여섯 베이면 정면 27.6m
      양 끝 베이는 개구가 좁다 (사진 49 의 폭/피치 0.46 : 0.63 -> 1.85m)
      아치 꼭대기가 벽의 56% -> 벽 높이 약 6.5m
    """
    NA = 26                                          # 아치테 분할. seg=6 이면 육각형으로 각진다
    for k in range(6):
        cx_ = arc0 + (k + 0.5) * pitch
        ow = ow_narrow if k in (0, 5) else ow_wide
        r_ = ow / 2
        rr = r_ + 0.34                               # 아치테 바깥 반지름
        # 개구 안: 유리는 표면에, 방 불빛은 그 뒤로 (표면에 발광 이미지를 붙이면 형광 줄무늬가 된다)
        glow.add(plane(ow, spr - 0.25), f @ T(cx_, (spr + 0.25) / 2, -0.85), random.choice(ROOMS), tile=None)
        glow.add(ring_segment(0, r_ - 0.02, 0, PI, 0.04), f @ T(cx_, spr, -0.85, 0, -PI / 2), random.choice(ROOMS), tile=None)
        asm.add(box(ow, spr - 0.25, 0.02), f @ T(cx_, (spr + 0.25) / 2, -0.26), M['winGlass'], 1)
        asm.add(ring_segment(0, r_ - 0.02, 0, PI, 0.02), f @ T(cx_, spr, -0.26, 0, -PI / 2), M['winGlass'], 1)
        for m in range(1, 3):                        # 유리문 세로 멀리언 (가늘게)
            asm.add(box(0.05, spr - 0.25, 0.08), f @ T(cx_ - ow / 2 + m * ow / 3, (spr + 0.25) / 2, -0.24), M['winFrame'], 1)
        for m in range(1, 4):                        # 반원 광창 방사 살
            a_ = PI * m / 4
            asm.add(box(0.045, r_ - 0.03, 0.08),
                    f @ T(cx_ + math.cos(a_) * (r_ - 0.03) / 2, spr + math.sin(a_) * (r_ - 0.03) / 2,
                          -0.24, 0, 0, a_ - PI / 2), M['winFrame'], 1)
        asm.add(box(ow, 0.07, 0.08), f @ T(cx_, spr, -0.24), M['winFrame'], 1)
        # 흰 돌 아치테 (촘촘히) + 문설주
        asm.add(ring_segment(r_, rr, 0, PI, DEPTH, seg=NA), f @ T(cx_, spr, -DEPTH, 0, -PI / 2), M['granite_clad'], 1.2)
        for sx_ in (-1, 1):
            asm.add(box(0.34, spr, DEPTH), f @ T(cx_ + sx_ * (ow + 0.34) / 2, spr / 2, -DEPTH / 2), M['granite_clad'], 1.2)
            asm.add(box((pitch - 2 * rr) / 2, h1, DEPTH),                              # 아치 옆 피어 (아치테 바깥부터)
                    f @ T(cx_ + sx_ * (pitch + 2 * rr) / 4, h1 / 2, -DEPTH / 2), M['granite_clad'], 1.2)
        # 스팬드럴 — 아치 바깥선을 따라가는 한 장의 면.
        # 상자를 층층이 쌓으면 계단처럼 각지고 모서리마다 세로 줄이 생긴다.
        asm.add(_spandrel(cx_, spr, rr, h1, pitch / 2, DEPTH), f @ T(0, 0, -DEPTH), M['granite_clad'], 1.2)
        asm.add(box(ow + 0.5, 0.22, 0.45), f @ T(cx_, 0.11, -0.24), M['granite'], 1.5)    # 디딤돌
    for (a_, b_) in ((0.0, arc0), (arc0 + 6 * pitch, L)):                                 # 아치 열 밖은 민 벽
        if b_ - a_ > 0.05:
            asm.add(box(b_ - a_, h1, DEPTH), f @ T((a_ + b_) / 2, h1 / 2, -DEPTH / 2), M['granite_clad'], 1.2)
    asm.add(box(L + 0.40, 0.34, DEPTH + 0.36), f @ T(L / 2, h1 - 0.17, -(DEPTH + 0.36) / 2), M['granite_clad'], 1.2)


def roof_hanok(asm, units, y0, axis, front, back, span0, span, eave=1.15, lamp0=520):
    """옥상 한옥 — 황룡원스테이가 공개한 **한옥층 평면도**(assets-src/refs/apec/plan_hanok_floor.png)
    에서 잰 배치 그대로.

    같은 도면의 객실층(plan_room_floor.png)에 있는 4인 침실 폭(약 5.5m)으로 축척을 잡으면
    15.5 px/m 이고, 그 자로 잰 값:
      평안재2호 7.7 x 10.0 / 대청 14.5 x 9.4 (가운데가 가장 크다) / 평안재1호 8.1 x 6.5
      세 채 뒤로 길이 35m · 폭 3.5m 짜리 **복도**가 지나 서로를 잇는다
    실제 옥상은 48m 인데 우리 씬의 옥상은 그보다 짧아, 도면의 **비례**를 유지한 채 줄여 앉힌다.

    axis='z' 면 배치축이 월드 z (정면은 -x), 'x' 면 배치축이 월드 x (정면은 -z).
    front/back 은 그 축과 직각인 방향의 앞선/뒤선.
    """
    ry = -PI / 2 if axis == 'z' else PI
    # 뒤를 잇는 복도 (기단 + 둥근 기둥 + 맞배 기와)
    cw = 3.0
    cc = back - cw / 2
    cf = T(cc, 0, span0 + span / 2, PI / 2) if axis == 'z' else T(span0 + span / 2, 0, cc, 0.0)
    asm.add(bevel_box(span - 1.0, 0.34, cw, 0.04), cf @ T(0, y0 + 0.17, 0), M['granite'], 1.5)
    n = max(2, round((span - 1.0) / 3.0))
    for k in range(n + 1):
        px = -(span - 1.0) / 2 + k * (span - 1.0) / n
        for pz in (-cw / 2 + 0.45, cw / 2 - 0.45):
            asm.add(cyl(0.16, 0.18, 2.5, 12), cf @ T(px, y0 + 0.34 + 1.25, pz), M['pillarStone'], 1)
    for pz in (-cw / 2 + 0.45, cw / 2 - 0.45):
        asm.add(box(span - 0.8, 0.34, 0.24), cf @ T(0, y0 + 2.96, pz), M['rafter'], 1)
    gb = y0 + 3.13
    half = (cw + 1.9) / 2
    rafters(asm, cf, span - 1.0, cw / 2, half - 0.25, lambda r: gb + 1.25 * (1 - r / half) - 0.1 * math.sin(PI * r / half), step=0.5)
    asm.add(gable_roof(span - 1.0, cw + 1.9, 1.25, sag=0.1), cf @ T(0, gb, 0), M['tileGrey'], 1.4)
    ridge(asm, cf, span - 1.4, gb + 1.25)
    # 채
    for k, (t, w, d, label) in enumerate(units):
        c = span0 + t * span
        a = front + d / 2 + 0.9                       # 채 중심 (앞선에서 조금 물러나 기단 자리를 둔다)
        cx, cz = (a, c) if axis == 'z' else (c, a)
        asm.add(bevel_box(w + 2.2 if axis == 'z' else d + 2.2, 0.34,
                          d + 2.2 if axis == 'z' else w + 2.2, 0.04),
                T(cx, y0 + 0.17, cz), M['granite'], 1.5)
        hanok(asm, cx, cz, w, d, ry=ry, y0=y0 + 0.34, label=label, lamp=lamp0 if k % 2 == 0 else 0, eave=eave)
        # 채 앞 자갈밭
        gx, gz = (front - 0.8, c) if axis == 'z' else (c, front - 0.8)
        asm.add(box(1.6 if axis == 'z' else w + 2.0, 0.06, w + 2.0 if axis == 'z' else 1.6),
                T(gx, y0 + 0.06, gz), M['terrace'], 1.6)


def yeonsu_block():
    """연수동 — 결과물 폴더 09-00-43 013 / 09-00-46 016 / 09-00-49 020 을 보고 다시.

    전에는 3단으로 물러나는 계단식 매스에, 앞쪽으로 임의의 연결동까지 달아 놨었다.
    사진의 실제 모습:
      · 두 동 모두 **2층** 화강석 몸체. 사람 키로 재니 한 층 약 4.6m (북동 9.2 / 북서 10.0)
      · 옥상 파라펫에 **흰 돌난간**, 그 뒤로 **물러앉은 한옥 누각**들과 분재 소나무
      · 1층 잔디 쪽은 **둥근 아치 열**, 위층은 **긴 리본 창** (안이 따뜻하게 밝다)
      · 두 동 사이는 **통유리 연결부**
      · 동쪽 동 앞 잔디 가장자리를 따라 **단층 기와 회랑**이 길게 지난다
    """
    # 귀빈동(북동동, 잔디 북쪽 / data.js 의 '귀빈동 테라스' 카메라가 이 옥상이다) 과
    # 연수동(북서동, 잔디 동쪽)은 서로 다른 동이다. 아치 정면은 **연수동** 것이다.
    NX0, NX1, NZ0, NZ1 = 23.0, 53.0, 20.0, 48.0
    H1, H2 = 5.3, 3.2                  # 아래단(아치 벽) / 물러앉은 윗단(유리층) — 사진 실측
    HG = 9.6                           # 귀빈동 몸체 (사진 013/020: 2층 리본창)
    HE = H1 + H2                       # 연수동 = 아래단 + 물러앉은 윗단
    YG, YE = HG + 0.35, HE + 0.35      # 각 옥상 바닥

    # ── 귀빈동 (잔디 북쪽) ────────────────────────────────────────
    # 실사 사진 결과물/KakaoTalk_Photo_2025-11-03-08-59-55 007.jpeg 를 확대해서 읽은 모습.
    # 날개 둘에 안마당(수영장)이 낀 h 자가 아니라 **거의 육면체인 한 덩어리**다.
    #   · 화강석 2층 몸체. 2층은 돌기둥이 하나도 없이 가는 멀리언만 선 **통창**이고,
    #     천장 다운라이트가 유리 뒤로 줄줄이 비친다.
    #   · 중도타워(-x) 쪽 2층은 유리가 안으로 물러나 그 앞이 **발코니**다. 흰 돌난간이
    #     둘러 있고 사람이 서 있다. 난간 아래 벽은 끊김 없이 그대로 내려가므로
    #     내민 발코니가 아니라 **들어간** 발코니다.
    #   · 옥상 파라펫에 흰 돌난간, 그 뒤로 한옥 (한옥 모양은 다음 단계)
    # 높이는 008-59-55 007 의 **돌난간(0.95m)을 자로** 삼아 잰 값이다 (84 px/m):
    #   돌난간 80px 0.95 / 난간 밑 돌띠 155px 1.84 / 2층 창 175px 2.08 /
    #   창 아래 민 돌벽 285px 3.4+ ... 그리고 사진 66 에서 1층 창은 2층 창의 0.54 배.
    # 발코니 **깊이**만은 어느 사진에서도 잴 수 없어 2.0m 로 가정했다.
    PRP = 0.77                                                             # 솔리드 파라펫 윗면 = HG + PRP
    BRC = 2.0                                                              # 발코니 깊이 (가정)
    W2 = (6.44, 8.52)                                                      # 2층 통창
    W1 = (2.92, 4.04)                                                      # 1층 창 (회랑 지붕 바로 위)
    BF = W2[0]                                                             # 창대 = 발코니 바닥
    block(ye_ne, NX0, NX1, NZ0, NZ1, HG, 2, parapet=PRP, ribbon=True, arcade='W',
          body_w=BRC + 0.5, win={0: W1, 1: W2}, rail=False)
    wall(ye_ne, NX0, NZ0, NZ1 - NZ0, -PI / 2, HG, 2, PRP, False, True, BRC, {0: W1, 1: W2})  # -x 면: 유리를 물려 발코니
    ye_ne.add(box(BRC + 0.5, BF - 0.3, NZ1 - NZ0 - 1.4),                       # 발코니 밑(1층)은 꽉 찬 몸체
              T(NX0 + 0.7 + (BRC + 0.5) / 2, (BF - 0.3) / 2, (NZ0 + NZ1) / 2), M['stoneWall'], 2)
    # 발코니 바닥 — 윗면을 창대(BF)와 **같은 높이로 두면 벽 면과 한 평면이 되어 z-fighting**.
    # 2cm 낮춰 깔고, 벽 쪽 창대 띠가 그 위로 조금 드러나게 둔다.
    ye_ne.add(box(BRC, 0.30, NZ1 - NZ0 - 1.8),                       # 마구리도 벽면보다 5cm 나오게
              T(NX0 - 0.05 + BRC / 2, BF - 0.17, (NZ0 + NZ1) / 2), M['terrace'], 1.6)
    balustrade(ye_ne, [(NX0 + 0.26, BF - 0.02, NZ0 + 1.0), (NX0 + 0.26, BF - 0.02, NZ1 - 1.0)], h=0.95, post=2.3)
    # 옥상 난간 — 파라펫 **위에** 올라탄다 (전에는 파라펫 속에 반쯤 묻혀 있었다).
    # 한 줄로 이어서 돌린다. 변마다 따로 부르면 모서리 동자기둥이 두 번 겹쳐 박힌다.
    balustrade(ye_ne, [(NX0 + 0.5, HG + PRP, NZ1 - 0.5), (NX0 + 0.5, HG + PRP, NZ0 + 0.5),
                       (NX1 - 0.5, HG + PRP, NZ0 + 0.5), (NX1 - 0.5, HG + PRP, NZ1 - 0.5)],
                h=0.95, post=2.5)
    # ── 귀빈동 옥상 한옥 ──────────────────────────────────────────
    # 클라이언트 도식(images/56) 아래 그림: 낱개 정자가 아니라 **한 덩어리로 이어진
    # ㄱ(4)자** — 깊이 방향 줄기 하나 + 아래쪽으로 뻗는 긴 가로 팔.
    GY = YG
    ARM_Z = NZ1 - 4.2
    hanok(ye_ne, (NX0 + 3.0 + NX1 - 3.0) / 2, ARM_Z, NX1 - NX0 - 6.0, 5.6,
          ry=PI, y0=GY + 0.34, label='행복재', lamp=660, eave=1.3)          # 긴 가로 팔
    ye_ne.add(bevel_box(NX1 - NX0 - 3.8, 0.34, 7.8, 0.04),
              T((NX0 + NX1) / 2, GY + 0.17, ARM_Z), M['granite'], 1.5)
    STEM_X = NX0 + 8.0
    # y0 를 가로 팔보다 1.2cm 올린다 — 두 채의 기단이 맞물리는 자리에서 윗면이 정확히
    # 같은 높이라 z-fighting 이 났다. 이어 붙는 모양 자체는 옥상 한옥 다시 만들 때 정리.
    hanok(ye_ne, STEM_X, ARM_Z - 9.6, 12.0, 5.6, ry=-PI / 2, y0=GY + 0.352,
          label='황룡헌', lamp=760, eave=1.3)                                # 깊이 방향 줄기
    # 줄기 기단은 가로 팔 기단(z = ARM_Z ± 3.9) 앞에서 끊는다. 겹쳐 깔면 윗면·밑면이
    # 두 장씩 같은 높이에 놓여 그대로 z-fighting 이 난다.
    SZ1 = ARM_Z - 3.9
    SZ0 = ARM_Z - 9.6 - 7.1
    ye_ne.add(bevel_box(7.8, 0.34, SZ1 - SZ0, 0.04), T(STEM_X, GY + 0.17, (SZ0 + SZ1) / 2), M['granite'], 1.5)
    for k in range(4):                                                       # 마당 쪽 분재 소나무
        ye_ne.add(cyl(0.55, 0.45, 0.6, 16), T(NX0 + 16.0 + k * 4.0, GY + 0.3, ARM_Z - 8.0), M['granite_clad'], 1)
        ye_ne.add(sphere(0.62, 2), T(NX0 + 16.0 + k * 4.0, GY + 0.85, ARM_Z - 8.0, sy=0.62), M['shrub'], 1)

    # ── 두 동 사이 통유리 연결부 (사진 013 가운데 유리 띠) ────────────────
    LX0, LX1, LZ0, LZ1 = 44.0, 50.0, 13.6, 20.0
    ye_ne.add(box(LX1 - LX0 - 1.2, HG, LZ1 - LZ0 - 1.2), T((LX0 + LX1) / 2, HG / 2, (LZ0 + LZ1) / 2), M['stoneWall'], 2)
    for (px, pz) in ((LX0, LZ0), (LX1, LZ0), (LX0, LZ1), (LX1, LZ1)):            # 모서리 멀리언
        ye_ne.add(box(0.26, HG + 0.5, 0.26), T(px, (HG + 0.5) / 2, pz), M['winFrame'], 1)
    for (cx_, cz_, w_, ry_) in ((LX0 + (LX1 - LX0) / 2, LZ0, LX1 - LX0, 0.0),
                                (LX0, LZ0 + (LZ1 - LZ0) / 2, LZ1 - LZ0, PI / 2)):
        g = T(cx_, 0, cz_, ry_)
        glass_roof.add(box(w_, HG - 0.2, 0.06), g @ T(0, (HG - 0.2) / 2 + 0.1, 0), M['skylight'])
        for j in range(1, max(2, round(w_ / 2.4))):                               # 세로 멀리언
            ye_ne.add(box(0.11, HG, 0.16), g @ T(-w_ / 2 + j * w_ / max(2, round(w_ / 2.4)), HG / 2, 0), M['winFrame'], 1)
        ye_ne.add(box(w_, 0.14, 0.18), g @ T(0, HG * 0.5, 0), M['winFrame'], 1)   # 중간 가로틀
        ye_ne.add(box(w_ + 0.3, 0.30, 0.34), g @ T(0, HG + 0.15, 0), M['granite_clad'], 1.2)   # 상부 돌띠

    # ── 옥상 천창 ────────────────────────────────────────────────────
    ye_ne.add(box(6.5, 0.25, 10.0), T(46, YG + 0.12, 40), M['granite_clad'], 1.2)
    glass_roof.add(box(6.1, 1.1, 9.6), T(46, YG + 0.80, 40), M['skylight'])

    # ── 옥상 테라스 가구 ─────────────────────────────────────────────
    # 두 프롭 모두 원점이 밑바닥이라 옥상 바닥 높이에 그대로 얹는다 (전에 공중에 떴었다)
    for k, (x, z) in enumerate(((27.0, 42), (33.0, 44), (39.0, 42), (45.0, 44.5))):
        ye_ne.add(mesh_source(SRC_TABLESET), T(x, YG, z, k * 0.7), list(SRC_TABLESET.data.materials))
        ye_ne.add(mesh_source(SRC_PARASOL), T(x, YG, z), list(SRC_PARASOL.data.materials))
    light(C_LIGHT, 'site_terrace', 'POINT', (34.0, YG + 2.6, 43), energy=160, color=(1.0, 0.78, 0.5), size=0.3)

    # ── 북서동 (잔디 동쪽) : 아케이드가 잔디(-x)를 본다 ──────────────────
    # 연수동 — 실측(사람 1.75m 기준): 베이 4.6 x 6 = 정면 27.6, 벽 6.5,
    #   물러앉은 윗단(객실 2~4층, 33실/113명)은 3.4 더, 단마다 흰 돌난간, 옥상은 한옥 마을.
    # 평면도 실측대로 **위아래로 긴** 건물 (48 x 17). 전에는 29.6 x 27.6 으로 거의
    # 정사각형이라 옥상이 좁고 한옥이 넘쳤다.
    EX0, EX1, EZ0, EZ1 = 36.4, 53.4, -26.0, 18.0     # 깊이 17 / 길이 44
    SET = 2.6
    # 실사 사진: 아치부터 처마 돌림띠까지 **한 면으로 쭉** 올라가고, 흰 돌난간은
    # 맨 위 한 줄뿐이다. 물러앉은 2단을 따로 얹었더니 중간에 단차가 생기고
    # 그 면에 큰 창이 줄지어 붙어 난간도 두 줄이 됐다 -> 한 덩어리로 되돌린다.
    HL, HU = 8.0, 0.0
    block(ye_nw, EX0, EX1, EZ0, EZ1, HL, 1, parapet=0.95, arcade='W')
    yeonsu_front(ye_nw, T(EX0, 0, EZ0, -PI / 2), EZ1 - EZ0, HL, arc0=(EZ1 - EZ0 - 27.6) / 2)
    balustrade(ye_nw, [(EX0 + 0.6, HL + 0.95, EZ0 + 0.8), (EX0 + 0.6, HL + 0.95, EZ1 - 0.8)], h=0.82, post=2.4)
    YBACK = EX1 - 1.4                                   # 채들이 붙는 뒤쪽 선
    # 클라이언트 도식(images/62)을 픽셀로 재서 비율 그대로.
    #   데크 180 x 288 / 양옆 138 x 60 (깊이 77%, 길이 21%) / 가운데 108 x 110 (정사각)
    #   셋 다 뒤쪽 변에 flush, 가운데가 좁아 잔디 쪽에 홈이 생긴다.
    #   우리 옥상(깊이 17 / 길이 44) 환산 -> 양옆 13.0 x 9.2, 가운데 10.2 x 10.2
    # 용마루는 각 채의 **긴 쪽**으로 간다: 양옆은 깊이 방향(x, ry=0/PI), 가운데는 z.
    # 세 채 모두 **잔디(-x) 쪽이 열린 대청마루**다 (실사 사진 08-59-54 005 확대).
    # 가운데는 긴 면이 잔디를 보므로 open_front, 양옆은 박공 끝이 잔디를 보므로
    # open_end 로 그 끝칸을 연다. 전에는 양옆을 open_front 로 열어 대청이 가운데
    # 채를 향하고, 잔디 쪽에는 흰 회벽만 보였다.
    ZMID = (EZ0 + EZ1) / 2
    # 양옆은 더 길쭉하고 얇게 (13.0 x 9.2 -> 13.0 x 6.0, 비 2.2:1).
    # 깊이는 건물(17)에서 처마 2.4 를 빼면 13.0 이 한계라 길이를 줄여 비례를 뽑는다.
    # ry=0 이면 로컬 x = 월드 x 라 잔디(-x)는 로컬 -x, ry=PI 면 뒤집혀 로컬 +x 다.
    SPEC = ((ZMID - 12.6, 13.0, 6.0, 0.0, '평안재2', 520, -1),
            (ZMID, 9.0, 9.0, -PI / 2, '대청', 720, 0),
            (ZMID + 12.6, 13.0, 6.0, PI, '평안재1', 460, +1))
    for (cz, deep, along, rk, label, lamp, oe) in SPEC:
        ridge_len, dep = (deep, along) if abs(rk) != PI / 2 else (along, deep)
        cx = YBACK - deep / 2
        ye_nw.add(bevel_box(deep + 1.8, 0.34, along + 1.8, 0.04), T(cx, HL + HU + 0.47, cz), M['granite'], 1.5)
        hanok(ye_nw, cx, cz, ridge_len, dep, ry=rk, y0=HL + HU + 0.64, label=label, lamp=lamp, eave=1.2,
              open_front=(oe == 0), open_end=oe, veranda=(oe == 0))
    # 세 채 앞(잔디 쪽) 빈 데크에 자갈밭 + 분재 소나무
    for k in range(5):
        ye_nw.add(cyl(0.55, 0.45, 0.6, 16), T(EX0 + SET + 1.8, HL + HU + 0.6, EZ0 + 5.0 + k * 8.5), M['granite_clad'], 1)
        ye_nw.add(sphere(0.62, 2), T(EX0 + SET + 1.8, HL + HU + 1.15, EZ0 + 5.0 + k * 8.5, sy=0.62), M['shrub'], 1)
    # 여기 있던 '계단실' 상자는 근거 없이 내가 넣은 것이다 — 뺀다
    # ── 잔디와 연수동 사이 광장 + 계단 ────────────────────────────────
    ye_nw.add(box(5.8, 0.45, 52), T(39.1, 0.22, -8), M['terrace'], 1.6)
    for k in range(3):
        ye_nw.add(box(0.4, 0.15 * (k + 1), 51.6), T(35.2 + k * 0.4, 0.075 * (k + 1), -8), M['terrace'], 1.6)
    for z in range(-30, 12, 10):
        light(C_LIGHT, f'site_wash_w{z}', 'SPOT', (39.5, 0.6, z), (42.5, 6, z), energy=900,
              color=(1.0, 0.8, 0.55), spot=0.6, blend=0.8, size=0.3)

    # (잔디 쪽 정면에는 아무것도 붙이지 않는다 — 클라이언트 사진에 아치 앞은 비어 있다)


def lodge_corridor(asm, cx, z0, z1, ry, w=3.4):
    """연수동 앞 단층 기와 회랑 — 돌기단 + 둥근 석주 + 주칠 도리 + 회색 기와 맞배지붕.
       사진 013/020: 잔디 가장자리를 따라 길게 지나며 처마 밑에 등이 줄지어 있다."""
    L = z1 - z0
    f = T(cx, 0, (z0 + z1) / 2, ry)          # 로컬 x = 길이 방향
    asm.add(bevel_box(L, 0.42, w + 1.0, 0.04), f @ T(0, 0.21, 0), M['granite'], 1.5)
    n = max(1, round(L / 3.2))
    for k in range(n + 1):
        x = -L / 2 + k * L / n
        for zz in (-w / 2, w / 2):
            asm.add(box(0.62, 0.30, 0.62), f @ T(x, 0.42 + 0.15, zz), M['granite'], 1)
            asm.add(cyl(0.22, 0.25, 2.85, 14), f @ T(x, 0.57 + 1.425, zz), M['pillarStone'], 1)
        asm.add(box(0.24, 0.36, w + 0.4), f @ T(x, 3.18, 0), M['rafter'], 1)          # 대들보
    for zz in (-w / 2, w / 2):
        asm.add(box(L + 0.3, 0.44, 0.28), f @ T(0, 3.22, zz), M['rafter'], 1)         # 도리
    gb = 3.44
    half = (w + 2.6) / 2
    slope = lambda r: gb + 1.55 * (1 - r / half) - 0.14 * math.sin(PI * r / half)
    rafters(asm, f, L, w / 2, half - 0.28, slope, step=0.55)
    asm.add(gable_roof(L, w + 2.6, 1.55, sag=0.14), f @ T(0, gb, 0), M['tileGrey'], 1.4)
    ridge(asm, f, L - 0.2, gb + 1.55)
    for k in range(0, n, 2):
        x = -L / 2 + (k + 0.5) * L / n
        light(C_LIGHT, f'site_lodge_{round(cx)}_{k}', 'POINT', tuple(f @ V((x, 2.9, 0))),
              energy=110, color=(1.0, 0.76, 0.46), size=0.3)


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
    """대기용 팝업 천막 (gear.popup_tent) + 접이식 테이블·의자"""
    f = T(x, 0.12, z, ry)
    gear.popup_tent(backstage, f, M, size=5.0, walls=(True, True, True, False))
    backstage.add(bevel_box(1.8, 0.04, 0.75, 0.01), f @ T(0, 0.74, -1.3), M['tent'], 1)
    for sx in (-0.8, 0.8):
        backstage.add(bevel_box(0.04, 0.72, 0.6, 0.005), f @ T(sx, 0.36, -1.3), M['alu'], 1)
        gear.folding_chair(backstage, f @ T(sx * 0.7, 0, -0.5, PI), M)


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
        for k in range(0 if (ax, az) == runs[0][0] else 1, n + 1):   # 모서리 기둥은 한 번만
            t = k / n
            backstage.add(box(0.04, DH, 0.04), T(ax + (bx - ax) * t, y0 + DH / 2, az + (bz - az) * t, ang), M['tent'], 1)
        for yy in (0.1, DH):
            gg, m = tube(V((ax, y0 + yy, az)), V((bx, y0 + yy, bz)), 0.02, 6)
            backstage.add(gg, m, M['tent'])
    # 운영 데스크: 플라이트 케이스 위에 실제 장비 (운영자는 -z 쪽에 앉아 무대(+z)를 본다)
    zt = zf - 0.9
    rows = ((cx - 3.2, 1.7, 'light'), (cx - 0.6, 1.5, 'audio'), (cx + 3.3, 1.9, 'video'))   # 기둥(x ±1.83) 피해서
    for (x, w, kind) in rows:
        gear.road_case(backstage, T(x, y0, zt), M, w, 0.8, 0.85)
        desk = T(x, y0 + 0.8, zt, PI)                                      # 장비 앞(+z 로컬)이 운영자 쪽
        if kind == 'light':
            gear.lighting_console(backstage, desk, M, glow)
        elif kind == 'audio':
            backstage.add(mesh_source(SRC_MIXER), desk, M['consoleBody'])
            gear.program_monitor(backstage, T(x + 0.55, y0 + 0.8, zt + 0.25), M, glow, M['uiAudio'], height=0.45, w=0.5, hgt=0.32)
        else:
            gear.video_switcher(backstage, desk @ T(-0.45, 0, 0.05), M, glow)
            backstage.add(mesh_source(SRC_LAPTOP), desk @ T(0.45, 0, 0.1), list(SRC_LAPTOP.data.materials))
            gear.program_monitor(backstage, T(x, y0 + 0.8, zt + 0.3), M, glow, M['uiVideo'], height=0.5, w=0.62, hgt=0.36)
    for (x, _, _) in rows:           # 스태프 접이식 의자
        gear.folding_chair(backstage, T(x, y0, zt - 1.0), M)
    # 55인치 프로그램 모니터 (칸막이 밖, 운영석 쪽을 봄)
    gear.program_monitor(backstage, T(cx - 2.0, y0, zf + 0.45), M, glow, bpy.data.materials['led'])
    gear.program_monitor(backstage, T(cx + 3.6, y0, zf + 0.35), M, glow, M['uiVideo'], height=1.7, w=0.62, hgt=0.4)
    # 오른쪽 옆 줄: 중계 데스크 (케이스 + 노트북)
    for zz in (zf - 1.2, zf - 2.6):
        gear.road_case(backstage, T(cx + 4.9, y0, zz), M, 0.75, 0.74, 1.3, handles=False)
        backstage.add(mesh_source(SRC_LAPTOP), T(cx + 4.9, y0 + 0.74, zz, -PI / 2), list(SRC_LAPTOP.data.materials))
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
        gear.road_case(backstage, T(x, y0, z), M, 0.8, 0.6, 0.6)


def backstage_block():
    # 대기용 천막: 무대 바로 뒤 (무대 뒤 계단과 신평루 사이)
    tent(2.8, -26.8)
    tent(9.2, -26.8)
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
    pts = [V((px, -0.15, pz))]
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
    g, m = tube(V((px, -0.15, pz)), top, 0.22 * s, 10, caps=True)
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
PLATE = (-84, 94, -66, 70)   # 웹 받침판 범위 (src/venues/apec/scene.js PLATE) — 판 밖 나무는 심지 않는다
for k, (x, z, dens) in enumerate(SITE_TREES):
    if not (PLATE[0] + 4 <= x <= PLATE[1] - 4 and PLATE[2] + 4 <= z <= PLATE[3] - 4):
        continue
    rs = random.Random(k)
    size = 0.85 + 0.35 * dens + rs.uniform(-0.1, 0.15)
    in_garden = -32 <= x <= 24 and 24 <= z <= 52
    on_lawn_ = -25 <= x <= 35 and -33 <= z <= 17
    if in_garden or on_lawn_ or rs.random() < 0.18:
        pine(x, z, size * (0.62 if on_lawn_ else 0.95), seed=k + 100)
    else:
        tree(x, z, size)
pines.build(smooth=True)
needles.build()
leaves.build()
glow.build()

# ── FOH: 회랑 가운데 누각 아래 콘솔 줄 (layout_v2 #14) ─────────────────────────
#    현장 사진의 오퍼레이터 줄은 신평루가 아니라 잔디를 마주 보는 회랑 누각 아래에 있었다.
foh = Assembly('foh_corridor', C_STATIC)
foh_glow = Assembly('foh_emissive', C_EMIT)
FOH_X, FOH_Z, FOH_Y = -5.5, 19.4, 0.45
# 회랑 아래 운영 부스 — onsite_085621_010 / _085619_007 실측.
# 전에는 상자 몇 개(192면)로 때워 놨었다. 실제로는 올리브색 파티션 패널 줄 +
# 그 위 전구 줄 + 플라이트 케이스에 올린 조명 콘솔 + 스탠드 PGM 모니터 +
# 노트북 올린 접이 테이블 + 쌓아 둔 랙 케이스 + 접이 의자다.
M_OLIVE = mat('fohOlive', 'cotton_jersey', (0.115, 0.135, 0.075), 0.92, normal=0.5)
M_ALU = mat('fohAlu', None, (0.52, 0.53, 0.55), 0.35, 0.8)
M_DESK = mat('fohDesk', None, (0.08, 0.08, 0.085), 0.5)
M_TABLE = mat('fohTable', None, (0.62, 0.60, 0.56), 0.6)
M_BULB = mat('fohBulb', None, (1.0, 0.86, 0.6), 0.3, emit=(1.0, 0.82, 0.52), emit_strength=22)


def foh_panel(f):
    """파티션 한 짝 1.2 x 1.0m: 알루미늄 테두리 + 올리브 천 + 밑에 받침발"""
    foh.add(box(1.2, 1.0, 0.035), f @ T(0, 0.5, 0), M_OLIVE, 1)
    for (yy, hh, ww) in ((0.985, 0.03, 1.22), (0.015, 0.03, 1.22)):
        foh.add(box(ww, hh, 0.045), f @ T(0, yy, 0), M_ALU, 1)
    for sx in (-0.6, 0.6):
        foh.add(box(0.03, 1.0, 0.045), f @ T(sx, 0.5, 0), M_ALU, 1)
        foh.add(box(0.05, 0.02, 0.26), f @ T(sx, 0.01, 0), M_ALU, 1)


def foh_table(f, w=1.5):
    """접이 테이블 — 상판 + X 다리"""
    foh.add(box(w, 0.035, 0.68), f @ T(0, 0.735, 0), M_TABLE, 1)
    foh.add(box(w - 0.04, 0.05, 0.05), f @ T(0, 0.70, 0), M_ALU, 1)
    for sx in (-w / 2 + 0.16, w / 2 - 0.16):
        for sz in (-1, 1):
            g_, m_ = tube(f @ V((sx, 0.70, sz * 0.28)), f @ V((sx, 0.0, sz * 0.32)), 0.016, 6)
            foh.add(g_, m_, M_ALU)
        g_, m_ = tube(f @ V((sx, 0.70, -0.28)), f @ V((sx, 0.0, 0.32)), 0.014, 6)
        foh.add(g_, m_, M_ALU)


def foh_laptop(f):
    """노트북 (화면 발광)"""
    foh.add(box(0.34, 0.015, 0.24), f, M_DESK, 1)
    lid = f @ T(0, 0.005, -0.12, 0, -1.85)
    foh.add(box(0.34, 0.012, 0.23), lid @ T(0, 0, 0.115), M_DESK, 1)
    foh_glow.add(plane(0.31, 0.20), lid @ T(0, 0.008, 0.115), M['uiVideo'], tile=None)


PZ = FOH_Z - 1.15
for k in range(8):                                            # 회랑 앞을 막은 파티션 줄
    foh_panel(T(FOH_X - 4.2 + k * 1.22, FOH_Y, PZ))
for k in range(3):                                            # 오른쪽으로 꺾인 세 짝
    foh_panel(T(FOH_X + 5.02, FOH_Y, PZ + 0.61 + k * 1.22, PI / 2))
for k in range(11):                                           # 파티션 위에 늘어뜨린 전구 줄
    bx = FOH_X - 4.6 + k * 1.02
    sag = 0.10 * math.sin(PI * (k % 2 + 0.5) / 2)
    foh.add(cyl(0.012, 0.012, 0.07, 8), T(bx, FOH_Y + 1.30 - sag, PZ - 0.02), M_DESK, 1)
    foh_glow.add(sphere(0.045, 2), T(bx, FOH_Y + 1.24 - sag, PZ - 0.02), M_BULB)
    light(C_LIGHT, f'foh_bulb_{k}', 'POINT', (bx, FOH_Y + 1.24 - sag, PZ - 0.02),
          energy=26, color=(1.0, 0.82, 0.55), size=0.05)

gear.road_case(foh, T(FOH_X - 2.6, FOH_Y, FOH_Z + 0.1), M, 1.35, 0.72, 0.78)   # 콘솔 받침 케이스
gear.lighting_console(foh, T(FOH_X - 2.6, FOH_Y + 0.72, FOH_Z + 0.1, PI), M, foh_glow)
# 회랑 앞 스탠드 PGM 모니터는 뺀다 — 잔디 한가운데 기둥에 판때기가 달린 꼴로 서 있었다
for (tx, tz, tw) in ((FOH_X + 0.6, FOH_Z + 0.2, 1.5), (FOH_X + 2.3, FOH_Z + 0.35, 1.5),
                     (FOH_X - 4.9, FOH_Z + 0.5, 1.2)):
    foh_table(T(tx, FOH_Y, tz))
    foh_laptop(T(tx - 0.3, FOH_Y + 0.755, tz - 0.03, 0.15))
gear.program_monitor(foh, T(FOH_X + 0.9, FOH_Y + 0.77, FOH_Z - 0.12), M, foh_glow, M['uiAudio'],
                     height=0.46, w=0.54, hgt=0.33, facing=0.0)
gear.video_switcher(foh, T(FOH_X + 2.4, FOH_Y + 0.77, FOH_Z + 0.3, PI), M, foh_glow)
for k in range(2):                                            # 쌓아 둔 랙 케이스 (3단은 토템처럼 솟아 보였다)
    gear.road_case(foh, T(FOH_X + 4.3, FOH_Y + k * 0.56, FOH_Z + 0.2), M, 0.62, 0.55, 0.72, handles=(k == 1))
for (cx_, cz_, cr) in ((FOH_X - 2.6, FOH_Z + 1.1, PI), (FOH_X + 0.7, FOH_Z + 1.2, PI),
                       (FOH_X + 2.4, FOH_Z + 1.3, PI + 0.2)):
    gear.folding_chair(foh, T(cx_, FOH_Y, cz_, cr), M)
foh.build()
foh_glow.build()

# ── 잔디에서 보이는 석조물 (assets-src/refs/apec/_notes_site_permanent.md) ────────
#    황룡원에 해태상은 없다. 잔디에서 보이는 사자 조각은 쌍사자 석등 하나뿐이고,
#    그 밖에 석양(石羊) 한 점, 탑 앞 당간지주형 표석, 북동 모서리 연못의 금룡이 있다.
stones = Assembly('site_stones', C_STATIC)
stones_glow = Assembly('site_stones_emissive', C_EMIT)
# 새하얗게 떠 보여서 사진의 화강암 회색으로 낮추고 석재 결을 넣었다
M_STONE = mat('siteGranite', 'granite_tile_03', (0.30, 0.295, 0.275), 0.92, normal=0.6)
M_GOLD = mat('siteGold', None, (0.66, 0.5, 0.18), 0.35, 0.85)
M_REDBAR = mat('siteRedBar', None, (0.42, 0.07, 0.06), 0.8)
M_LGLOW = mat('siteLanternGlow', None, (1, 0.8, 0.55), 0.5, emit=(1.0, 0.75, 0.45), emit_strength=4)


def lion_lantern(x, z, h=3.1):
    """쌍사자 석등 (법주사 쌍사자석등 형식) — 팔각 지대석·복련 하대석 위에 등을 맞댄
       사자 두 마리가 앙련 상대석을 이고, 그 위 팔각 화사석(화창 넷)과 처마가 들린
       팔각 옥개석, 꼭대기에 보주. 전에는 상자 몸통에 공 하나 얹은 정도였다."""
    f = T(x, 0, z)
    OCT = PI / 8
    stones.add(cyl(0.68, 0.68, 0.14, 8), f @ T(0, 0.07, 0, OCT), M_STONE, 1)             # 팔각 지대석
    stones.add(_sq(1.06, 0.86, 0.14, 8), f @ T(0, 0.21, 0, OCT), M_STONE, 1)             # 하대석 굄
    stones.add(_sq(0.86, 0.50, 0.26, 8), f @ T(0, 0.41, 0, OCT), M_STONE, 1)             # 복련 (엎은 연꽃)
    for i in range(8):                                                                   # 연꽃잎 여덟 장
        a = OCT + i * PI / 4
        stones.add(sphere(0.115, 2), f @ T(0.35 * math.sin(a), 0.36, 0.35 * math.cos(a),
                   a, 0, 0, 1.0, 0.62, 0.55), M_STONE)
    for sgn in (-1, 1):                                                                  # 등을 맞댄 사자 두 마리
        lf = f @ T(sgn * 0.165, 0.54, 0, 0, 0, sgn * 0.06)
        stones.add(bevel_box(0.235, 0.60, 0.40, 0.07), lf @ T(0, 0.32, -0.02), M_STONE, 1)   # 몸통
        stones.add(bevel_box(0.22, 0.30, 0.20, 0.06), lf @ T(0, 0.70, 0.07, 0, -0.30), M_STONE, 1)  # 가슴
        stones.add(sphere(0.155, 3), lf @ T(0, 0.90, 0.10, 0, 0, 0, 0.95, 1.0, 1.05), M_STONE)      # 갈기
        stones.add(bevel_box(0.115, 0.115, 0.13, 0.04), lf @ T(0, 0.86, 0.20), M_STONE, 1)          # 주둥이
        for sx_ in (-0.075, 0.075):                                                                  # 앞다리
            stones.add(cyl(0.045, 0.05, 0.40, 8), lf @ T(sx_, 0.20, 0.17, 0, 0.12), M_STONE, 1)
            stones.add(bevel_box(0.09, 0.05, 0.13, 0.02), lf @ T(sx_, 0.02, 0.22), M_STONE, 1)       # 발
        stones.add(cyl(0.05, 0.035, 0.36, 6), lf @ T(0, 0.34, -0.22, 0.55), M_STONE, 1)              # 꼬리
    stones.add(_sq(0.52, 0.86, 0.22, 8), f @ T(0, 1.52, 0, OCT), M_STONE, 1)             # 앙련 상대석
    for i in range(8):
        a = OCT + i * PI / 4
        stones.add(sphere(0.105, 2), f @ T(0.33 * math.sin(a), 1.52, 0.33 * math.cos(a),
                   a, 0, 0, 1.0, 0.58, 0.5), M_STONE)
    stones.add(cyl(0.48, 0.48, 0.07, 8), f @ T(0, 1.66, 0, OCT), M_STONE, 1)             # 화사석 받침
    HS, HH = 0.40, 0.60                                                                  # 화사석: 기둥 여덟 + 벽 넷
    for i in range(8):
        a = OCT + i * PI / 4
        stones.add(box(0.075, HH, 0.075), f @ T(HS * math.sin(a), 1.70 + HH / 2, HS * math.cos(a), a), M_STONE, 1)
    for i in range(4):
        a = OCT + (i * 2 + 1) * PI / 4 - PI / 8
        stones.add(box(0.30, HH, 0.07), f @ T((HS - 0.02) * math.sin(a), 1.70 + HH / 2, (HS - 0.02) * math.cos(a), a), M_STONE, 1)
    stones.add(cyl(0.46, 0.46, 0.06, 8), f @ T(0, 1.70 + HH + 0.03, 0, OCT), M_STONE, 1)  # 화사석 갑
    ry_ = 1.70 + HH + 0.06
    stones.add(_sq(0.96, 0.92, 0.09, 8), f @ T(0, ry_ + 0.045, 0, OCT), M_STONE, 1)      # 옥개석 처마
    stones.add(_sq(0.92, 0.30, 0.30, 8), f @ T(0, ry_ + 0.24, 0, OCT), M_STONE, 1)       # 낙수면
    for i in range(8):                                                                   # 처마 귀 반전
        a = OCT + i * PI / 4
        stones.add(bevel_box(0.14, 0.07, 0.11, 0.025), f @ T(0.44 * math.sin(a), ry_ + 0.10, 0.44 * math.cos(a), a, 0, -0.30), M_STONE, 1)
    stones.add(_sq(0.26, 0.14, 0.07, 8), f @ T(0, ry_ + 0.42, 0, OCT), M_STONE, 1)       # 노반
    stones.add(sphere(0.115, 3), f @ T(0, ry_ + 0.54, 0), M_STONE)                       # 보주
    stones_glow.add(cyl(0.30, 0.30, HH - 0.06, 8), f @ T(0, 1.70 + HH / 2, 0, OCT), M_LGLOW, 1)


def stone_ram(x, z, ry=0.0):
    """석양(石羊) — 왕릉 석물식 웅크린 돌 양 (전체 약 0.95m).
       전에는 상자 하나에 공 하나 붙인 것이었다: 몸통·네 다리·목·머리·말린 뿔·꼬리를 깎는다."""
    f = T(x, 0, z, ry)
    stones.add(bevel_box(1.26, 0.20, 0.78, 0.03), f @ T(0, 0.10, 0), M_STONE, 1)                  # 지대석
    stones.add(sphere(0.30, 3), f @ T(-0.04, 0.50, 0, 0, 0, 0, 1.55, 0.90, 0.80), M_STONE)        # 몸통
    stones.add(sphere(0.24, 3), f @ T(-0.34, 0.46, 0, 0, 0, 0, 1.0, 0.95, 0.85), M_STONE)         # 엉덩이
    for sx_ in (0.26, -0.24):                                                                     # 접은 네 다리
        for sz_ in (-0.19, 0.19):
            stones.add(bevel_box(0.20, 0.26, 0.13, 0.05), f @ T(sx_, 0.31, sz_), M_STONE, 1)
            stones.add(bevel_box(0.24, 0.10, 0.14, 0.04), f @ T(sx_ + 0.03, 0.23, sz_), M_STONE, 1)
    stones.add(cyl(0.13, 0.17, 0.26, 10), f @ T(0.33, 0.62, 0, 0, 0, -0.75), M_STONE, 1)          # 목
    stones.add(sphere(0.14, 3), f @ T(0.46, 0.70, 0, 0, 0, 0, 1.25, 0.95, 0.85), M_STONE)         # 머리
    stones.add(bevel_box(0.16, 0.11, 0.12, 0.04), f @ T(0.58, 0.66, 0), M_STONE, 1)               # 주둥이
    for sgn in (-1, 1):                                                                           # 말린 뿔
        prev = None
        for k in range(6):
            a = k * 0.85
            p = f @ V((0.46 - 0.05 * k + 0.07 * math.sin(a), 0.80 + 0.06 * k - 0.05 * (1 - math.cos(a)),
                       sgn * (0.09 + 0.05 * k)))
            if prev is not None:
                g_, m_ = tube(prev, p, 0.040 - 0.004 * k, 6)
                stones.add(g_, m_, M_STONE)
            prev = p
        stones.add(sphere(0.045, 2), f @ T(0.48, 0.79, sgn * 0.16), M_STONE)                      # 귀
    stones.add(cyl(0.05, 0.03, 0.16, 6), f @ T(-0.52, 0.52, 0, 0, 0, 1.1), M_STONE, 1)            # 꼬리


def danggan_marker(x, z, ry=0.0, h=2.0):
    """당간지주형 표석 — 화강석 기둥 두 개 + 붉은 목재 가로대, 구름무늬 기단"""
    f = T(x, 0, z, ry)
    stones.add(bevel_box(2.4, 0.3, 0.9, 0.04), f @ T(0, 0.15, 0), M_STONE, 1)
    for sgn in (-1, 1):
        stones.add(bevel_box(0.3, h, 0.42, 0.03), f @ T(sgn * 0.78, 0.3 + h / 2, 0), M_STONE, 1)
    for yy in (h * 0.45, h * 0.82):
        stones.add(box(1.86, 0.11, 0.16), f @ T(0, 0.3 + yy, 0.22), M_REDBAR, 1)


def gold_dragon_pool(x, z):
    """북동 모서리 반사 연못 위 검은 화강석 대 + 금룡 (약 4m)"""
    f = T(x, 0, z, 0.5)
    stones.add(box(7.0, 0.2, 4.2), f @ T(0, 0.1, 0), mat('poolEdge', None, (0.3, 0.3, 0.29), 0.7), 1)
    stones.add(box(6.4, 0.06, 3.6), f @ T(0, 0.19, 0), mat('poolWater', None, (0.06, 0.09, 0.1), 0.05, 0.2), 1)
    stones.add(bevel_box(2.2, 0.55, 1.1, 0.03), f @ T(0, 0.35, 0), mat('poolBlock', None, (0.09, 0.09, 0.1), 0.5), 1)
    prev = None
    for k in range(13):                                                              # 굽이치는 금룡 몸통
        t_ = k / 12
        p = f @ V((-1.9 + t_ * 3.8, 0.95 + 0.34 * math.sin(t_ * 5.0), 0.34 * math.cos(t_ * 4.2)))
        if prev is not None:
            g_, m_ = tube(prev, p, 0.11 - 0.045 * t_, 8)
            stones.add(g_, m_, M_GOLD)
        prev = p
    stones.add(sphere(0.2, 3), f @ T(-2.0, 1.05, 0.0, 0, 0, 0, 1.3, 0.9, 0.9), M_GOLD)


def _sq(bot, top, h, seg=4):
    """정사각 뿔대 (밑변 bot, 윗변 top). seg=8 이면 팔각."""
    k = math.sqrt(2) if seg == 4 else 1.0 / math.cos(PI / seg)
    return cyl(top * k / 2, bot * k / 2, h, seg)


def _roof_stone(asm, f, y, w, steps=5, rise=0.30, lip=0.07):
    """옥개석 — 밑에 층급받침 여러 단, 위에 낙수면, 네 귀퉁이 살짝 들림"""
    for k in range(steps):                                                   # 층급받침 (아래로 갈수록 좁다)
        sw = w - 0.24 + k * 0.24 / steps
        asm.add(box(sw, 0.055, sw), f @ T(0, y + 0.028 + k * 0.055, 0), M_STONE, 1)
    y0 = y + steps * 0.055
    asm.add(box(w, lip, w), f @ T(0, y0 + lip / 2, 0), M_STONE, 1)           # 처마 끝 (수평 띠)
    asm.add(_sq(w - 0.05, w * 0.42, rise), f @ T(0, y0 + lip + rise / 2, 0, PI / 4), M_STONE, 1)   # 낙수면
    for sx in (-1, 1):                                                       # 네 귀퉁이 반전 (전각)
        for sz in (-1, 1):
            asm.add(bevel_box(0.20, 0.10, 0.20, 0.03),
                    f @ T(sx * (w / 2 - 0.10), y0 + lip + 0.05, sz * (w / 2 - 0.10), 0, 0, sz * sx * 0.22), M_STONE, 1)
    return y0 + lip + rise


def _body_stone(asm, f, y, w, hh):
    """탑신 — 네 귀퉁이에 우주(모서리 기둥)를 얕게 새긴다"""
    asm.add(box(w, hh, w), f @ T(0, y + hh / 2, 0), M_STONE, 1)
    for sx in (-1, 1):
        for sz in (-1, 1):
            asm.add(box(0.10, hh - 0.04, 0.10), f @ T(sx * (w / 2 - 0.03), y + hh / 2, sz * (w / 2 - 0.03)), M_STONE, 1)
    return y + hh


def three_storey_pagoda(x, z, h=4.6):
    """삼층석탑 — 통일신라식 이중기단 + 3층 탑신·옥개석 + 상륜부.
       전에는 상자를 다섯 개 쌓고 공을 얹은 것뿐이었다 (층급받침·우주·전각이 없었다)."""
    f = T(x, 0, z)
    stones.add(box(2.30, 0.20, 2.30), f @ T(0, 0.10, 0), M_STONE, 1)                     # 지대석
    y = _body_stone(stones, f, 0.20, 1.92, 0.56)                                         # 하층기단 면석
    for sx_ in (-0.48, 0.48):                                                            # 하층기단 탱주
        stones.add(box(0.09, 0.52, 1.94), f @ T(sx_, 0.20 + 0.28, 0), M_STONE, 1)
        stones.add(box(1.94, 0.52, 0.09), f @ T(0, 0.20 + 0.28, sx_), M_STONE, 1)
    stones.add(box(2.08, 0.15, 2.08), f @ T(0, y + 0.075, 0), M_STONE, 1)                # 하층기단 갑석
    y += 0.15
    y = _body_stone(stones, f, y, 1.46, 0.72)                                            # 상층기단 면석
    stones.add(box(0.09, 0.68, 1.48), f @ T(0, y - 0.36, 0), M_STONE, 1)                 # 상층기단 탱주
    stones.add(box(1.48, 0.68, 0.09), f @ T(0, y - 0.36, 0), M_STONE, 1)
    stones.add(box(1.66, 0.14, 1.66), f @ T(0, y + 0.07, 0), M_STONE, 1)                 # 상층기단 갑석
    stones.add(_sq(1.66, 1.10, 0.12), f @ T(0, y + 0.20, 0, PI / 4), M_STONE, 1)         # 갑석 위 괴임
    y += 0.26
    for k, (bw, bh, rw) in enumerate(((0.98, 0.86, 1.60), (0.80, 0.40, 1.34), (0.66, 0.34, 1.10))):
        y = _body_stone(stones, f, y, bw, bh)                                            # 탑신
        y = _roof_stone(stones, f, y, rw, steps=5 - k, rise=0.30 - k * 0.04)             # 옥개석
    stones.add(box(0.52, 0.12, 0.52), f @ T(0, y + 0.06, 0), M_STONE, 1)                 # 노반
    stones.add(sphere(0.17, 3), f @ T(0, y + 0.20, 0, 0, 0, 0, 1, 0.7, 1), M_STONE)      # 복발
    stones.add(_sq(0.46, 0.22, 0.10, 8), f @ T(0, y + 0.33, 0), M_STONE, 1)              # 앙화
    for k in range(3):                                                                   # 보륜 세 개
        stones.add(cyl(0.17 - k * 0.02, 0.17 - k * 0.02, 0.05, 12), f @ T(0, y + 0.44 + k * 0.13, 0), M_STONE, 1)
        stones.add(cyl(0.035, 0.035, 0.13, 8), f @ T(0, y + 0.50 + k * 0.13, 0), M_STONE, 1)
    stones.add(_sq(0.34, 0.12, 0.09, 8), f @ T(0, y + 0.86, 0), M_STONE, 1)              # 보개
    stones.add(cyl(0.03, 0.03, 0.16, 8), f @ T(0, y + 0.98, 0), M_STONE, 1)
    stones.add(sphere(0.10, 3), f @ T(0, y + 1.10, 0), M_STONE)                          # 보주


def buddha_triad_stele(x, z, ry=0.0):
    """삼존불 석비 — 기단·비신·옥개석에 삼존불을 얕게 새긴다.
       전에는 판석 하나에 둥근 막대 셋을 붙인 것이었다."""
    f = T(x, 0, z, ry)
    stones.add(bevel_box(2.70, 0.24, 1.15, 0.04), f @ T(0, 0.12, 0), M_STONE, 1)                  # 지대석
    stones.add(_sq(2.36, 2.10, 0.30), f @ T(0, 0.39, 0, PI / 4), M_STONE, 1)                      # 기단 굄
    stones.add(bevel_box(2.06, 2.20, 0.42, 0.04), f @ T(0, 1.64, 0), M_STONE, 1)                  # 비신
    stones.add(bevel_box(1.78, 1.86, 0.06, 0.03), f @ T(0, 1.66, 0.22), M_STONE, 1)               # 감실 테두리 (얕게 판 면)
    for (sx_, sh, sr) in ((-0.60, 0.92, 0.19), (0.0, 1.26, 0.25), (0.60, 0.92, 0.19)):            # 삼존
        by = 0.80 + sh / 2
        stones.add(cyl(sr * 1.55, sr * 1.95, sh, 12), f @ T(sx_, by, 0.25), M_STONE, 1)           # 법의 (아래로 퍼짐)
        stones.add(sphere(sr * 0.98, 3), f @ T(sx_, 0.80 + sh + sr * 0.75, 0.25, 0, 0, 0, 1.0, 1.12, 0.9), M_STONE)   # 머리
        stones.add(sphere(sr * 0.30, 2), f @ T(sx_, 0.80 + sh + sr * 1.55, 0.25), M_STONE)        # 육계
        stones.add(cyl(sr * 1.5, sr * 1.5, 0.05, 20), f @ T(sx_, 0.80 + sh + sr * 0.75, 0.20), M_STONE, 1)   # 두광
        for s_ in (-1, 1):                                                                        # 어깨·팔
            stones.add(sphere(sr * 0.42, 2), f @ T(sx_ + s_ * sr * 1.25, 0.80 + sh - sr * 0.35, 0.27), M_STONE)
    stones.add(bevel_box(2.40, 0.16, 0.66, 0.03), f @ T(0, 2.82, 0), M_STONE, 1)                  # 옥개석 처마
    stones.add(_sq(2.40, 1.05, 0.34), f @ T(0, 3.07, 0, PI / 4, 0, 0, 1.0, 1.0, 0.30), M_STONE, 1)   # 옥개석 낙수면
    for s_ in (-1, 1):
        stones.add(bevel_box(0.18, 0.09, 0.18, 0.03), f @ T(s_ * 1.10, 2.94, 0, 0, 0, s_ * -0.25), M_STONE, 1)
    stones.add(sphere(0.12, 3), f @ T(0, 3.32, 0), M_STONE)                                       # 보주


def stone_dome(x, z, r=5.5, drum=5.4, rise=3.5, ry=0.0):
    """석불관 — 황룡원의 석굴암 재현 건물. 클라이언트 근접 사진(34.webp)에서 잰 형태다.
       난간 기둥 1.0m 를 자로 쓰면 지름 약 11m, 드럼 5.4m, 돔 3.5m, 전체 9.4m.
       드럼(세로 줄눈 + 가로 코스) / 밖으로 내민 처마 돌림띠 두 단 / 가로 코스와 방사
       줄눈이 위로 모이는 돔 / 꼭대기에 밖으로 뻗은 동틀돌 두 단 / 원형 천개석 /
       옆으로 붙은 기와지붕 통로."""
    f = T(x, 0, z, ry)
    S = mat('seokbulStone', 'granite_tile_03', (0.70, 0.665, 0.575), 0.86, normal=0.3)   # 사진의 따뜻한 크림색 석재
    SD = mat('seokbulJoint', None, (0.40, 0.40, 0.392), 0.93)   # 줄눈은 선이 아니라 그림자로 읽히게
    y0 = 0.69
    # 기단은 이미 있는 원형 광장(반경 5.5, 윗면 0.3)이다. 그 위에 낮은 굄돌만 얹는다.
    stones.add(cyl(r + 0.55, r + 0.55, 0.26, 64), f @ T(0, 0.43, 0), M['granite'], 1.5)
    # 줄눈을 도형으로 붙이면 빛을 받아 흰 선으로 번쩍인다.
    # 드럼을 세 단으로 쌓아 실제 턱에서 그림자가 지게 한다 (사진의 가로 코스).
    for k, (hh, dr) in enumerate(((drum * 0.42, 0.0), (drum * 0.34, 0.022), (drum * 0.24, 0.044))):
        base = y0 + sum(x[0] for x in ((drum * 0.42, 0), (drum * 0.34, 0), (drum * 0.24, 0))[:k])
        stones.add(cyl(r - dr, r - dr, hh, 72), f @ T(0, base + hh / 2, 0), S, 2.4)
    stones.add(cyl(r + 0.42, r + 0.42, 0.40, 72), f @ T(0, y0 + drum + 0.20, 0), S, 1.4)         # 처마 돌림띠 1단
    stones.add(cyl(r + 0.22, r + 0.14, 0.26, 72), f @ T(0, y0 + drum + 0.53, 0), S, 1.2)         # 2단

    dy = y0 + drum + 0.64

    # 정반구를 쓰면 위가 뾰족하다. 사진의 돔은 밑이 불룩하고 위로 갈수록 평평해진다.
    TCUT = 0.60                                        # 동틀돌이 앉는 자리에서 자른다 (0.86 은 윗면이 0.7m 밖에 안 나와 동틀돌이 묻혔다)

    def prof(t):
        return r * 0.99 * math.cos(t * PI / 2) ** 1.25, rise * math.sin(t * PI / 2) ** 0.62

    def dome_shell(bm):
        # 이 파일의 도형 함수는 전부 '웹 Y축이 높이' 규약이다 (lib.ring_segment 참고: (cos*r, h, sin*r)).
        # 여기만 높이를 z 에 넣어서 돔이 옆으로 누워 있었다 — 정면에서만 돔처럼 보이고
        # 뒤에서 보면 밑면 원판이 보였다. 그게 "돔 뒤편이 안 그려진다"의 정체다.
        NU, NV = 48, 16
        rows = []
        for j in range(NV + 1):
            rr, hh = prof(TCUT * j / NV)
            rows.append([bm.verts.new((rr * math.sin(2 * PI * i / NU), hh, rr * math.cos(2 * PI * i / NU)))
                         for i in range(NU)])
        for a_, b_ in zip(rows[:-1], rows[1:]):
            for i in range(NU):
                bm.faces.new((a_[i], a_[(i + 1) % NU], b_[(i + 1) % NU], b_[i]))
        bm.faces.new(rows[-1])
        bm.faces.new(rows[0])   # 밑면도 막아 닫힌 덩어리로 (열린 껍질은 스치는 각도에서 속이 뚫려 보인다)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        top = max(bm.faces, key=lambda fc: fc.calc_center_median().y)
        if top.normal.y < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces[:])

    stones.add(dome_shell, f @ T(0, dy, 0), S, 2.6)
    # 돔 줄눈도 같은 이유로 도형을 붙이지 않는다 (화강석 텍스처와 코스 턱으로 읽힌다)
    tr, th = prof(TCUT)
    ty = dy + th                                                                                 # 동틀돌이 앉는 높이
    # 천개석을 크게 덮으면 동틀돌이 그 밑에 묻혀 그냥 접시로 보인다. 사진처럼 꽃잎이 드러나게
    # 두 단을 엇갈려 놓고 그 위에 작은 원판만 얹는다.
    for tier, (nb, rad, out, up) in enumerate(((16, tr + 1.35, 2.30, 0.0), (16, tr + 0.80, 1.95, 0.72))):
        for k in range(nb):
            a_ = 2 * PI * (k + (0.5 if tier else 0.0)) / nb
            bf = f @ T((rad - out / 2) * math.sin(a_), ty + up + 0.20, (rad - out / 2) * math.cos(a_), -a_)
            stones.add(bevel_box(0.62, 0.44, out, 0.05), bf, S, 1)                               # 밖으로 뻗은 동틀돌
            stones.add(bevel_box(0.56, 0.30, 0.40, 0.05), bf @ T(0, -0.32, out / 2 - 0.20), S, 1)   # 끝의 턱
    stones.add(cyl(tr * 0.72, tr * 0.72, 0.28, 48), f @ T(0, ty + 1.24, 0), S, 1.4)              # 천개석
    stones.add(cyl(tr * 0.40, tr * 0.52, 0.22, 32), f @ T(0, ty + 1.48, 0), S, 1.2)

    # 옆으로 이어지는 기와채 — 사진(site_seokbulgwan_dome_1 / site_lawn_wide_seokbulgwan_dome_1):
    # 돔은 한쪽에만 붙어 있고, 그 옆으로 높이가 한 단씩 낮아지는 기와지붕 세 채가 이어진다.
    # 각 채는 앞에 흰 석벽이 서고(윗단에 작은 네모 돌이 줄지어 박힘) 기와지붕은 그 뒤로 물러앉는다.
    # 돔 뒤쪽 반은 이 석채 몸체가 메운다 (사진에서도 돔은 몸체 앞으로 불룩 나온 반원이다).
    ZF = 2.4                       # 석벽 앞면 (돔 앞면 r=4.6 보다 뒤 → 돔이 앞으로 튀어나온다)
    SIDE = -1                      # 신평루(11,-41) 쪽이 아니라 빈 쪽으로 뻗는다
    x0 = -(r - 0.8)                # 첫 채는 드럼에 물려서 시작
    # 높이는 사진에서 드럼 처마돌림띠(6.75)와 천개석(11.4)을 자로 재서 뽑았다:
    # 첫 채 벽 윗면 ≈ 5.1 / 처마 ≈ 6.4 / 용마루 ≈ 8.2.
    # 세 채가 순서대로 낮아지는 게 아니라 **가운데가 낮고 양옆이 높고 크다** (위성사진).
    # 깊이(D)는 사진으로 읽을 수 없어 높은 채가 더 깊어 보이는 정도로만 잡았다.
    for (L, WH, RH, D) in ((12.0, 5.0, 2.0, 8.6), (9.0, 3.4, 1.5, 6.6), (11.0, 4.7, 1.9, 8.2)):
        g = f @ T(x0 + SIDE * L / 2, 0, ZF - D / 2)
        stones.add(bevel_box(L + 0.6, 0.44, D + 0.8, 0.05), g @ T(0, 0.22, 0), M['granite'], 1.5)      # 기단
        stones.add(box(L, WH, D), g @ T(0, 0.44 + WH / 2, 0), S, 2.0)                                  # 석벽 몸체
        for k in range(int(L // 1.7)):                                                                 # 벽 윗단 네모 돌
            stones.add(bevel_box(0.56, 0.34, 0.34, 0.03),
                       g @ T(-L / 2 + 0.85 + k * 1.7, 0.44 + WH - 0.30, D / 2 + 0.06), S, 1)
        # 기와지붕은 석벽보다 뒤에서 시작해 위로 솟는다 (사진: 벽 너머로 지붕만 보인다)
        rb, rd = D / 2 - 0.9, D / 2 - 0.2                     # 지붕 몸체 중심 뒤로, 처마 깊이
        rf = g @ T(0, 0, -0.9)
        stones.add(box(L - 0.6, 0.46, D - 2.0), rf @ T(0, 0.44 + WH + 0.23, 0), M['vermilion'], 1)     # 창방
        stones.add(box(L - 0.2, 0.50, D - 1.4), rf @ T(0, 0.44 + WH + 0.71, 0), M['bracket'], 1)       # 평방
        hd_ = rd + 1.5
        cb = 0.44 + WH + 0.95                                  # 처마 밑면이 벽 윗면보다 0.95 위 (사진)
        rafters(stones, rf, L - 0.4, rd - 0.5, hd_ - 0.45, hip_under(cb, hd_, 0.78, RH))
        stones.add(hip_roof(L / 2 + 1.6, hd_, RH, ridge=0.78, lift=1.0), rf @ T(0, cb, 0), M['tileGrey'], 1.4)
        ridge(stones, rf, L * 0.74, cb + RH)
        x0 += SIDE * L
    # 돔 뒤를 메우는 몸체 — 사진에서 돔은 홀로 선 원통이 아니라 이 석채 앞으로 불룩 나온 반원이다.
    # (이게 없어서 돔 뒤쪽 반이 빈 채로 보였다)
    stones.add(bevel_box(10.0, 0.44, 9.4, 0.05), f @ T(0.9, 0.22, ZF - 8.6 / 2), M['granite'], 1.5)
    stones.add(box(9.4, 5.0, 8.6), f @ T(0.9, 0.44 + 2.5, ZF - 8.6 / 2), S, 2.0)
    for k in range(5):                                                  # 같은 벽 윗단 네모 돌
        stones.add(bevel_box(0.56, 0.34, 0.34, 0.03), f @ T(-3.0 + k * 1.7, 5.14, ZF + 0.06), S, 1)
    # 앞쪽 흰 돌난간 — 사진: 동자기둥 + 그 사이를 메운 판석. 돔 앞을 돌아 석채 앞을 따라 곧게 간다
    RB = r + 2.6
    pts = [(RB * math.sin(a), 0.30, RB * math.cos(a)) for a in
           [PI * (0.34 - 0.68 * k / 13) for k in range(14)]]
    pts += [(x0 + 1.0, 0.30, ZF + 2.6)]
    for a_, b_ in zip(pts[:-1], pts[1:]):
        ang = math.atan2(b_[0] - a_[0], b_[2] - a_[2])
        mid = ((a_[0] + b_[0]) / 2, (a_[2] + b_[2]) / 2)
        seg = math.dist((a_[0], a_[2]), (b_[0], b_[2]))
        stones.add(box(seg, 0.52, 0.14), f @ T(mid[0], 0.30 + 0.40, mid[1], -ang + PI / 2), M['balustrade'], 1)   # 판석
        stones.add(bevel_box(0.24, 0.94, 0.24, 0.03), f @ T(a_[0], 0.30 + 0.47, a_[2], -ang), M['balustrade'], 1)  # 동자기둥
    stones.add(bevel_box(0.24, 0.94, 0.24, 0.03), f @ T(pts[-1][0], 0.77, pts[-1][2]), M['balustrade'], 1)
    light(C_LIGHT, f'seokbul_{round(x)}', 'SPOT', (x, 0.8, z + r + 6.5), (x, drum + 2.5, z),
          energy=2400, color=(1.0, 0.94, 0.82), spot=0.7, blend=0.5, size=0.3)
    # 뒷면은 빛이 하나도 없어 까만 덩어리였다. 바닥에 두면 뒤를 메운 석채(윗면 5.44)에 가려서
    # 그 위 높이에서 쏜다 (베이크 때 반영된다 — 웹은 아직 베이크 전이라 실시간 조명으로 보인다)
    light(C_LIGHT, f'seokbul_back_{round(x)}', 'SPOT', (x, 8.0, z - r - 8.5), (x, drum + 2.4, z),
          energy=1400, color=(1.0, 0.92, 0.80), spot=0.9, blend=0.6, size=0.4)


# rise 2.5: 누워 있던 껍질을 세우고 나니 사진보다 훨씬 높았다. w_big 사진에서 드럼 지름 9.2m 를
# 자로 써서(72px/m) 처마돌림띠~천개석 밑을 다시 재니 약 2.4m 였다.
stone_dome(-17.0, -42.0, r=4.6, rise=2.5, ry=0.0)    # 무대 뒤편 원형 광장(중심 -17,-42 / 반경 5.5) 위,
                                           # 신평루 콘솔 부스(11,-41)와 같은 선

# 회랑에서 잔디로 나오는 포장길 (클라이언트 사진). 입구 석수는 생략 — 형태가 복잡해 뺀다.
PATH_X, PATH_W = 4.6, 3.2
for k in range(9):                                                                                # 큰 판석 포장
    for sx_ in (-1, 1):
        stones.add(bevel_box(PATH_W / 2 - 0.06, 0.10, 1.05, 0.02),
                   T(PATH_X + sx_ * PATH_W / 4, 0.17, 11.6 + k * 1.1), M['terrace'], 1.4)

lion_lantern(-9.5, 14.6)                   # 회랑 앞 (카메라 자리·포장길을 비켜 서쪽으로)
# 삼층석탑 두 기는 잔디 한가운데에 탑을 세워 둔 꼴이었고 현장 사진에 없다 → 뺀다
# 삼존불 석비도 현장 사진에 없어 뺀다
stone_ram(-16.5, 11.0, 0.6)                # 잔디 동남 모서리 화강석 보도 위
# 당간지주는 기단 계단 한복판을 막고 있었고 현장 사진에도 없다 → 뺀다
gold_dragon_pool(24.0, 16.5)               # 잔디 북동 모서리 반사 연못
stones.build()
stones_glow.build()

# 귀빈동(연수동 북동동 옥상) 테라스 — 실제 만찬 사진을 찍은 자리
camera(C_CAM, 'cam_terrace', (26.5, 14.6, 20.1), (-10.1, 23.4, -26.5), 84)   # 현장 사진에서 역산 (아이폰 광각, 위로 약 9°)
# 신평루 콘솔 부스 — 콘솔 뒤에서 무대 쪽 (소개서 18p 사진)
camera(C_CAM, 'cam_console', (SP[0] + 4.2, SP_BASE + 2.9, SP[1] - 0.8), (SP[0] - 6, 0.4, -24), 66)
# 위 44행의 삭제 목록이 apec_stage.py 의 어셈블리를 지워 버리는 사고가 한 번 있었다 (clad_tower·천막 전멸).
# 무대 쪽 덩어리가 살아 있는지 매번 확인한다.
MUST = ('ground', 'stage', 'truss', 'roof', 'stage_kit', 'tables', 'heaters', 'sign')
missing = [n for n in MUST if n not in bpy.data.objects]
if missing:
    raise SystemExit(f'apec_stage.py 의 객체가 사라졌다 (이름 충돌?): {missing}')
print('context built | stage objects ok')
