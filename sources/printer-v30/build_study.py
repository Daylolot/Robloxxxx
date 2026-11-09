"""Build a portable Blender scene with the original office layout and baked paper motion."""
from collections import defaultdict
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from paper_motion import FPS,DURATION,READ_AT,ONSET,make_sheets,pose,separated_positions,serializable,smooth

geometry, out = map(Path,sys.argv[sys.argv.index("--")+1:])
out.mkdir(parents=True,exist_ok=True)
parts=json.loads(geometry.read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version < (5,0,0) else "BLENDER_EEVEE"
scene.eevee.taa_render_samples=12
scene.render.resolution_x=1100
scene.render.resolution_y=700
scene.render.resolution_percentage=100
scene.render.fps=FPS
scene.frame_start=1
scene.frame_end=round(FPS*DURATION)+1
scene.view_settings.view_transform="AgX"
scene.view_settings.exposure=.45
world=bpy.data.worlds.new("Office daylight")
scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.23,.28,.32,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.48


def collection(name):
    result=bpy.data.collections.new(name)
    scene.collection.children.link(result)
    return result


room=collection("01 | Центральный офис")
paper=collection("02 | 60 листов")
printer=collection("03 | Предупреждение")
lighting=collection("04 | Свет")
cameras=collection("05 | Камеры проверки")


def local(point):
    x,y,z=point
    return Vector((x-1032,34-z,y))


def frame_at(seconds):
    return 1+round(seconds*FPS)


def mesh_obj(name,vertices,faces,materials,coll):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    for material in materials:
        mesh.materials.append(material)
    obj=bpy.data.objects.new(name,mesh)
    coll.objects.link(obj)
    return obj


def srgb(channel):
    return channel/12.92 if channel<.04045 else ((channel+.055)/1.055)**2.4


def material(name,rgb,roughness=.62,metallic=0):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.diffuse_color=(*rgb,1)
    node=mat.node_tree.nodes["Principled BSDF"]
    node.inputs["Base Color"].default_value=(*rgb,1)
    node.inputs["Roughness"].default_value=roughness
    node.inputs["Metallic"].default_value=metallic
    return mat,node


cube=[(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),
      (-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]
cube_faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
cylinder=[(x,math.cos(i*math.tau/12)*.5,math.sin(i*math.tau/12)*.5)
          for x in (-.5,.5) for i in range(12)]
cyl_faces=[tuple(reversed(range(12))),tuple(range(12,24))]+[
    (i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)]
groups=defaultdict(lambda:([],[]))
obstacles=defaultdict(list)
for item in parts:
    if item["group"].endswith("/Printer") and item["name"]=="Paper":
        continue
    pos=Vector(item["cf"][:3])
    rotation=Matrix([item["cf"][i:i+3] for i in (3,6,9)])
    size=item["size"]
    solid=item["transparency"]<.2
    key=(item["color"],item["material"],round(item["transparency"],2),item["name"]=="Display")
    vertices,faces=groups[key]
    coords,polys=(cylinder,cyl_faces) if item["shape"]==2 else (cube,cube_faces)
    points=[local(rotation@Vector([v*s for v,s in zip(point,size)])+pos) for point in coords]
    base=len(vertices)
    vertices.extend(points)
    faces.extend(tuple(base+i for i in face) for face in polys)
    if solid and math.prod(size)>.025 and 1.05<pos.y<10.5:
        lo=tuple(min(v[i] for v in points) for i in range(3))
        hi=tuple(max(v[i] for v in points) for i in range(3))
        for x in range(math.floor(lo[0]),math.floor(hi[0])+1):
            for y in range(math.floor(lo[1]),math.floor(hi[1])+1):
                obstacles[x,y].append((lo,hi,item["name"]))

for (color,token,trans,display),(vertices,faces) in groups.items():
    rgb=tuple(srgb(((color>>shift)&255)/255) for shift in (16,8,0))
    mat,node=material(f"Office {color:06X} · {token}",rgb,.53, .48 if token in {1088,1104} else 0)
    if trans>.05:
        mat.surface_render_method="DITHERED"
        node.inputs["Alpha"].default_value=max(.08,1-trans)
    if display or token==288:
        node.inputs["Emission Color"].default_value=(*rgb,1)
        node.inputs["Emission Strength"].default_value=1.4 if display else 3.4
    mesh_obj(f"Архитектура {color:06X}",vertices,faces,[mat],room)
print("Geometry",len(parts),"parts",len(groups),"batches",flush=True)


def page_material(index):
    base=(.91-index*.019,.87-index*.016,.78-index*.011)
    mat,node=material(f"Paper stock {index+1}",base,.75)
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    uv=nodes.new("ShaderNodeTexCoord")
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=195
    noise.inputs["Roughness"].default_value=.63
    links.new(uv.outputs["UV"],noise.inputs["Vector"])
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.12
    bump.inputs["Distance"].default_value=.007
    links.new(noise.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],node.inputs["Normal"])
    if index<5:
        path=geometry.parent/f"page_{index+1}.png"
        if path.exists():
            printout=nodes.new("ShaderNodeTexImage")
            printout.image=bpy.data.images.load(str(path.resolve()))
            printout.image.pack()
            links.new(uv.outputs["UV"],printout.inputs["Vector"])
            links.new(printout.outputs["Color"],node.inputs["Base Color"])
    return mat


stocks=[page_material(i) for i in range(5)]
plain_stock=page_material(5)
ink,_=material("Тонер",(0.055,.072,.071),.9)
grid_x,grid_y=8,12
sample_times=range(1,scene.frame_end+1,2)


def page_mesh(sheet):
    coords=[(i/grid_x-.5,j/grid_y-.5) for j in range(grid_y+1) for i in range(grid_x+1)]
    vertices=[(x*sheet.width,y*sheet.length,0) for x,y in coords]
    stride=grid_x+1
    faces=[(j*stride+i,j*stride+i+1,(j+1)*stride+i+1,(j+1)*stride+i)
           for j in range(grid_y) for i in range(grid_x)]
    obj=mesh_obj(sheet.name,vertices,faces,[stocks[sheet.ink],plain_stock],paper)
    uv=obj.data.uv_layers.new()
    for poly in obj.data.polygons:
        poly.use_smooth=True
        for loop in poly.loop_indices:
            x,y=coords[obj.data.loops[loop].vertex_index]
            uv.data[loop].uv=(x+.5,y+.5)
    obj.shape_key_add(name="Плоский лист")
    deformations=(
        ("Свободный край",lambda x,y:.20*(y+.5)**3*(.82+.3*x)),
        ("Продольная дуга",lambda x,y:.25*y*y),
        ("Поперечный сгиб",lambda x,y:.29*x*x),
        ("Скручивание",lambda x,y:.26*x*y),
    )
    heights=[]
    for name,shape in deformations:
        key=obj.shape_key_add(name=name)
        key.slider_min=-1
        key.slider_max=1.25
        height=[shape(x,y) for x,y in coords]
        for point,z in zip(key.data,height):
            point.co.z=z
        heights.append(height)
    solid=obj.modifiers.new("Толщина бумаги","SOLIDIFY")
    solid.thickness=.003
    solid.offset=0
    solid.material_offset=1
    solid.material_offset_rim=1
    return obj,vertices,heights


def linear(animation):
    action=animation.action
    slot=animation.action_slot
    for layer in action.layers:
        for strip in layer.strips:
            for curve in strip.channelbag(slot).fcurves:
                for key in curve.keyframe_points:
                    key.interpolation="LINEAR"


records=[]
sheets=make_sheets()
flight=list(separated_positions(sheets,((frame-1)/FPS for frame in sample_times)))
for sheet_index,sheet in enumerate(sheets):
    obj,vertices,heights=page_mesh(sheet)
    obj["Старт"]=sheet.packet
    obj["Траектория"]=sheet.kind
    obj["Шелест, с"]=round(sheet.stir,3)
    obj["Отрыв, с"]=round(sheet.peel,3)
    keys=list(obj.data.shape_keys.key_blocks)[1:]
    rest=local(sheet.origin)
    min_gap=100
    bad=[]
    touched=0
    unique=set()
    last=None
    max_step=0
    for sample,frame in enumerate(sample_times):
        time=(frame-1)/FPS
        _,angles,weights=pose(sheet,time)
        location=local(flight[sample][sheet_index])
        rotation=Euler(angles,"XYZ")
        matrix=rotation.to_matrix()
        offsets=[matrix@Vector((x,y,sum(w*height[i] for w,height in zip(weights,heights))))
                 for i,(x,y,_) in enumerate(vertices)]
        gap=location.z+min(p.z for p in offsets)-rest.z
        if time<sheet.peel+.62 and gap<.002:
            location.z+=.002-gap
            gap=.002
        if time<sheet.peel and gap<.014:
            touched+=1
        if time>sheet.peel+.62:
            for i in (0,4,8,27,31,35,54,58,62,81,85,89,108,112,116):
                p=location+offsets[i]
                if not (-23<p.x<23 and -24<p.y<25 and p.z<9.05):
                    bad.append((frame,"граница комнаты"))
                    break
                for lo,hi,name in obstacles.get((math.floor(p.x),math.floor(p.y)),()):
                    if all(lo[axis]+.012<p[axis]<hi[axis]-.012 for axis in range(3)):
                        bad.append((frame,name))
                        break
                else:
                    continue
                break
        if time<sheet.peel+.62:
            min_gap=min(min_gap,gap)
        if last is not None:
            max_step=max(max_step,(location-last).length)
        last=location.copy()
        unique.add(tuple(round(v,3) for v in location))
        obj.location=location
        obj.rotation_euler=rotation
        obj.keyframe_insert("location",frame=frame,group="Полёт")
        obj.keyframe_insert("rotation_euler",frame=frame,group="Полёт")
        for key,value in zip(keys,weights):
            key.value=value
            key.keyframe_insert("value",frame=frame)
    linear(obj.animation_data)
    linear(obj.data.shape_keys.animation_data)
    records.append({"sheet":sheet.name,"packet":sheet.packet,"kind":sheet.kind,
                    "stir":sheet.stir,"peel":sheet.peel,"contactSamples":touched,
                    "minGapStuds":min_gap,"maxStepStuds":max_step,
                    "positions":len(unique),"intersections":bad})
print("Baked",len(records),"sheets. Intersection samples:",sum(len(s["intersections"]) for s in records),flush=True)

warning=mesh_obj("Лист с предупреждением",[(x*.72,y*.98,0) for x,y in
    [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]],[(0,1,2,3)],[plain_stock],printer)
warning.modifiers.new("Толщина распечатки","SOLIDIFY").thickness=.006
font=bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial.ttf")

def label(name,body,size,position,parent=None):
    data=bpy.data.curves.new(name,"FONT")
    data.body=body
    data.font=font
    data.align_x="CENTER"
    data.align_y="CENTER"
    data.size=size
    data.materials.append(ink)
    source=bpy.data.objects.new(name,data)
    printer.objects.link(source)
    bpy.context.view_layer.update()
    mesh=bpy.data.meshes.new_from_object(source.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(source,do_unlink=True)
    bpy.data.curves.remove(data)
    obj=bpy.data.objects.new(name,mesh)
    printer.objects.link(obj)
    obj.parent=parent
    obj.location=position
    return obj


notice=label("Текст распечатки","ПРЕДУПРЕЖДЕНИЕ\nБУМАГА ПОДНИМЕТСЯ\nЧЕРЕЗ 5 СЕКУНД",.067,(0,0,.008),warning)
notice.rotation_euler.z=-math.pi/2
for frame in sample_times:
    t=(frame-1)/FPS
    feed=.34*smooth((t-.2)/.36)+.37*smooth((t-.64)/.4)+.29*smooth((t-1.11)/.43)
    warning.location=local((1053.695-.36*feed,3.786-.086*smooth((t-.65)/.89),42.43))
    warning.scale.x=max(.008,feed)
    warning.rotation_euler.y=-.19*math.sin(math.pi*smooth((t-.38)/1.15))
    warning.keyframe_insert("location",frame=frame)
    warning.keyframe_insert("scale",frame=frame)
    warning.keyframe_insert("rotation_euler",frame=frame)
linear(warning.animation_data)

display_labels=[("ГОТОВ",0,.21),("ПЕЧАТЬ",.21,1.54),("ЧИТАТЬ",1.54,READ_AT)]
display_labels.extend((f"00:0{5-i}",READ_AT+i,READ_AT+i+1) for i in range(5))
display_labels.append(("00:00",ONSET,DURATION+1))
for status,start,end in display_labels:
    obj=label("Дисплей / "+status,status,.091,local((1053.688,4.16,41.52)))
    obj.rotation_euler=(math.pi/2,0,-math.pi/2)
    for frame,hidden in [(1,start>0),(frame_at(start),False),(frame_at(end),True)]:
        obj.hide_render=hidden
        obj.hide_viewport=hidden
        obj.keyframe_insert("hide_render",frame=frame)
        obj.keyframe_insert("hide_viewport",frame=frame)
bpy.data.fonts.remove(font)

sound_path=out/"Printer_Paper_Review.wav"
if sound_path.exists():
    strip=scene.sequence_editor_create().strips.new_sound("Протяжка и шелест",str(sound_path.resolve()),
                                                          channel=1,frame_start=1)
    strip.sound.pack()

for x,z in [(1015,15),(1032,15),(1049,15),(1016,34),(1032,34),(1049,34),(1016,52),(1032,52),(1049,52)]:
    data=bpy.data.lights.new(f"Потолок {x} {z}","AREA")
    data.energy=870
    data.shape="RECTANGLE"
    data.size=5.0
    data.size_y=3.2
    data.color=(1,.944,.84)
    obj=bpy.data.objects.new(data.name,data)
    lighting.objects.link(obj)
    obj.location=local((x,10.5,z))

def make_camera(name,position,target,lens):
    data=bpy.data.cameras.new(name)
    data.lens=lens
    data.clip_start=.025
    data.clip_end=200
    obj=bpy.data.objects.new(name,data)
    cameras.objects.link(obj)
    obj.location=local(position)
    obj.rotation_euler=(local(target)-obj.location).to_track_quat("-Z","Y").to_euler()
    return obj


views=[
    ("Принтер",(1049.8,5.05,43.8),(1053.7,3.98,42),40),
    ("Распечатка",(1051.57,5.29,42.14),(1053.38,3.71,42.10),51),
    ("Край листа",(1051.95,4.10,40.24),(1053.37,3.76,41.72),47),
    ("Отрыв у стола",(1025.55,4.28,48.35),(1022.19,3.78,47.56),38),
    ("От принтера по залу",(1050,5.55,44.5),(1027,6.18,34),25),
    ("Поперёк прохода",(1029.75,5.4,55.6),(1031,4.55,28.3),24),
    ("Над полом",(1047,2.58,38),(1048,2.05,40),39),
]
cams=[make_camera(*view) for view in views]
sequence=[(0,0),(1.74,1),(ONSET-.55,2),(ONSET+1.38,3),(ONSET+3.45,4),(ONSET+9.1,5)]
for time,index in sequence:
    marker=scene.timeline_markers.new(cams[index].name,frame=frame_at(time))
    marker.camera=cams[index]
for time,name in [(READ_AT,"Прочитать лист"),(ONSET,"5 секунд · начало шелеста"),(ONSET+.57,"Отрыв края"),
                  (ONSET+4.8,"Расходятся по комнате"),(ONSET+11,"Левитация")]:
    scene.timeline_markers.new(name,frame=frame_at(time))
scene.camera=cams[0]
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=="VIEW_3D":
            area.spaces.active.region_3d.view_perspective="CAMERA"
bpy.ops.wm.save_as_mainfile(filepath=str((out/"Kontur_Printer_Paper_v30.blend").resolve()),compress=True)
report={"fps":FPS,"durationSeconds":DURATION,"readAt":READ_AT,"stirAt":ONSET,
        "partsFromMap":len(parts),"sheets":records}
(out/"Motion_Check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
(out/"Sheet_Choreography.json").write_text(json.dumps(serializable(sheets),ensure_ascii=False,indent=2)+"\n")
