"""동대문디자인플라자(DDP) 뮤지엄 전시1관 — 장 미셸 바스키아: 과거와 미래를 잇는 상징적 기호들 (2025.9.23~2026.1.31)

  python3 scripts/blender/bmcp.py exec scripts/blender/basquiat_scene.py

자료 (assets-src/refs/basquiat/index.md — 네이버 블로그 약 400개·노루페인트/팬톤 설치 사진·기사, 149장):
- 전시1관 (DDP 대관 안내서): 지하 2층, 1,216㎡, 39.7 × 35.4m, 층고 8.8m, 흰 에폭시 바닥, 흰 천장에 검은 선형 조명 슬롯,
  곡면 벽. 평면 윤곽은 안내서의 축측도(세로 0.68 축소)를 되돌려 얻음 (hall1_outline.json, 면적 오차 2%).
- 동선 (11개 섹션 + 서문·Phooey·Museum Security): 입구(동쪽, B2 로비) → 서문·Studio of the Street(빨간 카펫, 베이지 벽)
  → 회색 카펫 방(냉장고·화병 좌대) → Phooey 복도(왼쪽 네이비 벽, 오른쪽 Fun Gallery 흑백 사진 벽, 끝에 빨간 방이 보임)
  → Warriors 빨간 방(A-One·잉크 드로잉 7점·무신도 병풍 벽장·백남준 로봇) → 흰 방(Farina·검은 끝벽 Black Figure)
  → Heads 검은 작은 방(흰 복도 끝에 정면으로 보임) → Cartoons(이젤 좌대·Bombero 검은 가벽) → Words and Signs 긴 흰 복도
  → Museum Security(네이비, Masonic Lodge 상자) → 검은 커튼 → Temple of Words(네이비 벽·밝은 바닥·노트 페이지 격자·가운데 검은 상자)
  → It's All Drawing 복도(반구대 탁본 8.32m 낮은 선반, 끝 영상) → 연보·영상 → Anatomy(Flesh and Spirit 좌대) → Hidden Signs(Emblem 방)
  → Basquiat in Asia(추사 현판·프로젝션, 빨간 카펫) → Epilogue(끝 네이비 벽 EXU, 왼쪽 출구 커튼) → 디자인둘레길 아트샵.
- 벽 색 (팬톤 페인트 7색): Stalactite #F1F1EE · Nova Scotia #E8DDD0 · Tracing Gray #BCBCB9 · Coal Smoke #5A5659 ·
  Syrah #74373A · Black Beauty #3B3C40 · Silhouette #3A3F4A.
- 작품 텍스처는 설치 사진에서 원근을 편 것 (assets-src/shots/bq_w_*.png, 목록 refs/basquiat/works_*.json).
좌표: 전시홀 중심 원점 (웹 Y-up). -z 위쪽 직선 벽, +x 동쪽(입구·로비), +z 남쪽(출구·디자인둘레길 아트샵).
평면도는 없어서 방 배치는 사진 순서·시선 관계·작품 크기로 복원한 것.
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
from lib import (PI, SHOTS, Assembly, T, bevel_box, box, camera, collection, cyl, light, material,  # noqa: E402
                 plane, reset, sphere, tube)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

import gallery  # noqa: E402
import rooms as roomkit  # noqa: E402
importlib.reload(gallery)
importlib.reload(roomkit)
from gallery import srgb  # noqa: E402

REFS = '/Users/hare/Documents/큐비크스홈페이지/assets-src/refs/basquiat'
random.seed(9)
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

HALL_H, WALL_H, WALL_T, RAIL_Y = 8.8, 3.6, 0.2, 4.6

PANTONE = {'white': '#F1F1EE', 'beige': '#E8DDD0', 'grey': '#BCBCB9', 'coal': '#5A5659',
           'burgundy': '#74373A', 'black': '#3B3C40', 'navy': '#3A3F4A'}
M = {k: material(f'bqWall_{k}', None, srgb(v), 0.9) for k, v in PANTONE.items()}
M.update({
    'hallWall': material('bqHallWall', None, (0.8, 0.8, 0.79), 0.8),
    'ceiling': material('bqCeiling', None, (0.55, 0.55, 0.55), 0.85),
    'slot': material('bqSlot', None, (0.01, 0.01, 0.012), 0.5),
    'epoxy': material('bqEpoxy', None, (0.82, 0.82, 0.82), 0.25, coat=0.6),
    'carpetGrey': material('bqCarpetGrey', None, (0.055, 0.058, 0.064), 0.95),
    'carpetRed': material('bqCarpetRed', None, (0.15, 0.011, 0.014), 0.95),
    'floorPale': material('bqFloorPale', None, (0.6, 0.58, 0.54), 0.7),
    'rig': material('bqRig', None, (0.015, 0.015, 0.017), 0.4, 0.5),
    'lampLens': material('bqLampLens', None, (1, 1, 1), emit=(1.0, 0.93, 0.8), emit_strength=40),
    'downLens': material('bqDownLens', None, (1, 1, 1), emit=(1.0, 0.97, 0.92), emit_strength=15),
    'batten': material('bqBatten', None, (0.55, 0.42, 0.28), 0.8),
    'rope': material('bqRope', None, (0.7, 0.66, 0.58), 0.9),
    'canvasEdge': material('bqCanvasEdge', None, (0.75, 0.72, 0.66), 0.9),
    'frameWhite': material('bqFrameWhite', None, (0.88, 0.88, 0.86), 0.5),
    'frameOak': material('bqFrameOak', None, (0.55, 0.4, 0.24), 0.55),
    'frameBlack': material('bqFrameBlack', None, (0.02, 0.02, 0.022), 0.4),
    'frameGold': material('bqFrameGold', None, (0.6, 0.45, 0.2), 0.35, 0.8),
    'frameDark': material('bqFrameDark', None, (0.12, 0.07, 0.04), 0.5),
    'mat': material('bqMat', None, (0.9, 0.89, 0.86), 0.9),
    'labelCard': material('bqLabel', None, (0.85, 0.85, 0.83), 0.8),
    'glass': material('bqGlass', None, (0.9, 0.95, 0.97), 0.02, transmission=1.0),
    'vitrineBase': material('bqVitrineBase', None, (0.03, 0.03, 0.035), 0.5),
    'plinth': material('bqPlinth', None, (0.85, 0.85, 0.83), 0.6),
    'curtain': material('bqCurtain', 'cotton_jersey', (0.012, 0.012, 0.014), 0.9, normal=0.5, sheen=0.3),
    'foyerFloor': material('bqFoyer', None, (0.86, 0.86, 0.86), 0.12, coat=0.8),
    'counterRed': material('bqCounterRed', None, (0.35, 0.03, 0.04), 0.5),
})


def gmat(slug, emit=0.0):
    """shots 폴더의 작품/그래픽 텍스처 재질 (없으면 회색)"""
    for pre in ('bq_w_', 'bq_m_'):
        p = f'{SHOTS}/{pre}{slug}.png'
        if os.path.exists(p):
            if emit:
                return material(f'bqE_{slug}', emit_image=p, emit_strength=emit, rough=0.9)
            return material(f'bqG_{slug}', image_base=p, rough=0.75)
    print('texture missing:', slug)
    return material(f'bqMissing_{slug}', None, (0.4, 0.4, 0.4), 0.8)


hall = Assembly('hall', C_STATIC)          # 전시홀 외벽 (안을 보는 한 겹)
ceil = Assembly('ceiling', C_STATIC)       # 천장 (아래를 보는 한 겹)
floor = Assembly('floor', C_STATIC)
walls = Assembly('walls', C_STATIC)        # 가벽
works = Assembly('works', C_STATIC)        # 작품·액자·좌대·진열장
foyer = Assembly('foyer', C_STATIC)        # B2 로비·입구 파사드·디자인둘레길 아트샵
emit = Assembly('emissive', C_EMIT)
rig = Assembly('rig', C_DYNAMIC)           # 트랙 레일·스포트
glass = Assembly('glass', C_DYNAMIC)

# ── 전시홀 쉘 ────────────────────────────────────────────────
OUT = json.load(open(f'{REFS}/hall1_outline.json'))['outline']


def chaikin(pts, n=2):
    for _ in range(n):
        q = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            q += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        pts = q
    return pts


OUTLINE = chaikin(OUT, 2)
N = len(OUTLINE)


def poly_face(asm, pts, y, mat, down=False, tile=2.0):
    def build(bm):
        vs = [bm.verts.new((x, 0, z)) for x, z in pts]
        f = bm.faces.new(vs)
        bmesh.ops.triangulate(bm, faces=[f])
        for f in bm.faces:
            f.normal_update()
            if (f.normal.y < 0) != down:
                f.normal_flip()
    asm.add(build, T(0, y, 0), mat, tile)


poly_face(floor, OUTLINE, -0.02, M['carpetGrey'], tile=3)
COVE = 0.9
for i in range(N):
    (x1, z1), (x2, z2) = OUTLINE[i], OUTLINE[(i + 1) % N]
    d = V((x2 - x1, 0, z2 - z1))
    ry = math.atan2(-d.z, d.x)
    mid = T((x1 + x2) / 2, 0, (z1 + z2) / 2, ry)
    # 벽 (안쪽을 봄: 윤곽이 시계방향이면 +z 쪽이 안)
    hall.add(plane(d.length + 0.02, HALL_H - COVE), mid @ T(0, (HALL_H - COVE) / 2, 0), M['hallWall'], 3)
# 윤곽은 위(북)에서 동쪽으로 도는 시계방향이라 각 변의 로컬 +z(왼쪽 법선)가 홀 안쪽
# 천장 가장자리 곡면 (코브) + 천장
cx0 = sum(p[0] for p in OUTLINE) / N
cz0 = sum(p[1] for p in OUTLINE) / N
inner = [(cx0 + (x - cx0) * 0.955, cz0 + (z - cz0) * 0.955) for x, z in OUTLINE]


def cove(bm):
    rings = []
    for k in range(5):
        a = k / 4 * PI / 2
        t_, y = 1 - math.cos(a), HALL_H - COVE + math.sin(a) * COVE
        rings.append([bm.verts.new((o[0] + (i[0] - o[0]) * t_, y, o[1] + (i[1] - o[1]) * t_)) for o, i in zip(OUTLINE, inner)])
    for ra, rb in zip(rings, rings[1:]):
        for j in range(N):
            bm.faces.new((ra[j], ra[(j + 1) % N], rb[(j + 1) % N], rb[j]))
    for f in bm.faces:
        f.normal_update()
        c = f.calc_center_median()
        toward = V((cx0 - c.x, HALL_H - COVE - c.y, cz0 - c.z))
        if f.normal.dot(toward) < 0:
            f.normal_flip()


ceil.add(cove, T(), M['ceiling'], 3)
poly_face(ceil, inner, HALL_H, M['ceiling'], down=True, tile=3)
# 검은 선형 조명 슬롯 (빈 전시관 사진: 비스듬한 평행선, 약 3m 간격, 슬롯 안 작은 조명)
ANG = math.radians(-18)
ux, uz = math.cos(ANG), math.sin(ANG)


def inside(x, z, pts=inner):
    c = False
    for i in range(len(pts)):
        (xa, za), (xb, zb) = pts[i], pts[(i + 1) % len(pts)]
        if (za > z) != (zb > z) and x < (xb - xa) * (z - za) / (zb - za) + xa:
            c = not c
    return c


for k in range(-7, 8):
    off = k * 3.0
    seg = []
    for s in [i * 0.5 for i in range(-60, 61)]:
        x, z = -uz * off + ux * s, ux * off + uz * s
        ok = inside(x, z) and inside(x + ux * 1.2, z + uz * 1.2) and inside(x - ux * 1.2, z - uz * 1.2)
        if ok:
            seg.append((x, z))
        if (not ok or s == 30) and len(seg) > 4:
            (xa, za), (xb, zb) = seg[1], seg[-2]
            L = math.hypot(xb - xa, zb - za)
            if k % 2:
                # 짝수 줄은 끊어진 짧은 슬롯 여러 개
                pass
            ceil.add(plane(L, 0.28), T((xa + xb) / 2, HALL_H - 0.012, (za + zb) / 2, -ANG, PI / 2), M['slot'], 1)
            for j in range(int(L / 2.4)):
                t_ = (j + 0.5) / int(L / 2.4)
                px, pz = xa + (xb - xa) * t_, za + (zb - za) * t_
                emit.add(cyl(0.05, 0.05, 0.01, 12), T(px, HALL_H - 0.03, pz), M['downLens'])
            seg = []
        elif not ok:
            seg = []

# ── 방 배치 (사진 순서·시선·작품 크기로 복원) ─────────────────────
W = M
ROOMS = {
    'preface':   {'rect': (14.0, 19.4, -12.0, 0.0), 'color': W['beige']},
    'studioRed': {'rect': (5.0, 14.0, -12.0, -3.0), 'color': W['beige']},
    'studioGrey': {'rect': (5.0, 16.5, -17.4, -12.0), 'color': W['white'], 'sides': {'w': W['navy']}, 'open': {'n'}},
    'phooey':    {'rect': (-8.0, 5.0, -17.4, -13.0), 'color': W['white'], 'sides': {'s': W['navy']}, 'open': {'n'}},
    'red':       {'rect': (-18.6, -8.0, -17.0, -10.0), 'color': W['burgundy'], 'open': {'n'}},
    'white':     {'rect': (-19.3, -14.0, -10.0, 4.0), 'color': W['white'], 'open': {'w'}},
    'heads':     {'rect': (-16.5, -8.0, 4.0, 8.5), 'color': W['black']},
    'cartoons':  {'rect': (-14.0, -8.0, -10.0, 4.0), 'color': W['white']},
    'words':     {'rect': (-8.0, 5.0, -13.0, -8.5), 'color': W['white'], 'sides': {'n': W['grey']}},
    'msec':      {'rect': (0.0, 5.0, -8.5, -3.0), 'color': W['navy']},
    'temple':    {'rect': (-8.0, 0.0, -8.5, 5.0), 'color': W['navy']},
    'drawing':   {'rect': (0.0, 12.0, 1.0, 5.0), 'color': W['white']},
    'chrono':    {'rect': (12.0, 19.2, 0.0, 9.0), 'color': W['white'], 'open': {'e'}},
    'anatomy':   {'rect': (5.0, 12.0, 5.0, 11.0), 'color': W['white'], 'sides': {'w': W['black']}},
    'hidden':    {'rect': (12.0, 15.5, 9.0, 12.5), 'color': W['navy']},
    'asia':      {'rect': (8.0, 13.0, 11.0, 15.5), 'color': W['white']},
    'epilogue':  {'rect': (0.0, 8.0, 11.0, 17.0), 'color': W['white'], 'sides': {'w': W['navy']}, 'open': {'s'}},
}
ROOM_FLOOR = {'preface': 'carpetRed', 'studioRed': 'carpetRed', 'temple': 'floorPale', 'asia': 'carpetRed', 'epilogue': 'carpetRed'}
for rid, r in ROOMS.items():
    x0, x1, z0, z1 = r['rect']
    floor.add(box(x1 - x0, 0.02, z1 - z0), T((x0 + x1) / 2, -0.01, (z0 + z1) / 2), M[ROOM_FLOOR.get(rid, 'carpetGrey')], 3)
# 모서리가 홀 곡면 밖으로 나가는 방은 윤곽에 붙은 변을 열어 둔다 (홀 벽이 대신함)
ROOMS.clear()
ROOMS.update({
    'preface':    {'rect': (12.0, 19.4, -12.0, 0.0), 'color': W['beige'], 'open': {'e'}},
    'studioRed':  {'rect': (5.0, 12.0, -12.0, -3.0), 'color': W['beige']},
    'studioGrey': {'rect': (5.0, 16.5, -17.4, -12.0), 'color': W['white'], 'sides': {'w': W['navy']}, 'open': {'n'}},
    'phooey':     {'rect': (-8.0, 5.0, -17.4, -13.0), 'color': W['white'], 'sides': {'s': W['navy']}},
    'red':        {'rect': (-16.5, -8.0, -17.0, -10.0), 'color': W['burgundy']},
    'white':      {'rect': (-19.2, -12.5, -10.0, -3.0), 'color': W['white'], 'sides': {'s': W['black']}},
    'whiteCorr':  {'rect': (-15.0, -12.5, -3.0, 4.0), 'color': W['white']},
    'headsCorr':  {'rect': (-15.0, -12.2, 4.0, 7.0), 'color': W['white']},
    'headsBlack': {'rect': (-14.2, -10.2, 7.0, 9.4), 'color': W['black']},
    'toCartoons': {'rect': (-12.2, -9.0, 4.0, 7.0), 'color': W['white']},
    'cartoons':   {'rect': (-12.5, -6.0, -10.0, 4.0), 'color': W['white']},
    'words':      {'rect': (-6.0, 5.0, -13.0, -8.0), 'color': W['white'], 'sides': {'e': W['grey']}},
    'msec':       {'rect': (1.0, 5.0, -8.0, 1.0), 'color': W['navy']},
    'temple':     {'rect': (-6.0, 1.0, -8.0, 5.0), 'color': W['navy'], 'h': 4.5},
    'drawing':    {'rect': (1.0, 12.5, 1.0, 5.0), 'color': W['white'], 'h': 4.4},
    'chrono':     {'rect': (12.5, 19.2, 0.0, 8.5), 'color': W['white'], 'open': {'e'}},
    'anatomy':    {'rect': (5.0, 12.5, 5.0, 11.0), 'color': W['white'], 'sides': {'s': W['black']}, 'h': 4.4},
    'hidden':     {'rect': (12.5, 16.5, 8.5, 11.5), 'color': W['navy']},
    'asia':       {'rect': (7.5, 12.5, 11.0, 16.0), 'color': W['white']},
    'epilogue':   {'rect': (0.0, 7.5, 11.0, 17.0), 'color': W['white'], 'sides': {'w': W['navy']}, 'open': {'s'}},
})
ROOM_FLOOR['temple'] = 'floorPale'
# 방 바닥 다시 (위에서 만든 것은 첫 배치 기준이라 지우고 새로)
floor.bm.free()
floor = Assembly('floor', C_STATIC)
poly_face(floor, OUTLINE, -0.06, M['carpetGrey'], tile=3)
for rid, r in ROOMS.items():
    x0, x1, z0, z1 = r['rect']
    floor.add(box(x1 - x0, 0.06, z1 - z0), T((x0 + x1) / 2, -0.03, (z0 + z1) / 2), M[ROOM_FLOOR.get(rid, 'carpetGrey')], 3)

DOORS = [
    (11.8, 12.2, -12.0, -10.2),    # 서문 → 빨간 스튜디오 (초상 벽 북쪽 끝)
    (5.5, 8.5, -12.2, -11.8),      # 빨간 스튜디오 → 회색 방
    (4.8, 5.2, -17.0, -13.4),      # 회색 방 → Phooey 복도
    (-8.2, -7.8, -16.8, -13.2),    # Phooey → 빨간 방 (복도 끝에 A-One)
    (-15.5, -13.5, -10.2, -9.8),   # 빨간 방 → 흰 방
    (-14.7, -12.8, -3.2, -2.8),    # 흰 방 → 흰 복도 (콜라주 두 점)
    (-14.8, -12.4, 3.8, 4.2),      # 흰 복도 → Heads 흰 복도 (왕관 두상·가면)
    (-14.2, -12.2, 6.8, 7.2),      # Heads 복도 끝 → 검은 방 (자화상)
    (-12.2, -10.2, 6.8, 7.2),      # 검은 방 → Cartoons 쪽 통로
    (-11.8, -9.6, 3.8, 4.2),       # 통로 → Cartoons
    (-6.2, -5.8, -9.9, -8.1),      # Cartoons → Words and Signs
    (2.0, 4.5, -8.2, -7.8),        # Words → Museum Security
    (0.8, 1.2, -6.8, -5.2),        # Museum Security → 검은 커튼 → Temple
    (0.8, 1.2, -2.0, 0.6),         # (Museum Security 남쪽 끝은 Temple 과 벽)
    (0.8, 1.2, 1.5, 4.5),          # Temple → It's All Drawing
    (12.3, 12.7, 1.2, 4.8),        # Drawing → 연보·영상 (복도 끝에 프로젝션)
    (12.3, 12.7, 5.8, 8.3),        # 연보 → Anatomy
    (12.3, 12.7, 9.0, 11.0),       # Anatomy → Hidden Signs (Emblem 방, 넓은 입구)
    (11.0, 12.4, 10.8, 11.2),      # Anatomy → Asia
    (7.3, 7.7, 11.0, 16.0),        # Asia · Epilogue 는 빨간 카펫이 이어진 한 방 (사진: 왼쪽 두 작품, 끝 EXU, 오른쪽 Universal)
    (-0.2, 0.2, 14.4, 16.9),       # Epilogue → 검은 출구 커튼 (EXU 벽 왼쪽)
]

DECALS = []
ART = []          # (room, side, u, y, w, h, slug, display)
FREE = []


def A(room, side, u, y, w, h, slug, display='unframed_stretcher'):
    ART.append((room, side, u, y, w, h, slug, display))


def D(room, side, u, y, w, h, slug, emit_k=0.0):
    DECALS.append((room, side, u, y, w, h, gmat(slug, emit_k) if isinstance(slug, str) else slug))


# 1 서문·Studio of the Street — 입구 정면 초상 벽 (베이지), 서문 패널
D('preface', 'w', 7.05, 1.8, 9.5, 3.6, 'preface_portrait_wall')
D('preface', 's', 4.7, 1.8, 1.9, 1.47, 'preface_text_panel')
A('studioRed', 'n', 5.0, 1.6, 1.805, 1.09, 'car_crash')
A('studioRed', 'w', 4.5, 1.55, 2.197, 1.226, 'symphony_no1', 'unframed_panel')
A('studioRed', 's', 3.5, 1.6, 1.37, 1.67, 'number4')
# 2 회색 방 — 냉장고·화병 좌대, 뉴욕 뉴욕, 기차·자동차·배
A('studioGrey', 's', 7.5, 1.62, 2.262, 1.284, 'new_york_new_york')
A('studioGrey', 'e', 2.7, 1.55, 1.17, 0.71, 'train_car_ship', 'paper_oak')
# 3 Phooey & Fun Gallery — 왼쪽 네이비 벽, 오른쪽 흑백 사진 벽
A('phooey', 's', 6.5, 1.55, 3.55, 1.78, 'phooey')
D('phooey', 'n', 6.5, 2.15, 5.6, 4.3, 'fun_gallery_photo_mural')
D('phooey', 's', 11.4, 1.9, 1.3, 0.97, 'phooey_section_panel')
FREE.append(('phooey_ledge',))
A('phooey', 's', 1.3, 1.55, 0.762, 0.635, 'warrior_1982', 'paper_white')
A('phooey', 's', 2.6, 1.55, 0.67, 0.93, 'general_choi_young', 'dark_wood_frame')
# 4 Warriors & Power Figures — 빨간 방
A('red', 'w', 4.6, 1.65, 1.838, 1.829, 'aone_king')
for k in range(7):
    A('red', 'w', 0.55 + k * 0.4, 1.5, 0.229, 0.305, f'ink_drawing_{k + 1}', 'paper_black')
D('red', 'n', 5.0, 1.9, 1.3, 1.33, 'warriors_section_panel')
# 흰 방: Farina, 검은 끝벽 Black Figure, Blue Skies / 흰 복도: 콜라주 두 점
A('white', 'e', 4.0, 1.75, 1.73, 2.185, 'farina', 'black_frame')
A('white', 's', 2.2, 1.55, 2.44, 1.88, 'black_figure')
A('white', 'w', 3.5, 1.6, 2.1, 0.7, 'blue_skies', 'unframed_panel')
D('white', 'e', 1.3, 1.9, 1.2, 1.23, 'warriors_section_panel')
A('whiteCorr', 'w', 2.2, 1.7, 1.727, 2.183, 'untitled_1985_collage_woman', 'white_box_frame')
A('whiteCorr', 'w', 5.2, 1.7, 1.727, 2.183, 'joy_collage_skeleton', 'white_box_frame')
# 5 Heads and Masks — 검은 작은 방, 정면 금색 액자 자화상
A('headsBlack', 's', 0.8, 1.75, 0.61, 0.915, 'self_portrait_1983', 'gold_frame')
A('headsCorr', 'e', 1.6, 1.6, 1.016, 1.016, 'heads_two_crowned_heads', 'white_box_frame')
A('headsCorr', 'w', 1.6, 1.6, 0.71, 1.02, 'heads_mask_painting', 'white_box_frame')
D('whiteCorr', 'e', 6.0, 1.9, 1.1, 0.84, 'heads_section_panel')
# 6 Cartoons — 흰 방, 가운데 이젤 좌대, Bombero 검은 가벽
A('cartoons', 'w', 7.5, 1.6, 1.88, 1.416, 'job_analysis', 'black_frame')
A('cartoons', 'e', 8.5, 1.6, 1.83, 1.525, 'la_vieja')
A('cartoons', 'n', 3.25, 1.55, 0.9, 0.7, 'skier', 'black_frame')
A('cartoons', 'w', 11.2, 1.55, 0.71, 1.016, 'cartoons_untitled_1982_drawing', 'paper_black')
D('cartoons', 'e', 12.6, 1.9, 1.2, 1.13, 'cartoons_section_panel')
# 7 Words and Signs — 긴 흰·회색 복도
A('words', 'e', 2.5, 1.85, 1.917, 2.454, 'untitled_1983_soap_box_panels', 'white_box_frame')
D('words', 's', 1.0, 1.9, 1.1, 1.2, 'words_section_panel')
A('words', 's', 2.9, 1.65, 1.54, 1.677, 'ancient_scientist')
A('words', 's', 4.6, 1.5, 0.785, 0.53, 'color_of_a_yam', 'paper_black')
A('words', 's', 5.7, 1.5, 0.76, 0.56, 'louis_armstrong', 'paper_oak')
A('words', 's', 6.95, 1.5, 1.06, 0.75, 'snake', 'paper_black')
A('words', 'n', 5.0, 1.6, 1.02, 1.52, 'brown_circle', 'black_frame')
# Museum Security — 네이비, Masonic Lodge 는 깊은 상자 안
A('msec', 's', 2.0, 1.95, 2.134, 2.134, 'museum_security_broadway_meltdown')
FREE.append(('ledge', 'msec', 's', 2.0, 2.6))
# 8 Temple of Words — 검은 커튼 뒤, 네이비 벽·밝은 바닥, 노트 페이지 격자
A('temple', 'n', 3.5, 1.85, 3.465, 2.39, 'untitled_1986_pyramid_crane', 'white_box_frame')
D('temple', 'e', 3.4, 1.9, 1.4, 0.96, 'temple_section_panel')
# 9 It's All Drawing — 반구대 탁본(낮은 흰 선반 위), 맞은편 드로잉 한 줄
D('drawing', 'n', 5.5, 2.37, 8.32, 3.9, 'bangudae_rubbing')
D('drawing', 'w', 2.0, 1.9, 1.2, 1.18, 'panel_its_all_drawing')
for k, (slug, w_, h_, disp) in enumerate((('untitled_grid', 0.457, 0.61, 'paper_oak'), ('black_soap', 0.6, 0.9, 'paper_white'),
                                          ('jackie_robinson', 0.56, 0.76, 'paper_black'), ('peso_neto', 0.56, 0.76, 'paper_white'),
                                          ('untitled_1982_arches_woodframe', 0.55, 0.75, 'dark_wood_frame'),
                                          ('untitled_1982_tar_asbestos', 0.51, 0.76, 'paper_black'),
                                          ('untitled_1982_oilstick_head', 0.406, 0.5, 'paper_white'),
                                          ('untitled_warrior_1981', 0.279, 0.418, 'paper_oak'))):
    A('drawing', 's', 1.4 + k * 1.2, 1.55, w_, h_, slug, disp)
A('drawing', 's', 10.8, 1.7, 0.46, 0.86, 'chusa_mirror_inscription', 'dark_wood_frame')
# 연보·영상
D('chrono', 'n', 3.6, 1.9, 6.4, 1.62, 'chronology_wall')
D('chrono', 'n', 0.6, 2.1, 0.8, 2.2, 'chronology_column_1960s')
# 10 Anatomy — 검은 벽 앞 흰 낮은 좌대 위 Flesh and Spirit
A('anatomy', 's', 3.2, 2.4, 3.683, 3.683, 'flesh_and_spirit', 'unframed_panel')
D('anatomy', 'w', 3.0, 1.75, 4.6, 2.59, 'asia_projection_interview_still', 1.2)   # 방 끝 인터뷰 영상 (소개서 사진)
A('anatomy', 'n', 6.2, 1.6, 1.85, 1.55, 'ultraviolet')
A('anatomy', 'n', 4.0, 1.65, 1.525, 1.675, 'lungs_and_bladder', 'dark_wood_frame')
A('anatomy', 'n', 1.9, 1.65, 0.902, 1.524, 'study_of_feet')
D('anatomy', 's', 6.6, 1.9, 0.9, 0.85, 'panel_anatomy')
# Hidden Signs — Emblem 하나만 (뒤에서 빛)
D('hidden', 'w', 1.75, 1.9, 1.1, 1.12, 'panel_hidden_signs')
# 11 Basquiat in Asia — 프로젝션 벽, 추사 현판, 중국 음식
D('asia', 'e', 2.5, 1.65, 4.6, 2.59, 'asia_projection_mississippi_still', 1.2)
A('asia', 's', 1.3, 1.6, 1.5, 2.0, '2half_hours_chinese_food', 'white_box_frame')
A('asia', 's', 3.3, 1.6, 0.915, 1.22, 'chinese_man_orange', 'oak_frame')
A('asia', 'n', 1.8, 2.65, 1.666, 0.40, 'chusa_hakwiyujong', 'dark_wood_frame')
A('asia', 'n', 1.8, 1.5, 2.19, 0.84, 'chusa_panjeon', 'dark_wood_frame')
D('asia', 'w', 0.6, 1.9, 1.0, 0.94, 'panel_basquiat_in_asia')
# 12 Epilogue — 끝 네이비 벽 EXU, 왼쪽(남) 출구 커튼
A('epilogue', 'w', 1.7, 1.5, 2.54, 1.99, 'exu')
A('epilogue', 'n', 4.0, 1.65, 1.003, 1.257, 'universal', 'white_box_frame')
D('epilogue', 'n', 6.3, 1.9, 1.1, 0.98, 'panel_epilogue')

WALLS = roomkit.build(walls, ROOMS, DOORS, DECALS, WALL_H, WALL_T, W['white'])
for (room, side, u, w_) in (('words', 'e', 2.5, 2.3), ('temple', 'n', 3.5, 3.8)):
    f = roomkit.wall_face(room, side, u, ROOMS, WALL_T)
    walls.add(box(w_, 0.5, 0.45), f @ T(0, 0.25, 0.225), W['coal'], 1)
f = roomkit.wall_face('msec', 's', 2.0, ROOMS, WALL_T)                            # Museum Security 아래 낮은 단
walls.add(box(3.0, 0.3, 0.6), f @ T(0, 0.15, 0.3), W['navy'], 1)
walls.add(box(12.0, 0.12, 0.3), T(-1.5, 0.06, -13.0 - WALL_T / 2 - 0.15), W['navy'], 1)                 # Phooey 네이비 벽 아래 낮은 단

# ── 작품 걸기 + 캡션 + 조명 ─────────────────────────────────────
spots = []


def hang(frame, w, h, y, slug, display, spot=True, cap=True):
    f = frame @ T(0, y, 0)
    depth = gallery.artwork(works, f, w, h, gmat(slug), display, M)
    if cap:
        gallery.label(works, frame @ T(w / 2 + 0.25, 1.45, 0), M)
    if spot:
        spots.append((frame, w, h, y, depth))


for (room, side, u, y, w, h, slug, disp) in ART:
    hang(roomkit.wall_face(room, side, u, ROOMS, WALL_T), w, h, y, slug, disp)

# 서문 초상 벽에 끼운 양면 창문 작품 (앞: 서문 쪽, 뒤: 빨간 스튜디오 쪽)
fw = T(12.0, 1.82, -7.68, PI / 2)
works.add(bevel_box(1.1, 1.05, WALL_T + 0.16, 0.01), fw, M['frameWhite'], 1)
gallery.slab_art(works, fw @ T(0, 0, WALL_T / 2 + 0.081), 0.945, 0.88, 0.02, gmat('found_window_front'), M['frameWhite'])
gallery.slab_art(works, fw @ T(0, 0, -WALL_T / 2 - 0.081, PI), 0.945, 0.88, 0.02, gmat('found_window_back'), M['frameWhite'])
spots.append((T(12.0 + WALL_T / 2, 0, -7.68, PI / 2), 0.95, 0.9, 1.82, 0.1))

# 회색 방: 긴 흰 좌대 위 Fun Fridge + Vase
PX, PZ = 10.6, -14.6
works.add(bevel_box(3.4, 0.3, 1.1, 0.01), T(PX, 0.15, PZ), M['plinth'], 1)
fr = T(PX - 0.8, 0.3, PZ)
fridge_front = gmat('fun_fridge_front')
works.add(bevel_box(0.61, 1.435, 0.62, 0.03), fr @ T(0, 0.7175, -0.02), M['frameWhite'], 1)
works.add(plane(0.58, 1.40), fr @ T(0, 0.7175, 0.291), fridge_front, tile=None)


def vase(bm):
    prof = [(0.0, 0.0), (0.14, 0.0), (0.2, 0.08), (0.25, 0.28), (0.24, 0.42), (0.17, 0.53), (0.12, 0.58), (0.13, 0.61), (0.0, 0.61)]
    layer = bm.loops.layers.uv.active
    rings = [[bm.verts.new((r * math.cos(a), y, r * math.sin(a))) for a in [k / 32 * 2 * PI for k in range(33)]] for r, y in prof]
    for i, (ra, rb) in enumerate(zip(rings, rings[1:])):
        for k in range(32):
            f = bm.faces.new((ra[k], rb[k], rb[k + 1], ra[k + 1]))
            for lp, (uu, vv) in zip(f.loops, ((k / 32, i / 8), (k / 32, (i + 1) / 8), ((k + 1) / 32, (i + 1) / 8), ((k + 1) / 32, i / 8))):
                lp[layer].uv = (uu, vv)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


works.add(vase, T(PX + 0.9, 0.3, PZ), gmat('vase_unwrap150'), tile=None)
spots.append((T(PX, 0, PZ + 0.6), 3.0, 1.6, 1.0, 0.0))
gallery.stanchion_line(works, [(PX - 2.0, PZ + 1.2), (PX + 2.0, PZ + 1.2)], M)

# Phooey 복도 입구 검은 가벽 + 유명 야구 선수 초상
bp = T(6.6, 0, -15.2, PI / 2)
gallery.wall(walls, (6.6, -13.9), (6.6, -16.5), 3.6, 0.3, W['black'])
hang(bp @ T(0, 0, 0.15), 1.105, 1.273, 1.65, 'famous_ballplayer', 'black_frame')

# 빨간 방: 무신도 8폭 병풍 벽장 (붉은 속, 유리 앞) + 백남준 로봇
vf = roomkit.wall_face('red', 'n', 4.3, ROOMS, WALL_T)
for sx in (-1, 1):                                                               # 벽장 옆판
    works.add(box(0.15, 2.45, 0.6), vf @ T(sx * 2.475, 1.225, 0.3), W['burgundy'], 1)
works.add(box(5.1, 0.4, 0.6), vf @ T(0, 0.2, 0.3), W['burgundy'], 1)               # 창턱 0.4
works.add(box(5.1, 0.3, 0.6), vf @ T(0, 2.3, 0.3), W['burgundy'], 1)               # 윗판 (하향등)
gallery.slab_art(works, vf @ T(0, 1.2, 0.08), 4.07, 1.265, 0.08, gmat('shaman_screen_8panel'), M['frameDark'])
glass.add(box(4.8, 1.75, 0.012), vf @ T(0, 1.275, 0.58), M['glass'], 1)
for k in range(5):
    emit.add(cyl(0.04, 0.04, 0.01, 12), vf @ T(-1.9 + k * 0.95, 2.144, 0.3), M['downLens'])
    light(C_LIGHT, f'vitrine_{k}', 'SPOT', tuple(vf @ V((-1.9 + k * 0.95, 2.13, 0.3))), tuple(vf @ V((-1.9 + k * 0.95, 1.0, 0.05))),
          energy=40, color=(1.0, 0.93, 0.82), spot=1.0, blend=0.6, size=0.03)
contour = json.load(open(f'{SHOTS}/bq_paik_robot_contour.json'))
rb = T(-10.4, 0, -12.4, PI / 2 - 0.5)
works.add(bevel_box(1.55, 0.12, 0.7, 0.01), rb @ T(0, 0.06, 0), M['batten'], 1)
gallery.extrude_card(works, rb @ T(0, 0.12 - 0.035 * 1.93, 0), contour['pts'], 1.5, 1.93, 0.4, gmat('paik_robot_front'), M['frameBlack'])
spots.append((rb @ T(0, 0, 0.5), 1.5, 1.9, 1.1, 0.0))
gallery.stanchion_line(works, [(-11.6, -13.4), (-11.8, -11.2), (-10.0, -10.8)], M)

# Cartoons: 가운데 낮은 흰 좌대 위 이젤, Bombero 검은 가벽
EZ_ = T(-9.4, 0, -1.2, 0.5)
works.add(bevel_box(1.8, 0.25, 1.4, 0.01), EZ_ @ T(0, 0.125, 0), M['plinth'], 1)
ea = EZ_ @ T(0, 0.25, 0)
for lx, lz in ((-0.45, 0.25), (0.45, 0.25), (0.0, -0.45)):
    g, m = tube(ea @ V((lx, 0, lz)), ea @ V((lx * 0.25, 1.36, lz * 0.2)), 0.025, 8)
    works.add(g, m, M['batten'])
gallery.slab_art(works, ea @ T(0, 0.95, 0.2, 0, -0.12), 1.07, 0.78, 0.03, gmat('easel_board_front'), M['batten'])
works.add(box(1.2, 0.05, 0.12), ea @ T(0, 0.52, 0.26), M['batten'], 1)
spots.append((EZ_ @ T(0, 0, 1.0), 1.1, 1.3, 1.0, 0.0))
gallery.stanchion_line(works, [(-10.8, 0.4), (-8.0, 0.4)], M)
gallery.wall(walls, (-11.0, -6.2), (-7.4, -6.2), 3.6, 0.3, W['black'])
hang(T(-9.2, 0, -6.05, 0), 2.3, 1.648, 1.65, 'bombero', 'unframed_stretcher')

# Museum Security: Masonic Lodge 를 네이비 깊은 상자 안에
mf = roomkit.wall_face('msec', 'e', 2.6, ROOMS, WALL_T)
for s in (-1, 1):
    works.add(box(0.12, 2.9, 0.7), mf @ T(s * 1.36, 1.75, 0.35), W['navy'], 1)
works.add(box(2.84, 0.12, 0.7), mf @ T(0, 3.26, 0.35), W['navy'], 1)
works.add(box(2.84, 0.12, 0.7), mf @ T(0, 0.24, 0.35), W['navy'], 1)
hang(mf, 1.96, 2.19, 1.75, 'masonic_lodge', 'unframed_panel', cap=False)

# Temple of Words: 노트 페이지 격자 (흰 액자 5줄), 가운데 검은 상자 + 받침 진열장, 낮은 탁자 진열장
pages = [f'notebook_page_{i:02d}' for i in range(1, 20)]
PAGE_MATS = [gmat(p) for p in pages]


def notebook_grid(room, side, u0, cols, rows=5):
    for c in range(cols):
        for r in range(rows):
            f = roomkit.wall_face(room, side, u0 + c * 0.42, ROOMS, WALL_T) @ T(0, 0.75 + r * 0.42, 0)
            gallery._moulding(works, f, 0.3, 0.36, 0.025, 0.03, M['frameWhite'])
            gallery.slab_sides(works, f @ T(0, 0, 0.02), 0.3, 0.36, 0.02, M['mat'])
            gallery._face(works, f @ T(0, -0.18, 0.02), 0.3, 0.36, M['mat'],
                          [(0, 0.18, 0.247, 0.319, PAGE_MATS[(c * rows + r) % len(PAGE_MATS)])], 1)


notebook_grid('temple', 'w', 0.8, 7)
notebook_grid('temple', 'w', 4.6, 7)
notebook_grid('temple', 'w', 8.4, 7)
notebook_grid('temple', 's', 0.6, 6)
notebook_grid('temple', 's', 4.0, 5)
for (x, z) in ((-4.3, 0.2), (-4.3, 2.4), (-1.6, 2.4)):
    gallery.vitrine(works, glass, T(x, 0, z), 1.3, 0.75, 0.85, 0.2, M)
    for k in range(2):
        works.add(plane(0.247, 0.319), T(x - 0.3 + k * 0.6, 0.852, z, 0, -PI / 2), gmat(f'notebook_vitrine_cover_{k + 1}'), tile=None)
BX, BZ = -3.4, -2.6
walls.add(box(2.7, 4.5, 3.7), T(BX, 2.25, BZ), W['black'], 2)                   # 가운데 검은 상자 3.7×2.7×4.5 (동쪽 = 입구 쪽)
for (dx, dz, sx, sz) in ((1.36, 0, 0.02, 0.7),):
    pass
works.add(box(0.3, 0.72, 0.72), T(BX + 1.2, 1.9, BZ), M['frameBlack'], 1)        # 벽감 (안은 짙게)
works.add(plane(0.46, 0.5), T(BX + 1.351, 1.9, BZ, PI / 2), gmat('dizzy_sunny_side_up_boxed'), tile=None)
gallery.vitrine(works, glass, T(BX + 2.0, 0, BZ), 0.5, 0.5, 1.05, 0.35, M)
works.add(plane(0.4, 0.28), T(BX + 2.0, 1.052, BZ, PI / 2, -PI / 2), gmat('hunminjeongeum_spread'), tile=None)
spots.append((T(BX + 1.35, 0, BZ, PI / 2), 0.5, 0.5, 1.9, 0.0))
# Jimmy Best: 양면 유리 액자 (바닥 받침)
jb = T(-3.0, 0, 1.2, PI / 2)
works.add(bevel_box(0.36, 0.06, 0.3, 0.01), jb @ T(0, 0.03, 0), M['frameBlack'], 1)
works.add(box(0.03, 1.2, 0.03), jb @ T(0, 0.66, 0), M['frameBlack'], 1)
gallery.slab_art(works, jb @ T(0, 1.45, 0.012), 0.3, 0.45, 0.024, gmat('jimmy_best_on_his_back'), M['frameBlack'])
# Tar Tax 원판: 입구 옆 검은 벽의 불 켜진 벽감
tf_ = roomkit.wall_face('temple', 'e', 4.6, ROOMS, WALL_T)
works.add(box(0.7, 0.7, 0.3), tf_ @ T(0, 1.6, 0.15), M['frameBlack'], 1)
works.add(cyl(0.225, 0.225, 0.02, 48), tf_ @ T(0, 1.6, 0.31, 0, PI / 2), gmat('tar_tax_disc'), tile=None)
spots.append((tf_, 0.5, 0.5, 1.6, 0.3))
# 검은 커튼 (Museum Security → Temple)
for k in range(14):
    works.add(box(0.08, 3.0, 0.12), T(1.0 + (0.03 if k % 2 else -0.03), 1.5, -6.75 + k * 0.115), M['curtain'], 1)

# It's All Drawing: 반구대 탁본 앞 낮은 흰 선반
walls.add(box(8.6, 0.35, 0.5), T(6.5, 0.175, 1.0 + WALL_T / 2 + 0.25), M['plinth'], 1)
for k in range(4):
    spots.append((roomkit.wall_face('drawing', 'n', 2.4 + k * 2.1, ROOMS, WALL_T), 2.0, 3.9, 2.37, 0.0))
# 연보 방: 복도 끝에 보이는 영상 프로젝션 벽
walls.add(box(0.3, 3.6, 4.0), T(18.6, 1.8, 2.9), W['white'], 1)
emit.add(plane(3.6, 2.03), T(18.38, 2.0, 2.9, -PI / 2), gmat('asia_projection_painting_head_still', 1.2), tile=None)
light(C_LIGHT, 'proj_bounce', 'AREA', (18.2, 2.0, 2.9), (10, 2, 2.9), energy=60, color=(0.9, 0.9, 1.0), size=3)
# Anatomy: 흰 낮은 좌대
walls.add(box(6.0, 0.25, 1.4), T(8.2, 0.125, 11.0 - WALL_T / 2 - 0.7), M['plinth'], 1)
gallery.stanchion_line(works, [(5.4, 8.9), (11.0, 8.9)], M)
# Hidden Signs: Emblem 뒤에서 빛 (발광)
ef = roomkit.wall_face('hidden', 'e', 1.75, ROOMS, WALL_T)
works.add(box(1.52, 1.34, 0.1), ef @ T(0, 1.65, 0.05), M['frameBlack'], 1)
emit.add(plane(1.4, 1.23), ef @ T(0, 1.65, 0.101), gmat('emblem_backlit', 0.8), tile=None)
# Epilogue: EXU 네이비 벽 왼쪽 검은 출구 커튼 (0.4m 뒤), 벽 위 초록 비상구등, 커튼 앞 안내 사인
for k in range(22):
    works.add(box(0.1, 3.3, 0.12), T(-0.4 + (0.035 if k % 2 else -0.035), 1.65, 14.45 + k * 0.11), M['curtain'], 1)
walls.add(box(0.3, 0.3, 2.6), T(-0.4, 3.45, 15.65), W['navy'], 1)
emit.add(box(0.02, 0.18, 0.5), T(0.12, 3.0, 14.1), gmat('exit_sign_board', 0.6))
sg = T(1.2, 0, 15.6, PI / 2)
works.add(cyl(0.15, 0.16, 0.02, 20), sg @ T(0, 0.01, 0), M['rig'], 1)
works.add(cyl(0.015, 0.015, 1.1, 8), sg @ T(0, 0.57, 0), M['rig'], 1)
gallery.slab_art(works, sg @ T(0, 1.24, 0.012, 0, -0.2), 0.42, 0.3, 0.02, gmat('exit_sign_board'), M['rig'])

# 작품 앞 차단봉 (큰 작품)
for (room, side, u, y, w, h, slug, disp) in ART:
    if w * h > 2.5:
        f = roomkit.wall_face(room, side, u, ROOMS, WALL_T)
        p0 = f @ V((-w / 2 - 0.2, 0, 1.0))
        p1 = f @ V((w / 2 + 0.2, 0, 1.0))
        gallery.stanchion_line(works, [(p0.x, p0.z), (p1.x, p1.z)], M)

# ── 트랙 조명: 작품마다 앞 2m 천장 레일에 스포트 ─────────────────────
for i, (frame, w, h, y, depth) in enumerate(spots):
    base = frame @ V((0, RAIL_Y, 2.0))
    side = (frame.to_3x3() @ V((1, 0, 0))).normalized()
    a, b = base - side * max(0.8, w / 2 + 0.3), base + side * max(0.8, w / 2 + 0.3)
    gallery.track(rig, emit, [(a.x, a.z), (b.x, b.z)], RAIL_Y, HALL_H, M, rod_every=1.4)
    aim = frame @ V((0, y, depth))
    n_heads = 1 if w < 1.6 else 2
    for k in range(n_heads):
        at = base + side * ((k - (n_heads - 1) / 2) * w * 0.4)
        lens = gallery.spot_head(rig, emit, at, aim, M)
        light(C_LIGHT, f'spot_{i}_{k}', 'SPOT', tuple(lens), tuple(aim), energy=(300 + w * h * 160) / n_heads,
              color=(1.0, 0.9, 0.76), spot=min(1.2, 0.25 + max(w, h) * 0.18), blend=0.45, size=0.04)
print('spots', len(spots))

# ── B2 로비 (동쪽) · 입구 파사드 ─────────────────────────────────
# 소개서 입구 시뮬레이션·현장 사진: 흰 유광 바닥, 왼쪽(남) 검은 BASQUIAT 타이틀 판, 가운데 입구(안에 초상 벽이 보임),
# 빨간 안내대, 오른쪽(북) 기울어진 검은 판에 리지 힘멜 사진. 판들은 윗부분이 로비 쪽으로 기울어 있다.
foyer.add(box(12.0, 0.1, 22.0), T(26.0, -0.05, -6.0), M['foyerFloor'], 2)
DZ0, DZ1 = -4.4, -1.0                                                # 입구 (홀 동쪽 벽)


def lean_panel(x, z0, z1, h, lean, mat_front, mat_back, t=0.3):
    """윗부분이 +x(로비) 쪽으로 lean 만큼 기운 판 (앞면 = +x)"""
    def build(bm):
        layer = bm.loops.layers.uv.active
        L = z1 - z0
        P = [(0, 0), (L, 0), (L, h), (0, h)]
        fr = [bm.verts.new((t / 2 + lean * (y / h), y, -(zz - L / 2))) for zz, y in P]
        bk = [bm.verts.new((-t / 2 + lean * (y / h), y, -(zz - L / 2))) for zz, y in P]
        ff = bm.faces.new(fr)
        fb = bm.faces.new(list(reversed(bk)))
        sides = [bm.faces.new((fr[i], fr[(i + 1) % 4], bk[(i + 1) % 4], bk[i])) for i in range(4)]
        bm.normal_update()
        if ff.normal.x < 0:
            for f_ in [ff, fb] + sides:
                f_.normal_flip()
        for lp in ff.loops:
            lp[layer].uv = ((-lp.vert.co.z + L / 2) / L, lp.vert.co.y / h)
        ff.material_index = 0
        for f_ in [fb] + sides:
            f_.material_index = 1
    foyer.add(build, T(x, 0, (z0 + z1) / 2), [mat_front, mat_back], tile=None)


lean_panel(20.6, DZ1 + 0.3, DZ1 + 3.1, 4.4, 0.35, gmat('entrance_title_panel'), M['frameBlack'])
lean_panel(20.9, DZ0 - 6.2, DZ0 - 0.4, 4.2, 0.45, gmat('entrance_himmel_panel'), M['frameBlack'])
# 입구 문틀 (검은 기울어진 포털)
for zz in (DZ0 - 0.15, DZ1 + 0.15):
    foyer.add(box(0.6, 3.6, 0.3), T(20.1, 1.8, zz), M['frameBlack'], 1)
foyer.add(box(0.6, 0.6, DZ1 - DZ0 + 0.6), T(20.1, 3.9, (DZ0 + DZ1) / 2), M['frameBlack'], 1)
# 빨간 안내대 (흰 윗판)
foyer.add(bevel_box(0.6, 1.05, 0.6, 0.01), T(21.8, 0.525, DZ1 + 1.2), M['counterRed'], 1)
foyer.add(bevel_box(0.64, 0.12, 0.64, 0.01), T(21.8, 1.11, DZ1 + 1.2), M['frameWhite'], 1)
# 로비 벽 (흰 DDP 곡면)
for (a_, b_) in (((20.2, 4.0), (31.0, 4.0)), ((31.0, 4.0), (31.0, -16.0)), ((31.0, -16.0), (20.2, -16.0))):
    gallery.wall(foyer, a_, b_, 6.0, 0.4, M['hallWall'])
light(C_LIGHT, 'foyer_a', 'AREA', (26, 6.5, -6), (26, 0, -6), energy=5000, color=(1.0, 0.98, 0.95), size=10)

# 홀 동쪽 벽의 입구 구멍: 해당 조각 지우고 상인방
# (hall 조각은 위에서 이미 더했으므로 입구 앞에 문틀 안쪽 면만 둔다 — 아래에서 hall 을 다시 만든다)
hall.bm.free()
hall = Assembly('hall', C_STATIC)
for i in range(N):
    (x1, z1), (x2, z2) = OUTLINE[i], OUTLINE[(i + 1) % N]
    d = V((x2 - x1, 0, z2 - z1))
    mx, mz = (x1 + x2) / 2, (z1 + z2) / 2
    mid = T(mx, 0, mz, math.atan2(-d.z, d.x))
    H_ = HALL_H - COVE
    if mx > 18 and DZ0 - 0.3 < mz < DZ1 + 0.3:                   # 입구: 3.6m 위만
        hall.add(plane(d.length + 0.02, H_ - 3.6), mid @ T(0, 3.6 + (H_ - 3.6) / 2, 0), M['hallWall'], 3)
        continue
    if -2.8 < mx < 0.5 and mz > 15.5:                                # 출구 (디자인둘레길로)
        hall.add(plane(d.length + 0.02, H_ - 3.2), mid @ T(0, 3.2 + (H_ - 3.2) / 2, 0), M['hallWall'], 3)
        continue
    hall.add(plane(d.length + 0.02, H_), mid @ T(0, H_ / 2, 0), M['hallWall'], 3)

# ── 디자인둘레길 아트샵 (남쪽 곡면 복도) ─────────────────────────
# 소개서 아트샵 렌더·현장 사진: 흰 접힌 벽(약 12m, 높이 2.9m) 하단 1m 버건디 띠, 벽 글자, 걸린 후디·티셔츠,
# 카운터(버건디 하부·흰 윗판), 사진 기둥 4개, 검은 원형 테이블, 둥근 모서리의 기울어진 사진 판
SH_PTS = [(-6.0, 20.2), (0.0, 20.6), (6.0, 21.2), (12.0, 20.6)]
foyer.add(box(22.0, 0.1, 5.2), T(3.0, -0.08, 19.8), M['foyerFloor'], 2)
for k, ((xa, za), (xb, zb)) in enumerate(zip(SH_PTS, SH_PTS[1:])):
    slug = 'shop_title_wall_left' if k == 0 else 'shop_title_wall_right' if k == 1 else None
    L = math.hypot(xb - xa, zb - za)
    dec = [(0, 1.45, L, 2.9, gmat(slug))] if slug else []
    gallery.wall(foyer, (xb, zb), (xa, za), 2.9, 0.3, W['white'], decals_f=dec)
    if not slug:
        gallery.wall(foyer, (xb, zb), (xa, za), 1.0, 0.44, W['burgundy'])
for (x, z, w_, d_) in ((-2.0, 18.9, 2.4, 0.8), (3.5, 19.3, 1.8, 0.8), (8.5, 19.2, 1.2, 0.8)):
    foyer.add(bevel_box(w_, 0.85, d_, 0.01), T(x, 0.425, z), W['burgundy'], 1)
    foyer.add(bevel_box(w_ + 0.04, 0.05, d_ + 0.04, 0.01), T(x, 0.875, z), M['frameWhite'], 1)
for x in (-4.0, 1.0, 6.0, 11.0):                                   # 사진 기둥
    slab = T(x, 1.3, 17.9, 0)
    gallery.slab_art(foyer, slab @ T(0, 0, 0.25), 1.2, 2.6, 0.5, gmat('shop_pillar_wrap_side'), M['frameWhite'])
for (x, z) in ((-0.5, 18.4), (9.8, 18.3)):
    foyer.add(cyl(0.75, 0.75, 0.03, 40), T(x, 0.74, z), M['frameBlack'], 1)
    foyer.add(cyl(0.04, 0.04, 0.72, 10), T(x, 0.37, z), M['frameBlack'], 1)
    foyer.add(cyl(0.3, 0.3, 0.02, 24), T(x, 0.01, z), M['frameBlack'], 1)
light(C_LIGHT, 'shop_a', 'AREA', (0, 4.5, 19.5), (0, 0, 19.5), energy=2500, color=(1.0, 0.97, 0.92), size=8)
light(C_LIGHT, 'shop_b', 'AREA', (8, 4.5, 19.5), (8, 0, 19.5), energy=2500, color=(1.0, 0.97, 0.92), size=8)

# ── 전시장 바탕빛 (어두운 방, 작품만 밝게) ────────────────────────
for (x, z) in ((-10, -10), (8, -10), (-10, 6), (8, 8)):
    light(C_LIGHT, f'ambient_{x}_{z}', 'AREA', (x, HALL_H - 0.4, z), (x, 0, z), energy=260, color=(0.92, 0.94, 1.0), size=12)

for a in (hall, ceil, floor, walls, works, foyer, emit, rig, glass):
    a.build(smooth=(a is rig))
for n in ('bqHallWall', 'bqCeiling', 'bqSlot'):
    bpy.data.materials[n].use_backface_culling = True

bw = bpy.data.worlds.new('bq_world')
bw.use_nodes = True
bw.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.02, 0.025, 1)
scene.world = bw

camera(C_CAM, 'cam_overview', (40, 44, 48), (0, 0, 0), 42)
camera(C_CAM, 'cam_entrance', (29.0, 1.7, -3.2), (20.0, 2.1, -3.4), 58)        # 소개서 입구 시뮬레이션
camera(C_CAM, 'cam_intro', (19.0, 1.7, -3.2), (12.0, 1.8, -5.0), 62)          # 서문 초상 벽 (현장 사진)
camera(C_CAM, 'cam_studio', (11.4, 1.7, -3.8), (5.5, 1.7, -9.5), 64)          # 빨간 카펫 스튜디오
camera(C_CAM, 'cam_gallery', (15.8, 1.65, -13.2), (4.0, 1.8, -15.6), 62)      # 회색 방 → 네이비 벽·빨간 방 (소개서)
camera(C_CAM, 'cam_phooey', (4.2, 1.65, -14.4), (-16.0, 1.9, -14.0), 62)
camera(C_CAM, 'cam_red', (-9.0, 1.65, -15.8), (-16.5, 1.7, -12.6), 64)
camera(C_CAM, 'cam_cartoons', (-9.6, 1.65, 3.2), (-9.4, 1.6, -9.0), 66)
camera(C_CAM, 'cam_temple', (0.5, 1.7, -2.6), (-6.0, 1.6, -2.6), 70)
camera(C_CAM, 'cam_corridor', (1.6, 1.65, 3.0), (18.5, 1.8, 2.9), 60)         # 드로잉 복도 (소개서)
camera(C_CAM, 'cam_anatomy', (12.3, 1.65, 7.4), (5.0, 1.8, 8.2), 62)
camera(C_CAM, 'cam_epilogue', (12.2, 1.65, 13.4), (0.0, 1.5, 13.0), 60)
camera(C_CAM, 'cam_shop', (-5.0, 1.65, 18.6), (10.0, 1.4, 20.8), 60)
scene.camera = bpy.data.objects['cam_intro']
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
print('basquiat built:', {c.name: len(c.objects) for c in (C_STATIC, C_DYNAMIC, C_EMIT, C_LIGHT, C_CAM)})
