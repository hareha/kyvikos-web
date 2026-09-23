"""성수동 세원정밀 창고 — LOCAL POWER 2025 Hong Kong Fashion in Seoul (2025.9.27 쇼 · 9.28~10.11 전시)

  python3 scripts/blender/bmcp.py exec scripts/blender/localpower_scene.py

자료 (assets-src/refs/localpower/: index.md 사진 약 145장, site_layout.md/json, hall_layout.md/json, yard_layout.md/json):
- 부지: 서울 성동구 성수이로18길 20. 카카오 스카이뷰(0.125m/px)·그림자·블록 줄눈(200mm)으로 측량.
  창고 34.0 × 12.2m, 박공면이 도로(성수이로18길, 차도 6.45m)를 보고 용마루는 도로와 직각. 처마 3.7m, 용마루 5.35m(15°).
  푸른 골강판 지붕, 흰 칠 벽돌 박공, 서쪽(마당 쪽) 크림색 벽과 흰 골강판, 청록 물받이.
  서쪽 마당 25.2 × 10.5m (초록 철문 + 주황 메시, 블록 담 '20', 빨간 L자 길, 주황 가림막 4.7m + 가운데 출입문,
  홍콩 간판 포토월 4.95 × 3.24m, 판자집 앞 포토 링, 체험 존), 그 너머 흰 판자 2층집(검은 발코니).
  길 건너 S-Factory(흰 블록, 주차장), 북쪽 가로수, 콘크리트 전봇대 3개(변압기·가로등·CCTV), 동쪽 푸른 박공 창고.
- 전시장: 트러스 11개(2.78m 간격, 하현 3.7m), 시멘트 슬레이트 천장, 4-way 카세트 에어컨 4대, 흰 가벽 3.5m.
  URBAN JUNGLE 니트 8벌+실타래 탑 7개, 스카이라인 벽(백라이트 실루엣, 큐브 8개), 실 커튼 원기둥(5벌),
  양면 라이트박스(트램/농구장), 물결 커튼 섬(10벌), AI 키오스크, 하버 라이트박스, 뮤직 월(큐브 5개·원판).
  쇼 당일(9.27): 20 × 3m 런웨이, 흰 박스 벤치 3열 × 2, LED 3면(가운데 5 × 3m), 흰 조명탑 8개(무빙 4개씩).
좌표: 조사 좌표(site_layout, 왼손계)의 z 를 뒤집은 웹 좌표. 창고 중심 원점, +x 도로(박공), -z 마당(서쪽), +z 동쪽 창고.
"""
import importlib
import json
import math
import os
import random
import sys

sys.path.insert(0, '/Users/hare/Documents/큐비크스홈페이지/scripts/blender')
import lib  # noqa: E402

importlib.reload(lib)
from lib import (PI, SHOTS, Assembly, T, bevel_box, box, camera, collection, cyl, instance, light, material,  # noqa: E402
                 mesh_source, plane, reset, sphere, tube)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

import gallery  # noqa: E402
import gear  # noqa: E402
import props  # noqa: E402
importlib.reload(gallery)
importlib.reload(gear)
importlib.reload(props)
from gallery import srgb  # noqa: E402

REFS = '/Users/hare/Documents/큐비크스홈페이지/assets-src/refs/localpower'
HALL = json.load(open(f'{REFS}/hall_layout.json'))
random.seed(21)
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


def Z(z):
    """조사 좌표(왼손계) z → 웹 z"""
    return -z


HX, HZ, EAVE, RIDGE = 17.0, 6.1, 3.7, 5.35          # 벽 바깥 기준 반치수
IX, IZ = 16.7, 5.8                                   # 실내
PW_H, PW_T = 3.5, 0.12                              # 가벽


def T_(name):
    return f'{SHOTS}/lp_t_{name}.png'


M = {
    'brick': material('lpBrick', image_base=T_('brick_wall_tile'), rough=0.9),            # 흰 칠 벽돌
    'roofOut': material('lpRoofOut', image_base=T_('roof_tile'), rough=0.5),               # 푸른 골강판
    'roofIn': material('lpRoofIn', image_base=T_('interior_roof_underside'), rough=0.9),   # 시멘트 슬레이트 (그을음)
    'wallIn': material('lpWallIn', image_base=T_('interior_wall_old'), rough=0.9),         # 가벽 위로 보이는 그을린 벽
    'creamWall': material('lpCreamWall', None, srgb('#E0D9B8'), 0.85),                     # 마당 쪽 크림 벽
    'corrWhite': material('lpCorrWhite', 'corrugated_iron_02', (0.86, 0.87, 0.86), 0.6, 0.3),
    'teal': material('lpTeal', None, srgb('#3F8C8A'), 0.5, 0.4),
    'floor': material('lpFloor', image_base=T_('floor_concrete_dark'), rough=0.75),               # 그을린 낡은 콘크리트 (사진 톤)
    'steel': material('lpSteel', None, (0.32, 0.33, 0.34), 0.5, 0.6),                     # 회색 칠 앵글 트러스
    'black': material('lpBlack', None, (0.015, 0.015, 0.018), 0.5),
    'white': material('lpWhite', None, (0.86, 0.86, 0.84), 0.75),
    'partition': material('lpPartition', None, (0.9, 0.9, 0.88), 0.8),
    'plinth': material('lpPlinth', None, (0.92, 0.92, 0.9), 0.35, coat=0.4),
    'curtain': material('lpCurtain', None, (0.9, 0.9, 0.89), 0.7, sheen=0.6),
    'string': material('lpString', None, (0.95, 0.95, 0.94), 0.8),
    'silver': material('lpSilver', None, (0.8, 0.81, 0.82), 0.25, 1.0),
    'mirror': material('lpMirror', None, (0.85, 0.86, 0.88), 0.05, 1.0),
    'skin': material('lpSkin', None, (0.92, 0.92, 0.9), 0.3, coat=0.5),
    'ac': material('lpAC', None, (0.9, 0.9, 0.89), 0.5),
    'exitG': material('lpExit', None, (0.1, 0.8, 0.3), emit=(0.2, 1.0, 0.4), emit_strength=3),
    'ledStrip': material('lpLedStrip', None, (1, 1, 1), emit=(0.95, 0.97, 1.0), emit_strength=10),
    'lens': material('lpLens', None, (1, 1, 1), emit=(1.0, 0.95, 0.88), emit_strength=25),
    'street': material('lpStreet', None, (0.14, 0.145, 0.15), 0.9),
    'gutterStrip': material('lpGutterStrip', None, (0.55, 0.55, 0.53), 0.85),
    'lineW': material('lpLineW', None, (0.88, 0.88, 0.86), 0.7),
    'lineY': material('lpLineY', None, (0.9, 0.7, 0.1), 0.7),
    'yard': material('lpYard', None, srgb('#8B8272'), 0.9),
    'redPath': material('lpRedPath', None, srgb('#B5452F'), 0.8),
    'block': material('lpBlock', None, srgb('#978882'), 0.9),
    'corrGrey': material('lpCorrGrey', 'corrugated_iron_02', srgb('#8B9598'), 0.6, 0.4),
    'gateGreen': material('lpGateGreen', None, srgb('#5CC04A'), 0.5, 0.3),
    'clapboard': material('lpClapboard', image_base=T_('clapboard_siding'), rough=0.8),
    'roofLight': material('lpRoofLight', None, srgb('#D6DDD9'), 0.8),
    'nbrBlue': material('lpNbrBlue', 'corrugated_iron_02', srgb('#447C90'), 0.55, 0.4),
    'nbrGreen': material('lpNbrGreen', 'corrugated_iron_02', srgb('#3F7F6A'), 0.55, 0.4),
    'nbr': material('lpNbr', None, (0.55, 0.55, 0.54), 0.85),
    'nbrDark': material('lpNbrDark', None, (0.2, 0.2, 0.21), 0.85),
    'nbrBeige': material('lpNbrBeige', None, (0.62, 0.56, 0.45), 0.85),
    'nbrWhite': material('lpNbrWhite', None, (0.86, 0.86, 0.84), 0.8),
    'glassDark': material('lpGlassDark', None, (0.05, 0.06, 0.07), 0.15, 0.3),
    'pv': material('lpPV', None, (0.05, 0.07, 0.14), 0.2, 0.4),
    'orange': material('lpOrange', None, srgb('#E0602A'), 0.7),
    'bark': material('lpBark', 'dark_wooden_planks', (0.3, 0.26, 0.22), 0.9),
    'leaves': material('lpLeaves', image_base=f'{SHOTS}/apec_leaves.png', color=(0.62, 0.7, 0.58), rough=0.8, alpha=True),
    'wire': material('lpWire', None, (0.03, 0.03, 0.03), 0.6),
    'rope': material('lpRope', None, (0.55, 0.04, 0.05), 0.8),
    'wood': material('lpWood', 'dark_wooden_planks', (0.7, 0.5, 0.32), 0.7),
    'tent': material('tentWhite', 'cotton_jersey', (0.92, 0.92, 0.9), 0.8, normal=0.4),
    'tentBeige': material('tentBeige', 'cotton_jersey', (0.78, 0.7, 0.56), 0.8, normal=0.4),
    'alu': material('tentAlu', None, (0.8, 0.8, 0.82), 0.35, 1.0),
    'case': material('roadCase', None, (0.03, 0.03, 0.035), 0.5),
    'runwayTop': material('lpRunwayTop', None, (0.02, 0.02, 0.022), 0.1, coat=1.0),
    'bench': material('lpBench', None, (0.9, 0.9, 0.88), 0.6),
    'hazard': material('lpHazard', None, (0.9, 0.75, 0.05), 0.5),
    'slab': material('lpSlab', image_base=T_('floor_concrete'), color=srgb('#BEB9B0'), rough=0.9),          # 슬래브 콘크리트
    'asphalt': material('lpAsphalt', None, srgb('#55534F'), 0.95),                                          # 주차선 남은 아스팔트
    'drain': material('lpDrain', None, (0.18, 0.18, 0.18), 0.9),
    'paleGrey': material('lpPaleGrey', None, (0.72, 0.72, 0.7), 0.85),
    'pine': material('lpPine', 'dark_wooden_planks', (0.82, 0.68, 0.45), 0.9),                              # 생나무 팔레트
    'darkWood': material('lpDarkWood', 'dark_wooden_planks', (0.22, 0.14, 0.1), 0.6),
    'brass': material('lpBrass', None, (0.72, 0.56, 0.22), 0.3, 0.9),
    'bamboo': material('lpBamboo', image_base=f'{SHOTS}/apec_leaves.png', color=(0.4, 0.52, 0.34), rough=0.85, alpha=True),
    'rust': material('lpRust', None, srgb('#7A4A34'), 0.95),
    'corrGreen': material('lpCorrGreen', 'corrugated_iron_02', srgb('#AFBFA6'), 0.65, 0.35),                # 창고 마당쪽 연녹색 골강판
    'mesh': material('lpMesh', image_base=f'{SHOTS}/lp_t_gate.png', color=(0.42, 0.55, 0.4), rough=0.7, alpha=True),
    'bulb': material('lpBulb', None, (1, 1, 1), emit=(1.0, 0.93, 0.82), emit_strength=6),
    'bulbSoft': material('lpBulbSoft', None, (1, 1, 1), emit=(1.0, 0.94, 0.85), emit_strength=2.2),
}


def G(name, emit=0.0, alpha=False):
    p = T_(name)
    if not os.path.exists(p):
        print('texture missing:', name)
        return material(f'lpMissing_{name}', None, (0.5, 0.5, 0.5), 0.8)
    if emit:
        return material(f'lpE_{name}', emit_image=p, emit_strength=emit, rough=0.5)
    return material(f'lpG_{name}', image_base=p, rough=0.6, alpha=alpha)


# ── 의상 모델 (CC BY) + 조사된 룩 색으로 도색한 변형 ─────────────────
OUT1 = props.load('4fc7bc06a5b94568b1923268f4a6e825', 'src_out_hoodie', height=1.62, decimate=0.5, coll=C_SRC)
OUT2 = props.load('11db5ff86776413885c3f4770cea7eae', 'src_out_crop', height=1.62, decimate=0.35, coll=C_SRC)
OUT3 = props.load('3a3d8d3fc80c42baab590a63b180a65e', 'src_out_skirt', height=1.5, decimate=0.4, coll=C_SRC)
_LOOK = {}


def look_src(base, rgb):
    key = (base.name, rgb)
    if key not in _LOOK:
        o = props.retint(base, srgb(rgb), rgb[1:], sat_min=-1.0) if rgb else base      # 옷 전체를 룩 색으로 (명암 유지)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        C_SRC.objects.link(o)
        _LOOK[key] = o
    return _LOOK[key]


outfit_spots = []

shell = Assembly('shell', C_STATIC)            # 안쪽 벽·천장 (안을 보는 한 겹)
shellOut = Assembly('shellOut', C_STATIC)      # 바깥 벽·지붕 (밖을 보는 한 겹)
truss = Assembly('truss', C_STATIC)
floor = Assembly('floor', C_STATIC)
expo = Assembly('expo', C_STATIC)              # 전시 가벽·전시물
outer = Assembly('outer', C_STATIC)            # 도로·담·문·전봇대 가로등
court = Assembly('court', C_STATIC)            # 마당 가림막·소품
nbrs = Assembly('nbrs', C_STATIC)
emit = Assembly('emissive', C_EMIT)
rig = Assembly('rig', C_DYNAMIC)
leaves = Assembly('tree_leaves', C_DYNAMIC)
showday = Assembly('showday', C_DYNAMIC)       # 쇼 당일(9.27) 구성: 웹에서 런웨이 시점일 때만 보인다
showEmit = Assembly('showday_emit', C_EMIT)


def mannequin(asm, x, y, z, ry, base, rgb=None, head=True):
    """흰 추상 마네킹: 받침(은색 원판·봉) + 의상 모델(조사된 룩 색으로) + 목·두상"""
    f = T(x, y, z, ry)
    asm.add(cyl(0.26, 0.26, 0.02, 32), f @ T(0, 0.01, 0), M['silver'], 1)
    asm.add(cyl(0.012, 0.012, 0.22, 8), f @ T(0, 0.12, 0), M['silver'], 1)
    src = look_src(base, rgb)
    outfit_spots.append((src, f @ T(0, 0.015, 0)))
    if head:
        top = src.dimensions.z
        asm.add(cyl(0.045, 0.05, 0.14, 12), f @ T(0, 0.02 + top + 0.02, 0.01), M['skin'], 1)
        asm.add(sphere(0.1, 3), f @ T(0, 0.02 + top + 0.17, 0.01, 0, 0, 0, 0.85, 1.15, 0.95), M['skin'])


def member(asm, a, b, r, mat):
    g, m = tube(a, b, r, 8, caps=True)
    asm.add(g, m, mat)


def curtain_path(asm, pts2, h, y0, closed=False, amp=0.05):
    """주름진 흰 커튼 (점 사이를 촘촘히 나눠 사인 주름)"""
    def build(bm):
        P = [V((x, 0, z)) for x, z in pts2]
        if closed:
            P = P + [P[0]]
        dense = []
        for a, b in zip(P, P[1:]):
            n = max(2, int((b - a).length / 0.08))
            for i in range(n):
                dense.append(a + (b - a) * (i / n))
        dense.append(P[-1])
        cum = 0
        lows, highs = [], []
        for i, p in enumerate(dense):
            if i:
                cum += (p - dense[i - 1]).length
            t = (dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]).normalized()
            nrm = V((-t.z, 0, t.x))
            off = nrm * amp * math.sin(cum / 0.16 * PI)
            lows.append(bm.verts.new(p + off))
            highs.append(bm.verts.new(p + off + V((0, h, 0))))
        faces = [bm.faces.new((lows[i], lows[i + 1], highs[i + 1], highs[i])) for i in range(len(dense) - 1)]
        bmesh.ops.solidify(bm, geom=faces, thickness=0.02)          # 앞뒤 면이 따로 조명을 받도록 두께
    asm.add(build, T(0, y0, 0), M['curtain'], 1.5)


def slab_poly(asm, pts2, h, mat):
    def build(bm):
        bot = [bm.verts.new((x, 0, z)) for x, z in pts2]
        top = [bm.verts.new((x, h, z)) for x, z in pts2]
        bm.faces.new(list(reversed(bot)))
        bm.faces.new(top)
        n = len(pts2)
        for i in range(n):
            bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    asm.add(build, T(), mat, 1)


def panel(asm, w, h, f, gmat, back, t=0.1):
    """그래픽 판: 앞면이 곧 그래픽인 얇은 상자 (그래픽을 따로 띄우지 않아 z-fighting 없음). f 는 판 중심, 앞 = 로컬 +z"""
    asm.add(plane(w, h), f @ T(0, 0, t / 2), gmat, tile=None)
    asm.add(plane(w, h), f @ T(0, 0, -t / 2, PI), back, 2)
    asm.add(plane(t, h), f @ T(w / 2, 0, 0, PI / 2), back, 1)
    asm.add(plane(t, h), f @ T(-w / 2, 0, 0, -PI / 2), back, 1)
    asm.add(plane(w, t), f @ T(0, h / 2, 0, 0, -PI / 2), back, 1)
    asm.add(plane(w, t), f @ T(0, -h / 2, 0, 0, PI / 2), back, 1)


def catenary(asm, a, b, sag, r, mat, seg=12):
    pts = [a.lerp(b, i / seg) - V((0, sag * 4 * (i / seg) * (1 - i / seg), 0)) for i in range(seg + 1)]
    for p, q in zip(pts, pts[1:]):
        g, m = tube(p, q, r, 6)
        asm.add(g, m, mat)
    return pts


def tree(px, pz, s=1.0, y0=0.0):
    rnd = random.Random(int(px * 31 + pz * 17))
    top = V((px + rnd.uniform(-0.3, 0.3), y0 + 3.0 * s, pz + rnd.uniform(-0.3, 0.3)))
    g, m = tube(V((px, y0 - 0.1, pz)), top, 0.22 * s, 10, caps=True)
    outer.add(g, m, M['bark'], 0.8)
    crown_r, crown_h = rnd.uniform(2.6, 3.4) * s, rnd.uniform(3.6, 4.6) * s
    center = top + V((0, crown_h * 0.55, 0))
    for b in range(5):
        a = b / 5 * 2 * PI + rnd.uniform(-0.3, 0.3)
        tip = center + V((math.cos(a) * crown_r * 0.55, rnd.uniform(-0.4, 0.8) * s, math.sin(a) * crown_r * 0.55))
        g, m = tube(top, tip, 0.1 * s, 8, caps=True)
        outer.add(g, m, M['bark'], 0.8)
    for _ in range(int(26 * s)):
        u, v = rnd.uniform(0, 2 * PI), rnd.uniform(-0.55, 1.0)
        rr = rnd.uniform(0.7, 1.0)
        c = center + V((math.cos(u) * math.sqrt(1 - v * v) * crown_r * rr, v * crown_h * 0.5,
                        math.sin(u) * math.sqrt(1 - v * v) * crown_r * rr))
        size = rnd.uniform(1.8, 2.6) * s
        for _k in range(3):
            leaves.add(plane(size, size), T(c.x, c.y, c.z, rnd.uniform(0, 2 * PI), rnd.uniform(-1.2, 1.2), rnd.uniform(-0.6, 0.6)),
                       M['leaves'], tile=None)


def align_long_axis(obj):
    """모델의 긴 축(평면 주성분)을 Blender X 로 돌리고 바닥 중심을 원점에"""
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    p = co.reshape(-1, 3)
    xy = p[:, :2] - p[:, :2].mean(0)
    cxx, cyy, cxy = (xy[:, 0] ** 2).mean(), (xy[:, 1] ** 2).mean(), (xy[:, 0] * xy[:, 1]).mean()
    ang = 0.5 * math.atan2(2 * cxy, cxx - cyy)
    c_, s_ = math.cos(-ang), math.sin(-ang)
    x2 = p[:, 0] * c_ - p[:, 1] * s_
    y2 = p[:, 0] * s_ + p[:, 1] * c_
    p[:, 0] = x2 - (x2.min() + x2.max()) / 2
    p[:, 1] = y2 - (y2.min() + y2.max()) / 2
    p[:, 2] -= p[:, 2].min()
    me.vertices.foreach_set('co', p.ravel())
    me.update()
    return obj

expoEmit = Assembly('expo_emit', C_EMIT)       # 전시 발광 (쇼 당일 시점에서는 숨김)
BYID = {o['id']: o for o in HALL['objects']}
DEG = PI / 180


def wz(p):
    """조사 좌표 (x, z) → 웹 (x, z)"""
    return (p[0], Z(p[1]))


# ── 창고 외피 (바깥: 밖을 봄) ─────────────────────────────────────
O = 0.3
theta = math.atan2(RIDGE - EAVE, HZ)
sn, cs = math.sin(theta), math.cos(theta)


def gable_tri(asm, x, facing, mat, y0=EAVE, y1=RIDGE, zh=HZ, tile=1.5):
    def build(bm):
        vs = [bm.verts.new(p) for p in ((0, y0, -zh), (0, y0, zh), (0, y1, 0))]
        f = bm.faces.new(vs if facing < 0 else list(reversed(vs)))
    asm.add(build, T(x, 0, 0), mat, tile)


# 도로 쪽 박공 (흰 칠 벽돌) · 뒤 박공 · 동쪽 벽 (벽돌)
shellOut.add(plane(2 * HZ, EAVE), T(HX, EAVE / 2, 0, PI / 2), M['brick'], 1.5)
gable_tri(shellOut, HX, 1, M['brick'])
shellOut.add(plane(2 * HZ, EAVE), T(-HX, EAVE / 2, 0, -PI / 2), M['brick'], 1.5)
gable_tri(shellOut, -HX, -1, M['brick'])
shellOut.add(plane(2 * HX, EAVE), T(0, EAVE / 2, HZ), M['brick'], 1.5)
# 마당 쪽 벽 (-z): 연녹색 골강판 (파묘 2024 사진), 미닫이 방문객 문
DX0, DX1, DH = 5.5, 7.4, 2.4                                  # 가림막 출입 모듈(5.0~7.9) 과 맞춘 마당 문
for (a_, b_, mat) in ((-HX, -9.0, M['corrGreen']), (-9.0, -3.0, M['corrGreen']), (-3.0, DX0, M['corrGreen']),
                      (DX1, 9.5, M['corrGreen']), (9.5, 14.5, M['corrGreen']), (14.5, HX, M['corrGreen'])):
    shellOut.add(plane(b_ - a_, EAVE), T((a_ + b_) / 2, EAVE / 2, -HZ, PI), mat, 1.5)
shellOut.add(plane(DX1 - DX0, EAVE - DH), T((DX0 + DX1) / 2, (EAVE + DH) / 2, -HZ, PI), M['corrGreen'], 1.5)
# 문 (진회색 철문, 열린 한 짝)
outer.add(box(1.05, DH, 0.05), T(DX0 + 0.5, DH / 2, -HZ - 0.55, PI / 2 + 0.3), M['steel'], 1)
for x_ in (DX0 - 0.03, DX1 + 0.03):
    outer.add(box(0.06, DH + 0.06, 0.34), T(x_, (DH + 0.06) / 2, -HZ - 0.02 + 0.15), M['steel'], 1)
# 지붕: 푸른 골강판 (처마 0.35m, 박공 0.15m 내밈), 물받이·용마루
TH = 0.06
for s in (-1, 1):
    n_, u_ = V((0, cs, s * sn)), V((0, -sn, s * cs))
    t0 = -(TH) * sn / cs
    t1 = (HZ + 0.35) / cs
    c_ = V((0, RIDGE, 0)) + n_ * (TH / 2 + 0.01) + u_ * ((t0 + t1) / 2)
    shellOut.add(box(2 * HX + 0.3, TH, t1 - t0), T(0, c_.y, c_.z, 0, s * theta), M['roofOut'], 1.0)
    ez = s * (HZ + 0.35)
    ey = RIDGE - (HZ + 0.35) * math.tan(theta)
    outer.add(box(2 * HX + 0.3, 0.14, 0.14), T(0, ey - 0.05, ez + s * 0.07), M['teal'], 1)         # 청록 물받이
    for x_ in (-12.0, 4.0, 15.5):                                                               # 선홈통
        outer.add(cyl(0.05, 0.05, ey - 0.1, 10), T(x_, (ey - 0.1) / 2, ez + s * 0.05), M['teal'], 1)
shellOut.add(box(2 * HX + 0.3, 0.12, 0.4), T(0, RIDGE + 0.08, 0), M['roofOut'], 1)
for x_ in (-6.0, 6.0):                                                                          # 지붕 환기구
    shellOut.add(cyl(0.18, 0.22, 0.35, 16), T(x_, RIDGE - 0.35, 1.3), M['steel'], 1)
    shellOut.add(cyl(0.3, 0.3, 0.05, 16), T(x_, RIDGE - 0.15, 1.3), M['steel'], 1)
# 박공 환기창 · 도로 쪽 모서리 벽돌 기둥 (붉은 벽돌 머리)
outer.add(box(0.1, 0.6, 0.45), T(HX + 0.02, 4.3, 0), M['black'], 1)
outer.add(box(0.6, 4.5, 0.6), T(16.85, 2.25, Z(5.95)), M['brick'], 1.5)
outer.add(box(0.7, 0.12, 0.7), T(16.85, 4.56, Z(5.95)), material('lpRedBrick', None, (0.45, 0.16, 0.1), 0.9), 1)

# ── 창고 내부 (안: 안을 봄, 뒷면 제거) ──────────────────────────────
shell.add(plane(2 * IZ, EAVE), T(-IX, EAVE / 2, 0, PI / 2), M['wallIn'], 2)
gable_tri(shell, -IX, 1, M['wallIn'], zh=IZ, y1=RIDGE - 0.1)
shell.add(plane(2 * IZ, EAVE), T(IX, EAVE / 2, 0, -PI / 2), M['creamWall'], 2)                 # 도로 쪽 끝벽: 크림 칠
gable_tri(shell, IX, -1, M['creamWall'], zh=IZ, y1=RIDGE - 0.1)
shell.add(box(0.05, 0.9, 1.3), T(IX - 0.02, 3.75, Z(-1.0)), M['glassDark'], 1)                   # 높은 창
shell.add(plane(2 * IX, EAVE), T(0, EAVE / 2, IZ, PI), M['wallIn'], 2)
for (a_, b_) in ((-IX, DX0), (DX1, IX)):
    shell.add(plane(b_ - a_, EAVE), T((a_ + b_) / 2, EAVE / 2, -IZ), M['wallIn'], 2)
shell.add(plane(DX1 - DX0, EAVE - DH), T((DX0 + DX1) / 2, (EAVE + DH) / 2, -IZ), M['wallIn'], 2)
th_i = math.atan2(RIDGE - 0.1 - EAVE, IZ)
sl_i = math.hypot(RIDGE - 0.1 - EAVE, IZ)
for s in (-1, 1):                                                          # 천장 슬레이트 (아래를 봄)
    shell.add(plane(2 * IX, sl_i), T(0, (EAVE + RIDGE - 0.1) / 2, s * IZ / 2, 0, PI / 2 + s * th_i), M['roofIn'], 2)
for v in ('roof_vent_0', 'roof_vent_1'):                                    # 둥근 환기 구멍 (검은 테)
    c = BYID.get(v)
    if c:
        cx, cy, cz = c['geometry']['cylinder']['center']
        yy = RIDGE - 0.1 - abs(Z(cz)) * math.tan(th_i) - 0.03
        shell.add(cyl(0.3, 0.3, 0.02, 24), T(cx, yy, Z(cz), 0, -math.copysign(th_i, Z(cz))), M['black'], 1)

# ── 트러스 11개 (앵글 프랫 트러스, 하현 3.7) + 중도리·연결재·트랙 레일 ─────────────
BOT, APEX = 3.7, 5.2


def angle_member(a, b, w=0.07):
    d = b - a
    L = d.length
    if L < 1e-3:
        return
    m = (a + b) / 2
    ry = math.atan2(-d.z, d.x) if abs(d.x) + abs(d.z) > 1e-6 else 0.0
    rz = math.atan2(d.y, math.hypot(d.x, d.z))
    truss.add(box(L, w, w * 0.6), T(m.x, m.y, m.z, ry, 0, rz), M['steel'], 1)


top_y = lambda z: APEX - (APEX - BOT) * abs(z) / IZ  # noqa: E731
TRX = [o['geometry']['plane_x'] for o in HALL['objects'] if o['type'] == 'truss']
for x in TRX:
    angle_member(V((x, BOT, -IZ)), V((x, BOT, IZ)))
    angle_member(V((x, BOT, -IZ)), V((x, APEX, 0)))
    angle_member(V((x, BOT, IZ)), V((x, APEX, 0)))
    for i in range(1, 12):
        z = -IZ + i * 2 * IZ / 12
        angle_member(V((x, BOT, z)), V((x, top_y(z), z)), 0.05)
        if i < 12:
            z1 = -IZ + (i + 1) * 2 * IZ / 12 if z < 0 else -IZ + (i - 1) * 2 * IZ / 12
            if z < -0.1:
                angle_member(V((x, BOT, z)), V((x, top_y(z - 2 * IZ / 12), z - 2 * IZ / 12)), 0.04)
            elif z > 0.1:
                angle_member(V((x, BOT, z)), V((x, top_y(z + 2 * IZ / 12), z + 2 * IZ / 12)), 0.04)
for zz in (-5.5, -4.4, -3.3, -2.2, -1.1, 0.0, 1.1, 2.2, 3.3, 4.4, 5.5):                     # 중도리 (윗현 위)
    angle_member(V((-IX, top_y(zz) + 0.06, zz)), V((IX, top_y(zz) + 0.06, zz)), 0.06)
for zz in (-4.2, -1.5, 1.5, 4.2):                                                            # 하현 높이 연결재
    angle_member(V((-IX, BOT - 0.02, zz)), V((IX, BOT - 0.02, zz)), 0.05)
for i in range(len(TRX) - 1):                                                                 # 평면 가새
    angle_member(V((TRX[i], BOT - 0.03, -4.2)), V((TRX[i + 1], BOT - 0.03, 4.2)), 0.035)
for o in HALL['objects']:
    if o['type'] == 'track_light_rail':
        (xa, za), (xb, zb) = o['geometry']['polyline']
        a, b = V((xa, BOT - 0.1, Z(za))), V((xb, BOT - 0.1, Z(zb)))
        g, m = tube(a, b, 0.02, 6)
        rig.add(g, m, M['black'])
        n = int((b - a).length / 1.1)
        for k in range(n + 1):
            p = a.lerp(b, k / n)
            rig.add(cyl(0.045, 0.045, 0.16, 12), T(p.x, p.y - 0.12, p.z, 0, 0.5 * (1 if p.z < 0 else -1)), M['black'])
            expoEmit.add(cyl(0.03, 0.03, 0.005, 10), T(p.x, p.y - 0.2, p.z + (0.04 if p.z < 0 else -0.04)), M['lens'])
    elif o['type'] == 'cassette_ac':
        cx, cy, cz = o['geometry']['box']['center']
        truss.add(box(0.84, 0.25, 0.84), T(cx, cy + 0.02, Z(cz)), M['ac'], 1)
        truss.add(box(0.95, 0.03, 0.95), T(cx, cy - 0.12, Z(cz)), M['ac'], 1)
        truss.add(box(0.5, 0.005, 0.5), T(cx, cy - 0.137, Z(cz)), M['steel'], 1)
        for (hx, hz) in ((-0.35, -0.35), (0.35, -0.35), (-0.35, 0.35), (0.35, 0.35)):        # 지붕 밑까지 올린 행거
            zz = Z(cz) + hz
            member(truss, V((cx + hx, cy + 0.14, zz)), V((cx + hx, RIDGE - 0.1 - abs(zz) * math.tan(th_i) - 0.02, zz)), 0.008, M['steel'])
    elif o['type'] == 'speaker':
        cx, cy, cz = o['geometry']['box']['center']
        rig.add(bevel_box(0.3, 0.5, 0.3, 0.02), T(cx, cy, Z(cz)), M['black'])
    elif o['type'] == 'exit_sign':
        cx, cy, cz = o['geometry']['box']['center']
        expoEmit.add(box(0.06, 0.2, 0.4), T(cx, cy, Z(cz), PI / 2), M['exitG'])

# ── 바닥: 낡은 콘크리트 + 강재 테두리 트렌치 2줄 + 팔각 피트 테두리 ───────────────
floor.add(box(2 * IX, 0.2, 2 * IZ), T(0, -0.1, 0), M['floor'], 2.5)
for zz in (Z(-3.0), Z(2.0)):
    for s in (-1, 1):
        floor.add(box(2 * IX - 0.4, 0.03, 0.04), T(0, 0.015, zz + s * 0.15), M['steel'], 1)
pit = [(4.0, 1.9), (4.4, 1.5), (8.1, 1.5), (8.5, 1.9), (8.5, 4.1), (8.1, 4.5), (4.4, 4.5), (4.0, 4.1)]
for a, b in zip(pit, pit[1:] + pit[:1]):
    fr = T((a[0] + b[0]) / 2, 0.015, (a[1] + b[1]) / 2, math.atan2(-(b[1] - a[1]), b[0] - a[0]))
    floor.add(box(math.dist(a, b), 0.03, 0.05), fr, M['steel'], 1)

# ── 전시 가벽 (흰 3.5m) ───────────────────────────────────────────
for o in HALL['objects']:
    if o['type'] != 'partition':
        continue
    (xa, za), (xb, zb) = o['geometry']['segment']
    gallery.wall(expo, (xa, Z(za)), (xb, Z(zb)), PW_H, PW_T, M['partition'])
# 도로 쪽 끝 흰 드레이프 커튼 (파이프에 건 주름)
(xa, za), (xb, zb) = BYID['curtain_endA']['geometry']['segment']
curtain_path(expo, [(xa, Z(za)), (xb, Z(zb))], 2.95, 0.0, amp=0.06)
g, m = tube(V((xa, 3.0, Z(za))), V((xb, 3.0, Z(zb))), 0.02, 8)
rig.add(g, m, M['silver'])
# 입구 쪽 안내 데스크 (entry area)
expo.add(box(1.6, 0.95, 0.55), T(14.6, 0.475, Z(4.4)), M['white'], 1)

# ── URBAN JUNGLE: 긴 흰 좌대 + 실타래 탑 7 + 니트 8벌 + 코너 화면 ──────────────────
p_ = BYID['UJ_plinth']['geometry']['box']
expo.add(box(*p_['size']), T(p_['center'][0], p_['center'][1], Z(p_['center'][2])), M['plinth'], 1)
emit.add(box(p_['size'][0], 0.015, 0.015), T(p_['center'][0], 0.25, Z(p_['center'][2]) - 0.45), M['ledStrip'])
UJ_COL = {1: '#E050A0', 2: '#8A8A8A', 3: '#E07A20', 4: '#303030', 5: '#D8C8A8', 6: '#2848C0', 7: '#E8E0C8', 8: '#4070C0'}
UJ_BASE = {1: OUT3, 2: OUT3, 3: OUT1, 4: OUT1, 5: OUT3, 6: OUT3, 7: OUT2, 8: OUT1}
for o in HALL['objects']:
    if o['id'].startswith('UJ_tower'):
        c = o['geometry']['cylinder']['center']
        x, z = c[0], Z(c[2])
        y = 0.25
        k = 0
        while y < 0.25 + 1.75:
            r = 0.13 if k % 2 else 0.18
            h = 0.28 if k % 2 else 0.22
            expo.add(cyl(r, r * 1.05, h, 20), T(x, y + h / 2, z), M['white'] if k % 2 else M['string'], 1)
            y += h
            k += 1
        g, m = tube(V((x, y, z)), V((x, 0.25 + 1.9 + 0.25, z)), 0.01, 6)
        expo.add(g, m, M['white'])
    elif o['id'].startswith('UJ_look_'):
        c = o['geometry']['cylinder']['center']
        k = int(o['id'].rsplit('_', 1)[1])
        mannequin(expo, c[0], 0.25, Z(c[2]), PI, UJ_BASE[k], UJ_COL[k])
sc = BYID['screen_UJ']['geometry']['box']
fsc = T(sc['center'][0], sc['center'][1], Z(sc['center'][2]), PI)
expo.add(box(1.96, 1.16, 0.06), fsc @ T(0, 0, -0.03), M['white'], 1)
expoEmit.add(plane(1.9, 1.1), fsc @ T(0, 0, 0.06), G('urbanjungle_screen', 1.2), tile=None)

# ── 스카이라인 벽: 백라이트 홍콩 스카이라인 실루엣 + 흰 큐브 8 + 룩 8 + 거울 로고 ─────────────
(xa, za), (xb, zb) = BYID['skyline_cutout']['geometry']['segment']
cx_, cz_ = (xa + xb) / 2, Z((za + zb) / 2)
Lc = abs(xa - xb)
expoEmit.add(plane(Lc, 1.9), T(cx_, 1.55, cz_ + 0.03), G('skyline_mask', 1.6), tile=None)                   # 벽에 번지는 LED 빛
expo.add(plane(Lc, 1.9), T(cx_, 1.55, cz_ + 0.1), material('lpSkylineCut', image_base=T_('skyline_cut'), rough=0.7, alpha=True), tile=None)
SKY_COL = ['#6FB08A', '#2C3E6E', '#A8D8C0', '#C8A850', '#2A2A2A', '#E8E0D0', '#1A1A1A', '#EEE8D8']
SKY_BASE = [OUT3, OUT1, OUT3, OUT2, OUT1, OUT3, OUT3, OUT2]
for k in range(8):
    b_ = BYID[f'SKY_cube_{k + 1}']['geometry']['box']
    x, y, z = b_['center'][0], b_['size'][1], Z(b_['center'][2])
    expo.add(box(*b_['size']), T(x, y / 2, z), M['plinth'], 1)
    mannequin(expo, x, y, z, 0.0, SKY_BASE[k], SKY_COL[k])
ml = BYID['mirror_logo']['geometry']['box']
gallery.slab_art(expo, T(ml['center'][0], ml['center'][1], Z(ml['center'][2]) + 0.08), 0.65, 0.6, 0.08, G('mirror_logo'), M['mirror'])
for o in HALL['objects']:
    if o['type'] == 'info_stand':
        c = o['geometry']['box']['center']
        f = T(c[0], 0, Z(c[2]))
        expo.add(cyl(0.18, 0.18, 0.02, 20), f @ T(0, 0.01, 0), M['white'], 1)
        expo.add(cyl(0.02, 0.02, 1.2, 8), f @ T(0, 0.6, 0), M['white'], 1)
        expo.add(box(0.45, 0.65, 0.02), f @ T(0, 1.25, 0), M['white'], 1)

# ── 실 커튼 원기둥 섬 (지름 2.9 좌대, 1.4 커튼, 룩 5벌 바깥 향) ─────────────────
cp = BYID['COL_plinth']['geometry']['cylinder']
ccx, ccz = cp['center'][0], Z(cp['center'][2])
expo.add(cyl(1.45, 1.45, 0.3, 64), T(ccx, 0.15, ccz), M['plinth'], 1)
emit.add(cyl(1.47, 1.47, 0.03, 64), T(ccx, 0.27, ccz), M['ledStrip'])
ring = [(ccx + 0.7 * math.cos(i / 40 * 2 * PI), ccz + 0.7 * math.sin(i / 40 * 2 * PI)) for i in range(40)]
curtain_path(expo, ring, 3.4, 0.3, closed=True, amp=0.02)
expo.add(cyl(0.74, 0.74, 0.05, 40), T(ccx, 3.72, ccz), M['white'], 1)
COL_LOOKS = [(180, '#556B4A', OUT1), (125, '#D07030', OUT3), (55, '#8A4A2A', OUT3), (305, '#E8A0B0', OUT2), (235, '#6A88A8', OUT1)]
for ang, col, base in COL_LOOKS:
    a = ang * DEG
    x, z = ccx + 1.05 * math.cos(a), ccz - 1.05 * math.sin(a)
    mannequin(expo, x, 0.3, z, math.atan2(math.cos(a), -math.sin(a)), base, col)

# ── 양면 라이트박스 (End B 쪽 = 트램, 입구 쪽 = 농구장) ────────────────────────
lb = BYID['LB_tram_basketball']['geometry']['box']
lf = T(lb['center'][0], 0, Z(lb['center'][2]), -lb['rot_y_deg'] * DEG)
expo.add(box(2.0, 0.12, 0.5), lf @ T(0, 0.06, 0), M['white'], 1)
expo.add(box(0.2, 2.44, 1.8), lf @ T(0, 0.12 + 1.22, 0), M['white'], 1)
expoEmit.add(plane(1.7, 2.3), lf @ T(-0.16, 1.34, 0, -PI / 2), G('lightbox_tram', 1.3), tile=None)
expoEmit.add(plane(1.7, 2.3), lf @ T(0.16, 1.34, 0, PI / 2), G('lightbox_basketball', 1.3), tile=None)
# 하버 라이트박스·AI 키오스크 (동쪽 가벽 앞)
hb = BYID['LB_harbour']['geometry']['box']
hf = T(hb['center'][0], 0, Z(hb['center'][2]), PI)
expo.add(box(1.9, 0.25, 0.35), hf @ T(0, 0.125, 0), M['white'], 1)
expo.add(box(1.8, 2.1, 0.25), hf @ T(0, 0.25 + 1.05, 0), M['white'], 1)
expoEmit.add(plane(1.7, 2.0), hf @ T(0, 1.3, 0.19), G('lightbox_harbour', 1.3), tile=None)
kb = BYID['AI_kiosk']['geometry']['box']
kf = T(kb['center'][0], 0, Z(kb['center'][2]), PI)
expo.add(bevel_box(0.6, 0.75, 0.5, 0.02), kf @ T(0, 0.375, 0), M['white'], 1)
expo.add(box(0.7, 1.0, 0.12), kf @ T(0, 1.25, -0.1), M['white'], 1)
expoEmit.add(plane(0.62, 0.92), kf @ T(0, 1.25, -0.039), G('ai_kiosk_front', 1.0), tile=None)
expoEmit.add(box(0.72, 0.02, 0.02), kf @ T(0, 1.76, -0.04), M['ledStrip'])

# ── 물결 커튼 섬 (S자 좌대 + 흰 보일 커튼 + 앞뒤 5벌씩) ─────────────────────
sp = [wz(p) for p in BYID['SER_plinth']['geometry']['polyline']]
slab_poly(expo, sp, 0.2, M['plinth'])
for a, b in zip(sp, sp[1:] + sp[:1]):
    emit.add(box(math.dist(a, b), 0.012, 0.012), T((a[0] + b[0]) / 2, 0.2, (a[1] + b[1]) / 2, math.atan2(-(b[1] - a[1]), b[0] - a[0])), M['ledStrip'])
sc_ = [wz(p) for p in BYID['SER_curtain']['geometry']['polyline']]
curtain_path(expo, sc_, 3.35, 0.2, amp=0.05)
g, m = tube(V((sc_[0][0], 3.55, sc_[0][1])), V((sc_[-1][0], 3.55, sc_[-1][1])), 0.015, 6)
rig.add(g, m, M['silver'])
FRONT = [('#2A8A8A', OUT3), ('#B02020', OUT1), ('#1A1A1A', OUT1), ('#B08050', OUT3), ('#8A8A5A', OUT3)]
BACK = [('#E0A0B8', OUT3), ('#E8E0C8', OUT1), ('#202020', OUT1), ('#C8A060', OUT3), ('#252525', OUT2)]
for i, x in enumerate((-1.4, -2.6, -3.9, -5.1, -6.3)):
    zc = min(sc_, key=lambda p: abs(p[0] - x))[1]
    mannequin(expo, x, 0.2, zc - 0.7, PI, FRONT[i][1], FRONT[i][0])
    mannequin(expo, x - 0.3, 0.2, zc + 0.7, 0.0, BACK[i][1], BACK[i][0])
expo.add(box(0.6, 1.6, 0.05), T(-0.4, 0.8, Z(-3.3), 0.3), M['white'], 1)                      # FASHION SUMMIT 안내판

# ── 화면 (흰 테 액자 TV) ─────────────────────────────────────────
for (x, zlay, slug, face) in ((-8.5, 3.95, 'screen_1', 0.0), (-13.0, 3.95, 'screen_2', 0.0), (0.3, -5.55, 'screen_3', PI)):
    zw = Z(zlay) + (PW_T / 2 + 0.03) * (1 if face == 0.0 else -1)
    f = T(x, 1.55, zw, face)
    expo.add(box(1.7, 1.05, 0.06), f, M['white'], 1)
    expoEmit.add(plane(1.6, 0.95), f @ T(0, 0, 0.09), G(slug, 1.1), tile=None)

# ── 뮤직 월 (-x 끝 가벽): 흰 큐브 5 + 검은 룩 5 + 거울·비닐 원판과 CD ───────────────────
MUS = [('#151515', OUT1), ('#1A1A1A', OUT1), ('#202020', OUT1), ('#A02830', OUT3), ('#252525', OUT3)]
for i, zl in enumerate((-4.0, -2.8, -1.6, -0.4, 0.8)):
    z = Z(zl)
    expo.add(box(0.8, 0.6, 0.9), T(-15.75, 0.3, z), M['plinth'], 1)
    mannequin(expo, -15.75, 0.6, z, PI / 2, MUS[i][1], MUS[i][0])
gr = BYID['MUS_discs']['geometry']
PXD = -16.3 + PW_T / 2
for it in gr['items']:
    zc, yc = it['center_zy'] if 'center_zy' in it else (it.get('z', 0), it.get('y', 2))
    d_ = it.get('diameter', 0.3)
    mat = G('music_disc_logo') if 'big' in it.get('what', '') else (M['mirror'] if 'mirror' in it.get('what', '') else M['lineW'] if 'white' in it.get('what', '') else M['steel'])
    if mat.name.startswith('lpG_'):
        expo.add(cyl(d_ / 2, d_ / 2, 0.02, 40), T(PXD + 0.01, yc, Z(zc), 0, 0, PI / 2), M['black'], 1)
        expo.add(plane(d_ * 0.98, d_ * 0.98), T(PXD + 0.022, yc, Z(zc), PI / 2), material('lpDiscLogo', image_base=T_('music_disc_logo'), rough=0.3, alpha=True), tile=None)
    else:
        expo.add(cyl(d_ / 2, d_ / 2, 0.02, 40), T(PXD + 0.012, yc, Z(zc), 0, 0, PI / 2), mat, 1)
rng = random.Random(4)
for k in range(45):                                                                           # 무지갯빛 CD
    expo.add(cyl(0.06, 0.06, 0.004, 20), T(PXD + 0.012, rng.uniform(1.0, 3.0), Z(rng.uniform(-4.8, 1.6)), 0, 0, PI / 2), M['mirror'], 1)
for k in range(14):
    expo.add(cyl(0.15, 0.15, 0.008, 24), T(PXD + 0.014, rng.uniform(1.2, 2.8), Z(rng.uniform(-4.5, 1.4)), 0, 0, PI / 2), M['lineW'], 1)

# ══ 쇼 당일 (9.27): 런웨이·벤치·LED 3면·흰 조명탑 (웹: 런웨이 시점에서만 보임) ══════════════
for o in HALL['objects']:
    if o.get('phase') != 'show_27sep':
        continue
    g_ = o['geometry']['box']
    cx, cy, cz = g_['center']
    sx, sy, sz = g_['size']
    z = Z(cz)
    t = o['type']
    if t == 'runway':
        showday.add(box(sx, sy - 0.03, sz), T(cx, (sy - 0.03) / 2, z), M['bench'], 1)
        showday.add(box(sx, 0.03, sz), T(cx, sy - 0.015, z), M['runwayTop'], 1)
        for s in (-1, 1):
            showEmit.add(box(sx, 0.02, 0.03), T(cx, sy + 0.005, z + s * (sz / 2 - 0.02)), M['ledStrip'])
    elif t == 'bench_row':
        n = int(sx / 2.0)
        for k in range(n):
            bx = cx - sx / 2 + (k + 0.5) * sx / n
            showday.add(bevel_box(sx / n - 0.08, sy, sz, 0.01), T(bx, sy / 2, z), M['bench'], 1)
            if abs(z) < 2.5:                                                     # 앞줄 쇼핑백
                showday.add(bevel_box(0.26, 0.3, 0.1, 0.005), T(bx - 0.3, sy + 0.15, z), M['white'], 1)
    elif t == 'led_wall':
        slug = 'show_led_centre' if 'centre' in o['id'] else ('show_led_side' if o['id'].endswith('W') else 'show_led_side_r')
        showday.add(box(sx, sy + 0.1, sz + 0.1), T(cx - 0.05, cy, z), M['black'], 1)
        showEmit.add(plane(sz, sy), T(cx + sx / 2 + 0.02, cy, z, PI / 2), G(slug, 1.8), tile=None)
        showday.add(box(0.3, cy - sy / 2, 0.3), T(cx - 0.1, (cy - sy / 2) / 2, z), M['black'], 1)
    elif t == 'light_tower':
        showday.add(box(sx, sy, sz), T(cx, sy / 2, z), M['white'], 1)
        for k in range(4):                                                       # 무빙헤드 4개
            hx = cx - 0.75 + k * 0.5
            showday.add(bevel_box(0.3, 0.1, 0.3, 0.02), T(hx, 3.25, z - math.copysign(0.45, z)), M['black'], 1)
            showday.add(sphere(0.14, 2), T(hx, 3.08, z - math.copysign(0.45, z)), M['black'])
            showEmit.add(cyl(0.08, 0.08, 0.01, 12), T(hx, 2.93, z - math.copysign(0.45, z)), M['lens'])
        showday.add(box(2.0, 0.08, 0.12), T(cx, 3.33, z - math.copysign(0.45, z)), M['black'], 1)

# ══ 도로 쪽: 박공 가림막 · 투광등 · 담 · 철문 · 도로 · 전봇대 · 가로수 ═════════════════════
# 가림막 11.8 × 3.1m (y 0.2~3.3), 선버스트 + 로고, 위 후원사 띠 (현장 사진 텍스처)
panel(outer, 11.8, 3.1, T(HX + 0.09, 1.75, 0, PI / 2), G('street_banner'), M['black'], 0.12)
for k in range(7):                                                                           # 검은 구스넥 투광등
    z = -5.1 + k * 1.7
    g, m = tube(V((HX + 0.02, 3.55, z)), V((HX + 0.55, 3.62, z)), 0.018, 6)
    outer.add(g, m, M['black'])
    outer.add(cyl(0.07, 0.09, 0.14, 12), T(HX + 0.6, 3.52, z, 0, 0, 0.6), M['black'], 1)
    emit.add(cyl(0.06, 0.06, 0.01, 12), T(HX + 0.64, 3.45, z, 0, 0, 0.6), M['lens'])
# 담: 모서리 기둥 → 블록 담 '20' (1.66m + 회색 골강판 ~2.95m) → 초록 철문(주황 메시) → 서쪽 블록 담
FX = 17.6
outer.add(box(0.3, 1.66, 1.5), T(FX, 0.83, Z(7.15)), M['block'], 0.4)
outer.add(box(0.06, 1.29, 1.5), T(FX + 0.05, 1.66 + 0.645, Z(7.15)), M['corrGrey'], 1)
outer.add(plane(0.28, 0.33), T(FX + 0.152, 1.5, Z(6.9), PI / 2), G('blockwall_20'), tile=None)
outer.add(box(0.25, 3.0, 0.25), T(FX, 1.5, Z(7.9)), M['rust'], 1)                            # 녹슨 문설주
outer.add(plane(0.3, 0.11), T(FX + 0.152, 2.3, Z(6.8), PI / 2), material('lpStreetPlate', None, srgb('#1E4E9C'), 0.5), 1)
for (z0, z1, open_) in ((7.9, 10.8, True), (10.8, 13.7, False)):                              # 철문 두 짝
    w_ = z1 - z0
    if open_:
        f = T(FX - w_ / 2 * 0.2, 0, Z(z0) - 0.3, PI / 2 - 1.35)                                 # 안으로 열린 동쪽 짝
    else:
        f = T(FX, 0, Z((z0 + z1) / 2), PI / 2)
    outer.add(box(w_, 0.06, 0.06), f @ T(0, 2.17, 0), M['gateGreen'], 1)
    outer.add(box(w_, 0.06, 0.06), f @ T(0, 0.08, 0), M['gateGreen'], 1)
    for s in (-1, 1):
        outer.add(box(0.06, 2.2, 0.06), f @ T(s * (w_ / 2 - 0.03), 1.1, 0), M['gateGreen'], 1)
    court.add(plane(w_ - 0.1, 2.05), f @ T(0, 1.12, 0.05), G('gate', alpha=True), tile=None)
outer.add(box(0.3, 1.66, 16.55 - 13.7), T(FX, 0.83, Z((13.7 + 16.55) / 2)), M['block'], 0.4)
# 도로 (성수이로18길): 건물 선 0.3m 콘크리트 측구, 평행주차 칸(2m), 차도 6.45m, 북쪽 측구·가로수 띠
PZ0, PZ1 = -48.0, 44.0
outer.add(box(0.3, 0.06, PZ1 - PZ0), T(17.7, 0.0, (PZ0 + PZ1) / 2), M['gutterStrip'], 1)
outer.add(box(24.0 - 17.85, 0.06, PZ1 - PZ0), T((17.85 + 24.0) / 2, -0.005, (PZ0 + PZ1) / 2), M['street'], 4)
outer.add(box(0.95, 0.1, PZ1 - PZ0), T(24.475, 0.02, (PZ0 + PZ1) / 2), M['gutterStrip'], 1)
outer.add(box(30.3 - 24.95, 0.08, PZ1 - PZ0), T((24.95 + 30.3) / 2, 0.0, (PZ0 + PZ1) / 2), M['street'], 4)
for zl in range(-40, 44, 5):                                                                 # 주차 칸 선 (흰 선, 노란 번호)
    outer.add(box(2.0, 0.04, 0.1), T(18.55, 0.05, Z(zl)), M['lineW'], 1)
outer.add(box(0.1, 0.04, PZ1 - PZ0), T(19.55, 0.05, (PZ0 + PZ1) / 2), M['lineW'], 1)
TREES_Z = [47.75, 41.45, 35.15, 28.85, 22.55, 16.25, 9.95, 3.65, -2.65, -8.95, -15.25, -21.55, -27.85, -34.15]
for zl in TREES_Z:
    if PZ0 + 3 < Z(zl) < PZ1 - 3:
        tree(27.65, Z(zl), 1.0, 0.04)

# 전봇대 3개 (콘크리트, CC BY) + 전선 · A 변압기 · C 가로등·CCTV
POLE = props.load('f8b3249e56484746b193389914df9331', 'src_pole', height=10.5, coll=C_SRC)
import numpy as np  # noqa: E402
_co = np.empty(len(POLE.data.vertices) * 3, np.float32)
POLE.data.vertices.foreach_get('co', _co)
_co = _co.reshape(-1, 3)
_base = _co[_co[:, 2] < 1.0]
SHAFT = V((float(_base[:, 0].mean()), float(_base[:, 1].mean()), 0))
POLES = {'A': (17.95, Z(-7.85)), 'C': (17.25, Z(7.45)), 'B': (18.15, Z(20.15))}
POLE_RY = PI / 2                                                                    # 완목이 도로(+x)를 향하도록
for k_, (px, pz) in POLES.items():
    sx, sz = SHAFT.x, -SHAFT.y                                                       # 모델 안 기둥 중심 (웹 좌표)
    rx = sx * math.cos(POLE_RY) + sz * math.sin(POLE_RY)
    rz = -sx * math.sin(POLE_RY) + sz * math.cos(POLE_RY)
    instance(POLE, C_DYNAMIC, f'pole_{k_}', T(px - rx, 0.0, pz - rz, POLE_RY))
outer.add(cyl(0.35, 0.35, 1.1, 20), T(POLES['A'][0] + 0.4, 8.2, POLES['A'][1]), M['steel'], 1)        # 변압기
cx_, cz_ = POLES['C']
g, m = tube(V((cx_ - 0.05, 6.6, cz_)), V((cx_ + 2.5, 7.0, cz_)), 0.04, 8, caps=True)
outer.add(g, m, M['steel'])
outer.add(bevel_box(0.6, 0.12, 0.26, 0.02), T(cx_ + 2.7, 6.95, cz_), M['steel'], 1)
outer.add(sphere(0.12, 2), T(cx_ + 0.2, 4.2, cz_), M['white'])                                   # CCTV
outer.add(box(0.3, 0.45, 0.2), T(cx_ + 0.2, 2.2, cz_ - 0.45), material('lpBlueBox', None, (0.1, 0.25, 0.6), 0.5), 1)
order = sorted(POLES.values(), key=lambda p: p[1])
ends = [(18.0, PZ0 + 0.5)] + order + [(18.0, PZ1 - 0.5)]
for (dy, dx) in ((9.6, -0.3), (9.6, 0.3), (8.8, -0.5), (7.4, 0.2), (6.8, -0.2), (6.3, 0.25)):
    for (px, pz) in POLES.values():                                                          # 전봇대에 묶는 금구
        member(outer, V((px, dy, pz)), V((18.0 + dx, dy, pz)), 0.022, M['steel'])
    for a_, b_ in zip(ends, ends[1:]):
        catenary(rig, V((a_[0] + dx, dy, a_[1])), V((b_[0] + dx, dy, b_[1])), 0.4 + abs(b_[1] - a_[1]) * 0.012, 0.012, M['wire'], 14)

# ══ 이웃 (조사된 평면 상자) ════════════════════════════════════════════
def gable_block(x0, x1, z0, z1, eave, ridge, wall_mat, roof_mat, ridge_along='z'):
    """박공 지붕 창고: ridge_along 축으로 용마루"""
    cx, cz, w, d = (x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, z1 - z0
    nbrs.add(box(w, eave, d), T(cx, eave / 2, cz), wall_mat, 3)
    half = (w if ridge_along == 'z' else d) / 2
    th_ = math.atan2(ridge - eave, half)
    sl = math.hypot(ridge - eave, half) + 0.3
    for s in (-1, 1):
        if ridge_along == 'z':
            nbrs.add(box(0.06, sl, d + 0.3), T(cx + s * half / 2, (eave + ridge) / 2 + 0.03, cz, 0, 0, s * (PI / 2 - th_)), roof_mat, 2)
        else:
            nbrs.add(box(w + 0.3, sl, 0.06), T(cx, (eave + ridge) / 2 + 0.03, cz + s * half / 2, 0, -s * (PI / 2 - th_)), roof_mat, 2)
    for e in (-1, 1):
        def tri(bm, e=e):
            if ridge_along == 'z':
                vs = [bm.verts.new(p) for p in ((x0, eave, cz + e * d / 2), (x1, eave, cz + e * d / 2), (cx, ridge, cz + e * d / 2))]
            else:
                vs = [bm.verts.new(p) for p in ((cx + e * w / 2, eave, z0), (cx + e * w / 2, eave, z1), (cx + e * w / 2, ridge, cz))]
            bm.faces.new(vs)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            for f in bm.faces:
                f.normal_update()
                if (f.normal.z if ridge_along == 'z' else f.normal.x) * e < 0:
                    f.normal_flip()
        nbrs.add(tri, T(), wall_mat, 3)


def flat_block(x0, x1, z0, z1, h, mat, roof=None):
    nbrs.add(box(x1 - x0, h, z1 - z0), T((x0 + x1) / 2, h / 2, (z0 + z1) / 2), mat, 3)
    if roof:
        nbrs.add(box(x1 - x0 - 0.4, 0.05, z1 - z0 - 0.4), T((x0 + x1) / 2, h + 0.065, (z0 + z1) / 2), roof, 2)


gable_block(4.35, 16.95, 7.05, 42.85, 4.3, 6.0, M['nbr'], M['nbrBlue'], 'z')                 # 동쪽 푸른 박공 창고 (용마루 도로와 나란히)
flat_block(-1.35, 4.35, 7.05, 13.35, 3.0, M['nbrBeige'])                                     # 베이지 부속
flat_block(-7.35, -1.85, 7.15, 13.85, 3.0, M['nbrDark'])                                     # 어두운 평지붕
gable_block(-13.35, -4.85, 7.05, 43.85, 4.5, 6.5, M['nbr'], M['nbrGreen'], 'z')              # 청록 박공 창고
flat_block(-30.0, -18.35, 7.35, 44.0, 7.5, M['nbr'], M['nbrBlue'])                           # 남쪽 푸른 L 블록
flat_block(-33.35, -19.35, -16.0, 6.0, 2.0, M['block'])                                      # 남쪽 주차장 담 (낮게)
flat_block(-15.35, 8.65, -41.15, -30.85, 6.0, M['nbrDark'])                                  # 서쪽 어두운 지붕 건물
flat_block(-28.35, -17.35, -44.15, -18.15, 8.0, M['nbr'], M['pv'])                          # 남서 태양광 지붕 건물
# 흰 판자 2층집 (마당 서쪽): 가로 판자 사이딩, 흰 알루미늄 창, 북쪽 끝 검은 발코니
HX0, HX1, HZ0, HZ1, HH = -14.1, 10.55, Z(22.75), Z(16.55), 6.0
nbrs.add(box(HX1 - HX0, HH, HZ1 - HZ0 - 0.1), T((HX0 + HX1) / 2, HH / 2, (HZ0 + HZ1 - 0.1) / 2), M['nbrWhite'], 3)
nbrs.add(plane(HX1 - HX0, HH), T((HX0 + HX1) / 2, HH / 2, HZ1), M['clapboard'], 1.2)   # 마당 쪽 면 (판자)
nbrs.add(box(HX1 - HX0 + 0.3, 0.12, HZ1 - HZ0 + 0.3), T((HX0 + HX1) / 2, HH + 0.06, (HZ0 + HZ1) / 2), M['roofLight'], 2)
for fl in (1.2, 4.1):
    for x in [HX0 + 1.5 + k * 3.1 for k in range(8)]:
        nbrs.add(box(1.2, 1.0, 0.08), T(x, fl + 0.5, HZ1 + 0.04), M['glassDark'], 1)
        nbrs.add(box(1.3, 0.05, 0.12), T(x, fl, HZ1 + 0.05), M['white'], 1)
bal = T(8.5, 3.0, HZ1 + 0.6)
nbrs.add(box(3.0, 0.12, 1.2), bal, M['black'], 1)
for k in range(16):
    g, m = tube(bal @ V((-1.45 + k * 0.19, 0.06, 0.58)), bal @ V((-1.45 + k * 0.19, 1.1, 0.58)), 0.012, 5)
    rig.add(g, m, M['black'])
g, m = tube(bal @ V((-1.5, 1.1, 0.58)), bal @ V((1.5, 1.1, 0.58)), 0.02, 6)
rig.add(g, m, M['black'])
flat_block(-16.35, 4.65, Z(30.15), Z(22.75), 3.5, M['nbr'], M['roofLight'])                  # 낮은 뒤채
# 초록 철망 담 (판자집 앞, 1.8m)
court.add(plane(HX1 - (-7.55), 1.8), T((HX1 - 7.55) / 2, 0.9, Z(16.45) + 0.12), G('gate', alpha=True), tile=None)
# S-Factory (길 건너 흰 블록, 가로 창 띠) + 앞 주차장
flat_block(37.65, 58.0, -41.0, 19.0, 14.0, M['nbrWhite'], M['nbr'])
for fl in (2.0, 5.5, 9.0, 12.5):
    nbrs.add(box(0.1, 1.4, 58.0), T(37.6, fl, -11.0), M['glassDark'], 1)
nbrs.add(box(37.65 - 30.3, 0.05, 60.0), T((30.3 + 37.65) / 2, 0.025, -11.0), M['street'], 3)

# ══ 입구 마당 (25.2 × 10.5m) ═══════════════════════════════════════════════════════════
#    근거: assets-src/refs/localpower/yard_layout.md/json (2차 조사).
#    높이는 수평선(소실선)법으로 다시 잼: 가림막 4.2m, 포토월 2.85m (1차의 4.7/3.24 는 12% 과대).
#    바닥은 두 가지: x>4 슬래브 콘크리트(넓은 줄눈), x<4 주차선이 남은 아스팔트.
YX0, YX1, YZ0, YZ1 = -7.55, 17.6, Z(16.55), Z(6.1)                      # 마당 범위 (웹)
SURF_X = 4.0                                                            # 바닥이 바뀌는 선
court.add(box(YX1 - SURF_X, 0.1, YZ1 - YZ0), T((SURF_X + YX1) / 2, -0.05, (YZ0 + YZ1) / 2), M['slab'], 3)
court.add(box(SURF_X - YX0, 0.1, YZ1 - YZ0), T((YX0 + SURF_X) / 2, -0.05, (YZ0 + YZ1) / 2), M['asphalt'], 3)
for k in range(9):                                                      # 남아 있는 흰 주차선 (2.4m 간격)
    x_ = SURF_X - 0.6 - k * 2.4
    if x_ > YX0 + 0.3:
        court.add(box(0.1, 0.04, 4.6), T(x_, 0.02, Z(11.9)), M['lineW'], 1)
court.add(box(SURF_X - YX0 - 0.6, 0.04, 0.1), T((YX0 + SURF_X) / 2, 0.02, Z(9.6)), M['lineW'], 1)
court.add(box(0.45, 0.06, YZ1 - YZ0 - 1.0), T(15.3, 0.01, (YZ0 + YZ1) / 2), M['drain'], 1)     # 문 안쪽 배수 홈
court.add(cyl(0.325, 0.325, 0.03, 24), T(16.3, 0.02, Z(11.6)), M['steel'], 1)                  # 맨홀 뚜껑
court.add(cyl(0.3, 0.3, 0.03, 24), T(5.4, 0.02, Z(14.9)), M['steel'], 1)
# 빨간 길: 문 밖 노면에서 시작해 마당을 가로지른 뒤 가림막 문 앞에서 꺾인다 (폭 1.45m)
court.add(box(18.6 - 17.45, 0.04, 1.45), T((17.45 + 18.6) / 2, 0.021, Z(10.175)), M['redPath'], 2)
court.add(box(17.45 - 2.45, 0.04, 1.45), T((2.45 + 17.45) / 2, 0.02, Z(10.175)), M['redPath'], 2)
court.add(box(7.9 - 5.0, 0.04, Z(7.6) - Z(9.45)), T(6.45, 0.02, (Z(7.6) + Z(9.45)) / 2), M['redPath'], 2)

# ── 주황 가림막 (z=7.4 평면, 높이 4.2m, 두께 0.25m, 5개 모듈) ─────────────────────────
HOARD_Z, HOARD_H, HOARD_T = Z(7.4), 4.2, 0.25
for (x0, x1, slug) in ((12.6, 17.45, 'hoarding_text'),        # 인사말 + 본문 4단
                       (7.9, 12.6, 'hoarding_logo'),          # 세로 대형 워드마크
                       (1.6, 5.0, 'hoarding_exhibition')):    # EXHIBITION IN SEOUL + 3개 존 설명
    panel(court, x1 - x0, HOARD_H, T((x0 + x1) / 2, HOARD_H / 2, HOARD_Z, PI), G(slug), M['orange'], HOARD_T)
DR0, DR1, DR_H, OP_W, OP_H = 5.0, 7.9, 3.9, 1.9, 2.6          # 창고 출입 모듈 (여기만 낮아진다: 개구부 2.6 + 후원사판 1.3)
DRC = (DR0 + DR1) / 2
for s in (-1, 1):                                              # 주황 문설주
    jw = (DR1 - DR0 - OP_W) / 2
    panel(court, jw, DR_H, T(DRC + s * (OP_W + jw) / 2, DR_H / 2, HOARD_Z, PI), M['orange'], M['orange'], HOARD_T)
panel(court, OP_W, DR_H - OP_H, T(DRC, (OP_H + DR_H) / 2, HOARD_Z, PI), G('hoarding_sponsor'), M['white'], HOARD_T)
for s in (-1, 1):                                              # 문 뒤 통로 (가림막 ~ 창고 벽)
    court.add(plane(Z(6.1) - Z(7.4), OP_H), T(DRC + s * (OP_W / 2 - 0.12), OP_H / 2, Z(6.75), -s * PI / 2), M['orange'], 1)
court.add(plane(OP_W - 0.24, Z(6.1) - Z(7.4)), T(DRC, OP_H, Z(6.75), 0, PI / 2), M['black'], 1)
court.add(box(1.0, 0.02, 0.25), T(DRC, 0.03, Z(7.62)), M['hazard'], 1)                         # 문턱 위험 띠
court.add(bevel_box(0.6, 1.05, 0.6, 0.03), T(8.4, 0.525, Z(7.95)), M['black'], 1)              # 검은 이동식 쓰레기통
court.add(cyl(0.11, 0.12, 0.5, 16), T(4.6, 0.25, Z(7.85)), material('lpExtin', None, srgb('#B32019'), 0.5), 1)
for x_ in (16.0, 11.5, 7.0, 2.5):                                                              # 가림막 뒤 구스넥 투광등 (5m 기둥)
    court.add(cyl(0.05, 0.05, 5.0, 10), T(x_, 2.5, HOARD_Z + 0.5), M['black'], 1)
    g, m = tube(V((x_, 5.0, HOARD_Z + 0.5)), V((x_, 5.05, HOARD_Z - 0.35)), 0.025, 6)
    court.add(g, m, M['black'])
    court.add(cyl(0.08, 0.1, 0.16, 12), T(x_, 4.95, HOARD_Z - 0.42, 0, 0.7), M['black'], 1)
    emit.add(cyl(0.07, 0.07, 0.01, 12), T(x_, 4.87, HOARD_Z - 0.46, 0, 0.7), M['lens'])

# ── 홍콩 간판 포토월 (앞면 x=6.3, z 11.0~15.3, 4.35 × 2.85m = 콜라주 2.50 + 흰 머리띠 0.35) ──
PWX, PWH, PWT, PW_CAP = 6.3, 2.5, 0.25, 0.35
pwf = T(PWX - PWT / 2, PWH / 2, Z(13.15), PI / 2)
court.add(plane(4.35, PWH), pwf @ T(0, 0, PWT / 2), G('photowall_front'), tile=None)
court.add(plane(4.35, PWH), pwf @ T(0, 0, -PWT / 2, PI), G('photowall_back'), tile=None)
for s in (-1, 1):
    court.add(plane(PWT, PWH), pwf @ T(s * 2.175, 0, 0, s * PI / 2), M['white'], 1)
panel(court, 4.35, PW_CAP, T(PWX - PWT / 2 + 0.06, PWH + PW_CAP / 2, Z(13.15), PI / 2),        # 후원사 머리띠 (0.12 앞으로)
      G('photowall_sponsor') if os.path.exists(T_('photowall_sponsor')) else M['white'], M['white'], PWT + 0.12)
for s in (-1, 1):                                              # 양 끝 흰 리턴 (0.5m)
    court.add(box(0.5, PWH + PW_CAP, PWT), T(PWX - PWT - 0.25, (PWH + PW_CAP) / 2, Z(13.15 + s * 2.05)), M['white'], 1)
for zz in (Z(11.6), Z(14.7)):                                  # 뒤 투광등 (4m 기둥)
    court.add(cyl(0.045, 0.045, 4.0, 10), T(PWX - 1.1, 2.0, zz), M['black'], 1)
    g, m = tube(V((PWX - 1.1, 4.0, zz)), V((PWX - 0.15, 4.05, zz)), 0.022, 6)
    court.add(g, m, M['black'])
    court.add(cyl(0.075, 0.095, 0.15, 12), T(PWX - 0.05, 3.95, zz, 0, 0, -0.7), M['black'], 1)
    emit.add(cyl(0.065, 0.065, 0.01, 12), T(PWX + 0.02, 3.88, zz, 0, 0, -0.7), M['lens'])

# ── 서쪽 ㄱ자: 야경 패널 → 트램 컷아웃 → 금붕어 가게 → 붉은 대문 ──────────────────────
NS_Z = Z(15.9)
panel(court, 7.7, 2.4, T(2.45, 1.2, NS_Z), G('nightstreet_panel'), M['black'], 0.1)            # 홍콩 야경 두 장
for s in (-1, 1):
    member(court, V((2.45 + s * 3.6, 0.05, NS_Z - 0.45)), V((2.45 + s * 3.6, 2.25, NS_Z - 0.06)), 0.03, M['steel'])
tf = T(2.6, 0, Z(14.4))                                                                        # 트램 88 얼굴 컷아웃
panel(court, 1.25, 2.30, tf @ T(0, 1.15, 0), G('tram_cutout', alpha=True), M['white'], 0.07)
panel(court, 0.9, 0.35, tf @ T(0, 2.48, 0), M['white'], M['white'], 0.07)
court.add(box(1.4, 0.08, 0.5), tf @ T(0, 0.04, -0.3), M['black'], 1)
GF_X0, GF_X1, GF_Z, GF_D = -7.4, -3.9, Z(15.9), 1.8                                            # 금붕어 가게 (2면, ≈100°)
panel(court, GF_X1 - GF_X0, 2.4, T((GF_X0 + GF_X1) / 2, 1.2, GF_Z), G('goldfish_back'), M['white'], 0.08)
panel(court, GF_D, 2.4, T(GF_X0, 1.2, GF_Z + GF_D / 2, PI / 2 + 0.17), G('goldfish_left'), M['white'], 0.08)
court.add(box(GF_X1 - GF_X0, 0.05, 0.05), T((GF_X0 + GF_X1) / 2, 1.15, GF_Z - 0.06), M['white'], 1)   # 흰 가로 난간
gt = T((GF_X0 + GF_X1) / 2 + 0.2, 0, GF_Z + 1.15)                                              # 흰 철제 테이블 + 실제 수조
court.add(box(1.5, 0.04, 0.5), gt @ T(0, 0.78, 0), M['white'], 1)
for (sx, sz) in ((-0.7, -0.21), (0.7, -0.21), (-0.7, 0.21), (0.7, 0.21)):
    court.add(cyl(0.016, 0.016, 0.78, 8), gt @ T(sx, 0.39, sz), M['white'], 1)
    court.add(box(0.03, 0.03, 0.44), gt @ T(sx, 0.12, 0), M['white'], 1)
emit.add(box(1.46, 0.34, 0.39), gt @ T(0, 1.0, 0), material('lpTankLit', None, (0.3, 0.55, 0.62), 0.3, emit=(0.1, 0.3, 0.45), emit_strength=0.5), 1)
court.add(box(1.5, 0.12, 0.45), gt @ T(0, 0.86, 0), material('lpGravel', None, (0.72, 0.68, 0.6), 0.9), 1)
rig.add(box(1.5, 0.45, 0.45), gt @ T(0, 1.02, 0), material('lpTank', None, (0.6, 0.8, 0.85), 0.1, transmission=0.9), 1)
# 붉은 대문: 조사 위치 x=-8.0 은 부지 밖이라 서쪽 경계에 붙여 +x 를 보게 세움 (사진의 연회색 곡면 판도 같이)
rd = T(-7.05, 0, Z(13.6), PI / 2)
court.add(box(3.4, 3.3, 0.12), rd @ T(0, 1.65, -0.09), M['paleGrey'], 1)                       # 기댄 연회색 판
panel(court, 1.95, 2.90, rd @ T(0, 1.45, 0.08), G('red_door'), M['black'], 0.1)
for j in range(36):                                                                             # 금색 문정 6 × 6
    court.add(sphere(0.032, 2), rd @ T(-0.78 + (j % 6) * 0.31, 0.55 + (j // 6) * 0.41, 0.145, 0, 0, 0, 1, 1, 0.6), M['brass'])
court.add(cyl(0.085, 0.085, 0.02, 20), rd @ T(-0.72, 1.10, 0.16, 0, PI / 2), M['brass'], 1)
court.add(box(0.8, 0.06, 0.5), rd @ T(1.1, 0.03, 0.5, 0, 0, 0.2), M['gateGreen'], 1)           # 접힌 초록 펜스 조각
court.add(sphere(0.2, 2), rd @ T(0.75, 0.16, 0.45, 0, 0, 0, 1.5, 0.7, 1.0), material('lpSandbag', 'cotton_jersey', (0.2, 0.42, 0.24), 0.9))

# ── 딤섬 부스 (가림막 선을 잇는다, x 1.6 ~ -2.0, z=7.6, 2.6m, +z 로 열림) ───────────────
DM_X0, DM_X1, DM_Z, DM_D = -2.0, 1.6, Z(7.6), 1.6
panel(court, 1.8, 2.25, T(DM_X1 - 0.9, 1.125, DM_Z, PI), G('dimsum_dragon'), M['black'], 0.1)
panel(court, 1.8, 2.25, T(DM_X0 + 0.9, 1.125, DM_Z, PI), G('dimsum_phoenix'), M['black'], 0.1)
panel(court, DM_D, 2.25, T(DM_X0, 1.125, DM_Z - DM_D / 2, PI / 2), G('dimsum_phoenix'), M['black'], 0.1)
dm = T((DM_X0 + DM_X1) / 2, 0, DM_Z - 0.95)                                                    # 연회 원탁 Ø1.5 + 의자 5
court.add(cyl(0.75, 0.75, 0.05, 40), dm @ T(0, 0.735, 0), material('lpRedCloth', 'cotton_jersey', (0.5, 0.05, 0.06), 0.9), 1)
court.add(cyl(0.7, 0.73, 0.72, 40), dm @ T(0, 0.36, 0), material('lpRedCloth2', 'cotton_jersey', (0.45, 0.04, 0.05), 0.95), 1)
court.add(cyl(0.2, 0.2, 0.24, 24), dm @ T(0, 0.87, 0), material('lpCopper', None, (0.62, 0.38, 0.18), 0.35, 0.9), 1)
for k in range(7):                                                                              # 대나무 찜통 · 흰 찻잔
    a = k / 7 * 2 * PI
    court.add(cyl(0.1, 0.1, 0.07, 16), dm @ T(0.45 * math.cos(a), 0.795, 0.45 * math.sin(a)), M['wood'], 1)
    court.add(cyl(0.035, 0.04, 0.05, 12), dm @ T(0.66 * math.cos(a + 0.4), 0.785, 0.66 * math.sin(a + 0.4)), M['white'], 1)
for k in range(5):
    ch = dm @ T(1.12 * math.cos(k / 5 * 2 * PI + 0.7), 0, 1.12 * math.sin(k / 5 * 2 * PI + 0.7), -(k / 5 * 2 * PI + 0.7))
    court.add(box(0.42, 0.04, 0.42), ch @ T(0, 0.45, 0), M['darkWood'], 1)
    court.add(box(0.42, 0.55, 0.04), ch @ T(0, 0.73, 0.19), M['darkWood'], 1)
    for (lx, lz) in ((-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)):
        court.add(cyl(0.015, 0.015, 0.45, 6), ch @ T(lx, 0.225, lz), M['darkWood'], 1)

# ── 체험 존: 주차선 아스팔트 위 베이지 차양(9.0 × 4.5) 아래로 모여 있다 ────────────────
CAN_X0, CAN_X1, CAN_Z0, CAN_Z1, CAN_EAVE, CAN_RIDGE = -7.3, 1.7, Z(13.8), Z(9.3), 2.3, 2.9
for x_ in (CAN_X0 + 0.15, (CAN_X0 + CAN_X1) / 2, CAN_X1 - 0.15):                               # 회색 기둥 + 모래주머니
    for z_ in (CAN_Z0 + 0.15, CAN_Z1 - 0.15):
        court.add(cyl(0.03, 0.03, CAN_EAVE, 10), T(x_, CAN_EAVE / 2, z_), M['steel'], 1)
        court.add(sphere(0.17, 2), T(x_, 0.1, z_, 0, 0, 0, 1.4, 0.55, 1.0), M['black'])
for s in (-1, 1):                                                                               # 박공형 차양 천
    court.add(plane(CAN_X1 - CAN_X0, math.hypot(CAN_RIDGE - CAN_EAVE, (CAN_Z1 - CAN_Z0) / 2)),
              T((CAN_X0 + CAN_X1) / 2, (CAN_EAVE + CAN_RIDGE) / 2, (CAN_Z0 + CAN_Z1) / 2 + s * (CAN_Z1 - CAN_Z0) / 4,
                0, PI / 2 + s * math.atan2(CAN_RIDGE - CAN_EAVE, (CAN_Z1 - CAN_Z0) / 2)), M['tentBeige'], 2)
for k in range(13):                                                                             # 가장자리 전구 줄
    emit.add(sphere(0.045, 2), T(CAN_X0 + 0.3 + k * 0.7, CAN_EAVE - 0.12, CAN_Z0 + 0.12), M['bulb'])
BACK_Z = Z(9.45)                                                                                # 뒤 라인아트 패널 (2.4m, 빨강·주황)
panel(court, 3.6, 2.4, T(-5.3, 1.2, BACK_Z, PI), G('lineart_panel_red') if os.path.exists(T_('lineart_panel_red')) else G('tshirt_backdrop_lineart'), M['orange'], 0.08)
panel(court, 3.4, 2.4, T(-1.4, 1.2, BACK_Z, PI), G('tshirt_backdrop'), M['orange'], 0.08)
panel(court, 1.8, 2.4, T(1.35, 1.2, BACK_Z, PI), G('tshirt_backdrop_lineart'), M['orange'], 0.08)
vf = T(-5.3, 0, Z(10.1), PI)                                                                    # 뷰티존: 3.3m 검은 테이블 + 전구 거울 2
court.add(box(3.3, 0.06, 0.6), vf @ T(0, 0.75, 0), M['black'], 1)
court.add(box(3.3, 0.72, 0.05), vf @ T(0, 0.36, -0.275), M['black'], 1)
for s in (-1, 1):
    court.add(box(0.05, 0.72, 0.55), vf @ T(s * 1.62, 0.36, 0), M['black'], 1)
    mf = vf @ T(s * 0.8, 0, -0.18)
    court.add(box(1.25, 0.85, 0.03), mf @ T(0, 1.2, 0.02), M['mirror'], 1)
    for (bw, bh, by, bx) in ((1.35, 0.1, 0.475, 0.0), (1.35, 0.1, -0.475, 0.0), (0.1, 0.95, 0.0, 0.625), (0.1, 0.95, 0.0, -0.625)):
        court.add(box(bw, bh, 0.06), mf @ T(bx, 1.2 + by, 0.0), M['black'], 1)
    for j in range(14):
        a = j / 14 * 2 * PI
        emit.add(sphere(0.03, 2), mf @ T(0.62 * math.cos(a), 1.2 + 0.47 * math.sin(a), 0.04), M['bulbSoft'])
for k in range(3):                                                                              # 검은 접이 감독 의자 3
    cf = vf @ T(-1.0 + k * 1.0, 0, -0.95)
    court.add(box(0.46, 0.05, 0.44), cf @ T(0, 0.46, 0), M['black'], 1)
    court.add(box(0.46, 0.42, 0.05), cf @ T(0, 0.73, -0.2), M['black'], 1)
    for (lx, lz) in ((-0.2, -0.18), (0.2, -0.18), (-0.2, 0.18), (0.2, 0.18)):
        court.add(cyl(0.018, 0.018, 0.46, 6), cf @ T(lx, 0.23, lz), M['black'], 1)
court.add(box(0.6, 0.8, 0.06), vf @ T(-2.1, 1.5, -0.4), M['white'], 1)                          # 흰 LED 소프트박스
court.add(cyl(0.02, 0.02, 1.1, 8), vf @ T(-2.1, 0.55, -0.4), M['black'], 1)
tsf = T(-1.4, 0, Z(10.2), PI)                                                                   # DIY 티셔츠: 팔레트 카운터 3.0m + 열프레스 3
for k in range(5):
    court.add(box(0.64, 0.42, 0.9), tsf @ T(-1.2 + k * 0.6, 0.21, 0), M['pine'], 1)
    court.add(box(0.64, 0.44, 0.9), tsf @ T(-1.2 + k * 0.6, 0.63, 0), M['pine'], 1)
court.add(box(3.0, 0.06, 1.0), tsf @ T(0, 0.92, 0), M['pine'], 1)
for k in range(3):
    f = tsf @ T(-0.95 + k * 0.95, 0.99, 0)
    court.add(bevel_box(0.45, 0.14, 0.4, 0.02), f, M['white'], 1)
    court.add(bevel_box(0.45, 0.1, 0.4, 0.02), f @ T(0, 0.3, -0.06, 0, -0.55), M['white'], 1)
    court.add(cyl(0.02, 0.02, 0.32, 8), f @ T(0, 0.22, -0.24), M['steel'], 1)
panel(court, 2.0, 1.6, T(-1.4, 1.6, BACK_Z - 0.16, PI), G('tshirt_pegboard') if os.path.exists(T_('tshirt_pegboard')) else M['white'], M['white'], 0.05)
kf = T(0.9, 0, Z(10.3), PI / 2)                                                                 # AI 포토부스 (야외 1대)
court.add(bevel_box(0.7, 0.95, 0.95, 0.02), kf @ T(0, 0.475, 0), M['white'], 1)
court.add(bevel_box(0.78, 1.1, 0.88, 0.02), kf @ T(0, 1.5, -0.03), M['white'], 1)
emit.add(plane(0.62, 0.78), kf @ T(0, 1.52, 0.47), G('ai_kiosk_front', 1.0), tile=None)
for (bw, bh, by, bx) in ((0.78, 0.05, 0.55, 0.0), (0.78, 0.05, -0.55, 0.0), (0.05, 1.1, 0.0, 0.39), (0.05, 1.1, 0.0, -0.39)):
    emit.add(box(bw, bh, 0.04), kf @ T(bx, 1.5 + by, 0.47), M['ledStrip'])
emit.add(box(0.22, 0.03, 0.03), kf @ T(0, 0.75, 0.46), material('lpSlotRed', None, (1, 0.2, 0.15), 0.4, emit=(1, 0.15, 0.1), emit_strength=3), 1)
# 팔레트 테이블 3 + 상자 스툴 10 (차양 아래 아스팔트)
for (cx, cz, ry) in ((-4.6, Z(12.2), 0.2), (-2.6, Z(13.0), -0.35), (-0.6, Z(12.3), 0.1)):
    f = T(cx, 0, cz, ry)
    court.add(box(1.1, 0.30, 1.1), f @ T(0, 0.15, 0), M['pine'], 1)
    court.add(box(1.16, 0.12, 1.16), f @ T(0, 0.34, 0), M['pine'], 1)
for (sx, sz, sr) in ((-5.7, 12.2, 0.3), (-3.6, 12.3, -0.2), (-5.0, 13.3, 0.5), (-3.3, 13.7, 0.1),
                     (-1.7, 13.2, -0.4), (-3.6, 12.9, 0.2), (0.3, 12.4, 0.35), (-2.3, 11.6, -0.1),
                     (-6.0, 13.3, 0.15), (-0.5, 13.4, -0.3)):
    court.add(box(0.42, 0.42, 0.42), T(sx, 0.21, Z(sz), sr), M['pine'], 1)


def sign_stand(x, z, ry, slug, w=0.52, h=0.72, top=1.55):
    """검은 철제 사각 프레임 + 다리 두 개 (조사 v2: A1 스탠드가 아니다)"""
    f = T(x, 0, z, ry)
    for s in (-1, 1):
        court.add(box(0.03, top, 0.03), f @ T(s * (w / 2 + 0.03), top / 2, 0), M['black'], 1)
    panel(court, w, h, f @ T(0, top - h / 2 - 0.04, 0), G(slug), M['black'], 0.03)


sign_stand(-1.4, Z(11.4), PI, 'sign_tshirt' if os.path.exists(T_('sign_tshirt')) else 'sign_keyring')
sign_stand(-5.3, Z(11.3), PI, 'sign_beauty')
sign_stand(0.9, Z(11.5), PI, 'sign_aibooth')
sign_stand(-3.0, Z(12.4), PI, 'sign_keyring')
sign_stand(18.4, Z(8.6), PI / 2, 'info_sign', 0.55, 0.78, 1.60)        # 안내판은 문 밖 보도에 선다
# 남쪽 끝: 가림막(2.7m)으로 막히고 그 뒤로 대나무·상록수 덤불, 서쪽 경계는 초록 철망 담
court.add(plane(YZ1 - YZ0, 2.7), T(YX0 - 0.1, 1.35, (YZ0 + YZ1) / 2, PI / 2), M['paleGrey'], 2)
court.add(plane(Z(6.1) - Z(16.55), 1.8), T(YX0 + 0.05, 0.9, (YZ0 + YZ1) / 2, -PI / 2), M['mesh'], tile=None)
for pz in (8.0, 11.0, 14.0):
    tree(YX0 - 2.4, Z(pz), 1.1, 0.0)
    court.add(sphere(1.6, 3), T(YX0 - 1.2, 1.7, Z(pz + 1.4), 0, 0, 0, 1.0, 1.5, 1.0), M['bamboo'])

# ══ 조명 · 빌드 · 카메라 ═══════════════════════════════════════════
for x in (-12.5, -7.5, -2.5, 2.5, 7.5, 12.5):                                  # 전시장 트랙 조명 (밝은 흰 전시)
    for z in (-3.6, 3.6):
        light(C_LIGHT, f'track_{x}_{z}', 'AREA', (x, 3.5, z * 0.8), (x, 0, z * 0.2), energy=160, color=(1.0, 0.96, 0.9), size=2.5)
light(C_LIGHT, 'hall_fill', 'AREA', (0, 3.4, 0), (0, 0, 0), energy=300, color=(1.0, 0.97, 0.93), size=12)
light(C_LIGHT, 'col_spot', 'SPOT', (10.5, 3.6, 1.8), (10.5, 1.2, 0.6), energy=500, color=(1.0, 0.95, 0.88), spot=1.0, blend=0.5)
light(C_LIGHT, 'sun', 'SUN', (60, 50, -20), (0, 0, 0), energy=2.6, color=(1.0, 0.96, 0.9))

for a in (shell, shellOut, truss, floor, expo, outer, court, nbrs, emit, expoEmit, rig, leaves, showday, showEmit):
    a.build(smooth=(a is rig))
for n in ('lpBrick', 'lpRoofIn', 'lpWallIn', 'lpCreamWall', 'lpCorrWhite'):
    if n in bpy.data.materials:
        bpy.data.materials[n].use_backface_culling = True
for i, (src, mtx) in enumerate(outfit_spots):
    instance(src, C_DYNAMIC, f'outfit_{i:02d}', mtx)

w = bpy.data.worlds.new('lp_world')
w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.64, 0.78, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.5
scene.world = w

camera(C_CAM, 'cam_overview', (58, 44, 44), (4, 0, -4), 42)
camera(C_CAM, 'cam_aerial', (50, 34, 8), (2, 0, -5), 38)                  # 소개서 조감 시뮬레이션
camera(C_CAM, 'cam_street', (29.5, 1.7, 9.0), (14.0, 3.0, -6.0), 62)              # 거리 입면
camera(C_CAM, 'cam_hall_long', (-13.5, 1.6, 0.4), (16, 1.6, 0), 70)        # 긴 쪽 (hall_view_long)
camera(C_CAM, 'cam_exhibit', (14.3, 1.6, -1.2), (0, 1.5, 1.5), 64)          # 소개서 전시 사진
camera(C_CAM, 'cam_curtain', (-4.0, 1.6, -2.6), (-4.0, 1.5, 3.2), 64)      # 소개서 커튼 사진
camera(C_CAM, 'cam_music', (-8.0, 1.6, -0.5), (-16.3, 1.8, 1.0), 64)
camera(C_CAM, 'cam_yard', (16.0, 1.6, Z(12.3)), (6.3, 1.5, Z(13.15)), 62)          # 문 안쪽 → 포토월 정면 (보도자료 입면)
camera(C_CAM, 'cam_photowall', (2.0, 1.6, Z(12.2)), (6.2, 1.5, Z(13.2)), 62)        # 포토 링 안 → 포토월 뒷면
camera(C_CAM, 'cam_hoarding', (15.2, 1.6, Z(10.9)), (9.0, 2.3, Z(7.4)), 62)         # 주황 가림막 (yard_hoarding_run_full)
camera(C_CAM, 'cam_doorway', (9.6, 1.6, Z(10.6)), (2.0, 1.5, Z(8.2)), 62)           # 출입 모듈 → 딤섬 부스
camera(C_CAM, 'cam_yard_props', (-4.6, 1.55, Z(14.3)), (-6.2, 1.35, Z(15.8)), 72)   # 금붕어 가게 · 붉은 대문
camera(C_CAM, 'cam_canopy', (3.2, 1.6, Z(12.6)), (-5.2, 1.4, Z(10.4)), 66)          # 체험 존 차양
camera(C_CAM, 'cam_runway', (6.5, 1.8, 0.0), (-16.0, 2.0, 0.0), 58)         # 쇼 당일 (런웨이 끝)
camera(C_CAM, 'cam_showtop', (5.5, 3.4, -3.0), (-12.0, 0.3, 0.5), 66)
scene.camera = bpy.data.objects['cam_exhibit']
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
print('localpower built:', {c.name: len(c.objects) for c in (C_STATIC, C_DYNAMIC, C_EMIT, C_LIGHT, C_CAM)})
