"""KONTUR plants and desk decor as colour-grouped meshes (one mesh per quantised colour) for Roblox upload.
Reuses the generators of sources/visual-v36/blender/plants_v36.py (fig, lily, monstera, vase, bookstack, bookrow, openbook), whose per-vertex
colours are quantised per triangle into <= 24 colour groups; every group becomes <Item>_plant_<hex>.
Run: Blender -b --python plants_hero.py -- <out_dir> [fig,lily,...] [--norender]"""
import sys, math, random
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

_here = Path(__file__).resolve().parent
_k = (_here / "interior_hero.py").read_text()
exec(compile(_k[:_k.index("# ---------------------------------------------------------------- items")], "kit_head", "exec"), globals())
exec(compile(_k[_k.index("import struct, base64"):_k.index("def main():")], "kit_tail", "exec"), globals())
# plants generators live in their own namespace (they define their own lathe/tube/Builder)
_ps = (_here.parent.parent / "visual-v36" / "blender" / "plants_v36.py").read_text()
P = {"__name__": "plants_v36"}
exec(compile(_ps[:_ps.rindex("\nmain()")], "plants_v36", "exec"), P)

MATS["plant"] = ("#4a7a4a", .6, 0, 0, 0)
NAMES = {"fig": "PlantFig", "lily": "PlantLily", "monstera": "PlantMonstera", "vase": "DecorVase", "bookstack": "DecorBookStack",
         "bookrow": "DecorBookRow", "openbook": "DecorOpenBook"}
STEP = 16


def quant(c):
    return tuple(min(255, (int(round(x * 255)) // STEP) * STEP + STEP // 2) for x in c[:3])


def build_item(key):
    B = P[key]()
    it = Item(NAMES[key])
    groups = {}
    for tri in B.t:
        cols = [B.c[i] for i in tri]
        avg = tuple(sum(c[k] for c in cols) / 3 for k in range(3))
        groups.setdefault(quant(avg), []).append(tri)
    # merge the smallest groups into the nearest bigger ones until <= 24 remain
    while len(groups) > 24:
        small = min(groups, key=lambda k: len(groups[k]))
        tris = groups.pop(small)
        near = min(groups, key=lambda k: sum((k[i] - small[i]) ** 2 for i in range(3)))
        groups[near].extend(tris)
    for qc, tris in groups.items():
        bm = bmesh.new()
        vmap = {}
        for tri in tris:
            ids = []
            for i in tri:
                if i not in vmap:
                    vmap[i] = bm.verts.new(B.v[i])
                ids.append(vmap[i])
            try:
                bm.faces.new(ids)
            except ValueError:
                pass
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        hexc_ = "#%02x%02x%02x" % qc
        it.put(bm, "plant", hexc_)
    return it


def main():
    names = WANT or list(NAMES)
    for n in names:
        sc = setup_scene()
        it = build_item(n)
        objs = finish(it)
        stats(it.name, objs)
        if RENDER:
            render_views(sc, it.name, objs)
        export(it.name, objs)
    print("DONE", flush=True)


main()
