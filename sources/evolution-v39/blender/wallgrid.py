"""Ten-view contact sheet (5 x 2) of one wall item. Usage: python3 wallgrid.py <out_dir> <sheet.png> <ItemName>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, dest, name = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
ims = [Image.open(out / "previews" / f"{name}_w{k}.png").convert("RGB").resize((312, 240)) for k in range(10)]
sheet = Image.new("RGB", (312 * 5, 240 * 2))
d = ImageDraw.Draw(sheet)
for k, im in enumerate(ims):
    sheet.paste(im, ((k % 5) * 312, (k // 5) * 240))
    d.rectangle(((k % 5) * 312 + 3, (k // 5) * 240 + 3, (k % 5) * 312 + 90, (k // 5) * 240 + 18), fill=(0, 0, 0)); d.text(((k % 5) * 312 + 6, (k // 5) * 240 + 5), f"{name} v{k}", fill=(255, 255, 255))
sheet.save(dest)
