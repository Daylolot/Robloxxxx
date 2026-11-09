from pathlib import Path
import bpy, json
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'work/ceiling_worker_v18/assets/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
bpy.ops.wm.open_mainfile(filepath=str(p))
data=[]
for o in bpy.data.objects:
    row={'name':o.name,'type':o.type,'location':list(o.location),'dimensions':list(o.dimensions),'matrix':[list(r)for r in o.matrix_world],'groups':[g.name for g in o.vertex_groups]}
    if o.type=='MESH':
        row.update(vertices=len(o.data.vertices),faces=len(o.data.polygons),materials=[m.name if m else None for m in o.data.materials],modifiers=[(m.name,m.type)for m in o.modifiers],bounds=[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)]for i in range(3)] if o.data.vertices else [])
    data.append(row)
(ROOT/'work/ceiling_worker_v18/asset_inventory.json').write_text(json.dumps(data,indent=2))
print('ASSET_INVENTORY',json.dumps(data),flush=True)
