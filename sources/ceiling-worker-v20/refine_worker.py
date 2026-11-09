"""Fit individual typing poses to keycaps in the worker's upright coordinates."""
from collections import defaultdict
from pathlib import Path
import heapq
import json
import math
import random
import struct
import sys
import wave

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_path import PATH

root = Path(__file__).resolve().parents[2]
project = root / 'outputs/CeilingWorker_2026-11-08'
source = project / 'Revision19/Ceiling_Office_Character_Study_v19.blend'
out = project / 'Revision20'
if (root / 'models').is_dir():
    source = root / 'models/ceiling-worker-v19/Ceiling_Office_Character_Study_v19.blend'
    out = root / 'models/ceiling-worker-v20'
out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.context.scene
rig = bpy.data.objects['OfficeWorker anatomical rig']
skin = bpy.data.objects['Worker / face neck forearms and hands']
upper = bpy.data.objects['UPPER_OFFICE / local inverted gravity']


def update():
    bpy.context.view_layer.update()


def skin_points():
    evaluated = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [v.co.copy() for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def press_envelope(frame, strike):
    return ease((frame - strike + 2) / 2) * (1 - ease((frame - strike - 1) / 3))


def viewer_vectors(frame):
    for first, last in zip(PATH, PATH[1:]):
        if frame <= last[0]:
            weight = ease((frame - first[0]) / (last[0] - first[0]))
            return tuple(Vector(first[i]).lerp(Vector(last[i]), weight) for i in (1, 2))
    return Vector(PATH[-1][1]), Vector(PATH[-1][2])


flags = [modifier.show_viewport for modifier in skin.modifiers]
for modifier in skin.modifiers:
    if modifier.type != 'ARMATURE':
        modifier.show_viewport = False
scene.frame_set(120)
update()
baseline = skin_points()
keycaps = [obj for obj in scene.objects if obj.name.startswith('Keyboard key') or obj.name == 'Space bar']
key_locations = {key: key.location.copy() for key in keycaps}
key_tops = {key: key.location.z + key.dimensions.z / 2 for key in keycaps}
neighbors = defaultdict(list)
for edge in skin.data.edges:
    a, b = edge.vertices
    neighbors[a].append(b)
    neighbors[b].append(a)

# Start from the four separate distal mesh components in v19. Their
# order across the hand is index, middle, ring and little finger.
fingers = {}
thumbs = {}
rolls = {}
for side, sign in [('L', 1), ('R', -1)]:
    hand = rig.pose.bones['hand.' + side]
    domain = {i for i, p in enumerate(baseline) if p.x * sign > .022 and p.y < -.555 and .73 < p.z < .95}
    remaining = {i for i in domain if baseline[i].y < -.615}
    clusters = []
    while remaining:
        stack = [remaining.pop()]
        cluster = []
        while stack:
            i = stack.pop()
            cluster.append(i)
            for j in neighbors[i]:
                if j in remaining:
                    remaining.remove(j)
                    stack.append(j)
        if len(cluster) > 30:
            clusters.append(cluster)
    clusters.sort(key=lambda group: sum(sign * baseline[i].x for i in group) / len(group))
    assert len(clusters) == 4, (side, [len(group) for group in clusters])

    labels = {}
    queue = []
    for digit, group in enumerate(clusters):
        for index in group:
            heapq.heappush(queue, (0, index, digit))
    while queue:
        distance, i, digit = heapq.heappop(queue)
        if i in labels:
            continue
        labels[i] = digit
        for j in neighbors[i]:
            if j in domain and j not in labels:
                heapq.heappush(queue, (distance + (baseline[i] - baseline[j]).length, j, digit))
    fingers[side] = [[i for i in domain if labels.get(i) == digit] for digit in range(4)]
    thumbs[side] = [i for i in domain if i not in labels and abs(baseline[i].x) < .084]
    rolls[side] = (Matrix.Rotation(math.radians(-6 * sign), 4, 'Z')
                   @ Matrix.Rotation(math.radians(-26 * sign), 4, 'Y'))

# Use the quiet frame as the seated rest pose. Save the wrist and elbow
# positions so the motion deforms the fingers instead of lifting the hands.
arm_poses = {}
for side, roll in rolls.items():
    hand = rig.pose.bones['hand.' + side]
    arm = rig.pose.bones['forearm.' + side]
    hand_pose = roll @ hand.matrix
    hand_pose.translation = hand.head
    # Rotate the forearm about its own centreline by a fraction of the roll.
    axis = (arm.tail - arm.head).normalized()
    turn = Matrix.Rotation(math.radians(10 if side == 'L' else -10), 4, axis)
    arm_pose = turn @ arm.matrix
    arm_pose.translation = arm.head
    arm_poses[side] = (arm_pose, hand_pose)
    arm.matrix = arm_pose
    update()
    hand.matrix = hand_pose
    update()
points = skin_points()


def in_cap(p, key, inset=.001):
    origin = key_locations[key]
    return (abs(p.x - origin.x) < key.dimensions.x / 2 - inset
            and abs(p.y - origin.y) < key.dimensions.y / 2 - inset)


def centre(indices):
    return sum((points[i] for i in indices), Vector()) / len(indices)


body_keys = skin.data.shape_keys.key_blocks
hover = skin.shape_key_add(name='Relaxed typing curl', from_mix=False)
presses = {}
measurements = []
nails = skin.data.attributes.new('nail_bed', 'FLOAT', 'POINT')
for side, masks in fingers.items():
    hand = rig.pose.bones['hand.' + side]
    inverse = (hand.matrix @ hand.bone.matrix_local.inverted()).to_3x3().inverted()
    for digit, ids in enumerate(masks):
        tip_ids = sorted(ids, key=lambda i: points[i].y)[:12]
        tip = centre(tip_ids)
        root_ids = [i for i in ids if -.611 < baseline[i].y < -.598]
        base = centre(root_ids)
        axis = (tip - base)
        axis.z = 0
        length = axis.length
        axis.normalize()
        hinge = Vector((0, 0, 1)).cross(axis)
        first = base + axis * .004
        second = base + axis * (length * .51)

        def curl(point, angle):
            reach = (point - base).dot(axis)
            mid = Matrix.Rotation(angle * ease((reach / length - .39) / .42) * .52, 3, hinge)
            low = Matrix.Rotation(angle * ease((reach / length - .01) / .38), 3, hinge)
            return first + low @ (second + mid @ (point - second) - first)

        distal = [i for i in ids if (points[i] - base).dot(axis) > length * .66]
        key = min(keycaps, key=lambda k: (tip.x - k.location.x)**2 + (tip.y - k.location.y + .008)**2)
        # Nudge only the last two phalanges laterally, for a real contact patch.
        def pose(i, angle):
            p = curl(points[i], angle)
            reach = (points[i] - base).dot(axis)
            p.x += (key.location.x - tip.x) * ease((reach / length - .31) / .66) * .76
            return p

        def solve(height):
            best = None
            for step in range(-9, 90):
                angle = step * .013
                patch = [p.z for i in distal if in_cap(p := pose(i, angle), key, 0)]
                if patch:
                    error = abs(min(patch) - height)
                    if best is None or error < best[0]:
                        best = (error, angle, min(patch))
            return best

        quiet = solve(key_tops[key] + .007)
        contact = solve(key_tops[key] - .0025)
        assert quiet is not None and contact is not None, (side, digit, list(tip), key.name)
        assert contact[0] < .005, (side, digit, contact, key.name)
        name = ['Index', 'Middle', 'Ring', 'Little'][digit] + '.' + side
        press = skin.shape_key_add(name=name + ' press', from_mix=False)
        press.relative_key = hover
        presses[side, digit] = (press, key)
        for i in ids:
            # All affected vertices are in the fully weighted hand region.
            hand_weight = sum(g.weight for g in skin.data.vertices[i].groups
                              if skin.vertex_groups[g.group].name == hand.name)
            if hand_weight < .96:
                continue
            coord = body_keys['Basis'].data[i].co
            hover.data[i].co = coord + inverse @ (pose(i, quiet[1]) - points[i])
            press.data[i].co = coord + inverse @ (pose(i, contact[1]) - points[i])
            reach = (points[i] - base).dot(axis)
            across = (points[i] - tip).dot(hinge)
            top = ease((points[i].z - tip.z + .001) / .008)
            patch = ease((reach - length * .70) / .010)
            patch *= 1 - ease((abs(across) - .005) / .004)
            nails.data[i].value = patch * top
        measurements.append(dict(finger=name, key=key.name, hover_mm=1000 * (quiet[2] - key_tops[key]),
                                 contact_mm=1000 * (contact[2] - key_tops[key] + .0025),
                                 press_angle_deg=math.degrees(contact[1])))
    for i in thumbs[side]:
        weight = ease((-.556 - points[i].y) / .035)
        hover.data[i].co = body_keys['Basis'].data[i].co + inverse @ Vector((0, .003, -.006)) * weight

# Relative key targets copy the relaxed shape everywhere outside their finger.
for (side, digit), (shape, key) in presses.items():
    owned = set(fingers[side][digit])
    for i in range(len(skin.data.vertices)):
        if i not in owned or shape.data[i].co == body_keys['Basis'].data[i].co:
            shape.data[i].co = hover.data[i].co
hover.value = 1

# Restrained colour and specular variation gives the fingertip a nail bed
# without adding separate pieces that could slide away from the skin.
for material in skin.data.materials:
    shader = material.node_tree.nodes.get('Principled BSDF')
    if not shader:
        continue
    nodes, links = material.node_tree.nodes, material.node_tree.links
    attr = nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'nail_bed'
    mix = nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MIX'
    color = shader.inputs['Base Color']
    if color.is_linked:
        links.new(color.links[0].from_socket, mix.inputs[1])
    else:
        mix.inputs[1].default_value = color.default_value
    mix.inputs[2].default_value = (.55, .32, .25, 1)
    links.new(attr.outputs['Fac'], mix.inputs[0])
    links.new(mix.outputs[0], color)

# Bring the cuff opening onto the forearm, preserving the attachment to the
# sleeve. The photographed gap was at the free edge of each rolled cuff.
for cuff in (o for o in scene.objects if o.name.startswith('Worker / sewn sleeve cuff')):
    c = sum((v.co for v in cuff.data.vertices), Vector()) / len(cuff.data.vertices)
    side = 'L' if c.x > 0 else 'R'
    arm = rig.pose.bones['forearm.' + side]
    axis = (arm.tail - arm.head).normalized()
    along = [(v.co - arm.head).dot(axis) for v in cuff.data.vertices]
    lower, upper_edge = min(along), max(along)
    for vertex, distance in zip(cuff.data.vertices, along):
        centreline = arm.head + axis * distance
        fit = ease((distance - lower) / (upper_edge - lower))
        vertex.co = centreline + (vertex.co - centreline) * (1 - .18 * fit)
    cuff.data.update()

# One timeline drives fingertip flexion, key travel and click transients.
# The last key is released before the existing head lift starts at frame 49.
hits = [(4,'L',1), (8,'R',0), (12,'L',0), (16,'R',1), (21,'L',2), (24,'R',0),
        (29,'L',1), (34,'R',2), (38,'L',0), (43,'R',1),
        (212,'L',0), (217,'R',1), (221,'L',1), (225,'R',0), (229,'L',2), (235,'R',1)]
press_key_data = {}
for pair, (shape, key) in presses.items():
    press_key_data.setdefault(key, []).extend(f for f, side, finger in hits if (side, finger) == pair)

scene.frame_set(1)
update()
head_bone = rig.pose.bones['head']
head_attachment = bpy.data.objects['Head attachment and gaze pivot']
rest_head = head_bone.matrix.copy()
rest_attachment = head_attachment.matrix_basis.copy()
pivot = rest_head.translation.copy()
parent_inverse = head_attachment.parent.matrix_world.inverted()
eye_centre = Vector((0, -.12182286, 1.57370663))
local_forward = Vector((0, -1, 0))
rest_forward = (rest_attachment.to_3x3() @ local_forward).normalized()

for frame in range(1, 241):
    scene.frame_set(frame)
    for side, (arm_pose, hand_pose) in arm_poses.items():
        for name, pose in [('forearm', arm_pose), ('hand', hand_pose)]:
            bone = rig.pose.bones[name + '.' + side]
            bone.matrix = pose
            update()
            for prop in ['location', 'rotation_quaternion', 'scale']:
                bone.keyframe_insert(prop, frame=frame)
    for (side, digit), (shape, key) in presses.items():
        shape.value = max((press_envelope(frame, at) for at, s, d in hits if (s,d) == (side,digit)), default=0)
        shape.keyframe_insert('value', frame=frame)
    for key, frames in press_key_data.items():
        travel = max((press_envelope(frame, at) for at in frames), default=0)
        key.location.z = key_locations[key].z - travel * .0025
        key.keyframe_insert('location', index=2, frame=frame)
    track = ease((frame - 48) / 34) * (1 - ease((frame - 175) / 35))
    glance = ease((frame - 49) / 23) * (1 - ease((frame - 178) / 30))
    listener, _ = viewer_vectors(min(frame, 178))
    target = parent_inverse @ listener
    desired = (target - rest_attachment @ eye_centre).normalized()
    offset = rest_forward.rotation_difference(desired)
    max_turn = math.radians(30)
    turn = min(1, max_turn / max(.001, offset.angle)) * track
    rotation = Matrix.Identity(3).to_quaternion().slerp(offset, turn)
    transform = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
    head_bone.matrix = transform @ rest_head
    head_bone.keyframe_insert('rotation_quaternion', frame=frame)
    head_bone.keyframe_insert('location', frame=frame)
    head_attachment.matrix_basis = transform @ rest_attachment
    head_attachment.keyframe_insert('rotation_euler', frame=frame)
    head_attachment.keyframe_insert('location', frame=frame)
    local_target = (transform @ rest_attachment).inverted() @ target
    for side in ('L', 'R'):
        centre = bpy.data.objects['Sclera.' + side].location
        direction = (local_target - centre).normalized()
        turn_eye = local_forward.rotation_difference(direction)
        eye_limit = min(1, math.radians(13) / max(.001, turn_eye.angle))
        eye_rotation = Matrix.Identity(3).to_quaternion().slerp(turn_eye, glance * eye_limit)
        for name, radius in [('Iris', .011), ('Pupil', .0124)]:
            obj = bpy.data.objects[name + '.' + side]
            obj.location = centre + (eye_rotation @ local_forward) * radius
            obj.rotation_euler = eye_rotation.to_euler()
            obj.keyframe_insert('location', frame=frame)
            obj.keyframe_insert('rotation_euler', frame=frame)

for marker in list(scene.timeline_markers):
    scene.timeline_markers.remove(marker)
for frame, label in [(1, 'Typing'), (13, 'Player starts watching'), (49, '1.5 s observed / head lift'),
                     (83, 'Tracks gaze'), (169, 'Player turns away'), (212, 'First resumed key')]:
    scene.timeline_markers.new(label, frame=frame)

camera = scene.camera
camera.name = 'Player eyes / review route'
for frame, position, target, lens in PATH:
    camera.location = position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = lens
    camera.keyframe_insert('location', frame=frame)
    camera.keyframe_insert('rotation_euler', frame=frame)
    camera.data.keyframe_insert('lens', frame=frame)

random_source = random.Random(37)
rate = 24000
audio = [0.0] * (20 * rate)
keyboard_source = upper.matrix_world @ Vector((0, -.615, .80))
for strike, side, digit in hits:
    ear, look_at = viewer_vectors(strike)
    right = (look_at - ear).cross(Vector((0, 0, 1))).normalized()
    to_source = keyboard_source - ear
    pan = .7 * to_source.normalized().dot(right)
    level = .90 / (1 + .28 * to_source.length)
    left, right_gain = level * math.sqrt((1 - pan) * .5), level * math.sqrt((1 + pan) * .5)
    for frame_offset, volume, frequency in [(0, .21, 1850), (3, .077, 1280)]:
        start = round((strike + frame_offset - 1) * rate / 24)
        for i in range(int(.044 * rate)):
            t = i / rate
            transient = .68 * math.sin(math.tau * (frequency + 83 * digit) * t) + .32 * random_source.uniform(-1, 1)
            impulse = volume * math.exp(-t * 123) * transient
            audio[2 * (start + i)] += left * impulse
            audio[2 * (start + i) + 1] += right_gain * impulse
audio_file = out / 'Keyboard_Clicks.wav'
with wave.open(str(audio_file), 'wb') as sound:
    sound.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
    sound.writeframes(struct.pack('<' + 'h' * len(audio), *(int(x * 32767) for x in audio)))
scene.sequence_editor_create().strips.new_sound('Upper keyboard contacts', str(audio_file), channel=1, frame_start=1)

for modifier, flag in zip(skin.modifiers, flags):
    modifier.show_viewport = flag
scene.frame_set(1)
target = out / 'Ceiling_Office_Character_Study_v20.blend'
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=True)
bpy.ops.file.make_paths_relative()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=True)
(out / 'Contact_Check.json').write_text(json.dumps({'plannedContacts': measurements, 'strikes': hits}, indent=2))
print('V20_SAVED', json.dumps(measurements), flush=True)
