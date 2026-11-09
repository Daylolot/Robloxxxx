from pathlib import Path
import bpy,math,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Ceiling_Office_Character_Study_v18.blend'))
scene=bpy.context.scene;scene.frame_set(1);cam=scene.camera
cam.location=(-1.8,-1.5,2.1);cam.rotation_euler=(Vector((-1.1,0,3.18))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=50
scene.render.resolution_x=1200;scene.render.resolution_y=900;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
rows=[]
for x,y in [(920,552),(927,544),(904,549),(990,560),(945,526),(930,535),(915,536)]:
    frame=cam.data.view_frame(scene=scene)
    v=frame[3]+(frame[0]-frame[3])*(x/1200)+(frame[2]-frame[3])*(y/900)
    direction=cam.matrix_world.to_3x3()@v.normalized();hit,loc,normal,index,obj,matrix=scene.ray_cast(dg,cam.location,direction)
    rows.append({'pixel':[x,y],'object':obj.name if obj else None,'location':list(loc)})
body=bpy.data.objects['Worker / face neck forearms and hands'];ev=body.evaluated_get(dg);me=ev.to_mesh()
rows.append({'skinPoseZ':[min(v.co.z for v in me.vertices),max(v.co.z for v in me.vertices)]});ev.to_mesh_clear()
me=body.evaluated_get(dg).to_mesh()
rows.append({'lowestActualSkinFaces':[list(f.center)for f in sorted(me.polygons,key=lambda f:f.center.z)[:5]],'skinObjects':[ob.name for ob in scene.objects if ob.type=='MESH' and any(m and m.name.startswith('Skin /')for m in ob.data.materials)]})
body.evaluated_get(dg).to_mesh_clear()
(ROOT/'work/ceiling_worker_v18/detail_identity.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
