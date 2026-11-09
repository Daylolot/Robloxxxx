"""Verify the saved animation and that all media are packed in the scene."""
import json
from pathlib import Path
import sys

import bpy

out=Path(sys.argv[sys.argv.index("--")+1])
report=json.loads((out/"Motion_Check.json").read_text())
scene=bpy.context.scene
fps=report["fps"]
rows=report["sheets"]
assert len(rows)==60 and len({row["packet"] for row in rows})==5
assert len({row["stir"] for row in rows})==60
assert len({row["peel"] for row in rows})==60
assert all(row["positions"]>110 and row["contactSamples"]>80 for row in rows)
assert all(not row["intersections"] and row["minGapStuds"]>=.00199 for row in rows)
assert abs(report["stirAt"]-report["readAt"]-5)<1e-8
assert abs(min(row["stir"] for row in rows)-report["stirAt"])<1e-8
pages=[bpy.data.objects[row["sheet"]] for row in rows]
scene.frame_set(1+round((report["stirAt"]-.15)*fps))
rest=[obj.location.copy() for obj in pages]
assert all(abs(obj.data.shape_keys.key_blocks[1].value)<1e-6 for obj in pages)
scene.frame_set(1+round((report["stirAt"]+.29)*fps))
assert pages[0].data.shape_keys.key_blocks[1].value>.1
assert (pages[0].location-rest[0]).length<.022
scene.frame_set(1+round(19*fps))
now=[obj.location.copy() for obj in pages]
spans=[max(v[i] for v in now)-min(v[i] for v in now) for i in range(3)]
assert spans[0]>32 and spans[1]>36
levels={"low":sum(1.45<p.z<3.1 for p in now),"eye":sum(4.25<p.z<6 for p in now),
        "high":sum(7.25<p.z<8.55 for p in now)}
assert levels["low"]>=6 and levels["eye"]>=8 and levels["high"]>=12, levels
assert all((a-b).length>2.3 for a,b in zip(rest,now))
scene.frame_set(1+round(19.5*fps))
assert min((obj.location-pos).length for obj,pos in zip(pages,now))>.025
assert all(img.packed_file for img in bpy.data.images if img.source=="FILE")
assert len(bpy.data.sounds)==1 and all(sound.packed_file for sound in bpy.data.sounds)
assert not any(font.filepath.endswith("Arial.ttf") for font in bpy.data.fonts)
report["reopened"]={"spanStudsAt19s":[round(x,3) for x in spans],
                    "paperByHeightAt19s":levels,
                    "packedPageTextures":sum(1 for img in bpy.data.images if img.source=="FILE"),
                    "packedSound":True,"minSampledContacts":min(row["contactSamples"] for row in rows),
                    "checkingIntervalFrames":2,"verticesTestedPerSample":15}
(out/"Motion_Check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(report["reopened"],flush=True)
