from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/CeilingWorker_2026-11-08/Revision18/Ceiling_Office_Character_Study_v18.blend'))
scene=bpy.context.scene;scene.frame_set(120);rig=bpy.data.objects['OfficeWorker anatomical rig'];body=bpy.data.objects['Worker / face neck forearms and hands'];bpy.context.view_layer.update()
rows={'bones':{},'points':[]}
for m in body.modifiers:
 if m.type!='ARMATURE':m.show_viewport=False
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
rows['lowPoints']=[{'posed':list(v.co),'rest':list(body.data.vertices[v.index].co),'groups':[(body.vertex_groups[g.group].name,g.weight)for g in body.data.vertices[v.index].groups]}for v in sorted([v for v in me.vertices if -.647<v.co.y<-.503 and abs(v.co.x)<.22 and v.co.z>.65],key=lambda v:v.co.z)[:6]]
ev.to_mesh_clear()
base=bpy.data.objects['Anatomy working base']
rows['restSlices']=[{'z':z/100,'count':len(vs),'x':sum(v.co.x for v in vs)/len(vs),'y':sum(v.co.y for v in vs)/len(vs)}for z in range(74,121,4)if(vs:=[v for v in base.data.vertices if v.co.x>.27 and z/100<v.co.z<(z+4)/100])]
for name in ['upper_arm.L','forearm.L','hand.L']:
 b=rig.pose.bones[name];rows['bones'][name]={'matrix':[list(r)for r in b.matrix],'head':list(b.head),'tail':list(b.tail),'basis':[list(r)for r in b.matrix_basis]}
for v in sorted([v for v in body.data.vertices if v.co.x>.31 and v.co.z<.9],key=lambda v:v.co.z)[::35]:
 groups=[(body.vertex_groups[g.group].name,g.weight)for g in v.groups]
 rows['points'].append({'co':list(v.co),'groups':groups})
(ROOT/'work/ceiling_worker_v18/hand_weights.json').write_text(json.dumps(rows,indent=2))
print('WEIGHTS',json.dumps(rows))
