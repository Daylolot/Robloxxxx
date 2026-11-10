"""Update the portable studies for the v34 form, lettering and continuous drip."""
import math
from pathlib import Path
import re
import sys

import bpy
from mathutils import Matrix, Vector

kind, target = sys.argv[sys.argv.index("--") + 1:]
out = Path(target).resolve()
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
cam = scene.camera
fps = scene.render.fps
scene.eevee.taa_render_samples = 24


def ease(t):
    t = min(max(t, 0), 1)
    return t*t*(3-2*t)


def render(name, frame, position, aim, lens):
    scene.frame_set(frame)
    cam.location = position
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (Vector(aim)-cam.location).to_track_quat("-Z", "Y")
    cam.data.lens = lens
    scene.render.filepath = str(out / (name+".png"))
    bpy.ops.render.render(write_still=True)


def surface_text(collection, parent, text, location, size, style, mat):
    data = bpy.data.curves.new(text, "FONT")
    data.body = text
    data.font = style
    data.size = size
    data.align_x = "CENTER"
    data.align_y = "CENTER"
    data.materials.append(mat)
    obj = bpy.data.objects.new(text, data)
    collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    return obj


def quad(collection, parent, name, width, height, location, mat):
    mesh = bpy.data.meshes.new(name)
    w, h = width*.5, height*.5
    mesh.from_pydata([(-w,-h,0), (w,-h,0), (w,h,0), (-w,h,0)], [], [(0,1,2,3)])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    return obj


def finish(name,rgb,metal=0,rough=.58):
    def linear(c):
        c /= 255
        return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*map(linear,rgb),1)
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = rough
    return mat


def box(collection,name,position,size,material,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    collection.objects.link(obj)
    for v in obj.data.vertices:
        for axis in range(3):
            v.co[axis] *= size[axis]
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Soft manufactured edges","BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return obj


def hall_ceiling():
    environment = bpy.data.collections["Surveyed office"]
    acoustic = finish("Acoustic tiles",(206,207,190))
    seams = finish("Tile tracks",(92,103,96))
    plaster = finish("Upper plaster",(225,226,211))
    box(environment,"Ceiling panels",(4.0,0,6.75),(7.55,25,.13),acoustic)
    box(environment,"Wall between top rail and ceiling",(-.2,0,5.75),(.4,25,1.88),plaster)
    for i in range(17):
        box(environment,"Tile track",(4.0,(i-8)*1.5,6.68),(7.55,.018,.025),seams)
    for i in range(5):
        box(environment,"Tile track",(.3+1.50*i,0,6.68),(.018,25,.025),seams)


if kind == "Printer":
    collection = bpy.data.collections["Receipt · once per viewer"]
    ink = bpy.data.materials["Тонер"]
    seal = bpy.data.materials.new("Faded red ink")
    seal.diffuse_color = (.22,.043,.033,1)
    seal.roughness = .82
    top, bottom = (bpy.data.objects[f"Receipt half {i}"] for i in (1,2))
    first, second = (bpy.data.objects[name] for name in ("ПОДТВЕРДИТЕ","ПОЛУЧЕНИЕ"))
    first.location.y = -.074
    second.location.y = .081
    font = first.data.font
    surface_text(collection,top,"ВХОДЯЩЕЕ",(-.24,.093,.006),.060,font,ink)
    surface_text(collection,top,"№ 047",(.36,.093,.006),.060,font,ink)
    stamp = surface_text(collection,bottom,"ОЖИДАЕТСЯ",(.23,-.078,.006),.049,font,seal)
    stamp.rotation_euler.z = math.radians(5)
    for y in (-.044,.044):
        quad(collection,stamp,"Stamp rule",.35,.006,(0,y,.001),seal)
    for x in (-.175,.175):
        quad(collection,stamp,"Stamp edge",.006,.088,(x,0,.001),seal)
    quad(collection,bottom,"Signature line",.36,.003,(-.247,-.106,.006),ink)
    eye = Vector((1,-4,5.25))
    finish = Vector((1,.25,5.25))
    entry = Vector((3,1.75,5.95))
    leave = Vector((1,1.15,7.15))
    for i, leaf in enumerate((top,bottom)):
        sign = 1 if i==0 else -1
        for frame in range(1,scene.frame_end+1,2):
            t = (frame-1)/fps-7.45-4.65
            pos = entry.lerp(finish,ease(t/.86)).lerp(leave,ease((t-2.94)/.68))
            facing = (eye-pos).to_track_quat("Z","Y").to_matrix()
            turn = .33*ease((t-1.04)/.46)*(1-ease((t-2.78)/.48))
            motion = Matrix.Rotation(turn-.91*(1-ease(t/.86)),3,"Y")
            close = ease((t-2.78)/.42)
            crease = close*1.41+(1-close)*(.055+.025*math.sin(t*3.6))
            fold = Matrix.Rotation(sign*crease,3,"X")
            rot = facing @ motion @ fold
            leaf.location = pos+rot@Vector((0,sign*.17,0))
            leaf.rotation_quaternion = rot.to_quaternion()
            leaf.keyframe_insert("location",frame=frame)
            leaf.keyframe_insert("rotation_quaternion",frame=frame)
    for obj in collection.objects:
        if obj in (top,bottom,first,second):
            continue
        for frame, hidden in ((1,True),(1+math.ceil((7.45+4.65)*fps),False),(1+math.ceil((7.45+8.27)*fps),True)):
            obj.hide_render = obj.hide_viewport = hidden
            obj.keyframe_insert("hide_render",frame=frame)
            obj.keyframe_insert("hide_viewport",frame=frame)
    render("printer_form",1+round(13.12*fps),eye,finish,41)
    render("printer_side",1+round(13.76*fps),(2.60,-4,5.25),finish,41)
    render("printer_fold",1+round(15.13*fps),(2.35,-3.3,5.47),(1,.26,5.30),46)

elif kind == "Archive":
    collection = bpy.data.collections["Anomaly geometry"]
    advances = {" ":40,"Г":59,"Д":75,"Ж":87,"З":64,"Л":70,"О":76,"Т":65,"Ш":86,"Ы":84,"Ь":66}
    trails = [o for o in collection.objects if o.name.startswith("Pigment under glyph")]
    for prefix, text in (("First ","НЕ ОГЛЯДЫВАЙСЯ"),("Return ","ТЕПЕРЬ ПОЗДНО")):
        widths = [advances.get(c,70)*8.1/1120 for c in text]
        cursor = -sum(widths)*.5
        for index, (char,width) in enumerate(zip(text,widths)):
            if char != " ":
                glyph = bpy.data.objects[prefix+str(index)]
                new_y = -cursor-width*.5
                for trail in trails:
                    if (trail.location-(glyph.location+Vector((-.001,.032,-.255)))).length<.005:
                        trail.location.y += new_y-glyph.location.y
                        trails.remove(trail)
                        break
                glyph.location.y = new_y
            cursor += width
    render("archive_first",61,(-6.2,2.1,-.18),(0,0,0),28)
    render("archive_return",148,(-5.5,.05,-.18),(0,0,0),26)

elif kind == "Vent":
    collection = bpy.data.collections["Anomaly geometry"]
    hall_ceiling()
    mount = bpy.data.objects.new("Mount · 60% · below ceiling",None)
    collection.objects.link(mount)
    for obj in list(collection.objects):
        if obj!=mount and not obj.parent and not obj.name.startswith(
                ("Green droplet","Green wetness on floor","Single wet footprint")):
            obj.parent=mount
    mount.location=(0,-3.7,5.79)
    mount.scale=(.60,.60,.60)
    tip = Vector((.044,-4.06,4.698))
    runnel = bpy.data.objects["Tapered green runnel"].data
    runnel.splines[0].bezier_points[-1].co = (tip-mount.location)/.60
    runnel.animation_data_clear()
    for frame, progress in ((1,0),(12,0),(41,1)):
        runnel.bevel_factor_end = progress
        runnel.keyframe_insert("bevel_factor_end",frame=frame)
    for i,offset,count,step,width,delay,bend in (
        (1,-.50,6,.052,.025,.26,-.015),(2,.56,5,.043,.020,.58,.019)
    ):
        curve = bpy.data.curves.new(f"Side runoff {i}","CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = width*.46
        curve.bevel_resolution = 5
        curve.materials.append(runnel.materials[0])
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(count)
        for j,point in enumerate(spline.bezier_points):
            point.co = (.035,-3.7-offset-math.sin(j*.73)*bend-j*.0024,5.16-j*step)
            point.handle_left_type = point.handle_right_type = "AUTO"
            point.radius = 1-.77*j/count
        obj = bpy.data.objects.new(curve.name,curve)
        collection.objects.link(obj)
        for when,end in ((1,0),(round((.39+delay)*fps),0),(round((.91+delay+.09*count)*fps),1)):
            curve.bevel_factor_end = end
            curve.keyframe_insert("bevel_factor_end",frame=when)
    drops = sorted((o for o in collection.objects if o.name.startswith("Green droplet")),key=lambda o:o.name)
    for obj in drops[3:]:
        bpy.data.objects.remove(obj,do_unlink=True)
    bead = bpy.data.objects.new("Bead attached to runnel",drops[0].data)
    collection.objects.link(bead)
    fall = math.sqrt((4.67+tip.z-.022)/6.7)
    for i,obj in enumerate(drops[:3]):
        obj.animation_data_clear()
        for face in obj.data.polygons:
            face.use_smooth = True
        width = .016+i*.0014
        period = 2.34+i*.23
        for frame in range(1,scene.frame_end+1):
            t = (frame-1)/fps
            age = (t+i*.69)%period
            spread = i*.008
            obj.location = tip+Vector((.16*age+.058*age**2,-spread-.032*age,-.022-6.7*age**2))
            obj.scale = (width,width,width*(1.05+1.35*min(age/fall,1)))
            obj.hide_render = obj.hide_viewport = t<1.1 or age>fall
            for attr in ("location","scale","hide_render","hide_viewport"):
                obj.keyframe_insert(attr,frame=frame)
            if i==0:
                charge = ease((age-period+.44)/.44) if t>=1.1 else 0
                bead.scale = Vector((width,width,width*(.55+.70*charge)))*max(.1,charge)
                bead.location = tip+Vector((0,-spread,-bead.scale.z))
                bead.hide_render = bead.hide_viewport = charge<=0
                for attr in ("location","scale","hide_render","hide_viewport"):
                    bead.keyframe_insert(attr,frame=frame)
    footprint = bpy.data.objects["Single wet footprint"]
    footprint.location = (tip.x+.16*fall+.058*fall**2,tip.y-.032*fall,-4.718)
    for v in footprint.data.vertices:
        v.co.x *= .70
        v.co.y *= .68
    render("vent_bead",57,(1.41,-4.82,5.23),(.04,-4.06,4.91),46)
    render("vent_detach",62,(1.41,-4.82,5.23),(.04,-4.06,4.90),46)
    render("vent_trails",73,(2.45,-4.64,5.43),(.15,-3.74,5.22),46)
    render("vent_under_ceiling",79,(5.70,-7.60,.40),(.23,-3.70,5.35),30)
    render("vent_runoff",140,(3.02,-5.63,-2.41),(.31,-4.07,-3.73),45)

elif kind == "Door":
    hall_ceiling()
    collection = bpy.data.collections["Anomaly geometry"]
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    source=Path(__file__).with_name("DoorParts.luau").read_text()
    parts=re.findall(r'\{"([^"]+)",([^{}]+)\}',source)
    assert len(parts)==28
    paint={}
    for name, fields in parts:
        fields=fields.split(",")
        u,y,n,w,h,d,r,g,b=map(float,fields[:-1])
        metal=fields[-1]=="true"
        key=(r,g,b,metal)
        if key not in paint:
            paint[key]=finish(name,(r,g,b),.36 if metal else 0,.38 if metal else .58)
        box(collection,name,(.15+n,6.10-u,y-4.72),(d,w,h),paint[key],min(.014,d*.14,w*.15,h*.15))
    font=bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    font.pack()
    ink=finish("Identification ink",(38,52,47))
    label=surface_text(collection,None,"СЛУЖЕБНАЯ",(.271,6.10,1.62),.20,font,ink)
    label.rotation_euler=Matrix(((0,0,1),(1,0,0),(0,1,0))).to_euler()
    marker=bpy.data.objects.new("Audio source behind the leaf",None)
    marker.location=(.02,6.10,-.27)
    collection.objects.link(marker)
    for name,frame in (("Breath near the door",10),("First knock",36),("Second knock",44),("Second breath",92)):
        scene.timeline_markers.new(name,frame=frame)
    render("door_corridor",1,(7.10,.86,.17),(.28,6.10,.04),20)
    render("door_handle",1,(2.25,8.15,-.12),(.37,7.44,-.22),51)

else:
    raise ValueError(kind)

scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out / f"Kontur_{kind}_v34.blend"),compress=True)
