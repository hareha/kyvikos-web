"""벽 선분 목록 → 가벽 지오메트리 (rooms.py 를 대체).

rooms.py 는 **닫힌 직사각형 방**을 받아 사방에 벽을 세웠다. 실제 DDP 전시1관은
반경 16~23m 짜리 거의 원형인 무주 공간이고, 외곽 구역 벽은 그 껍데기를 따라
**휘어 있다** (`v3_a4b4_78406_006`, `..._78405_036`, `..._78406_075`).
게다가 가벽은 천장에 닿지 않고 3.0m 안팎에서 끊긴다.

여기서는 `layout_v4.json` 의 `walls` (선분 하나 = 가벽 한 장, 공유 구간은 한 장)를
그대로 세운다. 선분마다 자기 높이를 갖기 때문에 벽 위로 홀 천장이 그대로 보인다.

  build(asm, lay, decals, matmap, tile)
    lay     — layout_v4.json
    decals  — [(zone, face, u, y, w, h, gmat)] (u 는 rooms.py 규약 = x0/z0 부터)
    matmap  — 팔레트 키 → Blender 머티리얼
"""
import math

from mathutils import Vector as V

from lib import PI, T, plane
from gallery import _face


def _axis_of(side):
    return 0 if side in 'ns' else 1          # n/s 면은 x 를 따라, e/w 면은 z 를 따라


def u_world(rect, side, u):
    """rooms.py 규약의 u → 그 면이 달리는 축 위의 절대 좌표"""
    x0, x1, z0, z1 = rect
    return (x0 + u) if side in 'ns' else (z0 + u)


def _seg_frame(w, into, t):
    """선분 w 의 '안쪽(into 쪽)' 면 좌표계. 원점 = 면 가운데 바닥, +z = 안쪽"""
    p, q = V((w['p'][0], 0, w['p'][1])), V((w['q'][0], 0, w['q'][1]))
    d = q - p
    L = d.length
    ry = math.atan2(-d.z, d.x)               # 로컬 +x 가 p→q
    base = T((p.x + q.x) / 2, 0, (p.z + q.z) / 2, ry)
    # T(..., ry) 에서 로컬 +z 는 (sin ry, cos ry) = (-dz, dx)/L 방향
    # (gallery.wall 의 "앞면 = a→b 로 걸을 때 왼쪽" 과 같은 규약). into 가 반대면 180° 돌린다
    nx, nz = -d.z / L, d.x / L
    if (into[0] - (p.x + q.x) / 2) * nx + (into[1] - (p.z + q.z) / 2) * nz < 0:
        base = T((p.x + q.x) / 2, 0, (p.z + q.z) / 2, ry + PI)
    return base, L


def zone_centre(lay, zid):
    for z in lay['zones']:
        if z['id'] == zid:
            pts = z['poly']
            return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    return (0.0, 0.0)


def wall_face(zid, side, u, lay, t=None):
    """구역 zid 의 side 면, 그 면 위 u 지점의 좌표계 (원점 = 벽면 위 바닥, +z = 방 안쪽).

    곡선 벽이라 면 하나가 여러 선분으로 쪼개져 있다. u 가 떨어지는 선분을 찾아
    그 선분 위에서 좌표계를 만든다 — 그래서 작품이 곡면을 따라 살짝 돌아간다."""
    rect = next(z['rect'] for z in lay['zones'] if z['id'] == zid)
    ax = _axis_of(side)
    g = u_world(rect, side, u)
    cand = []
    for w in lay['walls']:
        for (zk, fk) in (('za', 'fa'), ('zb', 'fb')):
            if w[zk] == zid and w[fk] == side:
                lo, hi = sorted((w['p'][ax], w['q'][ax]))
                cand.append((w, lo, hi, abs((lo + hi) / 2 - g)))
    if not cand:
        x0, x1, z0, z1 = rect
        return {'n': T(x0 + u, 0, z0, 0), 's': T(x0 + u, 0, z1, PI),
                'w': T(x0, 0, z0 + u, PI / 2), 'e': T(x1, 0, z0 + u, -PI / 2)}[side]
    inside = [c for c in cand if c[1] - 0.05 <= g <= c[2] + 0.05]
    w, lo, hi, _ = (inside[0] if inside else min(cand, key=lambda c: c[3]))
    c = zone_centre(lay, zid)
    base, L = _seg_frame(w, c, w['t'])
    span = (hi - lo) or 1.0
    f = min(1.0, max(0.0, (g - lo) / span))                     # 선분 위 위치 0..1
    px, pz = w['p'], w['q']
    if (px[ax] > pz[ax]):
        f = 1.0 - f
    return base @ T((f - 0.5) * L, 0, w['t'] / 2)


def build(asm, lay, decals, matmap, tile=2.0):
    rects = {z['id']: z['rect'] for z in lay['zones']}
    cent = {z['id']: zone_centre(lay, z['id']) for z in lay['zones']}
    doors = []
    for d in lay.get('doors', []):
        if d['zone'] not in rects:
            continue
        x0, x1, z0, z1 = rects[d['zone']]
        sd, u0, u1 = d['face'], d['u0'], d['u1']
        L = (x1 - x0) if sd in 'ns' else (z1 - z0)
        a, b = (u0, u1) if sd in ('n', 'e') else (L - u1, L - u0)
        lo, hi = sorted((u_world(rects[d['zone']], sd, a), u_world(rects[d['zone']], sd, b)))
        doors.append({'zone': d['zone'], 'face': sd, 'ax': _axis_of(sd),
                      'lo': lo, 'hi': hi, 'h': d['h']})

    # 선분 끝점이 다른 벽과 이어지면 마구리를 만들지 않는다 (같은 면이 겹쳐 z-fighting)
    ends = {}
    for w in lay['walls']:
        for v in (w['p'], w['q']):
            k = (round(v[0], 2), round(v[1], 2))
            ends[k] = ends.get(k, 0) + 1

    built = 0
    for w in lay['walls']:
        za, zb, t, h = w['za'], w['zb'], w['t'], w['h']
        ax = _axis_of(w['fa'])
        lo, hi = sorted((w['p'][ax], w['q'][ax]))
        holes = []
        for d in doors:
            if d['zone'] not in (za, zb) or d['ax'] != ax:
                continue
            if d['face'] not in (w['fa'], w['fb']):
                continue
            a, b = max(d['lo'], lo), min(d['hi'], hi)
            if b - a > 0.05:
                holes.append((a, b, d['h']))
        base, L = _seg_frame(w, cent.get(za, (0, 0)), t)
        flip = w['p'][ax] > w['q'][ax]

        def loc(g):                                   # 축 좌표 → 로컬 x (-L/2..L/2)
            f = (g - lo) / ((hi - lo) or 1.0)
            return ((1 - f) - 0.5) * L if flip else (f - 0.5) * L

        parts = [(-L / 2, L / 2, 0.0, h)]
        for (a, b, dh) in holes:
            la, lb = sorted((loc(a), loc(b)))
            nxt = []
            for (p0, p1, y0, y1) in parts:
                if lb <= p0 or la >= p1:
                    nxt.append((p0, p1, y0, y1))
                    continue
                if la > p0:
                    nxt.append((p0, la, y0, y1))
                if lb < p1:
                    nxt.append((lb, p1, y0, y1))
                if dh < y1 - 0.03:
                    nxt.append((max(p0, la), min(p1, lb), dh, y1))   # 인방
            parts = [p for p in nxt if p[1] - p[0] > 0.03]

        ma = matmap.get(w['ma'], matmap['white'])
        mb = matmap.get(w['mb'], matmap['white'])
        for (p0, p1, y0, y1) in parts:
            sl, sh_ = p1 - p0, y1 - y0
            mid = (p0 + p1) / 2
            fr = base @ T(mid, y0, 0)

            def decs(zid, fc, side_sign):
                out = []
                if not zid or zid not in rects:
                    return out
                for (rm, sd, u, y, dw, dh, mt) in decals:
                    if rm != zid or sd != fc:
                        continue
                    g = u_world(rects[rm], sd, u)
                    lx = loc(g)
                    if lx + dw / 2 <= p0 or lx - dw / 2 >= p1:
                        continue
                    if y + dh / 2 <= y0 or y - dh / 2 >= y1:
                        continue
                    out.append((side_sign * (lx - mid), y - y0, dw, dh, mt))
                return out

            _face(asm, fr @ T(0, 0, t / 2), sl, sh_, ma, decs(za, w['fa'], 1), tile)
            _face(asm, fr @ T(0, 0, -t / 2, PI), sl, sh_, mb, decs(zb, w['fb'], -1), tile)
            if y1 >= h - 1e-6:
                asm.add(plane(sl, t), fr @ T(0, sh_, 0, 0, -PI / 2), ma, tile)
            if y0 > 1e-6:
                asm.add(plane(sl, t), fr @ T(0, 0, 0, 0, PI / 2), mb, tile)
            for s in (-1, 1):
                v = p1 if s > 0 else p0
                at_end = abs(abs(v) - L / 2) < 1e-6
                corner = (round(w['q'][0], 2), round(w['q'][1], 2)) if (v > 0) != flip else \
                         (round(w['p'][0], 2), round(w['p'][1], 2))
                if at_end and ends.get(corner, 0) > 1:
                    continue
                asm.add(plane(t, sh_), fr @ T(s * sl / 2, sh_ / 2, 0, s * PI / 2), ma, tile)
            built += 1
    return built


def island(asm, a, b, h, t, front, back, matmap, tile=2.0, decals_f=(), decals_b=()):
    """사방이 트인 독립 가벽 — 양 옆 마구리와 윗면을 다 만든다"""
    d = V((b[0] - a[0], 0, b[1] - a[1]))
    L = d.length
    base = T((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2, math.atan2(-d.z, d.x))
    mf = matmap.get(front, matmap['white'])
    mb = matmap.get(back, matmap['white'])
    _face(asm, base @ T(0, 0, t / 2), L, h, mf, decals_f, tile)
    _face(asm, base @ T(0, 0, -t / 2, PI), L, h, mb,
          [(-cx, cy, w_, h_, m) for (cx, cy, w_, h_, m) in decals_b], tile)
    asm.add(plane(L, t), base @ T(0, h, 0, 0, -PI / 2), mf, tile)
    for s in (-1, 1):
        asm.add(plane(t, h), base @ T(s * L / 2, h / 2, 0, s * PI / 2), mf, tile)
    return base
