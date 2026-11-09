"""Local, editable character/ceiling-office study. CC0 anatomy, bespoke tailoring and set."""
from pathlib import Path
import bpy, math, json, random, sys
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18'
OUT.mkdir(exist_ok=True,parents=True)
ASSET=ROOT/'work/ceiling_worker_v18/assets/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
random.seed(187)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.fps=24
scene.world=bpy.data.worlds.new('Soft office ambience');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.18,.19,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
scene.view_settings.view_transform='AgX'

def mat(name,c,rough=.5,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
def micro(m,scale,strength,distance):
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=distance
    l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    return tex
skin=mat('Skin / restrained pores and subsurface',(.48,.315,.225),.49)
p=skin.node_tree.nodes['Principled BSDF'];p.inputs['Subsurface Weight'].default_value=.09;p.inputs['Subsurface Radius'].default_value=(1,.38,.2)
micro(skin,185,.18,.0012)
n=skin.node_tree.nodes;l=skin.node_tree.links
attr=n.new('ShaderNodeVertexColor');attr.layer_name='Complexion';l.new(attr.outputs['Color'],p.inputs['Base Color'])
shirt=mat('Ivory cotton / woven and creased',(.72,.735,.71),.8);micro(shirt,280,.22,.001)
pants=mat('Charcoal woven trousers',(.035,.044,.052),.82);micro(pants,210,.19,.001)
hair=mat('Dark brown hair',(.018,.011,.008),.64);micro(hair,380,.3,.001)
lip=mat('Quiet lip tone',(.31,.15,.13),.54)
white=mat('Sclera / warm grey',(.65,.67,.62),.22)
iris=mat('Iris / grey hazel',(.095,.12,.105),.27);pupil=mat('Pupil',(.003,.004,.003),.12)
black=mat('Graphite enamel',(.018,.023,.025),.4,.3)
chrome=mat('Brushed nickel',(.22,.25,.26),.3,.78)
wood=mat('Aged walnut desktop',(.19,.105,.052),.47);micro(wood,65,.1,.001)
carpet=mat('Upper office / graphite olive carpet',(.11,.14,.12),.94);micro(carpet,340,.55,.002)
paper=mat('Paper / warm uncoated',(.78,.77,.66),.89)
tie=mat('Burgundy loosened tie',(.10,.025,.025),.64);micro(tie,210,.17,.001)
rubber=mat('Shoe leather',(.018,.014,.012),.36)
fabric=mat('Chair upholstery',(.032,.047,.05),.93);micro(fabric,220,.45,.001)
plaster=mat('Warm office plaster',(.58,.59,.51),.88);micro(plaster,95,.1,.001)
panel=mat('Aged ceiling tiles',(.60,.61,.54),.9);micro(panel,180,.15,.001)
green=mat('Muted office teal',(.11,.23,.22),.54)
earth=mat('Potting soil',(.045,.026,.013),.96)
leaf=mat('Living leaves',(.055,.15,.055),.67)
ceramic=mat('Coffee mug / cream glaze',(.71,.68,.55),.26)
coffee=mat('Coffee surface',(.025,.008,.003),.17)
yellow=mat('Old fluorescent diffuser',(.65,.55,.32),.6)
screen=mat('Monitor / floor plan',(.04,.10,.10),.35)
screen.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(.07,.19,.18,1)
screen.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.7

def mesh(name,vertices,faces,material,parent=None,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
    o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.parent=parent
    if material:me.materials.append(material)
    for f in me.polygons:f.use_smooth=smooth
    return o
def cube(name,pos,size,material,parent=None,bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    o.parent=parent;return o
def sphere(name,pos,size,material,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=pos)
    o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material);o.parent=parent
    for p in o.data.polygons:p.use_smooth=True
    return o
def cylinder(name,a,b,r,material,parent=None,r2=None):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r,radius2=r if r2 is None else r2,depth=(b-a).length,location=(a+b)*.5)
    o=bpy.context.object;o.name=name;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    o.data.materials.append(material);o.parent=parent
    for p in o.data.polygons:p.use_smooth=True
    return o
def curve(name,points,r,material,parent=None):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=10;cu.bevel_depth=r;cu.bevel_resolution=2
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.data.materials.append(material);o.parent=parent;return o
def text(name,body,pos,size,material,parent=None,rotation=(math.pi/2,0,0)):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.00015
    o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=rotation;o.data.materials.append(material);o.parent=parent;return o
def light(name,pos,power,size,color,parent=None):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.parent=parent;return o

upper=bpy.data.objects.new('UPPER_OFFICE / local inverted gravity',None);scene.collection.objects.link(upper)
worker=bpy.data.objects.new('WORKER / 33 years / seated anatomy',None);scene.collection.objects.link(worker);worker.parent=upper

with bpy.data.libraries.load(str(ASSET),link=False)as(src,dst):
    dst.objects=['GEO-body_male_realistic','GEO-body_male_realistic.eye.L','GEO-body_male_realistic.eye.R']
base=bpy.data.objects['GEO-body_male_realistic'];base.location=(0,0,0)
scene.collection.objects.link(base);base.name='Anatomy working base';base.modifiers.clear();base.data.materials.clear();base.data.materials.append(skin)
for poly in base.data.polygons:poly.use_smooth=True

# Anatomical skeleton and a reproducible seated pose. The face/hands retain proper topology.
rest={'pelvis':((0,0,.86),(0,0,1.03),None),
      'spine':((0,0,1.03),(0,-.005,1.26),'pelvis'),
      'chest':((0,-.005,1.26),(0,-.015,1.43),'spine'),
      'neck':((0,-.015,1.43),(0,-.01,1.51),'chest'),
      'head':((0,-.01,1.51),(0,-.015,1.68),'neck')}
pose={'pelvis':((0,0,.48),(0,-.025,.65)),
      'spine':((0,-.025,.65),(0,-.075,.88)),
      'chest':((0,-.075,.88),(0,-.095,1.05)),
      'neck':((0,-.095,1.05),(0,-.105,1.13)),
      'head':((0,-.105,1.13),(0,-.12,1.30))}
for side,s in [('L',1),('R',-1)]:
    rest.update({f'upper_arm.{side}':((s*.17,0,1.39),(s*.30,-.012,1.15),'chest'),
                 f'forearm.{side}':((s*.30,-.012,1.15),(s*.355,-.045,.94),f'upper_arm.{side}'),
                 f'hand.{side}':((s*.355,-.045,.94),(s*.415,-.055,.76),f'forearm.{side}'),
                 f'thigh.{side}':((s*.09,0,.87),(s*.105,-.015,.46),'pelvis'),
                 f'shin.{side}':((s*.105,-.015,.46),(s*.11,-.015,.10),f'thigh.{side}'),
                 f'foot.{side}':((s*.11,-.015,.10),(s*.11,-.17,.04),f'shin.{side}')})
    pose.update({f'upper_arm.{side}':((s*.17,-.085,1.01),(s*.255,-.26,.80)),
                 f'forearm.{side}':((s*.255,-.26,.80),(s*.155,-.49,.81)),
                 f'hand.{side}':((s*.155,-.49,.81),(s*.13,-.66,.80)),
                 f'thigh.{side}':((s*.09,0,.49),(s*.125,-.40,.48)),
                 f'shin.{side}':((s*.125,-.40,.48),(s*.14,-.43,.10)),
                 f'foot.{side}':((s*.14,-.43,.10),(s*.14,-.60,.04))})
ar=bpy.data.armatures.new('OfficeWorker anatomical rig');rig=bpy.data.objects.new('OfficeWorker anatomical rig',ar);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);base.select_set(False);bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b,parent)in rest.items():
    bone=ar.edit_bones.new(name);bone.head=a;bone.tail=b
    if parent:bone.parent=ar.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');rig.parent=worker
bpy.ops.object.select_all(action='DESELECT');base.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO');print('AUTOMATIC_SKINNING_DONE',flush=True)
for name,(a,b)in pose.items():
    pb=rig.pose.bones[name];old=ar.bones[name]
    rot=(old.tail_local-old.head_local).rotation_difference(Vector(b)-Vector(a))
    pb.matrix=Matrix.Translation(Vector(a))@rot.to_matrix().to_4x4()@Matrix.Translation(-old.head_local)@old.matrix_local
    bpy.context.view_layer.update()

def region(name,choose,material,inflate=0,folds=False):
    o=base.copy();o.data=base.data.copy();scene.collection.objects.link(o);o.name=name
    o.hide_render=False;o.hide_set(False)
    o.data.materials.clear();o.data.materials.append(material)
    # Cull unrelated faces without changing indices before assigning shape/weight data.
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data)
    remove=[]
    for f in bm.faces:
        c=f.calc_center_median()
        if not choose(c):remove.append(f)
    bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free();o.data.update()
    for v in o.data.vertices:
        co=v.co.copy();d=inflate
        if folds:d+=.0035*math.sin(co.z*72+co.x*18)*math.sin(co.y*83+co.z*19)
        v.co+=v.normal*d
    return o
skin_obj=region('Worker / face neck forearms and hands',lambda c:c.z>1.425 or(abs(c.x)>.30 and c.z<1.065),skin)
shirt_obj=region('Worker / tailored white cotton shirt',lambda c:.87<c.z<1.435 and not(abs(c.x)>.24 and c.z<1.04),shirt,.014,True)
pants_obj=region('Worker / dark seated trousers',lambda c:.08<c.z<.90 and abs(c.x)<.245,pants,.014,True)
base.hide_render=True;base.hide_set(True)

# Color variation is tied to anatomy, not to lighting: eyelids, ears and lips stay readable.
colors=skin_obj.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
for v,col in zip(skin_obj.data.vertices,colors.data):
    x,y,z=v.co
    under=math.exp(-((abs(x)-.032)/.025)**2-((z-1.555)/.018)**2)*max(0,min(1,(-y-.06)*20))
    lips=math.exp(-(x/.035)**4-((z-1.51)/.008)**2)*max(0,min(1,(-y-.08)*30))
    ear=max(0,(abs(x)-.065)*20)if z>1.50 else 0
    col.color=(.51-.10*under-.05*lips+.035*ear,.335-.085*under-.12*lips,.25-.05*under-.065*lips,1)
    # Restrained mouth-corner lift, approximately 1 mm; never an exaggerated grin.
    v.co.z+=.0012*math.exp(-((abs(x)-.026)/.011)**2-((z-1.510)/.015)**2)*max(0,min(1,(-y-.08)*30))
sub=skin_obj.modifiers.new('Facial surface subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
for o in [shirt_obj,pants_obj]:
    sub=o.modifiers.new('Tailored smooth fabric','SUBSURF');sub.levels=1;sub.render_levels=1
    sol=o.modifiers.new('Fabric edge thickness','SOLIDIFY');sol.thickness=.0015

# Head attachments use the same actual posed head transform as the anatomical mesh.
headrest=ar.bones['head'].matrix_local
headmap=rig.pose.bones['head'].matrix@headrest.inverted()
head=bpy.data.objects.new('Head attachment and gaze pivot',None);scene.collection.objects.link(head);head.parent=worker
head.matrix_basis=headmap
for suffix in ['L','R']:
    e=bpy.data.objects[f'GEO-body_male_realistic.eye.{suffix}'];scene.collection.objects.link(e)
    # Library objects have not necessarily evaluated matrix_world when first linked.
    # Use their source-space anatomical locations instead of a stale world matrix.
    center=Vector((.0328815 if suffix=='L' else -.03288,-.12182286,1.57370663))
    e.hide_render=True;e.hide_set(True)
    sphere('Sclera.'+suffix,center,(.012,.012,.012),white,head)
    sphere('Iris.'+suffix,center+Vector((0,-.011,0)),(.0052,.0016,.0052),iris,head)
    sphere('Pupil.'+suffix,center+Vector((0,-.0124,0)),(.0022,.0006,.0022),pupil,head)

# Hair cap follows a genuine scalp surface. The part and tapered strands break its silhouette.
hair_obj=region('Worker / close combed hair cap',lambda c:c.z>(1.625 if c.y<-.055 else 1.575 if c.y>.025 else 1.606),hair,.002)
# Relax just the cut boundary, so individual topology edges do not create a zigzag hairline.
import bmesh
bm=bmesh.new();bm.from_mesh(hair_obj.data)
edgeverts=[v for v in bm.verts if v.is_boundary]
for k in range(4):
    updates={v:sum((e.other_vert(v).co for e in v.link_edges if e.is_boundary),Vector())/max(1,sum(e.is_boundary for e in v.link_edges)) for v in edgeverts}
    for v,co in updates.items():v.co=v.co.lerp(co,.35)
bm.to_mesh(hair_obj.data);bm.free();hair_obj.data.update()
sub=hair_obj.modifiers.new('Scalp smooth','SUBSURF');sub.levels=1
hair_obj.data.calc_loop_triangles()
triangles=list(hair_obj.data.loop_triangles)
weights=[t.area for t in triangles]
groom=bpy.data.curves.new('Short groom / tapered combed fibres','CURVE');groom.dimensions='3D';groom.bevel_depth=.00022;groom.bevel_resolution=1;groom.resolution_u=3
for k in range(5200):
    tr=random.choices(triangles,weights=weights,k=1)[0];a,b,c=[hair_obj.data.vertices[i]for i in tr.vertices]
    u=random.random();v=random.random()
    if u+v>1:u,v=1-u,1-v
    co=a.co*(1-u-v)+b.co*u+c.co*v
    norm=(a.normal*(1-u-v)+b.normal*u+c.normal*v).normalized()
    side=1 if co.x>-.024 else -1
    direction=Vector((side*.42,.8,-.18));direction-=norm*direction.dot(norm);direction.normalize()
    # Short hair lies against the scalp, then lifts 1–3 mm at the tip.
    length=random.uniform(.008,.021)
    sp=groom.splines.new('POLY');sp.points.add(3)
    for j,p in enumerate(sp.points):
        t=j/3;point=co+direction*(length*t)+norm*(.0007+.0025*math.sin(t*math.pi*.72))
        p.co=(*point,1);p.radius=1-.80*t
go=bpy.data.objects.new('Worker / short hair with a side part',groom);scene.collection.objects.link(go);go.parent=head;go.data.materials.append(hair)
for s in [-1,1]:
    points=[(s*(.014+i*.007),-.121-abs(i-2)*.001,1.600+.003*math.sin(i*.75))for i in range(5)]
    curve('Natural eyebrow',points,.0014,hair,head)

# Shirt details are placed in the seated frame. Separate geometry gives folds clear scale.
for s in [-1,1]:
    collar=mesh('Open collar',[(s*.012,-.125,1.073),(s*.065,-.115,1.075),(s*.087,-.151,1.017),(s*.025,-.163,1.042)],[(0,1,2,3)],shirt,worker)
    sol=collar.modifiers.new('Collar thickness','SOLIDIFY');sol.thickness=.002
    bev=collar.modifiers.new('Collar corners','BEVEL');bev.width=.003;bev.segments=2
curve('Shirt front placket',[(0,-.142,1.05),(0,-.175,.95),(0,-.173,.84),(0,-.153,.67)],.006,shirt,worker)
for z,y in[(1.015,-.155),(.94,-.178),(.865,-.178),(.79,-.173),(.71,-.158)]:
    sphere('Mother of pearl shirt button',(0,y-.004,z),(.0031,.0015,.0031),paper,worker)
tie_obj=mesh('Loosened tie blade',[(-.015,-.175,1.035),(.015,-.175,1.035),(.022,-.194,.79),(0,-.199,.758),(-.022,-.194,.79)],[(0,1,2,3,4)],tie,worker)
sol=tie_obj.modifiers.new('Tie folded fabric','SOLIDIFY');sol.thickness=.003
sphere('Loose tie knot',(0,-.169,1.035),(.018,.012,.021),tie,worker)
cube('Trouser belt',(0,-.035,.545),(.30,.20,.032),rubber,worker)
cube('Belt buckle',(0,-.141,.546),(.038,.009,.025),chrome,worker,.003)
for s in [-1,1]:
    sphere('Leather office shoe',(s*.14,-.515,.057),(.058,.13,.049),rubber,worker)
    cube('Shoe sole',(s*.14,-.515,.022),(.113,.252,.016),black,worker,.012)
    for j in range(4):curve('Shoe lace',[(s*.14-.025,-.51+j*.012,.094),(s*.14+.025,-.505+j*.012,.094)],.0012,black,worker)
cube('Shirt pocket',(-.09,-.157,.943),(.07,.006,.073),shirt,worker,.003)
curve('Pocket stitch',[(-.123,-.162,.974),(-.123,-.162,.913),(-.09,-.164,.905),(-.056,-.162,.913),(-.056,-.162,.974)],.0006,paper,worker)

# Furniture uses real metric proportions, with a clear head silhouette from the doorway.
cube('Inverted carpet island',(0,-.25,-.018),(2.35,2.55,.04),carpet,upper)
cube('Ceiling desk / walnut top',(0,-.74,.733),(1.65,.76,.045),wood,upper,.012)
for x in [-.73,.73]:
    for y in [-1.02,-.47]:
        cube('Steel desk leg',(x,y,.35),(.04,.04,.70),chrome,upper,.003)
    cube('Desk cross rail',(x,-.745,.16),(.023,.56,.025),black,upper,.003)
cube('Desk modesty panel',(0,-1.045,.49),(1.50,.025,.34),green,upper)
chair=bpy.data.objects.new('Chair / castors on upper carpet',None);scene.collection.objects.link(chair);chair.parent=upper
cube('Seat cushion',(0,.015,.435),(.46,.45,.075),fabric,chair,.045)
back=cube('Ergonomic upholstered back',(0,.235,.755),(.445,.075,.52),fabric,chair,.045);back.rotation_euler[0]=-.1
cylinder('Chair lift',(0,.015,.13),(0,.015,.41),.032,chrome,chair)
for i in range(5):
    a=i*math.tau/5;b=(math.cos(a)*.29,.015+math.sin(a)*.29,.074)
    cylinder('Chair spoke',(0,.015,.13),b,.014,chrome,chair)
    sphere('Rubber caster',b,(.034,.025,.035),black,chair)
for s in [-1,1]:
    cube('Armrest',(s*.27,-.015,.66),(.06,.27,.033),black,chair)
    cylinder('Armrest support',(s*.26,.04,.45),(s*.27,.04,.65),.014,chrome,chair)
cube('Drawer pedestal',(.60,-.74,.34),(.34,.56,.67),green,upper)
drawer=cube('Linked drawer / sliding front',(.60,-.443,.545),(.32,.024,.205),green,upper)
cube('Drawer pull',(.60,-.425,.575),(.13,.023,.014),chrome,upper,.004)
cube('Drawer lower front',(.60,-.443,.24),(.32,.025,.38),green,upper)

cube('Monitor base',(.05,-.91,.773),(.25,.20,.027),black,upper)
cube('Monitor post',(.05,-.956,.88),(.042,.038,.20),chrome,upper)
cube('Monitor bezel',(.05,-.972,1.065),(.54,.045,.34),black,upper)
cube('Plan display',(.05,-.945,1.065),(.502,.004,.302),screen,upper,.001)
# Geometry-built schematic remains legible without a remote image asset.
for x in [-.175,-.02,.14,.275]:
    cube('Plan wall vertical',(x,-.939,1.07),(.003,.002,.205),paper,upper,.0001)
for z in [.974,1.065,1.169]:cube('Plan wall horizontal',(.05,-.939,z),(.45,.002,.003),paper,upper,.0001)
text('Plan heading','KONTUR  /  FLOOR 04',(-.18,-.937,1.185),.018,paper,upper)
for x,z in[(-.095,1.023),(.08,1.107)]:sphere('Player marker',(x,-.936,z),(.007,.002,.007),green,upper)
cube('Keyboard shell',(0,-.575,.778),(.44,.145,.022),black,upper,.007)
for row in range(4):
    for col in range(14):cube('Keyboard key',(-.202+col*.03,-.623+row*.031,.792),(.026,.026,.008),paper,upper,.002)
cube('Space bar',(0,-.505,.791),(.155,.024,.009),paper,upper,.002)
cube('Mouse pad',(.35,-.59,.76),(.23,.23,.003),black,upper,.002)
sphere('Computer mouse',(.35,-.59,.785),(.031,.05,.022),black,upper)
curve('Mouse cable',[(.35,-.64,.783),(.37,-.74,.765),(.29,-.86,.765),(.25,-1.03,.76)],.002,black,upper)
for j in range(4):
    pg=cube('Loose report paper',(-.47,-.72+j*.002,.76+j*.001),(.21,.275,.0007),paper,upper,.0002);pg.rotation_euler[2]=-.09+j*.025
curve('Fountain pen',[(-.57,-.61,.769),(-.46,-.70,.769)],.003,black,upper)
cube('Document binder',(-.48,-.96,.78),(.25,.22,.035),green,upper,.004)
# Hollow cup, not an upside-down solid cylinder.
verts=[];faces=[]
for z,r in[(0,.031),(.077,.038),(.077,.032),(.008,.027)]:
    for i in range(48):a=i*math.tau/48;verts.append((.48+math.cos(a)*r,-.91+math.sin(a)*r,.76+z))
for ring in range(3):
    for i in range(48):j=(i+1)%48;faces.append((ring*48+i,ring*48+j,(ring+1)*48+j,(ring+1)*48+i))
mesh('Hollow glazed coffee mug',verts,faces,ceramic,upper)
curve('Mug handle',[(.51,-.91,.82),(.54,-.91,.818),(.545,-.91,.792),(.51,-.91,.778)],.006,ceramic,upper)
cylinder('Coffee / local gravity',(.48,-.91,.813),(.48,-.91,.814),.031,coffee,upper)
# Put the monitor to one side and turn its screen toward the worker.
monitor_root=bpy.data.objects.new('Monitor / angled side position',None);scene.collection.objects.link(monitor_root);monitor_root.parent=upper
monitor_root.location=(.48,-.91,0);monitor_root.rotation_euler[2]=math.radians(24)
for obj in list(upper.children):
    if obj==monitor_root:continue
    if obj.name.startswith(('Monitor base','Monitor post','Monitor bezel','Plan display','Plan wall','Plan heading','Player marker')):
        basis=obj.matrix_basis.copy();obj.parent=monitor_root;obj.matrix_basis=Matrix.Translation(Vector((-.05,.95,0)))@basis
    elif obj.name.startswith(('Hollow glazed coffee mug','Mug handle','Coffee / local gravity')):
        obj.location.x-=.93
for j in range(2):
    x=-.61+j*.05
    curve('Desk lamp arm',[(x,-1,.77),(x,-1,1.06),(x+.12,-.92,1.19)],.008,black,upper)
cube('Desk lamp shade',(-.465,-.91,1.18),(.20,.11,.045),green,upper)
lamp=light('Yellow desk light',(-.46,-.91,1.145),20,.13,(1,.67,.27),upper)
lamp.rotation_euler=(0,0,0)

# Small upper office: an open front, partial partition, shelf and domestic details.
cube('Fabric cubicle divider',(1.02,-.19,.63),(.055,2.34,1.25),fabric,upper,.015)
for y in [-1.31,.95]:cube('Partition edge trim',(1.02,y,.63),(.075,.03,1.28),chrome,upper,.004)
cube('Back half partition',(0,1.005,.64),(2.09,.05,1.27),green,upper)
cube('Upper shelf',(0,1.005,1.13),(1.76,.24,.035),wood,upper)
for j in range(8):
    x=-.73+j*.055
    cube('Archive binder on shelf',(x,1.005,1.27),(.041,.19,.245),green if j%3 else black,upper,.002)
    cube('Binder spine label',(x,.907,1.28),(.027,.002,.065),paper,upper,.001)
cube('Pinned calendar',(.36,.972,.79),(.25,.005,.30),paper,upper,.001)
text('Calendar heading','NOVEMBER',(.255,.964,.886),.021,black,upper)
for k in range(20):
    x=.26+(k%5)*.042;z=.84-(k//5)*.043
    text('Calendar date',str(k+1),(x,.962,z),.015,black,upper)
for j in range(3):cube('Pinned sticky note',(-.54+j*.095,.973,.82-j*.04),(.072,.004,.07),yellow,upper,.001)
cylinder('Plant pot',(.66,1,1.15),(.66,1,1.28),.075,ceramic,upper,.10)
cylinder('Plant soil',(.66,1,1.275),(.66,1,1.28),.09,earth,upper)
for j in range(8):
    a=j*math.tau/8;end=Vector((.66+math.cos(a)*.13,1+math.sin(a)*.13,1.40+random.random()*.14))
    curve('Plant stem',[(.66,1,1.27),end],.002,leaf,upper)
    leaf_obj=sphere('Plant leaf',end,(.035,.013,.075),leaf,upper);leaf_obj.rotation_euler=(.4,a,.3)
cube('Waste bin',(-.95,.34,.16),(.21,.22,.30),black,upper,.018)
for j in range(6):sphere('Crumpled paper',(-.95+random.uniform(-.05,.05),.34+random.uniform(-.05,.05),.25+random.uniform(-.02,.03)),(.035,.03,.025),paper,upper)
curve('Power supply cable',[(-.63,-1.02,.765),(-.67,-1.02,.08),(-.99,-1.02,.04),(-.99,.84,.04),(-.94,.95,.18)],.004,black,upper)
cube('Upper power socket',(-.95,.971,.18),(.08,.015,.08),paper,upper,.005)

# Preview room at measured office ceiling height (11.44 studs × .28 m).
ceiling=11.44*.28
upper.location=(0,0,ceiling);upper.rotation_euler=(math.pi,0,0)
cube('Lower office floor',(0,0,-.04),(10,8,.08),carpet)
cube('Lower back wall',(0,3.85,ceiling/2),(10,.10,ceiling),plaster)
cube('Lower left wall',(-4.9,0,ceiling/2),(.10,8,ceiling),plaster)
cube('Wall teal trim',(0,3.78,1.03),(10,.015,.045),green)
for ix in range(-8,9):
    for iy in range(-6,7):
        x=ix*.60;y=iy*.60
        if abs(x)<1.22 and abs(y)<1.65:continue
        tile=cube('Suspended ceiling tile',(x,y,ceiling+.04),(.587,.587,.045),panel,bevel=.001)
# Raised edge tiles expose a shallow, dark cavity. No hanging fragments cross the face.
for s in [-1,1]:
    cube('Dark ceiling cavity',(s*1.21,.25,ceiling+.04),(.13,2.72,.12),black)
    t=cube('Raised ceiling border tile',(s*1.36,.25,ceiling+.035),(.25,2.73,.035),panel);t.rotation_euler[1]=s*.14
cube('Rear dark ceiling gap',(0,-1.14,ceiling+.05),(2.5,.13,.10),black)
cube('Raised rear ceiling strip',(0,-1.27,ceiling+.04),(2.52,.22,.035),panel)
# A cleared tabletop is the first cue at eye level. The drawer and lamp switch stay usable.
cube('Lower empty desk / first anomaly clue',(0,.0,.733),(1.65,.76,.045),wood)
for x in [-.73,.73]:
    for y in [-.28,.28]:cube('Lower desk leg',(x,y,.35),(.04,.04,.70),chrome)
cube('Lower drawer pedestal',(.60,.0,.34),(.34,.56,.67),green)
cube('Lower linked drawer',(.60,-.293,.545),(.32,.024,.205),green)
cube('Lower linked handle',(.60,-.315,.575),(.13,.023,.014),chrome)
cube('Lower retained light switch',(-.70,-.30,.77),(.055,.04,.025),black)
for j,(x,y)in enumerate([(-2.65,1.4),(2.7,1.8)]):
    cube('Other ordinary desktop',(x,y,.74),(1.55,.72,.045),wood)
    for s in [-1,1]:cube('Other desk legs',(x+s*.65,y,.36),(.045,.6,.72),black)
    cube('Other ordinary monitor',(x,y+.14,1.04),(.48,.05,.30),black)
    cube('Office file cabinet',(x+1.0,y+.4,1.0),(.62,.52,2),green)
    for z in [.4,.8,1.2,1.6]:cube('Cabinet handle',(x+1.,y+.128,z),(.14,.03,.022),chrome)
for x,y in[(-2,-2),(2,-1.8),(0,2.5)]:
    cube('Ceiling fluorescent',(x,y,ceiling-.035),(.58,.58,.05),yellow)
    light('Room ceiling light',(x,y,ceiling-.08),70,.55,(1,.84,.59))
fill=light('Doorway soft fill',(0,-3.4,2),80,3,(.61,.74,1));fill.rotation_euler=(math.radians(70),0,0)

# Save rigged study before review; render cameras are honest player and inspection views.
camdata=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.clip_start=.015;camdata.clip_end=100
def camera(pos,target,lens=32):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=lens
shots=[
 ('01_first_clue', (0,3.2,1.55),(0,0,.85),32,'Первый признак: пустой стол на уровне глаз.'),
 ('02_player_looks_up',(.3,2.8,1.55),(0,.15,2.25),29,'Игрок поднимает взгляд: полный кабинет на потолке.'),
 ('03_three_quarter',(-2.5,1.6,1.6),(0,.2,2.35),36,'Сбоку видны полка, перегородка и опора на верхний ковролин.'),
 ('04_face',(.27,.75,1.6),(0,.13,2.00),75,'Крупный план лица с высоты игрока; реальная анатомия.'),
 ('05_hands',(-.5,1.4,1.85),(0,.55,2.44),65,'Кисти на клавиатуре и манжеты.'),
 ('06_upper_shelf',(-1.5,-1.1,2.7),(0,-.8,2.25),45,'Календарь, папки и растение в перевёрнутом кабинете.'),
 ('07_ceiling_edge',(-1.8,-1.5,2.1),(-1.1,0,3.18),50,'Приподнятые плиты и тёмная щель вокруг ковролина.'),
 ('08_monitor_plan',(.0,1.1,2.1),(.05,.94,2.13),65,'Монитор с планом; метки игроков будут связаны с игровой позицией.'),
 ('09_wardrobe',(-.8,.8,2.0),(0,.05,2.2),55,'Белая рубашка, ослабленный галстук, брюки и обувь.'),
 ('10_full_scene',(-3,3.4,1.6),(0,0,1.85),28,'Общий масштаб сцены и свободные проходы.')]
(OUT/'Shots.json').write_text(json.dumps([{'name':n,'camera':p,'target':t,'lens':l,'caption':c}for n,p,t,l,c in shots],ensure_ascii=False,indent=2))
camera(*shots[1][1:4]);scene.frame_start=1;scene.frame_end=480
for t,name in [(1,'Work'),(180,'Eyes notice player'),(204,'Typing eases out'),(228,'Head follows'),(360,'Player leaves'),(432,'Resume work')]:scene.timeline_markers.new(name,frame=t)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ceiling_Office_Character_Study_v18.blend'),compress=True)
print('STUDY_SAVED',flush=True)
args=sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else[]
selected=next((a.split('=',1)[1].split(',')for a in args if a.startswith('--shots=')),['02','04'])
for name,pos,target,lens,caption in shots:
    if name[:2]not in selected:continue
    camera(pos,target,lens);scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    print('RENDER_DONE',name,flush=True)
print('BUILD_COMPLETE',flush=True)
