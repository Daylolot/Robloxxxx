"""Render matched hand views, player views and the animated monitor."""

from pathlib import Path
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "outputs/CeilingWorker_2026-11-08"
REVISIONS = {rev: PROJECT / f"Revision{rev}" for rev in (20, 21)}
if (ROOT / "models").is_dir():
    REVISIONS = {rev: ROOT / "models" / f"ceiling-worker-v{rev}" for rev in (20, 21)}
OUT = REVISIONS[21]
SIDE_VIEW = ((.83, -.42, 1.105), (0, -.46, .925), 43)
SHOTS = [
    ("01_v20_side", 20, 21, True, SIDE_VIEW),
    ("02_v21_side", 21, 21, True, SIDE_VIEW),
    ("03_v21_other_side", 21, 16, True, ((-.83, -.42, 1.105), (0, -.46, .925), 43)),
    ("04_v21_above", 21, 21, True, ((0, -.44, 2.19), (0, -.44, .83), 52)),
    ("05_v21_player", 21, 34, False, ((-.5, 1.4, 1.6), (0, .53, 2.36), 47)),
    ("06_v21_map_approach", 21, 13, False, None),
    ("07_v21_map_near", 21, 167, False, None),
    ("08_v21_lamp_off", 21, 34, False, ((-.5, 1.4, 1.6), (0, .53, 2.36), 47)),
]


def load(revision):
    path = REVISIONS[revision] / f"Ceiling_Office_Character_Study_v{revision}.blend"
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return bpy.context.scene


def place_camera(camera, position, target, lens):
    camera.location = position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = lens


def show_upright(scene):
    upper = bpy.data.objects["UPPER_OFFICE / local inverted gravity"]
    upper.location = (0, 0, 0)
    upper.rotation_euler = (0, 0, 0)
    visible = set(upper.children_recursive) | {upper, scene.camera}
    for obj in scene.objects:
        if obj not in visible:
            obj.hide_render = True
    light = bpy.data.lights.new("Arm inspection light", "AREA")
    light.energy, light.shape, light.size = 30, "DISK", .9
    obj = bpy.data.objects.new(light.name, light)
    scene.collection.objects.link(obj)
    obj.location = (.1, -.65, 1.8)


def movie(scene, name, height):
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 8
    scene.render.resolution_x = round(height * 4 / 3)
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = str(OUT / f"{name}.mp4")
    bpy.ops.render.render(animation=True)


if "--movie" in sys.argv:
    movie(load(21), "Office_Encounter", 600)
elif "--hands-movie" in sys.argv:
    scene = load(21)
    show_upright(scene)
    scene.camera.animation_data_clear()
    scene.camera.data.animation_data_clear()
    place_camera(scene.camera, *SIDE_VIEW)
    movie(scene, "Hands_In_Motion", 480)
else:
    selected = next((arg.split("=")[1].split(",") for arg in sys.argv if arg.startswith("--shots=")), None)
    for name, rev, frame, upright, view in SHOTS:
        if selected and name[:2] not in selected:
            continue
        scene = load(rev)
        scene.frame_set(frame)
        if name.endswith("lamp_off"):
            switch = bpy.data.objects["Lower desk / upper lamp switch"]
            switch["Upper lamp on"] = 0
            switch.update_tag()
        scene.camera.animation_data_clear()
        scene.camera.data.animation_data_clear()
        if upright:
            show_upright(scene)
        if view is None:
            matrix = bpy.data.objects["Monitor / angled side position"].matrix_world
            view = (matrix @ Vector((.09, .84, 1.075)), matrix @ Vector((0, .011, 1.075)), 49)
        place_camera(scene.camera, *view)
        scene.render.use_sequencer = False
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 18
        scene.cycles.use_denoising = True
        scene.render.resolution_x = 1000
        scene.render.resolution_y = 750
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(OUT / f"{name}.png")
        bpy.ops.render.render(write_still=True)
