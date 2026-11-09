from pathlib import Path
import bpy,json,sys,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Ceiling_Office_Character_Study_v18.blend'))
scene=bpy.context.scene;cam=scene.camera
args=sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else[]
def camera(pos,target,lens):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
if '--movie'in args:
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=16;scene.eevee.use_raytracing=False
    scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    # 120 rendered frames are encoded at 12 fps: ten seconds at the source 24 fps timing.
    scene.render.fps=12;scene.frame_step=2;scene.frame_start=1;scene.frame_end=239
    camera((.23,1.36,1.58),(0,.13,2.03),55)
    scene.render.image_settings.file_format='FFMPEG';scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264';scene.render.ffmpeg.constant_rate_factor='MEDIUM'
    scene.render.filepath=str(OUT/'Attention_Example_10sec.mp4');bpy.ops.render.render(animation=True)
else:
    select=next((s.split('=',1)[1].split(',')for s in args if s.startswith('--shots=')),None)
    scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
    scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    for shot in json.loads((OUT/'Shots.json').read_text()):
        if select and shot['name'][:2]not in select:continue
        if shot['name'].startswith('06_'):shot.update(camera=[-.8,.15,1.8],target=[0,-.93,2.35],lens=45)
        camera(shot['camera'],shot['target'],shot['lens']);scene.frame_set(120 if shot['name'][:2]in['04','09']else 1)
        scene.render.filepath=str(OUT/(shot['name']+'.png'));bpy.ops.render.render(write_still=True)
        print('REVIEW_FRAME_DONE',shot['name'],flush=True)
print('RENDER_COMPLETE',flush=True)
