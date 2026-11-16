"""Colour calibration: four cubes with vertex colour #808080 exported with different colour handling.
A: attribute = sRGB numbers, colors_type LINEAR   B: attribute = linear, colors_type LINEAR
C: attribute = linear, colors_type SRGB          D: attribute = sRGB numbers, colors_type SRGB
Run: Blender -b --python calib_colors.py -- <out_dir>"""
import sys
from pathlib import Path
import bpy
_here = Path(__file__).resolve().parent
_src = (_here / "interior_hero.py").read_text()
_head = _src[:_src.index("# ---------------------------------------------------------------- items")]
exec(compile(_head, "interior_hero_head", "exec"), globals())
for variant, srgb_numbers, ctype in (("A", True, "LINEAR"), ("B", False, "LINEAR"), ("C", False, "SRGB"), ("D", True, "SRGB")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    it = Item("Calib" + variant)
    box(it, "paint", (3, 3, 3), (0, 0, 0), bevel=0.0, color="#808080")
    objs = finish(it)
    for ob in objs:
        for d in ob.data.color_attributes["Col"].data:
            r, g, b, a = d.color
            if srgb_numbers:
                d.color = (unlin(r), unlin(g), unlin(b), a)
    (OUT / "fbx").mkdir(exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=str(OUT / "fbx" / f"Calib{variant}.fbx"), use_selection=True, object_types={"MESH"}, global_scale=1.0,
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                             colors_type=ctype, mesh_smooth_type="FACE", add_leaf_bones=False)
    print("exported", variant, ctype, "srgb_numbers" if srgb_numbers else "linear")
