"""외부 모델(Objaverse · Poly Haven, CC BY / CC0)을 장면에 쓸 수 있게 불러온다

load(uid, height=…) → SOURCES 컬렉션의 한 오브젝트 (여러 메시를 합치고, 실제 크기로 맞추고,
바닥 가운데를 원점으로). 재질은 모델 원래 것을 쓰고 웹에서도 그대로 쓰도록 web.keep 표시.
출처·저작자는 CREDITS.md 에 적는다.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

DIR = '/Users/hare/Documents/큐비크스홈페이지/assets-src/models/objaverse'


def _mark(m):
    """웹에서 원래 재질(텍스처 포함)을 그대로 쓰라는 표시"""
    if 'web' in m:
        return
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.use_nodes else None
    col = list(bsdf.inputs['Base Color'].default_value)[:3] if bsdf else [0.8, 0.8, 0.8]
    rough = bsdf.inputs['Roughness'].default_value if bsdf else 0.6
    metal = bsdf.inputs['Metallic'].default_value if bsdf else 0.0
    m['web'] = {'tex': '', 'color': col, 'rough': rough, 'metal': metal, 'emit': False, 'emitColor': [1, 1, 1],
                'emitStrength': 0.0, 'image': '', 'transmission': 0.0, 'alpha': False, 'keep': True}


def load(uid, name, height=None, width=None, rot_z=0.0, rot_x=0.0, decimate=None, coll=None, materials=None, parts=None):
    """height/width(m) 중 하나로 크기를 맞춘다. rot_z 는 Blender Z 축 회전(라디안).
    materials: 원래 재질 대신 쓸 재질 목록(순서대로) 또는 하나"""
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    before = set(bpy.data.objects)
    path = f'{DIR}/{uid}.glb'
    import os
    if not os.path.exists(path):   # Poly Haven 모델 (assets-src/models/<id>/<id>_1k.gltf)
        path = f'{DIR}/../{uid}/{uid}_1k.gltf'
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    bm = bmesh.new()
    mats = []
    meshes = sorted([o for o in new if o.type == 'MESH'], key=lambda o: o.name)
    for n, o in enumerate(meshes):
        if parts is not None and n not in parts:
            continue
        tmp = bmesh.new()
        tmp.from_mesh(o.data)
        tmp.transform(o.matrix_world)
        # 재질 번호를 합친 목록 기준으로
        local = [m for m in o.data.materials]
        for f in tmp.faces:
            m = local[f.material_index] if local else None
            if m not in mats:
                mats.append(m)
            f.material_index = mats.index(m)
        me = bpy.data.meshes.new('t')
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bm.transform(Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Rotation(rot_x, 4, 'X'))
    xs, ys, zs = zip(*[v.co[:] for v in bm.verts])
    size = Vector((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    k = height / size.z if height else (width / max(size.x, size.y) if width else 1.0)
    bm.transform(Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if materials is not None:
        mats = list(materials) if isinstance(materials, (list, tuple)) else [materials] * max(1, len(mats))
    for m in mats:
        me.materials.append(m)
        if m is not None and materials is None:
            _mark(m)
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)   # 모디파이어 평가를 위해 보이는 곳에서 먼저
    if decimate:
        mod = obj.modifiers.new('dec', 'DECIMATE')
        mod.ratio = decimate
        dg = bpy.context.evaluated_depsgraph_get()
        bpy.context.view_layer.update()
        new_me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
        old = obj.data
        obj.modifiers.clear()
        obj.data = new_me
        bpy.data.meshes.remove(old)
    for p in obj.data.polygons:
        p.use_smooth = True
    if coll is not None:
        bpy.context.scene.collection.objects.unlink(obj)
        coll.objects.link(obj)
    print('prop', name, len(obj.data.polygons), 'faces')
    return obj
