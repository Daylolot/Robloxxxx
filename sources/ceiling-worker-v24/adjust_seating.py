"""Move the seated worker closer, solve the limbs and keep typing contacts."""

import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector


source, target = map(Path, sys.argv[sys.argv.index("--") + 1:])
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
scene = bpy.context.scene
rig = bpy.data.objects["OfficeWorker anatomical rig"]
worker = rig.parent
body_shift = Vector((0, -.115, .080))
keyboard_shift = Vector((0, .025, 0))
scene.frame_set(120)
bpy.context.view_layer.update()


def aim(bone, head, tail, rotation=None):
    original = bone.matrix
    rotation = rotation or original.to_quaternion()
    direction = tail - head
    rotation = (rotation @ Vector((0, 1, 0))).rotation_difference(direction) @ rotation
    result = rotation.to_matrix().to_4x4()
    result.col[0] *= original.col[0].length
    result.col[1] *= direction.length / bone.bone.length
    result.col[2] *= original.col[2].length
    result.translation = head
    return result


def joint(start, end, upper, lower, preferred):
    axis = end - start
    span = axis.length
    assert abs(upper - lower) < span < upper + lower
    axis.normalize()
    distance = (upper**2 - lower**2 + span**2) / (2 * span)
    offset = preferred - start
    offset -= axis * offset.dot(axis)
    return start + axis * distance + offset.normalized() * math.sqrt(upper**2 - distance**2)


def translated(matrix, offset):
    result = matrix.copy()
    result.translation += offset
    return result


poses, forearm_changes, measurements = {}, {}, {}
for side in ("L", "R"):
    upper, fore, hand = (rig.pose.bones[f"{name}.{side}"] for name in ("upper_arm", "forearm", "hand"))
    wrist = hand.head + keyboard_shift - body_shift
    axis = (hand.tail - hand.head).normalized()
    elbow = joint(upper.head, wrist, upper.length, fore.length, wrist - axis * fore.length)
    poses[upper.name] = aim(upper, upper.head, elbow)
    palm_rotation = (hand.matrix @ hand.bone.matrix_local.inverted()).to_quaternion()
    poses[fore.name] = aim(fore, elbow, wrist, palm_rotation @ fore.bone.matrix_local.to_quaternion())
    poses[hand.name] = translated(hand.matrix, keyboard_shift - body_shift)
    forearm_changes[side] = poses[fore.name] @ fore.matrix.inverted()
    measurements[side] = {
        "oldElbowAngle": math.degrees((upper.head-fore.head).angle(hand.head-fore.head)),
        "elbowAngle": math.degrees((upper.head-elbow).angle(wrist-elbow)),
        "wristAngle": math.degrees((wrist-elbow).angle(axis)),
    }
    thigh, shin, foot = (rig.pose.bones[f"{name}.{side}"] for name in ("thigh", "shin", "foot"))
    ankle = foot.head - body_shift
    knee = joint(thigh.head, ankle, thigh.length, shin.length, shin.head)
    poses[thigh.name] = aim(thigh, thigh.head, knee)
    poses[shin.name] = aim(shin, knee, ankle)
    poses[foot.name] = translated(foot.matrix, -body_shift)

for frame in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(frame)
    for name, matrix in poses.items():
        bone = rig.pose.bones[name]
        bone.matrix = matrix
        bpy.context.view_layer.update()
        for property_name in ("location", "rotation_quaternion", "scale"):
            bone.keyframe_insert(property_name, frame=frame)

scene.frame_set(120)
bpy.context.view_layer.update()
skin = bpy.data.objects["Worker / face neck forearms and hands"]
for side in ("L", "R"):
    hand = rig.pose.bones[f"hand.{side}"]
    rest = hand.bone.matrix_local
    correction = rest @ hand.matrix.inverted() @ poses[hand.name] @ rest.inverted()
    index = skin.vertex_groups[hand.name].index
    for vertex in skin.data.vertices:
        weight = next((group.weight for group in vertex.groups if group.group == index), 0)
        influence = min(1, max(0, (weight - .65) / .30))
        if influence:
            influence *= influence * (3 - 2 * influence)
            for shape in skin.data.shape_keys.key_blocks:
                point = shape.data[vertex.index]
                point.co = point.co.lerp(correction @ point.co, influence)

for obj in worker.children:
    if obj.name.startswith("Worker / sewn sleeve cuff"):
        side = "L" if sum(v.co.x for v in obj.data.vertices) > 0 else "R"
        obj.data.transform(forearm_changes[side])
    elif obj.name.startswith(("Leather office shoe", "Shoe sole", "Shoe lace")):
        obj.location -= body_shift
worker.location += body_shift
for obj in worker.parent.children:
    if obj.name.startswith("Keyboard key") or obj.name in {"Space bar", "Keyboard shell"}:
        obj.location += keyboard_shift

chair = bpy.data.objects["Chair / castors on upper carpet"]
chair.location.y += body_shift.y
for obj in chair.children:
    if obj.name.startswith(("Armrest", "Seat cushion", "Ergonomic upholstered back")):
        obj.location.z += body_shift.z
    elif obj.name.startswith("Chair lift"):
        obj.location.z += body_shift.z / 2
        obj.dimensions.z += body_shift.z

# Correct the remaining skin fold across the wrist without shifting the keys or digits.
bpy.context.view_layer.update()
surface_modifiers = [modifier for modifier in skin.modifiers
                     if modifier.type != "ARMATURE" and modifier.show_viewport]
for modifier in surface_modifiers:
    modifier.show_viewport = False
bpy.context.view_layer.update()
posed_skin = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
points = [vertex.co.copy() for vertex in posed_skin.data.vertices]
room_from_skin = worker.parent.matrix_world.inverted() @ posed_skin.matrix_world
skin_from_room = room_from_skin.to_3x3().inverted()
assert len(points) == len(skin.data.vertices)
bone_maps = {}
for group in skin.vertex_groups:
    bone = rig.pose.bones.get(group.name)
    if bone and bone.bone.use_deform:
        bone_maps[group.index] = (bone.matrix @ bone.bone.matrix_local.inverted()).to_3x3()


def soft_peak(position, center, radius):
    return max(0, 1 - ((position - center) / radius)**2)**2


adjusted = 0
for vertex, point in zip(skin.data.vertices, points):
    x, y, z = room_from_skin @ point
    if not (.08 < abs(x) < .28 and -.555 < y < -.397 and .75 < z < .91):
        continue
    underside = min(1, max(0, (.834 - z) / .032))
    top = min(1, max(0, (z - .834) / .025))
    lift = .008 * soft_peak(-y, .443, .046)
    fill = .008 * soft_peak(-y, .503, .051)
    ridge = .006 * soft_peak(-y, .482, .046)
    offset = underside * (lift - fill) - top * ridge
    if abs(offset) < .00005:
        continue
    transform = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    weight = 0
    for group in vertex.groups:
        if group.group in bone_maps:
            transform += bone_maps[group.group] * group.weight
            weight += group.weight
    if weight:
        correction = (transform * (1 / weight)).inverted() @ skin_from_room @ Vector((0, 0, offset))
        for shape in skin.data.shape_keys.key_blocks:
            shape.data[vertex.index].co += correction
        adjusted += 1
for modifier in surface_modifiers:
    modifier.show_viewport = True
assert adjusted > 0

scene.frame_set(1)
bpy.context.view_layer.update()
target.parent.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(target.resolve()), compress=True)
report = json.loads(source.with_name("Pose_Check.json").read_text())
# Preserve the contact plan and keyframe schedule. Measurements are from this pose.
for name in ("evaluatedContacts", "armPosture", "worstWristBendDegrees", "minimumDeskClearanceMm",
             "deskClearanceSampleCount", "checkedFrames", "maximumJointGapMm"):
    report.pop(name, None)
report["seating"] = {
    "liftMetres": body_shift.z, "forwardMetres": -body_shift.y,
    "arms": measurements, "smoothedWristVertices": adjusted,
}
target.with_name("Pose_Check.json").write_text(json.dumps(report, indent=2) + "\n")
print(report["seating"], flush=True)
