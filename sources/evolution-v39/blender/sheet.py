"""Contact sheet of the 10 Blender preview views of one item. Usage: python3 sheet.py <out_dir> <ItemName>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, name = Path(sys.argv[1]), sys.argv[2]
ims = [Image.open(out / "previews" / f"{name}_v{k}.png").convert("RGB") for k in range(10)]
w, h = ims[0].size
sheet = Image.new("RGB", (w * 5, h * 2))
d = ImageDraw.Draw(sheet)
for k, im in enumerate(ims):
    sheet.paste(im, ((k % 5) * w, (k // 5) * h))
    d.rectangle(((k % 5) * w + 4, (k // 5) * h + 4, (k % 5) * w + 70, (k // 5) * h + 22), fill=(0, 0, 0))
    d.text(((k % 5) * w + 8, (k // 5) * h + 7), f"{name} v{k}", fill=(255, 255, 255))
(out / "sheets").mkdir(exist_ok=True)
sheet.save(out / "sheets" / f"{name}.png")
