"""바스키아 전시장 **벽체 설계 v4** — a4b4 워크스루 179장을 보행 순서대로 읽어 다시 그린다.

  python3 scripts/blender/basquiat_layout_v4.py

── 왜 다시 짰나 (원본 사진에서 확인한 것) ───────────────────────────────────

1. **바깥 벽이 곡선이다.** Words and Signs(`v3_a4b4_78406_006`), 콜라주 벽
   (`..._78405_036`), Asia·Epilogue(`..._78406_075`) 가 전부 길게 휘어 있다.
   전시1관은 중심에서 반경 15.9~23.0m(평균 20.7)인 거의 원형 홀이라 외곽 구역
   벽이 껍데기를 따라간다. v3 는 전부 직각 사각형이었고, 그게 "공간 구성이
   하나도 안 맞는다"의 가장 큰 원인이다.

2. **"방"이 아니라 열린 홀에 선 독립 가벽이다.** Blue Skies(4.1 x 3.0),
   Bombero(4.24 x 3.15), 볼플레이어, 펀갤러리 패널이 전부 사방이 트인 섬이고
   사진에서 벽 끝 모서리와 그 너머가 그대로 보인다.

3. **천장이 구역마다 다르다.** Words 는 사람 머리 바로 위(~2.9m)까지 내려온
   챠콜 데크, Temple 은 검은 벽 위로 크림색 DDP 소핏이 ~4.9m.

── 유지한 것과 바꾼 것 ──────────────────────────────────────────────────────

배치 **위상**(어느 구역이 어느 구역과 붙는가)은 유지한다. 동선 순서와
`layout_v2.md` §2 의 시선 관계를 전부 만족하는 구성이고, 순수한 동심 링으로
다시 짜 보면 cartoons→words→msec 인접이 깨진다.

**기하**는 전부 다시 잡았다:
  - 껍데기에 닿는 변을 밖으로 늘린 뒤 홀 윤곽으로 잘라 **곡선 벽**으로 만든다
  - 벽 높이를 면마다 사진에서 측정한 값으로
  - 독립 가벽(섬) 치수를 사진에서 측정한 값으로
"""
import json
import math
import sys

from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

ROOT = '/Users/hare/Documents/큐비크스홈페이지'
REFS = f'{ROOT}/assets-src/refs/basquiat'
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{REFS}/layout_v4.json'

V2 = json.load(open(f'{REFS}/layout_v2.json', encoding='utf-8'))
SHELL = json.load(open(f'{REFS}/hall1_outline_v2.json', encoding='utf-8'))['outline']
HALL = Polygon(SHELL)
INNER = HALL.buffer(-0.30)          # 껍데기에서 30cm 띄운 선 = 전시 외벽이 설 자리
T = 0.20
GROW = 4.5                          # 껍데기 쪽 변을 이만큼 밖으로 늘린 뒤 윤곽으로 자른다

# ─────────────────────────────────────────────────────────────────────────────
# 1. 구역 — (x0, x1, z0, z1, 바닥, 바깥으로 늘릴 변들, 근거)
#    'grow' 에 든 변은 밖으로 늘린 뒤 홀 윤곽으로 잘린다 → 그 변이 곡선이 된다.
# ─────────────────────────────────────────────────────────────────────────────
Z = {
    'preface':      (12.2, 18.0, -10.2,  -2.0, 'carpetRed', 'e',
                     '초상화 3.5 + 표제 3.0 + 창문박스 1.15 = 벽 8.2m (78405_005)'),
    'studioRed':    (5.4,  12.2, -10.2,  -2.0, 'carpetRed', '',
                     'Car Crash 가 걸린 맞은편 벽. 깊이는 fit'),
    'studioGrey':   (1.8,  12.2, -16.2, -10.2, 'carpetGrey', 'ne',
                     'Train,Car,Ship + 플린스 3.0 + Number 4 = 10.4m (78405_011). '
                     '서쪽 끝 **코발트 블루 벽** 실재 — v2 가 low 로 남겼던 것이 확인됐다'),
    'phooey':       (-11.2,  1.8, -15.2, -10.2, 'carpetGrey', 'n',
                     '네이비 벽: 섹션판 + Phooey 3.55 + 니치. 끝의 빨간 벽까지 ~20m (78405_023)'),
    'boh':          (-11.2,  5.4, -10.2,  -2.0, 'epoxy', '',
                     '서비스 코어 — 카툰 북쪽 구석의 흰 커튼 서비스문 + 녹색 비상구등이 여기로'),
    'red':          (-19.4, -11.2, -12.6, -4.4, 'carpetGrey', 'wn',
                     'A-One 1.83 + 공백 1.03 + 드로잉 7점 3.66 = 최소 8.1m. '
                     '벽높이 3.15m, 작품 중심 1.43m 실측 (78405_023)'),
    'warriorsWhite': (-20.0, -11.2, -4.4,  3.4, 'carpetGrey', 'w',
                      '검은 상자 + Blue Skies 독립 흰 가벽 4.1 x 3.0 (78405_036)'),
    'collage':      (-15.4, -11.2,  3.4,  9.6, 'carpetGrey', 'w',
                     'Joy 1.725 + 2.08 + Untitled 1985 1.727. 벽 자체가 곡선 (78405_036)'),
    'headsBlack':   (-14.6, -11.8,  9.6, 11.6, 'carpetGrey', '',
                     '전시에서 가장 작은 공간. 검은 벽감'),
    'cartoons':     (-11.2,  -3.0,  -2.0,  6.0, 'carpetGrey', '',
                     '봄베로 챠콜 독립 가벽 4.24 x 3.15 실측 (78405_053)'),
    'words':        (-3.0,  12.2,  -2.0,   3.6, 'carpetGrey', '',
                     '천장이 사람 머리 바로 위 ~2.9m 짜리 챠콜 데크 (78406_006)'),
    'msec':         (12.2, 18.8,  -2.0,   3.6, 'carpetGrey', 'e',
                     '어두운 방 + 아래 밝은 단, 맞은편에 메이소닉 깊은 상자 (78406_022)'),
    'temple':       (7.8,  17.2,   3.6,  12.6, 'floorPale', 'es',
                     '검은 벽 + 밝은 회색 바닥. 벽 위로 크림색 DDP 소핏이 ~4.9m. '
                     '가운데 **윗면이 경사진 쐐기 볼륨** + 모서리 슬롯 (78406_030)'),
    'templeW':      (-3.0,   7.8,   3.6,   8.6, 'floorPale', '',
                     'temple 서쪽 팔 — 노트 격자가 안쪽 모서리를 여러 번 돈다'),
    'drawing':      (-3.0,   7.8,   8.6,  12.6, 'carpetGrey', '',
                     '반구대 탁본 3.90 + 플린스 → 전시 최고 벽. 폭 3.4~4.2 (78406_045)'),
    'anatomy':      (-9.6,  -3.0,   6.0,  12.6, 'carpetGrey', 'w',
                     'Flesh and Spirit 3.683 + 그 밑 긴 흰 단. 검은 벽 쪽 천장도 검다 (78406_058)'),
    'hidden':       (-9.6,  -5.6,   9.4,  12.6, 'carpetGrey', '',
                     'anatomy 안에 박힌 전면 검정 방'),
    'asia':         (-5.0,   2.2,  12.6,  16.2, 'carpetRed', 'sw',
                     '인터뷰 프로젝션 + 맞은편 **곡선** 흰 벽에 추사 현판 2점 (78406_073)'),
    'epilogue':     (2.2,  10.8,  12.6,  18.0, 'carpetRed', 'se',
                     'Epilogue 독립 가벽 + 곡선 벽, EXU 는 낮은 검은 핀 (78406_075)'),
}
SERVICE = {'boh'}
MERGED = {'templeW': 'temple'}

# ─────────────────────────────────────────────────────────────────────────────
# 2. 벽 높이는 구역이 아니라 **면마다** 다르다. (구역, 면 또는 '*'): (높이, 근거)
# ─────────────────────────────────────────────────────────────────────────────
H_STD = 3.0
FACE_H = {
    ('preface', 'w'): (3.5, '프리페이스 초상화 벽 — 초상화가 전고'),
    ('red', '*'): (3.15, 'A-One 벽 실측 3.15m (78405_023)'),
    ('warriorsWhite', 's'): (3.6, '검은 상자 개구부 3.2 + 그 위 검은 헤더 0.4'),
    ('warriorsWhite', '*'): (3.2, '트랙암이 벽 위를 넘어온다'),
    ('collage', '*'): (3.03, 'Joy/Untitled 1985 로 보정한 기준 벽 (3.03m)'),
    ('headsBlack', '*'): (3.2, '벽감 인방'),
    ('words', '*'): (2.95, '천장 챠콜 데크가 사람 머리 바로 위 ~2.9m (78406_006)'),
    ('drawing', 'n'): (4.8, '반구대 탁본 3.90 + 플린스 0.4 → 전시 최고 벽'),
    ('drawing', '*'): (3.3, '복도 어두운 천장 + 검은 소핏 밴드'),
    ('anatomy', 'w'): (4.6, 'Flesh and Spirit 3.683, 중심 2.40 (78406_058)'),
    ('anatomy', '*'): (3.6, '맞은편 흰 벽'),
    ('temple', '*'): (3.6, '검은 벽 위로 크림색 소핏이 보인다 (78406_030)'),
    ('templeW', '*'): (3.6, '같음'),
    ('epilogue', 's'): (3.0, 'EXU 핀은 양 옆 벽보다 눈에 띄게 낮다'),
    ('epilogue', '*'): (3.2, ''),
    ('asia', '*'): (3.2, ''),
    ('phooey', 's'): (3.0, '네이비 벽 3.0 + 그 위 벌크헤드는 별도'),
    ('preface', '*'): (3.5, '서문 구역 전체가 표준보다 높다'),
}

FACE_FIX = {'temple': 'black', 'templeW': 'black', 'studioGrey': 'white', 'boh': 'white'}
OPEN = {('phooey', 'n'), ('temple', 'w'), ('templeW', 'e'), ('hidden', 'w')}

# ─────────────────────────────────────────────────────────────────────────────
# 3. 독립 가벽(섬) — 전부 사진에서 치수를 쟀다
#    (id, 구역, a, b, 두께, 높이, 앞면, 뒷면, 근거)
# ─────────────────────────────────────────────────────────────────────────────
ISLANDS = [
    ('ballplayer', 'studioGrey', [2.6, -14.6], [2.6, -11.1], 0.30, 3.3, 'coal', 'coal',
     '볼플레이어 흰 박스액자가 걸린 챠콜 가벽. 서쪽 끝에 코발트 블루 귀 (78405_011)'),
    ('funGallery', 'phooey', [-3.5, -14.2], [1.3, -14.2], 0.30, 3.3, 'white', 'white',
     '펀갤러리 전면 사진 자립 패널, 흰 옆면이 보인다. 뒤는 어두운 영상 벽감'),
    ('blueSkies', 'warriorsWhite', [-15.3, 1.6], [-11.2, 1.6], 0.30, 3.0, 'white', 'white',
     'Blue Skies 자립 흰 가벽 **4.1 x 3.0 실측** (78405_036)'),
    ('bombero', 'cartoons', [-9.5, 1.2], [-5.26, 1.2], 0.35, 3.15, 'coal', 'coal',
     'Bombero 챠콜 자립 가벽 **4.24 x 3.15 실측** (78405_053)'),
    ('epiloguePanel', 'epilogue', [2.6, 13.2], [8.4, 13.2], 0.30, 3.2, 'white', 'white',
     'Epilogue 문구 + 매입 모니터 + Universal (78406_075)'),
]

# Temple 중앙 쐐기 볼륨 — 윗면이 경사지고 한쪽 위 모서리에 세로 슬롯
TEMPLE_WEDGE = {
    'poly': [[10.6, 7.0], [14.0, 6.4], [14.6, 9.4], [11.2, 10.2]],
    'h_low': 3.9, 'h_high': 4.6, 'slot': [0.55, 2.35, 0.55, 1.15],
    'why': '주변 벽보다 확실히 높고 윗면이 한쪽으로 경사진 쐐기, 위 모서리에 세로 슬롯. '
           '앞면에 밝은 벽감(노트 표지) + 그 앞 검은 받침 진열장 (78406_030)',
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. 개구부 — (구역, 면, u0, u1, 높이, 종류, 신뢰도). u 는 위에서 봤을 때 시계방향.
# ─────────────────────────────────────────────────────────────────────────────
DOORS = [
    ('preface', 'e', 2.2, 4.2, 2.3, '자동 유리문 (검은 파사드 안)', 'medium'),
    ('preface', 'w', 6.8, 8.2, 3.5, '프리페이스 벽이 창문 작품에서 1m 더 가다 끊긴다 — 돌아가면 뒷면', 'high'),
    ('studioRed', 'n', 3.6, 6.1, 3.0, '열린 틈; 이 너머로 Number 4 가 보인다', 'high'),
    ('studioGrey', 'w', 0.4, 4.8, 3.0, '볼플레이어 검은 가벽이 절반쯤 가린다', 'high'),
    ('phooey', 'w', 0.2, 4.6, 3.0,
     '좁은 문이 아니라 복도 끝이 통째로 빨간 방으로 트여 있다 — '
     '78405_023 에서 검은 벽이 끝나고 빨간 벽이 그대로 펼쳐진다', 'high'),
    ('red', 's', 1.2, 5.4, 3.05, '빨간 벽이 끝나고 백남준 로봇이 선 흰 구역', 'high'),
    ('warriorsWhite', 's', 0.10, 1.90, 3.0,
     '검은 상자 동쪽 귀와 Blue Skies 흰 가벽 사이 좁은 슬롯. **미해결** — '
     '사진에서 상자 개구부가 7.0m 인데 벽 전체가 8.8m 라 3m 짜리 복도 입구가 들어갈 자리가 없다', 'low'),
    ('collage', 's', 0.6, 3.4, 3.2, '검은 벽감 — 막다른 곳, 보고 되돌아 나온다', 'high'),
    ('collage', 'e', 0.2, 2.5, 3.0, '카툰으로', 'low'),
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

FRM = {(d['zone'], d['face']): d['frm'] for d in V2['doors']}
TO = {(d['zone'], d['face']): d['to'] for d in V2['doors']}
FRM.update({('templeW', 's'): 'temple', ('hidden', 'e'): 'anatomy', ('cartoons', 'n'): '_service',
            ('collage', 's'): 'collage', ('collage', 'e'): 'collage'})
TO.update({('templeW', 's'): 'drawing', ('hidden', 'e'): 'hidden', ('cartoons', 'n'): 'boh',
           ('collage', 's'): 'headsBlack', ('collage', 'e'): 'cartoons'})

SIDES = ('n', 'e', 's', 'w')


def rect(zid):
    return Z[zid][:4]


def face_h(zid, side):
    if (zid, side) in FACE_H:
        return FACE_H[(zid, side)][0]
    if (zid, '*') in FACE_H:
        return FACE_H[(zid, '*')][0]
    return H_STD


def face_mat(zid, side):
    if zid in FACE_FIX:
        return FACE_FIX[zid]
    base = MERGED.get(zid, zid)
    for z in V2['zones']:
        if z['id'] == base:
            return z['walls'].get(side, 'white')
    return 'white'


def face_of(zid, p, q):
    """선분이 그 구역의 어느 면인지 (원래 사각형 기준). 곡선 구간도 같은 규칙."""
    x0, x1, z0, z1 = rect(zid)
    mx, mz = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    if abs(q[0] - p[0]) >= abs(q[1] - p[1]):
        return 'n' if abs(mz - z0) <= abs(mz - z1) else 's'
    return 'w' if abs(mx - x0) <= abs(mx - x1) else 'e'


def _lines(g):
    if g.is_empty:
        return []
    gs = list(g.geoms) if hasattr(g, 'geoms') else [g]
    return [x for x in gs if x.geom_type == 'LineString' and x.length > 0.05]


def derive_walls(polys):
    """구역 폴리곤들의 경계를 모아 벽을 만든다. 두 구역이 맞닿은 구간은 **한 장**만."""
    ids = list(polys)
    shared, touch = [], {z: [] for z in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            for ln in _lines(polys[a].boundary.intersection(polys[b].boundary)):
                shared.append((a, b, ln))
                touch[a].append(ln)
                touch[b].append(ln)
    runs = [(a, b, ln) for (a, b, ln) in shared]
    for z in ids:
        bnd = polys[z].boundary
        if touch[z]:
            bnd = bnd.difference(unary_union(touch[z]).buffer(0.01))
        for ln in _lines(bnd):
            runs.append((z, None, ln))

    walls = []
    for (a, b, ln) in runs:
        if b == 'hidden' or (a == 'hidden' and b == 'anatomy'):
            a, b = 'hidden', (a if a != 'hidden' else b)
        cs = list(ln.coords)
        for p, q in zip(cs, cs[1:]):
            if math.dist(p, q) < 0.05:
                continue
            fa = face_of(a, p, q)
            fb = face_of(b, p, q) if b else None
            if (a, fa) in OPEN and (b is None or (b, fb) in OPEN):
                continue
            h = max([face_h(a, fa)] + ([face_h(b, fb)] if b else []))
            ma, mb = face_mat(a, fa), (face_mat(b, fb) if b else 'white')
            if 'hidden' in (a, b):      # 전면 검정 방 — 바깥면도 검정으로 읽힌다
                ma = mb = 'black'
            walls.append({'p': [round(p[0], 3), round(p[1], 3)],
                          'q': [round(q[0], 3), round(q[1], 3)],
                          'len': round(math.dist(p, q), 3), 'h': round(h, 2), 't': T,
                          'za': a, 'fa': fa, 'ma': ma,
                          'zb': b, 'fb': fb, 'mb': mb})
    for i, w in enumerate(walls):
        w['id'] = f'W{i:03d}'
    return walls


def base_rect(zid):
    return sbox(*(rect(zid)[0], rect(zid)[2], rect(zid)[1], rect(zid)[3]))


def big(g):
    if g.is_empty:
        return g
    return max(g.geoms, key=lambda q: q.area) if g.geom_type == 'MultiPolygon' else g


def main():
    # 1) 모든 구역을 기본 사각형으로 놓는다 — 여기까지는 v3 와 같은 위상
    polys = {z: base_rect(z) for z in Z}
    # 2) 사각형들이 쓰고 남은 **빈 자리로만** 껍데기 쪽으로 자란다.
    #    남의 영역을 먹지 않으므로 인접 관계(동선)가 깨지지 않고,
    #    늘어난 변은 홀 윤곽에 잘려 **곡선**이 된다.
    occupied = unary_union([polys[z] for z in Z if z != 'hidden'])
    free = INNER.difference(occupied)
    for z in Z:
        g = Z[z][5]
        if not g:
            continue
        x0, x1, z0, z1 = rect(z)
        ext = sbox(x0 - (GROW if 'w' in g else 0), z0 - (GROW if 'n' in g else 0),
                   x1 + (GROW if 'e' in g else 0), z1 + (GROW if 's' in g else 0))
        gain = big(ext.intersection(free))
        if not gain.is_empty:
            polys[z] = big(unary_union([polys[z], gain]))
            free = free.difference(gain)
    used = unary_union([polys[z] for z in Z])
    free = HALL.difference(used)
    tot = sum(polys[z].area for z in Z) - polys['hidden'].area
    print(f'홀 {HALL.area:.0f}㎡  /  구역 {tot:.0f}㎡  /  남는 면적 {free.area:.0f}㎡')
    for z in sorted(Z, key=lambda k: -polys[k].area):
        print(f'   {z:14s} {polys[z].area:6.1f} ㎡   {Z[z][4]:10s} 곡선변={Z[z][5] or "-"}')

    walls = derive_walls(polys)
    print(f'   벽 {len(walls)}장, 총연장 {sum(w["len"] for w in walls):.1f}m')
    out = {
        '_about': 'Basquiat at DDP — 벽체 설계 v4. 바깥 벽을 홀 껍데기 곡선으로 깎고, '
                  '벽 높이와 독립 가벽 치수를 a4b4 워크스루 사진에서 실측했다.',
        '_frame': V2['_frame'],
        '_u_convention': V2['_u_convention'],
        'palette': V2['palette'],
        'globals': dict(V2['globals'], wall_thickness=T),
        'route': V2['route'],
        'shell': SHELL,
        'zones': [{
            'id': z, 'rect': list(rect(z)),
            'poly': [[round(x, 3), round(y, 3)] for x, y in polys[z].exterior.coords[:-1]],
            'area_m2': round(polys[z].area, 1), 'floor': Z[z][4], 'curved': Z[z][5],
            'service': z in SERVICE, 'merged_into': MERGED.get(z),
            'walls': {s: face_mat(z, s) for s in SIDES},
            'wall_h': {s: face_h(z, s) for s in SIDES},
            'open': sorted(s for s in SIDES if (z, s) in OPEN),
            'ceiling': next((d['ceiling'] for d in V2['zones'] if d['id'] == MERGED.get(z, z)),
                            {'type': 'ddp_soffit', 'h': 4.6}),
            'why': Z[z][6],
        } for z in Z],
        'islands': [{'id': i, 'zone': zz, 'a': a, 'b': b, 't': t, 'h': h,
                     'front': f, 'back': bk, 'why': w}
                    for (i, zz, a, b, t, h, f, bk, w) in ISLANDS],
        'temple_wedge': TEMPLE_WEDGE,
        'walls': walls,
        'doors': [{'zone': z, 'face': sd, 'u0': u0, 'u1': u1, 'h': h, 'kind': k, 'conf': c,
                   'frm': FRM.get((z, sd), z), 'to': TO.get((z, sd), '')}
                  for (z, sd, u0, u1, h, k, c) in DOORS],
        'works': V2['works'],
        'freestanding': V2['freestanding'],
        'check': {'hall_m2': round(HALL.area, 1), 'zones_m2': round(tot, 1),
                  'free_m2': round(free.area, 1)},
    }
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
