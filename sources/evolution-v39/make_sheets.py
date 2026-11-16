"""Contact sheets from studio_inspect_objects.py frames: one PNG per model, 5x2 grid of its 10 views.
Usage: python3 sources/evolution-v39/make_sheets.py <frames_dir>   (writes <frames_dir>/sheets/<kind>_<n>.png)"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

src = Path(sys.argv[1])
meta = json.loads((src / "meta.json").read_text())
out = src / "sheets"; out.mkdir(exist_ok=True)
W, H = 560, 330
for entry in meta:
    sheet = Image.new("RGB", (W * 5, H * 2), (18, 18, 20))
    draw = ImageDraw.Draw(sheet)
    for k, v in enumerate(entry["views"]):
        x, y = (k % 5) * W, (k // 5) * H
        if v is None:
            draw.text((x + 12, y + 12), f"view {k}: blocked", fill=(200, 120, 120))
            continue
        im = Image.open(src / v["file"]).convert("RGB")
        # crop the 3D viewport out of the Studio window chrome: keep the central area
        w, h = im.size
        im = im.crop((int(w * 0.08), int(h * 0.12), int(w * 0.92), int(h * 0.92))).resize((W - 4, H - 4))
        sheet.paste(im, (x + 2, y + 2))
        draw.rectangle((x + 4, y + 4, x + 150, y + 22), fill=(0, 0, 0))
        draw.text((x + 8, y + 7), f"{entry['kind']}#{entry['n']} v{k} az{v['az']} el{v['el']}", fill=(255, 255, 255))
    sheet.save(out / f"{entry['kind']}_{entry['n']}.png")
print("sheets:", len(meta))
