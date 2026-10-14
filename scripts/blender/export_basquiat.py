"""바스키아 GLB 만 다시 내보낸다 — **라이트맵은 절대 다시 굽지 않는다**.

  python3 scripts/blender/bmcp.py exec scripts/blender/basquiat_scene.py
  python3 scripts/blender/bmcp.py exec scripts/blender/export_basquiat.py
  node scripts/blender/publish.mjs basquiat

export_only.py(=APEC) 와 같은 이유로 둔 파일. bmcp.py 의 exec 은 스크립트 경로
하나만 받기 때문에 --pre 로 BAKE 를 넘기면 그냥 무시되고 256 샘플 베이크가
통째로 다시 돈다.

GROUPS 는 2026-09-21 베이크 때 쓴 것과 같다. 그때 'lobby' 였던 어셈블리가
지금은 'foyer' 라서 이름만 바꿔 넣었다 (bake.py 가 매니페스트의 오브젝트-그룹
대응표를 지금 씬 기준으로 다시 만들기 때문에 여기 빠지면 웹에서 그 덩어리의
텍스처가 통째로 안 붙는다).
"""
BAKE = {
    'name': 'basquiat',
    'export_only': True,
    'groups': {
        'floor': (['floor'], 4096),
        'hall': (['ceiling', 'hall', 'foyer'], 4096),
        'walls': (['walls'], 4096),
        'works': (['works'], 4096),
    },
}
with open('/Users/hare/Documents/큐비크스홈페이지/scripts/blender/bake.py', encoding='utf-8') as _f:
    exec(compile(_f.read(), 'bake.py', 'exec'))
