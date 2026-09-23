"""LOCAL POWER 처럼 전시/쇼 두 상태가 있는 장면의 카메라별 렌더.
  RENDER = {'cams': [...], 'show': ['cam_runway', ...], 'samples': 20, 'scale': 40, 'tag': 'x'} 를 앞에 붙여 보낸다.
쇼 카메라에서는 showday* 만 보이고 expo·expo_emit·outfit_* 는 숨긴다 (웹 localpower/scene.js onView 와 같은 규칙)."""
import bpy

cfg = globals().get('RENDER', {})
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = cfg.get('samples', 32)
scene.cycles.use_denoising = True
scene.render.resolution_percentage = cfg.get('scale', 50)
scene.render.image_settings.file_format = 'JPEG'


def phase(show):
    for o in bpy.data.objects:
        if o.name.startswith('showday'):
            o.hide_render = not show
        elif o.name in ('expo', 'expo_emit') or o.name.startswith('outfit_'):
            o.hide_render = show


out = []
for name in cfg.get('cams', []):
    phase(name in cfg.get('show', ()))
    scene.camera = bpy.data.objects[name]
    path = f"/Users/hare/Documents/큐비크스홈페이지/assets-src/renders/{cfg.get('tag', 'preview')}_{name}.jpg"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    out.append(path)
phase(False)
print('rendered:', out)
