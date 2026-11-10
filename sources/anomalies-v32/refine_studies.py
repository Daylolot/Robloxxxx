"""Carry vent pressure, impacts and the old calendar pin into the saved studies."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

kind, folder = sys.argv[sys.argv.index("--")+1:]
out=Path(folder).resolve()
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
cam=scene.camera

def ease(t):
    t=max(0,min(1,t))
    return t*t*(3-2*t)

def image(name, frame):
    scene.frame_set(frame)
    scene.render.filepath=str(out/(name+".png"))
    bpy.ops.render.render(write_still=True)

if kind=="Vent":
    for mat in bpy.data.materials:
        if not mat.name.startswith("Vapor density "):
            continue
        nodes,links=mat.node_tree.nodes,mat.node_tree.links
        volume=next(node for node in nodes if node.bl_idname=="ShaderNodeVolumePrincipled")
        density=volume.inputs["Density"]
        original=density.links[0].from_socket
        emission=volume.inputs["Emission Strength"].links[0].from_node
        pressure=nodes.new("ShaderNodeMath")
        pressure.name="Pressure pulse"; pressure.operation="MULTIPLY"
        links.new(original,pressure.inputs[0])
        links.new(pressure.outputs[0],density)
        links.new(pressure.outputs[0],emission.inputs[0])
        for frame in range(1,157,3):
            t=(frame-1)/24
            surge=ease((t-1.1)/.52)*(1-ease((t-2.05)/1.5))
            pressure.inputs[1].default_value=.44+.73*surge
            pressure.inputs[1].keyframe_insert("default_value",frame=frame)

    details=bpy.data.collections["Anomaly geometry"]
    mat=bpy.data.materials.new("Impact and wet highlight")
    mat.use_nodes=True
    surface=mat.node_tree.nodes.get("Principled BSDF")
    surface.inputs["Base Color"].default_value=(.25,.34,.105,1)
    surface.inputs["Roughness"].default_value=.19
    for i in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12)
        obj=bpy.context.object
        for coll in list(obj.users_collection):
            coll.objects.unlink(obj)
        details.objects.link(obj)
        obj.name=f"Small liquid impact {i+1}"
        obj.location=(.52,-.65+i*.06,-4.716+i*.001)
        obj.data.materials.append(mat)
        for frame in range(1,157,2):
            t=(frame-1)/24
            impact=(t+.22*i)%(1.02+i*.073)-.655
            active=t>1.4 and 0<=impact<.24
            size=.036+.082*max(0,impact)/.24
            obj.scale=(size,size*.76,.006 if active else .0005)
            obj.hide_render=obj.hide_viewport=not active
            obj.keyframe_insert("hide_render",frame=frame)
            obj.keyframe_insert("hide_viewport",frame=frame)
            obj.keyframe_insert("scale",frame=frame)
    image("vent_quiet",110)
    image("vent_pulse",47)
    cam.location=Vector((4.65,-3.45,-1.84))
    cam.rotation_euler=(Vector((.34,-.6,-4.29))-cam.location).to_track_quat("-Z","Y").to_euler()
    image("vent_drop_impact",112)
    cam.location=Vector((5.55,-2.35,.34))
    cam.rotation_euler=(Vector((.35,.02,-.56))-cam.location).to_track_quat("-Z","Y").to_euler()
elif kind=="Static":
    scene.frame_set(61)
    for item in bpy.data.collections["Calendar"].objects:
        item.location.z-=1.09
        item.keyframe_insert("location",frame=61)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=.032,depth=.022,
        location=(1008-1031.8,.223-17.1,6.74-5.36),rotation=(math.pi/2,0,0))
    obj=bpy.context.object
    obj.name="Old calendar pin"
    mat=bpy.data.materials.new("Aged pin")
    mat.diffuse_color=(.092,.082,.06,1)
    obj.data.materials.append(mat)
    for frame,visible in ((1,False),(41,False),(61,True),(81,False)):
        obj.hide_render=obj.hide_viewport=not visible
        obj.keyframe_insert("hide_render",frame=frame); obj.keyframe_insert("hide_viewport",frame=frame)
    image("calendar_old_pin",61)
else:
    raise ValueError(kind)

scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/("Kontur_"+kind+"_v32.blend")),compress=True)
