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
    'lawn': material('lawn', 'leafy_grass', (0.46, 0.7, 0.3), 0.95),
    'paver': material('paver', None, (0.74, 0.74, 0.72), 0.6),
    'plaza': material('plaza', 'asphalt_02', (0.35, 0.36, 0.38), 0.9),
    'stageFloor': material('stageFloor', image_base=f'{SHOTS}/apec_stage_floor.png', rough=0.25, coat=0.3),
    'stageBody': material('stageBody', None, (0.02, 0.02, 0.03), 0.6),
    'stairBlue': material('stairBlue', None, (0.04, 0.1, 0.45), 0.45),
    'nosing': material('nosing', None, (0.8, 0.9, 1), emit=(0.7, 0.85, 1.0), emit_strength=6),
    'fascia': material('fascia', emit_image=f'{SHOTS}/apec_real_fascia.png', emit_strength=1.3, rough=0.4),
    'led': material('led', emit_image=f'{SHOTS}/apec_real_led.png', emit_strength=3.0, rough=0.25),
    'ledFrame': material('ledFrame', None, (0.015, 0.015, 0.02), 0.5),
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
    'flame': material('flame', None, (1, 0.45, 0.1), emit=(1.0, 0.42, 0.1), emit_strength=35),
    'sign': material('sign', emit_image=f'{SHOTS}/apec_real_sign.png', emit_strength=0.35, rough=0.5),
    'stone': material('stone', 'rock_tile_floor_02', (0.6, 0.61, 0.62), 0.9),
    'candle': material('candle', None, (1, 0.7, 0.35), emit=(1.0, 0.62, 0.25), emit_strength=18),
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
for sx in (CX - 4.3, CX + 4.3):
    for k in (3, 2, 1):
        h = 0.3 * k
        zc = FRONT + 0.35 * (4 - k) - 0.175
        stage.add(box(3.0, h, 0.35), T(sx, h / 2, zc), M['stairBlue'], 1)
        emit.add(box(3.0, 0.07, 0.03), T(sx, h + 0.035, zc + 0.16), M['nosing'])
# 무대 뒤 계단 (대기 천막 쪽, 무대 오른쪽 뒤)
BACK = CZ - 4.5
for k in (3, 2, 1):
    h = 0.3 * k
    zc = BACK - 0.35 * (4 - k) + 0.175
    stage.add(box(2.4, h, 0.35), T(CX + 6.2, h / 2, zc), M['stairBlue'], 1)
# LED월 (하단 로고 띠 포함 14.4 × 6.2 m)
stage.add(bevel_box(14.8, 6.5, 0.35, 0.02), T(CX, TOP + 3.25, CZ - 3.9), M['ledFrame'])
emit.add(plane(14.4, 6.2), T(CX, TOP + 3.1, CZ - 3.64), M['led'], tile=None)   # 프레임 앞면(-3.725)보다 앞
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
roof.add(gable_skin(X1 - X0 + 1.2, slope), T(CX, (HT + HR) / 2 + 0.28, (ZB + ZR) / 2, 0, -theta), M['roof'], 3)
roof.add(gable_skin(X1 - X0 + 1.2, slope), T(CX, (HT + HR) / 2 + 0.28, (ZF + ZR) / 2, PI, -theta), M['roof'], 3)
roof.build(smooth=True)

# 전면 트러스 조명 두 줄: 위 워시 12개, 아래 파란 무빙라이트 14개
for i in range(12):
    lx = X0 + 1.4 + i * (X1 - X0 - 2.8) / 11
    truss.add(mesh_source(SRC_WASH), T(lx, HT + 0.21, ZF, 0, -(PI / 2 + 0.45)), list(SRC_WASH.data.materials))   # 워시: 렌즈가 무대(-z)·아래를 봄
    light(C_LIGHT, f'wash_{i}', 'SPOT', (lx, HT + 0.38, ZF + 0.2), (lx * 0.8 + CX * 0.2, TOP, CZ + 2.5),
          energy=520, color=(1.0, 0.88, 0.72), spot=0.8, blend=0.5, size=0.12)
for i in range(14):
    lx = X0 + 1.0 + i * (X1 - X0 - 2.0) / 13
    truss.add(mesh_source(SRC_MOVER), T(lx, HT - 0.21, ZF, 0, PI), list(SRC_MOVER.data.materials))   # 무빙헤드 (거꾸로 매달림)
    light(C_LIGHT, f'mover_{i}', 'SPOT', (lx, HT - 0.75, ZF + 0.15),
          (lx + random.uniform(-2, 2), 0.1, -5 + random.uniform(-2, 3)),
          energy=700, color=(0.3, 0.5, 1.0), spot=0.28, blend=0.35, size=0.04)
truss.build(smooth=True)

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
    light(C_LIGHT, f'heater_{hx}_{hz}', 'POINT', (hx, 1.5, hz), energy=70, color=(1.0, 0.55, 0.25), size=0.06)
heaters.build()
glass.build(smooth=True)

# ── 보라색 사인월 + 상단 투광등 4개 ─────────────────────────────
SIGN = T(-15.5, 0.12, -24.5, 0.55)   # 타워 기단 앞 동선 가 (드론 사진)
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
for (lx, lz) in ((-14.8, -17.5), (-15.2, -3.0), (-19.5, 8.5)):
    base = T(lx, 0.1, lz)
    lanterns.add(mesh_source(SRC_LANTERN), base, list(SRC_LANTERN.data.materials))   # 석등 (불러온 모델)
    emit.add(box(0.2, 0.2, 0.2), base @ T(0, LANTERN_FIRE, 0), M['lanternGlow'])      # 화사석 안 불빛
lanterns.build()
emit.build()

# ── 조명 ─────────────────────────────────────────────────────
# 잔디를 노랗게 비추는 강한 투광 (사진의 나트륨빛 톤)
# 연수동 옥상(북서동 · 북동동 테라스 모서리)에서 잔디를 비추는 투광
light(C_LIGHT, 'flood_left', 'AREA', (40, 19, -4), (4, 0, -2), energy=42000, color=(1.0, 0.76, 0.46), size=5)
light(C_LIGHT, 'flood_right', 'AREA', (22, 19, 17), (0, 0, 0), energy=30000, color=(1.0, 0.78, 0.5), size=5)
light(C_LIGHT, 'stage_top', 'AREA', (CX, 8.2, CZ + 1), (CX, TOP, CZ + 1), energy=1100, color=(0.85, 0.9, 1.0), size=8)
world_hdri(f'{HDRI}/moonless_golf_1k.hdr', 0.35)

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
