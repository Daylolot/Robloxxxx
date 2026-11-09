"""Render matching comparison views and a motion sample from the saved scenes."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[2]
models = root / 'models'
project = root / 'outputs/CeilingWorker_2026-11-08'
revisions = {version: project / f'Revision{version}' for version in (18, 19)}
if models.is_dir():
    revisions = {version: models / f'ceiling-worker-v{version}' for version in (18, 19)}
out = revisions[19]
movie = '--movie' in sys.argv
shots = [
    ('01_v18_overhead', 18, True, (0,-.55,1.9), (0,-.55,.82), 45, .64),
    ('02_v19_overhead', 19, True, (0,-.55,1.9), (0,-.55,.82), 45, .64),
    ('03_v19_left', 19, True, (-.76,-.34,1.15), (0,-.49,.86), 54, None),
    ('04_v19_right', 19, True, (.76,-.34,1.15), (0,-.49,.86), 54, None),
    ('05_v19_player', 19, False, (-.5,1.4,1.6), (0,.53,2.36), 49, None),
    ('06_v19_room', 19, False, (-2.5,1.6,1.6), (0,.2,2.35), 36, None),
]
if movie:
    shots = [('Typing_And_Pause', 19, True, (-.62,-.27,1.48), (0,-.47,.88), 44, None)]
for name, revision, upright, position, target, lens, ortho in shots:
    bpy.ops.wm.open_mainfile(filepath=str(revisions[revision] / f'Ceiling_Office_Character_Study_v{revision}.blend'))
    scene = bpy.context.scene
    upper = bpy.data.objects['UPPER_OFFICE / local inverted gravity']
    camera = scene.camera
    if upright:
        upper.location = (0,0,0)
        upper.rotation_euler = (0,0,0)
        for ob in scene.objects:
            if ob != upper and ob not in upper.children_recursive and ob != camera:
                ob.hide_render = True
        lamp = bpy.data.lights.new('Comparison softbox', 'AREA')
        lamp.energy = 32
        lamp.shape = 'DISK'
        lamp.size = .8
        light = bpy.data.objects.new('Comparison softbox', lamp)
        scene.collection.objects.link(light)
        light.location = (.15,-.56,1.8)
    camera.location = position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type = 'ORTHO' if ortho else 'PERSP'
    camera.data.lens = lens
    if ortho:
        camera.data.ortho_scale = ortho
    scene.render.resolution_x = 900 if not movie else 768
    scene.render.resolution_y = 675 if not movie else 576
    scene.render.resolution_percentage = 100
    if movie:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        scene.eevee.taa_render_samples = 8
        scene.render.fps = 12
        scene.frame_start, scene.frame_end, scene.frame_step = 1, 239, 2
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        scene.render.filepath = str(out / (name + '.mp4'))
        bpy.ops.render.render(animation=True)
    else:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 14
        scene.cycles.use_denoising = True
        scene.frame_set(120)
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = str(out / (name + '.png'))
        bpy.ops.render.render(write_still=True)
    print('RENDERED', name, flush=True)
