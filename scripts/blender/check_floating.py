"""떠 있는 부재 검사 — 서로 2cm 안으로 닿는 덩어리끼리 연결해, 땅(바닥 y<0.05)까지 이어지지 않는
덩어리 묶음을 찾는다. 기둥과 떨어진 지붕·보 묶음처럼 '통째로 떠 있는' 것도 잡힌다.

  python3 scripts/blender/bmcp.py exec scripts/blender/check_floating.py
결과: 묶음 크기(덩어리 수), 오브젝트, 밑면 높이, 웹 좌표 중심
"""
import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOUCH = 0.02
SKIP = ('pine_needles', 'tree_leaves', 'context_emissive', 'emissive', 'glass', 'context_glass')

verts, polys, face_island = [], [], []
islands = []          # (object, zmin, center, sample verts)
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.name.startswith(SKIP) or ob.name.startswith(('chair_', 'wineglass_')):
        continue
    if any(c.name in ('SOURCES', 'RENDER_ONLY', 'LIGHTS', 'CAMERAS') for c in ob.users_collection):
        continue
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    comp = [-1] * len(bm.verts)
    for v0 in bm.verts:
        if comp[v0.index] >= 0:
            continue
        iid = len(islands)
        stack, pts = [v0], []
        comp[v0.index] = iid
        while stack:
            v = stack.pop()
            pts.append(v.co.copy())
            for e in v.link_edges:
                w = e.other_vert(v)
                if comp[w.index] < 0:
                    comp[w.index] = iid
                    stack.append(w)
        zmin = min(p.z for p in pts)
        c = sum(pts, Vector()) / len(pts)
        step = max(1, len(pts) // 80)
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), zmin))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        islands.append((ob.name, zmin, c, pts[::step], lo, hi))
    base = len(verts)
    verts.extend(v.co.copy() for v in bm.verts)
    for f in bm.faces:
        polys.append([base + v.index for v in f.verts])
        face_island.append(comp[f.verts[0].index])
    bm.free()

tree = BVHTree.FromPolygons(verts, polys)
parent = list(range(len(islands)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb


# 서로 관통하는 덩어리 (면끼리 교차) 도 연결
isl_polys = {}
for fi, poly in enumerate(polys):
    isl_polys.setdefault(face_island[fi], []).append(poly)
trees = {}
def itree(i):
    if i not in trees:
        ps = isl_polys.get(i, [])
        idx = sorted({v for p in ps for v in p})
        remap = {v: k for k, v in enumerate(idx)}
        trees[i] = BVHTree.FromPolygons([verts[v] for v in idx], [[remap[v] for v in p] for p in ps]) if ps else None
    return trees[i]
cell = {}
for i, isl in enumerate(islands):
    lo, hi = isl[4], isl[5]
    for gx in range(int(lo.x // 4), int(hi.x // 4) + 1):
        for gy in range(int(lo.y // 4), int(hi.y // 4) + 1):
            cell.setdefault((gx, gy), []).append(i)
checked = set()
for members in cell.values():
    for a in range(len(members)):
        for b in range(a + 1, len(members)):
            i, j = members[a], members[b]
            if (i, j) in checked or find(i) == find(j):
                continue
            checked.add((i, j))
            A, B = islands[i], islands[j]
            if any(A[4][k] > B[5][k] + TOUCH or B[4][k] > A[5][k] + TOUCH for k in range(3)):
                continue
            ta, tb = itree(i), itree(j)
            if ta and tb and ta.overlap(tb):
                union(i, j)

for iid, (_, _, _, pts, _, _) in enumerate(islands):
    for p in pts:
        for (_, _, fi, _) in tree.find_nearest_range(p, TOUCH):
            j = face_island[fi]
            if j != iid:
                union(iid, j)

grounded = {find(i) for i, isl in enumerate(islands) if isl[1] < 0.05}
groups = {}
for i, isl in enumerate(islands):
    r = find(i)
    if r not in grounded:
        groups.setdefault(r, []).append(isl)
print('islands', len(islands), 'floating groups', len(groups))
rows = []
for r, g in groups.items():
    zmin = min(i[1] for i in g)
    c = sum((i[2] for i in g), Vector()) / len(g)
    names = sorted({i[0] for i in g})
    rows.append((len(g), names, round(zmin, 2), (round(c.x, 1), round(c.z, 1), round(-c.y, 1))))
for row in sorted(rows, key=lambda r: -r[0])[:120]:
    print(row)

# 큰 묶음은 구성 덩어리(밑면·범위)도 출력
if globals().get('VERBOSE'):
    for r, g in sorted(groups.items(), key=lambda t: -len(t[1]))[:VERBOSE]:
        if g[0][0] in ('backstage', 'lanterns', 'stage', 'tables'):
            continue
        print('--- group', len(g))
        for isl in sorted(g, key=lambda i: i[1])[:8]:
            lo, hi = isl[4], isl[5]
            print('   ', isl[0], 'y', round(lo.z, 2), '~', round(hi.z, 2), 'x', round(lo.x, 1), '~', round(hi.x, 1), 'z', round(-hi.y, 1), '~', round(-lo.y, 1))
