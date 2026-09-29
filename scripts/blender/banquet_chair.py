"""연회 의자 — 커버가 씌워진 실제 모델을 그대로 쓰고, 새틴 띠 색만 맞춘다.

프리미티브를 이어 붙여 커버를 흉내 내 봤지만(볼록 껍질+리메시, 상자 조립, 띠 면 스윕)
어느 쪽도 천으로 보이지 않았다. 커버가 씌워진 실제 모델을 쓰는 게 맞다.

  "Banquet Chair WITH COVER" by Event help (@sajan2) — CC-BY-4.0
  https://sketchfab.com/3d-models/banquet-chair-with-cover-17b52cddff214f14a3903175a339d939
  assets-src/models/banquet_chair_cover/scene.gltf
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

SRC = '/Users/hare/Documents/큐비크스홈페이지/assets-src/models/banquet_chair_cover/scene.gltf'
BOW = '/Users/hare/Documents/큐비크스홈페이지/assets-src/models/ribbon_bow/scene.gltf'   # 나비 고리만 쓴다
HEIGHT = 0.97          # 실제 연회 의자 높이 (m)


def _link_only(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def _bow_mesh(width=0.23):
    """받아온 리본 모델에서 나비 고리 부분을 가져온다 (고리가 ±y 로 퍼지고 매듭이 가운데).
       의자에 맞게 고리가 좌우(블렌더 x)로 퍼지도록 돌리고 실제 크기로 줄인다."""
    import os
    if not os.path.exists(BOW):
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=BOW)
    new = [o for o in bpy.data.objects if o not in before]
    src = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.polygons), default=None)
    bm = bmesh.new()
    if src is not None:
        bm.from_mesh(src.data)
        bm.transform(src.matrix_world)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    if not bm.verts:
        bm.free()
        return None
    # 모델 축: y = 고리가 퍼지는 방향(7.11), x = 고리의 넓은 쪽(3.28), z = 두께(1.75).
    # y->좌우(x), x->위아래(z), z->앞뒤(y) 로 돌려야 고리가 서고 납작해지지 않는다.
    bm.transform(Matrix(((0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 0), (0, 0, 0, 1))))
    vs = [v.co for v in bm.verts]
    span = max(v.x for v in vs) - min(v.x for v in vs)
    bm.transform(Matrix.Diagonal((width / span,) * 3 + (1,)))
    vs = [v.co for v in bm.verts]
    bm.transform(Matrix.Translation((-(min(v.x for v in vs) + max(v.x for v in vs)) / 2,
                                     -(min(v.y for v in vs) + max(v.y for v in vs)) / 2,
                                     -(min(v.z for v in vs) + max(v.z for v in vs)) / 2)))
    return bm


def _add_sash(me, sash_mat, at=0.70, band=0.105):
    """의자 커버 표면을 띠 높이에서 잘라내 그대로 띠로 쓴다 (밀착하는 면).

    판을 덧대거나(각지고 떠 보임) 단면을 재서 링을 만드는 방식(감축된 메시라 정점이
    모자라 후프가 되거나, 볼록 껍질이라 오목한 옆면에서 묻혀 끊김) 둘 다 실패했다.
    표면 자체를 잘라 법선으로 밀어내면 어떤 형상이든 정확히 밀착한다."""
    zs = [v.co.z for v in me.vertices]
    top = max(zs)
    zm = top * at
    z0, z1 = zm - band / 2, zm + band / 2

    bm = bmesh.new()

    def emit(builder):
        tmp = bmesh.new()
        builder(tmp)
        t = bpy.data.meshes.new('t')
        tmp.to_mesh(t)
        tmp.free()
        bm.from_mesh(t)
        bpy.data.meshes.remove(t)

    def band_build(b_):
        b_.from_mesh(me)
        for (co, clear) in (((0, 0, z0), 'inner'), ((0, 0, z1), 'outer')):
            g = b_.verts[:] + b_.edges[:] + b_.faces[:]
            bmesh.ops.bisect_plane(b_, geom=g, dist=1e-6, plane_co=co, plane_no=(0, 0, 1),
                                   clear_inner=(clear == 'inner'), clear_outer=(clear == 'outer'))
        # 자른 자리가 저폴리라 너덜거린다 — 겹친 점을 붙이고 찌그러진 면을 없앤다
        bmesh.ops.remove_doubles(b_, verts=b_.verts[:], dist=1e-4)
        bmesh.ops.dissolve_degenerate(b_, dist=1e-5, edges=b_.edges[:])
        loose = [v for v in b_.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(b_, geom=loose, context='VERTS')
        bmesh.ops.recalc_face_normals(b_, faces=b_.faces[:])
        b_.normal_update()
        for v in b_.verts:                       # 표면에서 살짝 띄운다 (천 두께)
            v.co += v.normal * 0.005
        if b_.faces:
            bmesh.ops.solidify(b_, geom=b_.faces[:], thickness=0.0035)

    emit(band_build)

    sl = [v.co for v in me.vertices if z0 - 0.02 < v.co.z < z1 + 0.02]
    if not sl:
        return
    cx = (min(v.x for v in sl) + max(v.x for v in sl)) / 2
    # 이 높이 전체의 최소 y 를 쓰면 등받이 말고 뒤로 더 나온 것(-0.334)이 잡혀
    # 나비가 등에서 12cm 뒤 허공에 떴다. 등받이 한가운데의 뒷면만 본다.
    cen = [v for v in sl if abs(v.x - cx) < 0.10] or sl
    ry = min(v.y for v in cen) - 0.009          # 등받이 뒷면 (블렌더 -y = 웹 +z)

    bow = _bow_mesh(width=0.155)               # 나비 고리는 받아온 모델 (deokpal, CC-BY)
    if bow is not None:
        bow.transform(Matrix.Translation((cx, ry - 0.040, zm - 0.004)))   # 띠 위에 얹힌다 (묻히지 않게)
        t = bpy.data.meshes.new('t')
        bow.to_mesh(t)
        bow.free()
        bm.from_mesh(t)
        bpy.data.meshes.remove(t)
    emit(lambda b_: bmesh.ops.create_cube(b_, size=1.0, matrix=Matrix.Translation((cx, ry - 0.036, zm))
         @ Matrix.Diagonal((0.040, 0.026, 0.044, 1))))   # 매듭

    # 꼬리: 매듭 밑에서 곧게 떨어진다. 면마다 커버 표면을 따라가게 했더니 굴곡 때문에
    #       중간이 커버 안으로 파묻혀 토막토막 끊겼다. 위·아래 두 점만 잡고 직선으로 잇는다.
    def back_y(z, prev):
        cand = [v.co.y for v in me.vertices if abs(v.co.z - z) < 0.030 and abs(v.co.x - cx) < 0.10]
        return min(cand) if cand else prev

    bm.faces.ensure_lookup_table()
    n_smooth = len(bm.faces)          # 여기까지(띠·나비·매듭)는 부드럽게, 꼬리는 각지게
    N, LEN = 40, 0.40
    z_top = zm + 0.010                # 매듭 안에서 시작해 띠 밑으로 빠져나온다
    z_bot = z_top - LEN
    y_top = ry - 0.024                # 매듭 앞면
    y_bot = back_y(z_bot, ry) - 0.011  # 아래쪽 커버 면에서 11mm
    tail, tw, tt = [], [], []
    for k in range(N):
        t = k / (N - 1)
        tail.append((cx, y_top + (y_bot - y_top) * t, z_top - LEN * t))
        tw.append(0.075 * (1 - 0.06 * t) * (1 - 0.85 * max(0.0, t - 0.92) / 0.08))
        tt.append(0.0)
    emit(_ribbon_bl(tail, tw, 0.0015, twist=tt))

    sm = bpy.data.meshes.new('sash')
    bm.to_mesh(sm)
    bm.free()
    n0 = len(me.polygons)
    j = bmesh.new()
    j.from_mesh(me)
    j.from_mesh(sm)
    j.to_mesh(me)
    j.free()
    bpy.data.meshes.remove(sm)
    # build() 의 use_smooth 는 이 앞에서 끝나 있다. 빠뜨리면 면 경계선이 다 보인다.
    # 다만 꼬리는 각져야 한다 — 납작한 띠를 부드럽게 칠하면 둥근 밧줄로 보인다.
    for k, f in enumerate(list(me.polygons)[n0:]):
        f.material_index = 1
        f.use_smooth = k < n_smooth


def build(coll, cover_mat, sash_mat, name='banquet_chair', decimate=0.22):
    """모델 안에는 같은 의자가 여섯 개와 원탁(Cylinder001) 하나가 들어 있다. 의자 하나만 쓴다.
    재질이 하나뿐이라 리본은 색이 분리돼 있지 않다 — 등받이 뒤로 튀어나온 부분(묶은 띠와
    늘어뜨린 꼬리)을 위치로 골라내 금색 새틴 재질을 입힌다."""
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC)
    new = [o for o in bpy.data.objects if o not in before]
    chairs = [o for o in new if o.type == 'MESH' and len(o.data.polygons) > 5000]
    src = max(chairs, key=lambda o: len(o.data.polygons))
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.transform(src.matrix_world)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)

    def ext():
        vs = [v.co for v in bm.verts]
        return [(min(v[i] for v in vs), max(v[i] for v in vs)) for i in range(3)]

    e = ext()
    up = max(range(3), key=lambda i: e[i][1] - e[i][0])
    if up == 0:
        bm.transform(Matrix.Rotation(-math.pi / 2, 4, 'Y'))
    elif up == 1:
        bm.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    e = ext()
    bm.transform(Matrix.Diagonal((HEIGHT / (e[2][1] - e[2][0]),) * 3 + (1,)))
    e = ext()
    bm.transform(Matrix.Translation((-(e[0][0] + e[0][1]) / 2, -(e[1][0] + e[1][1]) / 2, -e[2][0])))
    # 등받이 쪽을 블렌더 -y(웹 +z)로: 위쪽 절반의 무게중심이 치우친 방향을 뒤로 돌린다
    hi = [v.co for v in bm.verts if v.co.z > HEIGHT * 0.66]
    if hi:
        cx_ = sum(v.x for v in hi) / len(hi)
        cy_ = sum(v.y for v in hi) / len(hi)
        if math.hypot(cx_, cy_) > 1e-4:
            bm.transform(Matrix.Rotation(-math.atan2(cy_, cx_) - math.pi / 2, 4, 'Z'))
        e = ext()
        bm.transform(Matrix.Translation((-(e[0][0] + e[0][1]) / 2, -(e[1][0] + e[1][1]) / 2, 0)))

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(cover_mat)
    me.materials.append(sash_mat)
    for f in me.polygons:
        f.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    if decimate and decimate < 1.0:
        m = obj.modifiers.new('dec', 'DECIMATE')
        m.ratio = decimate
        dg = bpy.context.evaluated_depsgraph_get()
        nm = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
        obj.modifiers.clear()
        obj.data = nm
        bpy.data.meshes.remove(me)
    _add_sash(obj.data, sash_mat)          # 감축 뒤에 띠를 칠해야 얼룩이 안 생긴다
    _link_only(obj, coll)
    print('banquet chair %d faces (커버 씌워진 실제 모델)' % len(obj.data.polygons))
    return obj


def _ribbon_bl(pts, widths, thick=0.005, twist=None):
    """중심선을 따라 이어진 납작한 띠 (블렌더 좌표, z 가 위).
       상자를 여러 개 쌓으면 마디가 생겨 계단처럼 보이므로 한 장의 면으로 뽑는다.
       twist[i] 가 있으면 단면을 그만큼 돌려 천이 비틀려 늘어지게 한다."""
    def build(bm):
        rows = []
        for i, (p, w) in enumerate(zip(pts, widths)):
            p = Vector(p)
            t = Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])
            t = t.normalized() if t.length > 1e-6 else Vector((0, 0, -1))
            side = t.cross(Vector((0, 1, 0)))
            if side.length < 1e-6:
                side = t.cross(Vector((1, 0, 0)))
            side = side.normalized()
            if twist:
                side = (Matrix.Rotation(twist[i], 4, t) @ side).normalized()
            nrm = side.cross(t).normalized() * (thick / 2)
            side = side * (w / 2)
            rows.append([bm.verts.new(p - side + nrm), bm.verts.new(p + side + nrm),
                         bm.verts.new(p + side - nrm), bm.verts.new(p - side - nrm)])
        for a_, b_ in zip(rows[:-1], rows[1:]):
            for k in range(4):
                bm.faces.new((a_[k], a_[(k + 1) % 4], b_[(k + 1) % 4], b_[k]))
        bm.faces.new(rows[0][::-1])
        bm.faces.new(rows[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return build
