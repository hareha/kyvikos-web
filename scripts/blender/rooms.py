"""직사각형 방 배치 → 가벽 자동 생성 (공유 벽 한 번, 문 구멍, 방마다 면 색, 벽면 그래픽을 면 분할로)

rooms: {id: {'rect': (x0, x1, z0, z1), 'color': mat, 'sides': {'n'|'s'|'e'|'w': mat}, 'open': {'n', ...}}}
  - 'n' = z0 쪽 벽, 's' = z1 쪽, 'w' = x0 쪽, 'e' = x1 쪽 (웹 좌표 +z 가 남쪽)
  - 'open' 에 든 변은 벽을 세우지 않음 (전시홀 외벽에 붙은 변 등)
doors: [(x0, x1, z0, z1)] — 이 사각형과 겹치는 벽 구간을 비움
decals: [(room, side, u, y, w, h, mat)] — 방 안쪽에서 본 벽면 그래픽 (u: 그 변의 시작점(x0/z0)부터 가운데까지 거리)
"""
import math

from lib import PI, T, plane
from gallery import _face


def wall_face(room, side, u, rooms, t):
    """방 안쪽에서 본 벽면 위 한 점의 좌표계 (원점 = 벽면 위 바닥, +z = 방 안쪽, +x = 벽을 보고 오른쪽)"""
    x0, x1, z0, z1 = rooms[room]['rect']
    if side == 'n':
        return T(x0 + u, 0, z0 + t / 2, 0)
    if side == 's':
        return T(x0 + u, 0, z1 - t / 2, PI)
    if side == 'w':
        return T(x0 + t / 2, 0, z0 + u, PI / 2)
    return T(x1 - t / 2, 0, z0 + u, -PI / 2)


def build(asm, rooms, doors, decals, h, t, default_mat, tile=2.0):
    # 선(축, 좌표) 별로 구간과 양쪽 방을 모은다
    lines = {}
    for rid, r in rooms.items():
        x0, x1, z0, z1 = r['rect']
        for side, (axis, c, a, b, pos) in {'n': ('z', z0, x0, x1, +1), 's': ('z', z1, x0, x1, -1),
                                           'w': ('x', x0, z0, z1, +1), 'e': ('x', x1, z0, z1, -1)}.items():
            if side in r.get('open', ()):
                continue
            key = (axis, round(c, 3))
            lines.setdefault(key, []).append((a, b, rid, side, pos))
    walls = []
    for (axis, c), segs in lines.items():
        cuts = sorted({v for s in segs for v in (s[0], s[1])})
        for a, b in zip(cuts, cuts[1:]):
            if b - a < 1e-3:
                continue
            m = (a + b) / 2
            plus = next((s for s in segs if s[0] <= m <= s[1] and s[4] > 0), None)    # 선의 + 쪽(남/동)에 있는 방
            minus = next((s for s in segs if s[0] <= m <= s[1] and s[4] < 0), None)   # - 쪽(북/서) 방
            if not plus and not minus:
                continue
            # 문 구멍 빼기
            pieces = [(a, b)]
            for (dx0, dx1, dz0, dz1) in doors:
                if axis == 'z' and dz0 - 0.01 <= c <= dz1 + 0.01:
                    lo, hi = dx0, dx1
                elif axis == 'x' and dx0 - 0.01 <= c <= dx1 + 0.01:
                    lo, hi = dz0, dz1
                else:
                    continue
                nxt = []
                for (p, q) in pieces:
                    if hi <= p or lo >= q:
                        nxt.append((p, q))
                        continue
                    if lo > p:
                        nxt.append((p, lo))
                    if hi < q:
                        nxt.append((hi, q))
                pieces = nxt
            for (p, q) in pieces:
                if q - p > 0.05:
                    walls.append((axis, c, p, q, plus, minus))
    # 벽 조각 만들기: 면 = 양쪽 방 색, 그래픽은 해당 면으로
    for (axis, c, p, q, plus, minus) in walls:
        L = q - p
        hh = [rooms[s_[2]].get('h', h) for s_ in (plus, minus) if s_]
        wh = max(hh) if hh else h
        mid = (p + q) / 2
        if axis == 'z':
            base = T(mid, 0, c, 0)            # 로컬 +z = 남쪽 (plus 방 쪽)
        else:
            base = T(c, 0, mid, PI / 2)        # 로컬 +z = 동쪽 (plus 방 쪽); 로컬 +x = -z(북)

        def mat_of(s):
            if not s:
                return default_mat
            r = rooms[s[2]]
            return r.get('sides', {}).get(s[3], r['color'])

        def decs(s, flip):
            out = []
            if not s:
                return out
            for (rm, sd, u, y, w, hh, mt) in decals:
                if rm != s[2] or sd != s[3]:
                    continue
                x0, x1, z0, z1 = rooms[rm]['rect']
                g = (x0 if axis == 'z' else z0) + u        # 선 위 좌표
                if g + w / 2 <= p or g - w / 2 >= q:
                    continue
                lu = g - mid                                # 조각 가운데 기준
                # 면을 바라볼 때 오른쪽이 +x 가 되도록
                if axis == 'z':
                    cx = lu if not flip else -lu
                else:
                    cx = -lu if not flip else lu
                out.append((cx, y, w, hh, mt))
            return out

        # plus 쪽 면 (로컬 +z 를 봄): 이 면을 보는 사람의 오른쪽 = 로컬 +x
        _face(asm, base @ T(0, 0, t / 2), L, wh, mat_of(plus), decs(plus, False), tile)
        _face(asm, base @ T(0, 0, -t / 2, PI), L, wh, mat_of(minus), decs(minus, True), tile)
        top = mat_of(plus) if plus else mat_of(minus)
        asm.add(plane(L, t), base @ T(0, wh, 0, 0, -PI / 2), default_mat, tile)
        for s in (-1, 1):
            asm.add(plane(t, wh), base @ T(s * L / 2, wh / 2, 0, s * PI / 2), top, tile)
    return walls
