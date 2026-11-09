"""Check the posed arm joints and fingertip heights, then render matched views."""

import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


old, new = map(Path, sys.argv[sys.argv.index("--") + 1:])
out = new.parent
bpy.ops.wm.open_mainfile(filepath=str(new.resolve()))
scene = bpy.context.scene
rig = bpy.data.objects["OfficeWorker anatomical rig"]
skin = bpy.data.objects["Worker / face neck forearms and hands"]
upper = rig.parent.parent
report_path = out / "Pose_Check.json"
report = json.loads(report_path.read_text())
keys = {row["finger"]: bpy.data.objects[row["key"]] for row in report["plannedContacts"]}
contacts = []
gaps = []
for frame, side, digit in report["strikes"]:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    forearm, hand = (rig.pose.bones[f"{part}.{side}"] for part in ("forearm", "hand"))
    gaps.append((forearm.tail - hand.head).length)
    name = f'{("Index", "Middle", "Ring", "Little")[digit]}.{side}'
    key = keys[name]
    position, size = key.location, key.dimensions
    evaluated = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    transform = upper.matrix_world.inverted() @ evaluated.matrix_world
    patch = [p.z - position.z - size.z / 2 for v in mesh.vertices
             if abs((p := transform @ v.co).x-position.x) < size.x/2
             and abs(p.y-position.y) < size.y/2 and .75 < p.z < .95]
    clearance = min(patch, default=1)
    evaluated.to_mesh_clear()
    assert -.0015 <= clearance <= .002, (frame, name, clearance)
    contacts.append({"frame": frame, "finger": name, "clearanceMm": clearance * 1000})
assert max(gaps) < .0001
report.update(checkedStrikes=contacts, maxWristGapMm=max(gaps) * 1000)
report_path.write_text(json.dumps(report, indent=2) + "\n")
print("CHECKED", len(contacts), max(gaps), flush=True)

views = [
    ("01_v23_side", old, (.83, -.42, 1.13)),
    ("02_v24_side", new, (.83, -.42, 1.13)),
    ("03_v24_other_side", new, (-.83, -.42, 1.13)),
]
for filename, source, position in views:
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
    scene = bpy.context.scene
    scene.frame_set(21)
    camera = scene.camera
    camera.animation_data_clear()
    camera.data.animation_data_clear()
    upper = bpy.data.objects["UPPER_OFFICE / local inverted gravity"]
    upper.location = (0, 0, 0)
    upper.rotation_euler = (0, 0, 0)
    visible = set(upper.children_recursive) | {upper, camera}
    for obj in scene.objects:
        if obj not in visible:
            obj.hide_render = True
    light = bpy.data.lights.new("Comparison softbox", "AREA")
    light.energy, light.shape, light.size = 30, "DISK", .9
    softbox = bpy.data.objects.new(light.name, light)
    scene.collection.objects.link(softbox)
    softbox.location = (.1, -.65, 1.8)
    camera.location = position
    camera.rotation_euler = (Vector((0, -.43, .95)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 44
    scene.render.use_sequencer = False
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str((out / (filename + ".png")).resolve())
    bpy.ops.render.render(write_still=True)
