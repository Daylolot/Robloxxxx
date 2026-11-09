from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/CeilingWorker_2026-11-08/Revision18/Ceiling_Office_Character_Study_v18.blend'))
rows={}
for name in ['Anatomy working base','Worker / face neck forearms and hands','Worker / tailored white cotton shirt']:
    o=bpy.data.objects[name];vs=o.data.vertices
    rows[name]=[{'z':z/100,'n':len(vv),'xmin':min((v.co.x for v in vv),default=0),'xmax':max((v.co.x for v in vv),default=0)}for z in range(80,145,5)if(vv:=[v for v in vs if z/100<v.co.z<(z+5)/100 and abs(v.co.x)>.25])]
(ROOT/'work/ceiling_worker_v18/anatomy_slices.json').write_text(json.dumps(rows,indent=2))
print('ANATOMY',json.dumps(rows))
