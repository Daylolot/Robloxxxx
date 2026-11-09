"""Check the saved animation at the points where fingers should touch the keys."""
from pathlib import Path
import json
import math
import wave

import bpy

root = Path(__file__).resolve().parents[2]
out = root / 'outputs/CeilingWorker_2026-11-08/Revision20'
if (root / 'models').is_dir():
    out = root / 'models/ceiling-worker-v20'
bpy.ops.wm.open_mainfile(filepath=str(out / 'Ceiling_Office_Character_Study_v20.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['OfficeWorker anatomical rig']
skin = bpy.data.objects['Worker / face neck forearms and hands']
report = json.loads((out / 'Contact_Check.json').read_text())
timeline = {(frame, side, digit) for frame, side, digit in report['strikes']}
key_for = {row['finger']: bpy.data.objects[row['key']] for row in report['plannedContacts']}
names = ['Index', 'Middle', 'Ring', 'Little']
scene.frame_set(120)
key_rest = {key: key.location.z for key in key_for.values()}
rest_head = rig.pose.bones['head'].matrix.to_quaternion()
scene.frame_set(48)
head_before = rig.pose.bones['head'].matrix.to_quaternion()
scene.frame_set(49)
eye = bpy.data.objects['Iris.L']
eye_at_dwell = eye.location.copy()
assert (eye_at_dwell - bpy.data.objects['Sclera.L'].location).angle((0, -1, 0)) < .001
scene.frame_set(80)
head_after = rig.pose.bones['head'].matrix.to_quaternion()
assert (eye.location - eye_at_dwell).length > .0004
rows = []
worst_bend = 0
for frame in range(1, 241):
    scene.frame_set(frame)
    for side in ('L', 'R'):
        arm = rig.pose.bones['forearm.' + side]
        hand = rig.pose.bones['hand.' + side]
        assert (arm.tail - hand.head).length < .001
        worst_bend = max(worst_bend, math.degrees((arm.tail - arm.head).angle(hand.tail - hand.head)))
    if 48 <= frame < 210:
        assert all(abs(key.location.z - z) < 1e-5 for key, z in key_rest.items()), frame
    at_frame = [(side, digit) for f, side, digit in timeline if f == frame]
    if not at_frame:
        continue
    bpy.context.view_layer.update()
    evaluated = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    for side, digit in at_frame:
        name = names[digit] + '.' + side
        key = key_for[name]
        assert abs((key_rest[key] - key.location.z) - .0025) < .0001, (name, frame)
        p = key.location
        size = key.dimensions
        patch = [v.co.z - (p.z + size.z / 2) for v in mesh.vertices
                 if abs(v.co.x - p.x) < size.x / 2 and abs(v.co.y - p.y) < size.y / 2
                 and .75 < v.co.z < .87]
        distance = min(patch, default=1)
        assert -.001 <= distance <= .001, (name, frame, distance)
        rows.append({'frame': frame, 'finger': name, 'evaluatedClearance_mm': distance * 1000})
    evaluated.to_mesh_clear()
assert len(rows) == len(timeline)
assert head_before.rotation_difference(head_after).angle > .1
assert rest_head.rotation_difference(head_before).angle > .1

with wave.open(str(out / 'Keyboard_Clicks.wav'), 'rb') as sound:
    rate = sound.getframerate()
    sound.setpos(round(2 * rate))
    quiet = sound.readframes(round(6.7 * rate))
    assert not any(quiet)
assert any(strip.type == 'SOUND' for strip in scene.sequence_editor.strips)
report['evaluatedContacts'] = rows
report['checkedFrames'] = 240
report['worstWristBendDegrees'] = worst_bend
report['silentFromSecond'] = 2
report['silentThroughSecond'] = 8.7
(out / 'Contact_Check.json').write_text(json.dumps(report, indent=2) + '\n')
print('SAVED_CHECK', json.dumps(rows), flush=True)
