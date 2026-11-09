"""Straighten the seated worker's wrist line and animate the office map."""

import json
import math
from pathlib import Path
import shutil

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "outputs/CeilingWorker_2026-11-08"
BASE = PROJECT / "Revision20"
OUT = PROJECT / "Revision21"
if (ROOT / "models").is_dir():
    BASE = ROOT / "models/ceiling-worker-v20"
    OUT = ROOT / "models/ceiling-worker-v21"
OUT.mkdir(exist_ok=True)
SOURCE = BASE / "Ceiling_Office_Character_Study_v20.blend"
TARGET = OUT / "Ceiling_Office_Character_Study_v21.blend"
KEYBOARD_SHIFT = Vector((0, -.074, 0))
WORLD_MAP_ORIGIN = Vector((1020, 0, 44.35))
METRES_PER_STUD = .28


def update():
    bpy.context.view_layer.update()


def aim_segment(rotation, origin, end, bone, width, depth):
    axis = rotation @ Vector((0, 1, 0))
    rotation = axis.rotation_difference(end - origin) @ rotation
    matrix = rotation.to_matrix().to_4x4()
    matrix.col[0] *= width
    matrix.col[1] *= (end - origin).length / bone.bone.length
    matrix.col[2] *= depth
    matrix.translation = origin
    return matrix


def bend(forearm, hand):
    return math.degrees((forearm.tail - forearm.head).angle(hand.tail - hand.head))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
rig = bpy.data.objects["OfficeWorker anatomical rig"]
scene.frame_set(120)
update()
repose = {}
forearm_transforms = {}
arm_report = {}
for side in ("L", "R"):
    upper = rig.pose.bones["upper_arm." + side]
    fore = rig.pose.bones["forearm." + side]
    hand = rig.pose.bones["hand." + side]
    old_forearm = fore.matrix.copy()
    old_elbow = fore.head.copy()
    shoulder = upper.head.copy()
    wrist = hand.head + KEYBOARD_SHIFT
    fore_length = fore.length
    upper_length = upper.length
    hand_axis = (hand.tail - hand.head).normalized()
    straight_elbow = wrist - hand_axis * fore_length
    chain = wrist - shoulder
    distance = chain.length
    assert abs(upper_length - fore_length) < distance < upper_length + fore_length
    chain.normalize()
    projection = (upper_length ** 2 - fore_length ** 2 + distance ** 2) / (2 * distance)
    radius = math.sqrt(upper_length ** 2 - projection ** 2)
    # With both endpoints and lengths fixed, the elbow can lie on a circle.
    # Choose the position nearest to the straight line behind the hand.
    elbow_direction = straight_elbow - shoulder
    elbow_direction -= chain * elbow_direction.dot(chain)
    elbow = shoulder + chain * projection + elbow_direction.normalized() * radius
    upper_rotation = upper.matrix.to_quaternion()
    # Match the radial direction of the arm skin to the back of the hand.
    hand_deform = (hand.matrix @ hand.bone.matrix_local.inverted()).to_quaternion()
    fore_rotation = hand_deform @ fore.bone.matrix_local.to_quaternion()
    hand_pose = hand.matrix.copy()
    hand_pose.translation = wrist
    repose[side] = (
        aim_segment(upper_rotation, shoulder, elbow, upper, 1, 1),
        aim_segment(fore_rotation, elbow, wrist, fore, old_forearm.col[0].length, old_forearm.col[2].length),
        hand_pose,
    )
    forearm_transforms[side] = repose[side][1] @ old_forearm.inverted()
    arm_report[side] = {
        "v20BendDegrees": bend(fore, hand),
        "v20ElbowGapMm": (upper.tail - old_elbow).length * 1000,
        "elbowLiftMm": (elbow.z - old_elbow.z) * 1000,
        "upperLengthMm": upper_length * 1000,
        "forearmLengthMm": fore_length * 1000,
    }

for frame in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(frame)
    for side, poses in repose.items():
        for name, pose in zip(("upper_arm", "forearm", "hand"), poses):
            bone = rig.pose.bones[f"{name}.{side}"]
            bone.matrix = pose
            update()
            for prop in ("location", "rotation_quaternion", "scale"):
                bone.keyframe_insert(prop, frame=frame)

# Blender stores the child pose as rotation, location and scale. The new
# nonuniform forearm can change the evaluated hand transform slightly on bake.
# Correct this on the hand side of the seam so the fingertip poses still meet
# the same caps, and ease the correction out into the forearm.
scene.frame_set(120)
update()
skin = bpy.data.objects["Worker / face neck forearms and hands"]
shapes = skin.data.shape_keys.key_blocks
for side, poses in repose.items():
    hand = rig.pose.bones[f"hand.{side}"]
    rest = hand.bone.matrix_local
    correction = rest @ hand.matrix.inverted() @ poses[2] @ rest.inverted()
    group = skin.vertex_groups[hand.name].index
    for vertex in skin.data.vertices:
        weight = next((item.weight for item in vertex.groups if item.group == group), 0)
        influence = min(1, max(0, (weight - .68) / .27))
        if not influence:
            continue
        influence = influence * influence * (3 - 2 * influence)
        for shape in shapes:
            point = shape.data[vertex.index]
            point.co = point.co.lerp(correction @ point.co, influence)

for cuff in (obj for obj in scene.objects if obj.name.startswith("Worker / sewn sleeve cuff")):
    x = sum(v.co.x for v in cuff.data.vertices)
    cuff.data.transform(forearm_transforms["L" if x > 0 else "R"])

keyboard = [obj for obj in scene.objects
            if obj.name.startswith("Keyboard key") or obj.name in {"Space bar", "Keyboard shell"}]
for obj in keyboard:
    # Existing key curves animate only Z. Preserve their travel and timing.
    obj.location += KEYBOARD_SHIFT

monitor = bpy.data.objects["Monitor / angled side position"]
bezel = bpy.data.objects["Monitor bezel"]
post = bpy.data.objects["Monitor post"]
base = bpy.data.objects["Monitor base"]
post.location.y = bezel.location.y - (bezel.dimensions.y + post.dimensions.y) / 2 + .010
base.location.y -= .020
markers = [obj for obj in monitor.children if obj.name.startswith("Illustrative player marker")]
assert len(markers) == 2
dot = markers[0]
bpy.data.objects.remove(markers[1], do_unlink=True)
dot.name = "Map / player in central passage"
dot.scale = (1.20, .68, 1.20)
material = bpy.data.materials.new("Map / amber player light")
material.diffuse_color = (1, .37, .065, 1)
material.use_nodes = True
shader = material.node_tree.nodes["Principled BSDF"]
shader.inputs["Base Color"].default_value = (1, .37, .065, 1)
shader.inputs["Emission Color"].default_value = (1, .32, .036, 1)
shader.inputs["Emission Strength"].default_value = .5
dot.data.materials.clear()
dot.data.materials.append(material)

# The furniture has moved, but a small switch remains at the lower desk's
# measured lamp position. Its property powers the upper desk light.
def make_lower_switch():
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.047, depth=.011, location=(-.672, .758, .944))
    housing = bpy.context.object
    housing.name = "Lower desk / lamp switch housing"
    housing.scale.y = 1.13
    housing.data.materials.append(base.data.materials[0])
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=.015, depth=.006, location=(-.672, .758, .952))
    switch = bpy.context.object
    switch.name = "Lower desk / upper lamp switch"
    switch.data.materials.append(bpy.data.materials["Muted office teal"])
    switch["Upper lamp on"] = 1.0
    switch.id_properties_ui("Upper lamp on").update(
        min=0, max=1, description="Power the lamp above the lower desk")
    lamp = bpy.data.objects["Yellow desk light"].data
    driver = lamp.driver_add("energy").driver
    variable = driver.variables.new()
    variable.name = "power"
    target = variable.targets[0]
    target.id_type = "OBJECT"
    target.id = switch
    target.data_path = '["Upper lamp on"]'
    driver.expression = f"{lamp.energy} * power"


make_lower_switch()

for frame in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(frame)
    camera = scene.camera.location
    world_x = WORLD_MAP_ORIGIN.x - camera.x / METRES_PER_STUD
    world_z = WORLD_MAP_ORIGIN.z + camera.y / METRES_PER_STUD
    dot.location = (-.235 + (world_x - 964) / 148 * .47, .011, 1.18 - (world_z + 32) / 120 * .245)
    dot.keyframe_insert("location", frame=frame)

scene.frame_set(1)
update()
for side, report in arm_report.items():
    report["v21BendDegrees"] = bend(rig.pose.bones["forearm." + side], rig.pose.bones["hand." + side])

shutil.copyfile(BASE / "Keyboard_Clicks.wav", OUT / "Keyboard_Clicks.wav")
sound_strip = next(strip for strip in scene.sequence_editor.strips if strip.type == "SOUND")
sound_strip.sound.filepath = str(OUT / "Keyboard_Clicks.wav")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), compress=True)
bpy.ops.file.make_paths_relative()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), compress=True)

report = json.loads((BASE / "Contact_Check.json").read_text())
report.update(armPosture=arm_report, keyboardShiftMm=abs(KEYBOARD_SHIFT.y) * 1000)
(OUT / "Pose_Check.json").write_text(json.dumps(report, indent=2) + "\n")
print("POSE_V21", json.dumps(arm_report), flush=True)
