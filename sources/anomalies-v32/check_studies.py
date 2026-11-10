"""Check scene changes after reopening the two Blender files."""
from pathlib import Path
import json
import sys

import bpy

name,dest=sys.argv[sys.argv.index("--")+1:]
scene=bpy.context.scene
if name=="Vent":
    mat=next(x for x in bpy.data.materials if x.name.startswith("Vapor density "))
    knob=mat.node_tree.nodes["Pressure pulse"].inputs[1]
    scene.frame_set(47)
    high=knob.default_value
    scene.frame_set(110)
    low=knob.default_value
    assert high>1.1 and low<.5
    layers=sum(x.name.startswith("Small liquid impact ") for x in bpy.data.objects)
    assert layers==3
    data={"pulseMultiplier":high,"restMultiplier":low,"impactSurfaces":layers}
else:
    pin=bpy.data.objects["Old calendar pin"]
    calendar=next(iter(bpy.data.collections["Calendar"].objects))
    scene.frame_set(41)
    before=calendar.location.copy()
    assert pin.hide_render
    scene.frame_set(61)
    movement=calendar.location-before
    assert not pin.hide_render and abs(movement.x-2.45)<.0001 and abs(movement.z+.51)<.0001
    data={"offsetX":movement.x,"offsetHeight":movement.z,"pinVisibleWhenDisplaced":not pin.hide_render}
Path(dest).write_text(json.dumps(data,indent=2)+"\n")
