"""APEC 황룡원 만찬장 — 실제 현장 사진 기준 디테일 (배치는 반듯한 격자)

  python3 scripts/blender/bmcp.py exec scripts/blender/apec_stage.py

현장 사진에서 옮긴 것
- 테이블: 검정·남색 롱 테이블보, 흰 접시·냅킨, 와인잔
- 의자: 검정 커버 + 샴페인 골드 등받이 커버의 연회용 의자
- 무대: 흰 바닥, 파란 전면 판(로고), 좌우 계단 2개, 흰 연설대 2개
- 지붕: 회색 박공 막 + 네 모서리 트러스 타워(지붕 위로 솟음)
- 조명: 전면 트러스 위 따뜻한 워시 12개 + 아래 파란 무빙라이트 14개
- LED: 좌우 중계 화면 + 가운데 로고 + 하단 로고 띠
- 히터: 스테인리스 피라미드 히터 (가운데 불꽃 유리관, 위 피라미드 반사갓)
- 동선: 흰 사각 디딤돌 줄 + 무대 앞 동심원 패턴
- 사인월: 보라색 'APEC 경상북도' + 상단 투광등 4개
- 잔디: 강한 노란 투광

배치 좌표는 위성사진 실측 (scripts/blender/site_survey.md): 무대 앞 원형 디딤돌(MED)을 기준점으로
잔디마당 x -25~35 · z -33~17, 남동쪽은 중도타워 기단을 둘러싼 흰 원형 동선(중심 -43,-11 / 반지름 27)
"""
import importlib
import math
import random
import sys

sys.path.insert(0, '/Users/hare/Documents/큐비크스홈페이지/scripts/blender')
import lib  # noqa: E402

importlib.reload(lib)
from lib import (PI, SHOTS, HDRI, Assembly, T, bevel_box, box, camera, cloth_skirt, collection, cyl,  # noqa: E402
                 gable_skin, instance, light, material, plane, reset, ring_segment, sphere, tube, world_hdri)

import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

import gear  # noqa: E402
import props  # noqa: E402
importlib.reload(gear)
importlib.reload(props)
from lib import mesh_source  # noqa: E402

random.seed(7)
reset()
scene = bpy.context.scene
C_STATIC = collection('STATIC')      # 조명을 베이크할 정적 구조물
C_DYNAMIC = collection('DYNAMIC')    # 웹에서 실시간 재질로 그릴 것 (금속·유리·의자)
C_EMIT = collection('EMISSIVE')      # 발광체
C_LIGHT = collection('LIGHTS')
C_CAM = collection('CAMERAS')
C_RENDER_ONLY = collection('RENDER_ONLY')  # 웹에는 이미 있는 주변부
C_SRC = collection('SOURCES')        # 인스턴스 원본 (렌더 제외)
C_SRC.hide_render = True
C_SRC.hide_viewport = True

# ── 재질 ─────────────────────────────────────────────────────
M = {
    'lawn': material('lawn', 'leafy_grass', (0.62, 0.56, 0.26), 0.95),          # 11월 마른 잔디 (현장 사진)
    'paver': material('paver', None, (0.74, 0.74, 0.72), 0.6),
    'plaza': material('plaza', 'asphalt_02', (0.35, 0.36, 0.38), 0.9),
    'stageFloor': material('stageFloor', image_base=f'{SHOTS}/apec_stage_floor.png', rough=0.25, coat=0.3),
    'stageBody': material('stageBody', None, (0.035, 0.07, 0.24), 0.6),         # 남색 무대 몸통·치마
    'stairBlue': material('stairBlue', None, (0.05, 0.11, 0.38), 0.55),         # 남색 계단
    'nosing': material('nosing', None, (0.8, 0.9, 1), emit=(0.7, 0.85, 1.0), emit_strength=6),
    'fascia': material('fascia', emit_image=f'{SHOTS}/apec_real_fascia.png', emit_strength=1.3, rough=0.4),
    'led': material('led', emit_image=f'{SHOTS}/apec_real_led.png', emit_strength=3.0, rough=0.25),
    'ledFrame': material('ledFrame', None, (0.015, 0.015, 0.02), 0.5),
    'roofSkin': material('roofSkin', None, (0.88, 0.89, 0.88), 0.85),            # 흰 막지붕 (현장 사진)
    'lectern': material('lectern', None, (0.93, 0.94, 0.95), 0.3, coat=0.4),
    'lecternPanel': material('lecternPanel', None, (0.86, 0.88, 0.92), 0.12, coat=0.7),
    'roof': material('roof', None, (0.16, 0.17, 0.19), 0.55),
    'aluminium': material('aluminium', None, (0.82, 0.84, 0.86), 0.3, 1.0),
    'black': material('black', None, (0.012, 0.012, 0.015), 0.5),
    'washLens': material('washLens', None, (1, 0.9, 0.75), emit=(1.0, 0.86, 0.66), emit_strength=60),
    'blueLens': material('blueLens', None, (0.3, 0.5, 1), emit=(0.25, 0.45, 1.0), emit_strength=45),
    'tableCloth': material('tableCloth', 'cotton_jersey', (0.022, 0.026, 0.05), 0.85, normal=0.7, sheen=0.4),
    'plate': material('plate', None, (0.7, 0.7, 0.68), 0.15, coat=0.6),
    'napkin': material('napkin', 'cotton_jersey', (0.95, 0.95, 0.93), 0.9, normal=0.4),
    'glass': material('glass', None, (0.9, 0.93, 0.95), 0.03, transmission=1.0),
    'flower': material('flower', None, (0.92, 0.92, 0.95), 0.8, sheen=0.3),
    'chairBlack': material('chairBlack', 'cotton_jersey', (0.007, 0.007, 0.009), 0.75, normal=0.6, sheen=0.05),
    'chairGold': material('chairGold', 'cotton_jersey', (0.66, 0.47, 0.22), 0.28, 0.45, normal=0.25, sheen=0.6),
    'stainless': material('stainless', None, (0.8, 0.81, 0.82), 0.22, 1.0),
    'flame': material('flame', None, (1, 0.5, 0.15), emit=(1.0, 0.5, 0.15), emit_strength=70),
    'sign': material('sign', emit_image=f'{SHOTS}/apec_real_sign.png', emit_strength=0.35, rough=0.5),
    'stone': material('stone', 'rock_tile_floor_02', (0.6, 0.61, 0.62), 0.9),
    'candle': material('candle', None, (1, 0.7, 0.35), emit=(1.0, 0.62, 0.25), emit_strength=4),
    'lanternGlow': material('lanternGlow', None, (1, 0.8, 0.55), emit=(1.0, 0.75, 0.45), emit_strength=4),
}

emit = Assembly('emissive', C_EMIT)

# ── 불러온 소품 (CC BY, CREDITS.md) ────────────────────────────
SRC_PLATE = props.load('d045ad82b6fb4102b06c05eaea80961d', 'src_plate', width=0.28, decimate=0.06, coll=C_SRC, materials=M['plate'])
SRC_CUTLERY = props.load('f6efe212a8d9426481d877236a548a5a', 'src_cutlery', width=0.21, rot_x=-PI / 2, decimate=0.22, coll=C_SRC, materials=M['stainless'])
SRC_GLASS = props.load('88c1cc6d02fb49cfa35692b790134594', 'src_wineglass', height=0.2, decimate=0.3, coll=C_SRC, materials=M['glass'])
SRC_SPEAKER = props.load('f3209a6a45b844df92560099f982a508', 'src_speaker', height=1.6, coll=C_SRC)
SRC_LANTERN = props.load('4e674d91b33a450781aebd9c490b0f05', 'src_lantern', height=1.9, coll=C_SRC)
SRC_MOVER = props.load('3f838303f817454e9be539e244d039ac', 'src_mover', height=0.42, parts=[0, 5, 6, 7], coll=C_SRC)
SRC_WASH = props.load('3f838303f817454e9be539e244d039ac', 'src_wash', width=0.36, parts=[1, 2], coll=C_SRC)
PLATE_H = max(v.co.z for v in SRC_PLATE.data.vertices)
# 조명기 렌즈 재질을 발광으로 (워시: 따뜻한 흰빛, 무빙: 파랑)
for src, lens in ((SRC_WASH, M['washLens']), (SRC_MOVER, M['blueLens'])):
    for k, m in enumerate(src.data.materials):
        if m and 'Lens' in m.name:
            src.data.materials[k] = lens
glass = Assembly('glass', C_DYNAMIC)

# ── 잔디 · 디딤돌 ─────────────────────────────────────────────
ground = Assembly('ground', C_STATIC)
LAWN = (-25, 35, -33, 17)                       # x0, x1, z0, z1 (위성 실측)
TOWER_C, TOWER_R = (-43, -11), 27.5             # 중도타워 원형 동선
ground.add(box(LAWN[1] - LAWN[0], 0.12, LAWN[3] - LAWN[2]),
           T((LAWN[0] + LAWN[1]) / 2, 0.06, (LAWN[2] + LAWN[3]) / 2), M['lawn'], tile=2.5)
MED = (6, -7.6)  # 무대 앞 동심원 중심 (위성사진 기준점)


LAWN_PINES = ((22, 8, 4.6), (14.5, 14.5, 2.6))  # 잔디 위 소나무 (x, z, 비울 반지름) — apec_context.py 와 같은 값


def on_lawn(x, z, margin=0.0):
    inside = LAWN[0] + margin <= x <= LAWN[1] - margin and LAWN[2] + margin <= z <= LAWN[3] - margin
    clear = all(math.hypot(x - px, z - pz) > r + margin * 0.5 for px, pz, r in LAWN_PINES)
    return inside and clear and math.hypot(x - TOWER_C[0], z - TOWER_C[1]) > TOWER_R + margin


def paver(px, pz):
    if not on_lawn(px, pz, 0.3):
        return
    ground.add(bevel_box(0.5, 0.12, 0.5, 0.012), T(px, 0.135, pz, random.uniform(-0.02, 0.02)), M['paver'], 1.2)   # 잔디에 박힘, 윗면 0.195


# 무대 앞을 가로지르는 흰 디딤돌 두 줄
x = -24.0
while x <= 34:
    if abs(x - MED[0]) > 4.1:
        paver(x, MED[1] - 0.35)
        paver(x + 0.35, MED[1] + 0.35)
    x += 0.7
# 앞쪽으로 뻗는 동선 두 줄
z = MED[1] + 4.0
while z <= 16.5:
    paver(MED[0] - 0.35, z)
    paver(MED[0] + 0.35, z + 0.35)
    z += 0.7
# 동심원 패턴: 가운데 원판 + 끊어진 고리 세 겹
ground.add(cyl(0.9, 0.9, 0.12, 48), T(MED[0], 0.135, MED[1]), M['paver'], 1.2)
for r0, r1, count in ((1.45, 1.9, 12), (2.35, 2.75, 20), (3.15, 3.45, 28)):
    span = 2 * PI / count
    for i in range(count):
        a = i * span
        ground.add(ring_segment(r0, r1, a + span * 0.1, a + span * 0.9, 0.12), T(MED[0], 0.075, MED[1]), M['paver'], 1.2)
ground.build()

outer = Assembly('outer', C_RENDER_ONLY)
outer.add(box(160, 0.1, 140), T(0, -0.06, 0), M['plaza'], tile=4)
outer.build()

# ── 무대 ─────────────────────────────────────────────────────
CX, CZ, TOP = 6, -16, 1.2
FRONT = CZ + 4.5  # 무대 앞면 z = -11.5
stage = Assembly('stage', C_STATIC)
stage.add(bevel_box(18, TOP - 0.04, 9, 0.02), T(CX, (TOP - 0.04) / 2, CZ), M['stageBody'])
stage.add(box(18, 0.05, 9), T(CX, TOP - 0.025, CZ), M['stageFloor'], tile=None)   # 무대 상판 (윗면에 바닥 그래픽)
emit.add(plane(18, 1.1), T(CX, 0.58, FRONT + 0.07), M['fascia'], tile=None)
# 좌우 계단 (단 높이 0.3m, 앞끝에 흰 LED 라인)
STEP_W = 13.0                                                     # 앞면을 가로지르는 넓은 계단 (현장 사진)
for k in (3, 2, 1):
    h = TOP * k / 3
    zc = FRONT + 0.4 * (4 - k) - 0.2
    stage.add(box(STEP_W, h, 0.4), T(CX - 1.0, h / 2, zc), M['stairBlue'], 1)
# 무대 뒤 계단 (대기 천막 쪽, 무대 오른쪽 뒤)
BACK = CZ - 4.5
for k in (3, 2, 1):
    h = 0.3 * k
    zc = BACK - 0.35 * (4 - k) + 0.175
    stage.add(box(2.4, h, 0.35), T(CX + 6.2, h / 2, zc), M['stairBlue'], 1)
# LED월 (하단 로고 띠 포함 14.4 × 6.2 m)
stage.add(bevel_box(15.4, 5.0, 0.35, 0.02), T(CX, TOP + 2.55, CZ - 3.9), M['ledFrame'])
emit.add(plane(15.0, 4.7), T(CX, TOP + 2.55, CZ - 3.64), M['led'], tile=None)   # 15.0 x 4.7 (사진 비율 3.2:1)
stage.add(box(15.4, 0.9, 0.3), T(CX, TOP + 0.45, CZ - 3.88), M['stageBody'], 1)          # LED 아래 남색 로고 띠
for k in range(8):                                                                        # APEC · 경상북도 번갈아
    stage.add(plane(1.5, 0.46), T(CX - 6.6 + k * 1.9, TOP + 0.45, CZ - 3.72), M['sign'], tile=None)
# 흰 아크릴 연설대 2개 (gear.lectern)
for lx, lz in ((CX - 4.6, CZ + 2.2), (CX + 1.4, CZ + 1.3)):
    gear.lectern(stage, T(lx, TOP, lz), M)
# 무대 앞 양쪽 스피커 (불러온 모델)
for sx in (-4.3, 16.3):
    stage.add(mesh_source(SRC_SPEAKER), T(sx, 0.12, FRONT + 0.4), list(SRC_SPEAKER.data.materials))
stage.build()

# ── 지붕 · 트러스 타워 · 조명 ──────────────────────────────────
X0, X1, ZB, ZF = -5.2, 17.2, -21.4, -10.6
HT, HR, ZR, TOWER = 8.6, 10.8, -16, 14.2
truss = Assembly('truss', C_DYNAMIC)


def box_truss(a, b, s=0.42, chord=0.025, lace=0.011):
    d = (b - a).normalized()
    ref = V((1, 0, 0)) if abs(d.y) > 0.9 else V((0, 1, 0))
    u = d.cross(ref).normalized() * (s / 2)
    v = u.cross(d).normalized() * (s / 2)
    corners = [u + v, u - v, -u - v, -u + v]
    for k in corners:
        g, m = tube(a + k, b + k, chord, 10)
        truss.add(g, m, M['aluminium'])
    length = (b - a).length
    bays = max(1, round(length / (s * 1.4)))
    for i in range(bays):
        p0 = a + d * (length * i / bays)
        p1 = a + d * (length * (i + 1) / bays)
        for k in range(4):
            c0, c1 = corners[k], corners[(k + 1) % 4]
            s0, s1 = (c0, c1) if i % 2 else (c1, c0)
            g, m = tube(p0 + s0, p1 + s1, lace, 6)
            truss.add(g, m, M['aluminium'])
        for k in range(4):  # 가로대
            g, m = tube(p0 + corners[k], p0 + corners[(k + 1) % 4], lace, 6)
            truss.add(g, m, M['aluminium'])


# 네 모서리 타워 (지붕 위로 솟음) + 슬리브 블록 + 상부 헤드
for tx in (X0, X1):
    for tz in (ZB, ZF):
        truss.add(bevel_box(1.3, 0.1, 1.3, 0.02), T(tx, 0.17, tz), M['black'])
        box_truss(V((tx, 0.2, tz)), V((tx, TOWER, tz)), 0.52, 0.03, 0.013)
        truss.add(bevel_box(0.9, 0.7, 0.9, 0.03), T(tx, HT, tz), M['black'])
        truss.add(bevel_box(0.75, 0.35, 0.75, 0.03), T(tx, TOWER + 0.2, tz), M['black'])
# 지붕 틀
box_truss(V((X0, HT, ZF)), V((X1, HT, ZF)))
box_truss(V((X0, HT, ZB)), V((X1, HT, ZB)))
box_truss(V((X0, HT, ZB)), V((X0, HT, ZF)))
box_truss(V((X1, HT, ZB)), V((X1, HT, ZF)))
box_truss(V((X0, HR, ZR)), V((X1, HR, ZR)), 0.36)
for rx in (X0, CX, X1):
    box_truss(V((rx, HT, ZB)), V((rx, HR, ZR)), 0.3)
    box_truss(V((rx, HT, ZF)), V((rx, HR, ZR)), 0.3)

# 회색 박공 지붕 막
theta = math.atan2(HR - HT, ZR - ZB)
slope = math.hypot(HR - HT, ZR - ZB) + 0.6
roof = Assembly('roof', C_STATIC)
roof.add(gable_skin(X1 - X0 + 1.2, slope), T(CX, (HT + HR) / 2 + 0.28, (ZB + ZR) / 2, 0, -theta), M['roofSkin'], 3)
roof.add(gable_skin(X1 - X0 + 1.2, slope), T(CX, (HT + HR) / 2 + 0.28, (ZF + ZR) / 2, PI, -theta), M['roofSkin'], 3)
roof.build(smooth=True)

# 전면 트러스 조명 두 줄 (현장 사진: 위 따뜻한 워시, 아래 파란 무빙이 촘촘히 번갈아)
for i in range(18):
    lx = X0 + 1.2 + i * (X1 - X0 - 2.4) / 17
    truss.add(mesh_source(SRC_WASH), T(lx, HT + 0.21, ZF, 0, PI / 2 + 0.45), list(SRC_WASH.data.materials))   # 워시: 현장 사진처럼 객석(+z)·아래를 봄
    light(C_LIGHT, f'wash_{i}', 'SPOT', (lx, HT + 0.3, ZF + 0.25), (lx * 0.8 + CX * 0.2, 0, 6),
          energy=900, color=(1.0, 0.92, 0.8), spot=0.7, blend=0.6, size=0.12)
for i in range(20):
    lx = X0 + 0.9 + i * (X1 - X0 - 1.8) / 19
    truss.add(mesh_source(SRC_MOVER), T(lx, HT - 0.21, ZF, 0, PI), list(SRC_MOVER.data.materials))   # 무빙헤드 (거꾸로 매달림)
    light(C_LIGHT, f'mover_{i}', 'SPOT', (lx, HT - 0.75, ZF + 0.15),
          (lx + random.uniform(-2, 2), 0.1, -5 + random.uniform(-2, 3)),
          energy=700, color=(0.3, 0.5, 1.0), spot=0.28, blend=0.35, size=0.04)
truss.build(smooth=True)

# ── 백스테이지 · 설치장비 (현장 사진 assets-src/refs/apec/onsite/) ─────────────
#    트러스 타워 발치의 IBC 물탱크 밸러스트, 라인어레이 스택, 카메라 중계대, 대기실 천막.
#    정확한 평면 위치는 onsite 사진 실측(layout_v2) 나오면 다시 잡는다.
boh = Assembly('backstage', C_STATIC)
M['ibc'] = material('apIbc', None, (0.86, 0.87, 0.84), 0.35, transmission=0.25)
M['ibcCage'] = material('apIbcCage', None, (0.55, 0.56, 0.58), 0.45, 0.7)
M['ibcPallet'] = material('apIbcPallet', None, (0.45, 0.33, 0.2), 0.9)
M['speakerBox'] = material('apSpeaker', None, (0.045, 0.045, 0.05), 0.55)
M['scaffold'] = material('apScaffold', None, (0.62, 0.63, 0.6), 0.45, 0.7)
M['tentFab'] = material('apTentFab', 'cotton_jersey', (0.9, 0.9, 0.88), 0.85, normal=0.4)
M['tentAlu'] = material('apTentAlu', None, (0.72, 0.73, 0.75), 0.4, 0.8)


def ibc_tote(f):
    """1.2 × 1.0 × 1.16m IBC 물탱크 (트러스 타워 밸러스트) — 현장 사진에 네 타워 발치마다"""
    boh.add(box(1.2, 0.14, 1.0), f @ T(0, 0.07, 0), M['ibcPallet'], 1)
    boh.add(box(1.14, 1.0, 0.94), f @ T(0, 0.64, 0), M['ibc'], 1)
    for k in range(7):                                                   # 철망 케이지 가로살
        boh.add(box(1.18, 0.03, 0.98), f @ T(0, 0.18 + k * 0.155, 0), M['ibcCage'], 1)
    for sx in (-0.57, -0.19, 0.19, 0.57):
        boh.add(box(0.03, 1.0, 0.98), f @ T(sx, 0.64, 0), M['ibcCage'], 1)


def line_array(f, n=8):
    """지상 적재 라인어레이 + 서브우퍼 3통 (무대 양옆)"""
    for k in range(3):
        boh.add(box(1.25, 0.72, 0.9), f @ T(0, 0.36 + k * 0.72, 0), M['speakerBox'], 1)
    y0 = 3 * 0.72 + 0.1
    for k in range(n):                                                    # 살짝 뒤로 젖혀 쌓는다
        boh.add(box(1.1, 0.33, 0.72), f @ T(0, y0 + 0.17 + k * 0.34, 0.02 * k, 0, -0.045 * k), M['speakerBox'], 1)


def camera_tower(f, h=2.6):
    """비계 카메라 중계대: 발판 + 난간 + 위에 카메라"""
    for (sx, sz) in ((-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
        boh.add(cyl(0.024, 0.024, h, 8), f @ T(sx, h / 2, sz), M['scaffold'], 1)
        for k in range(1, 4):
            boh.add(cyl(0.02, 0.02, 1.7, 8), f @ T(sx, k * h / 4, 0, 0, 0, PI / 2), M['scaffold'], 1)
    boh.add(box(1.8, 0.06, 1.8), f @ T(0, h, 0), M['scaffold'], 1)
    for k in (0, 1):                                                      # 상부 난간 두 줄
        for (a_, b_) in (((-0.9, 0.9), (0.9, 0.9)), ((-0.9, -0.9), (-0.9, 0.9)), ((0.9, -0.9), (0.9, 0.9))):
            g, m = tube(f @ V((a_[0], h + 0.55 + k * 0.5, a_[1])), f @ V((b_[0], h + 0.55 + k * 0.5, b_[1])), 0.018, 6)
            boh.add(g, m, M['scaffold'])
    boh.add(cyl(0.03, 0.03, 1.45, 8), f @ T(0, h + 0.73, 0), M['black'], 1)     # 삼각대 기둥
    boh.add(bevel_box(0.26, 0.2, 0.55, 0.02), f @ T(0, h + 1.55, 0), M['black'], 1)
    boh.add(cyl(0.085, 0.09, 0.3, 16), f @ T(0, h + 1.57, 0.4, 0, PI / 2), M['black'], 1)


def marquee(f, w, d, eave=2.6, ridge=3.6, walls=True):
    """대기실용 대형 천막 (박공 막 + 철제 기둥). 무대 뒤쪽을 거의 덮고 있었다 (클라이언트)"""
    for sx in (-w / 2, 0, w / 2):
        for sz in (-d / 2, d / 2):
            boh.add(cyl(0.05, 0.05, eave, 10), f @ T(sx, eave / 2, sz), M['tentAlu'], 1)
    sl = math.hypot(ridge - eave, d / 2)
    for sgn in (-1, 1):
        boh.add(plane(w, sl), f @ T(0, (eave + ridge) / 2, sgn * d / 4, 0,
                PI / 2 + sgn * math.atan2(ridge - eave, d / 2)), M['tentFab'], 2)
    boh.add(plane(w, 0.28), f @ T(0, eave - 0.14, -d / 2), M['tentFab'], 1)      # 앞 처마 밸런스
    if walls:
        for sgn in (-1, 1):
            boh.add(plane(d, eave), f @ T(sgn * w / 2, eave / 2, 0, sgn * PI / 2), M['tentFab'], 2)
        boh.add(plane(w, eave), f @ T(0, eave / 2, d / 2, PI), M['tentFab'], 2)


for (tx, tz) in ((X0 + 0.9, ZB + 0.9), (X1 - 0.9, ZB + 0.9), (X0 + 0.9, ZF - 0.9), (X1 - 0.9, ZF - 0.9)):
    for sgn in (-1, 1):                                                   # 타워마다 IBC 두 통
        ibc_tote(T(tx, 0, tz + sgn * 0.75))
line_array(T(X0 + 1.2, 0, FRONT - 1.0))
line_array(T(X1 - 1.2, 0, FRONT - 1.0))
def clad_tower(f, w=3.0, d=2.6, h=3.6, lights=1, cam=True, face_graphic=True):
    """남색 천으로 감싼 비계 기둥 + 윗면 발판에 무빙라이트·중계카메라
       (현장 사진 client_cladtower_8/9/10.jpg: 무대를 보는 양옆에 하나씩, 정면에 한 대)"""
    boh.add(bevel_box(w, h, d, 0.02), f @ T(0, h / 2, 0), M['black'], 1)
    if face_graphic:                                                   # 무대 반대쪽(관객이 보는 면)에 APEC·경상북도
        boh.add(plane(w - 0.12, h - 0.5), f @ T(0, h / 2 + 0.1, d / 2 + 0.012), M['sign'], tile=None)
    boh.add(box(0.9, 2.0, 0.04), f @ T(w / 2 - 0.55, 1.0, -d / 2 - 0.022), M['black'], 1)   # 옆면 출입문
    boh.add(cyl(0.02, 0.02, 0.12, 8), f @ T(w / 2 - 0.15, 1.05, -d / 2 - 0.05, 0, PI / 2), M['scaffold'], 1)
    for (sx, sz) in ((-w / 2 + 0.12, -d / 2 + 0.12), (w / 2 - 0.12, -d / 2 + 0.12),
                     (-w / 2 + 0.12, d / 2 - 0.12), (w / 2 - 0.12, d / 2 - 0.12)):
        boh.add(cyl(0.024, 0.024, h + 1.3, 8), f @ T(sx, (h + 1.3) / 2, sz), M['scaffold'], 1)
    for k in range(12):                                                 # 윗면 그레이팅 발판
        boh.add(box(w - 0.2, 0.04, (d - 0.2) / 12 - 0.02), f @ T(0, h + 0.02, -d / 2 + 0.14 + k * (d - 0.2) / 12), M['scaffold'], 1)
    for k in (0, 1):                                                    # 상부 난간 두 줄 (무대 쪽은 비워 둔다)
        yy = h + 0.55 + k * 0.5
        for (a_, b_) in (((-w / 2, -d / 2), (w / 2, -d / 2)), ((-w / 2, -d / 2), (-w / 2, d / 2)), ((w / 2, -d / 2), (w / 2, d / 2))):
            g, m = tube(f @ V((a_[0], yy, a_[1])), f @ V((b_[0], yy, b_[1])), 0.018, 6)
            boh.add(g, m, M['scaffold'])
    if lights > 2:                                                      # 낮은 단상: 발판 위 가로 조명 바
        boh.add(box(w - 0.6, 0.08, 0.08), f @ T(0, h + 1.15, 0.25), M['scaffold'], 1)
    for k in range(lights):                                             # 무빙라이트 / 투광등
        lx = (k - (lights - 1) / 2) * (0.75 if lights <= 2 else (w - 1.2) / max(1, lights - 1))
        boh.add(bevel_box(0.3, 0.22, 0.28, 0.02), f @ T(lx, h + 0.17, 0.35), M['black'], 1)
        boh.add(bevel_box(0.26, 0.46, 0.3, 0.02), f @ T(lx, h + 0.5, 0.35, 0, 0, -0.5), M['black'], 1)
        emit.add(cyl(0.1, 0.1, 0.02, 16), f @ T(lx + 0.18, h + 0.65, 0.35, 0, PI / 2, -0.5), M['blueLens'])
    if cam:                                                             # 중계카메라 (삼각대 + 본체 + 렌즈 후드)
        boh.add(cyl(0.035, 0.035, 1.25, 8), f @ T(-0.5, h + 0.65, -0.5), M['black'], 1)
        for sgn in (-1, 1):
            g, m = tube(f @ V((-0.5, h + 0.9, -0.5)), f @ V((-0.5 + sgn * 0.35, h + 0.04, -0.5 + sgn * 0.2)), 0.016, 6)
            boh.add(g, m, M['black'])
        cf = f @ T(-0.5, h + 1.42, -0.5)
        boh.add(bevel_box(0.3, 0.26, 0.62, 0.02), cf, M['black'], 1)
        boh.add(cyl(0.1, 0.11, 0.34, 16), cf @ T(0, 0.02, 0.44, 0, PI / 2), M['black'], 1)
        boh.add(box(0.2, 0.14, 0.02), cf @ T(0.2, 0.06, -0.1, 0, 0, 0.25), M['black'], 1)


# 무대를 보는 양옆에 하나씩 + 정면(테이블 끝)에 중계카메라 단상
clad_tower(T(-8.5, 0, -5.0, -0.5))
clad_tower(T(20.5, 0, -5.0, 0.5))
# 정면(테이블 끝)에서 무대를 마주 보는 중계카메라 단상은 옆 두 기둥보다 낮고 옆으로 넓다
clad_tower(T(CX + 1.0, 0, FRONT + 21.0, PI), w=5.4, d=2.4, h=2.3, lights=4)   # 테이블 밭 뒤쪽 중앙 축
for (mx, mz, mw, md) in ((CX - 6.5, ZB - 8.5, 12.0, 9.0), (CX + 7.5, ZB - 8.0, 10.0, 8.0),
                         (CX - 14.5, ZB - 6.0, 8.0, 7.0)):
    marquee(T(mx, 0, mz), mw, md)
boh.build()

# ── 만찬 테이블 ────────────────────────────────────────────────
tables = Assembly('tables', C_STATIC)
# 가운데 동선(x≈6) 왼쪽(타워 쪽)에 엇갈린 격자, 오른쪽에 3열 — 잔디·타워 동선 안쪽만
TABLES = []
for row, tz in enumerate((-3, 2.5, 8, 13.5)):
    for tx in (-20, -14, -8, -2):
        x = tx + (3 if row % 2 else 0)
        if on_lawn(x, tz, 2.4):
            TABLES.append((x, tz))
for tz in (-3, 2.5, 8, 13.5):
    for tx in (13, 19.5, 26):
        if on_lawn(tx, tz, 2.4):
            TABLES.append((tx, tz))
print('tables', len(TABLES))


glass_spots = []


def wine_glass(base, a, r):
    """와인잔 (불러온 모델, 인스턴스)"""
    glass_spots.append(base @ T(math.sin(a) * r, 0.771, math.cos(a) * r, a))


chair_spots = []
for (tx, tz) in TABLES:
    base = T(tx, 0.12, tz)
    tables.add(cyl(0.92, 0.92, 0.03, 48), base @ T(0, 0.755, 0), M['tableCloth'], 0.6)
    tables.add(cloth_skirt(0.93, 1.0, 0.745, folds=16, depth=0.02), base @ T(0, 0.3725, 0, random.uniform(0, PI)),
               M['tableCloth'], 0.6)
    # 가운데 유리 캔들 세 개 (드론 사진의 테이블 가운데 불빛)
    for ci, (cx_, cz_, ch) in enumerate(((0, 0, 0.16), (0.13, 0.08, 0.11), (-0.12, 0.09, 0.13))):
        glass.add(cyl(0.045, 0.045, ch, 16), base @ T(cx_, 0.77 + ch / 2, cz_), M['glass'])
        emit.add(cyl(0.012, 0.018, 0.035, 8), base @ T(cx_, 0.77 + ch * 0.55, cz_), M['candle'])
    for i in range(10):
        a = i / 10 * 2 * PI + 0.16
        px, pz = math.sin(a) * 0.66, math.cos(a) * 0.66
        seat = base @ T(px, 0.771, pz, a)                                           # 로컬 +z = 바깥(손님 쪽)
        tables.add(mesh_source(SRC_PLATE), seat, M['plate'])
        tables.add(bevel_box(0.09, 0.02, 0.2, 0.008), seat @ T(0, PLATE_H + 0.01, 0), M['napkin'], 0.4)   # 접시 위 냅킨
        tables.add(mesh_source(SRC_CUTLERY), seat @ T(0.2, 0.0, 0.0), M['stainless'])       # 오른쪽 커트러리
        wine_glass(base, a + 0.13, 0.52)
        wine_glass(base, a - 0.1, 0.5)
        chair_spots.append(base @ T(math.sin(a) * 1.32, 0, math.cos(a) * 1.32, a))
tables.build(smooth=True)

# 연회 의자: 실제 의자 모델 + 바닥까지 내려오는 검은 스판 커버 + 금색 새틴 띠·리본 (banquet_chair.py)
import banquet_chair  # noqa: E402
importlib.reload(banquet_chair)
chair_src = banquet_chair.build(C_SRC, M['chairBlack'], M['chairGold'])
for i, spot in enumerate(chair_spots):
    instance(chair_src, C_DYNAMIC, f'chair_{i:03d}', spot)
for i, spot in enumerate(glass_spots):
    instance(SRC_GLASS, C_DYNAMIC, f'wineglass_{i:03d}', spot)

# ── 스테인리스 피라미드 히터 ───────────────────────────────────
# 테이블 사이 빈자리에 고르게 (동선·잔디 밖 제외)
HEATERS = []
for hz in (-6.2, -0.2, 5.3, 10.8, 15.8):
    for hx in range(-22, 34, 5):
        if not on_lawn(hx, hz, 0.8) or abs(hx - MED[0]) < 2.2:
            continue
        if min(math.hypot(hx - tx, hz - tz) for tx, tz in TABLES) < 2.7:
            continue
        if min((math.hypot(hx - a, hz - b) for a, b in HEATERS), default=99) < 5.5:
            continue
        HEATERS.append((hx, hz))
print('heaters', len(HEATERS))
heaters = Assembly('heaters', C_STATIC)
for k, (hx, hz) in enumerate(HEATERS):
    gear.pyramid_heater(heaters, T(hx, 0.12, hz, (k % 4) * PI / 8), M, glass=glass, emit=emit)
    light(C_LIGHT, f'heater_{k}', 'POINT', (hx, 1.4, hz), energy=160, color=(1.0, 0.55, 0.22), size=0.08)
    light(C_LIGHT, f'heater_{hx}_{hz}', 'POINT', (hx, 1.5, hz), energy=70, color=(1.0, 0.55, 0.25), size=0.06)
heaters.build()
glass.build(smooth=True)

# ── 보라색 사인월 + 상단 투광등 4개 ─────────────────────────────
SIGN = T(-19.0, 0.12, -1.5, 0.785)   # 드론 사진: 타워 계단 왼쪽 앞 포장면, 잔디·테라스 쪽을 봄
sign = Assembly('sign', C_STATIC)
sign.add(bevel_box(4.9, 0.3, 0.7, 0.02), SIGN @ T(0, 0.15, 0), M['black'])
sign.add(bevel_box(4.7, 3.3, 0.3, 0.02), SIGN @ T(0, 1.95, -0.02), M['black'])
sign.add(box(4.5, 3.2, 0.03), SIGN @ T(0, 1.95, 0.145), M['sign'], tile=None)   # 패널 앞면에 붙은 그래픽판
sign.add(box(4.3, 0.08, 0.08), SIGN @ T(0, 3.64, 0.05), M['black'])   # 패널 위 조명 바
for fx in (-1.5, -0.5, 0.5, 1.5):
    sign.add(bevel_box(0.4, 0.3, 0.25, 0.02), SIGN @ T(fx, 3.83, 0.05), M['black'])
    emit.add(plane(0.32, 0.22), SIGN @ T(fx, 3.83, 0.18), M['washLens'], tile=None)
    p = SIGN @ V((fx, 3.83, 0.2))
    tgt = SIGN @ V((fx * 2.5, 0, 10))
    light(C_LIGHT, f'sign_flood_{fx}', 'SPOT', tuple(p), tuple(tgt), energy=2600, color=(1.0, 0.9, 0.75),
          spot=0.9, blend=0.4, size=0.15)
sign.build()

# 석등
lanterns = Assembly('lanterns', C_STATIC)
LANTERN_FIRE = 1.9 * 0.66
for (lx, lz) in ((-18.5, 4.0), (-20.0, -18.5)):   # 드론 사진: 사인월 왼쪽, 계단 오른쪽
    base = T(lx, 0.1, lz)
    lanterns.add(mesh_source(SRC_LANTERN), base, list(SRC_LANTERN.data.materials))   # 석등 (불러온 모델)
    emit.add(box(0.2, 0.2, 0.2), base @ T(0, LANTERN_FIRE, 0), M['lanternGlow'])      # 화사석 안 불빛
lanterns.build()
emit.build()

# ── 조명 ─────────────────────────────────────────────────────
# 잔디를 노랗게 비추는 강한 투광 (사진의 나트륨빛 톤)
# 연수동 옥상(북서동 · 북동동 테라스 모서리)에서 잔디를 비추는 투광
# 잔디 투광: 연수동 옥상 가장자리에서 잔디만 비추는 좁은 스폿 (타워·지붕으로 새지 않게)
for k, (pos, tgt) in enumerate((((37.5, 17.0, -24.0), (8, 0, -22)), ((37.5, 17.0, -6.0), (4, 0, -6)),
                               ((37.5, 17.0, 10.0), (4, 0, 8)), ((10.0, 17.0, 19.5), (6, 0, -2)),
                               ((-10.0, 17.0, 19.5), (-8, 0, 0)))):
    light(C_LIGHT, f'flood_{k}', 'SPOT', pos, tgt, energy=48000, color=(1.0, 0.9, 0.52), spot=1.3, blend=0.95, size=1.5)
light(C_LIGHT, 'stage_top', 'AREA', (CX, 8.2, CZ + 1), (CX, TOP, CZ + 1), energy=1100, color=(0.85, 0.9, 1.0), size=8)
world_hdri(f'{HDRI}/moonless_golf_1k.hdr', 0.02)   # 현장 사진: 하늘이 완전히 검다

# ── 카메라 (현장 사진과 비슷한 위치) ─────────────────────────────
camera(C_CAM, 'cam_vip', (-2.2, 1.3, -0.4), (6, 4.0, -19), 50)       # 테이블에서 무대 (image36)
camera(C_CAM, 'cam_side', (26, 15.4, 22.5), (-10, 3, -15), 60)           # 좌측 상단에서 무대 (image38)
camera(C_CAM, 'cam_front', (6, 7, 24), (6, 3, -13), 42)
camera(C_CAM, 'cam_aerial', (-35, 60, 85), (8, 5, -8), 45)          # 전경 (image37)
scene.camera = bpy.data.objects['cam_side']

scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'

print('scene built:', {c.name: len(c.objects) for c in (C_STATIC, C_DYNAMIC, C_EMIT, C_LIGHT, C_CAM)})
