"""Render the hands, entrance and timed response from the v20 Blender scene."""
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_path import PATH

root = Path(__file__).resolve().parents[2]
out = root / 'outputs/CeilingWorker_2026-11-08/Revision20'
if (root / 'models').is_dir():
    out = root / 'models/ceiling-worker-v20'
source = out / 'Ceiling_Office_Character_Study_v20.blend'
shots = [
    ('01_keys_from_above', 16, True, (0, -.55, 1.88), (0, -.55, .82), 64),
    ('02_side_contact', 16, True, (-.62, -.43, 1.04), (-.045, -.55, .815), 63),
    ('03_other_side', 21, True, (.64, -.40, 1.04), (.05, -.55, .815), 63),
    ('04_look_from_door', 1, False, *PATH[0][1:]),
    ('05_follow_the_sound', 45, False, *PATH[2][1:]),
    ('06_gaze_after_pause', 106, False, (-.88, 1.45, 1.54), (0, .21, 2.00), 66),
    ('07_inverted_hands', 34, False, (-.5, 1.4, 1.6), (0, .53, 2.36), 49),
    ('08_wider_room', 106, False, (-2.5, 1.6, 1.6), (0, .2, 2.35), 36),
]


def camera(pos, target, lens):
    cam = bpy.context.scene.camera
    cam.location = pos
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens


def make_upright():
    scene = bpy.context.scene
    upper = bpy.data.objects['UPPER_OFFICE / local inverted gravity']
    upper.location = (0, 0, 0)
    upper.rotation_euler = (0, 0, 0)
    visible = set(upper.children_recursive) | {upper, scene.camera}
    for obj in scene.objects:
        if obj not in visible:
            obj.hide_render = True
    lamp = bpy.data.lights.new('Inspection softbox', 'AREA')
    lamp.energy = 32
    lamp.shape = 'DISK'
    lamp.size = .8
    light = bpy.data.objects.new('Inspection softbox', lamp)
    scene.collection.objects.link(light)
    light.location = (.15, -.56, 1.8)


if '--movie' in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = 8
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start, scene.frame_end, scene.frame_step = 1, 240, 1
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.audio_codec = 'AAC'
    scene.render.ffmpeg.audio_bitrate = 96
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.filepath = str(out / 'Doorway_And_Reaction.mp4')
    scene.render.use_sequencer = True
    bpy.ops.render.render(animation=True)
else:
    selection = next((arg.split('=')[1].split(',') for arg in sys.argv if arg.startswith('--shots=')), None)
    for name, frame, upright, pos, target, lens in shots:
        if selection and name[:2] not in selection:
            continue
        bpy.ops.wm.open_mainfile(filepath=str(source))
        scene = bpy.context.scene
        if upright:
            make_upright()
        scene.render.use_sequencer = False
        scene.frame_set(frame)
        scene.camera.animation_data_clear()
        scene.camera.data.animation_data_clear()
        camera(pos, target, lens)
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 18
        scene.cycles.use_denoising = True
        scene.render.resolution_x = 1000
        scene.render.resolution_y = 750
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = str(out / (name + '.png'))
        bpy.ops.render.render(write_still=True)
