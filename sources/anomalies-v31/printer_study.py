"""Preview the extra choreography in the original 60-sheet office study."""
import math
from pathlib import Path
import re
import sys

import bpy
from mathutils import Euler, Matrix, Vector

root=Path(__file__).resolve().parent
out=Path(sys.argv[sys.argv.index("--")+1]).resolve()
out.mkdir(parents=True,exist_ok=True)
source=(root/"PrinterDirection.luau").read_text()
contacts={int(i):(Vector(tuple(map(float,spot.split(",")))),*map(float,args.split(",")))
          for i,spot,args in re.findall(r"\[(\d+)\] = \{Vector3.new\(([^)]+)\), ([^}]+)\}",source)}
arc_section=source.split("local arcRanks = {")[1].split("}")[0]
arcs={int(i):int(rank) for i,rank in re.findall(r"\[(\d+)\]=(\d+)",arc_section)}
assert len(contacts)==3 and len(arcs)==9
scene=bpy.context.scene
fps=scene.render.fps
origin=Vector((1032,0,34))
def local(roblox):
    x,y,z=Vector(roblox)-origin
    return Vector((x,-z,y))

def ease(t):
    t=min(max(t,0),1)
    return t*t*(3-2*t)

sheets={i:bpy.data.objects[f"Лист {i:02d}"] for i in (contacts|arcs)}
samples={i:[] for i in sheets}
for frame in range(1,scene.frame_end+1,2):
    scene.frame_set(frame)
    age=(frame-1)/fps-7.45
    for i,obj in sheets.items():
        at=obj.location.copy()
        rot=obj.rotation_euler.to_quaternion()
        curl,bow,*_=obj.data.shape_keys.key_blocks[1:]
        newcurl,newbow=curl.value,bow.value
        if i in contacts:
            spot,start,hold,tilt,crease=contacts[i]
            weight=ease((age-start+1.30)/1.30)*(1-ease((age-start-hold)/1.45))
            if weight:
                slip=.20*ease((age-start)/hold) if i==28 else 0
                at=at.lerp(local(spot+Vector((slip,0,0))),weight)
                rot=rot.slerp(Euler((tilt+.027*math.sin(age*16),0,math.pi if i==17 else 0)).to_quaternion(),weight)
                newcurl+=(crease+.13*math.sin(age*20)-newcurl)*weight
                newbow+=(.24-newbow)*weight
        if i in arcs:
            rank=arcs[i]
            weight=ease((age-7.35-rank*.075)/1.35)*(1-ease((age-10.55-rank*.065)/1.25))
            if weight:
                a=(rank-5)*.17+(age-9.1)*.063
                at=at.lerp(local((1033.3-6.7*(1-math.cos(a)),7.5-.85*abs(a),36+11.4*math.sin(a))),weight)
                rot=rot.slerp(Euler((.12*math.sin(age*5+rank),-.19,a+1.15)).to_quaternion(),weight)
                newcurl+=(.36+.19*math.sin(age*7+rank)-newcurl)*weight
        samples[i].append((frame,at,rot,newcurl,newbow))
for i,obj in sheets.items():
    obj.rotation_mode="QUATERNION"
    for frame,at,rot,curl,bow in samples[i]:
        obj.location=at
        obj.rotation_quaternion=rot
        obj.keyframe_insert("location",frame=frame)
        obj.keyframe_insert("rotation_quaternion",frame=frame)
        for key,value in zip(obj.data.shape_keys.key_blocks[1:3],(curl,bow)):
            key.value=value
            key.keyframe_insert("value",frame=frame)

collection=bpy.data.collections.new("Receipt · once per viewer")
scene.collection.children.link(collection)
paper=bpy.data.materials["Paper stock 6"]
ink=bpy.data.materials["Тонер"]
font=bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
font.pack()
eye=local((1033,5.25,38)); start=local((1035,5.95,32.25)); finish=local((1033,5.25,33.75)); exit=local((1033,7.15,32.85))
for i,text in enumerate(("ПОДТВЕРДИТЕ","ПОЛУЧЕНИЕ")):
    sign=1 if i==0 else -1
    mesh=bpy.data.meshes.new("Half page")
    mesh.from_pydata([(-.57,-.17,0),(.57,-.17,0),(.57,.17,0),(-.57,.17,0)],[],[(0,1,2,3)])
    leaf=bpy.data.objects.new("Receipt half "+str(i+1),mesh); collection.objects.link(leaf)
    mesh.materials.append(paper)
    mod=leaf.modifiers.new("Paper thickness","SOLIDIFY");mod.thickness=.006
    data=bpy.data.curves.new(text,"FONT"); data.body=text; data.font=font
    data.size=.116; data.align_x="CENTER"; data.align_y="CENTER"; data.materials.append(ink)
    label=bpy.data.objects.new(text,data);collection.objects.link(label);label.parent=leaf;label.location.z=.005
    leaf.rotation_mode="QUATERNION"
    for frame in range(1,scene.frame_end+1,2):
        t=(frame-1)/fps-7.45-4.65
        p=start.lerp(finish,ease(t/.86)).lerp(exit,ease((t-2.94)/.68))
        facing=(eye-p).to_track_quat("Z","Y").to_matrix()
        rot=facing @ Matrix.Rotation(sign*ease((t-2.78)/.42)*1.41,3,"X")
        leaf.location=p+rot@Vector((0,sign*.17,0))
        leaf.rotation_quaternion=rot.to_quaternion()
        leaf.keyframe_insert("location",frame=frame);leaf.keyframe_insert("rotation_quaternion",frame=frame)
        for obj in (leaf,label):
            obj.hide_viewport=not 0<=t<3.62
            obj.hide_render=obj.hide_viewport
            obj.keyframe_insert("hide_render",frame=frame)
            obj.keyframe_insert("hide_viewport",frame=frame)
for time,name in ((7.45,"Шелест · лоток"),(7.83,"Шелест · папки"),(8.08,"Шелест · стол у прохода"),
                  (8.22,"Шелест · соседняя стопка"),(8.58,"Шелест · дальний стол")):
    scene.timeline_markers.new(name,frame=1+round(time*fps))
for marker in list(scene.timeline_markers):
    if marker.camera:
        marker.camera=None
scene.render.use_sequencer=False
scene.eevee.taa_render_samples=18
cam=bpy.data.objects["Поперёк прохода"]
scene.camera=cam
def shot(name,age,position,target,lens):
    scene.frame_set(1+round((7.45+age)*fps))
    cam.location=local(position)
    cam.rotation_euler=(local(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.lens=lens
    scene.render.filepath=str(out/(name+".png"))
    bpy.ops.render.render(write_still=True)
shot("printer_01_receipt",6.0,(1033,5.25,38),(1033,5.25,33.75),42)
shot("printer_02_fold",7.78,(1033,5.25,38),(1033,6.1,33.5),43)
shot("printer_03_monitor",5.06,(1023.5,5.8,48.0),(1020.36,5.335,47.60),52)
shot("printer_04_desk",5.92,(1024.2,4.85,46),(1022.23,3.37,46.05),52)
shot("printer_05_arc",9.46,(1030.5,5.23,48),(1032,7.05,33),29)
shot("printer_06_floor",10.45,(1045.4,2.15,40),(1048.1,.68,40),48)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/"Kontur_Printer_v31.blend"),compress=True)
