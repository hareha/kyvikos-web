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

    # 1) 커버 원형: 의자 + 좌판 아래를 바닥까지 채운 상자(아래로 살짝 퍼짐)
    bm = bmesh.new()
    bm.from_mesh(base.data)
    fill = bmesh.new()
    bmesh.ops.create_cube(fill, size=1.0)
    for v in fill.verts:
        flare = 1.06 if v.co.z < 0 else 1.0
        v.co.x = v.co.x * (x1 - x0) * flare
        v.co.y = (y0 + y1) / 2 + v.co.y * (y1 - y0) * flare
        v.co.z = (v.co.z + 0.5) * (seat - 0.02)
    me = bpy.data.meshes.new('f')
    fill.to_mesh(me)
    fill.free()
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
    m.voxel_size = 0.012
    m = cover.modifiers.new('smooth', 'CORRECTIVE_SMOOTH')
    m.iterations = 30
    m.smooth_type = 'LENGTH_WEIGHTED'
    m.use_only_smooth = True
    m = cover.modifiers.new('inflate', 'DISPLACE')
    m.strength = 0.01
    m.mid_level = 0.0
    m = cover.modifiers.new('decimate', 'DECIMATE')
    m.ratio = 0.12
    _apply_modifiers(cover)
    bpy.data.objects.remove(base, do_unlink=True)
    cover.data.materials.append(cover_mat)
    cover.data.materials.append(sash_mat)
    for p in cover.data.polygons:
        p.use_smooth = True

    # 3) 새틴 띠: 등받이 부분에서 띠 높이의 면을 떼어 바깥으로 두께
    bm = bmesh.new()
    bm.from_mesh(cover.data)
    # 띠 위아래를 평면으로 잘라 가장자리를 곧게
    for zc_ in SASH:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zc_), plane_no=(0, 0, 1))
    back_y = y0 + (y1 - y0) * 0.35          # 등받이 쪽(-y)
    band = [f for f in bm.faces
            if SASH[0] - 1e-4 <= min(v.co.z for v in f.verts) and max(v.co.z for v in f.verts) <= SASH[1] + 1e-4
            and f.calc_center_median().y < back_y]
    dup = bmesh.ops.duplicate(bm, geom=band)
    band_faces = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
    for f in band_faces:
        f.material_index = 1
    band_verts = {v for f in band_faces for v in f.verts}
    for v in band_verts:
        v.co += v.normal * 0.006
    bmesh.ops.solidify(bm, geom=band_faces, thickness=0.004)

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
        for i in range(n - 1):
            f = bm.faces.new((left[i], left[i + 1], right[i + 1], right[i]))
            f.material_index = 1
            f.smooth = True

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
