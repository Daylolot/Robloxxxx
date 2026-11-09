"""Check visible paper surfaces for intersections after they clear their packets."""
import json
from pathlib import Path
import sys
import bpy
from mathutils.bvhtree import BVHTree

out=Path(sys.argv[sys.argv.index("--")+1])
scene=bpy.context.scene
report=json.loads((out/"Motion_Check.json").read_text())
rows=report["sheets"]
sheets=[bpy.data.objects[row["sheet"]] for row in rows]
faces=[tuple(polygon.vertices) for polygon in sheets[0].data.polygons]
for obj in sheets:
    obj.modifiers[0].show_viewport=False
pairs={}
for frame in range(181,scene.frame_end+1,2):
    scene.frame_set(frame)
    time=(frame-1)/scene.render.fps
    dg=bpy.context.evaluated_depsgraph_get()
    vectors=[]
    for row,obj in zip(rows,sheets):
        if time<row["peel"]+1.15:
            vectors.append(None)
            continue
        evaluated=obj.evaluated_get(dg)
        vertices=[evaluated.matrix_world@v.co for v in evaluated.data.vertices]
        low=tuple(min(p[i] for p in vertices) for i in range(3))
        high=tuple(max(p[i] for p in vertices) for i in range(3))
        vectors.append((vertices,low,high))
    cache={}
    for i,a in enumerate(vectors):
        if a is None:
            continue
        av,al,ah=a
        for j in range(i+1,len(vectors)):
            b=vectors[j]
            if b is None:
                continue
            bv,bl,bh=b
            if not all(al[k]<bh[k] and bl[k]<ah[k] for k in range(3)):
                continue
            for index,verts in ((i,av),(j,bv)):
                if index not in cache:
                    cache[index]=BVHTree.FromPolygons(verts,faces,all_triangles=False)
            if cache[i].overlap(cache[j]):
                pairs.setdefault((i+1,j+1),[]).append(frame)
for pair,frames in sorted(pairs.items()):
    print(pair,frames)
print("Intersecting pairs",len(pairs),flush=True)
checks={"sheets":len(sheets),"startAfterPeelSeconds":1.15,"frameInterval":2,
        "intersectingPairs":[{"sheets":list(pair),"frames":frames} for pair,frames in sorted(pairs.items())]}
(out/"Paper_Overlap_Check.json").write_text(json.dumps(checks,indent=2)+"\n")
assert not pairs
