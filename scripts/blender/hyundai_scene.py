"""현대 모터스튜디오 서울 — 현대자동차 1억 대 생산 기념 전시 〈다시, 첫걸음 / One step further〉 (2024.10~12)

  python3 scripts/blender/bmcp.py exec scripts/blender/hyundai_scene.py

자료 (assets-src/refs/hyundai/: index.md, building_layout.md/json, exhibition_layout.md/json, 사진 약 170장):
- 건물: 언주로 738 (도산대로 × 언주로 남동 모서리). 서아키텍스 2014 리노베이션. 건축물대장 기준층 458㎡ ·
  평면 축척 0.035m/px (대장 면적·OSM·카카오 정사영상·프릿 입면·계단 단높이 다섯 가지로 교차 확인).
  1F 0 · 2F(메자닌) 3.75 · 3F 7.65 · 4F 12.63 · 5F 17.61 · 6F 22.59 · 지붕 27.57 · 파라펫 29.6.
  45° 모따기 유리면(12.87m)이 도산사거리를 보고, 북면 = 도산대로(입구), 서면 = 언주로.
  1~2층 7.65m 보이드 · 모따기 안쪽 0.55m 대형 스크린(11.2 × 3.95m, +3.15~+7.10) · 모따기와 나란한 직선 계단(28단).
  천장 = 아연도 강관 루버(모따기와 나란히), 기둥 = 세로 강관 링, 코어 = 짙은 화강석, 바닥 = 연마 콘크리트.
  유리: 층마다 한 장, 3~6층은 슬래브 높이로 점 프릿이 짙어짐(흰 띠), 로테이터 앞은 비움.
- 전시 (층별): 1F 코티나 Mk2(청록)·포니 에콰도르 택시(노랑)·'경 100,000,001대 생산 축' 아치·천장 컨베이어(노란 걸이 24개 1:4 차체)
  · 아카이브 카운터·미니카 장·컬렉션 벽감 / 2F 파울바셋 카페 + 어두운 방(벽 전시 3개·디오라마 2개·C자 사진 테이블)
  / 3F 쏘나타 Y1·스쿠프·엘란트라 + 조명 박스·알파 엔진·파란 리본 벽·1980년대 설계실
  / 4F 싼타페·코나 일렉트릭·캐스퍼 일렉트릭(파란 바닥·배경) + 캠핑 소품·곡면 아카이브 / 5F 아이오닉 5·5 N라인·6 + 충전기·빈백.
좌표 (웹 Y-up): 원점 = 기준층 윤곽 중심, 1F 바닥. +x ENE(도산대로와 나란히), -z NNW(도산대로 쪽), +z SSE.
"""
import importlib
import json
import math
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
import props  # noqa: E402
importlib.reload(gallery)
importlib.reload(props)
from gallery import srgb  # noqa: E402

REFS = '/Users/hare/Documents/큐비크스홈페이지/assets-src/refs/hyundai'
B = json.load(open(f'{REFS}/building_layout.json'))
L2 = json.load(open(f'{REFS}/layout_v2.json'))                  # 2차 실측 (layout_v2.md §1 교정표)
B['main_stair_1F_2F']['bottom_xz'] = L2['main_stair_1F_2F']['bottom_1F_xz']     # 계단 방향이 반대였다
B['main_stair_1F_2F']['top_xz'] = L2['main_stair_1F_2F']['top_landing_2F_xz']
B['screen']['bottom_m'] = L2['screen']['bottom_m']
B['screen']['top_m'] = L2['screen']['top_m']
B['screen']['height_m'] = L2['screen']['height_m']
E = json.load(open(f'{REFS}/exhibition_layout.json'))
random.seed(7)
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

LV = {k: B['levels_m'][k] for k in ('1F', '2F', '3F', '4F', '5F', '6F', 'roof')}
PARAPET = B['levels_m']['parapet_top']
SLAB_T = 0.35
TYP = [tuple(p) for p in B['floors']['3F']['outline_xz']]
OUT1 = [tuple(p) for p in B['floors']['1F']['outline_xz']]
VOID = [tuple(p) for p in B['floors']['2F']['void_xz']]


def tex(name, **kw):
    import os
    p = f'{SHOTS}/{name}.png'
    return p if os.path.exists(p) else None


def gm(slug, emit=0.0, fallback=(0.5, 0.5, 0.5)):
    p = tex(f'hy_t_{slug}')
    if p is None:
        print('texture missing:', slug)
        return material(f'hyMissing_{slug}', None, fallback, 0.8)
    if emit:
        return material(f'hyE_{slug}', emit_image=p, emit_strength=emit, rough=0.5)
    return material(f'hyG_{slug}', image_base=p, rough=0.6)


M = {
    'floor': material('hyFloor', image_base=f'{SHOTS}/hy_t_floor_concrete.png', color=(0.55, 0.55, 0.54), rough=0.22),   # 연마 콘크리트 (사진보다 밝던 것을 낮춤)
    'slabEdge': material('hySlabEdge', None, (0.05, 0.05, 0.055), 0.7),
    'slabUnder': material('hySlabUnder', None, (0.02, 0.02, 0.022), 0.8),           # 강관 루버 위 검은 슬래브
    'soffit': material('hySoffit', None, (0.78, 0.78, 0.77), 0.85),                # 메자닌 아래 평평한 석고 천장
    'pipe': material('hyPipe', None, (0.6, 0.62, 0.64), 0.45, 0.55),                # 아연도 강관 (무광, 사진)
    'pipeDark': material('hyPipeDark', None, (0.16, 0.16, 0.17), 0.4, 0.6),        # 3~5층 천장 강관 (사진: 짙은 회색)
    'stone': material('hyStone', image_base=f'{SHOTS}/hy_t_stone_core.png', rough=0.45),                    # 인산염 코팅 강판 (아연 결정 무늬) 코어
    'render': material('hyRender', None, (0.86, 0.86, 0.84), 0.8),                  # 남쪽 흰 미장
    'glass': material('hyGlass', None, (0.82, 0.88, 0.9), 0.02, transmission=1.0),
    'mullion': material('hyMullion', None, (0.25, 0.26, 0.28), 0.4, 0.7),
    'frit': material('hyFrit', None, (0.9, 0.9, 0.9), 0.6),                          # 슬래브 앞 짙은 점 프릿 띠
    'column': material('hyColumn', None, (0.3, 0.31, 0.33), 0.5, 0.5),
    'black': material('hyBlack', None, (0.012, 0.012, 0.015), 0.5),
    'chrome': material('hyChrome', None, (0.9, 0.9, 0.92), 0.12, 1.0),
    'steelGrey': material('hySteelGrey', None, (0.2, 0.21, 0.22), 0.45, 0.5),
    'aluRail': material('hyAluRail', None, (0.6, 0.61, 0.63), 0.35, 0.8),
    'cage': material('hyCage', None, srgb('#F4C430'), 0.45),
    'ledStrip': material('hyLedStrip', None, (1, 1, 1), emit=(1.0, 0.97, 0.92), emit_strength=14),
    'tube': material('hyTube', None, (1, 1, 1), emit=(1.0, 0.96, 0.9), emit_strength=6),
    'lightbox': material('hyLightbox', None, (1, 1, 1), emit=(0.96, 0.98, 1.0), emit_strength=2.2),
    'lampLens': material('hyLampLens', None, (1, 1, 1), emit=(1.0, 0.93, 0.82), emit_strength=30),
    'walnut': material('hyWalnut', 'dark_wooden_planks', (0.55, 0.38, 0.25), 0.5),
    'greyMat': material('hyGreyMat', None, (0.3, 0.3, 0.3), 0.9),
    'blueFloor': material('hyBlueFloor', None, (0.015, 0.03, 0.14), 0.6),                # 무광 남색 매트 (사진)
    'blueWall': material('hyBlueWall', None, (0.02, 0.05, 0.33), 0.6),
    'ribbon': material('hyRibbon', None, srgb('#1C2F8F'), 0.4, 0.3),
    'carpetDark': material('hyCarpetDark', None, (0.03, 0.03, 0.035), 0.95),
    'fabricDark': material('hyFabricDark', None, (0.05, 0.05, 0.055), 0.9),
    'white': material('hyWhite', None, (0.86, 0.86, 0.84), 0.7),
    'lightGrey': material('hyLightGrey', None, (0.36, 0.37, 0.37), 0.7),
    'perf': material('hyPerf', None, (0.7, 0.71, 0.72), 0.35, 0.8),
    'hazard': material('hyHazard', None, (0.9, 0.75, 0.05), 0.5),
    'road': material('hyRoad', None, (0.13, 0.13, 0.14), 0.9),
    'walk': material('hyWalk', None, (0.5, 0.49, 0.47), 0.85),
    'nbr': material('hyNbr', None, (0.55, 0.55, 0.54), 0.85),
    'glassDark': material('hyGlassDark', None, (0.05, 0.06, 0.07), 0.15, 0.3),
    'archNavy': material('hyArchNavy', None, srgb('#2A2D5C'), 0.5),
    'cream': material('hyCream', None, (0.62, 0.48, 0.18), 0.55),                   # 설계실 책상 (연노랑)
    'creamWall': material('hyCreamWall', None, (0.5, 0.45, 0.3), 0.8),
    'paleGreen': material('hyPaleGreen', None, (0.45, 0.55, 0.47), 0.55),
    'greyGreen': material('hyGreyGreen', None, (0.32, 0.37, 0.34), 0.55),
    'vinyl': material('hyVinyl', None, (0.42, 0.36, 0.24), 0.6),
    'paper': material('hyPaper', None, (0.9, 0.89, 0.85), 0.8),
}

bld = Assembly('building', C_STATIC)      # 슬래브·코어·기둥·파사드 틀
glass = Assembly('glass', C_DYNAMIC)
ceil = Assembly('ceilings', C_STATIC)     # 강관 루버 (정적, 베이크)
site = Assembly('site', C_STATIC)
expo = Assembly('exhibits', C_STATIC)
emit = Assembly('emissive', C_EMIT)
rig = Assembly('rig', C_DYNAMIC)          # 컨베이어·걸이 (움직이는 느낌의 금속)


# ── 도형 유틸 ─────────────────────────────────────────────────
def prism(asm, pts, y0, y1, mat, tile=2.0, top=True, bottom=True, sides=True, side_mat=None):
    """평면 다각형(xz)을 y0~y1 로 세운 입체 (오목 가능)"""
    def build(bm):
        n = len(pts)
        lo = [bm.verts.new((x, y0, z)) for x, z in pts]
        hi = [bm.verts.new((x, y1, z)) for x, z in pts]
        fs = []
        if top:
            fs.append(bm.faces.new(hi))
        if bottom:
            fs.append(bm.faces.new(list(reversed(lo))))
        if sides:
            for i in range(n):
                j = (i + 1) % n
                f = bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
                f.material_index = 1 if side_mat else 0
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        big = [f for f in bm.faces if len(f.verts) > 4]
        if big:
            bmesh.ops.triangulate(bm, faces=big)
    asm.add(build, T(), [mat, side_mat] if side_mat else mat, tile)


def seg_frame(a, b):
    d = V((b[0] - a[0], 0, b[1] - a[1]))
    return T((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2, math.atan2(-d.z, d.x)), d.length


def inward(a, b):
    """변 a→b 의 로컬 +z 가 건물 안쪽이면 1, 바깥이면 -1"""
    d = V((b[0] - a[0], 0, b[1] - a[1]))
    n = V((-d.z, 0, d.x))
    m = V(((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2))
    return 1 if n.dot(V((1.0, 0, 1.0)) - m) > 0 else -1


def clip_line(poly, p0, dvec):
    """무한 직선 p0 + t·d 와 다각형의 교차 구간들 [(t0, t1)]"""
    ts = []
    n = len(poly)
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        ex, ez = bx - ax, bz - az
        den = dvec[0] * ez - dvec[1] * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - p0[0]) * ez - (az - p0[1]) * ex) / den
        u = ((ax - p0[0]) * dvec[1] - (az - p0[1]) * dvec[0]) / den
        if 0 <= u < 1:
            ts.append(t)
    ts.sort()
    return [(ts[k], ts[k + 1]) for k in range(0, len(ts) - 1, 2)]


def inset(poly, d):
    """볼록·오목 다각형을 d 만큼 안으로 (단순 이등분선 방식)"""
    n = len(poly)
    out = []
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1 if area > 0 else -1
    for i in range(n):
        a, b, c = V((*poly[i - 1], 0)), V((*poly[i], 0)), V((*poly[(i + 1) % n], 0))
        e1 = (b - a).normalized()
        e2 = (c - b).normalized()
        n1 = V((-e1.y, e1.x, 0)) * s
        n2 = V((-e2.y, e2.x, 0)) * s
        m = (n1 + n2).normalized()
        k = d / max(0.3, m.dot(n1))
        out.append((b.x + m.x * k, b.y + m.y * k))
    return out


# ── 슬래브 ──────────────────────────────────────────────────
prism(bld, OUT1, -0.4, 0.0, M['floor'], 1.8, side_mat=M['slabEdge'])
# 2F 메자닌: 기준층 윤곽에서 모따기 쪽 보이드를 도려낸 한 다각형
SLAB2 = [(-11.454, 4.17)] + [VOID[i] for i in (6, 5, 4, 3, 2)] + [TYP[1], TYP[2], TYP[3], TYP[4], TYP[5], TYP[6], TYP[7], TYP[8], TYP[9]]
prism(bld, SLAB2, LV['2F'] - SLAB_T, LV['2F'], M['floor'], 1.8, side_mat=M['slabEdge'])
for f in ('3F', '4F', '5F', '6F', 'roof'):
    prism(bld, TYP, LV[f] - SLAB_T, LV[f], M['floor'] if f != 'roof' else M['slabEdge'], 1.8, side_mat=M['slabEdge'])
# 옥상 파라펫
for (a, b) in zip(TYP, TYP[1:] + TYP[:1]):
    fr, L = seg_frame(a, b)
    bld.add(box(L + 0.3, PARAPET - LV['roof'], 0.3), fr @ T(0, LV['roof'] + (PARAPET - LV['roof']) / 2, 0), M['render'], 2)

# ── 코어 (카리프트·계단·엘리베이터·화장실): 짙은 화강석 ─────────────────
CORE = B['core']
# 코어는 4cm 키워 슬래브 옆면을 덮는다 (같은 면 겹침 방지)
prism(bld, inset([tuple(p) for p in CORE['car_lift']['shaft_xz']], -0.04), -0.4, LV['roof'] + 2.0, M['stone'], 0.92)
prism(bld, inset([tuple(p) for p in CORE['stair_core']['outline_xz']], -0.04), -0.4, LV['roof'] + 2.0, M['stone'], 0.92)
prism(bld, inset([tuple(p) for p in CORE['lift_block_outline_xz']], -0.04), -0.4, LV['roof'] + 2.0, M['stone'], 0.92)
TOIL = [tuple(p) for p in CORE['toilets_3F_5F_xz']]
prism(bld, inset(TOIL, -0.04), LV['2F'], LV['roof'] + 0.05, M['stone'], 0.92)
# 카리프트 문 (북쪽 면, CARS ONLY + 검흰 빗금 띠) 층마다
door = CORE['car_lift']['door']
for f in ('1F', '3F', '4F', '5F'):
    y = LV[f]
    fr = T(door['centre_x'], y, -3.6 - 0.1, PI)
    gallery._face(expo, fr, door['width_m'], door['height_m'], M['pipe'], [(0, 1.05, door['width_m'], 1.6, gm('carlift_door'))], 1)
# 엘리베이터 문 (아연도)
for pl in CORE['passenger_lifts']:
    cx, cz = pl['centre_xz']
    for f in ('1F', '2F', '3F', '4F', '5F'):
        fr = T(cx - 1.05 * math.cos(PI / 4) - 0.01, LV[f], cz - 1.05 * math.sin(PI / 4) - 0.01, -PI / 4 - PI / 2)
        expo.add(plane(1.0, 2.3), fr @ T(0, 1.15, -0.08), M['pipe'], 1)

# ── 기둥: H형강 + (C1·C3·C4·C5) 세로 강관 링 ───────────────────────
for cid, c in B['columns'].items():
    x, z = c['xz']
    bld.add(box(0.4, LV['roof'], 0.4), T(x, LV['roof'] / 2 - 0.4, z), M['column'], 1)
    if cid in ('C1', 'C3', 'C4', 'C5'):
        for f0, f1 in (('1F', '3F'), ('3F', '4F'), ('4F', '5F'), ('5F', '6F')):
            y0, y1 = LV[f0], LV[f1] - SLAB_T
            for k in range(20):
                a = k / 20 * 2 * PI
                g, m = tube(V((x + math.cos(a) * 0.4, y0, z + math.sin(a) * 0.4)), V((x + math.cos(a) * 0.4, y1, z + math.sin(a) * 0.4)), 0.024, 6)
                ceil.add(g, m, M['pipe'])

# ── 강관 루버 천장 (모따기와 나란히 45°, 피치 약 0.15m) ─────────────────
CH_D = (0.714, -0.700)        # 모따기 방향
CH_N = (0.700, 0.714)         # 안쪽 법선


def pipe_ceiling(poly, y, pitch=0.105, r=0.025, battens=True, mat='pipe'):
    ins = inset(poly, 0.15)
    for k in range(-240, 240):
        off = k * pitch
        p0 = (CH_N[0] * off, CH_N[1] * off)
        for (t0, t1) in clip_line(ins, p0, CH_D):
            a = V((p0[0] + CH_D[0] * t0, y, p0[1] + CH_D[1] * t0))
            b = V((p0[0] + CH_D[0] * t1, y, p0[1] + CH_D[1] * t1))
            if (b - a).length > 0.3:
                g, m = tube(a, b, r, 6)
                ceil.add(g, m, M[mat])
    # LED 바: 강관과 직교, 2.4m 간격
    if battens:
        for k in range(-6, 6):
            off = k * 4.8
            p0 = (CH_D[0] * off, CH_D[1] * off)
            for (t0, t1) in clip_line(ins, p0, CH_N):
                a = V((p0[0] + CH_N[0] * t0, y - 0.05, p0[1] + CH_N[1] * t0))
                b = V((p0[0] + CH_N[0] * t1, y - 0.05, p0[1] + CH_N[1] * t1))
                L = (b - a).length
                if L > 0.5:
                    mid = (a + b) / 2
                    ang = math.atan2(-CH_N[1], CH_N[0])
                    emit.add(cyl(0.026, 0.026, L, 10), T(mid.x, mid.y - 0.06, mid.z, ang, 0, PI / 2), M['tube'])
                    for e_ in (-1, 1):                       # 매다는 가는 봉
                        pt = a + (b - a) * (0.5 + e_ * 0.42)
                        g2, m2 = tube(V((pt.x, y + 0.02, pt.z)), V((pt.x, y - 0.06, pt.z)), 0.008, 5)
                        rig.add(g2, m2, M['black'])


# 1F 보이드 천장(+7.1) + 메자닌 아래(+3.25), 3~5F(FL+4.2)
pipe_ceiling(VOID, 7.1)
UNDER2 = [(-11.349, 4.17), (-6.729, 4.17), (-3.719, 3.26), (2.756, -2.97), (3.771, -3.88), (-2.144, -11.37), (10.736, -11.37),
          (10.736, 3.61), (5.906, 3.61), (0.026, 9.385), (-11.349, 9.385)]
# 메자닌 아래는 강관 루버가 아니라 평평한 연한 석고 천장 + 표면부착 라인 조명 (layout_v2 §1-4)
prism(ceil, inset(UNDER2, 0.05), 3.25, 3.27, M['soffit'], 3, top=False, sides=False)
for k in range(-10, 10):
    off = k * 2.6
    p0 = (CH_D[0] * off, CH_D[1] * off)
    for (t0, t1) in clip_line(inset(UNDER2, 0.6), p0, CH_N):
        a = V((p0[0] + CH_N[0] * t0, 3.22, p0[1] + CH_N[1] * t0))
        b = V((p0[0] + CH_N[0] * t1, 3.22, p0[1] + CH_N[1] * t1))
        Lb = (b - a).length
        if Lb > 0.8:
            mid = (a + b) / 2
            emit.add(box(Lb - 0.2, 0.04, 0.07), T(mid.x, mid.y, mid.z, math.atan2(-CH_N[1], CH_N[0])), M['ledStrip'])
for f in ('3F', '4F', '5F'):
    pipe_ceiling(TYP, LV[f] + 4.2, mat='pipeDark')
    prism(ceil, inset(TYP, 0.1), LV[f] + 4.35, LV[f] + 4.36, M['slabUnder'], 3, top=False, sides=False)

# ── 유리 커튼월 (층마다 한 장, 모듈 약 2.13m 멀리언) + 슬래브 앞 흰 프릿 띠 ─────────
ROT = B['rotators_3F_5F']


def curtain(a, b, y0, y1, module=2.13, rot_windows=()):
    fr, L = seg_frame(a, b)
    si = inward(a, b)
    n = max(1, round(L / module))
    glass.add(plane(L, y1 - y0), fr @ T(0, (y0 + y1) / 2, -0.08 * si), M['glass'], 2)     # 슬래브 앞 8cm (바깥)
    for k in range(n + 1):
        u = -L / 2 + k * L / n
        bld.add(box(0.06, y1 - y0, 0.12), fr @ T(u, (y0 + y1) / 2, -0.02 * si), M['mullion'], 1)
    return fr, L


FACADE = {s_['id']: s_ for s_ in B['facade']['segments'] if 'from_xz' in s_}
for fid in ('chamfer', 'north', 'west', 'east'):
    s_ = FACADE[fid]
    a, b = tuple(s_['from_xz']), tuple(s_['to_xz'])
    if fid == 'north':
        # 1F 는 x ≤ 10.7 까지만 유리 (동쪽 3m 는 들어간 차로)
        curtain(a, (10.736, b[1]), LV['1F'], LV['2F'] - SLAB_T)
        curtain(a, b, LV['2F'], PARAPET)
    elif fid == 'west':
        curtain(a, (a[0], 9.385), LV['1F'], LV['2F'] - SLAB_T)
        curtain(a, b, LV['2F'], PARAPET)
    elif fid == 'east':
        curtain(a, b, LV['2F'], PARAPET)
    else:
        curtain(a, b, LV['1F'], PARAPET)
    # 3~6층 슬래브 앞 짙은 프릿 띠 (FL+3.9 ~ 다음 층 FL+0.1), 파라펫 띠
    fr, L = seg_frame(a, b)
    si = inward(a, b)
    for f, nxt in (('2F', '3F'), ('3F', '4F'), ('4F', '5F'), ('5F', '6F'), ('6F', 'roof')):
        y0, y1 = LV[nxt] - 1.0, LV[nxt] + 0.1
        bld.add(box(L - 0.4, y1 - y0, 0.04), fr @ T(0, (y0 + y1) / 2, 0.1 * si), M['frit'], 2)
    bld.add(box(L - 0.4, PARAPET - LV['roof'] + 0.1, 0.04), fr @ T(0, (LV['roof'] + PARAPET) / 2 - 0.15, 0.1 * si), M['frit'], 2)
# 1F 동쪽·남쪽 들어간 벽 (차로·남쪽 마당) + 2F 이상 남쪽 흰 미장 벽 (층마다 가로 창)
for (a, b) in ((( 10.736, -11.37), (10.736, 3.61)), ((10.736, 3.61), (5.906, 3.61)), ((5.906, 3.61), (0.026, 9.385)), ((0.026, 9.385), (-4.0, 9.385))):
    fr, L = seg_frame(a, b)
    bld.add(box(L, LV['2F'] - SLAB_T, 0.3), fr @ T(0, (LV['2F'] - SLAB_T) / 2, -0.15), M['render'], 2)
curtain((-4.0, 9.385), (-11.349, 9.385), LV['1F'], LV['2F'] - SLAB_T)     # 남쪽 유리 문 쪽
for (a, b) in (((13.711, -1.22), (10.701, -1.22)), ((10.701, -1.22), (10.701, 3.365)), ((2.651, 13.41), (-4.4, 13.41))):
    fr, L = seg_frame(a, b)
    bld.add(box(L, PARAPET - LV['2F'], 0.3), fr @ T(0, (LV['2F'] + PARAPET) / 2, -0.15), M['render'], 2)
curtain((-4.4, 13.41), (-11.454, 13.41), LV['2F'], PARAPET)
for f in ('3F', '4F', '5F', '6F'):
    fr, L = seg_frame((2.651, 13.41), (-4.4, 13.41))
    bld.add(box(4.2, 0.35, 0.44), fr @ T(0, LV[f] + 1.6, -0.15), M['glassDark'], 1)

# ── 1F→2F 직선 계단 (모따기와 나란히, 28단) + 강관 난간 ─────────────────
ST = B['main_stair_1F_2F']
sb, st_ = V((*ST['bottom_xz'], 0)), V((*ST['top_xz'], 0))
sd = V((st_.x - sb.x, st_.y - sb.y, 0))
L_run = sd.length
sd.normalize()
ry_st = math.atan2(-sd.y, sd.x)
nr = 28
for i in range(nr):
    t0 = i / nr * (L_run - 1.2)
    p = sb + sd * (t0 + 0.15)
    y = (i + 1) * LV['2F'] / (nr + 1)
    bld.add(box(0.30, 0.04, 1.4), T(p.x, y - 0.02, p.y, ry_st), M['steelGrey'], 1)
    bld.add(box(0.012, LV['2F'] / (nr + 1), 1.4), T(p.x - sd.x * 0.15, y - LV['2F'] / (nr + 1) / 2, p.y - sd.y * 0.15, ry_st), M['steelGrey'], 1)
land = sb + sd * (L_run - 0.6)
bld.add(box(1.2, 0.2, 1.4), T(land.x, LV['2F'] - 0.1, land.y, ry_st), M['steelGrey'], 1)
side = V((-sd.y, sd.x, 0))
for sgn in (-1, 1):                                                      # 계단 옆 판 + 강관 난간 5줄
    a0 = sb + side * sgn * 0.72
    a1 = st_ + side * sgn * 0.72
    for k in range(6):
        h = 0.22 + k * 0.178
        g, m = tube(V((a0.x, h, a0.y)), V((a1.x, LV['2F'] + h, a1.y)), 0.02, 6)
        rig.add(g, m, M['pipe'])
    for k in range(6):
        q = a0 + (a1 - a0) * (k / 5)
        yy = LV['2F'] * k / 5
        g, m = tube(V((q.x, yy, q.y)), V((q.x, yy + 1.1, q.y)), 0.018, 6)
        rig.add(g, m, M['pipe'])
# 계단 밑면: 가로 강관
for k in range(40):
    t_ = k / 40
    p = sb + sd * (t_ * L_run)
    y = LV['2F'] * t_ - 0.08
    g, m = tube(V((p.x - side.x * 0.7, y, p.y - side.y * 0.7)), V((p.x + side.x * 0.7, y, p.y + side.y * 0.7)), 0.018, 6)
    ceil.add(g, m, M['pipe'])


# ── 2F 보이드 가장자리 강관 난간 (1.1m, 가로 5줄) ─────────────────────
def pipe_rail(a, b, y, rails=5, h=1.1, asm=None):
    asm = asm or rig
    A, Bv = V((a[0], y, a[1])), V((b[0], y, b[1]))
    for k in range(rails):
        hh = 0.2 + k * (h - 0.2) / (rails - 1)
        g, m = tube(A + V((0, hh, 0)), Bv + V((0, hh, 0)), 0.02, 6)
        asm.add(g, m, M['pipe'])
    L = (Bv - A).length
    for k in range(int(L / 1.2) + 2):
        q = A.lerp(Bv, min(1, k * 1.2 / L))
        asm.add(box(0.04, h, 0.012), T(q.x, y + h / 2, q.z), M['pipe'], 1)


for i in (6, 5, 4):
    pipe_rail(VOID[i], VOID[i - 1], LV['2F'])
pipe_rail(VOID[3], VOID[2], LV['2F'])

# ── 대형 스크린 (모따기 안쪽 0.55m, 11.2 × 3.95m, +3.15~+7.10) ─────────────
SC = B['screen']
scx, scz = SC['centre_xz']
fx, fz = SC['facing_dir_xz']
ry_sc = math.atan2(fx, fz)
sf = T(scx, 0, scz, ry_sc)
bld.add(box(SC['width_m'] + 0.2, SC['height_m'] + 0.2, 0.25), sf @ T(0, (SC['bottom_m'] + SC['top_m']) / 2, -0.17), M['black'], 1)
emit.add(plane(SC['width_m'], SC['height_m']), sf @ T(0, (SC['bottom_m'] + SC['top_m']) / 2, 0.0), gm('mediawall_production', 2.2), tile=None)
light(C_LIGHT, 'screen_glow', 'AREA', tuple(sf @ V((0, 5.1, 1.0))), tuple(sf @ V((0, 3.0, 6.0))), energy=900, color=(0.85, 0.9, 1.0), size=8)

# 2024 전시 그래픽: 모따기 유리 바깥면 흰 글씨 (투명 배경 → 알파 카드)
chA, chB = tuple(FACADE['chamfer']['from_xz']), tuple(FACADE['chamfer']['to_xz'])
cfr, cL = seg_frame(chA, chB)
glass.add(plane(7.3, 2.72), cfr @ T(0.5, 5.2, -0.16 * inward(chA, chB)) @ T(0, 0, 0, PI if inward(chA, chB) > 0 else 0),
          material('hyExtGraphic', image_base=f'{SHOTS}/hy_t_ext_exhibition_graphic.png', rough=0.5, alpha=True), tile=None)
emit.add(plane(1.95, 0.82), T(9.6, 3.1, -11.3, PI), material('hyNeon', emit_image=f'{SHOTS}/hy_t_sign_motorstudio_neon.png', emit_strength=2.0), tile=None)

# ── 출입구 ────────────────────────────────────────────────────
nv = B['entrances']['north_vestibule']
vx, vz = nv['xz_centre']
for k in range(22):                                                    # 세로 강관 가림 (전실)
    x = vx - 2.1 + k * 0.2
    g, m = tube(V((x, 0, -11.9)), V((x, 3.3, -11.9)), 0.024, 6)
    ceil.add(g, m, M['pipe'])
site.add(box(4.4, 0.15, 1.2), T(vx, -0.25, -12.5), M['walk'], 1)
site.add(box(4.4, 0.15, 0.6), T(vx, -0.1, -12.2), M['walk'], 1)

# ── 주변: 도산대로(북)·언주로(서)·보도·이웃 건물 매스 ─────────────────────
site.add(box(80.0, 0.1, 5.0), T(0.0, -0.5, -14.6), M['walk'], 2)                  # 북쪽 보도
site.add(box(80.0, 0.1, 22.0), T(0.0, -0.55, -28.0), M['road'], 4)                # 도산대로 (왕복 8차로)
site.add(box(5.0, 0.1, 40.0), T(-14.4, -0.5, 6.0), M['walk'], 2)                  # 서쪽 보도
site.add(box(16.0, 0.1, 40.0), T(-25.0, -0.55, 6.0), M['road'], 4)                # 언주로
for k in range(12):                                                    # 차선
    site.add(box(3.0, 0.02, 0.15), T(-36 + k * 6.5, -0.49, -28.0), M['white'], 1)
    site.add(box(0.15, 0.02, 3.0), T(-25.0, -0.49, -12 + k * 5), M['white'], 1)
prism(site, [(13.9, -11.8), (28.0, -11.8), (28.0, 14.0), (13.9, 14.0)], -0.5, 18.0, M['nbr'], 3)     # 동쪽 이웃
prism(site, [(-11.9, 15.8), (13.9, 15.8), (13.9, 28.0), (-11.9, 28.0)], -0.5, 14.0, M['nbr'], 3)     # 남쪽 이웃
site.add(box(26.0, 0.1, 2.3), T(1.0, -0.45, 14.6), M['walk'], 2)                 # 남쪽 마당

# ══ 전시 ═══════════════════════════════════════════════════════
import numpy as np  # noqa: E402
X1, X3, X4, X5 = E['1F'], E['3F'], E['4F'], E['5F']
DEG = PI / 180


def align_long_axis(obj):
    """긴 축(평면 주성분)을 Blender X 로, 바닥 중심을 원점으로"""
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    p = co.reshape(-1, 3)
    xy = p[:, :2] - p[:, :2].mean(0)
    cxx, cyy, cxy = (xy[:, 0] ** 2).mean(), (xy[:, 1] ** 2).mean(), (xy[:, 0] * xy[:, 1]).mean()
    ang = 0.5 * math.atan2(2 * cxy, cxx - cyy)
    c_, s_ = math.cos(-ang), math.sin(-ang)
    x2, y2 = p[:, 0] * c_ - p[:, 1] * s_, p[:, 0] * s_ + p[:, 1] * c_
    p[:, 0] = x2 - (x2.min() + x2.max()) / 2
    p[:, 1] = y2 - (y2.min() + y2.max()) / 2
    p[:, 2] -= p[:, 2].min()
    me.vertices.foreach_set('co', p.ravel())
    me.update()
    return obj


# 차량 모델 (CC BY, CREDITS.md · refs/hyundai/car_models.md). 정확한 CC 모델이 없는 차종은 같은 차급·같은 시대 대체.
CARS = {
    'cortina':  dict(uid='31200fbcff0c4f2d80c24f81a786b594', length=4.27, color='#1FA7B0'),                      # VAZ-2101 (코티나 Mk2 대체)
    'pony':     dict(uid='04b1bede9039489eb7a8695e33e9e35a', length=3.97, decimate=0.08, retint='#FFC61A', flip=True),   # 포니1 택시 (실차, 에콰도르 택시 노랑)
    'sonata':   dict(uid='66697669831b47cea7874fc8c4544e74', length=4.695, color='#B9A98A', match='main_body',
                     keep=lambda co, mid: co.x < mid.x, drop=('body2',)),                                     # 볼보 240 (쏘나타 Y1 대체)
    'scoupe':   dict(uid='154f19805fbb4957b6aae8e3b23f9471', length=4.125, color='#A5121E', match='carpaint', decimate=0.08, flip=True),   # 칼리브라
    'elantra':  dict(uid='2b30faa611e64177a94a69098d27d1fb', length=4.37, color='#4A1622', decimate=0.25),                    # 코롤라 KE80
    'santafe':  dict(uid='26f042fcf1594890a529bfb41f0fae0d', length=4.83, color='#E9E9E6', match='body', decimate=0.2),        # 디펜더 (MX5 대체)
    'kona':     dict(uid='20896e8928d943dabcaaf67dbb53c9da', length=4.36, color='#9FB4A7', match='ceramicblue', decimate=0.25),  # 코나 EV 1세대
    'casper':   dict(uid='e6a63979813c4ee8953a740f05aa3d9e', length=3.83, color='#E2DFB4', match='material.015', decimate=0.03),  # 왜건R
    'ioniq5':   dict(uid='8d5fd459a54d4a529c2be4c7ac444b01', length=4.65, color='#DADCDC', match='varnish'),                      # 미니 컨트리맨
    'ioniq5n':  dict(uid='8d5fd459a54d4a529c2be4c7ac444b01', length=4.65, color='#6E7275', match='varnish'),
    'ioniq6':   dict(uid='3a602469d7874d1397efa67182198705', length=4.86, color='#B8BCBF', match='carpaint', decimate=0.25),     # 모델 3
}
_SRC = {}


def car_src(key):
    c = CARS[key]
    tag = f"{c['uid']}_{key}"
    if tag in _SRC:
        return _SRC[tag]
    o = props.load(c['uid'], f'src_car_{key}', decimate=c.get('decimate'), coll=C_SRC)
    if c.get('keep') or c.get('drop'):
        bm_ = bmesh.new()
        bm_.from_mesh(o.data)
        xs = [v.co.x for v in bm_.verts]
        mid = V(((min(xs) + max(xs)) / 2, 0, 0))
        drop_idx = [i for i, m in enumerate(o.data.materials) if m and any(d in m.name.lower() for d in c.get('drop', ()))]
        bad = [f for f in bm_.faces if f.material_index in drop_idx or (c.get('keep') and not c['keep'](f.calc_center_median(), mid))]
        bmesh.ops.delete(bm_, geom=bad, context='FACES')
        bm_.to_mesh(o.data)
        bm_.free()
    align_long_axis(o)
    L = o.dimensions.x
    k = c['length'] / L
    o.data.transform(__import__('mathutils').Matrix.Diagonal((k, k, k, 1)))
    o.data.update()
    if c.get('color'):
        o = props.set_material_color(o, c.get('match', 'auto'), srgb(c['color']), key)
    if c.get('retint'):
        o = props.retint(o, srgb(c['retint']), key)
    _SRC[tag] = o
    return o


def place_car(key, x, y, z, yaw_deg, name):
    src = car_src(key)
    ry = yaw_deg * DEG + (PI if CARS[key].get('flip') else 0)
    instance(src, C_DYNAMIC, name, T(x, y, z, ry))


def stanchion_rect(asm, cx, cz, w, d, yaw, y=0.0, posts=8):
    f = T(cx, y, cz, yaw)
    corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    pts = []
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        for k in range(posts // 4):
            t_ = k / (posts // 4)
            pts.append((a[0] + (b[0] - a[0]) * t_, a[1] + (b[1] - a[1]) * t_))
    W_ = [f @ V((px, 0, pz)) for px, pz in pts]
    for p in W_:
        asm.add(cyl(0.15, 0.15, 0.02, 20), T(p.x, y + 0.01, p.z), M['chrome'], 1)
        asm.add(cyl(0.02, 0.02, 0.9, 10), T(p.x, y + 0.46, p.z), M['chrome'], 1)
        asm.add(sphere(0.03, 2), T(p.x, y + 0.92, p.z), M['chrome'])
    for a, b in zip(W_, W_[1:] + W_[:1]):
        g, m = tube(a + V((0, 0.86, 0)), b + V((0, 0.86, 0)), 0.004, 5)
        asm.add(g, m, M['black'])


def rounded_rect(w, d, r, seg=6):
    pts = []
    for (cx, cz, a0) in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(seg + 1):
            a = (a0 + k * 90 / seg) * DEG
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def blob_plan(w, d, seed, n=6):
    """부드러운 자유 곡선 평면 (사진의 천 조명은 둥근 사각형이 아니라 유기적인 덩어리다)"""
    rnd = random.Random(seed)
    pts = [((w / 2) * math.cos(k / n * 2 * PI) * rnd.uniform(0.72, 1.12),
            (d / 2) * math.sin(k / n * 2 * PI) * rnd.uniform(0.72, 1.12)) for k in range(n)]
    for _ in range(3):                                     # 채이킨으로 매끈하게
        q = []
        for i in range(len(pts)):
            p0, p1 = pts[i], pts[(i + 1) % len(pts)]
            q += [(0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1]),
                  (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])]
        pts = q
    return pts


def light_box(cx, cz, yaw_deg, y_under, w=6.4, d=3.4, r=0.9, th=0.32):
    """천을 씌운 대형 백라이트 조명 (아랫면 발광, 평면은 유기적인 자유 형태)"""
    f = T(cx, 0, cz, yaw_deg * DEG)
    pts = [tuple((f @ V((px, 0, pz))).xz) for px, pz in blob_plan(w, d, int(abs(cx) * 100 + abs(cz) * 7 + y_under))]
    pts = [(p[0], p[1]) for p in pts]
    prism(expo, pts, y_under + 0.02, y_under + th, M['white'], 2, bottom=False)
    prism(emit, pts, y_under, y_under + 0.02, M['lightbox'], 2, top=False, sides=False)
    g, m = tube(V((cx, y_under + th, cz)), V((cx, y_under + 0.9, cz)), 0.01, 6)
    rig.add(g, m, M['black'])


def rotator(cx, cz, axis, span, fy, shell_key, backing=True, panel=None):
    """로테이터: 끝을 잡는 A자 기둥 두 개(빗금 피복) + 뒤집힌 하부 셸(아랫면이 방을 봄) + 유리 쪽 어두운 패널"""
    ax, az = axis
    ry = math.atan2(-az, ax)
    f = T(cx, fy, cz, ry)
    for s in (-1, 1):
        post = f @ T(s * span / 2, 0, 0)
        for k in (-1, 1):
            g, m = tube(post @ V((0, 0, k * 0.55)), post @ V((0, 1.55, 0)), 0.06, 8, caps=True)
            expo.add(g, m, M['hazard'])
        expo.add(box(0.3, 0.3, 0.3), post @ T(0, 1.55, 0), M['steelGrey'], 1)
        expo.add(box(0.5, 0.05, 1.3), post @ T(0, 0.025, 0), M['steelGrey'], 1)
    src = car_src(shell_key)
    # 하부가 실내를 보도록 긴 축으로 90° 굴림 (사진: 'DO NOT TOUCH' 기둥 사이 세워진 하부)
    nz = V((math.sin(ry), 0, math.cos(ry)))
    side = 1 if nz.dot(V((-cx, 0, -cz))) > 0 else -1
    h = src.dimensions.z
    instance(src, C_DYNAMIC, f'shell_{shell_key}_{cx:.0f}_{cz:.0f}_{fy:.0f}', f @ T(0, 1.55, 0, 0, -side * PI / 2) @ T(0, -h / 2, 0))
    if backing:
        # 유리 쪽 판: 실내 쪽은 검정, 거리 쪽은 노란 걸이에 매단 차 그림 발광 패널 (야간 외관 사진)
        expo.add(box(span - 0.6, 2.4, 0.05), f @ T(0, 1.55, -side * 1.1), M['black'], 1)
        if panel:
            emit.add(plane(span - 0.7, (span - 0.7) / 2.6), f @ T(0, 1.55, -side * 1.17, PI if side > 0 else 0), gm(panel, 1.4), tile=None)


# ── 1F 〈1억 대의 첫걸음〉 ───────────────────────────────────────
cars1 = X1['cars']
place_car('cortina', *cars1[0]['centre_xz'][:1], 0, cars1[0]['centre_xz'][1], cars1[0]['yaw_deg'], 'car_cortina')
place_car('pony', cars1[1]['centre_xz'][0], 0, cars1[1]['centre_xz'][1], cars1[1]['yaw_deg'], 'car_pony')
for rg in X1['stanchions']['rings']:
    stanchion_rect(expo, *rg['rect_centre_xz'], *rg['size_m'], rg['yaw_deg'] * DEG)
# 택시 지붕등
pc = cars1[1]['centre_xz']
expo.add(bevel_box(0.4, 0.12, 0.22, 0.02), T(pc[0], 1.42, pc[1], 44.4 * DEG + PI / 2), M['cage'], 1)
# 경 100,000,001대 생산 축 아치 (앞뒤 같은 그래픽, 다리 흰 받침)
A = X1['arch_100000001']
af = T(A['centre_xz'][0], 0, A['centre_xz'][1], A['yaw_deg_of_arch_plane_normal'] * DEG + PI / 2)
OW, OH, BW, DP = A['outer_width_m'], A['outer_height_m'], A['band_width_m'], A['depth_m']
for s in (-1, 1):
    expo.add(box(BW + 0.04, 0.3, DP + 0.04), af @ T(s * (OW - BW) / 2, 0.15, 0), M['white'], 1)
    expo.add(box(BW, OH - BW - 0.3, DP), af @ T(s * (OW - BW) / 2, 0.3 + (OH - BW - 0.3) / 2, 0), M['archNavy'], 1)
expo.add(box(OW, BW, DP), af @ T(0, OH - BW / 2, 0), M['archNavy'], 1)
for side, slug in ((1, 'arch_front'), (-1, 'arch_back')):
    fr = af @ T(0, OH / 2 + 0.15, side * (DP / 2 + 0.003), 0 if side > 0 else PI)
    # 그래픽은 아치 모양 그대로: 위 띠 + 두 다리 (텍스처 한 장을 세 조각 UV 로)
    gmat_ = gm(slug)
    H_ = OH - 0.3
    for (u0, u1, v0, v1) in ((0, 1, (H_ - BW) / H_, 1.0), (0, BW / OW, 0, (H_ - BW) / H_), (1 - BW / OW, 1, 0, (H_ - BW) / H_)):
        w_, h_ = (u1 - u0) * OW, (v1 - v0) * H_
        cxl = (u0 + u1) / 2 * OW - OW / 2
        cyl_ = (v0 + v1) / 2 * H_ - H_ / 2
        expo.add(gallery.quad_uv(w_, h_, (u0, v0, u1, v1)), fr @ T(cxl, cyl_, 0), gmat_, tile=None)

# 천장 컨베이어: 폐루프 레일 + 노란 걸이 24개 + 1:4 차체
RP = [V((p[0], p[1], p[2])) for p in X1['conveyor']['rail']['path_xyz']]
for _ in range(2):                                            # 사진의 레일은 꺾이지 않고 부드럽게 휜다
    RP = [RP[0]] + [q for a_, b_ in zip(RP, RP[1:]) for q in (a_ * 0.75 + b_ * 0.25, a_ * 0.25 + b_ * 0.75)] + [RP[-1]]
for a, b in zip(RP, RP[1:]):
    rig.add(box((b - a).length + 0.02, 0.10, 0.055), T((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2,
            math.atan2(-(b.z - a.z), b.x - a.x), 0, math.atan2(b.y - a.y, math.hypot(b.x - a.x, b.z - a.z))), M['aluRail'], 1)
acc_ = 99.0
for a, b in zip(RP, RP[1:]):
    acc_ += (b - a).length
    if acc_ >= 1.6:                                           # 1.6m 간격으로만 천장에 매단다
        acc_ = 0.0
        g, m = tube(a + V((0, 0.05, 0)), V((a.x, 7.1, a.z)), 0.012, 6)
        rig.add(g, m, M['steelGrey'])
BODY_COLS = {'red': '#B81D24', 'white': '#EDEDEB', 'navy/black': '#161A2A', 'silver': '#B8BCC0', 'yellow': '#E8C21C',
             'light blue': '#8EB9D8', 'teal-blue': '#2A7A8C', 'orange-gold': '#C8862A', 'burgundy': '#5C1622',
             'grey': '#6F7275', 'cream': '#E6DDC4', 'orange': '#D8742A', 'black': '#111', 'teal': '#2A8A8C', 'blue': '#2A4FA0'}
body_mats = {}
mini = props.load('edc994ad28ed438cb365c0e0389ac177', 'src_minibody', width=1.05, decimate=0.3, coll=C_SRC)
align_long_axis(mini)
for h in X1['conveyor']['hangers']['items']:
    p = V(h['rail_point_xyz'])
    tx, tz = h['tangent_xz']
    ry = math.atan2(-tz, tx)
    f = T(p.x, p.y - 0.25, p.z, ry)
    g, m = tube(V((p.x, p.y - 0.09, p.z)), V((p.x, p.y - 0.25, p.z)), 0.011, 6)
    rig.add(g, m, M['cage'])
    # 걸이는 상자가 아니라 차체 길이 방향의 납작한 노란 프레임 한 장 + 아래 받침 두 개 (사진)
    for (a_, b_) in (((-0.60, 0.0, 0), (0.60, 0.0, 0)), ((-0.60, 0.0, 0), (-0.60, -0.72, 0)),
                     ((0.60, 0.0, 0), (0.60, -0.72, 0)), ((-0.60, -0.72, 0), (0.60, -0.72, 0)),
                     ((-0.36, -0.72, -0.28), (-0.36, -0.72, 0.28)), ((0.36, -0.72, -0.28), (0.36, -0.72, 0.28))):
        g, m = tube(f @ V(a_), f @ V(b_), 0.009, 6)
        rig.add(g, m, M['cage'])
    col = BODY_COLS.get(h.get('body_colour', 'white'), '#CCCCCC')
    if col not in body_mats:
        body_mats[col] = material(f'hyBody_{col[1:]}', None, srgb(col if len(col) == 7 else '#111111'), 0.35, coat=0.6)
    rig.add(mesh_source(mini), f @ T(0, -0.66, 0), body_mats[col], 1)

# 아카이브 카운터·테이블·굿즈 테이블 (아연도 앵글, 회색 상판, 아크릴 상자)
for t in X1['archive_tables'] + X1['goods_tables']:
    cx, cz = t['centre_xz']
    sx, sy, sz = t['size_m']
    f = T(cx, 0, cz, t.get('yaw_deg', 0) * DEG)
    expo.add(box(sx, 0.04, sz), f @ T(0, 0.88, 0), M['steelGrey'], 1)
    expo.add(box(sx - 0.1, 0.03, sz - 0.1), f @ T(0, 0.3, 0), M['steelGrey'], 1)
    for ex_ in (-1, 1):
        for ez in (-1, 1):
            expo.add(box(0.04, 0.88, 0.04), f @ T(ex_ * (sx / 2 - 0.03), 0.44, ez * (sz / 2 - 0.03)), M['pipe'], 1)
    for k in range(int(sz / 0.8)):
        glass.add(box(min(0.5, sx - 0.2), 0.25, 0.45), f @ T(0, 1.03, -sz / 2 + 0.4 + k * 0.8), M['glass'], 1)
        expo.add(box(min(0.42, sx - 0.25), 0.02, 0.36), f @ T(0, 0.91, -sz / 2 + 0.4 + k * 0.8), M['paper'], 1)
lb = X1['goods_tables'][0]['centre_xz']
gallery.slab_art(expo, T(lb[0], 1.25, lb[1], PI / 2), 1.5, 0.6, 0.02, gm('1f_lineup_board'), M['white'])
# 미니카 장 (아크릴 10 × 12 격자, 약 150대)
mc = X1['minicar_case']
mf = T(mc['centre_xz'][0], 0, mc['centre_xz'][1], PI)
expo.add(box(2.2, 0.9, 0.45), mf @ T(0, 0.45, 0), M['white'], 1)
glass.add(box(2.2, 1.65, 0.3), mf @ T(0, 0.9 + 0.825, 0), M['glass'], 1)
cols_ = ['#B81D24', '#EDEDEB', '#161A2A', '#B8BCC0', '#E8C21C', '#2A4FA0', '#2A8A8C', '#6F7275']
for r_ in range(10):
    for c_ in range(12):
        col = cols_[(r_ * 7 + c_ * 3) % len(cols_)]
        if col not in body_mats:
            body_mats[col] = material(f'hyBody_{col[1:]}', None, srgb(col), 0.35, coat=0.6)
        expo.add(bevel_box(0.1, 0.035, 0.045, 0.01), mf @ T(-1.0 + c_ * 0.18, 1.0 + r_ * 0.155, 0.02), body_mats[col], 1)
    expo.add(box(2.15, 0.005, 0.28), mf @ T(0, 0.98 + r_ * 0.155, 0), M['glass'], 1)
# 현대 컬렉션 벽감 (짙은 돌, 회색 받침 3개)
nc = X1['hyundai_collection_niche']
nf = T(nc['centre_xz'][0], 0, nc['centre_xz'][1], nc['yaw_deg'] * DEG)
for k in (-1, 0, 1):
    expo.add(box(0.7, 0.9 + (k == 0) * 0.2, 0.5), nf @ T(k * 1.0, 0.45 + (k == 0) * 0.1, 0.1), M['lightGrey'], 1)
    expo.add(bevel_box(0.4, 0.2, 0.2, 0.02), nf @ T(k * 1.0, 1.0 + (k == 0) * 0.2, 0.1), M['chrome'], 1)
# 안내 데스크 (돌 앞면, 호두 상판)
rd = X1['reception_desk']
rf = T(rd['centre_xz'][0], 0, rd['centre_xz'][1], rd['yaw_deg'] * DEG)
expo.add(box(2.4, 1.0, 0.7), rf @ T(0, 0.5, 0), M['stone'], 1)
expo.add(box(2.45, 0.05, 0.75), rf @ T(0, 1.025, 0), M['walnut'], 1)
for k in (-1, 1):
    expo.add(box(0.5, 0.32, 0.03), rf @ T(k * 0.6, 1.25, -0.1), M['black'], 1)
# 층 안내판 (강관 패널)·인트로 배너
fd = X1['floor_directory_sign']
gallery.slab_art(expo, T(fd['centre_xz'][0], 1.3, fd['centre_xz'][1], fd['yaw_deg'] * DEG), 1.2, 1.8, 0.05, gm('1f_floor_directory'), M['pipe'])
ib = X1['intro_banner']
ibf = T(ib['centre_xz'][0], ib['top_m'] - 1.0, ib['centre_xz'][1], ib['yaw_deg'] * DEG)
gallery.slab_art(expo, ibf, 1.0, 2.0, 0.01, gm('1f_intro_panel'), M['white'])
g, m = tube(ibf @ V((0, 1.0, 0)), ibf @ V((0, 7.1 - ib['top_m'] + 1.0, 0)), 0.006, 5)
rig.add(g, m, M['black'])

# ── 2F 〈1억 대의 궤적〉: 파울바셋 카페 + 어두운 방 ─────────────────────
Y2 = LV['2F']
cafe = E['2F']['cafe']
ct = cafe['counter']
cf = T(ct['centre_xz'][0], Y2, ct['centre_xz'][1])
expo.add(box(3.6, 1.0, 0.7), cf @ T(0, 0.5, -0.25), M['black'], 1)
expo.add(box(0.7, 1.0, 1.2), cf @ T(1.45, 0.5, 0.25), M['black'], 1)
expo.add(box(3.7, 0.05, 0.8), cf @ T(0, 1.025, -0.25), M['walnut'], 1)
for k in range(8):                                                    # 북쪽 유리 바 좌석
    x = -0.5 + k * 1.5
    expo.add(box(1.2, 0.05, 0.45), T(x, Y2 + 1.05, -11.1), M['walnut'], 1)
    expo.add(cyl(0.18, 0.18, 0.05, 16), T(x, Y2 + 0.72, -10.55), M['black'], 1)
    expo.add(cyl(0.02, 0.02, 0.7, 8), T(x, Y2 + 0.35, -10.55), M['chrome'], 1)
for (x, z) in ((5.5, -7.5), (4.0, -5.5), (2.0, -8.5)):
    expo.add(cyl(0.35, 0.35, 0.03, 24), T(x, Y2 + 0.72, z), M['walnut'], 1)
    expo.add(cyl(0.03, 0.03, 0.7, 8), T(x, Y2 + 0.36, z), M['black'], 1)
expo.add(box(1.6, 0.4, 0.2), T(3.6, Y2 + 2.8, -3.6), M['black'], 1)             # 파울바셋 사인
# 어두운 방: 짙은 천 벽 (북쪽 3m 열림), 짙은 카펫
dr = E['2F']['dark_room']
x0, z0 = dr['outline_xz'][0]
x1, z1 = dr['outline_xz'][2]
DH = 3.3
prism(expo, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], Y2 + 0.001, Y2 + 0.03, M['carpetDark'], 2, bottom=False)
DARKWALL = material('hyDarkWall', None, (0.2, 0.2, 0.21), 0.8)
for (a, b) in (((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0)), ((x0, z0), (x0 + 2.2, z0)), ((x0 + 5.2, z0), (x1, z0))):
    gallery.wall(expo, (a[0], a[1]), (b[0], b[1]), DH, 0.15, DARKWALL, y0=Y2)
pipe_ceiling(inset([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], 0.1), Y2 + DH - 0.1)          # 강관 루버 천장 (사진)
prism(ceil, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], Y2 + DH + 0.2, Y2 + DH + 0.22, M['slabUnder'], 3, top=False, sides=False)
WALL_SLUGS = {1: '2f_wall1_first_step', 2: '2f_wall2_next_step', 3: '2f_wall3_one_step_further'}
for z_ in dr['wall_zones']:
    cx, cz = z_['centre_xz']
    L = z_['length_m']
    face = {1: -PI / 2, 2: PI, 3: PI / 2}[z_['id']]
    wf = T(cx, Y2, cz, face)
    gallery.slab_art(expo, wf @ T(0, 0.95 + 1.1, 0.05), L, 2.2 if z_['id'] == 1 else 2.0, 0.05, gm(WALL_SLUGS[z_['id']]), M['black'])
    emit.add(box(L, 0.03, 0.05), wf @ T(0, 0.95 + 2.25, 0.3), M['ledStrip'])
    expo.add(box(L, 0.9, 0.5), wf @ T(0, 0.45, 0.35), M['lightGrey'], 1)                 # 받침 진열대
    glass.add(box(L - 0.1, 0.3, 0.45), wf @ T(0, 1.05, 0.35), M['glass'], 1)
    emit.add(box(L, 0.02, 0.02), wf @ T(0, 0.88, 0.61), M['ledStrip'])
    for k in range(int(L / 0.6)):
        expo.add(box(0.3, 0.02, 0.22), wf @ T(-L / 2 + 0.3 + k * 0.6, 0.91, 0.35), M['paper'] if k % 3 else M['cage'], 1)
    if z_['id'] == 2:                                                     # 포니2 시작차 조립 디오라마
        d_ = wf @ T(1.2, 0.9, 0.35)
        expo.add(box(1.6, 0.03, 0.4), d_ @ T(0, 0.015, 0), M['greyMat'], 1)
        for k in range(6):
            expo.add(bevel_box(0.22, 0.07, 0.09, 0.02), d_ @ T(-0.65 + k * 0.26, 0.07, 0), M['steelGrey'], 1)
        expo.add(box(0.35, 0.2, 0.3), d_ @ T(0.62, 0.13, 0), M['cream'], 1)
    if z_['id'] == 3:                                                     # HMGICS 싱가포르 디오라마 (흰 원형 고리)
        d_ = wf @ T(-1.2, 0.9, 0.35)
        expo.add(box(1.5, 0.03, 0.42), d_ @ T(0, 0.015, 0), M['white'], 1)
        for k in range(24):
            a = k / 24 * 2 * PI
            g, m = tube(d_ @ V((math.cos(a) * 0.55, 0.12, math.sin(a) * 0.17)), d_ @ V((math.cos(a + 0.27) * 0.55, 0.12, math.sin(a + 0.27) * 0.17)), 0.012, 6)
            expo.add(g, m, M['white'])
        for k in range(5):
            expo.add(bevel_box(0.14, 0.05, 0.06, 0.015), d_ @ T(-0.4 + k * 0.2, 0.06, 0), M['white'], 1)
        expo.add(box(0.06, 0.04, 0.03), d_ @ T(0.62, 0.05, 0.1), M['cage'], 1)
# C자 사진 테이블 (지름 3.4, 폭 0.6, 높이 0.95, 북쪽이 열림)
tc = dr['c_table']['centre_xz']
for k in range(28):
    a0 = (60 + k * (300 / 28)) * DEG - PI / 2
    a1 = a0 + 300 / 28 * DEG
    for r_, rr in ((1.4, 1.7),):
        pa = [(tc[0] + math.cos(a) * r, tc[1] + math.sin(a) * r) for a, r in ((a0, r_), (a1, r_), (a1, rr), (a0, rr))]
        prism(expo, pa, Y2 + 0.9, Y2 + 0.95, M['white'], 1)
        emit.add(box(0.3, 0.02, 0.02), T(tc[0] + math.cos((a0 + a1) / 2) * 1.71, Y2 + 0.93, tc[1] + math.sin((a0 + a1) / 2) * 1.71, -(a0 + a1) / 2 + PI / 2), M['ledStrip'])
        if k % 2 == 0:
            expo.add(cyl(0.015, 0.015, 0.9, 6), T(tc[0] + math.cos(a0) * 1.55, Y2 + 0.45, tc[1] + math.sin(a0) * 1.55), M['white'], 1)
        expo.add(box(0.12, 0.09, 0.02), T(tc[0] + math.cos(a0) * 1.55, Y2 + 1.0, tc[1] + math.sin(a0) * 1.55, -a0 + PI / 2), M['paper'], 1)
jb = dr['journey_banner']
gallery.slab_art(expo, T(jb['centre_xz'][0], Y2 + jb['top_m'] - 1.0, jb['centre_xz'][1], jb['yaw_deg'] * DEG), 1.0, 2.0, 0.01, gm('2f_journey_panel'), M['white'])

# ── 3F 〈1억 대의 원동력〉 ────────────────────────────────────────
Y3 = LV['3F']
for c, key in zip(X3['cars'], ('sonata', 'scoupe', 'elantra')):
    cx, cz = c['centre_xz']
    yaw = c['yaw_deg']
    prism(expo, [tuple((T(cx, 0, cz, yaw * DEG) @ V((px, 0, pz))).xz) for px, pz in ((-3, -1.4), (3, -1.4), (3, 1.4), (-3, 1.4))],
          Y3, Y3 + 0.03, M['greyMat'], 2, bottom=False)
    place_car(key, cx, Y3 + 0.03, cz, yaw, f'car_{key}')
for lbx in X3['light_boxes']:
    light_box(*lbx['centre_xz'], lbx['yaw_deg'], Y3 + 3.6)
    light(C_LIGHT, f"lb3_{lbx['centre_xz'][0]:.0f}", 'AREA', (lbx['centre_xz'][0], Y3 + 3.55, lbx['centre_xz'][1]),
          (lbx['centre_xz'][0], Y3, lbx['centre_xz'][1]), energy=450, color=(0.96, 0.98, 1.0), size=4)
# 알파 엔진 두 대 (유리장 + 받침, 크롬 받침대)
for eng in X3['engines']:
    ex_, ez = eng['centre_xz']
    if 'vitrine' in eng['name']:
        expo.add(box(0.9, 0.9, 0.9), T(ex_, Y3 + 0.45, ez), M['black'], 1)
        glass.add(box(0.9, 0.9, 0.9), T(ex_, Y3 + 1.35, ez), M['glass'], 1)
        base = T(ex_, Y3 + 0.9, ez, 0.4)
    else:
        expo.add(box(0.8, 0.02, 0.8), T(ex_, Y3 + 0.01, ez), M['steelGrey'], 1)
        expo.add(cyl(0.05, 0.05, 0.85, 12), T(ex_, Y3 + 0.44, ez), M['chrome'], 1)
        base = T(ex_, Y3 + 0.86, ez, 0.4)
    expo.add(bevel_box(0.55, 0.32, 0.42, 0.03), base @ T(0, 0.2, 0), M['steelGrey'], 1)          # 블록
    expo.add(bevel_box(0.5, 0.12, 0.3, 0.03), base @ T(0, 0.42, 0), M['black'], 1)               # 헤드 커버
    for k in range(4):
        g, m = tube(base @ V((-0.2 + k * 0.13, 0.35, 0.18)), base @ V((-0.2 + k * 0.13, 0.2, 0.32)), 0.022, 8)
        expo.add(g, m, M['chrome'])
    expo.add(cyl(0.12, 0.12, 0.05, 20), base @ T(-0.3, 0.18, 0, 0, 0, PI / 2), M['black'], 1)
# 아카이브 테이블 (45° 돌 코어 벽을 따라 7 × 0.7, 뒤판 1m)
at = X3['archive_table']
af3 = T(at['centre_xz'][0], Y3, at['centre_xz'][1], at['yaw_deg'] * DEG)
expo.add(box(7.0, 0.04, 0.7), af3 @ T(0, 0.88, 0), M['steelGrey'], 1)
expo.add(box(7.0, 1.0, 0.04), af3 @ T(0, 1.4, -0.33), M['lightGrey'], 1)
for k in range(8):
    expo.add(box(0.04, 0.88, 0.6), af3 @ T(-3.45 + k * 0.985, 0.44, 0), M['steelGrey'], 1)
    expo.add(box(0.35, 0.02, 0.26), af3 @ T(-3.2 + k * 0.9, 0.91, 0.05), M['paper'], 1)
# 파란 리본 벽: 세로 강관 슬랫이 천장에서 바닥으로 휘어 내림 + 55인치 모니터
rbp = [V((p[0], 0, p[1])) for p in X3['blue_ribbon_wall']['plan_polyline_xz']]
tot = sum((b - a).length for a, b in zip(rbp, rbp[1:]))
acc = 0.0
for a, b in zip(rbp, rbp[1:]):
    L = (b - a).length
    n = int(L / 0.06)
    for k in range(n):
        p = a.lerp(b, k / n)
        t_ = (acc + L * k / n) / tot
        top = Y3 + 4.2
        bot = Y3 + (0.0 if t_ > 0.25 else (0.25 - t_) * 8)
        g, m = tube(V((p.x, bot, p.z)), V((p.x, top, p.z)), 0.02, 6)
        expo.add(g, m, M['ribbon'])
    acc += L
mp = rbp[1].lerp(rbp[2], 0.5)
expo.add(box(1.23, 0.71, 0.06), T(mp.x - 0.1, Y3 + 1.9, mp.z - 0.1, -PI / 4 + PI / 2), M['black'], 1)
emit.add(plane(1.2, 0.68), T(mp.x - 0.1, Y3 + 1.9, mp.z - 0.1, -PI / 4 + PI / 2) @ T(0, 0, 0.09), gm('3f_ribbon_monitor', 1.0), tile=None)
# 3F 광고 파티션 (타공 금속 2.4m, 액자 광고) + 연도 사진 파일론
for (slug, cx, cz, yaw, w_) in (('3f_scoupe_ads_wall', -6.8, -1.8, 45, 4.4), ('3f_elantra_wall', 4.0, -9.8, 0, 4.4), ('3f_scoupe_wall', -0.4, -4.6, 45, 1.2)):
    pf = T(cx, Y3, cz, yaw * DEG)
    expo.add(box(w_, 2.4, 0.04), pf @ T(0, 0.25 + 1.2, 0), M['perf'], 1)
    for s in (-1, 1):
        expo.add(box(0.05, 0.25, 0.4), pf @ T(s * (w_ / 2 - 0.1), 0.125, 0), M['steelGrey'], 1)
    gallery.slab_art(expo, pf @ T(0, 1.5, 0.05), w_ - 0.4, (w_ - 0.4) * 0.5 if w_ > 2 else 2.0, 0.02, gm(slug), M['black'])

# 설계실 (1980년대 제도실): 흰 판 벽 2.8m (북쪽 열림), 베이지 바닥
DR = X3['drafting_room']
(dx0, dz0), _, (dx1, dz1), _ = DR['outline_xz']
prism(expo, [(dx0, dz0), (dx1, dz0), (dx1, dz1), (dx0, dz1)], Y3, Y3 + 0.03, M['vinyl'], 2, bottom=False)
for (a, b) in (((dx0, dz0), (dx0, dz1)), ((dx0, dz1), (dx1, dz1)), ((dx1, dz1), (dx1, dz0))):
    gallery.wall(expo, a, b, 2.8, 0.1, M['creamWall'], y0=Y3)
for it in DR['contents']:
    nm = it['name']
    cx, cz = it['centre_xz']
    sx, sy, sz = it['size_m']
    f = T(cx, Y3, cz, it.get('yaw_deg', 0) * DEG)
    if nm.startswith('intro text'):
        gallery.slab_art(expo, f @ T(0, it['top_m'] - 0.5, 0.06), 1.6, 1.0, 0.01, gm('3f_drafting_intro_text'), M['white'])
    elif 'filing cabinet' in nm:
        expo.add(bevel_box(1.0, 1.0, 0.5, 0.01), f @ T(0, 0.5, 0), M['greyGreen'], 1)
        expo.add(cyl(0.1, 0.12, 0.18, 16), f @ T(-0.25, 1.09, 0), M['cage'], 1)                 # 노란 법랑 주전자
        expo.add(bevel_box(0.22, 0.08, 0.2, 0.02), f @ T(0.2, 1.04, 0), M['black'], 1)          # 다이얼 전화
    elif 'desk' in nm:
        mat = M['walnut'] if 'wood' in nm else M['cream']
        expo.add(box(sx, 0.04, sy), f @ T(0, 0.73, 0), mat, 1)
        expo.add(box(0.45, 0.7, sy - 0.05), f @ T(sx / 2 - 0.25, 0.36, 0), mat, 1)
        for s in (-1,):
            expo.add(box(0.04, 0.7, sy - 0.05), f @ T(-sx / 2 + 0.03, 0.36, 0), mat, 1)
        expo.add(box(0.8, 0.005, 0.55), f @ T(-0.2, 0.753, 0), M['paper'], 1)
        if 'typewriter' in nm:
            expo.add(bevel_box(0.45, 0.14, 0.38, 0.03), f @ T(0.35, 0.82, 0), M['greyGreen'], 1)
        if 'plotter' in nm:
            expo.add(box(0.55, 0.12, 0.45), f @ T(0.3, 0.81, 0), M['stone'], 1)
            for k in range(3):
                g, m = tube(f @ V((0.3, 0.87 + k * 0.18, 0)), f @ V((0.3 + (k % 2) * 0.15, 1.05 + k * 0.18, 0.05)), 0.03, 8)
                expo.add(g, m, M['white'])
        # 의자
        expo.add(box(0.45, 0.05, 0.45), f @ T(0, 0.45, 0.65), M['black'], 1)
        expo.add(box(0.45, 0.45, 0.05), f @ T(0, 0.7, 0.87), M['black'], 1)
        expo.add(cyl(0.025, 0.025, 0.43, 8), f @ T(0, 0.22, 0.65), M['chrome'], 1)
    elif 'drafting board' in nm:
        expo.add(box(0.06, 0.8, 0.06), f @ T(0, 0.4, 0), M['steelGrey'], 1)
        expo.add(box(0.9, 0.04, 0.6), f @ T(0, 0.02, 0), M['steelGrey'], 1)
        bf = f @ T(0, 1.05, 0, 0, -60 * DEG)
        expo.add(box(1.2, 0.9, 0.03), bf, M['white'], 1)
        expo.add(plane(0.8, 0.52), bf @ T(0, 0, 0.06), gm('3f_drafting_board_sheet'), tile=None)
        for k in range(2):
            g, m = tube(bf @ V((-0.5, 0.35 - k * 0.5, 0.03)), bf @ V((0.3, 0.1 - k * 0.2, 0.03)), 0.008, 6)
            expo.add(g, m, M['steelGrey'])
    elif 'flat-file' in nm:
        for k in (-1, 1):
            expo.add(bevel_box(0.58, 0.9, 0.85, 0.01), f @ T(k * 0.3, 0.45, 0), M['paleGreen'], 1)
        expo.add(bevel_box(0.4, 0.22, 0.18, 0.02), f @ T(-0.2, 1.01, 0), M['walnut'], 1)          # 라디오
    elif 'backlit' in nm:
        bot = it['top_m'] - sy
        slug = '3f_backlit_drawing' if sx > 3 else '3f_backlit_drawing_side'
        expo.add(box(sx + 0.08, sy + 0.08, 0.06), f @ T(0, bot + sy / 2, -sz / 2 - 0.02), M['steelGrey'], 1)
        emit.add(plane(sx, sy), f @ T(0, bot + sy / 2, -sz / 2 + 0.08), gm(slug, 1.2), tile=None)
    elif 'pendant' in nm:
        for k in range(4):
            px = -2.7 + k * 1.8
            emit.add(box(1.3, 0.04, 0.12), f @ T(px, 2.9, 0), M['ledStrip'])
            expo.add(box(1.3, 0.06, 0.28), f @ T(px, 2.95, 0), M['white'], 1)
            g, m = tube(f @ V((px, 2.98, 0)), f @ V((px, 4.2, 0)), 0.006, 5)
            rig.add(g, m, M['black'])
# 파이프 받침 모니터
for pt in X3['pipe_trolley_monitors']:
    cx, cz = pt['centre_xz']
    for s in (-1, 1):
        g, m = tube(V((cx + s * 0.25, Y3, cz)), V((cx + s * 0.25, Y3 + 1.8, cz)), 0.024, 6)
        expo.add(g, m, M['pipe'])
    expo.add(box(1.23, 0.71, 0.06), T(cx, Y3 + 1.45, cz, PI / 2), M['black'], 1)

# ── 4F·5F 〈1억 대의 내일〉: 파란 바닥·곡면 배경 + SUV / EV ──────────────
for FL, X, keys in (('4F', X4, ('santafe', 'kona', 'casper')), ('5F', X5, ('ioniq5', 'ioniq5n', 'ioniq6'))):
    Y = LV[FL]
    order = {c['centre_xz'][0]: c for c in X['cars']}
    for c in X['cars']:
        name = c.get('model') or c.get('name', '')
        key = {'Santa Fe': 'santafe', 'Kona': 'kona', 'Casper': 'casper', 'N Line': 'ioniq5n', 'IONIQ 6': 'ioniq6', 'IONIQ 5': 'ioniq5'}
        k_ = next(v for kk, v in key.items() if kk in name)
        cx, cz = c['centre_xz']
        yaw = c['yaw_deg']
        cf_ = T(cx, 0, cz, yaw * DEG)
        prism(expo, [tuple((cf_ @ V((px, 0, pz))).xz) for px, pz in ((-2.7, -1.25), (2.7, -1.25), (2.7, 1.25), (-2.7, 1.25))],
              Y, Y + 0.012, M['blueFloor'], 2, bottom=False)
        place_car(k_, cx, Y + 0.012, cz, yaw, f'car_{k_}')
        # 차 뒤(꽁무니 쪽) 곡면 파란 배경 3.5m (사진)
        bk = [cf_ @ V((-3.3 - 0.35 * math.cos((i - 5) / 5 * PI / 2), 0, -1.9 + i * 0.38)) for i in range(11)]
        for a, b in zip(bk, bk[1:]):
            expo.add(box((b - a).length + 0.02, 3.5, 0.06), T((a.x + b.x) / 2, Y + 1.75, (a.z + b.z) / 2, math.atan2(-(b.z - a.z), b.x - a.x)), M['blueWall'], 1)
        light_box(cx, cz, yaw, Y + 3.6)
        light(C_LIGHT, f'lb{FL}_{cx:.0f}', 'AREA', (cx, Y + 3.55, cz), (cx, Y, cz), energy=450, color=(0.96, 0.98, 1.0), size=4)
    # 곡면 아카이브 벽 + 호두 선반 (4F 기준, 5F 같은 자리)
    cw = X4['archive']['curved_wall']['plan_polyline_xz']
    segL = [math.dist(a, b) for a, b in zip(cw, cw[1:])]
    totL = sum(segL)
    acc = 0.0
    band = gm('4f_archive_wall' if FL == '4F' else '5f_archive_wall')
    for (a, b), L_ in zip(zip(cw, cw[1:]), segL):
        fr, _ = seg_frame(a, b)
        u0, u1 = acc / totL, (acc + L_) / totL
        acc += L_
        fb = fr @ T(0, Y + 1.8, 0.12, PI)                      # 실내(-z) 쪽을 보는 사진 띠, 벽에서 4cm
        gallery.slab_sides(expo, fb, L_, 1.17, 0.04, M['lightGrey'])
        expo.add(gallery.quad_uv(L_, 1.17, (1 - u1, 0, 1 - u0, 1)), fb, band, tile=None)
    for a, b in zip(cw, cw[1:]):
        fr, L = seg_frame(a, b)
        expo.add(box(L + 0.02, 2.4, 0.08), fr @ T(0, Y + 1.2, 0.2), M['lightGrey'], 1)
        expo.add(box(L + 0.02, 0.04, 0.45), fr @ T(0, Y + 0.9, -0.05), M['walnut'], 1)
        emit.add(box(L, 0.03, 0.05), fr @ T(0, Y + 2.45, 0.1), M['ledStrip'])
    isl = (X4 if FL == '4F' else X5)['archive']['island_table']
    fi = T(isl['centre_xz'][0], Y, isl['centre_xz'][1], isl.get('yaw_deg', 0) * DEG)
    expo.add(box(isl['size_m'][0], 0.05, isl['size_m'][2]), fi @ T(0, isl['top_m'] - 0.025, 0), M['walnut'], 1)
    expo.add(box(isl['size_m'][0] - 0.2, isl['top_m'] - 0.05, isl['size_m'][2] - 0.2), fi @ T(0, (isl['top_m'] - 0.05) / 2, 0), M['black'], 1)
    for k in range(4):
        expo.add(box(0.5, 0.02, 0.35), fi @ T(-1.0 + k * 0.66, isl['top_m'] + 0.01, 0), M['paper'], 1)
# 4F 캠핑 소품 (싼타페 트렁크 앞)
cs = X4['camping_set']
cf4 = T(cs['centre_xz'][0], LV['4F'], cs['centre_xz'][1], cs['yaw_deg'] * DEG)
for s in (-1, 1):
    ch = cf4 @ T(s * 0.8, 0, 0.3)
    expo.add(box(0.5, 0.04, 0.45), ch @ T(0, 0.35, 0), M['greyGreen'], 1)
    expo.add(box(0.5, 0.45, 0.04), ch @ T(0, 0.6, 0.22, 0, 0.25), M['greyGreen'], 1)
    for (lx, lz) in ((-0.22, -0.2), (0.22, -0.2), (-0.22, 0.2), (0.22, 0.2)):
        g, m = tube(ch @ V((lx, 0, lz)), ch @ V((lx * 0.9, 0.35, lz * 0.9)), 0.012, 6)
        expo.add(g, m, M['black'])
expo.add(box(0.7, 0.04, 0.45), cf4 @ T(0, 0.4, -0.2), M['walnut'], 1)
expo.add(box(0.5, 0.35, 0.35), cf4 @ T(0.1, 0.175, -0.8), M['black'], 1)
g, m = tube(cf4 @ V((-1.3, 0, -0.5)), cf4 @ V((-1.3, 1.6, -0.5)), 0.012, 6)
expo.add(g, m, M['black'])
expo.add(cyl(0.07, 0.07, 0.2, 12), cf4 @ T(-1.3, 1.5, -0.5), M['cage'], 1)
# 5F 충전기·빈백
ch5 = X5['charger']['centre_xz']
expo.add(cyl(0.175, 0.175, 1.6, 24), T(ch5[0], LV['5F'] + 0.8, ch5[1]), M['white'], 1)
bb = X5['beanbag_lounge']['centre_xz']
for k in range(5):
    a = k / 5 * 2 * PI
    expo.add(sphere(0.45, 3), T(bb[0] + math.cos(a) * 1.1, LV['5F'] + 0.3, bb[1] + math.sin(a) * 1.1, 0, 0, 0, 1, 0.62, 1), M['fabricDark'])
expo.add(cyl(0.3, 0.3, 0.4, 24), T(bb[0], LV['5F'] + 0.2, bb[1]), material('hyPink', None, srgb('#E9A9B5'), 0.6), 1)

# ── 3~5F 로테이터 (셸 하부가 방을 봄) + 유리 쪽 낮은 강관 레일 ────────────────
for FL, shell in (('3F', 'elantra'), ('4F', 'santafe'), ('5F', 'ioniq5')):
    for rid, r in ROT.items():
        col = {'west': 'left', 'chamfer': 'center', 'north': 'right'}[rid]
        rotator(*r['centre_xz'], r['axis_dir_xz'], r['clamp_to_clamp_m'], LV[FL], shell, panel=f'rotator_{FL}_{col}')
    for rl in B['rails_at_glass_3F_5F']:
        pipe_rail(rl['from_xz'], rl['to_xz'], LV[FL], rails=2, h=0.45, asm=expo)

# ── 빌드 · 조명 · 카메라 ──────────────────────────────────────────
light(C_LIGHT, 'sun', 'SUN', (-40, 60, -30), (0, 0, 0), energy=2.2, color=(1.0, 0.97, 0.92))
for f in ('1F', '3F', '4F', '5F'):
    light(C_LIGHT, f'fill_{f}', 'AREA', (0, LV[f] + 3.6, 0), (0, LV[f], 0), energy=900, color=(1.0, 0.98, 0.95), size=16)
for a in (bld, ceil, site, expo, emit, rig, glass):
    a.build(smooth=(a is rig))
w = bpy.data.worlds.new('hy_world')
w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.6, 0.66, 0.74, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
scene.world = w
camera(C_CAM, 'cam_overview', (-42, 34, -40), (1, 8, 1), 40)
camera(C_CAM, 'cam_street', (-31, 1.7, -25), (-3, 11, -3), 58)                               # ext_facade_full-dusk
camera(C_CAM, 'cam_1f', (5.0, 1.45, -9.3), (-4.3, 1.1, -3.6), 72)                            # 1F_overview_entrance-view
camera(C_CAM, 'cam_2f_top', (1.3, LV['2F'] + 1.2, -2.6), (-4.6, 0.3, -4.8), 76)              # 2F_view_topdown-arch-cortina
camera(C_CAM, 'cam_media', (-6.395 + 0.7 * 10.5, 5.2, -6.569 + 0.714 * 10.5), (-6.395, 5.1, -6.569), 64)   # 대형 미디어월 정면
camera(C_CAM, 'cam_conveyor', (3.0, LV['2F'] + 1.5, -7.0), (-6.4, 5.4, -6.4), 76)            # 2F_view_conveyor-from-2F
camera(C_CAM, 'cam_2f_dark', (-6.0, LV['2F'] + 1.6, 5.0), (-6.6, LV['2F'] + 0.9, 12.8), 76)  # 2F_center_dark-room-overview
camera(C_CAM, 'cam_3f', (-6.2, LV['3F'] + 1.35, 2.6), (3.0, LV['3F'] + 1.0, -6.0), 72)        # 3F_overview_scoupe-toward-archive
camera(C_CAM, 'cam_drafting', (-5.6, LV['3F'] + 1.6, 6.6), (-5.6, LV['3F'] + 1.2, 13.0), 72)  # 3F_drafting_room-straight
camera(C_CAM, 'cam_4f', (2.0, LV['4F'] + 1.4, 1.7), (-4.0, LV['4F'] + 1.0, -5.5), 74)         # 4F_santafe_front-wide-rotators
camera(C_CAM, 'cam_5f', (1.6, LV['5F'] + 1.3, 1.4), (-4.0, LV['5F'] + 1.2, -5.0), 74)         # 5F_ioniq5_front-wide-lightbox
scene.camera = bpy.data.objects['cam_1f']
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
print('hyundai built:', {c.name: len(c.objects) for c in (C_STATIC, C_DYNAMIC, C_EMIT, C_LIGHT, C_CAM)})
