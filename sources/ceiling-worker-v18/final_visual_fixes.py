from pathlib import Path
import bpy,json,math,calendar
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18';FILE=OUT/'Ceiling_Office_Character_Study_v18.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE));scene=bpy.context.scene
body=bpy.data.objects['Worker / face neck forearms and hands'];head=bpy.data.objects['Head attachment and gaze pivot'];upper=bpy.data.objects['UPPER_OFFICE / local inverted gravity']
# Skull, face and eyes are rigidly coherent; only the neck blends into the torso.
ids=[v.index for v in body.data.vertices if v.co.z>1.425]
for group in body.vertex_groups:group.remove(ids)
hg=body.vertex_groups['head'];ng=body.vertex_groups['neck']
for v in body.data.vertices:
    if v.co.z<=1.425:continue
    w=max(0,min(1,(v.co.z-1.425)/.025));hg.add([v.index],w,'REPLACE');ng.add([v.index],1-w,'REPLACE')
hair=bpy.data.objects['Worker / close combed hair cap'];ids=list(range(len(hair.data.vertices)))
for group in hair.vertex_groups:group.remove(ids)
hair.vertex_groups['head'].add(ids,1,'REPLACE')
font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial.ttf');font.pack()
ink=bpy.data.materials['Graphite enamel'];paper=bpy.data.materials['Paper / warm uncoated']
def text(name,body,pos,size,mat,rotation=(math.pi/2,0,0)):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.font=font;cu.extrude=.00005
    o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=rotation;o.parent=upper;cu.materials.append(mat);return o
for ob in list(scene.objects):
    if ob.name.startswith(('Calendar date','Calendar heading')):bpy.data.objects.remove(ob,do_unlink=True)
text('Calendar title / actual November 2026','НОЯБРЬ 2026',(.253,.961,.891),.018,ink)
text('Calendar weekdays','ПН  ВТ  СР  ЧТ  ПТ  СБ  ВС',(.254,.961,.863),.0115,ink)
start=calendar.monthrange(2026,11)[0]
for day in range(1,31):
    index=start+day-1
    text('Calendar day',str(day),(.258+(index%7)*.028,.961,.837-(index//7)*.026),.012,ink)
for ob in list(scene.objects):
    if ob.name.startswith(('Plan wall','Plan heading','Player marker')):bpy.data.objects.remove(ob,do_unlink=True)
monitor=bpy.data.objects['Monitor / angled side position']
# Draw the actual measured room layout into the monitor, rather than a decorative grid.
rectangles=[(1000,1032,-32,0),(1032,1096,-32,0),(964,1000,8,52),(1008,1056,8,60),(1064,1112,8,60),(1000,1008,0,76),(1056,1064,0,68),(1008,1032,68,88),(1032,1056,68,88),(976,1000,56,76)]
def point(x,z):return Vector((-.235+(x-964)/148*.47,.011,1.18-(z+32)/120*.245))
for x0,x1,z0,z1 in rectangles:
    verts=[point(x0,z0),point(x1,z0),point(x1,z1),point(x0,z1)]
    cu=bpy.data.curves.new('Measured floor plan wall','CURVE');cu.dimensions='3D';cu.bevel_depth=.00065;cu.bevel_resolution=0
    sp=cu.splines.new('POLY');sp.points.add(4)
    for p,co in zip(sp.points,verts+[verts[0]]):p.co=(*co,1)
    ob=bpy.data.objects.new('Measured floor plan wall',cu);scene.collection.objects.link(ob);ob.parent=monitor;cu.materials.append(paper)
# Studio review has illustrative markers. Runtime positions are still a separate integration step.
for x,z in [(1020,47),(1004,50)]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.0036,location=point(x,z));ob=bpy.context.object;ob.name='Illustrative player marker';ob.parent=monitor;ob.data.materials.append(bpy.data.materials['Muted office teal'])

# Verify the head attachments follow the same deformation as the face.
flags=[m.show_viewport for m in body.modifiers]
for m in body.modifiers:
    if m.type!='ARMATURE':m.show_viewport=False
coherence=[];dg=bpy.context.evaluated_depsgraph_get()
for frame in [1,48,84,120,180,240]:
    scene.frame_set(frame);bpy.context.view_layer.update();ev=body.evaluated_get(dg);me=ev.to_mesh()
    errors=[(me.vertices[v.index].co-head.matrix_basis@v.co).length for v in body.data.vertices if v.co.z>1.49]
    coherence.append({'frame':frame,'maxHeadAttachmentErrorMetres':max(errors)})
    ev.to_mesh_clear()
for m,flag in zip(body.modifiers,flags):m.show_viewport=flag
(OUT/'Head_Coherence_Check.json').write_text(json.dumps(coherence,indent=2))
assert all(r['maxHeadAttachmentErrorMetres']<.0002 for r in coherence),coherence
scene.frame_set(120);bpy.ops.wm.save_as_mainfile(filepath=str(FILE),compress=True)
print('FACE_ATTACHMENT_COHERENCE',json.dumps(coherence),flush=True)
