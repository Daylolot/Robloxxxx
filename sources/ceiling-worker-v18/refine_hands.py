from pathlib import Path
import bpy,math
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18';FILE=OUT/'Ceiling_Office_Character_Study_v18.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE))
rig=bpy.data.objects['OfficeWorker anatomical rig'];body=bpy.data.objects['Worker / face neck forearms and hands']
# Restore the unbent hand topology from the builder checkpoint, then bend with the corrected roll.
with bpy.data.libraries.load(str(FILE)+ '1',link=False)as(src,dst):dst.meshes=[body.data.name]
replacement=dst.meshes[0]
assert replacement is not None
assert len(replacement.vertices)==len(body.data.vertices)
body.data=replacement
for side,s in [('L',1),('R',-1)]:
    bone=rig.data.bones['hand.'+side]
    source=(bone.tail_local-bone.head_local).normalized();normal=Vector((0,-1,0))
    source_x=source.cross(normal).normalized();source_z=source_x.cross(source).normalized()
    target=Vector((-s*.025,-.17,-.01)).normalized();target_z=Vector((0,0,-1))
    target_x=target.cross(target_z).normalized();target_z=target_x.cross(target).normalized()
    old=Matrix((source_x,source,source_z)).transposed();new=Matrix((target_x,target,target_z)).transposed()
    R=new@old.transposed();wrist=Vector((s*.155,-.49,.81))
    bind=Matrix.Translation(wrist)@R.to_4x4()@Matrix.Translation(-bone.head_local)@bone.matrix_local
    pb=rig.pose.bones['hand.'+side]
    for frame in range(1,241):
        t=(frame-1)/24
        def ease(v):v=max(0,min(1,v));return v*v*(3-2*v)
        attention=ease((t-2)/1.4)*(1-ease((t-7)/2))
        pb.matrix=Matrix.Translation((0,0,.0018*math.sin(t*17+s*2)*(1-attention)))@bind
        pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
    direction=(bone.tail_local-bone.head_local).normalized();pivot=bone.head_local+direction*.105
    axis=direction.cross(normal).normalized()
    # The palmar normal now faces the key caps. Bend 25 degrees at the distal joints.
    for v in body.data.vertices:
        if v.co.x*s<.31 or v.co.z>.91:continue
        length=(v.co-bone.head_local).dot(direction)
        if length<.105:continue
        f=min(1,(length-.105)/.09)
        v.co=pivot+Matrix.Rotation(.45*f,3,axis)@(v.co-pivot)
body.data.update();bpy.context.scene.frame_set(120)
bpy.ops.wm.save_as_mainfile(filepath=str(FILE),compress=True)
print('HAND_ROLL_AND_FINGER_POSE_REFINED',flush=True)
