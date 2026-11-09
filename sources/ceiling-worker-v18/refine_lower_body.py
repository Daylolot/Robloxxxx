from pathlib import Path
import bpy,bmesh,math,json
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18';FILE=OUT/'Ceiling_Office_Character_Study_v18.blend'
bpy.ops.wm.open_mainfile(filepath=str(FILE));scene=bpy.context.scene;rig=bpy.data.objects['OfficeWorker anatomical rig'];base=bpy.data.objects['Anatomy working base'];skin=bpy.data.objects['Worker / face neck forearms and hands'];pants=bpy.data.objects['Worker / dark seated trousers']
# The A-pose toes extend past x=.24; exclude them explicitly from the skin cut.
vg=skin.vertex_groups.get('Visible face and arms')or skin.vertex_groups.new(name='Visible face and arms')
vg.add([v.index for v in skin.data.vertices if v.co.z>.65],1,'REPLACE')
mask=skin.modifiers.new('Remove source feet from face-and-arms cut','MASK');mask.vertex_group=vg.name
while list(skin.modifiers).index(mask)>1:
    bpy.context.view_layer.objects.active=skin;bpy.ops.object.modifier_move_up(modifier=mask.name)

# Preserve the outer sides of the trousers, while continuing to exclude hands.
pants.data=base.data.copy();pants.data.materials.clear();pants.data.materials.append(bpy.data.materials['Charcoal woven trousers'])
bm=bmesh.new();bm.from_mesh(pants.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if not(.08<(c:=f.calc_center_median()).z<.90 and(c.z<.65 or abs(c.x)<.245))],context='FACES')
bm.to_mesh(pants.data);bm.free();pants.data.update()
for v in pants.data.vertices:
    c=v.co.copy();v.co+=v.normal*(.014+.0035*math.sin(c.z*72+c.x*18)*math.sin(c.y*83+c.z*19))

# Align the rest leg bones with the source mesh's relaxed, spread stance.
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for side,s in [('L',1),('R',-1)]:
    b=rig.data.edit_bones['thigh.'+side];b.head=(s*.105,0,.87);b.tail=(s*.18,-.015,.46)
    b=rig.data.edit_bones['shin.'+side];b.head=(s*.18,-.015,.46);b.tail=(s*.24,-.015,.10)
    b=rig.data.edit_bones['foot.'+side];b.head=(s*.24,-.015,.10);b.tail=(s*.24,-.17,.04)
bpy.ops.object.mode_set(mode='OBJECT')
targets={}
for side,s in [('L',1),('R',-1)]:
    targets['thigh.'+side]=(Vector((s*.09,0,.49)),Vector((s*.125,-.40,.48)))
    targets['shin.'+side]=(Vector((s*.125,-.40,.48)),Vector((s*.14,-.43,.10)))
    targets['foot.'+side]=(Vector((s*.14,-.43,.10)),Vector((s*.14,-.60,.04)))
for frame in range(1,241):
    scene.frame_set(frame)
    for kind in ['thigh','shin','foot']:
        for side in ['L','R']:
            name=kind+'.'+side;a,b=targets[name];rest=rig.data.bones[name];R=(rest.tail_local-rest.head_local).rotation_difference(b-a)
            desired=Matrix.Translation(a)@R.to_matrix().to_4x4()@Matrix.Translation(-rest.head_local)@rest.matrix_local
            ratio=(b-a).length/(rest.tail_local-rest.head_local).length
            for row in range(3):desired[row][1]*=ratio
            p=rig.pose.bones[name];p.matrix=desired
            for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(channel,frame=frame)
        bpy.context.view_layer.update()
scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=skin.evaluated_get(dg);me=ev.to_mesh()
lowest=min(p.center.z for p in me.polygons);assert lowest>.6,lowest
ev.to_mesh_clear()
(OUT/'Lower_Body_Check.json').write_text(json.dumps({'lowestVisibleSkinFaceAboveUpperFloorMetres':lowest,'sourceFeetHidden':True,'trouserSidesPreserved':True,'legRestPoseAligned':True},indent=2))
scene.frame_set(120);bpy.ops.wm.save_as_mainfile(filepath=str(FILE),compress=True)
print('LOWER_BODY_REFINED',lowest,flush=True)
