"""동대문디자인플라자(DDP) 뮤지엄 전시1관 — 장 미셸 바스키아: 과거와 미래를 잇는 상징적 기호들 (2025.9.23~2026.1.31)

  python3 scripts/blender/bmcp.py exec scripts/blender/basquiat_scene.py

자료 (assets-src/refs/basquiat/index.md — 네이버 블로그 약 400개·노루페인트/팬톤 설치 사진·기사, 149장):
- 전시1관 (DDP 대관 안내서): 지하 2층, 1,216㎡, 39.7 × 35.4m, 층고 8.8m, 흰 에폭시 바닥, 흰 천장에 검은 선형 조명 슬롯,
  곡면 벽. 평면 윤곽은 DDP VR 투어 공식 치수 평면도의 벽 중심선을 실측 (hall1_outline_v2.json, 1220 vs 공식 1216m²,
  변 34.5·24.8·8.4·18.7·17.3·19m, 층고 8.8m). 평면도의 작은 사각형 14개는 기둥이 아니라 바닥 전기박스.
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

HALL_H, RAIL_Y = 8.8, 4.15                        # 홀 껍데기 8.8m, 트랙 레일 4.15m (소핏 4.6m 에서 0.45 드롭)
# 가벽 두께·높이·보이는 소핏 높이는 layout_v2.json 의 globals 에서 읽는다

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
OUT = json.load(open(f'{REFS}/hall1_outline_v2.json'))['outline']


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


poly_face(floor, OUTLINE, 0.0, M['epoxy'], tile=3)                      # 홀 맨바닥은 흰 유광 에폭시
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

# ── 방 배치 · 작품: assets-src/refs/basquiat/layout_v2.md/json 이 원본 ────────────
#    17개 구역(817m²)·18개 문·67점·거치물 16개. 모두 hall1_outline_v2 안에 들어가도록 검증됨.
#    v1 과의 큰 차이: 가벽 기본 3.0m(특수벽 4.4~4.8m), 가벽은 천장까지 닿지 않고 위가 비어 있다,
#    보이는 천장(소핏) 4.6m, 작품 중심 1.45~1.50m, 차단봉은 0.4m 기둥 + 바닥 레일.
LAY = json.load(open(f'{REFS}/layout_v2.json'))
GL = LAY['globals']
W = M
WALL_T = GL['wall_thickness']
SOFFIT = GL['visible_soffit_h']
ROOMS = {z['id']: {'rect': tuple(z['rect']), 'color': W[z['walls']['n']],
                   'sides': {k: W[v] for k, v in z['walls'].items()}, 'h': z['wall_h']} for z in LAY['zones']}
ROOM_FLOOR = {z['id']: z['floor'] for z in LAY['zones']}
ZONE = {z['id']: z for z in LAY['zones']}
for rid, r in ROOMS.items():                                # 구역 바닥 (에폭시 위 카펫 8mm)
    x0, x1, z0, z1 = r['rect']
    floor.add(plane(x1 - x0, z1 - z0), T((x0 + x1) / 2, 0.008, (z0 + z1) / 2, 0, PI / 2), M[ROOM_FLOOR[rid]], 3)


def U(room, side, u):
    """layout_v2 의 u(면을 보는 사람 기준 왼쪽→오른쪽) → rooms.py 의 u(x0/z0 부터)"""
    x0, x1, z0, z1 = ROOMS[room]['rect']
    L = (x1 - x0) if side in 'ns' else (z1 - z0)
    return u if side in ('n', 'e') else L - u


def face(room, side, u):
    return roomkit.wall_face(room, side, U(room, side, u), ROOMS, WALL_T)


DOORS = []
for d in LAY['doors']:
    if d['zone'] not in ROOMS:
        continue
    x0, x1, z0, z1 = ROOMS[d['zone']]['rect']
    u0, u1, sd = d['u0'], d['u1'], d['face']
    if sd == 'n':
        DOORS.append((x0 + u0, x0 + u1, z0 - WALL_T, z0 + WALL_T))
    elif sd == 's':
        DOORS.append((x1 - u1, x1 - u0, z1 - WALL_T, z1 + WALL_T))
    elif sd == 'e':
        DOORS.append((x1 - WALL_T, x1 + WALL_T, z0 + u0, z0 + u1))
    else:
        DOORS.append((x0 - WALL_T, x0 + WALL_T, z1 - u1, z1 - u0))

# 작품: 벽에 그려 넣을 것(패널·텍스트·프로젝션)과 걸 것(액자·캔버스)을 나눈다
FLAT = ('panel', 'wall_text', 'full_height_print', 'printed_vinyl', 'projection', 'wall_wash', 'ultra_matte')
FRAME_MAP = (('white_box_frame', 'white_box_frame'), ('plexi_box', 'white_box_frame'), ('black_box_frame', 'black'),
             ('heavy_black_frame', 'black'), ('black_frame', 'black'), ('gold_frame', 'gold'), ('oak_frame', 'oak'),
             ('dark_wood', 'dark_wood'), ('paper_black', 'paper_black'), ('paper_white', 'paper_white'),
             ('paper_oak', 'paper_oak'), ('plywood', 'unframed_panel'), ('unframed_panel', 'unframed_panel'))
ALIAS = {'studio_of_the_street_text': 'studio_of_the_street_text_panel', 'tar_tax': 'tar_tax_disc',
         'emblem': 'emblem_backlit', 'notebook_translation_projection': 'asia_projection_painting_head_still',
         'interview_projection': 'asia_projection_interview_still', 'exu_explainer_monitor': 'epilogue_exu_monitor_still',
         'magic_worms': 'untitled_grid', 'untitled_1985_words': 'black_soap', 'picasso': 'peso_neto'}


def disp_of(s):
    for key, val in FRAME_MAP:
        if key in s:
            return val
    return 'unframed_stretcher'


DECALS, ART, FREE = [], [], []
for w_ in LAY['works']:
    if w_['zone'] not in ROOMS:
        continue
    slug, d = ALIAS.get(w_['slug'], w_['slug']), w_['display']
    rec = (w_['zone'], w_['face'], w_['u'], w_['y'], w_['w'], w_['h'], slug, d)
    if any(k in d for k in FLAT):
        emit_k = 1.2 if ('projection' in d or 'wall_wash' in d or 'monitor' in d) else 0.0
        DECALS.append((w_['zone'], w_['face'], U(w_['zone'], w_['face'], w_['u']), w_['y'], w_['w'], w_['h'],
                       gmat(slug, emit_k)))
    else:
        ART.append((w_['zone'], w_['face'], w_['u'], w_['y'], w_['w'], w_['h'], slug, disp_of(d)))
FS = {(f['zone'], f['kind']): f for f in LAY['freestanding']}
_fg = FS[('phooey', 'panel')]                               # Fun Gallery 전면 사진은 복도 북쪽 벽면 그래픽으로
DECALS.append(('phooey', 'n', (_fg['a'][0] + _fg['b'][0]) / 2 - ROOMS['phooey']['rect'][0],
               1.55, abs(_fg['b'][0] - _fg['a'][0]), 2.9, gmat('fun_gallery_photo_mural')))
print('zones', len(ROOMS), 'doors', len(DOORS), 'art', len(ART), 'decals', len(DECALS))

WALLS = roomkit.build(walls, ROOMS, DOORS, DECALS, GL['wall_h_standard'], WALL_T, W['white'])

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
    hang(face(room, side, u), w, h, y, slug, disp)

# 서문 벽에 끼운 양면 창문 작품 (앞: 서문 쪽, 뒤: 빨간 스튜디오 쪽) — layout_v2 Z01
fw = face('preface', 'w', 6.9) @ T(0, 1.55, 0)
works.add(bevel_box(1.15, 1.20, WALL_T + 0.16, 0.01), fw @ T(0, 0, -WALL_T / 2 - 0.02), M['frameWhite'], 1)
gallery.slab_art(works, fw @ T(0, 0, 0.081), 0.945, 0.88, 0.02, gmat('found_window_front'), M['frameWhite'])
gallery.slab_art(works, fw @ T(0, 0, -WALL_T - 0.121, PI), 0.945, 0.88, 0.02, gmat('found_window_back'), M['frameWhite'])
spots.append((face('preface', 'w', 6.9), 0.95, 0.9, 1.55, 0.1))

# ── layout_v2 의 거치물(freestanding) ────────────────────────────


def fs(zone, kind):
    return FS.get((zone, kind))


def free_wall(a, b, h, t, mat):
    gallery.wall(walls, tuple(a), tuple(b), h, t, mat)


# 회색 방: 낮은 흰 좌대 위 Fun Fridge + Vase (중심 6.8, -15.6 / 3.0 × 1.2 × 0.4)
p = fs('studioGrey', 'plinth')
PX, PZ = p['centre']
works.add(bevel_box(p['size'][0], p['size'][2], p['size'][1], 0.01), T(PX, p['size'][2] / 2, PZ), M['plinth'], 1)
fr = T(PX - 0.75, p['size'][2], PZ)
works.add(bevel_box(0.61, 1.435, 0.62, 0.03), fr @ T(0, 0.7175, -0.02), M['frameWhite'], 1)
works.add(plane(0.58, 1.40), fr @ T(0, 0.7175, 0.291), gmat('fun_fridge_front'), tile=None)


def vase(bm):
    prof = [(0.0, 0.0), (0.14, 0.0), (0.2, 0.08), (0.25, 0.28), (0.24, 0.42), (0.17, 0.53), (0.12, 0.58), (0.13, 0.61), (0.0, 0.61)]
    layer = bm.loops.layers.uv.active
    rings = [[bm.verts.new((r * math.cos(a), y, r * math.sin(a))) for a in [k / 32 * 2 * PI for k in range(33)]] for r, y in prof]
    for i, (ra, rb) in enumerate(zip(rings, rings[1:])):
        for k in range(32):
            f_ = bm.faces.new((ra[k], rb[k], rb[k + 1], ra[k + 1]))
            for lp, (uu_, vv) in zip(f_.loops, ((k / 32, i / 8), (k / 32, (i + 1) / 8), ((k + 1) / 32, (i + 1) / 8), ((k + 1) / 32, i / 8))):
                lp[layer].uv = (uu_, vv)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


works.add(vase, T(PX + 0.95, p['size'][2], PZ), gmat('vase_unwrap150'), tile=None)
spots.append((T(PX, 0, PZ + 0.7), 3.0, 1.6, 1.0, 0.0))
gallery.stanchion_line(works, [(PX - 1.8, PZ + 1.0), (PX + 1.8, PZ + 1.0)], M)

# 회색 방 → Phooey: 검은 자립 가벽 (동쪽 면에 유명 야구 선수 초상)
q = fs('studioGrey', 'partition')
free_wall(q['a'], q['b'], q['height'], q['thickness'], W['black'])
bp = T(q['a'][0] + q['thickness'] / 2, 0, (q['a'][1] + q['b'][1]) / 2, -PI / 2)
hang(bp, 1.105, 1.273, 1.50, 'famous_ballplayer', 'white_box_frame')

# Phooey 복도: Fun Gallery 사진 벽(자립) + 네이비 벽 아래 낮은 단
lg = fs('phooey', 'ledge')
x0, x1, z0, z1 = ROOMS['phooey']['rect']
walls.add(box(x1 - x0, lg['size'][2], lg['size'][1]), T((x0 + x1) / 2, lg['size'][2] / 2, z1 - WALL_T / 2 - lg['size'][1] / 2), W['navy'], 1)

# Warriors 흰 방: 백남준 로봇 (자립, 흰 벽 앞)
q = fs('warriorsWhite', 'sculpture')
contour = json.load(open(f'{SHOTS}/bq_paik_robot_contour.json'))
rb = T(q['centre'][0], 0, q['centre'][1], 0.35)
works.add(bevel_box(q['base'][0], q['base'][2], q['base'][1], 0.01), rb @ T(0, q['base'][2] / 2, 0), M['batten'], 1)
gallery.extrude_card(works, rb @ T(0, q['base'][2] - 0.035 * q['size'][2], 0), contour['pts'], q['size'][0], q['size'][2], 0.4,
                     gmat('paik_robot_front'), M['frameBlack'])
spots.append((rb @ T(0, 0, 0.8), 1.5, 1.9, 1.1, 0.0))
gallery.stanchion_line(works, [(q['centre'][0] - 1.1, q['centre'][1] + 1.0), (q['centre'][0] + 1.1, q['centre'][1] + 1.0)], M)

# 빨간 방: 무신도 8폭 병풍 벽장 (붉은 속, 유리 앞, 아래 조명)
vf = face('red', 'e', 3.8)
for sx in (-1, 1):
    works.add(box(0.15, 2.45, 0.6), vf @ T(sx * 2.475, 1.225, 0.3), W['burgundy'], 1)
works.add(box(5.1, 0.4, 0.6), vf @ T(0, 0.2, 0.3), W['burgundy'], 1)
works.add(box(5.1, 0.3, 0.6), vf @ T(0, 2.3, 0.3), W['burgundy'], 1)
gallery.slab_art(works, vf @ T(0, 1.2, 0.08), 4.07, 1.265, 0.08, gmat('shaman_screen_8panel'), M['frameDark'])
glass.add(box(4.8, 1.75, 0.012), vf @ T(0, 1.275, 0.58), M['glass'], 1)
for k in range(5):
    emit.add(cyl(0.04, 0.04, 0.01, 12), vf @ T(-1.9 + k * 0.95, 2.144, 0.3), M['downLens'])
    light(C_LIGHT, f'vitrine_{k}', 'SPOT', tuple(vf @ V((-1.9 + k * 0.95, 2.13, 0.3))), tuple(vf @ V((-1.9 + k * 0.95, 1.0, 0.05))),
          energy=40, color=(1.0, 0.93, 0.82), spot=1.0, blend=0.6, size=0.03)

# Cartoons: 낮은 흰 좌대 위 이젤 + Bombero 챠콜 자립 가벽 + 흰 커튼 서비스 문
q = fs('cartoons', 'plinth')
EZ_ = T(q['centre'][0], 0, q['centre'][1], 0.5)
works.add(bevel_box(q['size'][0], q['size'][2], q['size'][1], 0.01), EZ_ @ T(0, q['size'][2] / 2, 0), M['plinth'], 1)
ea = EZ_ @ T(0, q['size'][2], 0)
for lx, lz in ((-0.45, 0.25), (0.45, 0.25), (0.0, -0.45)):
    g, m = tube(ea @ V((lx, 0, lz)), ea @ V((lx * 0.25, 1.36, lz * 0.2)), 0.025, 8)
    works.add(g, m, M['batten'])
gallery.slab_art(works, ea @ T(0, 0.95, 0.2, 0, -0.12), 1.07, 0.78, 0.03, gmat('easel_board_front'), M['batten'])
works.add(box(1.2, 0.05, 0.12), ea @ T(0, 0.52, 0.26), M['batten'], 1)
spots.append((EZ_ @ T(0, 0, 1.1), 1.1, 1.3, 1.0, 0.0))
gallery.stanchion_line(works, [(q['centre'][0] - 1.6, q['centre'][1] + 1.3), (q['centre'][0] + 1.6, q['centre'][1] + 1.3)], M)
q = fs('cartoons', 'partition')
free_wall(q['a'], q['b'], q['height'], q['thickness'], W['coal'])
hang(T((q['a'][0] + q['b'][0]) / 2, 0, q['a'][1] - q['thickness'] / 2, PI), 2.3, 1.648, 1.45, 'bombero', 'unframed_stretcher')

# Museum Security: 벽 아래 밝은 단 + Masonic Lodge 를 깊은 상자 안에
lg = fs('msec', 'ledge')
mx0, mx1, mz0, mz1 = ROOMS['msec']['rect']
walls.add(box(lg['size'][0], lg['size'][2], lg['size'][1]), T((mx0 + mx1) / 2, lg['size'][2] / 2, mz1 - WALL_T / 2 - lg['size'][1] / 2), W['coal'], 1)
mf = face('msec', 'e', 2.6)
for s in (-1, 1):
    works.add(box(0.12, 3.1, 1.8), mf @ T(s * 2.81, 1.75, 0.9), W['coal'], 1)
works.add(box(5.5, 0.12, 1.8), mf @ T(0, 3.16, 0.9), W['coal'], 1)
works.add(box(5.5, 0.2, 1.8), mf @ T(0, 0.1, 0.9), M['plinth'], 1)
hang(mf @ T(0, 0, 0.05), 1.96, 2.19, 1.75, 'masonic_lodge', 'unframed_panel', cap=False)

# ── Temple of Words: 노트 페이지 격자(4줄) · 가운데 검은 볼륨 · 탁자 진열장 · Jimmy Best ──
PAGE_MATS = [gmat(f'notebook_page_{i:02d}') for i in range(1, 20)]
ROW_Y = (1.07, 1.61, 2.15, 2.69)


def notebook_grid(room, side, u0, cols):
    """흰 박스 액자 0.36 × 0.44, 피치 0.44 × 0.54, 4줄 (layout_v2 temple/grid)"""
    for c in range(cols):
        for r, yy in enumerate(ROW_Y):
            f = face(room, side, u0 + c * 0.44) @ T(0, yy, 0)
            gallery._moulding(works, f, 0.36, 0.44, 0.04, 0.03, M['frameWhite'])
            gallery.slab_sides(works, f @ T(0, 0, 0.02), 0.36, 0.44, 0.02, M['mat'])
            gallery._face(works, f @ T(0, -0.22, 0.02), 0.36, 0.44, M['mat'],
                          [(0, 0.22, 0.247, 0.319, PAGE_MATS[(c * 4 + r) % len(PAGE_MATS)])], 1)


for (sd, u0_, cols) in (('e', 0.6, 11), ('s', 1.0, 10), ('s', 6.2, 7), ('w', 0.8, 9)):
    notebook_grid('temple', sd, u0_, cols)
q = fs('temple', 'volume')                                         # 가운데 검은 볼륨 (주변 벽보다 높다)
BX, BZ = q['centre']
BW, BD, BH = q['size']
walls.add(box(BW, BH, BD), T(BX, BH / 2, BZ), W['black'], 2)
nf = T(BX + BW / 2, 0, BZ, PI / 2)                                  # 입구(동)쪽 면의 밝은 벽감
works.add(box(0.72, 0.72, 0.3), nf @ T(0, 1.85, -0.15), M['frameBlack'], 1)
works.add(plane(0.5, 0.54), nf @ T(0, 1.85, 0.005), gmat('notebook_cover_framed_front'), tile=None)
emit.add(cyl(0.035, 0.035, 0.01, 12), nf @ T(0, 2.18, -0.14), M['downLens'])
spots.append((nf, 0.6, 0.6, 1.85, 0.0))
gallery.vitrine(works, glass, nf @ T(0, 0, 1.0, PI / 2), 0.5, 0.45, 0.9, 0.35, M)
works.add(plane(0.4, 0.28), nf @ T(0, 0.902, 1.0, 0, -PI / 2), gmat('hunminjeongeum_spread'), tile=None)
q = fs('temple', 'table_vitrine')                                   # 긴 검은 탁자 진열장 (노트 8권)
TVX, TVZ = q['centre']
gallery.vitrine(works, glass, T(TVX, 0, TVZ), q['size'][0], q['size'][1], q['size'][2], q['hood'], M)
for k in range(8):
    works.add(plane(0.247, 0.319), T(TVX - 1.75 + k * 0.5, q['size'][2] + 0.002, TVZ, 0, -PI / 2),
              gmat(f'notebook_vitrine_cover_{k % 3 + 1}'), tile=None)
q = fs('temple', 'case')                                            # Jimmy Best: 양면 유리 액자
jb = T(q['centre'][0], 0, q['centre'][1], PI / 2)
works.add(bevel_box(0.4, 0.06, 0.34, 0.01), jb @ T(0, 0.03, 0), M['frameBlack'], 1)
works.add(box(0.03, q['hood'], 0.03), jb @ T(0, 0.06 + q['hood'] / 2, 0), M['frameBlack'], 1)
gallery.slab_art(works, jb @ T(0, q['hood'] + 0.35, 0.012), 0.3, 0.45, 0.024, gmat('jimmy_best_on_his_back'), M['frameBlack'])
tf_ = face('temple', 'n', 8.4)                                      # Tar Tax 원판: 불 켜진 벽감
works.add(box(0.7, 0.7, 0.3), tf_ @ T(0, 1.6, 0.15), M['frameBlack'], 1)
works.add(cyl(0.225, 0.225, 0.02, 48), tf_ @ T(0, 1.6, 0.31, 0, PI / 2), gmat('tar_tax_disc'), tile=None)
spots.append((tf_, 0.5, 0.5, 1.6, 0.3))
# 검은 주름 커튼 (Museum Security → Temple): msec 남쪽 문 자리
dsec = next(d for d in LAY['doors'] if d['frm'] == 'msec')
cx0 = mx1 - dsec['u1']
for k in range(16):
    works.add(box(0.1, 3.4, 0.13), T(cx0 + 0.1 + k * 0.22, 1.7, mz1 + (0.04 if k % 2 else -0.04)), M['curtain'], 1)

# It's All Drawing: 반구대 탁본 앞 낮은 흰 선반 (곡벽 감실의 연석)
dx0, dx1, dz0, dz1 = ROOMS['drawing']['rect']
walls.add(box(8.6, 0.4, 0.4), T((dx0 + dx1) / 2, 0.2, dz0 + WALL_T / 2 + 0.2), M['plinth'], 1)
for k in range(4):
    spots.append((face('drawing', 'n', 2.4 + k * 2.1), 2.0, 3.9, 2.37, 0.0))

# Anatomy: Flesh and Spirit 벽 전체를 따라가는 낮은 흰 단
q = fs('anatomy', 'platform')
ax0, ax1, az0, az1 = ROOMS['anatomy']['rect']
works.add(bevel_box(q['size'][0], q['size'][2], q['size'][1], 0.01),
          T(ax0 + WALL_T / 2 + q['size'][1] / 2, q['size'][2] / 2, (az0 + az1) / 2, 0, 0, 0), M['plinth'], 1)
gallery.stanchion_line(works, [(ax0 + 1.8, az0 + 0.9), (ax0 + 1.8, az1 - 0.9)], M)

# Hidden Signs: Emblem 은 뒤에서 빛나는 배턴 조명 상자
ef = face('hidden', 'e', 1.6)
works.add(box(1.52, 1.34, 0.1), ef @ T(0, 1.65, 0.05), M['frameBlack'], 1)
emit.add(plane(1.4, 1.23), ef @ T(0, 1.65, 0.101), gmat('emblem_backlit', 0.8), tile=None)

# Epilogue: EXU 벽 왼쪽 검은 출구 커튼 · 초록 비상구등 · 재입장 불가 사인
ex0, ex1, ez0, ez1 = ROOMS['epilogue']['rect']
for k in range(22):
    works.add(box(0.11, 3.3, 0.13), T(ex0 - WALL_T / 2 + (0.04 if k % 2 else -0.04), 1.65, ez1 - 0.6 - k * 0.12, PI / 2), M['curtain'], 1)
emit.add(box(0.02, 0.18, 0.5), T(ex0 + 0.16, 3.0, ez1 - 0.5), gmat('exit_sign_board', 0.6))
sg = T(ex0 + 1.4, 0, ez1 - 1.4, PI / 2)
works.add(cyl(0.15, 0.16, 0.02, 20), sg @ T(0, 0.01, 0), M['rig'], 1)
works.add(cyl(0.015, 0.015, 1.1, 8), sg @ T(0, 0.57, 0), M['rig'], 1)
gallery.slab_art(works, sg @ T(0, 1.24, 0.012, 0, -0.2), 0.42, 0.3, 0.02, gmat('exit_sign_board'), M['rig'])

# 구역 위 보이는 소핏 (아래를 보는 한 겹). 홀의 8.8m 천장은 가운데 열린 곳에만 보인다.
for rid, r in ROOMS.items():
    x0, x1, z0, z1 = r['rect']
    cg = ZONE[rid].get('ceiling', {})
    ch = cg.get('h', SOFFIT)
    cm = M['slot'] if cg.get('type') == 'dark_painted' else M['ceiling']
    ceil.add(plane(x1 - x0 + 0.6, z1 - z0 + 0.6), T((x0 + x1) / 2, ch, (z0 + z1) / 2, 0, PI / 2), cm, 2)

# 큰 작품 앞 차단봉 (0.4m 기둥 + 바닥 레일)
for (room, side, u, y, w, h, slug, disp) in ART:
    if w * h > 2.5:
        f = face(room, side, u)
        p0 = f @ V((-w / 2 - 0.2, 0, 0.9))
        p1 = f @ V((w / 2 + 0.2, 0, 0.9))
        gallery.stanchion_line(works, [(p0.x, p0.z), (p1.x, p1.z)], M)

# ── 트랙 조명: 작품마다 앞 2m 천장 레일에 스포트 ─────────────────────
def rail_y(px, pz):
    """그 자리 구역의 소핏 높이에서 0.45 내려온 레일 높이 (방마다 천장이 다르다)"""
    for rid, r in ROOMS.items():
        x0, x1, z0, z1 = r['rect']
        if x0 - 0.3 <= px <= x1 + 0.3 and z0 - 0.3 <= pz <= z1 + 0.3:
            return ZONE[rid].get('ceiling', {}).get('h', SOFFIT) - 0.45
    return RAIL_Y


for i, (frame, w, h, y, depth) in enumerate(spots):
    o = frame @ V((0, 0, 1.0))
    ry_ = rail_y(o.x, o.z)
    base = frame @ V((0, ry_, 2.0))
    side = (frame.to_3x3() @ V((1, 0, 0))).normalized()
    a, b = base - side * max(0.8, w / 2 + 0.3), base + side * max(0.8, w / 2 + 0.3)
    gallery.track(rig, emit, [(a.x, a.z), (b.x, b.z)], ry_, ry_ + 0.45, M, rod_every=1.4)
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
DZ0, DZ1 = -8.0, -6.0                                                # 입구 (홀 동쪽 벽, layout_v2 preface e 면 u 2.2~4.2)


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
    if 6.3 < mx < 10.4 and mz > 15.5:                                # 출구 (디자인둘레길로, layout_v2 epilogue s 면)
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

# ── 전시장 바탕빛: 보이는 소핏(4.6m) 바로 아래에 구역마다 하나씩 ────────────
#    소핏을 8.8m 홀 천장 아래에 새로 깔았기 때문에 예전처럼 천장 높이에 두면 빛이 막힌다.
for rid, r in ROOMS.items():
    x0, x1, z0, z1 = r['rect']
    ch = ZONE[rid].get('ceiling', {}).get('h', SOFFIT)
    dark = ZONE[rid]['walls']['n'] in ('black', 'navy', 'coal') or rid in ('temple', 'msec', 'hidden', 'headsBlack')
    light(C_LIGHT, f'amb_{rid}', 'AREA', ((x0 + x1) / 2, ch - 0.25, (z0 + z1) / 2), ((x0 + x1) / 2, 0, (z0 + z1) / 2),
          energy=(34 if dark else 90) * (x1 - x0) * (z1 - z0) / 60, color=(0.96, 0.96, 1.0),
          size=min(x1 - x0, z1 - z0) * 0.8)
light(C_LIGHT, 'amb_hall', 'AREA', (0, HALL_H - 0.5, 0), (0, 0, 0), energy=400, color=(0.92, 0.94, 1.0), size=16)

for a in (hall, ceil, floor, walls, works, foyer, emit, rig, glass):
    a.build(smooth=(a is rig))
for n in ('bqHallWall', 'bqCeiling', 'bqSlot'):
    bpy.data.materials[n].use_backface_culling = True

bw = bpy.data.worlds.new('bq_world')
bw.use_nodes = True
bw.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.02, 0.025, 1)
scene.world = bw

camera(C_CAM, 'cam_overview', (40, 44, 48), (0, 0, 0), 42)
camera(C_CAM, 'cam_entrance', (29.0, 1.7, -6.0), (19.6, 2.1, -6.0), 58)        # B2 로비 → 검은 파사드
camera(C_CAM, 'cam_intro', (17.2, 1.6, -6.1), (12.2, 1.7, -6.6), 62)           # 서문 초상 벽 · 창문 작품
camera(C_CAM, 'cam_studio', (11.4, 1.6, -4.0), (5.6, 1.6, -8.4), 64)           # 빨간 카펫 스튜디오
camera(C_CAM, 'cam_grey', (11.2, 1.6, -11.2), (2.6, 1.6, -15.4), 64)           # 회색 방 (냉장고·화병 좌대)
camera(C_CAM, 'cam_phooey', (1.2, 1.6, -12.3), (-11.8, 1.7, -11.4), 62)        # Phooey 네이비 복도 → 빨간 방
camera(C_CAM, 'cam_red', (-13.0, 1.6, -11.8), (-18.8, 1.7, -7.0), 64)          # Warriors 빨간 방
camera(C_CAM, 'cam_white', (-12.0, 1.6, -4.2), (-18.6, 1.7, 1.6), 64)          # Warriors 흰 방 · 백남준 로봇
camera(C_CAM, 'cam_heads', (-13.2, 1.6, 4.0), (-13.2, 1.65, 11.4), 62)         # 흰 복도 → 검은 Heads 감실
camera(C_CAM, 'cam_cartoons', (-3.6, 1.6, 5.8), (-10.4, 1.6, -1.0), 66)        # Cartoons (이젤 좌대 · Bombero)
camera(C_CAM, 'cam_words', (-2.4, 1.6, 1.8), (11.4, 1.65, -1.8), 60)           # Words and Signs 긴 복도
camera(C_CAM, 'cam_msec', (18.4, 1.6, -1.8), (12.6, 1.75, 3.0), 62)            # Museum Security · Masonic 상자
camera(C_CAM, 'cam_temple', (16.8, 1.6, 5.6), (8.4, 1.7, 11.6), 66)            # Temple of Words (노트 격자)
camera(C_CAM, 'cam_drawing', (7.0, 1.6, 11.8), (-2.2, 1.9, 9.0), 62)           # It's All Drawing (반구대 탁본)
camera(C_CAM, 'cam_anatomy', (-3.4, 1.6, 7.2), (-9.0, 1.9, 11.4), 62)          # Anatomy (Flesh and Spirit)
camera(C_CAM, 'cam_asia', (1.4, 1.6, 15.6), (-4.4, 1.6, 13.6), 62)             # Basquiat in Asia (추사 현판)
camera(C_CAM, 'cam_epilogue', (10.0, 1.6, 17.2), (2.6, 1.55, 13.2), 60)        # Epilogue (EXU · 출구 커튼)
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
