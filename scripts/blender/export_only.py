"""GLB 만 다시 내보낸다 — **라이트맵은 절대 다시 굽지 않는다**.

  python3 scripts/blender/bmcp.py exec scripts/blender/export_only.py

bmcp.py 의 exec 은 스크립트 경로 하나만 받는다. 그동안 써 온
  bmcp.py exec .../bake.py --pre "BAKE = {... 'export_only': True}"
의 --pre 는 **그냥 무시**되고 있었고, 그래서 배포할 때마다 256 샘플 베이크가
통째로 다시 돌고 라이트맵이 새로 구워져 올라갔다. 그 사고를 막으려고 둔 파일.
"""
BAKE = {'name': 'apec_stage', 'export_only': True}
with open('/Users/hare/Documents/큐비크스홈페이지/scripts/blender/bake.py', encoding='utf-8') as _f:
    exec(compile(_f.read(), 'bake.py', 'exec'))
