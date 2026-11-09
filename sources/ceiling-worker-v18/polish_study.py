from pathlib import Path
import bpy,json,math,random
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/CeilingWorker_2026-11-08/Revision18'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Ceiling_Office_Character_Study_v18.blend'))
scene=bpy.context.scene;upper=bpy.data.objects['UPPER_OFFICE / local inverted gravity'];worker=bpy.data.objects['WORKER / 33 years / seated anatomy']
rig=bpy.data.objects['OfficeWorker anatomical rig'];head=bpy.data.objects['Head attachment and gaze pivot']
skin=bpy.data.materials['Skin / restrained pores and subsurface'];cotton=bpy.data.materials['Ivory cotton / woven and creased']
for n in skin.node_tree.nodes:
    if n.type=='TEX_NOISE':n.inputs['Scale'].default_value=1100
    if n.type=='BUMP':n.inputs['Distance'].default_value=.0004;n.inputs['Strength'].default_value=.12

# Curl the distal fingers down to the key caps, keeping the original anatomical topology.
o=bpy.data.objects['Worker / face neck forearms and hands']
for side,s in [('L',1),('R',-1)]:
    wrist=Vector((s*.355,-.045,.94));direction=Vector((s*.060,-.010,-.18)).normalized()
    lateral=direction.cross(Vector((0,1,0))).normalized();pivot=wrist+direction*.105
    deformer=rig.pose.bones['hand.'+side].matrix@rig.data.bones['hand.'+side].matrix_local.inverted()
    bend_sign=1 if(deformer.to_3x3()@Vector((0,1,0))).z<0 else -1
    for v in o.data.vertices:
        if v.co.x*s<.31 or v.co.z>.91:continue
        length=(v.co-wrist).dot(direction)
        if length<.105:continue
        factor=min(1,(length-.105)/.09)
        v.co=pivot+Matrix.Rotation(bend_sign*.65*factor,3,lateral)@(v.co-pivot)
o.data.update()

def cube(name,pos,size,material,bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);ob=bpy.context.object;ob.name=name;ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(material)
    if bevel:
        b=ob.modifiers.new('Edge highlight','BEVEL');b.width=bevel;b.segments=2
        ob.modifiers.new('Face normals','WEIGHTED_NORMAL')
    return ob

# The sleeve-to-skin transition is a sewn cuff with thickness, never a raw cut mesh edge.
dg=bpy.context.evaluated_depsgraph_get()
mods=[m for m in o.modifiers if m.type!='ARMATURE'];flags=[m.show_viewport for m in mods]
for m in mods:m.show_viewport=False
bpy.context.view_layer.update();evaluated=o.evaluated_get(dg).to_mesh()
for s in [-1,1]:
    vv=[evaluated.vertices[v.index].co for v in o.data.vertices if v.co.x*s>.30 and 1.035<v.co.z<1.075]
    center=sum(vv,Vector())/len(vv)if vv else Vector((s*.18,-.43,.81))
    axis=Vector((-s*.10,-.23,.01)).normalized();right=axis.cross(Vector((0,0,1))).normalized();up=right.cross(axis).normalized()
    vertices=[];faces=[]
    for dist,radius in [(-.035,.049),(.035,.047),(.035,.039),(-.035,.041)]:
        for i in range(48):
            a=i*math.tau/48;vertices.append(center+axis*dist+right*math.cos(a)*radius+up*math.sin(a)*radius)
    for j in range(4):
        k=(j+1)%4
        for i in range(48):q=(i+1)%48;faces.append((j*48+i,j*48+q,k*48+q,k*48+i))
    me=bpy.data.meshes.new('Tailored cuff');me.from_pydata(vertices,[],faces);me.update();ob=bpy.data.objects.new('Worker / sewn sleeve cuff',me);scene.collection.objects.link(ob);ob.parent=worker;me.materials.append(cotton)
    for f in me.polygons:f.use_smooth=True
o.evaluated_get(dg).to_mesh_clear()
for m,flag in zip(mods,flags):m.show_viewport=flag

# Replace the dimensional placeholder by measured map geometry, preserving the character/set.
def belongs(ob,ancestor):
    while ob:
        if ob==ancestor:return True
        ob=ob.parent
    return False
for ob in list(scene.objects):
    if ob.type=='CAMERA' or belongs(ob,upper) or ob.hide_render:continue
    bpy.data.objects.remove(ob,do_unlink=True)
data=json.loads((ROOT/'work/ceiling_worker_v18/office_context.json').read_text())
M=Matrix(((-1,0,0),(0,0,1),(0,1,0)))
context=bpy.data.collections.new('Measured office context / v13 geometry retained in v17');scene.collection.children.link(context)
materials={};geometry={};removed=[]
def srgb(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def getmat(color,kind):
    key=(tuple(round(c,4)for c in color),kind)
    if key not in materials:
        m=bpy.data.materials.new('Map material '+str(len(materials)));m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=tuple(srgb(c)for c in color)+(1,);p.inputs['Roughness'].default_value=.75 if kind!='1088'else .95
        materials[key]=m
    return materials[key]
unitverts=[Vector((x,y,z))for x,y,z in [(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]]
boxfaces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(3,0,4,7)]
for row in data['parts']:
    cf=row['cf'];x,y,z=cf[:3];sz=row['size'];model=row['model']
    # Empty the chosen desk, remove its floor chair, keep the desk body and lamp switch.
    if model=='V09_0107_ErgoChair' or (1016.5<x<1023.5 and 45.3<z<48.8 and y>3.22 and model not in ['V09_0098_StraightDesk','V09_0440_SlimDeskLamp','OfficeMap','CENTER']):
        removed.append(row['path']);continue
    if model=='V09_0440_SlimDeskLamp' and row['name']not in ['Base','Foot','Switch']:continue
    position=Vector((-(x-1020)*.28,(z-44.35)*.28,y*.28));rotation=M@Matrix([cf[3:6],cf[6:9],cf[9:12]])
    # Cut the ceiling tiles into the exact opening around the carpet island.
    boxes=[(position,Vector(sz)*.28)]
    if row['name']=='TileCENTER':
        hx,hz=sz[0]*.14,sz[2]*.14;lx,rx=position.x-hx,position.x+hx;ly,ry=position.y-hz,position.y+hz
        a,b,c,d=-1.235,1.235,-1.59,1.09
        if rx>a and lx<b and ry>c and ly<d:
            boxes=[]
            for u,v,w,t in [(lx,min(rx,a),ly,ry),(max(lx,b),rx,ly,ry),(max(lx,a),min(rx,b),ly,min(ry,c)),(max(lx,a),min(rx,b),max(ly,d),ry)]:
                if v-u>.002 and t-w>.002:
                    # The map tile's local Y is vertical.
                    boxes.append((Vector(((u+v)/2,(w+t)/2,position.z)),Vector((v-u,sz[1]*.28,t-w))))
    material=getmat(row['color'],row['material'])
    for pos,size in boxes:
        vs,fs=geometry.setdefault(material,([],[]));start=len(vs)
        vs.extend(pos+rotation@Vector((v.x*size.x,v.y*size.y,v.z*size.z))for v in unitverts)
        fs.extend(tuple(start+i for i in face)for face in boxfaces)
for material,(vs,fs)in geometry.items():
    me=bpy.data.meshes.new(material.name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('Map context / '+material.name,me);context.objects.link(ob);me.materials.append(material)
floor=cube('Measured office floor',(0,0,.075*.28-.025),(12,15,.05),bpy.data.materials['Upper office / graphite olive carpet'],0)
for x,z in [(1016,51.33),(1032,51.33),(1016,34),(1032,34)]:
    ld=bpy.data.lights.new('Mapped fluorescent light','AREA');ld.energy=65;ld.shape='DISK';ld.size=.65;ld.color=(1,.80,.47)
    lo=bpy.data.objects.new('Mapped fluorescent light',ld);scene.collection.objects.link(lo);lo.location=(-(x-1020)*.28,(z-44.35)*.28,3.11)
ld=bpy.data.lights.new('Doorway bounce','AREA');ld.energy=45;ld.size=3;ld.color=(.64,.73,1)
lo=bpy.data.objects.new('Doorway bounce',ld);scene.collection.objects.link(lo);lo.location=(0,2.7,1.8);lo.rotation_euler=(math.radians(65),0,math.pi)
(OUT/'Map_Context_Check.json').write_text(json.dumps({'source':data['source'],'parts':len(data['parts']),'removed':removed,'sourceOriginStuds':[1020,11.44,44.35],'upperFootprintMetres':[2.35,2.55],'nativeMapModified':False,'approximation':'Context SpecialMesh silhouettes use measured bounding shapes; this is a Blender study, not a Studio screenshot.'},ensure_ascii=False,indent=2))

# Bake the attention example to ordinary keyframes: it remains portable when reopened.
pb=rig.pose.bones['head'];head_basis=pb.matrix.copy();attachment_basis=head.matrix_basis.copy();pivot=head_basis.translation.copy()
hand_bases={name:rig.pose.bones[name].matrix.copy()for name in ['hand.L','hand.R']}
def ease(v):v=max(0,min(1,v));return v*v*(3-2*v)
for frame in range(1,241):
    t=(frame-1)/24
    attention=ease((t-2)/1.4)*(1-ease((t-7)/2))
    yaw=math.radians(12)*math.sin(max(0,t-3)*.65)*attention
    pitch=math.radians(-27)*attention
    transform=Matrix.Translation(pivot)@Matrix.Rotation(yaw,4,'Z')@Matrix.Rotation(pitch,4,'X')@Matrix.Translation(-pivot)
    pb.matrix=transform@head_basis;pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
    head.matrix_basis=transform@attachment_basis;head.keyframe_insert('rotation_euler',frame=frame);head.keyframe_insert('location',frame=frame)
    for i,name in enumerate(hand_bases):
        hand=rig.pose.bones[name];delta=.002*math.sin(t*17+i*2)*(1-attention)
        hand.matrix=Matrix.Translation((0,0,delta))@hand_bases[name];hand.keyframe_insert('rotation_quaternion',frame=frame);hand.keyframe_insert('location',frame=frame)
scene.frame_start=1;scene.frame_end=240;scene.frame_set(120)
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
for f,name in [(1,'Typing'),(49,'Player has watched for 1.5 s'),(66,'Typing slows'),(83,'Head follows'),(169,'Player leaves'),(217,'Resume work')]:scene.timeline_markers.new(name,frame=f)
scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.cycles.samples=24
cam=scene.camera
cam.location=(.27,.75,1.6);cam.rotation_euler=(Vector((0,.13,2.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=75
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Ceiling_Office_Character_Study_v18.blend'),compress=True)
print('POLISHED_AND_BAKED',flush=True)
shots=json.loads((OUT/'Shots.json').read_text())
for shot in shots:
    if shot['name'].startswith('08_'):
        shot.update(camera=[.55,.35,2.05],target=[.48,.94,2.14],lens=65)
(OUT/'Shots.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2))
