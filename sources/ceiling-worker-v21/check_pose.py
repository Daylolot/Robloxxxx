"""Measure joints, desk clearance, typing contacts and monitor tracking."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/CeilingWorker_2026-11-08/Revision21"
if (ROOT / "models").is_dir():
    OUT = ROOT / "models/ceiling-worker-v21"
bpy.ops.wm.open_mainfile(filepath=str(OUT / "Ceiling_Office_Character_Study_v21.blend"))
scene = bpy.context.scene
rig = bpy.data.objects["OfficeWorker anatomical rig"]
skin = bpy.data.objects["Worker / face neck forearms and hands"]
desk = bpy.data.objects["Ceiling desk / walnut top"]
dot = bpy.data.objects["Map / player in central passage"]
report_path = OUT / "Pose_Check.json"
report = json.loads(report_path.read_text())
digit_names = ("Index", "Middle", "Ring", "Little")
keys = {row["finger"]: bpy.data.objects[row["key"]] for row in report["plannedContacts"]}
scene.frame_set(120)
key_rest = {obj: obj.location.z for obj in keys.values()}
desk_top = desk.location.z + desk.dimensions.z / 2
strike_rows = []
desk_clearance = float("inf")
joint_gap = 0
bend = 0
map_delta = 0
first_dot = None
strikes = {frame: f"{digit_names[digit]}.{side}" for frame, side, digit in report["strikes"]}
samples = set(strikes) | {1, 48, 120, 210, 240}

for frame in range(1, 241):
    scene.frame_set(frame)
    for side in ("L", "R"):
        upper, fore, hand = (rig.pose.bones[f"{part}.{side}"] for part in ("upper_arm", "forearm", "hand"))
        joint_gap = max(joint_gap, (upper.tail - fore.head).length, (fore.tail - hand.head).length)
        bend = max(bend, math.degrees((fore.tail - fore.head).angle(hand.tail - hand.head)))
        saved = report["armPosture"][side]
        assert abs(upper.length * 1000 - saved["upperLengthMm"]) < .1
        assert abs(fore.length * 1000 - saved["forearmLengthMm"]) < .1
    if 48 <= frame < 210:
        assert all(abs(key.location.z - z) < .00001 for key, z in key_rest.items()), frame
    player = scene.camera.location
    decoded = Vector((1020 - (964 + (dot.location.x + .235) / .47 * 148),
                      -32 + (1.18 - dot.location.z) / .245 * 120 - 44.35)) * .28
    assert (decoded - player.xy).length < .001, frame
    if first_dot is None:
        first_dot = dot.location.copy()
    map_delta = max(map_delta, (first_dot - dot.location).length)
    if frame not in samples:
        continue
    evaluated = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    hand_area = [v.co for v in mesh.vertices if abs(v.co.x) < .40 and -.93 < v.co.y < -.36]
    desk_clearance = min(desk_clearance, min(p.z - desk_top for p in hand_area))
    if frame in strikes:
        name = strikes[frame]
        key = keys[name]
        assert abs(key_rest[key] - key.location.z - .0025) < .0001
        position, size = key.location, key.dimensions
        patch = [p.z - (position.z + size.z / 2) for p in hand_area
                 if abs(p.x - position.x) < size.x / 2 and abs(p.y - position.y) < size.y / 2]
        distance = min(patch, default=1)
        assert -.001 <= distance <= .001, (name, frame, distance)
        strike_rows.append({"frame": frame, "finger": name, "clearanceMm": distance * 1000})
    evaluated.to_mesh_clear()

assert joint_gap < .001, joint_gap
assert bend < 5, bend
assert desk_clearance > .01, desk_clearance
assert len(strike_rows) == len(strikes)
assert map_delta > .006, map_delta
lamp = bpy.data.objects["Yellow desk light"]
switch = bpy.data.objects["Lower desk / upper lamp switch"]
levels = []
for power in (1.0, 0.0, 1.0):
    switch["Upper lamp on"] = power
    switch.update_tag()
    bpy.context.view_layer.update()
    levels.append(lamp.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.energy)
assert levels[0] > 0 and levels[1] == 0 and levels[2] == levels[0], levels
report.update(
    evaluatedContacts=strike_rows,
    checkedFrames=240,
    worstWristBendDegrees=bend,
    maximumJointGapMm=joint_gap * 1000,
    minimumDeskClearanceMm=desk_clearance * 1000,
    deskClearanceSampleCount=len(samples),
    maxMapMarkerTravelMm=map_delta * 1000,
    lampPowerTestWatts=levels,
)
report_path.write_text(json.dumps(report, indent=2) + "\n")
print("POSE_CHECKED", bend, joint_gap * 1000, desk_clearance * 1000, map_delta * 1000, flush=True)
