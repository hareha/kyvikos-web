"""성수동 세원정밀 창고 — LOCAL POWER 2025 홍콩 패션 in 서울

  python3 scripts/blender/bmcp.py exec scripts/blender/localpower_scene.py

자료: 소개서 19~22p 현장 사진·렌더
- 창고: 박공 철골 트러스 지붕(8m 간격, 하현·도리·가새), 흰 도장 벽, 짙은 회색 콘크리트 바닥(오래된 레일 자국), 고창.
- 패션쇼장: 유광 블랙 상판 + 흰 스커트 런웨이(가장자리 흰 LED 라인), 흰 박스 벤치 3열 + 앞줄 쇼핑백,
           LED 백드롭(LOCAL POWER), 사이드 트러스·무빙라이트, 오렌지 조명 (현장 사진).
- 전시장: 흰 가벽 앞 긴 전시대의 마네킹, 흰 커튼 원형 기둥 전시대·물결 커튼 전시대, 라이트박스(URBAN JUNGLE).
- 거리 쪽: 주황 LOCAL POWER 가림막, 레드카펫 입구. 옆 중정: 흰 담장, 파고다 텐트, 하이테이블, 홍등.
- 마네킹: 흰 추상 두상·목·받침대 + 실제 의상 모델(CC BY): 후드+청바지, 크롭 후드 세트, 후드+스커트
좌표: 창고 중심 원점. -x 런웨이 백드롭, +x 전시장·중정, +z 거리(가림막).
"""
import importlib
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

import gear  # noqa: E402
import props  # noqa: E402
importlib.reload(gear)
importlib.reload(props)

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

HX, HZ, EAVE, RIDGE = 32.0, 10.0, 6.6, 9.4

M = {
    'floor': material('lpFloor', 'concrete_floor_01', (0.3, 0.33, 0.37), 0.7),   # 짙은 회색 (갈색 기 빼기)
    'white': material('lpWhite', 'painted_plaster_wall', (0.88, 0.88, 0.86), 0.85),
    'shell': material('lpShell', 'painted_plaster_wall', (0.78, 0.78, 0.76), 0.85),
    'roof': material('lpRoof', 'corrugated_iron_02', (0.35, 0.36, 0.37), 0.6, 0.5),
    'steel': material('lpSteel', None, (0.18, 0.19, 0.2), 0.5, 0.7),
    'truss': material('lpTruss', None, (0.03, 0.03, 0.035), 0.4, 0.6),
    'black': material('lpBlack', None, (0.015, 0.015, 0.018), 0.5),
    'runwayTop': material('lpRunwayTop', None, (0.01, 0.01, 0.012), 0.08, coat=1.0),
    'bench': material('lpBench', None, (0.9, 0.9, 0.88), 0.6),
    'paper': material('lpPaper', None, (0.93, 0.92, 0.88), 0.8),
    'plinth': material('lpPlinth', None, (0.92, 0.92, 0.9), 0.35, coat=0.4),
    'curtain': material('lpCurtain', 'cotton_jersey', (0.93, 0.93, 0.92), 0.7, normal=0.3, sheen=0.6),
    'silver': material('lpSilver', None, (0.8, 0.81, 0.82), 0.25, 1.0),
    'skin': material('lpSkin', None, (0.92, 0.92, 0.9), 0.3, coat=0.5),
    'carpet': material('lpCarpet', 'cotton_jersey', (0.45, 0.03, 0.03), 0.9),
    'court': material('lpCourt', 'rock_tile_floor_02', (0.55, 0.55, 0.53), 0.8),
    'street': material('lpStreet', 'asphalt_02', (0.3, 0.3, 0.32), 0.9),
    'wood': material('lpWood', 'dark_wooden_planks', (0.7, 0.5, 0.32), 0.7),
    'tent': material('tentWhite', 'cotton_jersey', (0.92, 0.92, 0.9), 0.8, normal=0.4),
    'alu': material('tentAlu', None, (0.8, 0.8, 0.82), 0.35, 1.0),
    'case': material('roadCase', None, (0.03, 0.03, 0.035), 0.5),
    'white_led': material('lpEdgeLed', None, (1, 1, 1), emit=(1.0, 0.97, 0.95), emit_strength=12),
    'lens': material('lpLens', None, (1, 1, 1), emit=(1.0, 0.75, 0.5), emit_strength=30),
    'lantern': material('lpLantern', None, (1, 0.3, 0.2), emit=(1.0, 0.25, 0.12), emit_strength=6),
    'down': material('lpDown', None, (1, 1, 1), emit=(1.0, 0.96, 0.9), emit_strength=25),
    'led': material('lpLed', emit_image=f'{SHOTS}/lp_ledTexture.png', emit_strength=2.4, rough=0.3),
    'panel': material('lpPanel', emit_image=f'{SHOTS}/lp_panelTexture.png', emit_strength=1.6, rough=0.3),
    'hoarding': material('lpHoarding', image_base=f'{SHOTS}/lp_hoardingTexture.png', rough=0.6),
    'exhibition': material('lpExhibition', image_base=f'{SHOTS}/lp_exhibitionTexture.png', rough=0.6),
    'sponsor': material('lpSponsor', image_base=f'{SHOTS}/lp_sponsorTexture.png', rough=0.6),
    'lightbox': material('lpLightbox', emit_image=f'{SHOTS}/lp_r_lightbox.png', emit_strength=2.0, rough=0.3),
    'city': material('lpCity', emit_image=f'{SHOTS}/lp_lightboxTexture.png', emit_strength=1.8, rough=0.3),
}

# ── 의상 모델 (CC BY) ─────────────────────────────────────────
OUT1 = props.load('4fc7bc06a5b94568b1923268f4a6e825', 'src_out_hoodie', height=1.62, decimate=0.5, coll=C_SRC)
OUT2 = props.load('11db5ff86776413885c3f4770cea7eae', 'src_out_crop', height=1.62, decimate=0.35, coll=C_SRC)
OUT3 = props.load('3a3d8d3fc80c42baab590a63b180a65e', 'src_out_skirt', height=1.5, decimate=0.4, coll=C_SRC)
OUT2R = props.retint(OUT2, (0.75, 0.12, 0.1), 'red')
OUT2G = props.retint(OUT2, (0.1, 0.35, 0.2), 'green')
OUT1B = props.retint(OUT1, (0.1, 0.1, 0.12), 'black')
for o in (OUT2R, OUT2G, OUT1B):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    C_SRC.objects.link(o)
OUTFITS = [OUT1, OUT2, OUT3, OUT2R, OUT1B, OUT2G]
outfit_spots = []

shell = Assembly('shell', C_STATIC)
floor = Assembly('floor', C_STATIC)
show = Assembly('show', C_STATIC)
expo = Assembly('expo', C_STATIC)
court = Assembly('court', C_STATIC)
emit = Assembly('emissive', C_EMIT)
rig = Assembly('rig', C_DYNAMIC)


def mannequin(asm, x, y, z, ry, k, head=True):
    """흰 추상 마네킹: 받침(은색 원판·봉) + 의상 모델 + 목·두상"""
    f = T(x, y, z, ry)
    asm.add(cyl(0.3, 0.3, 0.02, 32), f @ T(0, 0.01, 0), M['silver'], 1)
    asm.add(cyl(0.012, 0.012, 0.22, 8), f @ T(0, 0.12, 0), M['silver'], 1)
    outfit_spots.append((OUTFITS[k % len(OUTFITS)], f @ T(0, 0.015, 0)))
    if head:
        top = OUTFITS[k % len(OUTFITS)].dimensions.z * 1.0
        asm.add(cyl(0.045, 0.05, 0.14, 12), f @ T(0, 0.02 + top + 0.02, 0.01), M['skin'], 1)
        asm.add(sphere(0.1, 3), f @ T(0, 0.02 + top + 0.17, 0.01, 0, 0, 0, 0.85, 1.15, 0.95), M['skin'])


# ── 창고 ──────────────────────────────────────────────────────
floor.add(box(HX * 2, 0.2, HZ * 2), T(0, -0.1, 0), M['floor'], 3)
for z in (-2.5, -1.0):                                          # 옛 레일 자국
    floor.add(box(HX * 2 - 1, 0.012, 0.08), T(0, 0.005, z), M['steel'], 1)
WALL_T = 0.3
# 외피는 안쪽을 향한 한 겹 면(뒷면 제거): 밖(조감)에서는 투명하게 보여 내부가 보이고, 안에서는 벽·지붕으로 보인다
shell.add(plane(HX * 2, EAVE), T(0, EAVE / 2, -HZ), M['shell'], 2)                  # 뒷벽 (+z 를 봄)
shell.add(plane(HX * 2, EAVE), T(0, EAVE / 2, HZ, PI), M['shell'], 2)               # 거리 쪽 벽
shell.add(plane(HZ * 2, EAVE), T(-HX, EAVE / 2, 0, PI / 2), M['shell'], 2)          # 백드롭 쪽 끝벽
shell.add(plane(HZ * 2, EAVE), T(HX, EAVE / 2, 0, -PI / 2), M['shell'], 2)          # 중정 쪽 끝벽
for sx in (-1, 1):
    def gable(bm, sx=sx):
        vs = [bm.verts.new(p) for p in ((0, EAVE, -HZ), (0, EAVE, HZ), (0, RIDGE, 0))]
        bm.faces.new(list(reversed(vs)) if sx < 0 else vs)
    shell.add(gable, T(sx * HX, 0, 0), M['shell'], 2)
theta = math.atan2(RIDGE - EAVE, HZ)
slope = math.hypot(RIDGE - EAVE, HZ)
for s in (-1, 1):                                                                 # 지붕 두 경사면 (아래를 봄)
    shell.add(plane(HX * 2, slope), T(0, (EAVE + RIDGE) / 2, s * HZ / 2, 0, PI / 2 + s * theta), M['roof'], 2)


def member(asm, a, b, r, mat):
    g, m = tube(a, b, r, 8, caps=True)
    asm.add(g, m, mat)


for x in [HX * (2 * i / 8 - 1) for i in range(9)]:
    for z in (-HZ + 0.25, HZ - 0.25):
        shell.add(box(0.3, EAVE, 0.3), T(x, EAVE / 2, z), M['steel'], 1)
    bot = EAVE - 0.9
    top_y = lambda z: EAVE + (RIDGE - EAVE) * (1 - abs(z) / HZ)  # noqa: E731
    member(shell, V((x, bot, -HZ)), V((x, bot, HZ)), 0.07, M['steel'])
    member(shell, V((x, EAVE, -HZ)), V((x, RIDGE, 0)), 0.09, M['steel'])
    member(shell, V((x, EAVE, HZ)), V((x, RIDGE, 0)), 0.09, M['steel'])
    for i in range(9):
        z = -HZ + i * HZ * 2 / 8
        member(shell, V((x, bot, z)), V((x, top_y(z), z)), 0.04, M['steel'])
        if i < 8:
            z1 = z + HZ * 2 / 8
            up = z < 0
            member(shell, V((x, bot, z if up else z1)), V((x, top_y(z1 if up else z), z1 if up else z)), 0.035, M['steel'])
for i in range(5):
    t = i / 4
    for s in (-1, 1):
        if i == 4 and s == 1:
            continue
        z = s * HZ * (1 - t)
        member(shell, V((-HX, EAVE + (RIDGE - EAVE) * t + 0.05, z)), V((HX, EAVE + (RIDGE - EAVE) * t + 0.05, z)), 0.06, M['steel'])
# 고창 (창틀 + 유리빛)
for x in range(-28, 32, 8):
    for s in (-1, 1):
        shell.add(box(4.2, 1.2, 0.08), T(x, 4.9, s * (HZ + 0.02)), M['steel'], 1)

# ── 패션쇼장 ──────────────────────────────────────────────────
RX0, RX1, RW, RH = -25.0, -4.2, 3.2, 0.5
RL, RCX = RX1 - RX0, (RX0 + RX1) / 2
show.add(box(RL, RH - 0.04, RW), T(RCX, (RH - 0.04) / 2, 0), M['bench'], 1)
show.add(box(RL, 0.04, RW), T(RCX, RH - 0.02, 0), M['runwayTop'], 1)
for s in (-1, 1):
    emit.add(box(RL, 0.02, 0.04), T(RCX, RH + 0.01, s * (RW / 2 - 0.03)), M['white_led'])
emit.add(box(0.04, 0.02, RW), T(RX1 - 0.03, RH + 0.01, 0), M['white_led'])
show.add(box(4, RH, 15), T(-27.2, RH / 2, 0), M['black'], 1)
show.add(box(0.5, 5.2, 15.4), T(-29.5, 2.6 + RH, 0), M['black'], 1)
emit.add(plane(7.2, 4.0), T(-29.24, RH + 2.5, 0, PI / 2), M['led'], tile=None)
for s in (-1, 1):
    emit.add(plane(3.0, 4.0), T(-29.24, RH + 2.5, s * 5.5, PI / 2), M['panel'], tile=None)
for s in (-1, 1):
    for row, (z, bh) in enumerate(((2.55, 0.45), (3.55, 0.6), (4.55, 0.75))):
        sx = -23.5
        while sx < -5:
            cx = sx + 2
            show.add(bevel_box(4, bh, 0.55, 0.01), T(cx, bh / 2, s * z), M['bench'], 1)
            if row == 0:
                for kk in range(5):
                    bx = cx - 1.6 + kk * 0.8
                    show.add(bevel_box(0.26, 0.3, 0.1, 0.005), T(bx, bh + 0.15, s * (z + 0.05)), M['paper'], 1)
                    for hx in (-0.05, 0.05):                # 손잡이
                        member(show, V((bx + hx, bh + 0.3, s * (z + 0.05))), V((bx + hx, bh + 0.38, s * (z + 0.05))), 0.004, M['paper'])
            sx += 4.8
for x in [-28 + 4.5 * i for i in range(6)]:
    for s in (-1, 1):
        show.add(box(1.0, 5.2, 0.5), T(x, 2.6, s * (HZ - 0.5)), M['white'], 1)
# 트러스 + 무빙라이트
TOP, TZ, PX = 5.6, 6.6, -2.6


def box_truss(a, b, s=0.3):
    d = (b - a).normalized()
    ref = V((1, 0, 0)) if abs(d.y) > 0.9 else V((0, 1, 0))
    u = d.cross(ref).normalized() * (s / 2)
    v = u.cross(d).normalized() * (s / 2)
    cs = [u + v, u - v, -u - v, -u + v]
    for c in cs:
        g, m = tube(a + c, b + c, 0.022, 8)
        rig.add(g, m, M['truss'])
    L = (b - a).length
    n = max(1, round(L / 0.45))
    for i in range(n):
        p0, p1 = a + d * (L * i / n), a + d * (L * (i + 1) / n)
        for k in range(4):
            c0, c1 = cs[k], cs[(k + 1) % 4]
            g, m = tube(p0 + (c0 if i % 2 else c1), p1 + (c1 if i % 2 else c0), 0.01, 6)
            rig.add(g, m, M['truss'])


for z in (-TZ, TZ):
    for x in (-24, -16, -8):
        rig.add(bevel_box(0.8, 0.08, 0.8, 0.01), T(x, 0.04, z), M['truss'])
        box_truss(V((x, 0.08, z)), V((x, TOP, z)))
    box_truss(V((-24, TOP, z)), V((-8, TOP, z)))
    rig.add(bevel_box(0.8, 0.08, 0.8, 0.01), T(PX, 0.04, z), M['truss'])
    box_truss(V((PX, 0.08, z)), V((PX, TOP, z)))
box_truss(V((PX, TOP, -TZ)), V((PX, TOP, TZ)))
heads = [(x, z) for z in (-TZ, TZ) for x in [-23 + 2.8 * i for i in range(6)]] + [(PX, z) for z in (-5, -2.5, 0, 2.5, 5)]
for k, (x, z) in enumerate(heads):
    rig.add(bevel_box(0.36, 0.12, 0.36, 0.02), T(x, TOP - 0.21, z), M['black'])
    rig.add(bevel_box(0.34, 0.3, 0.06, 0.01), T(x, TOP - 0.42, z), M['black'])
    rig.add(sphere(0.17, 2), T(x, TOP - 0.56, z), M['black'])
    emit.add(cyl(0.1, 0.1, 0.02, 16), T(x, TOP - 0.74, z), M['lens'])
    tgt = (x - 1.5 + (k % 3), RH, -z * 0.1) if x != PX else (-12, RH, z * 0.3)
    light(C_LIGHT, f'mover_{k}', 'SPOT', (x, TOP - 0.76, z), tgt, energy=1400, color=(1.0, 0.55, 0.22),
          spot=0.45, blend=0.5, size=0.06)
show.add(box(1.6, 0.6, 5), T(-2.2, 0.3, 0), M['black'], 1)
show.add(box(0.8, 0.4, 5), T(-1.8, 0.8, 0), M['black'], 1)
mannequin(show, -21.5, RH, 0, PI / 2, 2)
# 벽을 붉게 물들이는 오렌지 워시 (현장 사진)
for x in (-24, -14, -6):
    for s in (-1, 1):
        light(C_LIGHT, f'wash_{x}_{s}', 'SPOT', (x, 0.4, s * (HZ - 2.5)), (x, 4.5, s * HZ), energy=2600,
              color=(1.0, 0.45, 0.15), spot=1.1, blend=0.8, size=0.2)

# ── 전시장 ────────────────────────────────────────────────────
expo.add(box(0.3, 5, 14), T(0, 2.5, -3), M['white'], 2)
expo.add(box(0.3, 5, 1.5), T(0, 2.5, HZ - 0.75), M['white'], 2)
expo.add(box(27, 4.2, 0.3), T(16.5, 2.1, -9.3), M['white'], 2)
expo.add(bevel_box(26, 0.22, 1.3, 0.01), T(16.5, 0.11, -8.4), M['plinth'], 1)
k = 0
x = 4.3
while x <= 28.8:
    if k % 4 == 0:
        for j in range(5):
            expo.add(cyl(0.14 - (j % 2) * 0.04, 0.14, 0.34, 16), T(x, 0.22 + 0.17 + j * 0.34, -8.4), M['plinth'], 1)
    else:
        mannequin(expo, x, 0.22, -8.4, 0, k)
    x += 1.4
    k += 1
expo.add(box(0.3, 3.8, 8), T(3.6, 1.9, -1), M['white'], 2)
expo.add(bevel_box(0.1, 1.8, 3.4, 0.01), T(3.8, 2.1, -1), M['white'], 1)
emit.add(plane(3.2, 1.6), T(3.86, 2.1, -1, PI / 2), M['lightbox'], tile=None)


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


ring = lambda cx, cz, r, n=48: [(cx + r * math.cos(i / n * 2 * PI), cz + r * math.sin(i / n * 2 * PI)) for i in range(n)]  # noqa: E731


def column(cx, cz, rp, rc, h, count, k0):
    slab_poly(expo, ring(cx, cz, rp), 0.3, M['plinth'])
    curtain_path(expo, ring(cx, cz, rc, 36), h, 0.3, closed=True)
    expo.add(cyl(rc + 0.08, rc + 0.08, 0.06, 36), T(cx, 0.3 + h + 0.03, cz), M['white'], 1)       # 커튼 레일 링
    for s in (-1, 1):
        member(expo, V((cx + s * rc * 0.7, 0.3 + h, cz)), V((cx + s * rc * 0.7, EAVE - 0.9, cz)), 0.012, M['steel'])
    for i in range(count):
        a = PI / 2 + (i - (count - 1) / 2) * 0.9
        r = (rp + rc) / 2 + 0.05
        mannequin(expo, cx + math.cos(a) * r, 0.3, cz + math.sin(a) * r, PI / 2 - a, k0 + i)


column(10.5, -1.5, 2.2, 1.15, 4.6, 3, 1)
column(25.5, -4.5, 1.6, 0.85, 4.2, 2, 4)
# 물결 커튼 전시대 (현장 사진: 흰 커튼 앞 긴 물결 좌대)
WX, WZ, HALF = 20.0, 3.0, 4.6
back = lambda x: -1.0 + 0.45 * math.sin(x * 0.85)  # noqa: E731
front = lambda x: 1.15 + 0.35 * math.sin(x * 0.85 + 0.9)  # noqa: E731
pts = [(WX + x, WZ + back(x)) for x in [-HALF + i * HALF * 2 / 30 for i in range(31)]]
for x0, d in ((HALF, 1), (-HALF, -1)):
    b0, f0 = back(x0), front(x0)
    c, r = (b0 + f0) / 2, (f0 - b0) / 2
    arc = [(WX + x0 + d * r * math.sin(i / 12 * PI), WZ + c - d * r * math.cos(i / 12 * PI)) for i in range(1, 12)]
    pts += arc
    if d > 0:
        pts += [(WX + x, WZ + front(x)) for x in [HALF - i * HALF * 2 / 30 for i in range(31)]]
slab_poly(expo, pts, 0.3, M['plinth'])
curtain_path(expo, [(WX + x, WZ + back(x) + 0.3) for x in [-HALF + 0.5 + i * (HALF - 0.5) * 2 / 24 for i in range(25)]], 4.1, 0.3)
member(expo, V((WX - HALF + 0.5, 4.4, WZ + back(-HALF + 0.5) + 0.3)), V((WX + HALF - 0.5, 4.4, WZ + back(HALF - 0.5) + 0.3)), 0.02, M['steel'])
for i, x in enumerate((-3.6, -1.8, 0, 1.8, 3.6)):
    mannequin(expo, WX + x, 0.3, WZ + (back(x) + front(x)) / 2 + 0.25, 0, i + 2)
for (x, z, ry) in ((14.8, -5.6, 0.3), (28.6, 3.8, -PI / 2)):
    f = T(x, 0, z, ry)
    expo.add(bevel_box(1.25, 2.1, 0.22, 0.01), f @ T(0, 1.05, 0), M['white'], 1)
    emit.add(plane(1.05, 1.9), f @ T(0, 1.07, 0.115), M['city'], tile=None)
# 전시장 천장 레일 다운라이트
for x in (8, 16, 24):
    for z in (-7, -3.5, 0, 3.5, 7):
        rig.add(cyl(0.07, 0.08, 0.18, 16), T(x, EAVE - 1.05, z), M['black'])
        emit.add(cyl(0.06, 0.06, 0.01, 16), T(x, EAVE - 1.145, z), M['down'])
    member(rig, V((x, EAVE - 0.96, -8)), V((x, EAVE - 0.96, 8)), 0.025, M['black'])
    light(C_LIGHT, f'expo_{x}', 'AREA', (x, EAVE - 1.2, 0), (x, 0, 0), energy=2200, color=(1.0, 0.96, 0.9), size=6)
light(C_LIGHT, 'expo_wall', 'AREA', (16.5, EAVE - 1.3, -6.5), (16.5, 1, -9.3), energy=2600, color=(1.0, 0.97, 0.92), size=10)

# ── 거리 쪽 가림막 + 레드카펫 + 중정 ─────────────────────────────
outer = Assembly('outer', C_STATIC)
outer.add(box(110, 0.1, 14), T(8, -0.05, HZ + 8), M['street'], 3)
ZH, HH = HZ + 0.9, 4.2
for (x0, w, mat) in ((-31.5, 24, 'hoarding'), (-7.5, 4, 'sponsor'), (-3.5, 14, 'exhibition')):
    outer.add(box(w, HH, 0.2), T(x0 + w / 2, HH / 2, ZH), M['black'], 1)
    outer.add(plane(w, HH), T(x0 + w / 2, HH / 2, ZH + 0.105), M[mat], tile=None)
for x in range(-31, 11, 3):                                      # 가림막 뒤 비계
    member(outer, V((x, 0, ZH - 0.6)), V((x, HH, ZH - 0.6)), 0.024, M['silver'])
for y in (0.6, 2.1, 3.6):
    member(outer, V((-31.5, y, ZH - 0.6)), V((10.5, y, ZH - 0.6)), 0.024, M['silver'])
    for x in range(-31, 11, 3):
        member(outer, V((x, y, ZH - 0.6)), V((x, y, ZH - 0.1)), 0.02, M['silver'])
outer.add(box(3, 0.03, 13), T(38, 0.015, 6.5), M['carpet'], 1.5)
outer.add(box(6.5, 0.03, 2.6), T(35.2, 0.015, 1.5), M['carpet'], 1.5)
X0c, X1c, Z0c, Z1c, WH = HX + 0.3, 47.0, -7.0, HZ + 1.5, 2.6
court.add(box(X1c - X0c, 0.08, Z1c - Z0c), T((X0c + X1c) / 2, 0.04, (Z0c + Z1c) / 2), M['court'], 1.5)
court.add(box(X1c - X0c, WH, 0.25), T((X0c + X1c) / 2, WH / 2, Z0c), M['white'], 2)
court.add(box(0.25, WH, Z1c - Z0c), T(X1c, WH / 2, (Z0c + Z1c) / 2), M['white'], 2)
court.add(box(36.5 - X0c, WH, 0.25), T((X0c + 36.5) / 2, WH / 2, Z1c), M['white'], 2)
court.add(box(X1c - 39.5, WH, 0.25), T((39.5 + X1c) / 2, WH / 2, Z1c), M['white'], 2)
for gx in (36.5, 39.5):
    court.add(box(0.6, 3.6, 0.6), T(gx, 1.8, Z1c), M['white'], 1)
for tx in (35.5, 39.5, 43.5):
    gear.popup_tent(court, T(tx, 0.08, -4.4), M, size=3.0, h=2.4, walls=(False, False, False, False))
court.add(bevel_box(0.8, 1.05, 5, 0.01), T(45.6, 0.525 + 0.08, 3), M['white'], 1)
for (x, z) in ((35, 3.5), (41.5, 2.5), (35.2, 8), (42.5, 7.5), (40.5, -0.8)):
    court.add(cyl(0.38, 0.38, 0.04, 24), T(x, 1.1, z), M['white'], 1)
    court.add(cyl(0.035, 0.035, 1.0, 10), T(x, 0.6, z), M['silver'], 1)
    court.add(cyl(0.25, 0.25, 0.02, 20), T(x, 0.09, z), M['silver'], 1)
    for i in range(3):
        a = i / 3 * 2 * PI + x
        court.add(cyl(0.17, 0.17, 0.72, 16), T(x + math.cos(a) * 0.75, 0.44, z + math.sin(a) * 0.75), M['wood'], 1)
for z in (0.5, 4.5, 8.5):
    pts3 = [V((X0c + (X1c - X0c) * t, 3.4 - math.sin(t * PI) * 0.45, z)) for t in [i / 10 for i in range(11)]]
    for a, b in zip(pts3, pts3[1:]):
        g, m = tube(a, b, 0.006, 6)
        rig.add(g, m, M['black'])
    for p in pts3[1:-1]:
        member(rig, p, p - V((0, 0.12, 0)), 0.004, M['black'])
        emit.add(sphere(0.2, 2), T(p.x, p.y - 0.32, z, 0, 0, 0, 1, 1.15, 1), M['lantern'])
    for p in (pts3[0], pts3[-1]):                                  # 줄을 거는 기둥
        court.add(cyl(0.04, 0.04, 3.4, 8), T(p.x, 1.7 + 0.08, z), M['silver'], 1)
light(C_LIGHT, 'court_sun', 'SUN', (40, 30, 20), (38, 0, 0), energy=2.5, color=(1.0, 0.97, 0.92))

# ── 쇼장 기본광·전시장 창빛 ──────────────────────────────────────
light(C_LIGHT, 'show_fill', 'AREA', (-15, EAVE - 1.2, 0), (-15, 0, 0), energy=1500, color=(1.0, 0.6, 0.35), size=14)
light(C_LIGHT, 'backdrop', 'AREA', (-29.0, 2.8, 0), (-10, 1, 0), energy=900, color=(1.0, 0.6, 0.3), size=7)

for a in (floor, shell, show, expo, outer, court, emit, rig):
    a.build(smooth=(a is rig))
for n in ('lpShell', 'lpRoof'):
    bpy.data.materials[n].use_backface_culling = True
for i, (src, mtx) in enumerate(outfit_spots):
    instance(src, C_DYNAMIC, f'outfit_{i:02d}', mtx)

w = bpy.data.worlds.new('lp_world')
w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.55, 0.62, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.4
scene.world = w

camera(C_CAM, 'cam_overview', (32, 62, 58), (5, 0, 0), 42)
camera(C_CAM, 'cam_runway', (-2.2, 2.4, 0.4), (-29, 2.3, 0), 58)
camera(C_CAM, 'cam_showtop', (-1.5, 5.3, 8.8), (-19, 0, -1), 58)
camera(C_CAM, 'cam_exhibit', (16, 1.65, 8.5), (5, 1.7, -8), 60)
camera(C_CAM, 'cam_curtain', (20, 1.7, 9.5), (20, 1.7, 2), 60)
scene.camera = bpy.data.objects['cam_runway']
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
print('localpower built:', {c.name: len(c.objects) for c in (C_STATIC, C_DYNAMIC, C_EMIT, C_LIGHT, C_CAM)})
