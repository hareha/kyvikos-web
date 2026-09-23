"""사진 ↔ 렌더 대조표: python3 scripts/blender/compare_sheet.py <out.jpg> <photo> <render> [<photo> <render> ...]"""
import sys
from PIL import Image, ImageDraw, ImageFont

out, pairs = sys.argv[1], sys.argv[2:]
W, H = 760, 428
rows = len(pairs) // 2
sheet = Image.new('RGB', (W * 2 + 30, rows * (H + 34) + 10), (18, 18, 20))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc', 20, index=6)
for r in range(rows):
    for c in range(2):
        p = pairs[r * 2 + c]
        im = Image.open(p).convert('RGB')
        im.thumbnail((W, H))
        x, y = 10 + c * (W + 10), 10 + r * (H + 34)
        sheet.paste(im, (x + (W - im.width) // 2, y + 26 + (H - im.height) // 2))
        d.text((x, y), ('사진 · ' if c == 0 else '모델 렌더 · ') + p.rsplit('/', 1)[-1], fill=(220, 220, 220), font=font)
sheet.save(out, quality=88)
print('saved', out)
