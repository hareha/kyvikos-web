"""APEC 황룡원 — 중도타워(9층 목탑)·한옥 회랑·소나무 (apec_stage.py 다음에 실행)

  python3 scripts/blender/bmcp.py exec scripts/blender/apec_context.py

현장 사진 기준
- 중도타워: 층마다 불 켜진 창호, 금빛 난간, 짙은 기와의 곡선 처마(추녀 들림), 처마 끝 흰 조명
- 흰 화강석 기단과 난간, 잔디 쪽 계단
- 한옥 회랑: 흰 회벽 + 붉은 목재 기둥·창방, 곡선 기와지붕
- 전경의 소나무
"""
import importlib
import math
import random
import sys

sys.path.insert(0, '/Users/hare/Documents/큐비크스홈페이지/scripts/blender')
import lib  # noqa: E402

importlib.reload(lib)
from lib import (PI, SHOTS, Assembly, T, bevel_box, box, camera, cyl, light, material, plane, sphere, tube)  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

random.seed(11)
C_STATIC = bpy.data.collections['STATIC']
C_EMIT = bpy.data.collections['EMISSIVE']
C_LIGHT = bpy.data.collections['LIGHTS']
C_CAM = bpy.data.collections['CAMERAS']
for name in ('pagoda', 'halls', 'pines', 'context_emissive'):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
for o in [o for o in C_LIGHT.objects if o.name.startswith(('pagoda_', 'hall_'))]:
    bpy.data.objects.remove(o, do_unlink=True)


def mat(name, *args, **kw):
    return bpy.data.materials.get(name) or material(name, *args, **kw)


M = {
    'tile': mat('tile', 'ceramic_roof_01', (0.09, 0.1, 0.11), 0.55),
    'wood': mat('wood', 'dark_wooden_planks', (0.42, 0.24, 0.14), 0.7),
    'woodRed': mat('woodRed', 'dark_wooden_planks', (0.62, 0.2, 0.12), 0.7),
    'rail': mat('rail', None, (0.62, 0.45, 0.2), 0.45, 0.3),
    'granite': mat('granite', 'rock_tile_floor_02', (0.82, 0.82, 0.8), 0.8),
    'plaster': mat('plaster', 'beige_wall_001', (0.95, 0.93, 0.88), 0.9),
    'windowGlow': mat('windowGlow', emit_image=f'{SHOTS}/apec_windows.png', emit_strength=3.2, rough=0.5),
    'lattice': mat('lattice', None, (1, 0.8, 0.55), emit=(1.0, 0.72, 0.42), emit_strength=1.2),
    'eaveLamp': mat('eaveLamp', None, (1, 1, 1), emit=(1.0, 0.97, 0.9), emit_strength=80),
    'bronze': mat('bronze', None, (0.55, 0.42, 0.22), 0.35, 1.0),
    'pineNeedle': mat('pineNeedle', None, (0.012, 0.03, 0.015), 0.95, sheen=0.2),
    'pineBark': mat('pineBark', 'dark_wooden_planks', (0.45, 0.25, 0.16), 0.9),
}


# ── 곡선 우진각 지붕 (웹 kit.js roofGeometry 와 같은 형태 + 두께) ─────────
def hip_roof(hw, hd, h, ridge=0.85, lift=None, curve=1.8, seg_u=12, seg_t=8, thickness=0.22):
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


def window_band(asm, cx, y, cz, width, height, bay=1.3):
    """네 면에 불 켜진 창호 패널 (텍스처 한 장 = 4칸)"""
    n = max(1, round(width / (bay * 4)))
    seg = width / n
    for k in range(n):
        off = -width / 2 + seg * (k + 0.5)
        for ry, (px, pz) in ((0, (off, width / 2)), (PI, (-off, -width / 2)),
                             (PI / 2, (width / 2, -off)), (-PI / 2, (-width / 2, off))):
            asm.add(plane(seg - 0.05, height), T(cx + px, y, cz + pz, ry), M['windowGlow'], tile=None)


# ── 중도타워 ──────────────────────────────────────────────────
PX, PZ = -30, -38
pagoda = Assembly('pagoda', C_STATIC)
glow = Assembly('context_emissive', C_EMIT)

# 기단 + 흰 화강석 난간 + 잔디 쪽 계단
pagoda.add(bevel_box(28, 2.2, 28, 0.05), T(PX, 1.1, PZ), M['granite'], 1.5)
for i in range(36):
    t = -13.6 + i * 27.2 / 35
    for (x, z) in ((PX + t, PZ + 13.8), (PX + t, PZ - 13.8), (PX + 13.8, PZ + t), (PX - 13.8, PZ + t)):
        if abs(x - PX) < 4.2 and z > PZ:
            continue  # 계단 자리
        pagoda.add(bevel_box(0.22, 1.0, 0.22, 0.02), T(x, 2.7, z), M['granite'], 1)
for (a, b) in (((PX - 13.8, PZ + 13.8), (PX - 4.2, PZ + 13.8)), ((PX + 4.2, PZ + 13.8), (PX + 13.8, PZ + 13.8)),
               ((PX - 13.8, PZ - 13.8), (PX + 13.8, PZ - 13.8)), ((PX - 13.8, PZ - 13.8), (PX - 13.8, PZ + 13.8)),
               ((PX + 13.8, PZ - 13.8), (PX + 13.8, PZ + 13.8))):
    for ry in (2.55, 3.15):
        g, m = tube(V((a[0], ry, a[1])), V((b[0], ry, b[1])), 0.07, 8)
        pagoda.add(g, m, M['granite'])
for k in range(7):
    pagoda.add(box(8.4, 2.2 - k * 0.3, 0.5), T(PX, (2.2 - k * 0.3) / 2, PZ + 14.25 + k * 0.5), M['granite'], 1.5)

y = 2.2
top_width = None
for i in range(9):
    w = 17.5 - i * 1.15
    h = 6.8 if i == 0 else 4.3
    half = w / 2
    core = w - 1.8
    pagoda.add(box(w + 0.8, 0.35, w + 0.8), T(PX, y + 0.17, PZ), M['wood'], 1.5)          # 마루
    pagoda.add(box(core, h, core), T(PX, y + h / 2, PZ), M['wood'], 1.5)                    # 몸체
    window_band(glow, PX, y + h * 0.52, PZ, core + 0.02, h * 0.62)
    for k in range(7):                                                                        # 기둥
        t = -half + k * w / 6
        for (x, z) in ((t, half), (t, -half), (half, t), (-half, t)):
            pagoda.add(box(0.34, h, 0.34), T(PX + x, y + h / 2, PZ + z), M['woodRed'], 1)
    for rh in (0.55, 1.05):                                                                    # 금빛 난간
        for (a, b) in (((-half, half), (half, half)), ((-half, -half), (half, -half)),
                       ((half, -half), (half, half)), ((-half, -half), (-half, half))):
            g, m = tube(V((PX + a[0], y + 0.35 + rh, PZ + a[1])), V((PX + b[0], y + 0.35 + rh, PZ + b[1])), 0.045, 8)
            pagoda.add(g, m, M['rail'])
    pagoda.add(box(core + 0.3, 0.5, core + 0.3), T(PX, y + h - 0.25, PZ), M['woodRed'], 1)  # 창방
    # 처마
    rh_ = 1.9 if i == 0 else 1.6
    hb = half + (2.8 if i == 0 else 2.3)
    ht = half - 0.5
    lift = 1.0
    eave = y + h - 0.2
    pagoda.add(hip_roof(hb, hb, rh_, ridge=1 - ht / hb, lift=lift, thickness=0.25), T(PX, eave, PZ), M['tile'], 1.4)
    for (lx, lz) in ((hb, hb), (-hb, hb), (hb, -hb), (-hb, -hb)):
        glow.add(sphere(0.22, 2), T(PX + lx, eave + lift - 0.05, PZ + lz), M['eaveLamp'])
        light(C_LIGHT, f'pagoda_lamp_{i}_{lx:.0f}_{lz:.0f}', 'POINT', (PX + lx, eave + lift - 0.3, PZ + lz),
              energy=260, color=(1.0, 0.95, 0.88), size=0.2)
    y += h + rh_ - 0.25
# 상륜부
pagoda.add(cyl(0.25, 1.0, 9, 12), T(PX, y + 4.5, PZ), M['bronze'])
for k in range(7):
    r = 1.1 - k * 0.11
    pagoda.add(cyl(r, r, 0.16, 20), T(PX, y + 1.8 + k * 1.05, PZ), M['bronze'])
pagoda.add(sphere(0.5, 2), T(PX, y + 9.3, PZ), M['bronze'])
pagoda.build(smooth=False)

# 기단 앞 타워 투광 (따뜻한 업라이트)
for ux in (-8, 0, 8):
    light(C_LIGHT, f'pagoda_up_{ux}', 'SPOT', (PX + ux, 3.0, PZ + 17), (PX + ux * 0.5, 22, PZ + 6),
          energy=9000, color=(1.0, 0.78, 0.5), spot=0.7, blend=0.6, size=0.4)


# ── 한옥 회랑 ─────────────────────────────────────────────────
halls = Assembly('halls', C_STATIC)


def hanok(cx, cz, w, d, h, ry=0.0, roof_h=3.4, base_h=0.9):
    base = T(cx, 0, cz, ry)
    halls.add(bevel_box(w + 1.2, base_h, d + 1.2, 0.04), base @ T(0, base_h / 2, 0), M['granite'], 1.5)
    halls.add(box(w, h, d), base @ T(0, base_h + h / 2, 0), M['plaster'], 2.5)
    bays = max(2, round(w / 3))
    for k in range(bays + 1):
        px = -w / 2 + k * w / bays
        for pz in (-d / 2, d / 2):
            halls.add(cyl(0.2, 0.22, h, 12), base @ T(px, base_h + h / 2, pz + (0.05 if pz > 0 else -0.05)), M['woodRed'], 1)
        if k < bays:
            for pz, rot in ((d / 2 + 0.03, 0), (-d / 2 - 0.03, PI)):
                glow.add(plane(w / bays - 0.7, h * 0.46), base @ T(px + w / bays / 2, base_h + h * 0.48, pz, rot), M['lattice'], tile=None)
    halls.add(box(w + 0.5, 0.5, d + 0.5), base @ T(0, base_h + h - 0.25, 0), M['woodRed'], 1)
    hw, hd = w / 2 + 2.0, d / 2 + 2.0
    halls.add(hip_roof(hw, hd, roof_h, ridge=0.85, lift=roof_h * 0.32, thickness=0.22), base @ T(0, base_h + h - 0.1, 0), M['tile'], 1.4)
    ridge_len = max(hw - hd * 0.85, hd * 0.15) * 2 + 0.6
    halls.add(bevel_box(ridge_len, 0.34, 0.42, 0.05), base @ T(0, base_h + h - 0.1 + roof_h + 0.12, 0), M['tile'], 1)
    light(C_LIGHT, f'hall_{cx}_{cz}', 'AREA', tuple(base @ V((0, base_h + h + 0.5, d / 2 + 3))),
          tuple(base @ V((0, base_h + 1, d / 2))), energy=900, color=(1.0, 0.8, 0.55), size=w * 0.6)


hanok(-22, 37, 34, 10, 5.6)                 # 귀빈동 (테라스, 사진을 찍은 곳)
hanok(-41, 2, 36, 8, 4.6, ry=PI / 2)         # 좌측 회랑
hanok(6, 29.5, 10, 6, 3.4, roof_h=2.6)       # 콘솔 부스 정자
halls.build()

# ── 소나무 (전경) ─────────────────────────────────────────────
pines = Assembly('pines', C_STATIC)


def pine(px, pz, s=1.0):
    pts = [V((px, 0.1, pz))]
    lean = V((random.uniform(-0.5, 0.5), 1, random.uniform(-0.5, 0.5))).normalized()
    for k in range(5):
        prev = pts[-1]
        pts.append(prev + (lean * 1.1 + V((random.uniform(-0.35, 0.35), 0, random.uniform(-0.35, 0.35)))) * s)
    for k in range(len(pts) - 1):
        g, m = tube(pts[k], pts[k + 1], (0.32 - k * 0.04) * s, 10, caps=True)
        pines.add(g, m, M['pineBark'], 0.8)
    top = pts[-1]
    for k in range(9):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.6, 2.6) * s
        c = V((top.x + math.cos(a) * r, top.y - random.uniform(0.2, 2.4) * s, top.z + math.sin(a) * r))
        sx, sy = random.uniform(1.4, 2.2) * s, random.uniform(0.45, 0.7) * s

        def pad(bm, sx=sx, sy=sy):
            bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
            for v in bm.verts:
                v.co.x *= sx * (1 + random.uniform(-0.12, 0.12))
                v.co.z *= sx * (1 + random.uniform(-0.12, 0.12))
                v.co.y *= sy * (1 + random.uniform(-0.1, 0.1))
        pines.add(pad, T(c.x, c.y, c.z, random.uniform(0, PI)), M['pineNeedle'], 1)


pine(14, 18.5, 1.1)
pine(19.5, 20.5, 0.95)
pine(-31, 21, 0.85)
pines.build(smooth=True)
glow.build()

camera(C_CAM, 'cam_terrace', (-26, 14.5, 38), (2, 5, -14), 48)   # 귀빈동 테라스 (image29)
print('context built')
