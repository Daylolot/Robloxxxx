from pathlib import Path
import bpy,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Ceiling_Office_Character_Study_v18.blend'))
scene=bpy.context.scene;upper=bpy.data.objects['UPPER_OFFICE / local inverted gravity'];upper.location=(0,0,0);upper.rotation_euler=(0,0,0)
scene.frame_set(120)
bpy.data.collections['Measured office context / v13 geometry retained in v17'].hide_render=True
bpy.data.objects['Measured office floor'].hide_render=True
ld=bpy.data.lights.new('Portrait inspection softbox','AREA');ld.energy=18;ld.shape='DISK';ld.size=.8
lo=bpy.data.objects.new('Portrait inspection softbox',ld);scene.collection.objects.link(lo);lo.location=(.30,-.65,1.7);lo.rotation_euler=(Vector((0,-.12,1.20))-lo.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera;cam.location=(.22,-.89,1.44);cam.rotation_euler=(Vector((0,-.12,1.20))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=70
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'11_upright_character_inspection.png');bpy.ops.render.render(write_still=True)
print('PORTRAIT_DONE / inspection orientation only / source file unchanged',flush=True)
