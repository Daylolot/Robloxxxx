"""Extend the portable Blender studies with the v33 look and cue timing."""
import math
from pathlib import Path
import re
import sys

import bpy
from mathutils import Matrix, Vector

kind, folder = sys.argv[sys.argv.index("--")+1:]
out=Path(folder).resolve()
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
cam=scene.camera
scene.eevee.taa_render_samples=24

def image(name,frame):
    scene.frame_set(frame)
    scene.render.filepath=str(out/(name+".png"))
    bpy.ops.render.render(write_still=True)

def eye(position,target,lens=None):
    cam.location=position
    cam.rotation_mode="QUATERNION"
    cam.rotation_quaternion=(Vector(target)-cam.location).to_track_quat("-Z","Y")
    if lens is not None:
        cam.data.lens=lens

def material(name,color,rough):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*color,1)
    shader.inputs["Roughness"].default_value=rough
    return mat

if kind=="Vent":
    details=bpy.data.collections["Anomaly geometry"]
    for obj in details.objects:
        if obj.name.startswith("Green wetness on floor"):
            obj.hide_render=True
            obj.hide_viewport=True
            obj.animation_data_clear()
    sides=96
    vertices=[(0,0,.001)]
    for radius in (.63,.88,1):
        for i in range(sides):
            theta=i*math.tau/sides
            shape=1+.125*math.cos(3*theta+.2)+.08*math.sin(5*theta+.8)+.032*math.sin(8*theta-.6)
            vertices.append((.265*radius*shape*math.cos(theta),.22*radius*shape*math.sin(theta),
                             (1-radius)**1.7*.002))
    faces=[]
    for i in range(sides):
        j=(i+1)%sides
        faces.append((0,i+1,j+1))
        for layer in (0,1):
            a=1+layer*sides
            faces.append((a+i,a+i+sides,a+j+sides,a+j))
    mesh=bpy.data.meshes.new("Wet shape")
    mesh.from_pydata(vertices,[],faces)
    obj=bpy.data.objects.new("Single wet footprint",mesh)
    details.objects.link(obj)
    obj.location=(.36,-.63,-4.718)
    for name,color,roughness in (("Wet core",(.071,.126,.032),.19),("Damp boundary",(.14,.184,.067),.34)):
        mesh.materials.append(material(name,color,roughness))
    for idx,face in enumerate(mesh.polygons):
        face.material_index=1 if idx%3==2 else 0
        face.use_smooth=True
    for frame,scale,hidden in ((1,.38,True),(34,.38,True),(35,.38,False),(145,1,False)):
        obj.hide_render=obj.hide_viewport=hidden
        obj.scale=(scale,scale,1)
        obj.keyframe_insert("hide_render",frame=frame); obj.keyframe_insert("hide_viewport",frame=frame)
        obj.keyframe_insert("scale",frame=frame)
    for i,drop in enumerate(o for o in details.objects if o.name.startswith("Green droplet")):
        width=.018+i*.0015
        for frame in range(1,157,2):
            age=(frame/24+i*.143)%(1.05+i*.039)
            drop.scale=(width,width,width*(1.05+1.35*min(age/.655,1)))
            drop.keyframe_insert("scale",frame=frame)
    scene.frame_set(145)
    saved=(cam.location.copy(),cam.rotation_euler.copy(),cam.rotation_mode,cam.data.lens)
    eye((2.8,-2.1,-2.68),(.43,-.63,-4.65),48)
    image("vent_footprint",145)
    eye((4.8,-2.8,-.2),(.3,0,-.65),38)
    image("vent_hall",47)
    cam.location,old,cam.rotation_mode,cam.data.lens=saved
    cam.rotation_euler=old
elif kind=="Static":
    def srgb(linear):
        return 12.92*linear if linear<=.0031308 else 1.055*linear**(1/2.4)-.055
    def linear(value):
        return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4
    for name,z,angle in (("ArtA",-21,-2.7),("ArtB",-14,1.8)):
        scene.frame_set(21)
        pivot=Vector((-.162,-17.1-z,8.191-5.36))
        rot=Matrix.Rotation(math.radians(angle),3,"X")
        for obj in bpy.data.collections[name].objects:
            obj.location=pivot+rot@(obj.location-pivot)
            obj.rotation_euler=(rot@obj.rotation_euler.to_matrix()).to_euler()
            obj.keyframe_insert("location",frame=21)
            obj.keyframe_insert("rotation_euler",frame=21)
    recolored=0
    scene.frame_set(81)
    for obj in bpy.data.collections["Plant"].objects:
        if not obj.data.materials: continue
        current=obj.data.materials[0]
        shader=current.node_tree.nodes.get("Principled BSDF")
        base=tuple(shader.inputs["Base Color"].default_value[:])
        mat=current.copy()
        mat.node_tree.animation_data_clear()
        col=mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"]
        obj.data.materials[0]=mat
        col.default_value=base
        name=obj.name.split(".")[0]
        if name in {"LeafBlade","TerminalLeaf"}:
            local_size=[max(v.co[i] for v in obj.data.vertices)-min(v.co[i] for v in obj.data.vertices) for i in range(3)]
            width,length,_=local_size
            verts=[]
            for row in range(17):
                u=row/16
                edge=width*.5*max(.035,math.sin(math.pi*u)**.68)*(1.08-.16*u)
                for col_idx in range(7):
                    side=col_idx/3-1
                    verts.append((side*edge,length*(u-.5),
                                  .013*math.sin(math.pi*u)*(1-.8*side*side)-.011*u*u))
            polys=[(r*7+c,r*7+c+1,(r+1)*7+c+1,(r+1)*7+c) for r in range(16) for c in range(6)]
            mesh=bpy.data.meshes.new("Tapered leaf blade")
            mesh.from_pydata(verts,[],polys); mesh.materials.append(mat)
            obj.data=mesh
            for face in mesh.polygons: face.use_smooth=True
            obj.modifiers.new("Thin leaf skin","SOLIDIFY").thickness=.005
        if name in {"LeafBlade","TerminalLeaf","LeafMidrib_Wire"}:
            r,g,b=map(srgb,base[:3])
            tinted=[(83+g*185)/255,(18+r*95)/255,(54+b*118)/255]
            col.keyframe_insert("default_value",frame=81)
            col.default_value=(*map(linear,[min(1,x) for x in tinted]),1)
            col.keyframe_insert("default_value",frame=101)
            recolored+=1
    assert recolored==78
    image("swapped_frames",21)
    image("leaf_close",101)
elif kind=="Archive":
    details=bpy.data.collections["Anomaly geometry"]
    for i,letter in enumerate(o for o in list(details.objects) if o.name.startswith(("First ","Return "))):
        if i%3: continue
        mesh=bpy.data.meshes.new("Dry trail")
        mesh.from_pydata([(0,0,0),(0,.012,.002),(0,.008,-.035),(0,.002,-.053)],[],[(0,1,2,3)])
        obj=bpy.data.objects.new("Pigment under glyph",mesh); details.objects.link(obj)
        obj.location=letter.location+Vector((-.001,.032,-.255))
        mat=letter.data.materials[0]
        mesh.materials.append(mat)
        for frame in (1,34,61,89,111,148):
            scene.frame_set(frame)
            obj.hide_render=obj.hide_viewport=letter.hide_render
            obj.keyframe_insert("hide_render",frame=frame); obj.keyframe_insert("hide_viewport",frame=frame)
    scene.frame_set(61)
    cam.animation_data_clear()
    eye((-6.2,2.1,-.18),(0,0,0),25)
    image("archive_angle",61)
    eye((-5.5,.05,-.18),(0,0,0),32)
    image("archive_return",148)
elif kind=="Printer":
    src=Path(__file__).with_name("PrinterDirection.luau").read_text()
    cues=re.findall(r'\{"([A-Za-z]+)",\d+,"rbxassetid://\d+",([.\d]+),',src)
    assert len(cues)==9
    for marker in list(scene.timeline_markers):
        if marker.name.startswith("Шелест"):
            scene.timeline_markers.remove(marker)
    for name,when in cues:
        scene.timeline_markers.new("Шелест · "+name,frame=1+round((7.45+float(when))*scene.render.fps))
    eye((1,-4,5.25),(1,.25,5.25),39)
    image("printer_receipt",1+round(13.45*24))
else:
    raise ValueError(kind)

scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/("Kontur_"+kind+"_v33.blend")),compress=True)
