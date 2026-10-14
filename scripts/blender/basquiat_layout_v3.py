"""바스키아 전시장 **벽체 설계 v3** — 닫힌 방 17개 → 벽 선분 그래프로 다시 짠다.

  python3 scripts/blender/basquiat_layout_v3.py

v2 의 구조적 결함 세 가지를 고친다.

1. **방이 섬처럼 떠 있다.** v2 의 17개 사각형을 합치면 797㎡, 홀은 1220㎡.
   남는 423㎡ 중 **137㎡ 가 홀 한가운데에 사방이 막힌 빈 공간**이다
   (x -12.4..5.4, z -10.2..-1.6). 전시장 한복판에 그런 공간은 없다.
   → 그 자리는 **백오브하우스(서비스 코어)** 다. 근거: 카툰 구역 구석의
   "흰 커튼이 달린 폭 2.8 x 3.3m 서비스 출입구 + 위쪽 녹색 비상구 표시"
   (`05cartoons_room_wide_2.jpg`) 가 바로 이 블록으로 들어가는 문이다.
   네 면(푸이 복도 남벽, 스튜디오 서벽, 워즈/카툰 북벽, 레드/화이트 동벽)이
   모두 전시 벽이라 코어가 공짜로 생긴다.

2. **방들이 서로 0.2~0.6m 씩 어긋나 있다.** 공유해야 할 벽면이 두 장이 되어
   죽은 틈이 생긴다. → 모든 인접 모서리를 한 평면으로 맞췄다.

3. **가벽이 천장까지 닿아 있다.** 실제는 3.0m(특수벽 4.4~4.8m)에서 끊기고
   그 위로 DDP 소핏이 보인다 (`layout_v2.md` §0.2, 근거사진 4장).
   → 벽은 선분마다 자기 높이를 갖고, 천장은 구역별 별도 평면이다.

출력 `layout_v3.json`:
  zones    — 구역(바닥 영역 + 면 색). 'service': true 면 비공개 코어.
  walls    — 벽 선분 [{id, a, b, h, t, L, R, top, zl, zr, ev, conf}]
             a→b 로 걸어갈 때 왼쪽 면 재질이 L, 오른쪽이 R. zl/zr 은 그 면이
             속한 구역. 공유 벽은 **한 장만** 나온다.
  openings — 벽 선분 위의 구멍 [{wall, u0, u1, y0, y1, kind}]
  ceilings — 구역별 천장 평면
"""
import json
import math
import sys

ROOT = '/Users/hare/Documents/큐비크스홈페이지'
REFS = f'{ROOT}/assets-src/refs/basquiat'
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{REFS}/layout_v3.json'

V2 = json.load(open(f'{REFS}/layout_v2.json', encoding='utf-8'))
SHELL = json.load(open(f'{REFS}/hall1_outline_v2.json', encoding='utf-8'))['outline']

T = 0.20                      # 가벽 두께 (layout_v2 globals.wall_thickness)
H_STD = 3.0                   # 표준 가벽
SOFFIT = 4.6                  # 갤러리 위로 보이는 DDP 소핏

# ─────────────────────────────────────────────────────────────────────────────
# 1. 구역 — 모든 인접 모서리를 한 평면에 맞춘 v3 사각형
#    'why' 는 그 치수가 어디서 왔는지. fit = 사진에 안 나와서 타일링으로 푼 값.
# ─────────────────────────────────────────────────────────────────────────────
ZONES = {
    # id            x0      x1      z0      z1     h     floor         why
    'preface':      (12.2,  18.0, -10.2,  -2.0, 3.5, 'carpetRed',
                     '벽길이 8.2 = 초상화 3.5 + 표제 3.0 + 창문박스 1.15 (high); 깊이 fit'),
    'studioRed':    (5.4,   12.2, -10.2,  -2.0, 3.0, 'carpetRed',
                     '둘 다 fit — 사진에 치수 단서 없음'),
    'studioGrey':   (1.8,   12.2, -16.2, -10.2, 3.0, 'carpetGrey',
                     'n 벽 10.4 = Train,Car,Ship + 플린스 3.0 + Number 4 (high); 깊이 fit'),
    'phooey':       (-11.2,  1.8, -15.2, -10.2, 3.0, 'carpetGrey',
                     's 벽 13.0 = 섹션판+Phooey 3.55+니치 3.5 (high); n 은 홀 외벽(가벽 없음)'),
    'boh':          (-11.2,  5.4, -10.2,  -2.0, 3.0, 'epoxy',
                     '서비스 코어 — 카툰 구석 커튼 서비스문이 이리로 들어간다'),
    'red':          (-19.4, -11.2, -12.6,  -4.4, 3.05, 'carpetGrey',
                     'w 벽 8.2 = A-One 1.6 + 공백 2.5 + 잉크 7점 4.0 (high); 폭 fit'),
    'warriorsWhite': (-20.0, -11.2, -4.4,   3.4, 3.0, 'carpetGrey',
                      's 벽 8.8 = 검은 리세스 개구부 7.0 + 양쪽 단 (high); 깊이 fit'),
    'whiteCorr':    (-15.4, -11.2,   3.4,   9.6, 3.03, 'carpetGrey',
                     'e 벽 6.2 = Joy 1.725 + 2.08 + Untitled 1.727 + 여백 (high); 폭 4.2 (high)'),
    'headsBlack':   (-14.6, -11.8,   9.6,  11.6, 3.2, 'carpetGrey',
                     '개구부 2.6~3.0 x 깊이 1.5~2.0 리세스 (high)'),
    'cartoons':     (-11.2,  -3.0,  -2.0,   6.0, 3.0, 'carpetGrey',
                     '8.0 x 8.2 — 이젤 플린스 + 봄베로 가벽 + 3면 작품 (medium)'),
    'words':        (-3.0,  12.2,  -2.0,   3.6, 3.0, 'carpetGrey',
                     's 벽 15.2 = 작품 10점 0.6~0.9m 간격 (high); 깊이 fit'),
    'msec':         (12.2,  18.8,  -2.0,   3.6, 3.0, 'carpetGrey',
                     '메이소닉 박스 개구부 5.5 + 양쪽 (high); 깊이 fit'),
    'temple':       (7.8,   17.2,   3.6,  12.6, 3.2, 'floorPale',
                     'L자 — 노트 150장 4단 그리드가 안쪽 모서리 3개 이상을 돌려면 '
                     '랩된 평면이어야 한다 (high). 실치수는 fit (추정폭 8x11~12x16)'),
    'templeW':      (-3.0,   7.8,   3.6,   8.6, 3.2, 'floorPale',
                     'temple 의 서쪽 팔 — 같은 방'),
    'drawing':      (-3.0,   7.8,   8.6,  12.6, 4.6, 'carpetGrey',
                     'n 벽 10.6 = 반구대 베이 8.8 + 출입 1.8 (high); 폭 4.0 (high)'),
    'anatomy':      (-9.6,  -3.0,   6.0,  12.6, 4.5, 'carpetGrey',
                     'w 벽 6.6 = 흰 플랫폼 6.5 (high); 폭 fit'),
    'hidden':       (-9.6,  -5.6,   9.4,  12.6, 3.0, 'carpetGrey',
                     'Emblem 2.489 가 한쪽 긴 벽 (high). anatomy 안에 박혀 있다'),
    'asia':         (-5.0,   2.2,  12.6,  16.2, 3.2, 'carpetRed',
                     '프로젝션 3.6~4.2 + 섹션문구 (high); "너무나도 협소" 라 깊이 3.2'),
    'epilogue':     (2.2,   10.8,  12.6,  18.0, 3.2, 'carpetRed',
                     's 벽 8.6 = EXU 핀 6.5 + 출구커튼 3.4 겹침 (high); 깊이 fit'),
}
SERVICE = {'boh'}
MERGED = {'templeW': 'temple'}          # 같은 방의 두 번째 사각형

# 벽을 세우지 않는 변 (홀 외벽에 면하거나 같은 방끼리 맞닿은 변)
OPEN = {
    ('phooey', 'n'),                     # 홀 외벽 — 펀갤러리 사진패널은 독립 설치물
    ('temple', 'w'), ('templeW', 'e'),   # L 자 내부
    ('hidden', 'w'),                     # anatomy 서벽과 같은 선 — anatomy 가 갖는다
}

# ─────────────────────────────────────────────────────────────────────────────
# 1b. 개구부 — (구역, 면, u0, u1, 높이, 종류, 신뢰도)
#     u 는 layout_v2 와 같은 규약: 위에서 봤을 때 시계방향.
#     n = x0→x1, e = z0→z1, s = x1→x0, w = z1→z0
# ─────────────────────────────────────────────────────────────────────────────
DOORS = [
    ('preface', 'e', 2.2, 4.2, 2.3, '자동 유리문 (검은 파사드 안)', 'medium'),
    ('preface', 'w', 6.8, 8.2, 3.5, '프리페이스 벽이 창문 작품에서 1m 더 가다 끊긴다 — 돌아가면 뒷면', 'high'),
    ('studioRed', 'n', 3.6, 6.1, 3.0, '열린 틈; 이 너머로 Number 4 가 보인다', 'high'),
    ('studioGrey', 'w', 0.4, 4.8, 3.0, '볼플레이어 검은 가벽이 절반쯤 가린다', 'high'),
    ('phooey', 'w', 0.2, 2.3, 3.0, '복도 입구 — 20m 앞 A-One 빨간 벽이 정면으로 보인다', 'high'),
    ('red', 's', 1.2, 5.4, 3.05, '빨간 벽이 끝나고 백남준 로봇이 선 흰 구역', 'high'),
    ('warriorsWhite', 's', 0.10, 1.90, 3.0,
     '검은 상자 동쪽 귀와 Blue Skies 흰 가벽 사이 좁은 슬롯. **미해결** — '
     '사진에서 상자 개구부가 7.0m 인데 벽 전체가 8.8m 라 3m 짜리 복도 입구가 들어갈 자리가 없다', 'low'),
    ('whiteCorr', 's', 0.6, 3.4, 3.2, '검은 벽감 — 막다른 곳, 보고 되돌아 나온다', 'high'),
    ('whiteCorr', 'e', 0.2, 2.5, 3.0, '카툰으로', 'low'),
    ('cartoons', 'e', 2.4, 5.4, 3.0, '넓은 개구부', 'medium'),
    ('cartoons', 'n', 5.0, 7.8, 3.3, '**흰 커튼 서비스 출입구 + 위에 녹색 비상구 등** — 백오브하우스로', 'high'),
    ('words', 'e', 1.0, 4.4, 3.0, '조명이 떨어진다; 비스듬한 크림색 문구 벽을 지나', 'high'),
    ('msec', 's', 2.0, 5.5, 3.5, '검은 플리츠 커튼, 바닥까지, 가운데 트임, 흰 문설주', 'high'),
    ('templeW', 's', 0.2, 2.2, 3.2, '반구대 베이가 서쪽 8.8m 를 쓰므로 개구부는 동쪽 끝', 'medium'),
    ('drawing', 'w', 0.6, 3.4, 3.3, '복도를 빠져나와 돌면 연보 벽이 정면', 'medium'),
    ('hidden', 'e', 1.0, 2.1, 2.4, 'anatomy 검은 뒷벽에 뚫린 사각 구멍', 'high'),
    ('anatomy', 's', 0.2, 1.8, 3.2, '인터뷰 프로젝션이 있는 비좁은 접합부', 'high'),
    ('asia', 'e', 0.4, 3.0, 3.2, '열림', 'low'),
    ('epilogue', 's', 0.4, 3.8, 3.3, '검은 플리츠 출구 커튼 — EXU 벽을 마주봤을 때 왼쪽 끝', 'high'),
]

# 면 색 보정 (v2 walls 를 그대로 쓰되 §4 에서 틀렸다고 한 것만)
FACE_FIX = {
    ('temple', '*'): 'black',            # §7.1 navy → black
    ('templeW', '*'): 'black',
    ('studioGrey', '*'): 'white',
    ('boh', '*'): 'white',
}

# 벽 높이는 구역이 아니라 **면마다** 다르다. 여기 없는 면은 ZONES 의 h.
#   (구역, 면): (높이, 근거)
FACE_H = {
    ('preface', 'w'): (3.5, '프리페이스 초상화 벽 — 초상화가 전고 3.5 (high)'),
    ('drawing', 'n'): (4.8, '반구대 탁본 3.90m + 플린스 0.4 → 전시 통틀어 가장 높은 벽 (high)'),
    ('drawing', 's'): (3.3, '복도 어두운 천장 + 검은 소핏 밴드 밑면 3.3 (high)'),
    ('drawing', 'w'): (3.3, '같음'),
    ('drawing', 'e'): (3.3, '같음'),
    ('anatomy', 'w'): (4.6, 'Flesh and Spirit 3.683m, 중심 2.40m → 4.5~4.6 (high)'),
    ('anatomy', 'n'): (3.6, '맞은편 흰 벽 3.0~3.6 (high)'),
    ('anatomy', 'e'): (3.6, '같음'),
    ('anatomy', 's'): (3.6, 'Hidden Signs 로 들어가는 검은 뒷벽'),
    ('epilogue', 's'): (3.0, 'EXU 핀 2.9~3.3 — 양 옆 벽보다 눈에 띄게 낮다 (high)'),
    ('warriorsWhite', 's'): (3.6, '검은 상자 개구부 3.2 + 그 위 검은 헤더 0.4 (high)'),
    ('phooey', 's'): (3.0, '네이비 벽 3.0 + 그 위 네이비 벌크헤드는 별도 (medium)'),
}


def face_h(zid, side):
    return FACE_H.get((zid, side), (ZONES[zid][4], ''))[0]


# ─────────────────────────────────────────────────────────────────────────────
# 2. 선분 그래프 유도 — 같은 평면에 놓인 변들을 모아 한 장의 벽으로
# ─────────────────────────────────────────────────────────────────────────────
SIDES = {'n': ('z', 0, 2, +1), 's': ('z', 1, 2, -1), 'w': ('x', 0, 0, +1), 'e': ('x', 1, 0, -1)}
#   side -> (평면 축, rect 안의 좌표 인덱스(z0/z1 or x0/x1), 구간 축 인덱스, 방이 있는 쪽 부호)


def rect(zid):
    return ZONES[zid][:4]


def face_mat(zid, side):
    base = MERGED.get(zid, zid)
    if (zid, '*') in FACE_FIX:
        return FACE_FIX[(zid, '*')]
    for z in V2['zones']:
        if z['id'] == base:
            return z['walls'].get(side, 'white')
    return 'white'


def face_axis(zid, side):
    """(평면축, 평면좌표, 구간시작, 구간끝) — u 0 지점과 진행 방향까지"""
    x0, x1, z0, z1 = rect(zid)
    return {'n': ('z', z0, x0, +1), 's': ('z', z1, x1, -1),
            'e': ('x', x1, z0, +1), 'w': ('x', x0, z1, -1)}[side]


def u_world(zid, side, u):
    _axis, _c, origin, d = face_axis(zid, side)
    return origin + d * u


def openings_world():
    out = []
    for (zid, side, u0, u1, h, kind, conf) in DOORS:
        axis, c, _o, _d = face_axis(zid, side)
        a, b = sorted((u_world(zid, side, u0), u_world(zid, side, u1)))
        out.append({'zone': zid, 'face': side, 'axis': axis, 'c': round(c, 3),
                    'a': round(a, 3), 'b': round(b, 3), 'h': h, 'kind': kind, 'conf': conf})
    return out


def derive():
    lines = {}
    for zid in ZONES:
        x0, x1, z0, z1 = rect(zid)
        for side in ('n', 's', 'w', 'e'):
            if (zid, side) in OPEN:
                continue
            axis = 'z' if side in 'ns' else 'x'
            c = {'n': z0, 's': z1, 'w': x0, 'e': x1}[side]
            a, b = (x0, x1) if axis == 'z' else (z0, z1)
            sgn = +1 if side in 'ns' else +1          # plus = 평면의 + 쪽에 방이 있다
            sgn = +1 if side in ('n', 'w') else -1
            lines.setdefault((axis, round(c, 3)), []).append((a, b, zid, side, sgn))

    walls = []
    for (axis, c), segs in sorted(lines.items()):
        cuts = sorted({v for s in segs for v in (s[0], s[1])})
        for a, b in zip(cuts, cuts[1:]):
            if b - a < 0.05:
                continue
            m = (a + b) / 2
            plus = next((s for s in segs if s[0] <= m <= s[1] and s[4] > 0), None)   # +쪽(남/동) 방
            minus = next((s for s in segs if s[0] <= m <= s[1] and s[4] < 0), None)  # -쪽(북/서) 방
            if not plus and not minus:
                continue
            h = max(face_h(s[2], s[3]) for s in (plus, minus) if s)
            zp = plus[2] if plus else None
            zm = minus[2] if minus else None
            walls.append({
                'axis': axis, 'c': round(c, 3), 'a': round(a, 3), 'b': round(b, 3),
                'h': round(h, 3), 't': T,
                'plus': zp, 'plus_face': plus[3] if plus else None,
                'minus': zm, 'minus_face': minus[3] if minus else None,
                'mat_plus': face_mat(zp, plus[3]) if plus else 'white',
                'mat_minus': face_mat(zm, minus[3]) if minus else 'white',
            })
    for i, w in enumerate(walls):
        w['id'] = f'W{i:03d}'
        if w['axis'] == 'z':
            w['p'], w['q'] = [w['a'], w['c']], [w['b'], w['c']]
        else:
            w['p'], w['q'] = [w['c'], w['a']], [w['c'], w['b']]
        w['len'] = round(w['b'] - w['a'], 3)
    return walls


# ─────────────────────────────────────────────────────────────────────────────
# 3. 검증
# ─────────────────────────────────────────────────────────────────────────────
def poly_area(pts):
    s = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


def inside(px, pz, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % n]
        if (z0 > pz) != (z1 > pz) and px < (x1 - x0) * (pz - z0) / (z1 - z0) + x0:
            c = not c
    return c


def check(walls):
    bad = []
    for zid in ZONES:
        x0, x1, z0, z1 = rect(zid)
        free = set()
        for side in ('n', 's', 'w', 'e'):
            if (zid, side) in OPEN:
                free |= {{'n': ((x0, z0), (x1, z0)), 's': ((x0, z1), (x1, z1)),
                          'w': ((x0, z0), (x0, z1)), 'e': ((x1, z0), (x1, z1))}[side][i]
                         for i in (0, 1)}
        for (px, pz) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
            if (px, pz) in free:
                continue
            if not inside(px, pz, SHELL):
                bad.append(f'{zid} 모서리 ({px}, {pz}) 가 홀 밖')
    # 겹침
    ids = [z for z in ZONES]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if ids[j] == 'hidden' and ids[i] == 'anatomy':
                continue
            if ids[i] == 'hidden' and ids[j] == 'anatomy':
                continue
            ax0, ax1, az0, az1 = rect(ids[i])
            bx0, bx1, bz0, bz1 = rect(ids[j])
            ox = min(ax1, bx1) - max(ax0, bx0)
            oz = min(az1, bz1) - max(az0, bz0)
            if ox > 0.01 and oz > 0.01:
                bad.append(f'{ids[i]} ∩ {ids[j]} = {ox:.2f} x {oz:.2f}')
    # 동선 인접
    route = [r for r in V2['route'] if r in ZONES]
    seq = [r for i, r in enumerate(route) if i == 0 or r != route[i - 1]]
    for p, q in zip(seq, seq[1:]):
        ax0, ax1, az0, az1 = rect(p)
        bx0, bx1, bz0, bz1 = rect(q)
        shx = abs(ax1 - bx0) < 0.3 or abs(ax0 - bx1) < 0.3
        shz = abs(az1 - bz0) < 0.3 or abs(az0 - bz1) < 0.3
        ovx = min(ax1, bx1) - max(ax0, bx0) > 0.5
        ovz = min(az1, bz1) - max(az0, bz0) > 0.5
        nested = (ax0 <= bx0 and ax1 >= bx1 and az0 <= bz0 and az1 >= bz1) or \
                 (bx0 <= ax0 and bx1 >= ax1 and bz0 <= az0 and bz1 >= az1)
        if not ((shx and ovz) or (shz and ovx) or nested):
            bad.append(f'동선 {p} → {q} 가 벽을 공유하지 않는다')
    return bad


# v3 에서 구역 사각형이 움직인 만큼 독립 설치물도 따라 옮긴다 (벽 속에 박히지 않도록)
FS_FIX = {
    ('studioGrey', 'plinth'): {'centre': [7.0, -15.4]},      # n 벽이 -16.4 → -16.2
    ('studioGrey', 'partition'): {'a': [2.6, -14.6], 'b': [2.6, -11.1]},
    ('phooey', 'panel'): {'a': [-3.5, -14.2], 'b': [1.3, -14.2]},   # n 쪽은 홀 외벽, 그 앞에 독립 설치
    ('warriorsWhite', 'sculpture'): {'centre': [-15.5, -3.8]},      # ww 의 n 벽이 -5.0 → -4.4
}

# 개구부가 잇는 두 구역 (v2 doors 의 frm/to 를 그대로)
FRM = {(d['zone'], d['face']): d['frm'] for d in V2['doors']}
TO = {(d['zone'], d['face']): d['to'] for d in V2['doors']}
FRM[('templeW', 's')] = 'temple'
TO[('templeW', 's')] = 'drawing'
FRM[('hidden', 'e')] = 'anatomy'
TO[('hidden', 'e')] = 'hidden'
FRM[('cartoons', 'n')] = '_service'
TO[('cartoons', 'n')] = 'boh'

# 검은 상자가 벽 중앙이 아니라 서쪽으로 치우치므로 그 안의 작품도 따라간다
WORK_FIX = {('warriorsWhite', 'black_figure'): 5.30}

V2RECT = {z['id']: z['rect'] for z in V2['zones']}
# v2 구역 → v3 구역 (L 자로 쪼갠 temple, 이름이 그대로인 나머지)
ZMAP = {z: z for z in ZONES}


def face_len(r, side):
    x0, x1, z0, z1 = r
    return (x1 - x0) if side in 'ns' else (z1 - z0)


def remap_u(zid, side, u):
    """v2 면 길이 대비 비율을 유지한 채 v3 면 길이로 옮긴다 (가운데는 가운데로)"""
    src = V2RECT.get(MERGED.get(zid, zid))
    if not src:
        return round(u, 3)
    a, b = face_len(src, side), face_len(rect(zid), side)
    return round(u * b / a, 3) if a > 0.01 else round(u, 3)


def attach(walls, ops):
    """개구부를 벽 선분에 붙이고, 벽이 없는 자리에 뚫린 건 잡아낸다"""
    bad = []
    for o in ops:
        hit = [w for w in walls if w['axis'] == o['axis'] and abs(w['c'] - o['c']) < 0.01
               and min(w['b'], o['b']) - max(w['a'], o['a']) > 0.05]
        o['walls'] = [w['id'] for w in hit]
        cov = sum(min(w['b'], o['b']) - max(w['a'], o['a']) for w in hit)
        if cov < (o['b'] - o['a']) - 0.05:
            bad.append(f"개구부 {o['zone']}/{o['face']} ({o['a']:.2f}..{o['b']:.2f}) 중 "
                       f"{o['b'] - o['a'] - cov:.2f}m 가 벽 바깥")
    return bad


def main():
    walls = derive()
    ops = openings_world()
    bad = check(walls) + attach(walls, ops)
    works = []
    for w in V2['works']:
        zid = w['zone']
        if zid not in ZONES:
            bad.append(f"작품 {w['slug']} 의 구역 {zid} 이 v3 에 없다")
            continue
        u_ = WORK_FIX.get((zid, w['slug']), remap_u(zid, w['face'], w['u']))
        works.append(dict(w, u=u_))
    hall = poly_area(SHELL)
    area = {z: (rect(z)[1] - rect(z)[0]) * (rect(z)[3] - rect(z)[2]) for z in ZONES}
    pub = sum(a for z, a in area.items() if z not in SERVICE) - area['hidden']
    out = {
        '_about': 'Basquiat at DDP — 벽체 설계 v3. 닫힌 방 대신 벽 선분 그래프. '
                  'layout_v2.json 의 §0.1/§0.2 (가벽 3.0m, 천장에 안 닿음) 를 구조에 반영했다.',
        '_frame': V2['_frame'],
        '_u_convention': V2['_u_convention'],
        'palette': V2['palette'],
        'globals': dict(V2['globals'], wall_thickness=T, visible_soffit_h=SOFFIT),
        'route': V2['route'],
        'shell': SHELL,
        'zones': [{
            'id': z, 'rect': list(rect(z)), 'wall_h': ZONES[z][4], 'floor': ZONES[z][5],
            'size_m': [round(rect(z)[1] - rect(z)[0], 2), round(rect(z)[3] - rect(z)[2], 2)],
            'walls': {sd: face_mat(z, sd) for sd in ('n', 'e', 's', 'w')},
            'open': sorted(sd for sd in ('n', 'e', 's', 'w') if (z, sd) in OPEN),
            'service': z in SERVICE, 'merged_into': MERGED.get(z),
            'area_m2': round(area[z], 1), 'why': ZONES[z][6],
            'ceiling': next((d['ceiling'] for d in V2['zones'] if d['id'] == MERGED.get(z, z)),
                            {'type': 'ddp_soffit', 'h': SOFFIT}),
        } for z in ZONES],
        'walls': [{
            'id': w['id'], 'p': w['p'], 'q': w['q'], 'axis': w['axis'], 'c': w['c'],
            'a': w['a'], 'b': w['b'], 'len': w['len'], 'h': w['h'], 't': w['t'],
            'plus': w['plus'], 'plus_face': w['plus_face'], 'mat_plus': w['mat_plus'],
            'minus': w['minus'], 'minus_face': w['minus_face'], 'mat_minus': w['mat_minus'],
        } for w in walls],
        'openings': ops,
        'doors': [{'zone': z, 'face': s, 'u0': u0, 'u1': u1, 'h': h, 'kind': k, 'conf': c,
                   'frm': FRM.get((z, s), z), 'to': TO.get((z, s), '')}
                  for (z, s, u0, u1, h, k, c) in DOORS],
        'works': works,
        'freestanding': [dict(f, **FS_FIX.get((f['zone'], f['kind']), {})) for f in V2['freestanding']],
        'check': {
            'hall_m2': round(hall, 1),
            'public_m2': round(pub, 1),
            'service_m2': round(sum(area[z] for z in SERVICE), 1),
            'wall_count': len(walls),
            'wall_run_m': round(sum(w['len'] for w in walls), 1),
            'problems': bad,
        },
    }
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'wrote {OUT}')
    print(f"  홀 {hall:.0f}㎡ / 공개구역 {pub:.0f}㎡ / 서비스코어 {sum(area[z] for z in SERVICE):.0f}㎡")
    print(f"  벽 {len(walls)}장, 총연장 {sum(w['len'] for w in walls):.1f}m")
    if bad:
        print('  ✗ 문제 %d건' % len(bad))
        for b in bad:
            print('    -', b)
    else:
        print('  ✓ 홀 안쪽 / 겹침 없음 / 동선 전구간 벽 공유')


if __name__ == '__main__':
    main()
