"""Preview the v35 door response and the two-stage condensation paths."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

kind, target = sys.argv[sys.argv.index("--")+1:]
out = Path(target).resolve()
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
cam = scene.camera
fps = scene.render.fps
collection = bpy.data.collections["Anomaly geometry"]


def ease(t):
    t = min(max(t, 0), 1)
    return t*t*(3-2*t)


def show(obj, visible, frame):
    obj.hide_render = obj.hide_viewport = not visible
    obj.keyframe_insert("hide_render", frame=frame)
    obj.keyframe_insert("hide_viewport", frame=frame)


def render(name, t, position, target, lens):
    scene.frame_set(round(t*fps)+1)
    cam.location = position
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (Vector(target)-cam.location).to_track_quat("-Z","Y")
    cam.data.lens = lens
    scene.render.filepath = str(out / (name+".png"))
    bpy.ops.render.render(write_still=True)


def trajectory(tip, age):
    return tip+Vector((.16*age+.058*age**2,-.032*age,-.022-6.7*age**2))


if kind == "Vent":
    drops = sorted((obj for obj in collection.objects if obj.name.startswith("Green droplet")),key=lambda obj:obj.name)
    for obsolete in drops[2:]:
        bpy.data.objects.remove(obsolete, do_unlink=True)
    bead = bpy.data.objects["Bead attached to runnel"]
    main = bpy.data.objects["Single wet footprint"]
    for obj in (bead, main):
        obj.animation_data_clear()
    side = main.copy()
    side.data = main.data.copy()
    for vertex in side.data.vertices:
        x,y,_ = vertex.co
        vertex.co.x = .87*x+.18*y
        vertex.co.y = .63*y-.025*math.sin(x*13)+.04*x
    side.name = "Side wet footprint"
    collection.objects.link(side)
    bead_side = bead.copy()
    bead_side.name = "Side bead attached to runnel"
    collection.objects.link(bead_side)
    side_tip_y = -3.70+.50+math.sin(6*.73)*.015-6*.0024
    streams = (
        (drops[0],bead,main,Vector((.044,-4.061,4.698)),2.34,2.34,.018,1),
        (drops[1],bead_side,side,Vector((.044,side_tip_y,4.842)),3.85,4.21,.0145,.70),
    )
    scene.frame_end = 181
    for drop, bead, puddle, tip, start, period, width, scale in streams:
        drop.animation_data_clear()
        fall = math.sqrt((tip.z+4.67-.022)/6.7)
        landing = trajectory(tip,fall)
        puddle.location = (landing.x,landing.y,-4.718)
        splash_mesh = puddle.data.copy()
        splash = bpy.data.objects.new("Impact spread",splash_mesh)
        splash.location = (landing.x,landing.y,-4.716)
        collection.objects.link(splash)
        for frame in range(1,scene.frame_end+1):
            t = (frame-1)/fps
            age = (t-start)%period
            charge = ease((age-period+.44)/.44) if t>=start-.44 else 0
            bead.scale = Vector((width,width,width*(.55+.70*charge)))*max(.04,charge)
            bead.location = tip-Vector((0,0,bead.scale.z))
            bead.keyframe_insert("location",frame=frame)
            bead.keyframe_insert("scale",frame=frame)
            show(bead,charge>0,frame)
            drop.location = trajectory(tip,age)
            drop.scale = (width,width,width*(1.05+1.35*min(age/fall,1)))
            drop.keyframe_insert("location",frame=frame)
            drop.keyframe_insert("scale",frame=frame)
            show(drop,t>=start and age<fall,frame)
            growth = ease((t-start-fall)/5.2)
            puddle.scale = (scale*(.34+.66*growth),scale*(.4+.6*growth),1)
            puddle.keyframe_insert("scale",frame=frame)
            show(puddle,t>=start+fall,frame)
            impact = age-fall
            size = scale*(.19+.25*ease(impact/.26))
            splash.scale = (size,size,1)
            splash.keyframe_insert("scale",frame=frame)
            show(splash,t>=start and 0<=impact<.26,frame)
    for name,time in (("Первый отрыв",2.34),("Первое пятно",3.52),("Отрыв второго потёка",3.85),("Второй след",5.03)):
        scene.timeline_markers.new(name,frame=round(time*fps)+1)
    render("vent_sources",3.77,(2.40,-4.64,5.43),(.15,-3.73,5.09),43)
    render("vent_drop_side",4.04,(2.03,-4.40,5.08),(.12,-3.33,4.86),43)
    render("vent_floor_two_marks",7.25,(2.55,-5.06,-2.70),(.32,-3.62,-4.66),42)
elif kind == "Door":
    pivot = bpy.data.objects.new("Lever axis at the latch",None)
    collection.objects.link(pivot)
    pivot.location = (.386,7.58,-.29)
    bpy.context.view_layer.update()
    for name in ("Lever","LeverTip"):
        obj=bpy.data.objects[name]
        matrix=obj.matrix_world.copy()
        obj.parent=pivot
        obj.matrix_world=matrix
    for frame in range(1,scene.frame_end+1):
        t=(frame-1)/fps
        angle=0
        for knock,kick in ((1.46,.145),(1.79,.082)):
            age=t-knock
            if 0<=age<.32:
                angle=kick*math.sin(age*38)*(1-age/.32)**2
        pivot.rotation_euler.x=angle
        pivot.keyframe_insert("rotation_euler",frame=frame)
    render("door_handle_rest",1.33,(1.6,7.93,-.13),(.38,7.38,-.28),54)
    render("door_handle_knock",1.50,(1.6,7.93,-.13),(.38,7.38,-.28),54)
    render("door_at_player_height",.40,(7.10,.86,.17),(.28,6.10,.04),18)
else:
    raise ValueError(kind)

scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/f"Kontur_{kind}_v35.blend"),compress=True)
