"""Render the timed Blender preview with the packed review audio."""
from pathlib import Path
import sys
import bpy

out=Path(sys.argv[sys.argv.index("--")+1]).resolve()
scene=bpy.context.scene
scene.render.resolution_x=768
scene.render.resolution_y=486
scene.eevee.taa_render_samples=4
scene.render.image_settings.media_type="VIDEO"
scene.render.ffmpeg.format="MPEG4"
scene.render.ffmpeg.codec="H264"
scene.render.ffmpeg.audio_codec="AAC"
scene.render.ffmpeg.constant_rate_factor="MEDIUM"
scene.render.filepath=str(out/"Printer_Paper_v28.mp4")
bpy.ops.render.render(animation=True)
