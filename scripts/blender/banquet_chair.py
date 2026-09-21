"""연회 의자 — 실제 의자 모델에 스판 커버와 금색 새틴 띠를 씌운다 (apec_stage.py 에서 사용)

원본: "Banquet Chair" (Sketchfab 3621b93ff2cc4252a302391cb22a6116, CC Attribution, Objaverse 경유)
     assets-src/models/objaverse/3621b93ff2cc4252a302391cb22a6116.glb

APEC 만찬 사진의 의자: 바닥까지 내려오는 검은 스판 커버 + 등받이 가운데를 감싼 샴페인 골드 새틴 띠(뒤에서 리본).
1. 원본 의자를 실제 크기(높이 약 0.97m)로 맞추고 등받이가 웹 +z(Blender -y)를 향하게 돌린다
2. 다리 부분을 바닥까지 채운 뒤 복셀 리메시 → 스무딩 → 살짝 부풀림 → 감축: 의자 형태를 그대로 따르는 커버 곡면
3. 커버 표면에서 등받이 띠 높이의 면만 떼어 두께를 주면 몸에 붙는 새틴 띠, 뒤에 커브로 리본 고리·꼬리
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

SRC_GLB = '/Users/hare/Documents/큐비크스홈페이지/assets-src/models/objaverse/3621b93ff2cc4252a302391cb22a6116.glb'
SCALE = 0.0233          # 원본 41.6 단위 → 0.97m
SASH = (0.64, 0.8)      # 띠 높이 (바닥 기준, m)


def _link_only(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def _apply_modifiers(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = me
    bpy.data.meshes.remove(old)


def _import_base(coll):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC_GLB)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    bm = bmesh.new()
    for o in meshes:
        tmp = bmesh.new()
        tmp.from_mesh(o.data)
        tmp.transform(o.matrix_world)
        me = bpy.data.meshes.new('t')
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    # 실제 크기 + 등받이(원본 -x)를 Blender -y(웹 +z)로
    bm.transform(Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Diagonal((SCALE, SCALE, SCALE, 1)))
    zmin = min(v.co.z for v in bm.verts)
    bm.transform(Matrix.Translation((0, 0, -zmin)))
    me = bpy.data.meshes.new('chair_base')
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new('chair_base', me)
    bpy.context.scene.collection.objects.link(obj)   # 모디파이어 평가를 위해 보이는 곳에서 만든다
    return obj


def build(coll, cover_mat, sash_mat, name='banquet_chair'):
    base = _import_base(coll)
    vs = [v.co for v in base.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
    seat = max(v.z for v in vs if v.y > (y0 + y1) / 2 + 0.05)     # 앞쪽 좌판 윗면 높이

    # 1) 커버 원형 — 스판 커버는 뼈대 사이 빈 곳을 당겨 덮는다:
    #    등받이: 등받이 쿠션 + 뒷다리 영역의 볼록 껍질을 바닥까지 (뒤는 꼭대기에서 바닥까지 곧게 떨어짐)
    #    좌판: 좌판 + 네 다리의 볼록 껍질 (다리가 벌어진 만큼 아래로 살짝 퍼짐)
    back_pts = [v for v in vs if v.z > seat + 0.04]
    yb0 = min(v.y for v in back_pts)
    yb1 = max(v.y for v in back_pts)                               # 등받이 앞면
    back_region = [v.copy() for v in vs if v.y <= yb1 + 0.005]
    back_region += [Vector((v.x, v.y, 0.0)) for v in back_region]
    seat_region = [v.copy() for v in vs if v.z <= seat + 0.005]
    seat_region += [Vector((v.x, v.y, 0.0)) for v in seat_region]

    bm = bmesh.new()
    for pts in (back_region, seat_region):
        tmp = bmesh.new()
        for p in pts:
            tmp.verts.new(p)
        res = bmesh.ops.convex_hull(tmp, input=tmp.verts[:])
        extra = {v for v in res.get('geom_interior', []) + res.get('geom_unused', []) if isinstance(v, bmesh.types.BMVert)}
        bmesh.ops.delete(tmp, geom=list(extra), context='VERTS')
        me = bpy.data.meshes.new('h')
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    cover = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(cover)

    # 2) 원단 곡면: 리메시(물 샐 틈 없는 한 겹) → 스무딩 → 1cm 부풀림 → 감축
    m = cover.modifiers.new('remesh', 'REMESH')
    m.mode = 'VOXEL'
    m.voxel_size = 0.008
    m = cover.modifiers.new('smooth', 'CORRECTIVE_SMOOTH')
    m.iterations = 18
    m.smooth_type = 'LENGTH_WEIGHTED'
    m.use_only_smooth = True
    m = cover.modifiers.new('inflate', 'DISPLACE')
    m.strength = 0.004
    m.mid_level = 0.0
    m = cover.modifiers.new('decimate', 'DECIMATE')
    m.ratio = 0.08
    _apply_modifiers(cover)
    bpy.data.objects.remove(base, do_unlink=True)
    cover.data.materials.append(cover_mat)
    cover.data.materials.append(sash_mat)
    for p in cover.data.polygons:
        p.use_smooth = True

    # 3) 새틴 띠: 등받이를 높이별로 잘라 얻은 단면 고리를 바깥으로 살짝 띄워 이어 붙인다 (깨끗한 띠)
    bm = bmesh.new()
    bm.from_mesh(cover.data)
    back_y = yb1 + 0.03

    def section(z, n=64):
        tmp = bm.copy()
        cut = bmesh.ops.bisect_plane(tmp, geom=tmp.verts[:] + tmp.edges[:] + tmp.faces[:],
                                     plane_co=(0, 0, z), plane_no=(0, 0, 1))
        pts = [v.co.copy() for v in cut['geom_cut'] if isinstance(v, bmesh.types.BMVert) and v.co.y < back_y]
        tmp.free()
        c = sum(pts, Vector()) / len(pts)
        pts.sort(key=lambda p: math.atan2(p.y - c.y, p.x - c.x))
        # 각도 기준으로 고르게 다시 뽑기
        out = []
        for k in range(n):
            a = -math.pi + 2 * math.pi * k / n
            best = max(pts, key=lambda p: math.cos(math.atan2(p.y - c.y, p.x - c.x) - a))
            d = (best - c)
            d.z = 0
            out.append(Vector((c.x, c.y, z)) + d * (1 + 0.012 / max(d.length, 1e-3)))
        return out

    levels = [SASH[0] + (SASH[1] - SASH[0]) * t for t in (0, 0.25, 0.5, 0.75, 1)]
    rings = []
    for i, z in enumerate(levels):
        bulge = 0.004 * math.sin(math.pi * i / (len(levels) - 1))       # 가운데가 살짝 부푼 새틴
        rings.append([bm.verts.new(p + (p - Vector((0, (yb0 + yb1) / 2, z))).normalized() * bulge) for p in section(z)])
    band_faces = []
    for r0, r1 in zip(rings[:-1], rings[1:]):
        n = len(r0)
        for k in range(n):
            f = bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
            f.material_index = 1
            f.smooth = True
            band_faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=band_faces)
    band_verts = {v for f in band_faces for v in f.verts}

    # 뒤 리본: 고리 두 개 + 꼬리 두 개 (납작한 띠)
    rear = min(v.co.y for v in band_verts)
    zc = sum(SASH) / 2

    def ribbon(points, width, twist=0.0):
        """점을 따라가는 폭 width 의 납작한 띠 (등받이 뒷면과 평행)"""
        n = len(points)
        left, right = [], []
        for i, p in enumerate(points):
            a = points[min(i + 1, n - 1)] - points[max(i - 1, 0)]
            side = a.cross(Vector((0, 1, 0))).normalized()
            if side.length < 0.5:
                side = Vector((0, 0, 1))
            left.append(bm.verts.new(p + side * width / 2))
            right.append(bm.verts.new(p - side * width / 2))
        faces = []
        for i in range(n - 1):
            f = bm.faces.new((left[i], left[i + 1], right[i + 1], right[i]))
            f.material_index = 1
            f.smooth = True
            faces.append(f)
        bmesh.ops.solidify(bm, geom=faces, thickness=0.004)   # 웹에서 양쪽 모두 보이도록 두께

    for s in (-1, 1):   # 고리 (작은 나비 모양)
        pts = [Vector((s * 0.055 * math.sin(t * math.pi),
                       rear - 0.008 - 0.022 * math.sin(t * math.pi),
                       zc + 0.022 * math.sin(t * 2 * math.pi) * s))
               for t in [k / 12 for k in range(13)]]
        ribbon(pts, 0.045)
    for s in (-1, 1):   # 꼬리
        pts = [Vector((s * (0.012 + 0.03 * t), rear - 0.01 - 0.012 * t, zc - 0.015 - 0.2 * t))
               for t in [k / 8 for k in range(9)]]
        ribbon(pts, 0.04)
    knot = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.018)
    for v in knot['verts']:
        v.co = Vector((v.co.x * 1.2, v.co.y * 0.8 + rear - 0.02, v.co.z + zc))
    for f in {f for v in knot['verts'] for f in v.link_faces}:
        f.material_index = 1
        f.smooth = True
    bm.to_mesh(cover.data)
    bm.free()
    _link_only(cover, coll)
    print('banquet chair', len(cover.data.polygons), 'faces, seat', round(seat, 2))
    return cover
