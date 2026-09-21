"""카메라별 Cycles 렌더 (Blender MCP 로 실행)

  RENDER = {'cams': ['cam_vip'], 'samples': 32, 'scale': 50, 'tag': 'preview'} 를 앞에 붙여 보낸다.
"""
import bpy

cfg = globals().get('RENDER', {})
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = cfg.get('samples', 32)
scene.cycles.use_denoising = True
scene.render.resolution_percentage = cfg.get('scale', 50)
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 88

out = []
for name in cfg.get('cams', ['cam_vip']):
    scene.camera = bpy.data.objects[name]
    path = f"/Users/hare/Documents/큐비크스홈페이지/assets-src/renders/{cfg.get('tag', 'preview')}_{name}.jpg"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    out.append(path)
print('rendered:', out)
