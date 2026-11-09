from pathlib import Path
import bpy,bmesh,math,json,numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18';FILE=OUT/'Ceiling_Office_Character_Study_v18.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE));scene=bpy.context.scene
rig=bpy.data.objects['OfficeWorker anatomical rig'];body=bpy.data.objects['Worker / face neck forearms and hands'];base=bpy.data.objects['Anatomy working base']
# The source hands are naturally angled forward. Align the rest bones to that anatomy,
# rather than treating them as flat A-pose hands.
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for side,s in [('L',1),('R',-1)]:
    hand=rig.data.edit_bones['hand.'+side];hand.head=(s*.365,-.05,.90);hand.tail=(s*.42,-.12,.745)
    rig.data.edit_bones['forearm.'+side].tail=hand.head
bpy.ops.object.mode_set(mode='OBJECT')
body.data=base.data.copy();body.data.materials.clear();body.data.materials.append(bpy.data.materials['Skin / restrained pores and subsurface'])
bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if not((c:=f.calc_center_median()).z>1.425 or(abs(c.x)>.24 and c.z<1.065))],context='FACES')
bm.to_mesh(body.data);bm.free();body.data.update()
colors=body.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
for v,col in zip(body.data.vertices,colors.data):
    x,y,z=v.co;under=math.exp(-((abs(x)-.032)/.025)**2-((z-1.555)/.018)**2)*max(0,min(1,(-y-.06)*20))
    lips=math.exp(-(x/.035)**4-((z-1.51)/.008)**2)*max(0,min(1,(-y-.08)*30));ear=max(0,(abs(x)-.065)*20)if z>1.50 else 0
    col.color=(.51-.10*under-.05*lips+.035*ear,.335-.085*under-.12*lips,.25-.05*under-.065*lips,1)
    v.co.z+=.0012*math.exp(-((abs(x)-.026)/.011)**2-((z-1.510)/.015)**2)*max(0,min(1,(-y-.08)*30))
hand_binds={};fore_binds={};old_fore={s:rig.pose.bones['forearm.'+s].matrix.copy()for s in ['L','R']}
for side,s in [('L',1),('R',-1)]:
    bone=rig.data.bones['hand.'+side];source=(bone.tail_local-bone.head_local).normalized()
    palm=np.array([list(v.co)for v in base.data.vertices if v.co.x*s>.30 and .79<v.co.z<.90])
    values,vectors=np.linalg.eigh(np.cov(palm.T));normal=Vector(vectors[:,0])
    if normal.y>0:normal=-normal
    print('ANATOMICAL_PALM_PLANE',side,list(normal),flush=True)
    source_x=source.cross(normal).normalized();source_z=source_x.cross(source).normalized()
    target=Vector((-s*.025,-.17,-.01)).normalized();target_z=Vector((0,0,-1));target_x=target.cross(target_z).normalized();target_z=target_x.cross(target).normalized()
    R=Matrix((target_x,target,target_z)).transposed()@Matrix((source_x,source,source_z))
    wrist=Vector((s*.155,-.49,.847))
    hand_binds[side]=Matrix.Translation(wrist)@R.to_4x4()@Matrix.Translation(-bone.head_local)@bone.matrix_local
    fb=rig.data.bones['forearm.'+side];elbow=Vector((s*.255,-.26,.80));FR=(fb.tail_local-fb.head_local).rotation_difference(wrist-elbow)
    fore_binds[side]=Matrix.Translation(elbow)@FR.to_matrix().to_4x4()@Matrix.Translation(-fb.head_local)@fb.matrix_local
    # Match elbow-to-wrist distance, so the skinned joint does not pinch or separate.
    ratio=(wrist-elbow).length/(fb.tail_local-fb.head_local).length
    for row in range(3):fore_binds[side][row][1]*=ratio
    direction=source;pivot=bone.head_local+direction*.105;axis=direction.cross(normal).normalized()
    for v in body.data.vertices:
        if v.co.x*s<.31 or v.co.z>.91:continue
        length=(v.co-bone.head_local).dot(direction)
        if length>.105:v.co=pivot+Matrix.Rotation(.06*min(1,(length-.105)/.09),3,axis)@(v.co-pivot)
for frame in range(1,241):
    scene.frame_set(frame)
    t=(frame-1)/24
    def ease(v):v=max(0,min(1,v));return v*v*(3-2*v)
    attention=ease((t-2)/1.4)*(1-ease((t-7)/2))
    # Parent pose must be evaluated before deriving a child's local pose basis.
    for kind in ['forearm','hand']:
        for side,s in [('L',1),('R',-1)]:
            name=kind+'.'+side;bind=fore_binds[side]if kind=='forearm'else hand_binds[side]
            pb=rig.pose.bones[name];pb.matrix=Matrix.Translation((0,0,.0018*math.sin(t*17+s*2)*(1-attention)))@bind
            pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame);pb.keyframe_insert('scale',frame=frame)
        bpy.context.view_layer.update()
scene.frame_set(120);body.data.update();bpy.context.view_layer.update()
for ob in [v for v in scene.objects if v.name.startswith('Worker / sewn sleeve cuff')]:
    center=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);side='L'if center.x>0 else'R'
    delta=fore_binds[side]@old_fore[side].inverted()
    for v in ob.data.vertices:v.co=delta@v.co
    ob.data.update()
# Measure actual evaluated skin points over the keyboard, including the typing extremes.
checks=[];dg=bpy.context.evaluated_depsgraph_get()
for frame in [1,17,36,60,84,120,180,225,240]:
    scene.frame_set(frame);bpy.context.view_layer.update();ev=body.evaluated_get(dg);me=ev.to_mesh()
    points=[v.co for v in me.vertices if -.665<v.co.y<-.49 and abs(v.co.x)<.225 and v.co.z>.65]
    checks.append({'frame':frame,'pointsOverKeyboard':len(points),'lowestHandMetres':min((p.z for p in points),default=0),'keyCapsMetres':.796})
    ev.to_mesh_clear()
(OUT/'Hand_Contact_Check.json').write_text(json.dumps(checks,indent=2))
scene.frame_set(120);bpy.ops.wm.save_as_mainfile(filepath=str(FILE),compress=True)
print('HAND_CLEARANCE',json.dumps(checks),flush=True)
