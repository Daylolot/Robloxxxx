from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18';FILE=OUT/'Ceiling_Office_Character_Study_v18.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE));scene=bpy.context.scene;body=bpy.data.objects['Worker / face neck forearms and hands'];head=bpy.data.objects['Head attachment and gaze pivot']
dg=bpy.context.evaluated_depsgraph_get();hand=[]
for f in [1,17,36,60,84,120,180,225,240]:
    scene.frame_set(f);bpy.context.view_layer.update();ev=body.evaluated_get(dg);me=ev.to_mesh()
    pts=[v.co for v in me.vertices if -.665<v.co.y<-.49 and abs(v.co.x)<.225 and v.co.z>.65]
    hand.append({'frame':f,'pointsOverKeyboard':len(pts),'lowestHandMetres':min(v.z for v in pts),'keyCapsMetres':.796});ev.to_mesh_clear()
assert min(r['lowestHandMetres']for r in hand)>.7965
(OUT/'Hand_Contact_Check.json').write_text(json.dumps(hand,indent=2))
flags=[m.show_viewport for m in body.modifiers]
for m in body.modifiers:
    if m.type!='ARMATURE':m.show_viewport=False
coherence=[]
for f in [1,48,84,120,180,240]:
    scene.frame_set(f);bpy.context.view_layer.update();ev=body.evaluated_get(dg);me=ev.to_mesh()
    error=max((me.vertices[v.index].co-head.matrix_basis@v.co).length for v in body.data.vertices if v.co.z>1.49)
    coherence.append({'frame':f,'maxHeadAttachmentErrorMetres':error});ev.to_mesh_clear()
assert max(r['maxHeadAttachmentErrorMetres']for r in coherence)<.0002
for m,flag in zip(body.modifiers,flags):m.show_viewport=flag
(OUT/'Head_Coherence_Check.json').write_text(json.dumps(coherence,indent=2))
scene.frame_set(120);bpy.context.view_layer.update();stats=[]
for name in ['Worker / face neck forearms and hands','Worker / tailored white cotton shirt','Worker / dark seated trousers','Worker / close combed hair cap']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
    stats.append({'object':name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles)});ev.to_mesh_clear()
native={}
for name,expected in [('Kontur_Office_v17_No_Red_Lines.rbxl','47e921f189cc34a6bf3e32f116122ce1d94375fa2d2c4f180c581b7593dfe193'),('Office_v17_BloodFlood_QA.rbxl','ce59e3f73a727cecd22c22e7c7bbaa5caeb0cfe72dd92f347046c8b5b65d8e42')]:
    digest=hashlib.sha256((ROOT/'outputs/BloodFlood_2026-11-08'/name).read_bytes()).hexdigest();assert digest==expected;native[name]=digest
audit={'stage':'First Blender art study; not installed in Roblox','sourceBlendSha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),'anatomy':'Blender Studio Human Base Meshes 1.4.1 / CC0','geometry':stats,'previewFrames':240,'sceneFps':24,'minimumKeyClearanceMetres':min(r['lowestHandMetres']-.796 for r in hand),'maximumHeadCoherenceErrorMetres':max(r['maxHeadAttachmentErrorMetres']for r in coherence),'externalLibraries':[l.filepath for l in bpy.data.libraries],'unpackedExternalFonts':[f.filepath for f in bpy.data.fonts if f.filepath and f.filepath!='<builtin>'and not f.packed_file],'nativeMapHashes':native,'robloxUploads':0,'pending':['Final visual feedback on skin, eyelids and garment finish','Coffee, document, mouse and chair poses for the new mesh','Decision on the linked lower drawer location','Roblox mesh conversion, material parity, lower desk and ceiling reset','Live player markers and server shared interactions','Audio','Actual single-player and co-op tests']}
assert not audit['externalLibraries']and not audit['unpackedExternalFonts']
(OUT/'Art_Stage_Check.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print('ART_AUDIT_PASS',json.dumps(audit),flush=True)
