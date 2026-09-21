"""z-fighting 검사 — 같은 방향을 보며 거의 같은 평면(2cm 이내)에서 겹치는 면 쌍을 모두 찾는다

  python3 scripts/blender/bmcp.py exec scripts/blender/check_zfight.py

결과는 웹 좌표(x, y, z)로 겹치는 영역의 중심과 두 오브젝트/재질 이름을 출력한다.
식생(솔잎·잎 카드·나무)과 의자 인스턴스는 제외.
"""
import math
from collections import defaultdict

import bpy

TOL = 0.06          # 평면 사이 거리 (웹 조감 거리에서 깊이 버퍼가 구분 못 하는 간격)
MIN_AREA = 0.02     # 겹치는 넓이(m²) 이상만
SKIP = ('pines', 'pine_needles', 'tree_leaves', 'banquet_chair')

faces = []   # (obj, mat, normal, d, verts(world))
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.name.startswith(SKIP) or ob.name.startswith('chair_'):
        continue
    if any(c.name in ('SOURCES', 'RENDER_ONLY') for c in ob.users_collection):
        continue
    mw = ob.matrix_world
    me = ob.data
    for p in me.polygons:
        if p.area < 1e-4:
            continue
        vs = [mw @ me.vertices[i].co for i in p.vertices]
        n = (mw.to_3x3() @ p.normal).normalized()
        if n.z < -0.9:      # 아래를 보는 면(Blender -z = 웹 아래)은 바닥·몸체 속에 묻혀 보이지 않음
            continue
        mat = me.materials[p.material_index].name if me.materials else ''
        faces.append((ob.name, mat, n, n.dot(vs[0]), vs))

buckets = defaultdict(list)
for i, (_, _, n, d, _) in enumerate(faces):
    key = (round(n.x, 1), round(n.y, 1), round(n.z, 1))
    buckets[key].append(i)


def basis(n):
    a = (1, 0, 0) if abs(n.x) < 0.9 else (0, 1, 0)
    from mathutils import Vector
    u = n.cross(Vector(a)).normalized()
    return u, n.cross(u)


hits = defaultdict(float)
where = {}
for key, idx in buckets.items():
    idx.sort(key=lambda i: faces[i][3])
    n0 = faces[idx[0]][2]
    u, v = basis(n0)
    poly2 = {}
    for i in idx:
        poly2[i] = [(p.dot(u), p.dot(v)) for p in faces[i][4]]

    def area(P):
        return abs(sum(P[k][0] * P[k - 1][1] - P[k - 1][0] * P[k][1] for k in range(len(P)))) / 2

    def clip(P, Q):
        """볼록 다각형 P 를 볼록 다각형 Q 로 자른다 (Sutherland–Hodgman)"""
        if area(Q) < 1e-9:
            return []
        sgn = 1 if sum(Q[k][0] * Q[k - 1][1] - Q[k - 1][0] * Q[k][1] for k in range(len(Q))) < 0 else -1
        out = P
        for k in range(len(Q)):
            a, b = Q[k - 1], Q[k]
            inp, out = out, []
            if not inp:
                break
            side = lambda p: sgn * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= -1e-9
            for m in range(len(inp)):
                cur, prev = inp[m], inp[m - 1]
                if side(cur):
                    if not side(prev):
                        out.append(inter(prev, cur, a, b))
                    out.append(cur)
                elif side(prev):
                    out.append(inter(prev, cur, a, b))
        return out

    def inter(p, q, a, b):
        x1, y1, x2, y2, x3, y3, x4, y4 = *p, *q, *a, *b
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    bbox = {i: (min(q[0] for q in P), max(q[0] for q in P), min(q[1] for q in P), max(q[1] for q in P)) for i, P in poly2.items()}
    for a in range(len(idx)):
        i = idx[a]
        for b in range(a + 1, len(idx)):
            j = idx[b]
            if faces[j][3] - faces[i][3] > TOL:
                break
            if faces[i][2].dot(faces[j][2]) < 0.999:
                continue
            ra, rb = bbox[i], bbox[j]
            if min(ra[1], rb[1]) - max(ra[0], rb[0]) <= 0.01 or min(ra[3], rb[3]) - max(ra[2], rb[2]) <= 0.01:
                continue
            ov = area(clip(poly2[i], poly2[j])) if len(poly2[i]) >= 3 else 0
            if ov < MIN_AREA:
                continue
            oi, mi = faces[i][0], faces[i][1]
            oj, mj = faces[j][0], faces[j][1]
            k = tuple(sorted(((oi, mi), (oj, mj))))
            c = sum(faces[i][4], faces[i][4][0] * 0) / len(faces[i][4])
            hits[k] += ov
            where.setdefault(k, []).append((round(c.x, 1), round(c.z, 1), round(-c.y, 1), round(faces[j][3] - faces[i][3], 3)))

print('z-fight pairs:', len(hits))
for k, area in sorted(hits.items(), key=lambda t: -t[1])[:80]:
    pts = where[k]
    print(f'{area:8.2f} m²  {k[0][0]}/{k[0][1]}  ×  {k[1][0]}/{k[1][1]}   n={len(pts)} e.g. {pts[:3]}')
