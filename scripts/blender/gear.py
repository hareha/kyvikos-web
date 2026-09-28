"""행사 장비·소품 — 실제 제품 치수와 구조대로 (공개 모델이 없는 것들)

모든 함수는 asm(Assembly), frame(웹 좌표 변환), 재질 사전 M 을 받아 부품을 더한다.
로컬 좌표: 원점 = 바닥 가운데, +z = 앞(사람·관객 쪽)

- pyramid_heater   피라미드 가스 히터 (높이 2.27m, 받침 0.5m): 테이퍼 받침함·손잡이·유리관·네 다리·반사갓
- lectern          흰 아크릴 연설대 (1.15m): 기울어진 윗판·앞 패널·구즈넥 마이크
- popup_tent       팝업 천막: 각 기둥·가위 트러스·처진 지붕 천·밸런스·세 면 벽
- road_case        플라이트 케이스 (검정 합판 + 알루미늄 모서리·코너 캡·손잡이)
- lighting_console 조명 콘솔 (grandMA3 light 계열 1.25 × 0.8m): 경사 본체·터치스크린 둘·페이더·엔코더·키
- video_switcher   영상 스위처 (조명 버튼 줄·T바)
- program_monitor  55인치 모니터 + 스탠드
- folding_chair    접이식 스태프 의자
"""
import math

import bmesh
from mathutils import Vector as V

from lib import PI, T, bevel_box, box, cyl, plane, sphere, tube


def _prism(profile, depth):
    """옆모습 다각형(z, y 목록)을 x 방향으로 depth 만큼 뽑은 기둥 (가운데 기준)"""
    def build(bm):
        a = [bm.verts.new((-depth / 2, y, z)) for z, y in profile]
        b = [bm.verts.new((depth / 2, y, z)) for z, y in profile]
        bm.faces.new(list(reversed(a)))
        bm.faces.new(b)
        n = len(profile)
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.006, segments=2, affect='EDGES', profile=0.5)
    return build


def _frustum(b_half, t_half, h, seg=4):
    """정사각 뿔대 (아래 반폭 b_half, 위 반폭 t_half)"""
    k = math.sqrt(2)
    return cyl(t_half * k, b_half * k, h, seg)


# ── 피라미드 히터 ───────────────────────────────────────────────
def pyramid_heater(asm, frame, M, glass=None, emit=None):
    """오벨리스크형 가스 히터 (총 2.16m) — 클라이언트 사진 kakao 16 실측.

    바닥에서 꼭대기까지 하나로 이어지는 사각 테이퍼다(밑변 0.50m → 윗변 0.21m).
    아래 0.82m 는 크림색 철판 패널 + 스테인리스 모서리 기둥 + 가로 크롬 손잡이,
    위 1.22m 는 유리관을 감싼 철망 케이지, 꼭대기는 밖으로 벌어진 스테인리스 갓.
    (전에는 가는 기둥에 받침함과 버섯 갓을 얹은 다른 형태였다.)
    """
    s, g, f = M['stainless'], M['glass'], M['flame']
    body = M.get('heaterBody', s)
    HB, HC, B0, B1, B2 = 0.82, 2.04, 0.25, 0.191, 0.105      # 몸통 높이 / 케이지 상단 / 반폭 세 단계
    for sx in (-1, 1):                                                                 # 바닥 발 네 개
        for sz in (-1, 1):
            asm.add(bevel_box(0.07, 0.035, 0.07, 0.008), frame @ T(sx * (B0 - 0.05), 0.017, sz * (B0 - 0.05)), s)
    for sx in (-1, 1):                                                                 # 모서리 스테인리스 기둥 (통으로 테이퍼)
        for sz in (-1, 1):
            gm, mm = tube(frame @ V((sx * B0, 0.03, sz * B0)), frame @ V((sx * B2, HC, sz * B2)), 0.019, 4)
            asm.add(gm, mm, s)
    asm.add(_frustum(B0 - 0.012, B1 - 0.012, HB - 0.03, 4), frame @ T(0, (HB - 0.03) / 2 + 0.03, 0, PI / 4), body)   # 크림 패널 몸통
    asm.add(cyl(0.016, 0.016, 0.26, 12), frame @ T(0, 0.60, B1 + 0.035, 0, PI / 2), s)         # 앞면 가로 크롬 손잡이
    for sx in (-1, 1):
        asm.add(cyl(0.012, 0.012, 0.05, 8), frame @ T(sx * 0.12, 0.60, B1 + 0.012), s)
    asm.add(bevel_box(0.07, 0.035, 0.012, 0.004), frame @ T(B1 + 0.012, 0.66, 0.0, 0, 0, 0, 1, 1, 1), M['black'])   # 옆면 점검구
    asm.add(bevel_box(2 * B1 + 0.03, 0.025, 2 * B1 + 0.03, 0.006), frame @ T(0, HB, 0), s)     # 몸통 상단 판
    for k in range(10):                                                                # 철망 케이지: 가로 링 열 개
        t = k / 9
        y = HB + 0.05 + t * (HC - HB - 0.09)
        hw = B1 + (B2 - B1) * (y - HB) / (HC - HB)
        for (ax, az, ww, dd) in ((0, hw, 2 * hw, 0.008), (0, -hw, 2 * hw, 0.008), (hw, 0, 0.008, 2 * hw), (-hw, 0, 0.008, 2 * hw)):
            asm.add(box(ww, 0.009, dd), frame @ T(ax, y, az), s)
    for i in range(12):                                                                # 세로 철사
        u = (i % 3 + 1) / 4 * 2 - 1
        side = i // 3
        p0 = V((u * B1, HB + 0.05, B1)) if side == 0 else V((u * B1, HB + 0.05, -B1)) if side == 1 else \
            V((B1, HB + 0.05, u * B1)) if side == 2 else V((-B1, HB + 0.05, u * B1))
        p1 = V((u * B2, HC - 0.04, B2)) if side == 0 else V((u * B2, HC - 0.04, -B2)) if side == 1 else \
            V((B2, HC - 0.04, u * B2)) if side == 2 else V((-B2, HC - 0.04, u * B2))
        gm, mm = tube(frame @ p0, frame @ p1, 0.005, 4)
        asm.add(gm, mm, s)
    asm.add(_frustum(0.23, 0.05, 0.13, 4), frame @ T(0, HC + 0.065, 0, PI / 4), s)             # 밖으로 벌어진 갓
    asm.add(bevel_box(0.47, 0.016, 0.47, 0.006), frame @ T(0, HC + 0.008, 0), s)               # 갓 아래 립
    asm.add(bevel_box(0.075, 0.05, 0.075, 0.008), frame @ T(0, HC + 0.155, 0), s)              # 꼭지
    asm.add(sphere(0.022, 2), frame @ T(0, HC + 0.195, 0), s)
    if glass is not None:
        glass.add(cyl(0.062, 0.062, 1.14, 24), frame @ T(0, HB + 0.62, 0), g)
    if emit is not None:
        emit.add(cyl(0.024, 0.032, 1.0, 12), frame @ T(0, HB + 0.56, 0), f)


# ── 연설대 ──────────────────────────────────────────────────────
def lectern(asm, frame, M, emit=None):
    w = M['lectern']
    # 옆모습: 앞(+z)이 높고 뒤(연사)가 낮은 윗판, 아래로 갈수록 좁아짐
    prof = [(0.19, 0.0), (0.21, 0.08), (0.26, 1.16), (-0.22, 1.06), (-0.17, 0.08), (-0.15, 0.0)]
    def body(bm):
        top_w, bot_w = 0.62, 0.46
        rows = []
        for z, y in prof:
            t = y / 1.16
            hw = (bot_w + (top_w - bot_w) * t) / 2
            rows.append((bm.verts.new((-hw, y, z)), bm.verts.new((hw, y, z))))
        bm.faces.new([r[0] for r in reversed(rows)])
        bm.faces.new([r[1] for r in rows])
        n = len(rows)
        for i in range(n):
            a, b = rows[i], rows[(i + 1) % n]
            bm.faces.new((a[0], b[0], b[1], a[1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.012, segments=3, affect='EDGES', profile=0.5)
    asm.add(body, frame, w)
    asm.add(bevel_box(0.56, 0.1, 0.48, 0.01), frame @ T(0, 0.03, 0.02), w)                   # 받침
    asm.add(bevel_box(0.48, 0.5, 0.012, 0.004), frame @ T(0, 0.72, 0.235, 0, -0.045), M['lecternPanel'])   # 앞 패널
    # 구즈넥 마이크
    base = V((0.16, 1.1, -0.12))
    pts = [base + V((0, 0.02 * i, -0.012 * i * i)) for i in range(9)]
    for a, b in zip(pts[:-1], pts[1:]):
        g, m = tube(frame @ a, frame @ b, 0.006, 8, caps=True)
        asm.add(g, m, M['black'])
    asm.add(cyl(0.012, 0.018, 0.07, 12), frame @ T(*(pts[-1] + V((0, 0.02, -0.03)))[:], 0, 0.9), M['black'])


# ── 팝업 천막 ───────────────────────────────────────────────────
def popup_tent(asm, frame, M, size=4.5, h=2.35, walls=(True, True, True, False)):
    """walls: (뒤, 오른쪽, 왼쪽, 앞) 벽 유무"""
    a, fab = M['alu'], M['tent']
    half = size / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            asm.add(bevel_box(0.04, h, 0.04, 0.005), frame @ T(sx * half, h / 2, sz * half), a)    # 각 기둥
            asm.add(box(0.16, 0.08, 0.16), frame @ T(sx * half, 0.03, sz * half), a)            # 발판 (바닥에 박힘)
            asm.add(bevel_box(0.07, 0.12, 0.07, 0.01), frame @ T(sx * half, h - 0.06, sz * half), M['black'])   # 모서리 조인트
    # 가위 트러스 (네 변, 칸마다 X)
    bays, th = 3, 0.42
    for (ax, az, bx, bz) in ((-half, half, half, half), (-half, -half, half, -half), (-half, -half, -half, half), (half, -half, half, half)):
        for k in range(bays):
            t0, t1 = k / bays, (k + 1) / bays
            p0 = V((ax + (bx - ax) * t0, 0, az + (bz - az) * t0))
            p1 = V((ax + (bx - ax) * t1, 0, az + (bz - az) * t1))
            for (u, v) in ((p0 + V((0, h - th, 0)), p1 + V((0, h, 0))), (p0 + V((0, h, 0)), p1 + V((0, h - th, 0)))):
                g, m = tube(frame @ u, frame @ v, 0.012, 6)
                asm.add(g, m, a)
    # 지붕 천: 가운데가 솟고 면마다 살짝 처진 네 경사면
    peak = h + 0.95
    def roof(bm, n=10):
        corners = [(-half - 0.05, -half - 0.05), (half + 0.05, -half - 0.05), (half + 0.05, half + 0.05), (-half - 0.05, half + 0.05)]
        apex = (0.0, peak, 0.0)
        for i in range(4):
            (x0, z0), (x1, z1) = corners[i], corners[(i + 1) % 4]
            grid = []
            for j in range(n + 1):
                t = j / n
                row = []
                for k in range(n + 1 - j):
                    u = k / n
                    # 삼각형 면 위 점: 가장자리 → 꼭짓점
                    x = x0 + (x1 - x0) * u + (apex[0] - x0) * t
                    z = z0 + (z1 - z0) * u + (apex[2] - z0) * t
                    y = h + (peak - h) * t
                    w_ = u * (1 - t - u) * t
                    row.append(bm.verts.new((x, y - 0.35 * w_ * 4, z)))
                grid.append(row)
            for j in range(n):
                for k in range(n - j):
                    bm.faces.new((grid[j][k], grid[j][k + 1], grid[j + 1][k]))
                    if k < n - j - 1:
                        bm.faces.new((grid[j][k + 1], grid[j + 1][k + 1], grid[j + 1][k]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.015)
    asm.add(roof, frame, fab, 1.5)
    # 밸런스 (지붕 가장자리 늘어진 천, 0.25m) + 벽
    for i, (px, pz, ry) in enumerate(((0, -half - 0.06, PI), (half + 0.06, 0, PI / 2), (-half - 0.06, 0, -PI / 2), (0, half + 0.06, 0))):
        asm.add(box(size + 0.12, 0.25, 0.012), frame @ T(px, h - 0.12, pz, ry), fab, 1.5)
        if walls[i]:
            asm.add(box(size - 0.06, h - 0.3, 0.01), frame @ T(px * 0.985, (h - 0.3) / 2 + 0.02, pz * 0.985, ry), fab, 1.5)


# ── 플라이트 케이스 ─────────────────────────────────────────────
def road_case(asm, frame, M, w, h, d, handles=True):
    asm.add(box(w - 0.06, h, d - 0.06), frame @ T(0, h / 2, 0), M['case'], 0.8)   # 상판 = h (장비가 얹힘)
    e = 0.022
    for sy in (0.011, h - 0.005):                                     # 알루미늄 모서리 (위는 6mm 솟은 립)
        for sz in (-d / 2 + 0.011, d / 2 - 0.011):
            asm.add(box(w - 0.044, e, e), frame @ T(0, sy, sz), M['alu'])
        for sx in (-w / 2 + 0.011, w / 2 - 0.011):
            asm.add(box(e, e, d - 0.044), frame @ T(sx, sy, 0), M['alu'])
    for sx in (-w / 2 + 0.011, w / 2 - 0.011):
        for sz in (-d / 2 + 0.011, d / 2 - 0.011):
            asm.add(box(e, h - 0.044, e), frame @ T(sx, h / 2, sz), M['alu'])
            for sy in (0.02, h - 0.02):
                asm.add(sphere(0.022, 1), frame @ T(sx, sy, sz), M['alu'])   # 공 모양 코너 캡
    if handles:
        for sx in (-1, 1):
            asm.add(bevel_box(0.03, 0.05, 0.14, 0.006), frame @ T(sx * (w / 2 - 0.02), h * 0.6, 0), M['alu'])
        asm.add(bevel_box(0.08, 0.05, 0.03, 0.006), frame @ T(-w / 4, h - 0.07, d / 2 - 0.02), M['alu'])   # 잠금 걸쇠
        asm.add(bevel_box(0.08, 0.05, 0.03, 0.006), frame @ T(w / 4, h - 0.07, d / 2 - 0.02), M['alu'])


# ── 조명 콘솔 ───────────────────────────────────────────────────
def lighting_console(asm, frame, M, emit):
    k = M['consoleBody']
    # 옆모습 (z, y): 앞이 낮고 뒤로 올라가는 경사 본체
    prof = [(0.4, 0.0), (0.4, 0.07), (-0.05, 0.13), (-0.4, 0.17), (-0.4, 0.0)]
    asm.add(_prism(prof, 1.25), frame, k)
    slope = math.atan2(0.13 - 0.07, 0.45)
    def on_deck(x, z, lift=0.0):
        """앞 경사면 위 점"""
        t = (0.4 - z) / 0.45
        return frame @ T(x, 0.07 + 0.06 * t + lift, z, 0, -slope)
    # 페이더 15개 (홈 + 캡) + 실행 버튼 줄 (발광)
    for i in range(15):
        x = -0.58 + i * 0.05
        asm.add(box(0.008, 0.004, 0.11), on_deck(x, 0.26, 0.001), M['black'])
        asm.add(bevel_box(0.022, 0.018, 0.03, 0.004), on_deck(x, 0.24 + (i % 4) * 0.02, 0.01), M['alu'])
        emit.add(box(0.03, 0.006, 0.014), on_deck(x, 0.17, 0.003), M['keyAmber'] if i % 3 else M['keyWhite'])
    # 엔코더 5개 + 키 격자
    for i in range(5):
        asm.add(cyl(0.017, 0.019, 0.03, 16), on_deck(-0.5 + i * 0.1, 0.06, 0.015), M['black'])
    for r in range(4):
        for c in range(9):
            asm.add(bevel_box(0.03, 0.012, 0.028, 0.004), on_deck(0.12 + c * 0.052, 0.3 - r * 0.045, 0.006), M['keyGrey'])
    # 터치스크린 둘 (경첩 받침 + 베젤 + 화면)
    for sx in (-0.3, 0.3):
        asm.add(bevel_box(0.1, 0.06, 0.05, 0.01), frame @ T(sx, 0.19, -0.33), k)
        f = frame @ T(sx, 0.36, -0.36, 0, -0.35)
        asm.add(bevel_box(0.5, 0.33, 0.025, 0.008), f, k)
        emit.add(plane(0.46, 0.29), f @ T(0, 0, 0.03), M['uiLight'], tile=None)
    # 구즈넥 조명
    base = frame @ V((0.58, 0.16, -0.38))
    pts = [base + (frame.to_3x3() @ V((0, 0.03 * i, 0.012 * i * i * 0.3))) for i in range(10)]
    for a, b in zip(pts[:-1], pts[1:]):
        g, m = tube(a, b, 0.005, 8, caps=True)
        asm.add(g, m, M['black'])
    emit.add(cyl(0.01, 0.015, 0.03, 10), T(*pts[-1][:]), M['clipLamp'])


# ── 영상 스위처 ────────────────────────────────────────────────
def video_switcher(asm, frame, M, emit):
    prof = [(0.17, 0.0), (0.17, 0.04), (-0.17, 0.07), (-0.17, 0.0)]
    asm.add(_prism(prof, 0.62), frame, M['consoleBody'])
    slope = math.atan2(0.03, 0.34)
    colors = [M['keyRed'], M['keyGreen'], M['keyWhite'], M['keyAmber']]
    for r in range(4):
        for c in range(10):
            z = 0.1 - r * 0.045
            y = 0.04 + 0.03 * (0.17 - z) / 0.34
            m = colors[r] if (c + r) % 4 == 0 else M['keyGrey']
            (emit if m is not M['keyGrey'] else asm).add(bevel_box(0.03, 0.012, 0.03, 0.004), frame @ T(-0.25 + c * 0.045, y + 0.006, z, 0, -slope), m)
    asm.add(box(0.06, 0.006, 0.16), frame @ T(0.26, 0.058, 0.0, 0, -slope), M['black'])     # T바 홈
    g, m = tube(frame @ V((0.26, 0.06, 0.02)), frame @ V((0.26, 0.16, -0.02)), 0.008, 8, caps=True)
    asm.add(g, m, M['alu'])
    asm.add(bevel_box(0.07, 0.025, 0.025, 0.008), frame @ T(0.26, 0.17, -0.025), M['black'])


# ── 모니터 · 의자 ──────────────────────────────────────────────
def program_monitor(asm, frame, M, emit, screen, height=2.45, w=1.24, hgt=0.72, facing=PI):
    """스탠드 위 모니터. facing: 화면이 보는 방향 (로컬 ry)"""
    asm.add(bevel_box(0.6, 0.07, 0.5, 0.008), frame @ T(0, 0.035, 0), M['black'])
    asm.add(bevel_box(0.05, height - 0.1, 0.05, 0.008), frame @ T(0, (height - 0.1) / 2, 0), M['alu'])
    f = frame @ T(0, height, 0, facing)
    asm.add(bevel_box(0.2, 0.2, 0.05, 0.01), f @ T(0, 0, -0.04), M['black'])               # VESA 마운트
    asm.add(bevel_box(w, hgt, 0.035, 0.006), f, M['black'])                                 # 베젤
    emit.add(plane(w - 0.03, hgt - 0.03), f @ T(0, 0, 0.03), screen, tile=None)


def folding_chair(asm, frame, M):
    """접이식 의자: X 다리 → 좌판 밑면, 뒷다리가 그대로 등받이 기둥으로 이어짐"""
    for sx in (-0.2, 0.2):
        rear_top, front_top = V((sx, 0.46, -0.18)), V((sx, 0.46, 0.16))
        for (a, b) in ((V((sx, 0, 0.2)), rear_top), (V((sx, 0, -0.2)), front_top), (rear_top, V((sx, 0.9, -0.25)))):
            g, m = tube(frame @ a, frame @ b, 0.011, 8, caps=True)
            asm.add(g, m, M['alu'])
    asm.add(bevel_box(0.44, 0.02, 0.4, 0.008), frame @ T(0, 0.47, 0), M['black'])
    asm.add(bevel_box(0.42, 0.22, 0.02, 0.008), frame @ T(0, 0.76, -0.225, 0, 0.14), M['black'])
