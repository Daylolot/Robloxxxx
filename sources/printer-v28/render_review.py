"""Render the key views from the final saved Blender scene."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

out=Path(sys.argv[sys.argv.index("--")+1])
scene=bpy.context.scene
shots=(
    ("01_printer_before",0.12,"Принтер"),
    ("02_paper_feed",0.88,"Принтер"),
    ("03_warning_read",2.45,"Распечатка"),
    ("04_contact_before",7.2,"Край листа"),
    ("05_first_edge",7.8,"Край листа"),
    ("06_peel_at_desk",9.1,"Отрыв у стола"),
    ("07_wave_from_printer",11.0,"От принтера по залу"),
    ("08_across_aisle",15.0,"Поперёк прохода"),
    ("09_levitation",19.0,"От принтера по залу"),
    ("10_print_output",1.41,"Принтер"),
    ("11_countdown",5.6,"Край листа"),
    ("12_next_stack",8.83,"Отрыв у стола"),
)
# For stills, use manual cameras in the already baked frame and disable sequencer overlays.
for marker in list(scene.timeline_markers):
    scene.timeline_markers.remove(marker)
scene.render.image_settings.file_format="PNG"
scene.render.use_sequencer=False
scene.eevee.taa_render_samples=16
scene.render.resolution_x=1180
scene.render.resolution_y=750
for name,seconds,camera in shots:
    scene.frame_set(1+round(seconds*scene.render.fps))
    scene.camera=bpy.data.objects[camera]
    scene.render.filepath=str((out/(name+".png")).resolve())
    bpy.ops.render.render(write_still=True)

cam=bpy.data.objects["Поперёк прохода"]
cam.data.lens=54
for name,number,seconds,offset in (
    ("13_sheet_arc",3,10.5,(-2.9,-1.8,.27)),
    ("14_sheet_roll",10,12.55,(2.55,1.15,-.45)),
    ("15_sheet_hover",24,17.75,(-1.6,2.65,.02)),
):
    scene.frame_set(1+round(seconds*scene.render.fps))
    target=bpy.data.objects[f"Лист {number:02d}"].location.copy()
    cam.location=target+Vector(offset)
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=cam
    scene.render.filepath=str((out/(name+".png")).resolve())
    bpy.ops.render.render(write_still=True)
