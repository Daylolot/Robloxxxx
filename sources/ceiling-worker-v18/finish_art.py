from pathlib import Path
import bpy,math,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18';FILE=OUT/'Ceiling_Office_Character_Study_v18.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE));scene=bpy.context.scene
body=bpy.data.objects['Worker / face neck forearms and hands']
body.shape_key_add(name='Basis');blink=body.shape_key_add(name='Natural upper eyelid blink')
for v,p in zip(body.data.vertices,blink.data):
    x,y,z=v.co
    if y>-.098 or z<1.553 or z>1.594:continue
    dx=abs(x)-.03288;dz=z-1.5737066
    if abs(dx)>.018 or abs(dz)>.017:continue
    w=max(0,1-(dx/.018)**2)**.35*max(0,1-(dz/.017)**2)**.6
    if dz<0:w*=.24
    p.co.z=z+(1.5742-z)*w
    target=-.12182286-math.sqrt(max(.0123**2-dx**2,0))-.0005
    p.co.y=y+(target-y)*w
for frame,value in [(1,0),(53,0),(56,1),(59,0),(151,0),(154,1),(157,0),(240,0)]:blink.value=value;blink.keyframe_insert('value',frame=frame)
lamp=bpy.data.lights.get('Yellow desk light')
if lamp:
    for frame,power in [(1,20),(171,20),(173,12),(175,20),(240,20)]:lamp.energy=power;lamp.keyframe_insert('energy',frame=frame)
scene.frame_set(120)
checks=json.loads((OUT/'Hand_Contact_Check.json').read_text())
assert all(c['pointsOverKeyboard']>0 and c['lowestHandMetres']>=c['keyCapsMetres']+.0005 for c in checks),checks
stats=[];dg=bpy.context.evaluated_depsgraph_get()
for name in ['Worker / face neck forearms and hands','Worker / tailored white cotton shirt','Worker / dark seated trousers','Worker / close combed hair cap']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
    stats.append({'object':name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles)})
    ev.to_mesh_clear()
audit={'stage':'Blender art study, not a finished playable anomaly','frames':240,'fps':24,'previewStates':['typing','pause','head follows','looks after departure','resumes'],
       'anatomy':'Blender Studio Human Base Meshes 1.4.1 / CC0; tailored clothing and office constructed locally',
       'geometry':stats,'externalLibraries':[str(l.filepath)for l in bpy.data.libraries],
       'minimumKeyClearanceMetres':min(c['lowestHandMetres']-c['keyCapsMetres']for c in checks),
       'pendingGameplay':['local mesh conversion and materials in Roblox','coffee, mouse, documents and chair animation polish','live player map','linked lamp and drawer','shared object drops and room reset','audio','single player and co-op acceptance'],
       'nativeMapsUnmodified':True,'robloxUploads':0}
(OUT/'Art_Stage_Check.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(FILE),compress=True)
print('ART_STAGE_READY',json.dumps(audit),flush=True)
