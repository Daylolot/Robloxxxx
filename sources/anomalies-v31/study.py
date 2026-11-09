"""Build reproducible player-eye studies from surveyed office geometry."""
import math
import json
from pathlib import Path
from random import Random
import sys

import bpy
from mathutils import Matrix, Vector

root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
from vent_spec import parts

scene_type, revision_text, out_text=sys.argv[sys.argv.index("--")+1:]
revision=int(revision_text)
out=Path(out_text).resolve()
out.mkdir(parents=True,exist_ok=True)
anchor=(1031.8,5.36,-17.1) if scene_type in ("archive","static") else (1000.2,4.82,45.8)
basis=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
def point(p):
    return basis@(Vector(p)-Vector(anchor))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version<(5,0,0) else "BLENDER_EEVEE"
scene.eevee.taa_render_samples=20
scene.render.resolution_x=1120
scene.render.resolution_y=704
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.render.fps=24
scene.frame_end=156
scene.world=bpy.data.worlds.new("Office ambient")
scene.world.use_nodes=True
scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.32,.4,.41,1)
scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.43

def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c

environment=collection("Surveyed office")
detail=collection("Anomaly geometry")
lighting=collection("Office fixtures and camera")
def move(obj, coll):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj

def srgb(v):
    v/=255
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

material_cache={}
def material(rgb,metallic=0,roughness=.63):
    key=rgb,metallic,roughness
    if key in material_cache: return material_cache[key]
    mat=bpy.data.materials.new("Finish "+str(rgb))
    mat.use_nodes=True
    node=mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value=(*map(srgb,rgb),1)
    node.inputs["Roughness"].default_value=roughness
    node.inputs["Metallic"].default_value=metallic
    material_cache[key]=mat
    return mat

def box(name,pos,size,mat,coll=detail,rot=None,bevel=0):
    mesh=bpy.data.meshes.new(name)
    vertices=[(x*size[0],y*size[1],z*size[2]) for x,y,z in
        ((-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),
         (-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5))]
    faces=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
    mesh.from_pydata(vertices,[],faces)
    obj=bpy.data.objects.new(name,mesh)
    coll.objects.link(obj)
    obj.location=pos
    if rot is not None: obj.rotation_euler=rot
    obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new("Manufactured radius","BEVEL"); mod.width=bevel; mod.segments=3
        obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return obj

geometry_path=root/("HallGeometry.json" if scene_type=="vent" else "ArchiveGeometry.json")
for name,cf,size,color in json.loads(geometry_path.read_text()):
    rgb=((color>>16)&255,(color>>8)&255,color&255)
    rotation=basis@Matrix((cf[3:6],cf[6:9],cf[9:12]))
    box(name,point(cf[:3]),size,material(rgb),environment,rotation.to_euler())

def area(name,position,target,energy,size,color):
    data=bpy.data.lights.new(name,"AREA"); data.energy=energy; data.shape="DISK"; data.size=size; data.color=color
    obj=bpy.data.objects.new(name,data); lighting.objects.link(obj)
    obj.location=point(position); obj.rotation_euler=(point(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def camera(position,target,lens):
    data=bpy.data.cameras.new("Player lens"); data.lens=lens; data.clip_start=.025
    obj=bpy.data.objects.new("Player eyes",data); lighting.objects.link(obj)
    obj.location=point(position); obj.rotation_euler=(point(target)-obj.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=obj
    return obj

def render(name, frame):
    scene.frame_set(frame)
    scene.render.filepath=str(out/(name+".png"))
    bpy.ops.render.render(write_still=True)

def keys(obj,states):
    for frame,hidden in states:
        obj.hide_render=hidden
        obj.hide_viewport=hidden
        obj.keyframe_insert("hide_render",frame=frame)
        obj.keyframe_insert("hide_viewport",frame=frame)

if scene_type in ("archive","static"):
    area("Archive fluorescent", (1027.0,8.75,-16.1), (1031.8,4.9,-17.1), 480,4.8,(.91,.95,1))
    area("Bounce off cabinet",(1024,5.3,-11),(1031.8,5.2,-17.1),125,4,(.92,.84,.67))
else:
    area("Corridor strip",(1004,8.85,44.2),(1000.3,4.25,45.8),500,4.2,(.90,.96,1))
    area("Warm end of corridor",(1004,6.55,51.0),(1000.3,3.1,45.8),120,4,(1,.85,.65))

random=Random(3157)
if scene_type=="archive":
    cam=camera((1026.1,5.22,-15.95),(1031.8,5.33,-17.1),29 if revision>=2 else 34)
    font=bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    font.pack()
    writing_basis=Matrix(((0,0,-1),(-1,0,0),(0,1,0)))
    def pigment(color):
        mat=material(color,0,.84)
        if revision<3 or mat.get("pigment"): return mat
        mat["pigment"]=True
        nodes=mat.node_tree.nodes
        links=mat.node_tree.links
        noise=nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=104
        noise.inputs["Detail"].default_value=3
        coord=nodes.new("ShaderNodeTexCoord")
        if revision>=5:
            grain=nodes.new("ShaderNodeVectorMath")
            grain.operation="MULTIPLY"
            grain.inputs[1].default_value=(.47,1.6,1)
            links.new(coord.outputs["Object"],grain.inputs[0])
            links.new(grain.outputs[0],noise.inputs["Vector"])
        else:
            links.new(coord.outputs["Object"],noise.inputs["Vector"])
        ramp=nodes.new("ShaderNodeValToRGB")
        low,high=ramp.color_ramp.elements
        low.position=.25
        high.position=.82
        low.color=(*[srgb(v)*.63 for v in color],1)
        high.color=(*[srgb(v)*1.56 for v in color],1)
        if revision>=5:
            wear=ramp.color_ramp.elements.new(.765)
            wear.color=(*[srgb(v)*1.29 for v in color],1)
            high.color=(.165,.157,.14,1)
        links.new(noise.outputs["Fac"],ramp.inputs[0])
        links.new(ramp.outputs["Color"],nodes.get("Principled BSDF").inputs["Base Color"])
        return mat
    def write(text,final):
        count=len(text)
        for index,char in enumerate(text):
            if char==" ": continue
            data=bpy.data.curves.new(char,"FONT")
            data.font=font; data.body=char; data.align_x="CENTER"; data.align_y="CENTER"
            data.size=(.66 if revision<2 else .71)*random.uniform(.94,1.055)
            data.extrude=.0008
            color=(99,63,56) if not final else (119,42,34)
            if revision>=3:
                color=tuple(max(0,i+random.randint(-13,9)) for i in color)
            data.materials.append(pigment(color))
            obj=bpy.data.objects.new(("Return " if final else "First ")+str(index),data)
            detail.objects.link(obj)
            x=(index-(count-1)*.5)*(.441 if revision<2 else .423)
            obj.location=Vector((-.015,-x,random.uniform(-.055,.055) if revision>=2 else 0))
            obj.rotation_euler=(writing_basis@Matrix.Rotation(random.uniform(-.071,.071) if revision>=2 else 0,3,"Z")).to_euler()
            if final:
                keys(obj,[(1,True),(100+index,False)])
            elif revision>=2:
                keys(obj,[(1,True),(19+index,False),(88,True)])
    write("НЕ ОГЛЯДЫВАЙСЯ",False)
    if revision>=4: write("ТЕПЕРЬ ПОЗДНО",True)
    if revision>=3:
        for i in range(13 if revision>=5 else 21):
            x=random.uniform(-3.13,3.13)
            z=random.uniform(-.42,-.235)
            h=random.uniform(.016,.079 if revision>=5 else .14)
            obj=box("Pigment trace",(-.017,x,z),(.003,random.uniform(.008,.023),h),
                material((95,53,44),0,.95),rot=(random.uniform(-.21,.19),0,0))
            keys(obj,[(1,True),(25+i%15,False)])
    if revision>=4:
        poses={1:((1026.1,5.22,-15.95),(1031.8,5.33,-17.1)),
               62:((1026.1,5.22,-15.95),(1031.8,5.33,-17.1)),
               85:((1026.1,5.22,-15.95),(1019,5.3,-17.7)),
               98:((1026.1,5.22,-15.95),(1019,5.3,-17.7)),
               120:((1026.1,5.22,-15.95),(1031.8,5.33,-17.1))}
        cam.rotation_mode="QUATERNION"
        for frame,(pos,target) in poses.items():
            cam.location=point(pos); cam.rotation_quaternion=(point(target)-cam.location).to_track_quat("-Z","Y")
            cam.keyframe_insert("location",frame=frame); cam.keyframe_insert("rotation_quaternion",frame=frame)
    if revision==5:
        render("archive_05_before",60); render("archive_05_turn",88); render("archive_05_return",148)
    else:
        render(f"archive_{revision:02d}",61 if revision<4 else 146)
elif scene_type=="static":
    cam=camera((1021.0,6.46,-17.45),(1031.65,8.1,-17.55),27)
    font=bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    font.pack()
    for obj in environment.objects:
        obj.hide_render=True
        obj.hide_viewport=True
    sets={}
    backdrops={}
    area("West wall fixture",(995.45,7.34,49.4),(999.4,4.3,48),410,4.1,(.9,.96,1))
    area("Calendar fixture",(1011.4,7.95,-3.75),(1010.0,5.92,-.29),260,3.4,(.98,.95,.83))
    for name,center,span in (("Archive",(1031.9,5.15,-17.5),(17,10.1,.16)),
                             ("Calendar",(1009.5,5.15,-.10),(9.5,10.1,.16)),
                             ("Plant",(999.88,5.15,48),(9.5,10.1,.16))):
        backdrop=box(name+" wall",point(center),(.16,span[0],span[1]) if name!="Calendar" else (span[0],.16,span[1]),material((205,208,190)))
        backdrops[name]=backdrop
    for name in ("ArtA","ArtB","Calendar","Plant"):
        rows=json.loads((root/(name+"Geometry.json")).read_text())
        folder=collection(name)
        sets[name]=[]
        for label,cf,size,color in rows:
            rgb=((color>>16)&255,(color>>8)&255,color&255)
            rotation=basis@Matrix((cf[3:6],cf[6:9],cf[9:12]))
            obj=box(label,point(cf[:3]),size,material(rgb),folder,rotation.to_euler())
            sets[name].append((obj,obj.location.copy(),rgb))
        if name.startswith("Art"):
            z=-14 if name=="ArtA" else -21
            text="МИРОВАЯ ТОРГОВЛЯ" if name=="ArtA" else "ТЕХНОЛОГИИ"
            color=(56,112,127) if name=="ArtA" else (162,112,60)
            data=bpy.data.curves.new(text,"FONT")
            data.body=text; data.size=.33; data.font=font; data.align_x="CENTER"; data.align_y="CENTER"
            data.materials.append(material((50,65,64)))
            obj=bpy.data.objects.new(text,data); folder.objects.link(obj)
            obj.location=point((1031.57,9.02,z))
            obj.rotation_euler=Matrix(((0,0,-1),(-1,0,0),(0,1,0))).to_euler()
            sets[name].append((obj,obj.location.copy(),None))
            for i in range(5):
                h=.45+(i if name=="ArtA" else 4-i)*.18
                obj=box("Printed bar",point((1031.566,7.55+h*.5,z-1.48+i*.74)),(.009,.38,h),material(color),folder)
                sets[name].append((obj,obj.location.copy(),None))
        if name=="Calendar":
            x,y,z=1008,5.47,-.374
            heading=bpy.data.curves.new("Calendar heading","FONT")
            heading.body="НОЯБРЬ"; heading.size=.122; heading.font=font
            heading.align_x="CENTER"; heading.materials.append(material((37,65,62)))
            obj=bpy.data.objects.new(heading.name,heading); folder.objects.link(obj)
            obj.location=point((x,y+.55,z))
            obj.rotation_euler=Matrix(((-1,0,0),(0,0,1),(0,1,0))).to_euler()
            sets[name].append((obj,obj.location.copy(),None))
            for i in range(7):
                for j in range(5):
                    mat=material((87,116,104) if i<5 else (153,90,63))
                    mark=box("Calendar day",point((x+(i-3)*.16,y+.27-j*.177,z)),(.106,.005,.041),mat,folder)
                    sets[name].append((mark,mark.location.copy(),None))
    views={
        "Archive":((1021,6.46,-17.45),(1031.65,8.1,-17.55),("ArtA","ArtB")),
        "Calendar":((1009.55,5.68,-6.3),(1009.55,6.05,-.28),("Calendar",)),
        "Plant":((995.66,5.3,49.8),(999.4,4.41,48.0),("Plant",)),
    }
    for index,(mode,(position,target,visible)) in enumerate(views.items()):
        for name,obj in backdrops.items():
            keys(obj,[(1+index*40,name!=mode),(21+index*40,name!=mode)])
        for name,items in sets.items():
            for obj,location,rgb in items:
                keys(obj,[(1+index*40,name not in visible),(21+index*40,name not in visible)])
                if name not in visible: continue
                offset={"ArtA":(0,0,-7),"ArtB":(0,0,7),"Calendar":(2.45,.58,0),"Plant":(0,0,0)}[name]
                for frame,position_shift in ((1+index*40,Vector()),(21+index*40,basis@Vector(offset))):
                    obj.location=location+position_shift
                    obj.keyframe_insert("location",frame=frame)
                if mode=="Plant" and rgb and rgb[1]>rgb[0]*1.2 and rgb[1]>rgb[2]*1.17:
                    variant=obj.data.materials[0].copy()
                    node=variant.node_tree.nodes.get("Principled BSDF").inputs["Base Color"]
                    node.keyframe_insert("default_value",frame=81)
                    shifted=(min(255,88+rgb[1]/255*240),24+rgb[0]/255*65,78+rgb[2]/255*85)
                    node.default_value=(*map(srgb,shifted),1)
                    node.keyframe_insert("default_value",frame=101)
                    obj.data.materials[0]=variant
        cam.location=point(position)
        cam.rotation_euler=(point(target)-cam.location).to_track_quat("-Z","Y").to_euler()
        for frame in (1+index*40,21+index*40):
            cam.keyframe_insert("location",frame=frame)
            cam.keyframe_insert("rotation_euler",frame=frame)
        render("static_"+mode.lower()+"_before",1+index*40)
        render("static_"+mode.lower()+"_after",21+index*40)
else:
    box("Hall floor",point((1004,.05,45.8)),(7.98,23,.10),material((139,142,129)),environment)
    cam=camera((1005.75,5.16,48.15),(1000.55,4.26,45.78),32 if revision>=2 else 39)
    hinge=bpy.data.objects.new("Hatch hinge",None); detail.objects.link(hinge)
    hinge.location=(.17,.97,0)
    for name,x,y,z,w,h,d,r,g,b,moving,angle in parts(revision):
        obj=box(name,(z,-x,y),(d,w,h),material((r,g,b),0 if name=="DuctShadow" else .62,.36),
            rot=(0,-angle,0),bevel=.009 if min(w,h,d)>.04 else .002)
        if moving:
            matrix=obj.matrix_world.copy()
            bpy.context.view_layer.update()
            matrix=obj.matrix_world.copy()
            obj.parent=hinge; obj.matrix_world=matrix
    for frame,angle in ((1,0),(16,0),(38,math.radians(16)),(156,math.radians(16))):
        hinge.rotation_euler[2]=angle
        hinge.keyframe_insert("rotation_euler",frame=frame)
    if revision>=3:
        for i in range(17 if revision>=5 else 11):
            phase=i*.57
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10)
            obj=move(bpy.context.object,detail); obj.name=f"Vapor layer {i+1}"
            mat=bpy.data.materials.new(f"Vapor density {i+1}")
            mat.use_nodes=True
            nodes=mat.node_tree.nodes; nodes.clear()
            output=nodes.new("ShaderNodeOutputMaterial")
            volume=nodes.new("ShaderNodeVolumePrincipled")
            volume.inputs["Color"].default_value=(.29,.55,.13,1)
            volume.inputs["Anisotropy"].default_value=.22
            volume.inputs["Emission Color"].default_value=(.19,.38,.043,1)
            coord=nodes.new("ShaderNodeTexCoord")
            noise=nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value=4.6
            dist=nodes.new("ShaderNodeVectorMath"); dist.operation="DISTANCE"; dist.inputs[1].default_value=(.5,.5,.5)
            mask=nodes.new("ShaderNodeMapRange"); mask.inputs["From Min"].default_value=.07; mask.inputs["From Max"].default_value=.51; mask.inputs["To Min"].default_value=1; mask.inputs["To Max"].default_value=0
            density=nodes.new("ShaderNodeMath"); density.operation="MULTIPLY"
            strength=nodes.new("ShaderNodeMath"); strength.operation="MULTIPLY"
            strength.inputs[1].default_value=1.45 if revision>=4 else .75
            links=mat.node_tree.links
            for node in (noise,dist): links.new(coord.outputs["Generated"],node.inputs[0])
            links.new(dist.outputs["Value"],mask.inputs[0]); links.new(mask.outputs[0],density.inputs[0])
            links.new(noise.outputs["Fac"],density.inputs[1]); links.new(density.outputs[0],strength.inputs[0])
            links.new(strength.outputs[0],volume.inputs["Density"])
            emission=nodes.new("ShaderNodeMath"); emission.operation="MULTIPLY"; emission.inputs[1].default_value=.24
            links.new(strength.outputs[0],emission.inputs[0]); links.new(emission.outputs[0],volume.inputs["Emission Strength"])
            links.new(volume.outputs[0],output.inputs["Volume"])
            obj.data.materials.append(mat)
            keys(obj,[(1,True),(32+i,False)])
            for frame in range(1,157,3):
                t=frame/24
                q=(t*.39+phase)%1
                obj.location=(.26+2.65*q, .08+math.sin(q*6+phase)*(.09+.52*q), .03+.52*q+math.sin(q*6.3+phase)*.23)
                obj.scale=(.17+.56*q,.19+.65*q,.18+.54*q)
                obj.keyframe_insert("location",frame=frame); obj.keyframe_insert("scale",frame=frame)
                if revision>=5:
                    density_envelope=min(1,q/.19,(1-q)/.27)
                    strength.inputs[1].default_value=2.3*density_envelope
                    strength.inputs[1].keyframe_insert("default_value",frame=frame)
    if revision>=4:
        wet=material((86,130,35),.12,.19)
        tag=box("Maintenance plate",(.096,.27,-1.185),(.025,.96,.22),material((182,182,159),.5,.39),bevel=.009)
        data=bpy.data.curves.new("Maintenance identification","FONT")
        data.font=bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Bold.ttf"); data.font.pack()
        data.body="ВЫТЯЖКА  В-04"; data.size=.091; data.align_x="CENTER"; data.align_y="CENTER"
        data.materials.append(material((41,53,47)))
        label=bpy.data.objects.new(data.name,data); detail.objects.link(label)
        label.location=(.111,.27,-1.185)
        label.rotation_euler=Matrix(((0,0,1),(1,0,0),(0,1,0))).to_euler()
        if revision<5:
            for i in range(9):
                width=.017+random.random()*.033
                box("Wet track",(.030,-.58+math.sin(i*.8)*.019,-.89-i*.07),(.013,width,.114),wet,bevel=.005)
        else:
            track=bpy.data.curves.new("Runnel along plaster","CURVE")
            track.dimensions="3D"; track.bevel_depth=.022; track.bevel_resolution=5
            spline=track.splines.new("BEZIER"); spline.bezier_points.add(7)
            for i,bezier in enumerate(spline.bezier_points):
                bezier.co=(.032,-.58+math.sin(i*.73)*.021-i*.004,-1.05-i*.091)
                bezier.handle_left_type=bezier.handle_right_type="AUTO"
                bezier.radius=1-i*.105
            obj=bpy.data.objects.new("Tapered green runnel",track); detail.objects.link(obj)
            track.materials.append(wet)
            for frame,end in ((1,0),(31,0),(70,1)):
                track.bevel_factor_end=end
                track.keyframe_insert("bevel_factor_end",frame=frame)
        for i in range(6):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10)
            drop=move(bpy.context.object,detail); drop.name="Green droplet"
            drop.scale=(.020,.021,.047); drop.data.materials.append(wet)
            keys(drop,[(1,True),(37+i*3,False)])
            for frame in range(1,157,2):
                t=(frame/24+i*.143)%(1.05+i*.039)
                y=-1.12-6.2*t*t
                drop.location=(.12+t*.32,-.59+i*.013,max(-4.695,y))
                if revision>=5 and frame>=37+i*3:
                    drop.hide_render=drop.hide_viewport=y< -4.69
                    drop.keyframe_insert("hide_render",frame=frame); drop.keyframe_insert("hide_viewport",frame=frame)
                drop.keyframe_insert("location",frame=frame)
        if revision>=5:
            for i in range(5):
                bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12)
                puddle=move(bpy.context.object,detail); puddle.name="Green wetness on floor"
                puddle.location=(.38+i*.061,-.57+random.uniform(-.19,.21),-4.72+i*.0005)
                puddle.scale=(.17+i*.03,.13+i*.026,.008)
                puddle.data.materials.append(wet)
                keys(puddle,[(1,True),(51+i*6,False)])
    if revision==5:
        render("vent_05_closed",1); render("vent_05_active",124)
        cam.location=point((1003.1,4.45,47.6))
        cam.rotation_euler=(point((1000.65,4.31,46.0))-cam.location).to_track_quat("-Z","Y").to_euler()
        render("vent_05_close",124)
        cam.location=point((1004.85,2.98,49.25))
        cam.rotation_euler=(point((1000.56,1.61,46.33))-cam.location).to_track_quat("-Z","Y").to_euler()
        render("vent_05_runoff",124)
        cam.location=point((1005.75,5.16,48.15))
        cam.rotation_euler=(point((1000.55,4.14,45.78))-cam.location).to_track_quat("-Z","Y").to_euler()
    else:
        render(f"vent_{revision:02d}",124)

if revision==5:
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/("Kontur_"+scene_type.title()+"_v31.blend")),compress=True)
