"""KONTUR wall decor (Blender, quality level 5): air conditioners, stains, cracks, peeling paint, pipes, panels, alarms, cameras, signs, vents, shelves.
Run: Blender -b --python wall_hero.py -- <out_dir> [item,item|all] [--norender] [--front]
Every item is modelled in wall coordinates (see wall_core.py): origin = item centre on the wall plane, front = -Z. Exported to <out_dir>/fbx/<Item>.fbx,
previews: wall backdrop, views from the front and two three-quarter angles (`_w0.._w3`)."""
import sys, math, random
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

_here = Path(__file__).resolve().parent
_src = (_here / "hub_hero.py").read_text()
_helpers_src = (_here / "interior_hero.py").read_text()
exec(compile(_helpers_src[:_helpers_src.index("# ---------------------------------------------------------------- items")], "interior_hero_head", "exec"), globals())
exec(compile(_helpers_src[_helpers_src.index("import struct, base64"):_helpers_src.index("def main():")], "interior_hero_tail", "exec"), globals())
_hub = (_here / "hub_hero.py").read_text()
exec(compile(_hub[_hub.index("MATS.update({"):_hub.index("def hazmat():")], "hub_helpers", "exec"), globals())
# hub_hero.py's own head defines tube()/torus(): load them
exec(compile(_src[_src.index("def tube("):_src.index("def hazmat():")], "hub_tube", "exec"), globals())

for _f in ("wall_core.py", "wall_a.py", "wall_b.py", "wall_c.py", "wall_d.py"):
    if (_here / _f).exists():
        exec(compile((_here / _f).read_text(), _f, "exec"), globals())

ITEMS = {}
for _n in ("ITEMS_A", "ITEMS_B", "ITEMS_C", "ITEMS_D"):
    ITEMS.update(globals().get(_n, {}))
VIEWS = [(0, 0), (34, 10), (-34, -8), (0, 60)]
# ten views of the frontal hemisphere (the back is the wall): straight, four side angles, from above, from below, two diagonal, one grazing
VIEWS10 = [(0, 0), (30, 8), (-30, 8), (60, 10), (-60, 10), (0, 42), (0, -36), (28, 30), (-28, -24), (80, 4)]


def main():
    names = WANT or list(ITEMS)
    front_only = "--front" in argv
    for n in names:
        sc = setup_scene()
        it = ITEMS[n]()
        objs = finish(it)
        flatten_decals(objs)
        stats(it.name, objs)
        if RENDER:
            if "--detail" in argv and globals().get("DETAILS", {}).get(n):
                render_wall(sc, it.name + "_d", objs, DETAILS[n])
            else:
                render_wall(sc, it.name, objs, VIEWS[:1] if front_only else (VIEWS10 if "--ten" in argv else VIEWS))
        export(it.name, objs)
    print("DONE", flush=True)


main()
