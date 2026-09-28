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
    'lawn': material('lawn', 'leafy_grass', (0.115, 0.215, 0.075), 0.95),     # 초록 잔디 (마른 갈색으로 잘못 깔아 뒀었다)
    # 디딤돌이 잔디보다 밝아서 하얀 덩어리로 떠 보였다. 사진에서는 잔디보다 어두운 회색 석재다.
    'paver': material('paver', 'rock_tile_floor_02', (0.56, 0.56, 0.545), 0.92, normal=0.9),   # 밝은 회색 자연석
    'plaza': material('plaza', 'asphalt_02', (0.35, 0.36, 0.38), 0.9),
    'stageFloor': material('stageFloor', image_base=f'{SHOTS}/apec_stage_floor.png', rough=0.25, coat=0.3),
    'stageBody': material('stageBody', None, (0.017, 0.026, 0.100), 0.7),             # 남색 치마 (#232A55)
    'deckCarpet': material('deckCarpet', None, (0.055, 0.115, 0.335), 0.85),          # 파란 니들펀치 갑판 (행사 사진)
    'redStrip': material('redStrip', None, (1, 0.1, 0.1), 0.4, emit=(1.0, 0.08, 0.06), emit_strength=3),
    'scafTube': material('scafTube', None, (0.6, 0.61, 0.59), 0.45, 0.7),        # 시스템 비계 파이프
    'screenWood': material('screenWood', None, (0.052, 0.030, 0.019), 0.55),    # 병풍·연설대 호두나무 (사진 확대)
    'hanjiPaper': material('hanjiPaper', image_base=f'{SHOTS}/apec_hanji.png', rough=0.88),   # 병풍 배접 한지
    'plinthRed': material('plinthRed', 'cotton_jersey', (0.32, 0.03, 0.04), 0.9),  # 붉은 천 좌대
    'stairBlue': material('stairBlue', None, (0.05, 0.11, 0.38), 0.55),         # 계단 챌판 (중청)
    'stairTread': material('stairTread', None, (0.26, 0.34, 0.62), 0.7),        # 계단 디딤판 (연청, 사진)
    'rampLogo': material('rampLogo', image_base=f'{SHOTS}/apec_ramp_logo.png', rough=0.6),   # 경사면 가운데 로고 한 벌
    'nosing': material('nosing', None, (0.8, 0.9, 1), emit=(0.7, 0.85, 1.0), emit_strength=6),
    'fascia': material('fascia', emit_image=f'{SHOTS}/apec_real_fascia.png', emit_strength=1.3, rough=0.4),
    'led': material('led', emit_image=f'{SHOTS}/apec_real_led.png', emit_strength=1.8, rough=0.25),
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
    'cladPanel': material('apCladPanel', image_base=f'{SHOTS}/apec_clad_panel.png', rough=0.72),   # 실제 사진에서 뜬 벽체 인쇄면
    'grating': material('grating', None, (0.045, 0.046, 0.05), 0.55, 0.7),   # 발판 강재 그레이팅
    'heaterMesh': material('heaterMesh', None, (0.10, 0.10, 0.105), 0.55, 0.65),   # 히터 철망 (밝은 크롬이 아니라 어두운 강선)
    'heaterBody': material('heaterBody', None, (0.84, 0.81, 0.70), 0.42),   # 히터 크림색 철판 (kakao 16)
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


# apec_context.py 가 잔디 가장자리에 세우는 석조물·카메라 단상 자리 (x, z, 반경).
# 여기를 비워 두지 않으면 원탁이 석등·석탑을 뚫고 앉는다.
SITE_OBSTACLES = [(-16.6, -1.0, 4.2), (-9.5, 14.6, 2.4), (-13.5, 15.6, 2.6), (9.5, 15.2, 2.6),
                  (-19.5, 13.0, 2.4), (-16.5, 11.0, 1.8), (-21.5, -11.0, 1.8),
                  (0.6, 15.4, 3.4), (4.6, 14.0, 2.6), (24.0, 16.5, 3.0)]   # 포장길 포함


def on_lawn(x, z, margin=0.0):
    inside = LAWN[0] + margin <= x <= LAWN[1] - margin and LAWN[2] + margin <= z <= LAWN[3] - margin
    clear = all(math.hypot(x - px, z - pz) > r + margin * 0.5 for px, pz, r in LAWN_PINES)
    free = all(math.hypot(x - ox, z - oz) > r + margin * 0.5 for ox, oz, r in SITE_OBSTACLES)
    return inside and clear and free and math.hypot(x - TOWER_C[0], z - TOWER_C[1]) > TOWER_R + margin


def paver(px, pz):
    if not on_lawn(px, pz, 0.3):
        return
    # 덩어리로 튀지 않게 얇게, 잔디에 거의 묻히는 높이로 (윗면 0.135)
    ground.add(bevel_box(0.52, 0.05, 0.52, 0.01), T(px, 0.11, pz, random.uniform(-0.05, 0.05)), M['paver'], 0.55)


# 무대 앞을 가로지르는 연석 줄과 가운데 큰 원형 석재는 실제 현장에 없다 (클라이언트 확인).
# 회랑에서 잔디로 나오는 짧은 진입 동선만 남긴다.
z = 11.0
while z <= 16.5:
    paver(MED[0] - 0.35, z)
    paver(MED[0] + 0.35, z + 0.35)
    z += 0.72
ground.build()

outer = Assembly('outer', C_RENDER_ONLY)
outer.add(box(160, 0.1, 140), T(0, -0.06, 0), M['plaza'], tile=4)
outer.build()

# ── 무대 ─────────────────────────────────────────────────────
CX, CZ, TOP = 6, -16, 0.55                      # 갑판 높이 0.55m (IBC·접이의자 두 자로 실측)
FRONT = CZ + 4.5  # 무대 앞면 z = -11.5
stage = Assembly('stage', C_STATIC)
stage.add(bevel_box(18.2, TOP - 0.04, 9, 0.02), T(CX, (TOP - 0.04) / 2, CZ), M['stageBody'])
# 치마의 APEC·경상북도 로고 띠. fascia 판이 1.1m 짜리라 갑판(0.55m) 위로 0.58m 솟아 있었고,
# 무대 위에서는 그 뒷면이 보여 글씨가 거울상으로 뒤집혀 나왔다. 치마 높이에 맞춰 눕힌다.
emit.add(plane(18.0, TOP - 0.06), T(CX, (TOP - 0.06) / 2 + 0.02, FRONT + 0.006), M['fascia'], tile=None)
emit.add(box(17.6, 0.035, 0.03), T(CX, 0.07, FRONT + 0.02), M['redStrip'])
stage.add(box(18.2, 0.05, 9), T(CX, TOP - 0.025, CZ), M['deckCarpet'], 2)         # 연회색 카펫 갑판
# 좌우 계단 (단 높이 0.3m, 앞끝에 흰 LED 라인)
def step_unit(cx_, cz_, w_, ry_=0.0):
    """3단 계단 (남색 챌판 + 연회색 카펫 디딤판, 난간 없음) — layout_v2 rear_stairs"""
    f = T(cx_, 0, cz_, ry_)
    for k in (3, 2, 1):
        h = TOP * k / 3
        zc = 0.3 * (4 - k) - 0.15
        stage.add(box(w_, h, 0.3), f @ T(0, h / 2, zc), M['stairBlue'], 1)
        stage.add(box(w_, 0.03, 0.3), f @ T(0, h + 0.015, zc), M['stairTread'], 1)


# 무대 앞 — 클라이언트 지시 그대로: 가운데가 경사면이고 그 양옆에 계단이 붙는다.
# (직전에 '계단+경사로 한 벌이 좌우에 하나씩'으로 바꾼 것은 내가 지어낸 배치다.
#  z_ramp 크롭은 무대 앞의 일부만 잘린 것이라 계단 한 짝과 경사로만 보였을 뿐이다.)
RMP_W, RMP_L, STP_W = 2.6, 1.9, 2.3     # 사진 실측: 계단 2.0 · 경사면 2.1m 남짓, 나머지는 민 치마


def _ramp(bm):
    """가운데 경사면 — 무대 앞면(z=0)에서 갑판 높이, 객석 쪽(z=RMP_L)에서 바닥"""
    import bmesh as _bm
    hw = RMP_W / 2
    vs = [bm.verts.new(p) for p in ((-hw, TOP, 0), (hw, TOP, 0), (hw, 0, RMP_L), (-hw, 0, RMP_L),
                                    (-hw, 0, 0), (hw, 0, 0))]
    bm.faces.new([vs[i] for i in (0, 1, 2, 3)])                     # 사면 (로고가 박히는 면)
    bm.faces.new([vs[i] for i in (4, 3, 2, 5)])
    bm.faces.new([vs[i] for i in (0, 4, 5, 1)])
    bm.faces.new([vs[i] for i in (0, 3, 4)])
    bm.faces.new([vs[i] for i in (1, 5, 2)])
    _bm.ops.recalc_face_normals(bm, faces=bm.faces[:])


RF = T(CX, 0, FRONT)
stage.add(_ramp, RF, M['stairBlue'], 1)
stage.add(plane(RMP_W * 0.80, RMP_W * 0.80 * 360 / 1600),
          RF @ T(0, TOP / 2 + 0.006, RMP_L / 2, 0, math.atan2(TOP, RMP_L) - PI / 2),
          M['rampLogo'], tile=None)                                 # 사면 가운데 로고 한 벌
for sgn in (-1, 1):                                                 # 경사면에 딱 붙는 계단 두 짝
    step_unit(CX + sgn * (RMP_W / 2 + STP_W / 2), FRONT + 0.45, STP_W)
for k in range(7):                                                 # 무대 앞 잔디의 검은 모니터 스피커
    stage.add(bevel_box(0.44, 0.3, 0.34, 0.02), T(CX - 7.5 + k * 2.6, 0.16, FRONT + 0.32, 0, -0.12), M['black'], 1)
# 무대 뒤 계단 — 사진은 파란 챌판 + 흰 디딤판의 줄무늬 계단이다 (앞 계단과 다르다)
M['stairWhite'] = material('stairWhite', None, (0.72, 0.73, 0.75), 0.8)


def rear_step(cx_, cz_, w_, ry_=0.0):
    f = T(cx_, 0, cz_, ry_)
    for k in (3, 2, 1):
        hh = TOP * k / 3
        zc = 0.3 * (4 - k) - 0.15
        stage.add(box(w_, hh, 0.3), f @ T(0, hh / 2, zc), M['stairBlue'], 1)
        stage.add(box(w_ + 0.03, 0.035, 0.32), f @ T(0, hh + 0.018, zc), M['stairWhite'], 1)


for (sx_, sz_, sry) in ((13.5, -21.0, PI), (1.5, -21.0, PI), (-3.5, -18.0, -PI / 2)):
    rear_step(sx_, sz_, 1.6, sry)
# LED월 (하단 로고 띠 포함 14.4 × 6.2 m)
# LED 는 갑판에 놓인 상자가 아니라, 잔디에 선 8.5m 시스템 비계 앞면에 매달린다 (layout_v2 led_wall)
LEDZ, LED_W, LED_H, LED_B = -20.2, 16.0, 5.5, 0.55
for bx in range(10):                                                                # 베이 1.8m x 10, 단높이 1.7m x 5
    px = CX - 9.0 + bx * 1.8
    for zz in (LEDZ - 0.12, LEDZ - 2.3):
        stage.add(cyl(0.024, 0.024, 8.5, 8), T(px, 4.25, zz), M['scafTube'], 1)
        if bx < 9:
            for by in range(1, 6):
                g_, m_ = tube(V((px, by * 1.7, zz)), V((px + 1.8, by * 1.7, zz)), 0.02, 6)
                stage.add(g_, m_, M['scafTube'])
    for by in range(1, 6):                                                          # 앞뒤 연결재
        g_, m_ = tube(V((px, by * 1.7, LEDZ - 0.12)), V((px, by * 1.7, LEDZ - 2.3)), 0.02, 6)
        stage.add(g_, m_, M['scafTube'])
stage.add(bevel_box(LED_W + 0.4, LED_H + 0.3, 0.3, 0.02), T(CX, LED_B + LED_H / 2, LEDZ - 0.15), M['ledFrame'])
emit.add(plane(LED_W, LED_H), T(CX, LED_B + LED_H / 2, LEDZ + 0.01), M['led'], tile=None)
# LED 뒤쪽은 검은 시스템 비계 그리드로 받친다 (무대 뒤편 사진). 전에는 앞면만 있었다.
for bx in range(10):
    px = CX - 9.0 + bx * 1.8
    for by in range(1, 6):
        for zz in (LEDZ - 2.3, LEDZ - 4.3):
            if bx < 9:
                g_, m_ = tube(V((px, by * 1.7, zz)), V((px + 1.8, by * 1.7, zz)), 0.02, 6)
                stage.add(g_, m_, M['scafTube'])
        g_, m_ = tube(V((px, by * 1.7, LEDZ - 2.3)), V((px, by * 1.7, LEDZ - 4.3)), 0.02, 6)
        stage.add(g_, m_, M['scafTube'])
    stage.add(cyl(0.024, 0.024, 8.5, 8), T(px, 4.25, LEDZ - 4.3), M['scafTube'], 1)
for by in (1, 3, 5):                                                                # 비계 작업 발판
    for k in range(9):
        stage.add(box(1.72, 0.05, 0.62), T(CX - 8.1 + k * 1.8, by * 1.7 + 0.03, LEDZ - 3.3), M['grating'], 1)
for sgn in (-1, 1):                                                                 # LED 양 끝 남색 마스킹 플랫 6 x 4.5
    # 날개 깊이가 6m 라 객석에서 보면 거대한 파란 벽처럼 보였다 (사진은 2~3m).
    stage.add(box(0.12, 4.5, 2.6), T(CX + sgn * (LED_W / 2 + 0.6), TOP + 2.25, LEDZ + 1.4), M['stageBody'], 1)

# 무대 위 (onsite_085952_003 확대): 호두나무색 창살 병풍 다섯 폭 + 그 앞 목재 연설대.
# 전에는 병풍이 무늬 없는 판 네 장, 연설대가 흰 상자, 그 옆에 붉은 상자였다.
# 붉은 좌대는 소개서에만 있고 현장 사진 어디에도 없어서 뺀다.
SCR_PW, SCR_PH = 0.42, 2.02                                               # 한 폭 폭·높이 (사람 1.75m 를 자로)


# 병풍은 뺀다 — 공연 한 대목에만 세웠던 것이고, 클라이언트가 보내 준 만찬 장면
# 사진에는 무대 뒤가 LED 뿐이다.


def podium(f, w=0.58, h=1.18, d=0.44):
    """연단 — 거의 곧은 상자에 어두운 윗판과 앞면 로고.
       사다리꼴(cyl seg=4)로 만들었더니 앞면이 기울어 로고 판이 면에 안 붙었다.
       곧은 상자로 바꿔 로고를 앞면에 정확히 붙인다."""
    stage.add(bevel_box(w, h - 0.06, d, 0.012), f @ T(0, (h - 0.06) / 2 + 0.02, 0), M['lectern'], 1)
    stage.add(bevel_box(w + 0.05, 0.055, d + 0.05, 0.012), f @ T(0, h - 0.03, 0), M['black'], 1)   # 어두운 윗판
    stage.add(bevel_box(w + 0.06, 0.04, d + 0.06, 0.01), f @ T(0, 0.02, 0), M['lectern'], 1)       # 밑동
    stage.add(plane(w * 0.74, w * 0.74 * 1152 / 1792), f @ T(0, h * 0.56, d / 2 + 0.006), M['lecternPanel'], tile=None)
    stage.add(cyl(0.007, 0.007, 0.22, 8), f @ T(-0.15, h + 0.10, 0.06, 0, -0.55), M['black'], 1)   # 구즈넥
    stage.add(cyl(0.006, 0.006, 0.14, 8), f @ T(-0.15, h + 0.21, 0.16, 0, -1.15), M['black'], 1)
    stage.add(sphere(0.014, 2), f @ T(-0.15, h + 0.25, 0.215), M['black'])


M['lecternPanel'] = material('lecternPanel', image_base=f'{SHOTS}/apec_clad_panel.png', rough=0.25, coat=0.5)
podium(T(CX + 0.6, TOP, CZ - 0.6, -0.16))
podium(T(CX - 6.4, TOP, CZ + 0.4, 0.22))
# 무대 앞 양쪽 스피커 (불러온 모델)
for sx in (-4.3, 16.3):
    stage.add(mesh_source(SRC_SPEAKER), T(sx, 0.12, FRONT + 0.4), list(SRC_SPEAKER.data.materials))
stage.build()

# ── 지붕 · 트러스 타워 · 조명 ──────────────────────────────────
X0, X1, ZB, ZF = -5.2, 17.2, -21.4, -10.6
# 클라이언트 야경 사진(kakao 15)에서 LED 높이 5.5m 를 자로 재고 원근을 보정한 값:
# 처마 7.5 · 용마루 9.8 · 네 모서리 타워 11.2 (타워가 지붕 위로 확실히 솟는다)
HT, HR, ZR, TOWER = 7.5, 9.8, -16, 11.2
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
box_truss(V((CX, HR, ZB)), V((CX, HR, ZF)), 0.36)                     # 용마루는 앞뒤(z) 방향 — 객석이 박공 끝면을 본다
for rz in (ZB, (ZB + ZF) / 2, ZF):
    box_truss(V((X0, HT, rz)), V((CX, HR, rz)), 0.3)
    box_truss(V((X1, HT, rz)), V((CX, HR, rz)), 0.3)

# 회색 박공 지붕 막
theta = math.atan2(HR - HT, CX - X0)
slope = math.hypot(HR - HT, CX - X0) + 0.6
roof = Assembly('roof', C_STATIC)
# rx 부호가 뒤집혀 있어서 막이 골짜기(V) 모양으로 꺾여 있었다. +theta 여야 가운데가 솟는다.
roof.add(gable_skin(ZF - ZB + 1.2, slope), T((X0 + CX) / 2, (HT + HR) / 2 + 0.28, (ZB + ZF) / 2, -PI / 2, theta), M['roofSkin'], 3)
roof.add(gable_skin(ZF - ZB + 1.2, slope), T((X1 + CX) / 2, (HT + HR) / 2 + 0.28, (ZB + ZF) / 2, PI / 2, theta), M['roofSkin'], 3)
roof.build(smooth=True)

# 전면 조명 (kakao 15 야경: 지붕 앞 트러스 '위'에 흰 블라인더 12 대가 올라앉고,
# 그 1.5m 아래 별도 조명 트러스에 파란 무빙 14 대와 흰 LED 바 13 개가 번갈아 매달린다)
LT = HT - 1.55
box_truss(V((X0 + 0.6, LT, ZF + 0.2)), V((X1 - 0.6, LT, ZF + 0.2)), 0.42)
for sx in (X0 + 0.6, X1 - 0.6):                                       # 지붕 트러스에 매다는 체인 호이스트
    truss.add(box(0.14, HT - LT - 0.2, 0.14), T(sx, (HT + LT) / 2, ZF + 0.2), M['black'], 1)
for i in range(12):                                                    # 블라인더 (트러스 위, 객석을 정면으로)
    lx = X0 + 1.4 + i * (X1 - X0 - 2.8) / 11
    for s_ in (-0.26, 0.26):
        truss.add(mesh_source(SRC_WASH), T(lx + s_, HT + 0.24, ZF, 0, PI / 2 + 0.30), list(SRC_WASH.data.materials))
    light(C_LIGHT, f'wash_{i}', 'SPOT', (lx, HT + 0.34, ZF + 0.25), (lx * 0.8 + CX * 0.2, 0, 8),
          energy=1100, color=(1.0, 0.94, 0.84), spot=0.75, blend=0.6, size=0.14)
for i in range(14):                                                    # 파란 무빙헤드 (조명 트러스에 거꾸로)
    lx = X0 + 1.1 + i * (X1 - X0 - 2.2) / 13
    truss.add(mesh_source(SRC_MOVER), T(lx, LT - 0.28, ZF + 0.2, 0, PI), list(SRC_MOVER.data.materials))
    light(C_LIGHT, f'mover_{i}', 'SPOT', (lx, LT - 0.82, ZF + 0.35),
          (lx + random.uniform(-2, 2), 0.1, -5 + random.uniform(-2, 3)),
          energy=700, color=(0.3, 0.5, 1.0), spot=0.28, blend=0.35, size=0.04)
for i in range(13):                                                    # 무빙 사이사이 흰 LED 바
    lx = X0 + 1.1 + (i + 0.5) * (X1 - X0 - 2.2) / 13
    truss.add(box(0.86, 0.11, 0.14), T(lx, LT - 0.34, ZF + 0.2), M['black'], 1)
    emit.add(plane(0.78, 0.07), T(lx, LT - 0.40, ZF + 0.2, 0, -PI / 2 + 0.35), M['washLens'], tile=None)
truss.build(smooth=True)

# ── 백스테이지 · 설치장비 (현장 사진 assets-src/refs/apec/onsite/) ─────────────
#    트러스 타워 발치의 IBC 물탱크 밸러스트, 라인어레이 스택, 카메라 중계대, 대기실 천막.
#    정확한 평면 위치는 onsite 사진 실측(layout_v2) 나오면 다시 잡는다.
#    주의: 이름을 'backstage' 로 두면 apec_context.py 가 자기 동명 어셈블리를 다시 만들기 위해
#    지우는 목록(그 파일 44행)에 걸려 이 덩어리 전체가 삭제된다. 반드시 다른 이름으로.
boh = Assembly('stage_kit', C_STATIC)
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


def line_array(f, n=4):
    """지상 적재 라인어레이 (onsite_085951_002 / 085952_003 실측: 서브 2통 + 모듈 4통, 전체 2.6m)
       옆에 선 사람 키 1.75m 를 자로 재면 서브 0.66m · 모듈 0.31m 였다 (전에는 5m 로 너무 높았다)"""
    for k in range(2):
        boh.add(box(1.25, 0.66, 0.92), f @ T(0, 0.33 + k * 0.66, 0), M['speakerBox'], 1)
    y0 = 2 * 0.66
    for k in range(n):                                                    # 살짝 뒤로 젖혀 쌓는다
        boh.add(box(1.14, 0.30, 0.74), f @ T(0, y0 + 0.155 + k * 0.31, 0.015 * k, 0, -0.04 * k), M['speakerBox'], 1)
    boh.add(box(1.3, 0.06, 1.0), f @ T(0, 0.03, 0), M['black'], 1)        # 밑에 까는 합판


def tripod_cam(f, h=1.45):
    """잔디에 세운 중계카메라 (삼각대 + ENG 카메라) — onsite_090013_030 에 무대 정면으로 두 대"""
    for k in range(3):
        g, m = tube(f @ V((0, h, 0)), f @ V((math.sin(k * 2.094) * 0.62, 0.02, math.cos(k * 2.094) * 0.62)), 0.019, 6)
        boh.add(g, m, M['black'])
    boh.add(cyl(0.045, 0.045, 0.5, 10), f @ T(0, h + 0.18, 0), M['black'], 1)     # 엘리베이터 컬럼
    boh.add(box(0.2, 0.09, 0.3), f @ T(0, h + 0.47, 0), M['black'], 1)            # 헤드
    cf = f @ T(0, h + 0.66, 0)
    boh.add(bevel_box(0.27, 0.26, 0.68, 0.02), cf, M['black'], 1)                 # 본체
    boh.add(cyl(0.095, 0.105, 0.36, 16), cf @ T(0, 0.02, 0.48, 0, PI / 2), M['black'], 1)   # 렌즈 후드
    boh.add(box(0.19, 0.13, 0.02), cf @ T(0.19, 0.07, -0.12, 0, 0, 0.25), M['black'], 1)    # 뷰파인더
    boh.add(box(0.1, 0.1, 0.26), cf @ T(0, 0.19, -0.2), M['black'], 1)            # 위 무선 송신기


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
    for sgn in (-1, 1):                                              # 네 모임지붕 (사각뿔)
        sl = math.hypot(ridge - eave, d / 2)
        boh.add(plane(w, sl), f @ T(0, (eave + ridge) / 2, sgn * d / 4, 0,
                PI / 2 + sgn * math.atan2(ridge - eave, d / 2)), M['tentFab'], 2)
        sl2 = math.hypot(ridge - eave, w / 2)
        boh.add(plane(d, sl2), f @ T(sgn * w / 4, (eave + ridge) / 2, 0, sgn * PI / 2,
                PI / 2 + math.atan2(ridge - eave, w / 2)), M['tentFab'], 2)
    boh.add(plane(w, 0.22), f @ T(0, eave - 0.11, -d / 2), M['tentFab'], 1)      # 처마 밸런스
    for sx in (-w / 2, w / 2):                                       # 다리마다 검은 모래주머니
        for sz in (-d / 2, d / 2):
            boh.add(sphere(0.16, 2), f @ T(sx, 0.1, sz, 0, 0, 0, 1.3, 0.6, 1.0), M['black'])
    if walls:
        for sgn in (-1, 1):
            boh.add(plane(d, eave), f @ T(sgn * w / 2, eave / 2, 0, sgn * PI / 2), M['tentFab'], 2)
        boh.add(plane(w, eave), f @ T(0, eave / 2, d / 2, PI), M['tentFab'], 2)


for (tx, tz) in ((X0 + 0.9, ZB + 0.9), (X1 - 0.9, ZB + 0.9), (X0 + 0.9, ZF - 0.9), (X1 - 0.9, ZF - 0.9)):
    for sgn in (-1, 1):                                                   # 타워마다 IBC 두 통
        ibc_tote(T(tx, 0, tz + sgn * 0.75))
line_array(T(X0 + 1.2, 0, FRONT - 1.0))
line_array(T(X1 - 1.2, 0, FRONT - 1.0))
M['cladNavy'] = material('apCladNavy', None, (0.026, 0.038, 0.125), 0.72)   # 남색 클래딩 (#2E3C6B, cladtower_8)


M['benchBlue'] = material('apBenchBlue', None, (0.024, 0.068, 0.328), 0.72)   # 코발트 청색 스커트 (#2B4A9B)
M['caseAlu'] = material('apCaseAlu', None, (0.52, 0.53, 0.55), 0.35, 0.8)


def side_tower(f, kind='tower', aim=None):
    """남색 클래딩 타워 — 클라이언트 근접 사진 기준으로 다시.

    전에는 폭 5.6 x 높이 3.6 의 납작한 벽체에 4구 블라인더 네 조를 얹어 놓았는데,
    사진의 타워는 폭보다 높은 3.0 x 4.0m 짜리 통이고, 윗면 그레이팅 발판에
    큰 무빙헤드 한 대와 검은 랙 상자 하나가 올라가 있다. 난간은 한 줄뿐이다.
    로고(APEC 위, 경상북도 아래)는 잔디 쪽 면 위쪽에 박힌다.
    """
    # kind='wall'  : 중도타워 앞 — 폭이 넓고 낮은 벽체, 위 프레임에 워시 다섯 (항공 사진)
    # kind='tower' : 잔디 동쪽 — 폭보다 높은 통, 발판에 큰 무빙헤드 한 대 + 랙 (근접 사진)
    wide = kind == 'wall'
    w, h, d = (6.0, 3.4, 2.4) if wide else (3.0, 4.0, 2.6)
    boh.add(bevel_box(w, h, d, 0.02), f @ T(0, h / 2, 0), M['cladNavy'], 1)
    boh.add(plane(w * (0.46 if wide else 0.84), w * (0.46 if wide else 0.84) * 1152 / 1792),
            f @ T(0, h * (0.58 if wide else 0.66), d / 2 + 0.009), M['cladPanel'], tile=None)
    boh.add(box(0.04, 2.0, 0.85), f @ T(w / 2 + 0.022, 1.0, -d / 2 + 0.75), M['cladNavy'], 1)      # 옆면 출입문
    boh.add(cyl(0.018, 0.018, 0.10, 8), f @ T(w / 2 + 0.05, 1.05, -d / 2 + 1.14, 0, PI / 2), M['scaffold'], 1)
    # 상부: 파라펫 없이 그레이팅 발판이 통 위에 바로 얹히고, 그 둘레에 낮은 난간 한 줄
    for k in range(10):
        boh.add(box(w - 0.06, 0.05, (d - 0.1) / 10 - 0.02), f @ T(0, h + 0.03, -d / 2 + 0.1 + k * (d - 0.1) / 10), M['grating'], 1)
    boh.add(box(w + 0.12, 0.06, 0.09), f @ T(0, h + 0.02, d / 2 + 0.03), M['scaffold'], 1)
    for (sx, sz) in ((-w / 2 + 0.08, -d / 2 + 0.08), (w / 2 - 0.08, -d / 2 + 0.08),
                     (-w / 2 + 0.08, d / 2 - 0.08), (w / 2 - 0.08, d / 2 - 0.08)):
        boh.add(cyl(0.024, 0.024, 1.05, 8), f @ T(sx, h + 0.55, sz), M['scaffold'], 1)             # 난간 기둥
    for yy in (h + 0.58, h + 1.02):
        for (a_, b_) in (((-w / 2 + 0.08, -d / 2 + 0.08), (w / 2 - 0.08, -d / 2 + 0.08)),
                         ((-w / 2 + 0.08, -d / 2 + 0.08), (-w / 2 + 0.08, d / 2 - 0.08)),
                         ((w / 2 - 0.08, -d / 2 + 0.08), (w / 2 - 0.08, d / 2 - 0.08)),
                         ((-w / 2 + 0.08, d / 2 - 0.08), (w / 2 - 0.08, d / 2 - 0.08))):
            g, m = tube(f @ V((a_[0], yy, a_[1])), f @ V((b_[0], yy, b_[1])), 0.018, 6)
            boh.add(g, m, M['scaffold'])
    tx_, ty_, tz_ = aim or (CX, 2.0, FRONT - 2.0)
    if wide:
        # 항공 사진: 벽체 위 프레임에 따뜻한 워시 다섯 대가 잔디(테이블)를 향해 늘어선다
        for yy in (h + 0.62, h + 1.12):
            g, m = tube(f @ V((-w / 2 + 0.14, yy, 0.12)), f @ V((w / 2 - 0.14, yy, 0.12)), 0.021, 6)
            boh.add(g, m, M['scaffold'])
        for k in range(5):
            lx = (k - 2) * (w - 1.5) / 4
            boh.add(mesh_source(SRC_WASH), f @ T(lx, h + 1.02, 0.22, 0, PI / 2 + 0.42), list(SRC_WASH.data.materials))
            pos = f @ V((lx, h + 0.95, 0.45))
            light(C_LIGHT, f'sidewash_{round(pos.x, 1)}_{k}', 'SPOT', pos[:], (f @ V((lx, 0.9, 9.0)))[:],
                  energy=1800, color=(1.0, 0.86, 0.66), spot=0.88, blend=0.6, size=0.24)
        return
    p = f @ V((-w * 0.22, h, -d * 0.12))                                                           # 발판 위 큰 무빙헤드 한 대
    yaw = math.atan2(-(tx_ - p.x), -(tz_ - p.z))
    g_ = T(p.x, 0, p.z, yaw)
    boh.add(bevel_box(0.46, 0.14, 0.46, 0.03), g_ @ T(0, h + 0.12, 0), M['black'], 1)              # 받침 플레이트
    boh.add(mesh_source(SRC_MOVER), g_ @ T(0, h + 0.19, 0, 0, 0, 0, 1.45, 1.45, 1.45), list(SRC_MOVER.data.materials))
    light(C_LIGHT, f'sidemover_{round(p.x, 1)}', 'SPOT', (p.x, h + 0.95, p.z), (tx_, ty_, tz_),
          energy=1600, color=(0.45, 0.6, 1.0), spot=0.20, blend=0.4, size=0.06)
    rf = f @ T(w * 0.26, h + 0.06, d * 0.10)                                                       # 그 옆 검은 랙 상자
    boh.add(bevel_box(0.56, 0.72, 0.66, 0.03), rf @ T(0, 0.36, 0), M['black'], 1)
    boh.add(box(0.58, 0.05, 0.68), rf @ T(0, 0.735, 0), M['scaffold'], 1)
    boh.add(bevel_box(0.34, 0.24, 0.30, 0.02), rf @ T(0.02, 0.88, 0), M['black'], 1)


def cam_riser(f, run=5.0, ret=1.6, d=0.9, h=1.35):
    """무대를 정면으로 보는 중계카메라 자리 — kakao 16 실측.
       단이 아니라 ㄱ자로 두른 코발트 청색 스커트(높이 1.35m)다. 그 위에 랙 케이스를
       쌓아 두고, 카메라는 단 위가 아니라 스커트 앞 잔디에 삼각대로 선다."""
    for (cx_, cz_, ww, ry_) in ((0.0, 0.0, run, 0.0), (run / 2 - d / 2, -ret / 2 - d / 2, ret, PI / 2)):
        g_ = f @ T(cx_, 0, cz_, ry_)
        boh.add(bevel_box(ww, h, d, 0.02), g_ @ T(0, h / 2, 0), M['benchBlue'], 1)
        boh.add(bevel_box(ww + 0.06, 0.05, d + 0.06, 0.01), g_ @ T(0, h + 0.02, 0), M['black'], 1)   # 상판
    for k in range(2):                                                   # 스커트 위에 쌓은 랙 케이스 2 x 2
        for j in range(2):
            cf = f @ T(-0.5 + k * 0.62, h + 0.05 + j * 0.42, -0.02)
            boh.add(bevel_box(0.58, 0.4, 0.62, 0.02), cf @ T(0, 0.2, 0), M['black'], 1)
            for s_ in (-1, 1):                                           # 알루미늄 모서리
                boh.add(box(0.03, 0.4, 0.66), cf @ T(s_ * 0.29, 0.2, 0), M['caseAlu'], 1)
            boh.add(plane(0.4, 0.2), cf @ T(0, 0.2, 0.315), M['black'], tile=None)
    for k, (ox, oz) in enumerate(((-1.55, 0.95), (-0.55, 1.15), (0.75, 1.0))):   # 스커트 앞 잔디의 삼각대 카메라 셋
        tripod_cam(f @ T(ox, 0, oz, 0.06 * (k - 1)), h=1.5)   # 로컬 +z 가 무대 쪽


# 잔디 좌우 긴 변, 건물에 붙여 하나씩 — 무대 쪽 면을 비우고 테이블 쪽에 그래픽
# 잔디 양옆에 마주 보게 한 대씩 (서쪽 중도타워 앞 / 동쪽 연수동 아케이드 앞), z 는 같게
side_tower(T(-16.6, 0, -1.0, PI / 2), kind='wall')   # 기단 계단 앞 포장 마당을 지나 그 앞쪽 (항공 사진)
side_tower(T(26.5, 0, 4.0, -PI / 2 - 0.25), kind='tower')   # 잔디 동쪽 (근접 사진의 높은 통 + 무빙헤드 한 대)
# 무대를 정면으로 보는 낮은 중계카메라 단상 — 회랑(z≈19) 열주 앞 잔디
cam_riser(T(0.6, 0, 15.4, PI), run=4.2)   # 회랑 앞, 잔디로 나가는 포장길(x 3.0~6.2) 바로 서쪽
# 무대 정면 잔디의 삼각대 카메라는 뺀다 — 만찬 사진에는 객석뿐이다 (리허설 때만 있었다)
# 대기 천막 — 무대 뒤편 사진: 무대 바로 옆(오른쪽 뒤)에 큰 흰 천막이 붙어 있고,
# 그 뒤로 작은 천막들이 이어진다. 전에는 무대 뒤에 다섯 동을 나란히 세워 놨었다.
marquee(T(X1 + 4.6, 0, ZB + 3.2), 7.2, 7.2, eave=2.6, ridge=4.1)
for k in range(3):
    marquee(T(CX - 6.2 + k * 5.4, 0, ZB - 5.0), 5.0, 5.0, eave=2.2, ridge=3.3)
for (ix, iz) in ((X1 + 1.2, ZB - 1.0), (X1 + 1.2, ZB - 2.4), (CX - 8.0, ZB - 1.2)):
    ibc_tote(T(ix, 0, iz))                                          # 비계 발치 IBC 물탱크
boh.build()

# ── 만찬 테이블 ────────────────────────────────────────────────
tables = Assembly('tables', C_STATIC)
# 가운데 동선(x≈6) 왼쪽(타워 쪽)에 엇갈린 격자, 오른쪽에 3열 — 잔디·타워 동선 안쪽만
TABLES = []
# 항공 사진: 원탁 22개가 잔디 전체가 아니라 가운데(중도타워 쪽으로 치우친 블록)에 모여 있고,
# 무대 앞과 좌우 가장자리에는 넓은 빈 잔디가 남는다. 전에는 잔디를 꽉 채워 놨었다.
FIELD_X0, FIELD_X1, FIELD_Z0, FIELD_Z1 = -12.8, 5.6, -7.5, 12.0   # 벽체(x -16.6) 앞에서 시작
jit = random.Random(11)


def place(x, z):
    if len(TABLES) >= 22:
        return
    for r in (0.0, 1.0, 1.8, 2.6):
        for k in range(12):
            a_ = k * PI / 6
            nx, nz = x + r * math.cos(a_), z + r * math.sin(a_)
            if on_lawn(nx, nz, 2.3) and all(math.hypot(nx - p, nz - q) > 3.5 for p, q in TABLES):
                TABLES.append((nx, nz))
                return


for row in range(5):                                        # 5줄 x 5열 격자를 엇갈리게, 22개까지
    tz = FIELD_Z0 + row * (FIELD_Z1 - FIELD_Z0) / 4
    for col in range(5):
        tx = FIELD_X0 + (col + (0.5 if row % 2 else 0.0)) * (FIELD_X1 - FIELD_X0) / 5
        place(tx + jit.uniform(-0.55, 0.55), tz + jit.uniform(-0.5, 0.5))
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
# 사진: 난로는 테이블 사이사이가 아니라 테이블 블록 바깥 둘레(특히 앞·좌우)로 빠져 있다.
RING = []
for k in range(9):                                          # 앞쪽(객석 뒤) 한 줄
    RING.append((FIELD_X0 - 1.2 + k * (FIELD_X1 - FIELD_X0 + 2.4) / 8, FIELD_Z1 + 2.6))
# 무대 쪽 한 줄은 두지 않는다 — 무대 앞을 가로막는다 (사진에도 무대 바로 앞엔 없다)
for k in range(6):                                          # 좌우 두 줄
    zz = FIELD_Z0 - 1.0 + k * (FIELD_Z1 - FIELD_Z0 + 2.0) / 5
    RING.append((FIELD_X0 - 3.0, zz))
    RING.append((FIELD_X1 + 3.0, zz))
for (hx, hz) in RING:
    if not on_lawn(hx, hz, 0.8):
        continue
    if min((math.hypot(hx - tx, hz - tz) for tx, tz in TABLES), default=99) < 2.4:
        continue
    if min((math.hypot(hx - a_, hz - b_) for a_, b_ in HEATERS), default=99) < 2.8:
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

# layout_v2 #13: 피라미드 히터가 주류지만 버섯형(돔) 히터도 몇 대 섞여 있었다
M['heaterCream'] = material('heaterCream', None, (0.86, 0.84, 0.78), 0.5)
extra = Assembly('extra_kit', C_STATIC)
# 여기 있던 버섯형 히터 네 대는 옛 버전이다. 현장은 오벨리스크형 한 종류뿐이고
# 그건 heaters 어셈블리(gear.pyramid_heater)가 이미 세운다 — 접시 달린 옛 것은 지운다.

# layout_v2 #15: 백스테이지 쪽에 깔린 어두운 바닥 보호 매트 (행사 당일에도 남아 있었다)
M['groundMat'] = material('groundMat', None, (0.14, 0.15, 0.13), 0.9)
for (mx0, mx1, mz0, mz1) in ((-12.0, 20.0, -26.5, -22.5), (16.0, 20.0, -22.5, -6.0), (-12.0, -8.0, -22.5, -12.0)):
    extra.add(box(mx1 - mx0, 0.03, mz1 - mz0), T((mx0 + mx1) / 2, 0.135, (mz0 + mz1) / 2), M['groundMat'], 2)

# layout_v2 #16: 잔디 한가운데 딜레이 스피커 스택
for dx in (-9.0, 21.0):
    df = T(dx, 0.12, 6.0)
    extra.add(cyl(0.05, 0.05, 3.2, 10), df @ T(0, 1.6, 0), M['scafTube'], 1)
    extra.add(box(0.9, 0.05, 0.9), df @ T(0, 0.03, 0), M['black'], 1)
    for k in range(3):
        extra.add(box(0.62, 0.3, 0.42), df @ T(0, 2.3 + k * 0.31, 0.03 * k, 0, -0.06 * k), M['speakerBox'], 1)
extra.build()

# ── 중도타워 상향 투광 스탠드 ───────────────────────────────────
# 전에는 여기에 남색 큐브 2.4 x 2.4 x 2.8 + 별도 투광 스탠드를 세웠는데, 현장 사진
# (onsite_090013_030 / _085633_027, client_cladtower_9·10) 을 보면 그 사인월이 곧
# 위 flood_wall — 폭 6.4m 가벽 + 그 위 프레임에 워시 다섯 대 — 하나였다. 큐브는 중복이라 뺀다.
# 남기는 것은 기단 발치에서 중도타워를 올려 쏘는 투광 스탠드 두 짝 (사진에 층마다 빛이 올라간다).
sign = Assembly('sign', C_STATIC)
for (sx_, sz_) in ((-20.5, -16.5), (-20.5, -5.5)):
    fst = T(sx_, 0, sz_, -PI / 2)
    for s_ in (-1, 1):
        sign.add(cyl(0.05, 0.05, 1.5, 10), fst @ T(s_ * 0.45, 0.75, 0), M['black'], 1)
        sign.add(box(0.8, 0.05, 0.45), fst @ T(s_ * 0.45, 0.03, 0), M['black'], 1)
    sign.add(box(1.15, 0.09, 0.09), fst @ T(0, 1.5, 0), M['black'], 1)
    for k in range(3):
        fx_ = -0.36 + k * 0.36
        sign.add(bevel_box(0.3, 0.26, 0.28, 0.02), fst @ T(fx_, 1.36, 0.05, 0, -0.9), M['black'], 1)
        emit.add(cyl(0.11, 0.11, 0.02, 16), fst @ T(fx_, 1.5, 0.14, 0, PI / 2 - 0.9), M['washLens'])
        pf = fst @ V((fx_, 1.5, 0.16))
        light(C_LIGHT, f'jdup_{sz_}_{k}', 'SPOT', tuple(pf), (-43.0, 26.0, sz_), energy=2400,
              color=(1.0, 0.9, 0.75), spot=0.45, blend=0.4, size=0.15)
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
