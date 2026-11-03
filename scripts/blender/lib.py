"""Blender 장면 구성 공통 도구 — 장면 스크립트에서 import 해서 쓴다.

좌표는 웹(three.js)과 같은 Y-up 으로 작성하고, 오브젝트를 만들 때 Blender(Z-up)로 변환한다.
그래서 glTF 로 내보내면 웹 장면과 위치가 정확히 일치한다.
"""
import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

ROOT = '/Users/hare/Documents/큐비크스홈페이지'
SRC = f'{ROOT}/assets-src'
TEX = f'{SRC}/textures'
SHOTS = f'{SRC}/shots'
HDRI = f'{SRC}/hdri'
PI = math.pi

# 웹(Y-up) → Blender(Z-up): X축 +90° 회전
TO_BL = Matrix.Rotation(PI / 2, 4, 'X')
TO_WEB = TO_BL.inverted()


def T(x=0, y=0, z=0, ry=0, rx=0, rz=0, sx=1, sy=1, sz=1):
    """three.js 의 compose(T·R·S, Euler XYZ) 와 같은 웹 좌표 변환"""
    return (
        Matrix.Translation((x, y, z))
        @ Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()
        @ Matrix.Diagonal((sx, sy, sz, 1))
    )


# ── 장면 초기화 / 컬렉션 ──────────────────────────────────────
def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for d in list(block):
            block.remove(d)
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


# ── 재질 ─────────────────────────────────────────────────────
def image(path, colorspace='sRGB'):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    return img


_TEX_MEAN = {}


def tex_mean(tid):
    """텍스처 디퓨즈의 **선형 평균 밝기**(RGB). 웹에서 색 x 텍스처로 곱할 때 보정에 쓴다."""
    if tid in _TEX_MEAN:
        return _TEX_MEAN[tid]
    src = image(f'{TEX}/{tid}_diff.jpg')
    c = src.copy()
    c.scale(16, 16)
    px = list(c.pixels)
    n = len(px) // 4
    m = tuple(sum(px[i * 4 + k] for i in range(n)) / n for k in range(3))
    bpy.data.images.remove(c)
    m = tuple(max(0.04, v) for v in m)
    _TEX_MEAN[tid] = m
    return m


def material(name, tex=None, color=(1, 1, 1), rough=0.8, metal=0.0, normal=1.0,
             emit=None, emit_strength=0.0, emit_image=None, image_base=None,
             transmission=0.0, sheen=0.0, coat=0.0, alpha=False, tex_mix=1.0,
             bump=None, bump_strength=1.0, bump_rough=0.0, wave=0.0, wave_strength=0.25):
    """Principled BSDF 재질. tex = Poly Haven 텍스처 id (디퓨즈 × color, 노멀)

    tex_mix < 1 이면 **색이 주인공이고 텍스처는 얼룩만** 더한다 (1.0 이면 예전과 같다).

    bump = 텍스처 id 를 주면 **노멀(요철)만** 쓰고 색은 건드리지 않는다. 칠한 합판·
    카펫·금속처럼 "색은 단색이 맞는데 표면이 너무 매끈해서 짜쳐 보이는" 면에 쓴다.
    베이크가 그 요철의 음영을 담기 때문에 웹에서도 그대로 보인다. bump_rough 를 주면
    거칠기도 같은 텍스처로 흔들어 반사가 균일하지 않게 한다."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    base = (*color, 1)
    if wave:
        # 물결 — 폴리헤이븐에 물 텍스처가 없어서 절차적 파형을 노멀로 쓴다.
        # 베이크가 이 잔물결의 음영·반사를 담으므로 웹에서도 평평해 보이지 않는다.
        w1 = nodes.new('ShaderNodeTexWave')
        w1.wave_type = 'BANDS'
        w1.bands_direction = 'DIAGONAL'
        w1.inputs['Scale'].default_value = wave
        w1.inputs['Distortion'].default_value = 7.0
        w1.inputs['Detail'].default_value = 3.0
        bp = nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = wave_strength
        bp.inputs['Distance'].default_value = 0.02
        links.new(w1.outputs['Fac'], bp.inputs['Height'])
        links.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    if bump:
        # 색은 그대로 두고 **요철만** 준다. 칠한 합판·카펫·금속처럼 색은 단색이 맞는데
        # 표면이 너무 매끈해서 평평해 보이는 면용.
        #
        # 주의: 노멀맵은 **베이크해야** 보인다. 베이크 전 웹에서는 아무 무늬도 안 나와
        # 단색 그대로였다(11/03 지적). 그래서 웹에는 같은 텍스처의 **디퓨즈**를 넘기고,
        # 웹이 색 x 텍스처로 곱하니 평균 밝기만큼 색을 미리 올려 둔다 — 그래야
        # 블렌더에서 보던 색 그대로 나오면서 무늬가 보인다.
        n = nodes.new('ShaderNodeTexImage')
        n.image = image(f'{TEX}/{bump}_nor.jpg', 'Non-Color')
        nm = nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = bump_strength
        links.new(n.outputs['Color'], nm.inputs['Color'])
        links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
        if bump_rough:
            d_ = nodes.new('ShaderNodeTexImage')
            d_.image = image(f'{TEX}/{bump}_diff.jpg', 'Non-Color')
            mr = nodes.new('ShaderNodeMapRange')
            mr.inputs['To Min'].default_value = max(0.0, rough - bump_rough)
            mr.inputs['To Max'].default_value = min(1.0, rough + bump_rough)
            links.new(d_.outputs['Color'], mr.inputs['Value'])
            links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])
    if tex:
        t = nodes.new('ShaderNodeTexImage')
        t.image = image(f'{TEX}/{tex}_diff.jpg')
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = tex_mix
        # MULTIPLY 는 A*(1-f) + A*B*f 다. f=1 이면 어느 쪽이 A든 같지만, f<1 로 질감을
        # 약하게 쓸 때는 **색이 A** 여야 색이 남는다 (텍스처가 A 면 색이 날아간다).
        if tex_mix >= 1.0:
            links.new(t.outputs['Color'], mix.inputs[6])
            mix.inputs[7].default_value = base
        else:
            mix.inputs[6].default_value = base
            links.new(t.outputs['Color'], mix.inputs[7])
        links.new(mix.outputs[2], bsdf.inputs['Base Color'])
        n = nodes.new('ShaderNodeTexImage')
        n.image = image(f'{TEX}/{tex}_nor.jpg', 'Non-Color')
        nm = nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = normal
        links.new(n.outputs['Color'], nm.inputs['Color'])
        links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    elif image_base:
        t = nodes.new('ShaderNodeTexImage')
        t.image = image(image_base)
        if alpha:
            t.image.alpha_mode = 'STRAIGHT'
            links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
            mix = nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            links.new(t.outputs['Color'], mix.inputs[6])
            mix.inputs[7].default_value = base
            links.new(mix.outputs[2], bsdf.inputs['Base Color'])
        else:
            links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        bsdf.inputs['Base Color'].default_value = base
    if emit_image:
        e = nodes.new('ShaderNodeTexImage')
        e.image = image(emit_image)
        links.new(e.outputs['Color'], bsdf.inputs['Base Color'])
        links.new(e.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = emit_strength
    elif emit:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1)
        bsdf.inputs['Emission Strength'].default_value = emit_strength
    if transmission:
        bsdf.inputs['Transmission Weight'].default_value = transmission
    if sheen:
        bsdf.inputs['Sheen Weight'].default_value = sheen
    if coat:
        bsdf.inputs['Coat Weight'].default_value = coat
    # 웹으로 옮길 때 참고할 값 (glTF extras 로 나감)
    graphic = emit_image or image_base
    # 웹은 라이트맵이 없을 때 color x map 으로만 그린다. bump 로 준 질감도 웹에는
    # 디퓨즈로 넘겨야 보이고, 그때 색이 어두워지지 않게 평균 밝기로 나눠 둔다.
    web_tex, web_color = tex or '', list(color)
    if not tex and not bump and wave:
        # 절차적 물결은 블렌더에서만 보인다. 웹에는 결이 비슷한 대리석 무늬를 넘겨
        # 물이 단색 판으로 보이지 않게 한다.
        web_tex = 'marble_01'
        mu = tex_mean(web_tex)
        lm = max(0.03, 0.2126 * mu[0] + 0.7152 * mu[1] + 0.0722 * mu[2])
        web_color = [min(6.0, color[k] / lm) for k in range(3)]
    if not tex and bump:
        # 채널별로 나누면 텍스처 색조만큼 색이 틀어진다(갈색 금속판에 회색을 맞추면 파래진다).
        # **밝기 한 값**으로만 나눠 원래 색조를 그대로 두고, 질감의 색조는 얹히게 한다.
        web_tex = bump
        mu = tex_mean(bump)
        lum = max(0.03, 0.2126 * mu[0] + 0.7152 * mu[1] + 0.0722 * mu[2])
        web_color = [min(6.0, color[k] / lum) for k in range(3)]
    m['web'] = {
        'tex': web_tex, 'color': web_color, 'rough': rough, 'metal': metal,
        'emit': bool(emit or emit_image), 'emitColor': list(emit or (1, 1, 1)), 'emitStrength': emit_strength,
        'image': graphic.rsplit('/', 1)[-1] if graphic else '', 'transmission': transmission,
        'alpha': alpha,
    }
    return m


# ── 메시 조립 ─────────────────────────────────────────────────
class Assembly:
    """웹 좌표로 도형을 모아 한 오브젝트로 만든다 (재질 슬롯 여러 개, UV0 = 월드 박스 투영)."""

    def __init__(self, name, coll):
        self.name, self.coll = name, coll
        self.bm = bmesh.new()
        self.bm.loops.layers.uv.new('UVMap')
        self.mats = []

    def add(self, build, matrix, mat, tile=2.0):
        """tile=None 이면 도형의 원래 UV(0~1)를 유지 — 그래픽이 들어가는 화면용"""
        tmp = bmesh.new()
        tmp.loops.layers.uv.new('UVMap')
        build(tmp)
        bmesh.ops.transform(tmp, matrix=matrix, verts=tmp.verts)
        me = bpy.data.meshes.new('tmp')
        tmp.to_mesh(me)
        tmp.free()
        start = len(self.bm.faces)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        self.bm.faces.ensure_lookup_table()
        # mat 이 목록이면 도형 원래의 재질 번호를 그 목록에 맞춰 옮긴다 (불러온 모델)
        mats = mat if isinstance(mat, (list, tuple)) else [mat]
        for m in mats:
            if m not in self.mats:
                self.mats.append(m)
        remap = [self.mats.index(m) for m in mats]
        uv = self.bm.loops.layers.uv.active
        for f in self.bm.faces[start:]:
            f.material_index = remap[min(f.material_index, len(remap) - 1)] if len(remap) > 1 else remap[0]
            if tile is None:
                continue
            n = f.normal
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            for loop in f.loops:
                x, y, z = loop.vert.co
                if ay >= ax and ay >= az:
                    loop[uv].uv = (x / tile, z / tile)
                elif ax >= az:
                    loop[uv].uv = (z / tile, y / tile)
                else:
                    loop[uv].uv = (x / tile, y / tile)

    def build(self, smooth=False, to_blender=True):
        if to_blender:
            bmesh.ops.transform(self.bm, matrix=TO_BL, verts=self.bm.verts)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        obj = bpy.data.objects.new(self.name, me)
        if self.coll:
            self.coll.objects.link(obj)
        return obj


# ── 도형 (웹 좌표, 원점 중심) ─────────────────────────────────
def box(w, h, d):
    return lambda bm: bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((w, h, d, 1)))


def cyl(rt, rb, h, seg=24):
    """세로(웹 Y축) 원통/원뿔대. rt=윗반지름, rb=아랫반지름"""
    return lambda bm: bmesh.ops.create_cone(
        bm, cap_ends=True, segments=seg, radius1=rb, radius2=rt, depth=h,
        matrix=Matrix.Rotation(-PI / 2, 4, 'X'))


def bevel_box(w, h, d, amount=0.02, segments=2):
    def build(bm):
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((w, h, d, 1)))
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=amount, segments=segments, affect='EDGES', profile=0.5)
    return build


def plane(w, h):
    """XY 평면(+z 를 바라봄), UV 0~1 — 화면·그래픽용"""
    return lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True,
                                            matrix=Matrix.Diagonal((w, h, 1, 1)))


def sphere(r, subdiv=2):
    return lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)


def tube(a, b, r, seg=8, caps=False):
    """a→b 를 잇는 원통 (웹 좌표 Vector). (build, matrix) 를 돌려준다"""
    d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    m = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
    return (lambda bm: bmesh.ops.create_cone(bm, cap_ends=caps, segments=seg, radius1=r, radius2=r,
                                             depth=d.length)), m


def ring_segment(r0, r1, a0, a1, h, seg=6):
    """두께 h 의 부채꼴 조각 (바닥 y=0, 윗면 y=h)"""
    def build(bm):
        angles = [a0 + (a1 - a0) * i / seg for i in range(seg + 1)]
        outer_t = [bm.verts.new((math.cos(a) * r1, h, math.sin(a) * r1)) for a in angles]
        inner_t = [bm.verts.new((math.cos(a) * r0, h, math.sin(a) * r0)) for a in angles]
        outer_b = [bm.verts.new((v.co.x, 0, v.co.z)) for v in outer_t]
        inner_b = [bm.verts.new((v.co.x, 0, v.co.z)) for v in inner_t]
        for i in range(seg):
            bm.faces.new((inner_t[i], inner_t[i + 1], outer_t[i + 1], outer_t[i]))
            bm.faces.new((outer_b[i], outer_b[i + 1], inner_b[i + 1], inner_b[i]))
            bm.faces.new((outer_t[i], outer_t[i + 1], outer_b[i + 1], outer_b[i]))
            bm.faces.new((inner_b[i], inner_b[i + 1], inner_t[i + 1], inner_t[i]))
        bm.faces.new((inner_t[0], outer_t[0], outer_b[0], inner_b[0]))
        bm.faces.new((outer_t[-1], inner_t[-1], inner_b[-1], outer_b[-1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return build


def cloth_skirt(r_top, r_bottom, h, folds=14, depth=0.035, seg=96, rings=8):
    """아래로 갈수록 퍼지고 주름이 잡히는 천 (원점 = 높이 중앙)"""
    def build(bm):
        verts = []
        for j in range(rings + 1):
            t = j / rings
            y = h / 2 - t * h
            r = r_top + (r_bottom - r_top) * (t ** 1.6)
            row = []
            for i in range(seg):
                a = i / seg * 2 * PI
                rr = r + depth * (t ** 1.3) * math.sin(folds * a + 0.3 * math.sin(3 * a))
                row.append(bm.verts.new((math.cos(a) * rr, y, math.sin(a) * rr)))
            verts.append(row)
        for j in range(rings):
            for i in range(seg):
                a, b = verts[j][i], verts[j][(i + 1) % seg]
                c, d = verts[j + 1][(i + 1) % seg], verts[j + 1][i]
                bm.faces.new((a, d, c, b))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)   # 윗면은 열어 둔다 (테이블 윗판이 덮음)
    return build


def gable_skin(width, slope, sag=0.12, seg_x=40, seg_y=8):
    """지붕 막: 가운데가 살짝 처진 평면 (로컬: x 폭, z 경사 방향)"""
    def build(bm):
        grid = []
        for j in range(seg_y + 1):
            row = []
            for i in range(seg_x + 1):
                u, v = i / seg_x, j / seg_y
                x = (u - 0.5) * width
                z = (v - 0.5) * slope
                y = -sag * math.sin(PI * v) * (0.6 + 0.4 * abs(math.sin(PI * u * 4)))
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        for j in range(seg_y):
            for i in range(seg_x):
                bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    return build


# ── 조명 / 카메라 ──────────────────────────────────────────────
def light(coll, name, kind, pos, target=None, energy=1000, color=(1, 1, 1), size=0.5, spot=0.6, blend=0.4):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if kind == 'AREA':
        data.size = size
    elif kind == 'SPOT':
        data.spot_size = spot
        data.spot_blend = blend
        data.shadow_soft_size = size
    else:
        data.shadow_soft_size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = TO_BL @ Vector(pos)
    if target:
        d = (TO_BL @ Vector(target)) - obj.location
        obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(obj)
    return obj


def camera(coll, name, pos, target, fov):
    data = bpy.data.cameras.new(name)
    data.sensor_fit = 'VERTICAL'
    data.angle = math.radians(fov)
    data.clip_end = 2000
    obj = bpy.data.objects.new(name, data)
    obj.location = TO_BL @ Vector(pos)
    d = (TO_BL @ Vector(target)) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(obj)
    return obj


def world_hdri(path, strength=0.5):
    world = bpy.data.worlds.new('world')
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    env = nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(path, check_existing=True)
    bg = nodes['Background']
    bg.inputs['Strength'].default_value = strength
    links.new(env.outputs['Color'], bg.inputs['Color'])
    bpy.context.scene.world = world
    return world


def mesh_source(obj):
    """Blender 오브젝트의 메시를 Assembly.add 에 넣을 수 있는 도형으로 (웹 좌표, UV·재질 번호 유지)"""
    def build(bm):
        me = obj.data
        bm.from_mesh(me)
        bmesh.ops.transform(bm, matrix=TO_WEB @ obj.matrix_world, verts=bm.verts)
    return build


def instance(src, coll, name, web_matrix):
    """메시를 공유하는 복제 (웹 좌표 변환을 Blender 로 옮겨 적용)"""
    inst = src.copy()
    inst.name = name
    inst.matrix_world = TO_BL @ web_matrix @ TO_WEB @ src.matrix_world
    coll.objects.link(inst)
    return inst


def texturize_all(default='metal_plate', strength=0.35, rough=0.06, skip=()):
    """씬에 **텍스처가 하나도 안 붙은 재질**이 남지 않게 마감한다.

    내려받은 외부 모델(glTF)의 재질처럼 우리가 material() 로 안 만든 것들은
    단색으로 남아 평평해 보인다. 이미지든 절차적 노드든 아무 질감도 없는 재질에
    노멀(요철)과 거칠기 흔들림을 채운다. 색은 건드리지 않는다.

    씬 스크립트 **맨 끝**(어셈블리 build 뒤)에서 한 번 부른다.
    """
    TEXN = ('TEX_IMAGE', 'TEX_WAVE', 'TEX_NOISE', 'TEX_VORONOI', 'TEX_MUSGRAVE',
            'TEX_MAGIC', 'TEX_CHECKER', 'TEX_BRICK', 'TEX_GRADIENT')
    used = set()
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        for m in ob.data.materials:
            if m:
                used.add(m.name)
    filled = []
    for name in sorted(used):
        m = bpy.data.materials.get(name)
        if not m or not m.use_nodes or name in skip:
            continue
        nodes, links = m.node_tree.nodes, m.node_tree.links
        if any(n.type in TEXN for n in nodes):
            continue
        bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf:
            continue
        n = nodes.new('ShaderNodeTexImage')
        n.image = image(f'{TEX}/{default}_nor.jpg', 'Non-Color')
        nm = nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = strength
        links.new(n.outputs['Color'], nm.inputs['Color'])
        links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
        if rough and not bsdf.inputs['Roughness'].is_linked:
            r0 = bsdf.inputs['Roughness'].default_value
            d_ = nodes.new('ShaderNodeTexImage')
            d_.image = image(f'{TEX}/{default}_diff.jpg', 'Non-Color')
            mr = nodes.new('ShaderNodeMapRange')
            mr.inputs['To Min'].default_value = max(0.0, r0 - rough)
            mr.inputs['To Max'].default_value = min(1.0, r0 + rough)
            links.new(d_.outputs['Color'], mr.inputs['Value'])
            links.new(mr.outputs['Result'], bsdf.inputs['Roughness'])
        # 웹도 라이트맵 없이 색만 쓰면 평평하다. 같은 텍스처를 디퓨즈로 넘기고
        # 밝기만큼 색을 올려 둔다 (material() 의 bump 와 같은 규칙).
        w = m.get('web')
        if w is not None and not w.get('tex') and not w.get('image') and not w.get('keep'):
            mu = tex_mean(default)
            lm = max(0.03, 0.2126 * mu[0] + 0.7152 * mu[1] + 0.0722 * mu[2])
            col = list(w.get('color') or [1, 1, 1])
            w['tex'] = default
            w['color'] = [min(6.0, c / lm) for c in col]
            m['web'] = dict(w)
        filled.append(name)
    print(f'texturize_all: 단색으로 남아 있던 재질 {len(filled)} 개 채움 {filled if filled else ""}')
    return filled
