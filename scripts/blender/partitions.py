"""벽 선분 그래프 → 가벽 지오메트리 (rooms.py 를 대체).

rooms.py 는 **닫힌 직사각형 방**을 받아 사방에 벽을 세웠다. 실제 DDP 전시1관은
무주 공간 하나에 가벽이 서 있는 구조라서, 그 모델로는 방이 섬처럼 떠 있고
가벽이 천장까지 닿는다 (layout_v2.md §0.1 / §0.2 가 둘 다 틀렸다고 지적한 것).

여기서는 `layout_v3.json` 의 `walls` (선분 하나 = 가벽 한 장, 공유 벽은 한 장)와
`openings` (선분 위 구멍)을 그대로 세운다. 각 선분이 **자기 높이**를 갖기 때문에
벽 위로 홀 천장이 그대로 보인다.

  build(asm, lay, decals, matmap, tile)
    lay     — layout_v3.json
    decals  — [(zone, face, u, y, w, h, gmat)] (u 는 rooms.py 규약 = x0/z0 부터)
    matmap  — 팔레트 키 → Blender 머티리얼
"""
from lib import PI, T, plane
from gallery import _face


def wall_face(room, side, u, rooms, t):
    """방 안쪽에서 본 벽면 위 한 점의 좌표계 (원점 = 벽면 위 바닥, +z = 방 안쪽)
    rooms.py 와 똑같다 — 작품 배치 코드가 그대로 돌아가도록."""
    x0, x1, z0, z1 = rooms[room]['rect']
    if side == 'n':
        return T(x0 + u, 0, z0 + t / 2, 0)
    if side == 's':
        return T(x0 + u, 0, z1 - t / 2, PI)
    if side == 'w':
        return T(x0 + t / 2, 0, z0 + u, PI / 2)
    return T(x1 - t / 2, 0, z0 + u, -PI / 2)


def _subtract(span, holes):
    """[a, b) 에서 holes 구간들을 뺀 나머지"""
    out = [span]
    for (lo, hi) in holes:
        nxt = []
        for (p, q) in out:
            if hi <= p + 1e-6 or lo >= q - 1e-6:
                nxt.append((p, q))
                continue
            if lo > p:
                nxt.append((p, lo))
            if hi < q:
                nxt.append((hi, q))
        out = nxt
    return [(p, q) for (p, q) in out if q - p > 0.03]


def build(asm, lay, decals, matmap, tile=2.0):
    walls = lay['walls']
    ops = lay['openings']
    rects = {z['id']: z['rect'] for z in lay['zones']}

    # 같은 선 위에서 이어지는 조각끼리는 마구리를 만들지 않는다 (같은 면이 겹쳐 z-fighting)
    ends = {}
    for w in walls:
        for v in (w['a'], w['b']):
            k = (w['axis'], round(w['c'], 3), round(v, 3))
            ends[k] = ends.get(k, 0) + 1

    built = 0
    for w in walls:
        axis, c, h, t = w['axis'], w['c'], w['h'], w['t']
        holes = [(max(o['a'], w['a']), min(o['b'], w['b'])) for o in ops
                 if o['axis'] == axis and abs(o['c'] - c) < 0.01
                 and min(o['b'], w['b']) - max(o['a'], w['a']) > 0.03]
        # (구간, 바닥높이, 꼭대기높이)
        parts = [(p, q, 0.0, h) for (p, q) in _subtract((w['a'], w['b']), holes)]
        for o in ops:                                    # 개구부 위 인방
            if o['axis'] != axis or abs(o['c'] - c) > 0.01:
                continue
            lo, hi = max(o['a'], w['a']), min(o['b'], w['b'])
            if hi - lo > 0.03 and o['h'] < h - 0.03:
                parts.append((lo, hi, o['h'], h))

        for (p, q, y0, y1) in parts:
            L, hh = q - p, y1 - y0
            mid = (p + q) / 2
            base = (T(mid, y0, c, 0) if axis == 'z' else T(c, y0, mid, PI / 2))

            def decs(zid, fc, flip):
                out = []
                if not zid or zid not in rects:
                    return out
                x0, _x1, z0, _z1 = rects[zid]
                for (rm, sd, u, y, dw, dh, mt) in decals:
                    if rm != zid or sd != fc:
                        continue
                    g = (x0 if axis == 'z' else z0) + u
                    if g + dw / 2 <= p or g - dw / 2 >= q:
                        continue
                    if y + dh / 2 <= y0 or y - dh / 2 >= y1:
                        continue
                    lu = g - mid
                    cx = (lu if not flip else -lu) if axis == 'z' else (-lu if not flip else lu)
                    out.append((cx, y - y0, dw, dh, mt))
                return out

            mp = matmap.get(w['mat_plus'], matmap['white'])
            mm = matmap.get(w['mat_minus'], matmap['white'])
            _face(asm, base @ T(0, 0, t / 2), L, hh, mp, decs(w['plus'], w['plus_face'], False), tile)
            _face(asm, base @ T(0, 0, -t / 2, PI), L, hh, mm, decs(w['minus'], w['minus_face'], True), tile)
            if y1 >= h - 1e-6:                            # 벽 꼭대기 (여기서 끊기고 위는 빈 공간)
                asm.add(plane(L, t), base @ T(0, hh, 0, 0, -PI / 2), mp, tile)
            if y0 > 1e-6:                                 # 인방 밑면
                asm.add(plane(L, t), base @ T(0, 0, 0, 0, PI / 2), mm, tile)
            for s in (-1, 1):
                v = q if s > 0 else p
                # 벽 끝이면서 다른 벽이 이어지지 않는 곳만 마구리를 만든다.
                # 개구부 때문에 생긴 끝(= 문설주)은 언제나 만든다.
                jamb = any(abs(v - x) < 1e-6 for hs in holes for x in hs)
                if not jamb and ends.get((axis, round(c, 3), round(v, 3)), 0) > 1:
                    continue
                asm.add(plane(t, hh), base @ T(s * L / 2, hh / 2, 0, s * PI / 2), mp, tile)
            built += 1
    return built
