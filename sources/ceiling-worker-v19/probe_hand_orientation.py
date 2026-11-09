"""Read the v18 hand landmarks in the worker's coordinates."""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[2]
source = root / 'outputs/CeilingWorker_2026-11-08/Revision18/Ceiling_Office_Character_Study_v18.blend'
if (root / 'models').is_dir():
    source = root / 'models/ceiling-worker-v18/Ceiling_Office_Character_Study_v18.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.context.scene
scene.frame_set(120)
rig = bpy.data.objects['OfficeWorker anatomical rig']
skin = bpy.data.objects['Worker / face neck forearms and hands']
for modifier in skin.modifiers:
    if modifier.type != 'ARMATURE':
        modifier.show_viewport = False
bpy.context.view_layer.update()
evaluated = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
for side, sign in [('L', 1), ('R', -1)]:
    hand = rig.pose.bones['hand.' + side]
    vertices = [v for v in skin.data.vertices if v.co.x * sign > .31 and .71 < v.co.z < .91]
    thumb = min(vertices, key=lambda v: v.co.y)
    fingers = [v for v in vertices if v.co.z < .775]
    for name, v in [('thumb candidate', thumb), ('long finger tip', min(fingers, key=lambda v: v.co.z))]:
        p = mesh.vertices[v.index].co
        print(side, name, v.index, 'rest', tuple(v.co), 'posed', tuple(p),
              'inward metres', (hand.head.x - p.x) * sign, flush=True)
evaluated.to_mesh_clear()
