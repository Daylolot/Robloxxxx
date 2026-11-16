"""Лист 5x2 из десяти ракурсов предмета: python3 sheet10.py <out_dir> <Предмет> [ширина_ячейки]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, name = Path(sys.argv[1]), sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 560
frames = [Image.open(out / "previews" / f"{name}_v{k}.png").convert("RGB") for k in range(10)]
H = int(W * frames[0].size[1] / frames[0].size[0])
sheet = Image.new("RGB", (W * 5, H * 2))
dr = ImageDraw.Draw(sheet)
for k, im in enumerate(frames):
    sheet.paste(im.resize((W, H)), ((k % 5) * W, (k // 5) * H))
    dr.rectangle(((k % 5) * W + 4, (k // 5) * H + 4, (k % 5) * W + 130, (k // 5) * H + 22), fill=(0, 0, 0))
    dr.text(((k % 5) * W + 8, (k // 5) * H + 7), f"{name} v{k}", fill=(255, 255, 255))
(out / "sheets").mkdir(exist_ok=True)
dest = out / "sheets" / f"{name}_10views.jpg"
sheet.save(dest, quality=90)
print(dest)
