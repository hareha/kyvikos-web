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

    # 근접 사진 기준: 평범한 연회 의자에 검은 천 커버를 씌우고, 등받이 윗부분을
    # 샴페인 골드 새틴 띠로 묶어 뒤에서 리본을 매고 꼬리를 길게 아래로 늘어뜨린다.
    # 등받이는 웹 +z 쪽 (apec_stage 의 의자 배치가 그 전제로 각을 준다).
    BZ = SEAT_D / 2 - BACK_T / 2 - 0.01
    BY0 = SEAT_H + 0.01                                             # 등받이 밑
    add(_skirt(SEAT_W - 0.04, SEAT_D - 0.04, SEAT_W + 0.04, SEAT_D + 0.04, SEAT_H - 0.06, 0.0), Matrix(), cover_mat)
    for sx in (-1, 1):                                              # 자락에 잡히는 세로 주름
        for dz in (-0.28, 0.0, 0.28):
            add(bevel_box(0.035, SEAT_H - 0.09, 0.035, 0.012),
                T(sx * (SEAT_W / 2 + 0.012), (SEAT_H - 0.09) / 2, dz * SEAT_D), cover_mat)
            add(bevel_box(0.035, SEAT_H - 0.09, 0.035, 0.012),
                T(dz * SEAT_W, (SEAT_H - 0.09) / 2, sx * (SEAT_D / 2 + 0.012)), cover_mat)
    add(bevel_box(SEAT_W, 0.07, SEAT_D, 0.02), T(0, SEAT_H - 0.035, 0), cover_mat)                # 좌판
    add(bevel_box(SEAT_W - 0.04, BACK_H - 0.09, BACK_T, 0.022), T(0, BY0 + (BACK_H - 0.09) / 2, BZ, 0, 0.05), cover_mat)
    add(cyl(BACK_T / 2, BACK_T / 2, SEAT_W - 0.04, 12),                                            # 둥근 등받이 윗마구리
        T(0, BY0 + BACK_H - 0.045, BZ + 0.002, 0, 0, PI / 2), cover_mat)
    add(bevel_box(0.075, 0.075, SEAT_D - 0.08, 0.025), T(0, SEAT_H + 0.07, 0.0), cover_mat)        # 좌판 뒤 턱

    # 새틴 띠 — 등받이 윗부분 (사진: 등받이 꼭대기 바로 아래)
    ym, sh = BY0 + BACK_H * 0.70, BACK_H * 0.26
    add(box(SEAT_W - 0.03, sh, 0.013), T(0, ym, BZ - BACK_T / 2 - 0.007), sash_mat)
    add(box(SEAT_W - 0.03, sh, 0.013), T(0, ym, BZ + BACK_T / 2 + 0.007), sash_mat)
    for sx in (-1, 1):
        add(box(0.014, sh, BACK_T + 0.027), T(sx * (SEAT_W / 2 - 0.021), ym, BZ), sash_mat)
    rz = BZ + BACK_T / 2 + 0.028
    add(bevel_box(0.075, 0.075, 0.05, 0.02), T(0, ym, rz + 0.012), sash_mat)                       # 매듭
    for sx in (-1, 1):                                                                              # 리본 고리
        add(sphere(0.052, 3), T(sx * 0.072, ym + 0.012, rz + 0.026, 0, 0, sx * 0.55, 1.35, 0.85, 0.42), sash_mat)
        # 길게 늘어뜨린 꼬리: 좌판 아래까지 내려오며 살짝 벌어지고 끝이 꺾인다
        prev_y = ym - 0.03
        for k in range(5):
            t = k / 4
            yy = prev_y - 0.085
            add(box(0.072 - 0.006 * k, 0.095, 0.012),
                T(sx * (0.055 + 0.030 * t), yy, rz + 0.020 + 0.012 * t, 0, 0, sx * (0.16 + 0.10 * t)), sash_mat)
            prev_y = yy
        add(box(0.058, 0.055, 0.012), T(sx * 0.098, prev_y - 0.055, rz + 0.034, 0, 0, sx * 0.55), sash_mat)   # 꼬리 끝

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
