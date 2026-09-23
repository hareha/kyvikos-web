"""전시 구성 요소 — 가벽(그래픽이 벽면 자체인 면 분할), 작품 거는 방식별 액자, 차단봉, 곡선 트랙 조명, 진열장

모든 함수는 웹 좌표(Y-up), 로컬 +z = 앞(관람객 쪽). asm 은 lib.Assembly.
z-fighting 방지: 그래픽·작품 면은 따로 띄우지 않고 벽/판 면 자체를 그 그래픽으로 나눠 만든다.
"""
import math

import bmesh
from mathutils import Matrix
from mathutils import Vector as V

from lib import PI, T, bevel_box, box, cyl, plane, sphere, tube


def srgb(hex_):
    """'#RRGGBB' → Blender 선형 RGB"""
    h = hex_.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def quad_uv(w, h, uv=(0, 0, 1, 1)):
    """w×h 평면(+z 를 봄), UV 를 uv=(u0, v0, u1, v1) 범위로"""
    def build(bm):
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True,
                              matrix=Matrix.Diagonal((w, h, 1, 1)))
        layer = bm.loops.layers.uv.active
        for f in bm.faces:
            for lp in f.loops:
                u, v = lp[layer].uv
                lp[layer].uv = (uv[0] + u * (uv[2] - uv[0]), uv[1] + v * (uv[3] - uv[1]))
    return build


def _face(asm, frame, W, H, mat, decals, tile):
    """벽 한 면(로컬 원점 = 면 가운데 아래, +z 를 봄)을 그래픽 사각형 경계로 나눠 채운다.
    decals: [(cx, cy, w, h, gmat)] — cx 는 면 가운데 기준, cy 는 바닥 기준 가운데 높이"""
    xs = {-W / 2, W / 2}
    ys = {0.0, H}
    rects = []
    for (cx, cy, w, h, gm) in decals:
        x0, x1 = max(-W / 2, cx - w / 2), min(W / 2, cx + w / 2)
        y0, y1 = max(0.0, cy - h / 2), min(H, cy + h / 2)
        rects.append((x0, x1, y0, y1, gm, cx - w / 2, cy - h / 2, w, h))
        xs |= {x0, x1}
        ys |= {y0, y1}
    xs, ys = sorted(xs), sorted(ys)
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            a, b, c, d = xs[i], xs[i + 1], ys[j], ys[j + 1]
            if b - a < 1e-4 or d - c < 1e-4:
                continue
            mx, my = (a + b) / 2, (c + d) / 2
            hit = next((r for r in rects if r[0] <= mx <= r[1] and r[2] <= my <= r[3]), None)
            f = frame @ T(mx, my, 0)
            if hit:
                _, _, _, _, gm, gx, gy, gw, gh = hit
                uv = ((a - gx) / gw, (c - gy) / gh, (b - gx) / gw, (d - gy) / gh)
                asm.add(quad_uv(b - a, d - c, uv), f, gm, tile=None)
            else:
                asm.add(plane(b - a, d - c), f, mat, tile)


def wall(asm, a, b, h, t, front, back=None, decals_f=(), decals_b=(), top=None, ends=None, tile=2.0, y0=0.0):
    """가벽 a→b (xz 점). 앞면 = a→b 를 따라 걸을 때 왼쪽((-dz, dx) 방향). 두께 t, 높이 h.
    decals_f/b: 앞/뒷면 그래픽 [(cx, cy, w, h, mat)] (cx: 벽 가운데 기준, 앞면에서 볼 때 오른쪽 +)"""
    back = back or front
    d = V((b[0] - a[0], 0, b[1] - a[1]))
    L = d.length
    ry = math.atan2(-d.z, d.x)
    base = T((a[0] + b[0]) / 2, y0, (a[1] + b[1]) / 2, ry)
    _face(asm, base @ T(0, 0, t / 2), L, h, front, decals_f, tile)
    # 뒷면: 뒷면에서 볼 때 오른쪽이 +x 가 되도록 돌림
    _face(asm, base @ T(0, 0, -t / 2, PI), L, h, back, [(-cx, cy, w, hh, m) for (cx, cy, w, hh, m) in decals_b], tile)
    asm.add(plane(L, t), base @ T(0, h, 0, 0, -PI / 2), top or front, tile)
    for s in (-1, 1):
        asm.add(plane(t, h), base @ T(s * L / 2, h / 2, 0, s * PI / 2), ends or front, tile)
    return base


def wall_frame(a, b):
    """벽 a→b 의 앞면 기준 좌표계 (원점 = 벽 가운데 바닥, +z = 앞)"""
    d = V((b[0] - a[0], 0, b[1] - a[1]))
    return T((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2, math.atan2(-d.z, d.x)), d.length


def slab_sides(asm, f, w, h, depth, side_mat, back_mat=None):
    """판의 뒷면·옆면 (앞면 제외). f = 앞면 가운데"""
    asm.add(plane(w, h), f @ T(0, 0, -depth, PI), back_mat or side_mat, 1)
    asm.add(plane(depth, h), f @ T(w / 2, 0, -depth / 2, PI / 2), side_mat, 1)
    asm.add(plane(depth, h), f @ T(-w / 2, 0, -depth / 2, -PI / 2), side_mat, 1)
    asm.add(plane(w, depth), f @ T(0, h / 2, -depth / 2, 0, -PI / 2), side_mat, 1)
    asm.add(plane(w, depth), f @ T(0, -h / 2, -depth / 2, 0, PI / 2), side_mat, 1)


def slab_art(asm, f, w, h, depth, art, side_mat, back_mat=None):
    """앞면이 곧 그림인 얇은 판 (f = 판 앞면 가운데, 판은 -z 로 depth 만큼)"""
    asm.add(plane(w, h), f, art, tile=None)
    slab_sides(asm, f, w, h, depth, side_mat, back_mat)


def _moulding(asm, f, w, h, bw, bd, mat, z0=0.0):
    """안쪽 크기 w×h 를 두르는 액자 테 (폭 bw, 깊이 bd, 뒤 끝이 z0)"""
    for s in (-1, 1):
        asm.add(bevel_box(bw, h + 2 * bw, bd, min(0.006, bw / 4)), f @ T(s * (w / 2 + bw / 2), 0, z0 + bd / 2), mat, 1)
        asm.add(bevel_box(w, bw, bd, min(0.006, bw / 4)), f @ T(0, s * (h / 2 + bw / 2), z0 + bd / 2), mat, 1)


def artwork(asm, f, w, h, art, display, M):
    """작품 (f = 벽면 위 작품 가운데, +z = 벽 밖). 반환: 앞으로 튀어나온 깊이.
    display: unframed_stretcher / unframed_panel / white_box_frame / oak_frame / black_frame / gold_frame /
             dark_wood_frame / paper_white / paper_oak / paper_black (종이 작품: 흰 매트 + 테)"""
    if display == 'unframed_stretcher':
        # 캔버스를 한 치수 큰 나무 각재 틀에 끈으로 묶어 건 방식 (A-One·Phooey·Car Crash 사진)
        g = 0.09
        _moulding(asm, f, w + 2 * g, h + 2 * g, 0.05, 0.045, M['batten'], 0.0)
        slab_art(asm, f @ T(0, 0, 0.065), w, h, 0.035, art, M['canvasEdge'])
        for sx in (-1, 1):                      # 모서리 끈 (캔버스 → 각재)
            for sy in (-1, 1):
                p = f @ V((sx * (w / 2 - 0.02), sy * (h / 2 - 0.02), 0.06))
                q = f @ V((sx * (w / 2 + g + 0.025), sy * (h / 2 + g + 0.025), 0.03))
                g_, m_ = tube(p, q, 0.006, 6)
                asm.add(g_, m_, M['rope'])
        for k in (-1, 1):                       # 긴 변 가운데 끈
            for (px, py, qx, qy) in ((0, k * (h / 2 - 0.02), 0, k * (h / 2 + g + 0.025)), (k * (w / 2 - 0.02), 0, k * (w / 2 + g + 0.025), 0)):
                g_, m_ = tube(f @ V((px, py, 0.06)), f @ V((qx, qy, 0.03)), 0.006, 6)
                asm.add(g_, m_, M['rope'])
        return 0.1
    if display == 'unframed_panel':
        slab_art(asm, f @ T(0, 0, 0.04), w, h, 0.04, art, M['canvasEdge'])
        return 0.04
    if display == 'white_box_frame':
        # 깊은 흰 상자 액자: 테 8cm, 깊이 10cm, 그림은 안쪽으로 들어가 있음
        _moulding(asm, f, w + 0.06, h + 0.06, 0.07, 0.1, M['frameWhite'])
        slab_art(asm, f @ T(0, 0, 0.035), w, h, 0.015, art, M['frameWhite'])
        return 0.1
    paper = display.startswith('paper_')
    col = {'oak_frame': 'frameOak', 'paper_oak': 'frameOak', 'black_frame': 'frameBlack', 'paper_black': 'frameBlack',
           'gold_frame': 'frameGold', 'dark_wood_frame': 'frameDark', 'paper_white': 'frameWhite'}.get(display, 'frameBlack')
    mat_w = 0.07 if paper else 0.0
    bw = 0.035 if paper else 0.06
    iw, ih = w + 2 * mat_w, h + 2 * mat_w
    _moulding(asm, f, iw, ih, bw, 0.045, M[col])
    if paper:
        slab_sides(asm, f @ T(0, 0, 0.02), iw, ih, 0.02, M['mat'])                # 흰 매트 판: 앞면 = 매트 + 가운데 그림
        _face(asm, f @ T(0, -ih / 2, 0.02), iw, ih, M['mat'], [(0, ih / 2, w, h, art)], 1)
    else:
        slab_art(asm, f @ T(0, 0, 0.03), w, h, 0.03, art, M['canvasEdge'])
    return 0.045


def label(asm, f, M, w=0.11, h=0.075):
    """작품 캡션 (벽에서 3mm)"""
    asm.add(box(w, h, 0.004), f @ T(0, 0, 0.002), M['labelCard'], 1)


def stanchion_line(asm, pts, M, h=0.55, top=0.0):
    """검은 낮은 차단봉 + 줄 (사진: 무릎 높이, 작품 앞 1m)"""
    for x, z in pts:
        asm.add(cyl(0.13, 0.14, 0.02, 20), T(x, top + 0.01, z), M['rig'], 1)
        asm.add(cyl(0.016, 0.016, h, 10), T(x, top + 0.02 + h / 2, z), M['rig'], 1)
        asm.add(sphere(0.022, 2), T(x, top + 0.02 + h, z), M['rig'])
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        a, b = V((x0, top + h, z0)), V((x1, top + h, z1))
        n = 8
        prev = a
        for i in range(1, n + 1):
            t = i / n
            p = a.lerp(b, t) - V((0, 0.08 * 4 * t * (1 - t), 0))
            g, m = tube(prev, p, 0.005, 5)
            asm.add(g, m, M['rig'])
            prev = p


def track(rig, emit, pts, y, ceil_y, M, rod_every=3.0):
    """곡선 검은 트랙 레일 (천장에서 봉으로 매달림). pts: [(x, z)]"""
    P = [V((x, y, z)) for x, z in pts]
    for a, b in zip(P, P[1:]):
        g, m = tube(a, b, 0.022, 8)
        rig.add(g, m, M['rig'])
    acc = 0.0
    for i, (a, b) in enumerate(zip(P, P[1:])):
        if i == 0 or acc >= rod_every:
            g, m = tube(V((a.x, y, a.z)), V((a.x, ceil_y, a.z)), 0.008, 6)
            rig.add(g, m, M['rig'])
            acc = 0.0
        acc += (b - a).length
    g, m = tube(V((P[-1].x, y, P[-1].z)), V((P[-1].x, ceil_y, P[-1].z)), 0.008, 6)
    rig.add(g, m, M['rig'])


def spot_head(rig, emit, at, aim, M):
    """트랙 스포트 (어댑터 + 원통 몸체 + 렌즈). 반환: 렌즈 위치"""
    head = at - V((0, 0.16, 0))
    g, m = tube(at, head, 0.014, 6)
    rig.add(g, m, M['rig'])
    dvec = (aim - head).normalized()
    g, m = tube(head - dvec * 0.1, head + dvec * 0.11, 0.045, 12, caps=True)
    rig.add(g, m, M['rig'])
    lens = head + dvec * 0.112
    emit.add(cyl(0.035, 0.035, 0.004, 12), T(lens.x, lens.y, lens.z) @ _look(dvec), M['lampLens'])
    return lens


def _look(dvec):
    """로컬 +y 를 dvec 로 돌리는 회전 (cyl 은 y 축)"""
    up = V((0, 1, 0))
    q = up.rotation_difference(dvec)
    return q.to_matrix().to_4x4()


def vitrine(asm, glass_asm, f, w, d, h_base, h_glass, M, base_mat=None):
    """받침 + 유리 덮개 진열장 (f = 바닥 가운데)"""
    asm.add(bevel_box(w, h_base, d, 0.008), f @ T(0, h_base / 2, 0), base_mat or M['vitrineBase'], 1)
    glass_asm.add(box(w - 0.02, h_glass, d - 0.02), f @ T(0, h_base + h_glass / 2, 0), M['glass'], 1)


def extrude_card(asm, f, contour, w, h, depth, front, side, back=None):
    """정규화 윤곽선(0~1, v 위로) 을 w×h 로 키워 두께 depth 로 뽑은 판. 앞면 UV = 윤곽 좌표 (사진 그대로).
    f = 바닥 가운데 (앞 = +z)"""
    def build(bm):
        layer = bm.loops.layers.uv.active
        fr = [bm.verts.new(((u - 0.5) * w, v * h, depth / 2)) for u, v in contour]
        bk = [bm.verts.new(((u - 0.5) * w, v * h, -depth / 2)) for u, v in contour]
        ff = bm.faces.new(fr)
        fb = bm.faces.new(list(reversed(bk)))
        n = len(contour)
        sides = [bm.faces.new((fr[i], fr[(i + 1) % n], bk[(i + 1) % n], bk[i])) for i in range(n)]
        bm.normal_update()
        if ff.normal.z < 0:
            for x in [ff, fb] + sides:
                x.normal_flip()
        for lp in ff.loops:
            u = lp.vert.co.x / w + 0.5
            v = lp.vert.co.y / h
            lp[layer].uv = (u, v)
        ff.material_index = 0
        for x in [fb] + sides:
            x.material_index = 1
        bmesh.ops.triangulate(bm, faces=[ff, fb])
    asm.add(build, f, [front, side if back is None else back], tile=None)
