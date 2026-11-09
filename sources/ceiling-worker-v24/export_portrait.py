"""Bake the anatomical surface and its individual keystrokes for Studio."""
from collections import defaultdict
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector


source, output = map(Path, sys.argv[sys.argv.index("--") + 1:])
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
scene = bpy.context.scene
worker = bpy.data.objects["WORKER / 33 years / seated anatomy"]
upper = bpy.data.objects["UPPER_OFFICE / local inverted gravity"]
skin = bpy.data.objects["Worker / face neck forearms and hands"]
rig = bpy.data.objects["OfficeWorker anatomical rig"]
for obj in worker.children_recursive:
    if obj.type == "MESH":
        for modifier in obj.modifiers:
            if modifier.type in {"SUBSURF", "SOLIDIFY"}:
                modifier.show_viewport = False
        if 400 <= len(obj.data.vertices) <= 500 and not obj.hide_render:
            modifier = obj.modifiers.new("Studio accessory reduction", "DECIMATE")
            modifier.ratio = .24

SCALE = 2.64


def room_point(point):
    return Vector((point.x, point.z + .048, point.y + .55)) * SCALE


def room_normal(normal):
    return Vector((normal.x, normal.z, normal.y))


def evaluated(obj):
    result = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = result.to_mesh()
    mesh.calc_loop_triangles()
    local = upper.matrix_world.inverted() @ result.matrix_world
    return result, mesh, local


def quantize(vector, scale):
    return tuple(round(value * scale) for value in vector)


groups = defaultdict(lambda: {"points": [], "normals": [], "faces": [], "colors": []})
skin_indices = {}
scene.frame_set(1)
bpy.context.view_layer.update()
pivot = room_point(upper.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones["head"].head)
chair = bpy.data.objects["Chair / castors on upper carpet"]
seat = next(obj for obj in chair.children if obj.name.startswith("Seat cushion"))
chair_center = room_point(upper.matrix_world.inverted() @ seat.matrix_world.translation)


def append(obj, name, selected=None):
    evaluated_obj, mesh, transform = evaluated(obj)
    data = groups[name]
    index = {}
    complexion = mesh.color_attributes.get("Complexion")
    nails = mesh.attributes.get("nail_bed")
    for face in mesh.loop_triangles:
        if selected and not all(selected(i, mesh.vertices[i]) for i in face.vertices):
            continue
        for i in face.vertices:
            if i not in index:
                vertex = mesh.vertices[i]
                index[i] = len(data["points"])
                data["points"].append(room_point(transform @ vertex.co))
                normal = transform.to_3x3().inverted().transposed() @ vertex.normal
                data["normals"].append(room_normal(normal.normalized()))
                if complexion:
                    color = complexion.data[i].color_srgb[:3]
                    nail = nails.data[i].value if nails else 0
                    tone = tuple(value*(1-nail)+nail*shade for value,shade in zip(color,(.78,.62,.56)))
                    data["colors"].append(tuple(round(max(0,min(1,value))*31) for value in tone))
        a,b,c = face.vertices
        data["faces"].append((index[a],index[c],index[b]))
    evaluated_obj.to_mesh_clear()
    return index


head_region = lambda _, v: v.co.z > .975 and abs(v.co.x) < .14
face_indices = append(skin, "face", head_region)
skin_indices = append(skin, "hands", lambda i, v: not head_region(i, v))
for obj in worker.children_recursive:
    if obj.type != "MESH" or obj.hide_render or obj == skin:
        continue
    name = obj.name
    if name.startswith(("Iris", "Pupil")):
        group = "iris"
    elif name.startswith("Sclera"):
        group = "eyes"
    elif "hair cap" in name:
        group = "hair"
    elif "tie" in name:
        group = "tie"
    elif any(label in name.lower() for label in ("trouser", "shoe", "buckle")):
        group = "trousers"
    else:
        group = "shirt"
    append(obj, group)

blink_key = skin.data.shape_keys.key_blocks["Natural upper eyelid blink"]
blink_key.value = 1
bpy.context.view_layer.update()
evaluated_obj, mesh, transform = evaluated(skin)
blink = []
for vertex, i in face_indices.items():
    point = room_point(transform @ mesh.vertices[vertex].co)
    delta = quantize(point - groups["face"]["points"][i], 10000)
    if any(delta):
        blink.append((i, *delta))
evaluated_obj.to_mesh_clear()
blink_key.value = 0
assert blink, "No eyelid motion was baked"

details = json.loads(source.with_name("Pose_Check.json").read_text())
digit_names = ["Index", "Middle", "Ring", "Little"]
key_for = {row["finger"]: row["key"] for row in details["plannedContacts"]}
hits = []
deltas = {}
for frame, side, digit in details["strikes"]:
    finger = f"{digit_names[digit]}.{side}"
    key = key_for[finger]
    hits.append((frame, key))
    if key in deltas:
        continue
    scene.frame_set(frame)
    evaluated_obj, mesh, transform = evaluated(skin)
    rows = []
    for vertex, i in skin_indices.items():
        point = room_point(transform @ mesh.vertices[vertex].co)
        delta = quantize(point - groups["hands"]["points"][i], 10000)
        if any(delta):
            rows.append((i, *delta))
    deltas[key] = rows
    evaluated_obj.to_mesh_clear()

scene.frame_set(1)
keys = {}
for obj in upper.children:
    if obj.name.startswith("Keyboard key") or obj.name in {"Space bar", "Keyboard shell"}:
        keys[obj.name] = (room_point(obj.location), Vector((obj.dimensions.x, obj.dimensions.z, obj.dimensions.y)) * SCALE)


def pack(pattern, rows):
    return "".join(struct.pack(pattern, *row).hex() for row in rows)


def vec(value):
    return "Vector3.new(" + ",".join(f"{x:.6f}" for x in value) + ")"


lines = ["local portraitData = {", f"pivot={vec(pivot)},", f"seat={vec(chair_center)},",
         f'blink="{pack("<Hhhh",blink)}",', "meshes={"]
for name, group in groups.items():
    points = group["points"]
    centre = Vector([(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)])
    assert len(group["faces"]) < 20000 and len(points) < 60000
    lines.append(f'{name}={{center={vec(centre)},vertices="{pack("<hhh",(quantize(p-centre,10000) for p in points))}",')
    lines.append(f'normals="{pack("<bbb",(quantize(n,127) for n in group["normals"]))}",')
    if group["colors"]:
        lines.append(f'colors="{pack("<BBB",group["colors"])}",')
    lines.append(f'triangles="{pack("<HHH",group["faces"])}"}},')
lines.extend(["},", "keys={"])
for name, (position, size) in sorted(keys.items()):
    lines.append(f'["{name}"]={{position={vec(position)},size={vec(size)}}},')
lines.extend(["},", "deltas={"])
for name, rows in deltas.items():
    lines.append(f'["{name}"]="{pack("<Hhhh",rows)}",')
lines.extend(["},", "hits={"])
lines.extend(f'{{{frame},"{name}"}},' for frame, name in hits)
lines.append("}}")
output.write_text("\n".join(lines) + "\n")
print({name: (len(group["points"]), len(group["faces"])) for name, group in groups.items()}, flush=True)
print({name: len(rows) for name, rows in deltas.items()}, flush=True)
