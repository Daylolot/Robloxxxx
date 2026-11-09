"""Check saved scenes and the endpoints of their authored animations."""
import math
import json
from pathlib import Path
import sys

import bpy

name, dest = sys.argv[sys.argv.index("--")+1:]
scene = bpy.context.scene
objects = bpy.data.objects
if name == "archive":
    def visible(prefix, frame):
        scene.frame_set(frame)
        return sum(not x.hide_render for x in objects if x.name.startswith(prefix))
    checks = {"start":visible("First ",1), "read":visible("First ",60),
              "afterTurnFirst":visible("First ",148),"return":visible("Return ",148)}
    assert checks=={"start":0,"read":13,"afterTurnFirst":0,"return":12},checks
elif name == "vent":
    hinge = objects["Hatch hinge"]
    scene.frame_set(1)
    closed=abs(hinge.rotation_euler.z)
    scene.frame_set(124)
    opened=math.degrees(hinge.rotation_euler.z)
    vapors=sum(not x.hide_render for x in objects if x.name.startswith("Vapor layer"))
    puddles=sum(not x.hide_render for x in objects if x.name.startswith("Green wetness on floor"))
    checks={"closed":closed,"openDegrees":opened,"vaporLayers":vapors,"puddleShapes":puddles}
    assert closed<.0001 and abs(opened-16)<.001 and vapors==17 and puddles==5,checks
elif name == "static":
    checks={}
    for label,start,finish,delta in (("ArtA",1,21,7),("ArtB",1,21,7),("Calendar",41,61,math.hypot(2.45,.58))):
        obj=next(iter(bpy.data.collections[label].objects))
        scene.frame_set(start)
        base=obj.location.copy()
        scene.frame_set(finish)
        checks[label]=(base-obj.location).length
        assert abs(checks[label]-delta)<.0001,checks
    checks["PlantAnimatedFinishes"]=sum(mat.node_tree is not None and mat.node_tree.animation_data is not None for mat in bpy.data.materials)
    assert checks["PlantAnimatedFinishes"]>0,checks
elif name=="printer":
    checks={"sheets":len(bpy.data.collections["02 | 60 листов"].objects),
            "receiptPanels":sum(x.name.startswith("Receipt half") for x in objects),
            "rustleCues":sum(x.name.startswith("Шелест") for x in scene.timeline_markers)}
    assert checks=={"sheets":60,"receiptPanels":2,"rustleCues":5},checks
else:
    raise ValueError(name)
Path(dest).write_text(json.dumps(checks,indent=2)+"\n")
