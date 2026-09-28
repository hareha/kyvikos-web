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


def _add_sash(me, sash_mat, at=0.76, band=0.092):
    """등받이 단면을 실제로 재서 그 둘레에 새틴 띠를 감고, 뒤에 리본과 늘어뜨린 꼬리를 단다.
       (이 모델에는 리본이 없다. 커버만 씌워져 있다.)"""
    zs = [v.co.z for v in me.vertices]
    top = max(zs)
    zm = top * at
    sl = [v.co for v in me.vertices if abs(v.co.z - zm) < 0.012]
    if len(sl) < 8:
        return
    cx = sum(v.x for v in sl) / len(sl)
    cy = sum(v.y for v in sl) / len(sl)
    # 등받이는 납작한 판이다. 윤곽을 각도로 추적하면 점이 성겨 띠가 들쭉날쭉해지니,
    # 단면의 가로·세로만 재서 상자 하나로 두른다 (밖에서 보면 감긴 띠로 읽힌다).
    bx0, bx1 = min(v.x for v in sl), max(v.x for v in sl)
    by0, by1 = min(v.y for v in sl), max(v.y for v in sl)

    bm = bmesh.new()

    def emit(builder):
        tmp = bmesh.new()
        builder(tmp)
        t = bpy.data.meshes.new('t')
        tmp.to_mesh(t)
        tmp.free()
        bm.from_mesh(t)
        bpy.data.meshes.remove(t)

    # 띠는 도형을 덧대지 않고 의자 표면 자체를 칠한다.
    # (상자든 스윕이든 덧대면 등받이보다 넓게 떠서 챙처럼 보였다.)
    cx, ry = (bx0 + bx1) / 2, by0 - 0.010               # 등받이 뒷면 (블렌더 -y = 웹 +z)
    bow = _bow_mesh(width=0.21)                          # 나비 고리는 받아온 모델 (deokpal, CC-BY)
    if bow is not None:
        bow.transform(Matrix.Translation((cx, ry - 0.022, zm - 0.008)))
        t = bpy.data.meshes.new('t')
        bow.to_mesh(t)
        bow.free()
        bm.from_mesh(t)
        bpy.data.meshes.remove(t)
    for sx in (-1, 1):
        tail, tw = [], []
        for k in range(10):                              # 좌판 아래까지 늘어뜨린 꼬리 (두 갈래가 확실히 벌어지게)
            t = k / 9
            tail.append((cx + sx * (0.062 + 0.105 * t * t), ry - 0.016 - 0.034 * math.sin(t * 2.3),
                         zm - 0.030 - 0.052 * k))
            tw.append(0.082 - 0.028 * t)
        emit(_ribbon_bl(tail, tw, 0.007))

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
    for f in list(me.polygons)[n0:]:
        f.material_index = 1
    # 면의 중심만 보면 큰 면이 통째로 칠해져 삼각형 얼룩이 된다. 모든 꼭짓점이 띠 안일 때만.
    for f in me.polygons:
        if all(abs(me.vertices[i].co.z - zm) <= band / 2 for i in f.vertices):
            f.material_index = 1


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


def _ribbon_bl(pts, widths, thick=0.006):
    """중심선을 따라 이어진 납작한 띠 (블렌더 좌표, z 가 위).
       상자를 여러 개 쌓으면 마디가 생겨 계단처럼 보이므로 한 장의 면으로 뽑는다."""
    def build(bm):
        rows = []
        for i, (p, w) in enumerate(zip(pts, widths)):
            p = Vector(p)
            t = Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])
            t = t.normalized() if t.length > 1e-6 else Vector((0, 0, -1))
            side = t.cross(Vector((0, 1, 0)))
            if side.length < 1e-6:
                side = t.cross(Vector((1, 0, 0)))
            side = side.normalized() * (w / 2)
            nrm = side.cross(t).normalized() * (thick / 2)
            rows.append([bm.verts.new(p - side + nrm), bm.verts.new(p + side + nrm),
                         bm.verts.new(p + side - nrm), bm.verts.new(p - side - nrm)])
        for a_, b_ in zip(rows[:-1], rows[1:]):
            for k in range(4):
                bm.faces.new((a_[k], a_[(k + 1) % 4], b_[(k + 1) % 4], b_[k]))
        bm.faces.new(rows[0][::-1])
        bm.faces.new(rows[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return build
