"""Export the baked animation from the final Blender scene in map coordinates."""
import math
from pathlib import Path
import struct
import sys

import bpy

output=Path(sys.argv[sys.argv.index("--")+1])
scene=bpy.context.scene
sheets=sorted(bpy.data.collections["02 | 60 листов"].objects,key=lambda obj:obj.name)
assert len(sheets)==60
start=179
end=505
# Match the original 12 Hz bake, beginning just before the first active instant.
frames=range(start,end+1,2)
records=[bytearray() for _ in sheets]
for frame in frames:
    scene.frame_set(frame)
    for obj,record in zip(sheets,records):
        x,y,z=obj.location
        rx,ry,rz=obj.rotation_euler
        curl,bow,fold,twist=(key.value for key in obj.data.shape_keys.key_blocks[1:])
        coordinates=[round(v*1024) for v in (x,z,-y)]
        rotation=[round(v*2048) for v in (rx,ry,rz)]
        bend=[round(v*4096) for v in (curl,bow,fold,twist)]
        record.extend(struct.pack("<10h",*coordinates,*rotation,*bend))

# Use a single ASCII row per sheet so the map does not need external content.
lines=['-- Generated from Kontur_Printer_Paper_v30.blend by export_flight.py.',
       'local flight = {',f'    count = {len(frames)}, rate = 12, lead = {7.45-(start-1)/24:.9f},',
       '    sheets = {']
for obj,record in zip(sheets,records):
    points=obj.data.vertices
    width=max(v.co.x for v in points)-min(v.co.x for v in points)
    length=max(v.co.y for v in points)-min(v.co.y for v in points)
    assert len(record)==len(frames)*20
    encoded=record.hex()
    lines.append(f'        {{width={width:.6f},length={length:.6f},data="{encoded}"}},')
lines.extend(('    },','}',''))
output.write_text("\n".join(lines))
print(f"Exported {len(sheets)} sheets, {len(frames)} samples each")
