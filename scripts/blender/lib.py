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


def material(name, tex=None, color=(1, 1, 1), rough=0.8, metal=0.0, normal=1.0,
             emit=None, emit_strength=0.0, emit_image=None, image_base=None,
             transmission=0.0, sheen=0.0, coat=0.0, alpha=False):
    """Principled BSDF 재질. tex = Poly Haven 텍스처 id (디퓨즈 × color, 노멀)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    base = (*color, 1)
    if tex:
        t = nodes.new('ShaderNodeTexImage')
        t.image = image(f'{TEX}/{tex}_diff.jpg')
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        links.new(t.outputs['Color'], mix.inputs[6])
        mix.inputs[7].default_value = base
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
    m['web'] = {
        'tex': tex or '', 'color': list(color), 'rough': rough, 'metal': metal,
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
