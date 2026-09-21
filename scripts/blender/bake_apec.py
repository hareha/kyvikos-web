"""APEC 무대 구역 — 조명 베이크 + GLB 내보내기 (Blender MCP 로 실행)

  앞에 BAKE = {'samples': 256} 를 붙여 보낸다.

1. 정적 구조물에 두 번째 UV('Lightmap')를 펼친다
2. Cycles 로 조명(직접광+간접광, 색 제외)을 라이트맵에 굽는다
3. 8비트 sRGB PNG 로 저장 (밝은 값은 scale 로 나눠 담고, 웹에서 다시 곱한다)
4. 웹에 필요한 오브젝트를 GLB 로 내보낸다
"""
import json
import math
import os

import bpy
import numpy as np

CFG = globals().get('BAKE', {})
ROOT = '/Users/hare/Documents/큐비크스홈페이지'
OUT = f'{ROOT}/assets-src/blender'
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = CFG.get('samples', 256)
bake = scene.render.bake
bake.use_pass_direct = True
bake.use_pass_indirect = True
bake.use_pass_color = False
bake.margin = 8
bake.margin_type = 'EXTEND'

GROUPS = {
    'ground': (['ground'], CFG.get('ground_size', 4096)),
    'objects': (['stage', 'roof', 'tables', 'heaters', 'sign', 'lanterns', 'backstage'], CFG.get('objects_size', 4096)),
    'pagoda': (['pagoda'], CFG.get('pagoda_size', 4096)),
    'halls': (['halls', 'garden', 'pines'], CFG.get('halls_size', 4096)),
    'yeonsu_ne': (['yeonsu_ne'], CFG.get('yeonsu_size', 4096)),
    'yeonsu_nw': (['yeonsu_nw'], CFG.get('yeonsu_size', 4096)),
}


def view3d_override():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                region = next(r for r in area.regions if r.type == 'WINDOW')
                return {'window': window, 'screen': window.screen, 'area': area, 'region': region}
    return {}


def select_only(objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def unwrap(objs):
    for o in objs:
        uvs = o.data.uv_layers
        lm = uvs.get('Lightmap') or uvs.new(name='Lightmap')
        uvs['UVMap'].active_render = True
        uvs.active = lm
    with bpy.context.temp_override(**view3d_override()):
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        select_only(objs)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, area_weight=0.0,
                                 scale_to_bounds=False)
        bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
        bpy.ops.object.mode_set(mode='OBJECT')


def bake_group(name, objs, size):
    img = bpy.data.images.get(f'LM_{name}')
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(f'LM_{name}', size, size, float_buffer=True, alpha=False)
    img.colorspace_settings.name = 'Linear Rec.709'
    targets = []
    for m in {m for o in objs for m in o.data.materials if m}:
        node = m.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = img
        m.node_tree.nodes.active = node
        targets.append((m, node))
    with bpy.context.temp_override(**view3d_override()):
        select_only(objs)
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'}, margin=8, use_clear=True,
                            target='IMAGE_TEXTURES')
    for m, node in targets:
        m.node_tree.nodes.remove(node)

    # 선형 float → 8비트 sRGB. 상위 0.5% 밝기가 0.92 에 오도록 나눠 담는다
    px = np.empty(size * size * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    rgb = px.reshape(size, size, 4)[..., :3]
    peak = float(np.percentile(rgb.max(axis=2), 99.5))
    scale = max(peak, 1e-4) / 0.92
    enc = np.clip(rgb / scale, 0.0, 1.0)
    enc = np.where(enc <= 0.0031308, enc * 12.92, 1.055 * np.power(enc, 1 / 2.4) - 0.055)
    out = np.ones((size, size, 4), dtype=np.float32)
    out[..., :3] = enc
    png = bpy.data.images.new(f'LM_{name}_8', size, size, alpha=False)
    png.colorspace_settings.name = 'sRGB'
    png.pixels.foreach_set(out.ravel())
    png.filepath_raw = f'{OUT}/lightmap_{name}.png'
    png.file_format = 'PNG'
    png.save()
    bpy.data.images.remove(png)
    return {'scale': scale, 'size': size, 'mean': float(rgb.mean())}


# 렌더 전용(주변 바닥·나무)은 베이크에서 제외
hidden = [o for o in bpy.data.collections['RENDER_ONLY'].objects]
for o in hidden:
    o.hide_render = True

MANIFEST = f'{OUT}/apec_stage.json'
if CFG.get('export_only'):
    with open(MANIFEST) as f:
        manifest = json.load(f)
else:
    manifest = {'groups': {}, 'materials': {}, 'objects': {}}
    for name, (names, size) in GROUPS.items():
        objs = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
        unwrap(objs)
        manifest['groups'][name] = bake_group(name, objs, size)
        for o in objs:
            manifest['objects'][o.name] = name
            for m in o.data.materials:
                manifest['materials'][m.name] = name
        print('baked', name, manifest['groups'][name])

for o in hidden:
    o.hide_render = False

# ── GLB 내보내기 ──────────────────────────────────────────────
# glTF 내보내기는 재질이 쓰는 UV 만 내보낸다. 라이트맵을 '차폐(occlusion)' 슬롯에
# 두 번째 UV 로 연결해 TEXCOORD_1 이 함께 나가게 한다 (웹에서는 이 UV 를 라이트맵에 쓴다).
def gltf_output_group():
    group = bpy.data.node_groups.get('glTF Material Output')
    if group is None:
        group = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
        group.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    return group


placeholder = bpy.data.images.get('LM_placeholder') or bpy.data.images.new('LM_placeholder', 4, 4, alpha=False)
placeholder.filepath_raw = f'{OUT}/lm_placeholder.png'
placeholder.file_format = 'PNG'
placeholder.save()

lm_nodes = []
for mat_name, group_name in manifest['materials'].items():
    m = bpy.data.materials.get(mat_name)
    if m is None:
        continue
    nodes, links = m.node_tree.nodes, m.node_tree.links
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'Lightmap'
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = placeholder  # 실제 라이트맵은 따로 배포하므로 GLB 에는 작은 이미지만
    sep = nodes.new('ShaderNodeSeparateColor')
    out = nodes.new('ShaderNodeGroup')
    out.node_tree = gltf_output_group()
    links.new(uv.outputs['UV'], tex.inputs['Vector'])
    links.new(tex.outputs['Color'], sep.inputs['Color'])
    links.new(sep.outputs[0], out.inputs['Occlusion'])
    lm_nodes.append((m, [uv, tex, sep, out]))

export = [o for c in ('STATIC', 'DYNAMIC', 'EMISSIVE') for o in bpy.data.collections[c].objects]
with bpy.context.temp_override(**view3d_override()):
    select_only(export)
    bpy.ops.export_scene.gltf(
        filepath=f'{OUT}/apec_stage.glb',
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_gpu_instances=True,
        export_extras=True,
        export_cameras=False,
        export_lights=False,
    )

for m, nodes in lm_nodes:
    for n in nodes:
        m.node_tree.nodes.remove(n)

with open(MANIFEST, 'w') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print('exported', len(export), 'objects')
