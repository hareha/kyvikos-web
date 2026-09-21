"""동대문디자인플라자(DDP) 전시홀 — 장미셸 바스키아 SEOUL 〈과거와 미래를 잇는 상징적 기호들〉

  python3 scripts/blender/bmcp.py exec scripts/blender/basquiat_scene.py

자료: 소개서 11~14p 현장 사진·렌더
- 전시홀: 곡선 모서리 외벽, 어두운 회색 타공 천장에 휘어진 검은 조명 슬롯, 짙은 회색 카펫.
          천장에서 내려온 검은 파이프 행거 끝에 스포트라이트 (갤러리 사진).
- 입구: 흰 곡면 로비, 검은 로고 패널 + 기울어진 흰 포털 + 검은 포스터 패널, 마룬 안내 데스크.
- 인트로: 빨간 카펫, 베이지 벽에 초상 사진·'Studio of the Street' 글·박스 액자 작품.
- 갤러리: 네이비·검은 벽, 흰 벽에 작품, 흰 좌대 위 조형물·하늘색 도자기, 차단봉.
- 복도: 검은 벽에 대형 종이 연작 + 흰 낮은 좌대, 끝에 프로젝션 영상.
- 미디어룸·아트샵: 마룬 하단 띠의 흰 곡면 벽, 티셔츠·굿즈, 카운터.
작품 이미지는 현장 사진에서 잘라 원근을 편 것 (assets-src/shots/bq_r_*.png).
좌표: 전시홀 중심 원점. +z 로비·입구, -z 영상 복도, +x 미디어룸·아트샵.
"""
import importlib
import math
import random
import sys

sys.path.insert(0, '/Users/hare/Documents/큐비크스홈페이지/scripts/blender')
import lib  # noqa: E402

importlib.reload(lib)
from lib import (PI, SHOTS, Assembly, T, bevel_box, box, camera, collection, cyl, light, material,  # noqa: E402
                 mesh_source, plane, reset, sphere, tube)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

import gear  # noqa: E402
import props  # noqa: E402
importlib.reload(gear)
importlib.reload(props)

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

SA, SC, SE, SH = 26.0, 17.0, 0.5, 6.5      # 슈퍼타원 외벽 (반폭 x, 반폭 z, 지수, 높이)
WALL_H, RIG_Y = 4.2, 5.3


def shell_pt(t):
    c, s = math.cos(t), math.sin(t)
    return SA * math.copysign(abs(c) ** SE, c), SC * math.copysign(abs(s) ** SE, s)


M = {
    'carpet': material('bqCarpet', 'cotton_jersey', (0.34, 0.35, 0.37), 0.95, normal=0.8),
    'redCarpet': material('bqRedCarpet', 'cotton_jersey', (0.32, 0.03, 0.03), 0.95, normal=0.8),
    'lobby': material('bqLobby', 'marble_01', (0.9, 0.9, 0.9), 0.3),
    'shell': material('bqShell', 'painted_plaster_wall', (0.3, 0.3, 0.32), 0.85),
    'ceiling': material('bqCeiling', 'painted_plaster_wall', (0.22, 0.22, 0.23), 0.9),
    'white': material('bqWhite', 'painted_plaster_wall', (0.88, 0.87, 0.84), 0.85),
    'beige': material('bqBeige', 'painted_plaster_wall', (0.6, 0.48, 0.36), 0.85),
    'navy': material('bqNavy', 'painted_plaster_wall', (0.08, 0.11, 0.2), 0.85),
    'black': material('bqBlack', None, (0.02, 0.02, 0.022), 0.6),
    'dark': material('bqDark', None, (0.012, 0.012, 0.014), 0.4, 0.3),
    'maroon': material('bqMaroon', None, (0.3, 0.04, 0.05), 0.6),
    'frameWood': material('bqFrameWood', None, (0.32, 0.2, 0.1), 0.5),
    'frameWhite': material('bqFrameWhite', None, (0.9, 0.9, 0.88), 0.5),
    'vase': material('bqVase', None, (0.2, 0.55, 0.65), 0.2, coat=0.8),
    'rig': material('bqRig', None, (0.015, 0.015, 0.017), 0.4, 0.5),
    'lampLens': material('bqLampLens', None, (1, 1, 1), emit=(1.0, 0.93, 0.8), emit_strength=40),
    'slotFrame': material('bqSlotFrame', None, (0.012, 0.012, 0.014), 0.4, 0.3),
    'slot': material('bqSlot', None, (1, 1, 1), emit=(0.95, 0.95, 1.0), emit_strength=1.2),
    'stripWarm': material('bqStrip', None, (1, 1, 1), emit=(1.0, 0.92, 0.8), emit_strength=10),
    'poster': material('bqPoster', image_base=f'{SHOTS}/bq_r_poster.png', rough=0.6),
    'intro': material('bqIntro', image_base=f'{SHOTS}/bq_r_intro.png', rough=0.8),
    'logo': material('bqLogo', image_base=f'{SHOTS}/bq_logo.png', rough=0.6),
    'photo': material('bqPhoto', image_base=f'{SHOTS}/bq_photo.png', rough=0.7),
    'shopWall': material('bqShop', image_base=f'{SHOTS}/bq_shop.png', rough=0.7),
    'projection': material('bqProjection', emit_image=f'{SHOTS}/bq_r_projection.png', emit_strength=1.6, rough=0.9),
    'screen': material('bqScreen', emit_image=f'{SHOTS}/bq_screen.png', emit_strength=2.0, rough=0.3),
    'tee': material('bqTee', 'cotton_jersey', (0.02, 0.02, 0.022), 0.9, normal=0.6),
}
ART = {k: material(f'bqArt_{k}', image_base=f'{SHOTS}/bq_r_art_{k}.png', rough=0.75)
       for k in ('cart', 'back', 'blue', 'small', 'panels', 'organ')}
PLANT = props.load('potted_plant_02', 'src_plant', height=1.6, decimate=0.2, coll=C_SRC)

hall = Assembly('hall', C_STATIC)
floor = Assembly('floor', C_STATIC)
ceil = Assembly('ceiling', C_STATIC)
walls = Assembly('walls', C_STATIC)
works = Assembly('works', C_STATIC)
emit = Assembly('emissive', C_EMIT)
rig = Assembly('rig', C_DYNAMIC)

# ── 전시홀 쉘: 바닥 · 외벽 · 천장(타공판 + 휘어진 조명 슬롯) ─────────────
N = 96
pts = [shell_pt(i / N * 2 * PI) for i in range(N)]


def flat_poly(asm, poly, y, mat, tile=3.0, flip=False):
    def build(bm):
        vs = [bm.verts.new((x, 0, z)) for x, z in poly]
        f = bm.faces.new(vs if not flip else list(reversed(vs)))
        bmesh.ops.triangulate(bm, faces=[f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if flip:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    asm.add(build, T(0, y, 0), mat, tile)


flat_poly(floor, pts, 0.0, M['carpet'], 2.0)
hall.add(box(SA * 2 + 1, 0.2, SC * 2 + 1), T(0, -0.1, 0), M['shell'], 3)
for i in range(N):
    (x1, z1), (x2, z2) = pts[i], pts[(i + 1) % N]
    L = math.hypot(x2 - x1, z2 - z1)
    mx, mz = (x1 + x2) / 2, (z1 + z2) / 2
    ry = math.atan2(-(z2 - z1), x2 - x1)
    if mz > 10 and -23 < mx < -6:          # 입구 개구부 (로비 쪽)
        hall.add(box(L + 0.06, SH - 4.6, 0.4), T(mx, 4.6 + (SH - 4.6) / 2, mz, ry), M['shell'], 2)
        continue
    hall.add(box(L + 0.06, SH, 0.4), T(mx, SH / 2, mz, ry), M['shell'], 2)
# 천장 판 (살짝 안쪽)
flat_poly(ceil, [(x * 0.99, z * 0.99) for x, z in pts], SH, M['ceiling'], 3.0, flip=True)
# 휘어진 조명 슬롯 (사진: 천장을 가로지르는 검은 곡선 띠 + 안쪽 발광)
for k in range(-3, 4):
    prev = None
    for x in [x / 2 for x in range(-46, 47)]:
        z = k * 4.2 + math.sin(x * 0.12 + k) * 1.6
        zmax = SC * (1 - (abs(x) / SA) ** (2 / SE)) ** (SE / 2) - 0.8
        if abs(z) > zmax:
            prev = None
            continue
        p = V((x, SH - 0.03, z))
        if prev:
            d = p - prev
            ang = math.atan2(-d.z, d.x)
            ceil.add(plane(d.length + 0.02, 0.34), T((p.x + prev.x) / 2, SH - 0.02, (p.z + prev.z) / 2, ang, PI / 2), M['slotFrame'], 1)
            emit.add(plane(d.length + 0.02, 0.12), T((p.x + prev.x) / 2, SH - 0.05, (p.z + prev.z) / 2, ang, PI / 2), M['slot'])
        prev = p

# ── 로비 (흰 곡면) ─────────────────────────────────────────────
lobby = Assembly('lobby', C_STATIC)
lobby.add(box(34, 0.1, 13), T(-10, -0.05, 21.5), M['lobby'], 2.5)
curve = [V((-27 + t * 34, 0, 28 - math.sin(t * PI) * 1.2)) for t in [i / 24 for i in range(25)]]
for a, c in zip(curve, curve[1:]):
    d = c - a
    lobby.add(box(d.length + 0.05, 4.5, 0.4), T((a.x + c.x) / 2, 2.25, (a.z + c.z) / 2, math.atan2(-d.z, d.x)), M['white'], 2)
for (px, pz) in ((-19, 16), (-6, 17)):
    lobby.add(mesh_source(PLANT), T(px, 0, pz, random.uniform(0, PI)), list(PLANT.data.materials))


# ── 가벽 · 작품 · 조명 ─────────────────────────────────────────
spots = []


def wall(x1, z1, x2, z2, h=WALL_H, t=0.3, mat=None):
    d = V((x2 - x1, 0, z2 - z1))
    walls.add(box(d.length, h, t), T((x1 + x2) / 2, h / 2, (z1 + z2) / 2, math.atan2(-d.z, d.x)), mat or M['white'], 2)


def track_light(p_wall, normal, y_aim, w, name):
    """천장 파이프 행거 + 가로 트랙 + 스포트 (작품 앞 2.2m)"""
    base = p_wall + normal * 2.2
    g, m = tube(V((base.x, SH, base.z)), V((base.x, RIG_Y, base.z)), 0.02, 8)
    rig.add(g, m, M['rig'])
    side = V((-normal.z, 0, normal.x))
    a, b = base + side * 0.9, base - side * 0.9
    g, m = tube(V((a.x, RIG_Y, a.z)), V((b.x, RIG_Y, b.z)), 0.025, 8)
    rig.add(g, m, M['rig'])
    head = V((base.x, RIG_Y - 0.18, base.z))
    g, m = tube(V((base.x, RIG_Y, base.z)), head, 0.018, 8)          # 트랙 → 조명 머리
    rig.add(g, m, M['rig'])
    aim = (V((p_wall.x, y_aim, p_wall.z)) - head).normalized()
    g, m = tube(head - aim * 0.12, head + aim * 0.12, 0.07, 12, caps=True)
    rig.add(g, m, M['rig'])
    lens = head + aim * 0.125
    emit.add(sphere(0.05, 2), T(lens.x, lens.y, lens.z), M['lampLens'])
    light(C_LIGHT, name, 'SPOT', tuple(lens), (p_wall.x, y_aim, p_wall.z), energy=900 + w * 300,
          color=(1.0, 0.9, 0.76), spot=min(0.9, 0.3 + w * 0.12), blend=0.5, size=0.05)


def art(x, z, ry, w, h, key, y=2.0, frame='wood', spot=True):
    """작품: 로컬 +z = 앞면. 액자(두께 5cm) + 그림(액자 앞면에 붙음)"""
    f = T(x, 0, z, ry)
    if frame:
        works.add(bevel_box(w + 0.12, h + 0.12, 0.05, 0.008), f @ T(0, y, 0.025), M['frameWood' if frame == 'wood' else 'frameWhite'], 1)
        works.add(plane(w, h), f @ T(0, y, 0.058), ART[key], tile=None)
    else:
        works.add(bevel_box(w, h, 0.03, 0.004), f @ T(0, y, 0.015), M['frameWhite'], 1)
        works.add(plane(w, h), f @ T(0, y, 0.038), ART[key], tile=None)
    if spot:
        n = V((math.sin(ry), 0, math.cos(ry)))
        track_light(V((x, 0, z)), n, y, w, f'spot_{len(spots)}')
        spots.append((x, z))


def stanchions(pts_):
    for x, z in pts_:
        works.add(cyl(0.16, 0.16, 0.03, 20), T(x, 0.015, z), M['rig'], 1)
        works.add(cyl(0.022, 0.022, 0.9, 10), T(x, 0.47, z), M['rig'], 1)
        works.add(cyl(0.035, 0.03, 0.05, 12), T(x, 0.94, z), M['rig'], 1)


def plinth(x, z, w, d, h=0.3, ry=0.0):
    works.add(bevel_box(w, h, d, 0.01), T(x, h / 2, z, ry), M['white'], 1)


# 입구 (외부 그래픽)
EZ, EH = 13.6, 4.4


def slab(pts2, depth, holes=()):
    def build(bm):
        front = [bm.verts.new((x, y, depth / 2)) for x, y in pts2]
        back = [bm.verts.new((x, y, -depth / 2)) for x, y in pts2]
        bm.faces.new(front)
        bm.faces.new(list(reversed(back)))
        n = len(pts2)
        for k in range(n):
            bm.faces.new((front[k], back[k], back[(k + 1) % n], front[(k + 1) % n]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return build


walls.add(slab([(-21.3, 0), (-17.9, 0), (-17.6, EH), (-21.3, EH)], 0.3), T(0, 0, EZ), M['black'], 1)
works.add(plane(3.2, 4.0), T(-19.55, 2.3, EZ + 0.155), M['logo'], tile=None)
# 기울어진 흰 포털 (좌우 기둥 + 윗보, 안쪽이 입구)
walls.add(slab([(-17.5, 0), (-17.0, 0), (-16.7, 3.7), (-16.9, EH), (-17.1, EH)], 0.7), T(0, 0, EZ), M['white'], 1)
walls.add(slab([(-14.6, 0), (-14.1, 0), (-13.7, EH), (-14.3, 3.7)], 0.7), T(0, 0, EZ), M['white'], 1)
walls.add(slab([(-16.9, 3.7), (-14.3, 3.7), (-13.7, EH), (-17.1, EH)], 0.7), T(0, 0, EZ), M['white'], 1)
walls.add(box(2.4, 0.02, 0.7), T(-15.8, 0.01, EZ), M['maroon'], 1)
walls.add(slab([(-13.6, 0), (-6.8, 0), (-6.8, EH), (-13.2, EH)], 0.3), T(0, 0, EZ), M['black'], 1)
works.add(plane(5.9, 5.9 * 1150 / 1400), T(-10.05, 2.25, EZ + 0.155), M['poster'], tile=None)
works.add(bevel_box(1.1, 0.95, 0.65, 0.02), T(-18.7, 0.475, EZ + 1.0), M['maroon'], 1)
works.add(bevel_box(1.14, 0.08, 0.69, 0.01), T(-18.7, 0.99, EZ + 1.0), M['white'], 1)

# 인트로 (빨간 카펫 + 베이지 벽)
IZ = 8.5
floor.add(box(14, 0.012, 5), T(-16, 0.006, IZ + 2.6), M['redCarpet'], 2)
wall(-22.5, IZ, -9.6, IZ, mat=M['beige'])
works.add(plane(12.6, 12.6 * 718 / 2048), T(-16.05, 2.1, IZ + 0.155), M['intro'], tile=None)
track_light(V((-19, 0, IZ)), V((0, 0, 1)), 2.2, 4, 'intro_a')
track_light(V((-12, 0, IZ)), V((0, 0, 1)), 2.2, 3, 'intro_b')

# 갤러리 A (네이비·흰 벽, 좌대의 조형물·도자기)
wall(-8, 0, -8, 11, mat=M['navy'])
art(-7.84, 5.2, PI / 2, 1.7, 2.4, 'blue', frame='white')
wall(-6, -2, 5, -2)
art(-0.5, -1.84, 0, 3.0, 1.7, 'back', frame='wood')
wall(6, -2, 6, 11)
art(5.84, 5.5, -PI / 2, 2.4, 3.6, 'cart', y=2.2, frame=None)
art(5.84, 1.2, -PI / 2, 1.2, 1.3, 'small', frame='white', spot=False)
plinth(2.3, 4.8, 3.2, 1.5)
works.add(bevel_box(0.8, 1.4, 0.8, 0.02), T(1.5, 1.0, 4.8, 0.3), M['white'], 1)          # 그림 그린 캐비닛
for k in range(4):
    works.add(plane(0.8, 1.4), T(1.5, 1.0, 4.8, 0.3 + k * PI / 2) @ T(0, 0, 0.408), ART['back'], tile=None)
def vase(bm):
    prof = [(0.0, 0.0), (0.2, 0.0), (0.33, 0.25), (0.36, 0.45), (0.3, 0.65), (0.18, 0.74), (0.19, 0.8), (0.0, 0.8)]
    rings = []
    for r, y in prof:
        rings.append([bm.verts.new((r * math.cos(a), y, r * math.sin(a))) for a in [k / 24 * 2 * PI for k in range(24)]])
    for a, b in zip(rings, rings[1:]):
        for k in range(24):
            bm.faces.new((a[k], a[(k + 1) % 24], b[(k + 1) % 24], b[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
works.add(vase, T(3.1, 0.3, 5.0), M['vase'], 1)
track_light(V((2.3, 0, 4.8)), V((0, 0, 1)), 0.9, 2, 'plinth_a')
stanchions([(0.2, 6.3), (4.4, 6.3), (-3.5, 8.5), (-5.5, 3), (-2.5, 0)])

# 갤러리 B (검은 벽)
wall(-17, -12.5, -6, -12.5, h=4.6, mat=M['black'])
art(-11.5, -12.34, 0, 2.8, 2.0, 'back', y=2.1)
wall(-18, -12.5, -18, -3)
art(-17.84, -8, PI / 2, 1.9, 2.8, 'cart', y=2.2, frame='wood')
wall(-3, -12.5, -3, -3)
art(-3.16, -8, -PI / 2, 3.2, 2.1, 'blue', frame='wood')
plinth(-14.8, -5.2, 2.6, 1.6, 0.35)
f = T(-14.8, 0.35, -5.2, 0.4)
for lx, lz in ((-0.5, 0.35), (0.5, 0.35), (0, -0.45)):
    g, m = tube(f @ V((lx, 0, lz)), f @ V((0, 1.7, 0)), 0.025, 8)
    works.add(g, m, M['dark'])
works.add(bevel_box(1.1, 0.9, 0.04, 0.01), f @ T(0, 1.2, 0.2, 0, -0.15), M['frameWood'], 1)
works.add(plane(1.02, 0.82), f @ T(0, 1.2, 0.2, 0, -0.15) @ T(0, 0, 0.027), ART['small'], tile=None)
works.add(box(1.2, 0.04, 0.12), f @ T(0, 0.73, 0.22), M['frameWood'], 1)          # 이젤 받침대
g, m = tube(f @ V((0, 1.7, 0)), f @ V((0, 1.7, 0.2)), 0.02, 8)
works.add(g, m, M['dark'])
track_light(V((-14.8, 0, -5.2)), V((0, 0, 1)), 1.2, 1.5, 'easel')
stanchions([(-13, -3.8), (-9, -9.5), (-6, -9.5), (-5.5, -6)])

# 영상 복도 (검은 벽의 대형 연작 + 흰 낮은 좌대 + 끝 프로젝션)
ZN = -13.5
wall(1, ZN, 18.5, ZN, h=4.8, mat=M['black'])
for k in range(4):
    x = 3.4 + k * 3.25
    works.add(plane(3.15, 3.5), T(x, 2.5, ZN + 0.155), ART['panels'], tile=None)
    track_light(V((x, 0, ZN)), V((0, 0, 1)), 2.5, 3, f'panel_{k}')
works.add(bevel_box(16, 0.22, 0.9, 0.01), T(9.5, 0.11, ZN + 0.8), M['white'], 1)
wall(4, -6.5, 10.5, -6.5)
art(5.8, -6.66, PI, 1.1, 1.6, 'organ', frame='wood', spot=False)
art(8.6, -6.66, PI, 2.0, 2.8, 'organ', frame='wood')
wall(19.5, ZN, 19.5, -6.5, mat=M['white'])
emit.add(plane(4.2, 3.57), T(19.33, 2.1, -10.4, -PI / 2), M['projection'], tile=None)
stanchions([(3, -9.5), (8, -8.5), (13, -9.5), (16, -8)])
light(C_LIGHT, 'projection_bounce', 'AREA', (19.0, 2.1, -10.4), (10, 2, -10.4), energy=120, color=(0.8, 0.9, 0.7), size=3)

# 미디어룸
X0m, X1m, Z0m, Z1m = 11, 21, -4.5, 4
wall(X0m, Z0m, X1m, Z0m)
wall(X1m, Z0m, X1m, Z1m)
wall(X0m, Z0m, X0m, -1.2)
wall(X0m, 1.6, X0m, Z1m)
wall(X0m, Z1m, X1m, Z1m)
works.add(bevel_box(3.9, 2.3, 0.1, 0.01), T(16, 2.05, Z0m + 0.2), M['dark'], 1)
emit.add(plane(3.7, 2.1), T(16, 2.05, Z0m + 0.26), M['screen'], tile=None)
light(C_LIGHT, 'screen_glow', 'AREA', (16, 2.05, Z0m + 0.4), (16, 2, 4), energy=80, color=(0.85, 0.9, 1.0), size=3)

# 아트샵: 곡면 굿즈 벽 (마룬 하단 띠) + 카운터 + 옷걸이 + 사진 월
n = 12
cz = lambda x: 6.2 + 1.4 * ((x - 16) / 7) ** 2  # noqa: E731
xs = [9.2 + 14.0 * i / n for i in range(n + 1)]
WH = 3.6
for i in range(n):
    a, c = V((xs[i], 0, cz(xs[i]))), V((xs[i + 1], 0, cz(xs[i + 1])))
    d = c - a
    fr = T((a.x + c.x) / 2, 0, (a.z + c.z) / 2, math.atan2(-d.z, d.x))
    walls.add(box(d.length + 0.04, WH, 0.3), fr @ T(0, WH / 2, 0), M['white'], 2)
    walls.add(box(d.length + 0.04, 0.9, 0.02), fr @ T(0, 0.45, 0.16), M['maroon'], 1)
    for k in range(2):                                           # 걸린 티셔츠
        tx = -d.length / 4 + k * d.length / 2
        works.add(bevel_box(0.5, 0.62, 0.03, 0.01), fr @ T(tx, 1.55, 0.18), M['tee'], 1)
        works.add(bevel_box(0.72, 0.18, 0.03, 0.01), fr @ T(tx, 1.78, 0.18), M['tee'], 1)
        works.add(cyl(0.008, 0.008, 0.2, 6), fr @ T(tx, 1.95, 0.17, 0, PI / 2), M['rig'], 1)
emit.add(box(14, 0.04, 0.06), T(16, WH - 0.05, 7.4), M['stripWarm'])
for (x, z, w, d, ry) in ((10.8, 11.8, 1.1, 0.7, 0), (12.6, 8.9, 2.8, 0.8, -0.05), (16.5, 11.2, 2.2, 1.0, 0)):
    works.add(bevel_box(w, 0.85, d, 0.01), T(x, 0.425, z, ry), M['maroon'], 1)
    works.add(bevel_box(w + 0.04, 0.05, d + 0.04, 0.01), T(x, 0.875, z, ry), M['white'], 1)
f = T(19.6, 0, 9.4)
for sx in (-0.8, 0.8):
    g, m = tube(f @ V((sx, 0, 0)), f @ V((sx, 1.6, 0)), 0.02, 8)
    works.add(g, m, M['rig'])
g, m = tube(f @ V((-0.8, 1.6, 0)), f @ V((0.8, 1.6, 0)), 0.02, 8)
works.add(g, m, M['rig'])
for k in range(7):
    works.add(bevel_box(0.05, 0.75, 0.5, 0.01), f @ T(-0.6 + k * 0.2, 1.23, 0), M['tee'], 1)
wall(8.2, 7, 8.2, 14, h=4.0)
works.add(plane(6.6, 3.8), T(8.355, 2.05, 10.5, PI / 2), M['photo'], tile=None)
light(C_LIGHT, 'shop_a', 'AREA', (12.5, SH - 0.2, 10), (12.5, 0, 10), energy=900, color=(1.0, 0.96, 0.9), size=5)
light(C_LIGHT, 'shop_b', 'AREA', (19, SH - 0.2, 10), (19, 0, 10), energy=900, color=(1.0, 0.96, 0.9), size=5)

# 로비 조명 (밝은 흰 공간)
light(C_LIGHT, 'lobby_a', 'AREA', (-14, 7.5, 21), (-14, 0, 21), energy=6000, color=(1.0, 0.98, 0.95), size=14)
light(C_LIGHT, 'lobby_b', 'AREA', (-2, 7.5, 21), (-2, 0, 21), energy=4000, color=(1.0, 0.98, 0.95), size=10)
# 전시실 전체의 아주 약한 바탕빛 (사진: 어두운 실내에 작품만 밝음)
light(C_LIGHT, 'ambient', 'AREA', (0, SH - 0.3, 0), (0, 0, 0), energy=1600, color=(0.9, 0.92, 1.0), size=30)

for a in (hall, floor, ceil, lobby, walls, works, emit, rig):
    a.build(smooth=(a is rig))
# 천장은 아래(실내)에서만 보이게: 조감(위)에서는 뒷면이라 그려지지 않아 내부가 보인다
for n in ('bqCeiling', 'bqSlotFrame', 'bqSlot'):
    bpy.data.materials[n].use_backface_culling = True

bw = bpy.data.worlds.new('bq_world')
bw.use_nodes = True
bw.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.02, 0.025, 1)
scene.world = bw

camera(C_CAM, 'cam_overview', (34, 36, 46), (0, 0, -1), 42)
camera(C_CAM, 'cam_entrance', (-12.5, 1.7, 25), (-15, 2.3, 13.5), 54)
camera(C_CAM, 'cam_intro', (-11, 1.65, 12.6), (-17, 2.1, 8.5), 58)
camera(C_CAM, 'cam_gallery', (-5.5, 1.65, 11), (2, 1.9, -1), 60)
camera(C_CAM, 'cam_corridor', (1.5, 1.65, -9.8), (19, 2.0, -10.8), 62)
camera(C_CAM, 'cam_shop', (9.6, 1.65, 14), (19, 1.6, 7.5), 58)
scene.camera = bpy.data.objects['cam_gallery']
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
print('basquiat built:', {c.name: len(c.objects) for c in (C_STATIC, C_DYNAMIC, C_EMIT, C_LIGHT, C_CAM)})
