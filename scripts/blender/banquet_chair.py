"""연회 의자 — 검은 스판 커버를 씌운 연회 의자 + 샴페인 골드 새틴 띠 (apec_stage.py 에서 사용)

전에는 불러온 의자 모델을 볼록 껍질 → 복셀 리메시 → 스무딩 → 감축으로 감싸 커버를 만들었는데,
어떤 값을 써도 등받이 각과 좌판 선이 뭉개져 둥근 덩어리가 됐다. 사진의 커버는 몸에 딱 맞는
스판이라 면이 평평하고 모서리가 살아 있다. 그래서 형태를 직접 깎는다.

사진(APEC 만찬) 기준 치수
  전체 높이 0.95m · 좌판 높이 0.46m · 좌판 0.46 x 0.46 · 등받이 0.44 x 0.49 (두께 0.07)
  커버 자락은 좌판에서 바닥까지 곧게 떨어지며 아래로 아주 조금 퍼진다
  등받이 위쪽을 두른 새틴 띠 + 뒤에서 묶은 리본
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from lib import PI, T, bevel_box, box, cyl, sphere

SEAT_H, SEAT_W, SEAT_D = 0.46, 0.46, 0.46
BACK_H, BACK_T = 0.49, 0.075
SASH = (0.63, 0.80)


def _skirt(w0, d0, w1, d1, h, y0):
    """아래로 살짝 퍼지는 네 면 자락 (윗면 w0 x d0 -> 밑면 w1 x d1)"""
    def build(bm):
        top = [(-w0 / 2, y0 + h, -d0 / 2), (w0 / 2, y0 + h, -d0 / 2), (w0 / 2, y0 + h, d0 / 2), (-w0 / 2, y0 + h, d0 / 2)]
        bot = [(-w1 / 2, y0, -d1 / 2), (w1 / 2, y0, -d1 / 2), (w1 / 2, y0, d1 / 2), (-w1 / 2, y0, d1 / 2)]
        tv = [bm.verts.new(p) for p in top]
        bv = [bm.verts.new(p) for p in bot]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((tv[i], tv[j], bv[j], bv[i]))
        bm.faces.new(tv[::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.012, segments=2, affect='EDGES', profile=0.6)
    return build


def build(coll, cover_mat, sash_mat, name='banquet_chair'):
    bm_by_mat = {}

    def add(builder, matrix, mat):
        tmp = bmesh.new()
        tmp.loops.layers.uv.new('UVMap')
        builder(tmp)
        bmesh.ops.transform(tmp, matrix=matrix, verts=tmp.verts)
        me = bpy.data.meshes.new('t')
        tmp.to_mesh(me)
        tmp.free()
        bm_by_mat.setdefault(mat, bmesh.new()).from_mesh(me)
        bpy.data.meshes.remove(me)

    # 자락 (좌판 밑 ~ 바닥) + 좌판 + 등받이
    add(_skirt(SEAT_W - 0.01, SEAT_D - 0.01, SEAT_W + 0.06, SEAT_D + 0.06, SEAT_H - 0.05, 0.0), Matrix(), cover_mat)
    add(bevel_box(SEAT_W, 0.075, SEAT_D, 0.022), T(0, SEAT_H - 0.035, 0), cover_mat)
    add(bevel_box(SEAT_W - 0.03, BACK_H, BACK_T, 0.028), T(0, SEAT_H + BACK_H / 2 + 0.01, -SEAT_D / 2 + BACK_T / 2 + 0.01, 0, -0.05), cover_mat)
    add(bevel_box(SEAT_W - 0.06, 0.05, BACK_T + 0.02, 0.02), T(0, SEAT_H + BACK_H + 0.03, -SEAT_D / 2 + BACK_T / 2 + 0.005), cover_mat)   # 등받이 윗마구리

    # 새틴 띠: 등받이를 두르고 뒤에서 리본
    sh = SASH[1] - SASH[0]
    for (w_, d_, x_, z_) in ((SEAT_W + 0.01, 0.012, 0.0, -SEAT_D / 2 + BACK_T + 0.012),
                             (SEAT_W + 0.01, 0.012, 0.0, -SEAT_D / 2 - 0.006)):
        add(box(w_, sh, d_), T(x_, (SASH[0] + SASH[1]) / 2, z_), sash_mat)
    for sx in (-1, 1):
        add(box(0.014, sh, BACK_T + 0.03), T(sx * (SEAT_W / 2 - 0.003), (SASH[0] + SASH[1]) / 2, -SEAT_D / 2 + BACK_T / 2), sash_mat)
    rz = -SEAT_D / 2 - 0.02
    for sx in (-1, 1):                                        # 리본 고리 두 개
        add(sphere(0.055, 3), T(sx * 0.055, SASH[0] + sh * 0.5, rz - 0.035, 0, 0, sx * 0.5, 1.5, 1.0, 0.55), sash_mat)
        add(box(0.035, 0.16, 0.012), T(sx * 0.05, SASH[0] - 0.06, rz - 0.02, 0, 0, sx * 0.35), sash_mat)   # 꼬리
    add(sphere(0.028, 2), T(0, SASH[0] + sh * 0.5, rz - 0.03), sash_mat)   # 매듭

    mats = list(bm_by_mat.keys())
    out = bmesh.new()
    me = bpy.data.meshes.new(name)
    for mi, m in enumerate(mats):
        tmp = bpy.data.meshes.new('t')
        bm_by_mat[m].to_mesh(tmp)
        bm_by_mat[m].free()
        start = len(out.faces)
        out.from_mesh(tmp)
        out.faces.ensure_lookup_table()
        for f in out.faces[start:]:
            f.material_index = mi
        bpy.data.meshes.remove(tmp)
    bmesh.ops.transform(out, matrix=Matrix.Rotation(PI / 2, 4, 'X'), verts=out.verts)   # 웹 Y-up -> 블렌더
    out.to_mesh(me)
    out.free()
    for m in mats:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    print('banquet chair %d faces, seat %.2f' % (len(me.polygons), SEAT_H))
    return obj
