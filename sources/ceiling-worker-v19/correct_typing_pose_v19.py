"""Refine the saved v18 arm rig without replacing its mesh, face or shape keys."""
from pathlib import Path
import hashlib
import json
import math
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'outputs/CeilingWorker_2026-11-08'
MODELS = ROOT / 'models'
SOURCE = PROJECT / 'Revision18/Ceiling_Office_Character_Study_v18.blend'
OUT = PROJECT / 'Revision19'
if MODELS.is_dir():
    SOURCE = MODELS / 'ceiling-worker-v18/Ceiling_Office_Character_Study_v18.blend'
    OUT = MODELS / 'ceiling-worker-v19'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
rig = bpy.data.objects['OfficeWorker anatomical rig']
skin = bpy.data.objects['Worker / face neck forearms and hands']
scene.frame_set(120)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
landmarks = {}
binds = {}
for side, sign in [('L', 1), ('R', -1)]:
    hand = rig.pose.bones['hand.' + side]
    arm = rig.pose.bones['forearm.' + side]
    vertices = [v for v in skin.data.vertices if v.co.x * sign > .31 and .70 < v.co.z < .91]
    thumb = min(vertices, key=lambda v: v.co.y)
    fingertip = min(vertices, key=lambda v: v.co.z)
    landmarks[side] = (thumb.index, fingertip.index, sign)
    old_arm = arm.matrix.copy()
    new_hand = hand.matrix @ Matrix.Rotation(math.pi, 4, 'Y')
    wrist = hand.head + Vector((-sign * .019, .025, .003))
    new_hand.translation = wrist
    elbow = arm.head.copy()
    old_axis = (arm.tail - elbow).normalized()
    axis = (wrist - elbow).normalized()
    swing = old_axis.rotation_difference(axis)
    new_arm = swing.to_matrix().to_4x4() @ old_arm
    new_arm.translation = elbow
    # Share the needed radial-side rotation across the forearm and wrist.
    radial = thumb.co - hand.bone.head_local
    old_radial = (new_arm @ arm.bone.matrix_local.inverted()).to_3x3() @ radial
    desired_radial = (new_hand @ hand.bone.matrix_local.inverted()).to_3x3() @ radial
    old_radial = (old_radial - axis * old_radial.dot(axis)).normalized()
    desired_radial = (desired_radial - axis * desired_radial.dot(axis)).normalized()
    angle = math.atan2(axis.dot(old_radial.cross(desired_radial)), old_radial.dot(desired_radial))
    new_arm = Matrix.Rotation(angle * .50, 4, axis) @ new_arm
    new_arm.translation = elbow
    new_arm.col[1] = (*((wrist - elbow) / arm.bone.length), 0)
    binds[side] = (old_arm, new_arm, new_hand)

keys = [o for o in scene.objects if o.name.startswith('Keyboard key') or o.name == 'Space bar']
for ob in keys + [bpy.data.objects['Keyboard shell']]:
    ob.location.y -= .040
key_bounds = [(o.location.x - o.dimensions.x / 2, o.location.x + o.dimensions.x / 2,
               o.location.y - o.dimensions.y / 2, o.location.y + o.dimensions.y / 2,
               o.location.z + o.dimensions.z / 2) for o in keys]

def apply_pose(height, movement):
    for side, (_, arm, _) in binds.items():
        offset = binds[side][2].translation + Vector((0, 0, height + movement[side])) - arm.translation
        swing = arm.col[1].to_3d().rotation_difference(offset)
        frame = swing.to_matrix().to_4x4() @ arm
        frame.translation = arm.translation
        frame.col[1] = (*(offset / rig.data.bones['forearm.' + side].length), 0)
        rig.pose.bones['forearm.' + side].matrix = frame
    bpy.context.view_layer.update()
    for side, (_, _, hand) in binds.items():
        frame = hand.copy()
        frame.translation = rig.pose.bones['forearm.' + side].tail
        rig.pose.bones['hand.' + side].matrix = frame
    bpy.context.view_layer.update()

def evaluated_points():
    obj = skin.evaluated_get(dg)
    mesh = obj.to_mesh()
    points = [v.co.copy() for v in mesh.vertices if -.735 < v.co.y < -.495 and .68 < v.co.z < .98]
    obj.to_mesh_clear()
    return points

def clearance(points):
    return min((p.z - top for p in points for x0, x1, y0, y1, top in key_bounds
                if x0 <= p.x <= x1 and y0 <= p.y <= y1), default=1)

still = {'L': 0, 'R': 0}
apply_pose(0, still)
initial = clearance(evaluated_points())
height = .0015 - initial
assert abs(height) < .05, initial
apply_pose(height, still)
for ob in [o for o in scene.objects if o.name.startswith('Worker / sewn sleeve cuff')]:
    center = sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
    side = 'L' if center.x > 0 else 'R'
    delta = rig.pose.bones['forearm.' + side].matrix @ binds[side][0].inverted()
    for v in ob.data.vertices:
        v.co = delta @ v.co
    ob.data.update()

def ease(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)

for frame in range(1, 241):
    scene.frame_set(frame)
    seconds = (frame - 1) / 24
    activity = 1 - ease((seconds - 2) / 1.4) * (1 - ease((seconds - 7) / 2))
    lift = {side: .0035 * (.5 + .5 * math.sin(seconds * 13 + phase)) * activity
            for side, phase in [('L', 0), ('R', math.pi)]}
    apply_pose(height, lift)
    for side in binds:
        for kind in ['forearm', 'hand']:
            bone = rig.pose.bones[kind + '.' + side]
            for prop in ['location', 'rotation_quaternion', 'scale']:
                bone.keyframe_insert(prop, frame=frame)

checks = []
for frame in range(1, 241, 4):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    distance = clearance(evaluated_points())
    assert -.0005 <= distance < .020, (frame, distance)
    checks.append({'frame': frame, 'closestSkinAboveKeyMetres': distance})

flags = [modifier.show_viewport for modifier in skin.modifiers]
for modifier in skin.modifiers:
    if modifier.type != 'ARMATURE':
        modifier.show_viewport = False
joint_checks = []
for frame in range(1, 241):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    obj = skin.evaluated_get(dg)
    mesh = obj.to_mesh()
    for side, (thumb, tip, sign) in landmarks.items():
        hand = rig.pose.bones['hand.' + side]
        forearm = rig.pose.bones['forearm.' + side]
        upper = rig.pose.bones['upper_arm.' + side]
        p = mesh.vertices[thumb].co
        q = mesh.vertices[tip].co
        inward = (hand.head.x - p.x) * sign
        finger_reach = hand.head.y - q.y
        wrist_gap = (forearm.tail - hand.head).length
        elbow_gap = (upper.tail - forearm.head).length
        angle = math.degrees((forearm.tail - forearm.head).angle(hand.tail - hand.head))
        assert inward > .035 and finger_reach > .12 and wrist_gap < .001 and elbow_gap < .02 and angle < 35, (frame, side, inward, finger_reach, wrist_gap, elbow_gap, angle)
        joint_checks.append({'frame': frame, 'side': side, 'thumbInwardMetres': inward,
                             'fingerReachMetres': finger_reach, 'wristGapMetres': wrist_gap,
                             'elbowGapMetres': elbow_gap, 'wristBendDegrees': angle})
    obj.to_mesh_clear()
for modifier, flag in zip(skin.modifiers, flags):
    modifier.show_viewport = flag

scene.frame_set(120)
upper_drawer = bpy.data.objects.get('Linked drawer / sliding front')
if upper_drawer:
    upper_drawer.name = 'Upper drawer / decorative front'
target = OUT / 'Ceiling_Office_Character_Study_v19.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=True)
report = {
    'stage': 'Blender pose revision',
    'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'blendSha256': hashlib.sha256(target.read_bytes()).hexdigest(),
    'jointChecks': joint_checks,
    'keyClearanceChecks': checks,
    'heightCorrectionMetres': height,
    'limitation': 'Samples test geometry and landmarks; visual review is separate. The animation uses small hand lifts, not individual keypresses.'
}
(OUT / 'Pose_Check.json').write_text(json.dumps(report, indent=2))
print('POSE_SAVED', height, min(c['closestSkinAboveKeyMetres'] for c in checks), flush=True)
