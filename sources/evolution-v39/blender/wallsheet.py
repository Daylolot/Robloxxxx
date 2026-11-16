"""Contact sheet of wall-item previews. Usage: python3 wallsheet.py <out_dir> <sheet.png> Name1 Name2 ... [--views=0,1,2]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, dest = Path(sys.argv[1]), Path(sys.argv[2])
names = [a for a in sys.argv[3:] if not a.startswith("--")]
views = [0, 1, 2, 3]
for a in sys.argv[3:]:
    if a.startswith("--views="):
        views = [int(v) for v in a[8:].split(",")]
rows = []
for n in names:
    ims = []
    for k in views:
        p = out / "previews" / f"{n}_w{k}.png"
        if p.exists():
            ims.append(Image.open(p).convert("RGB").resize((390, 300)))
    rows.append((n, ims))
w, h = 390, 300
sheet = Image.new("RGB", (w * len(views), h * len(rows)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for r, (n, ims) in enumerate(rows):
    for c, im in enumerate(ims):
        sheet.paste(im, (c * w, r * h))
    d.rectangle((4, r * h + 4, 150, r * h + 22), fill=(0, 0, 0)); d.text((8, r * h + 7), n, fill=(255, 255, 255))
dest.parent.mkdir(parents=True, exist_ok=True)
sheet.save(dest)
print("sheet", dest, sheet.size)

