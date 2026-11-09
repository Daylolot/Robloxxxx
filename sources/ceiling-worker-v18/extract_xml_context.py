"""Read-only streaming geometry extraction; no Studio or extra map window needed."""
from pathlib import Path
from xml.parsers import expat
import json,math
ROOT=Path(__file__).resolve().parents[2]
src=ROOT/'outputs/CeilingWorker_2026-11-08/Kontur_Office_v13_Ceiling_Worker.rbxlx'
p=expat.ParserCreate();stack=[];depth=0;prop=None;leaf=None;rows=[]
def start(tag,a):
    global depth,prop,leaf
    depth+=1
    if tag=='Item':stack.append({'class':a.get('class'),'name':'?','props':{},'depth':depth})
    elif stack and 'name'in a and a['name']in ['Name','CFrame','Size','size','Color3uint8','Color','Transparency','Material','shape']:
        prop={'name':'Size'if a['name']=='size'else a['name'],'depth':depth,'text':[],'values':{}}
    elif prop:leaf=(tag,[])
def text(s):
    if leaf:leaf[1].append(s)
    elif prop:prop['text'].append(s)
def end(tag):
    global depth,prop,leaf
    if prop and depth==prop['depth']:
        value=prop['values']or ''.join(prop['text'])
        stack[-1]['props'][prop['name']]=value
        if prop['name']=='Name':stack[-1]['name']=value
        prop=None;leaf=None
    elif leaf and leaf[0]==tag:
        prop['values'][tag]=''.join(leaf[1]);leaf=None
    if tag=='Item':
        o=stack[-1];v=o['props']
        if o['class']in ['Part','MeshPart','WedgePart','UnionOperation']and'CFrame'in v and'Size'in v and any(a['name']=='OfficeMap'for a in stack):
            cf=v['CFrame'];size=v['Size']
            x,y,z=[float(cf[k])for k in ['X','Y','Z']];sz=[float(size[k])for k in ['X','Y','Z']]
            if 1008<=x<=1043 and 35<=z<=61 and -.5<=y<=12 and float(v.get('Transparency','0'))<.95 and math.sqrt(sum(a*a for a in sz))>=.19:
                models=[a['name']for a in stack[:-1]if a['class']=='Model']
                rgb=int(v.get('Color3uint8','4288914336'));color=[((rgb>>s)&255)/255 for s in [16,8,0]]
                rows.append({'name':o['name'],'model':models[-1]if models else'','size':sz,'cf':[x,y,z]+[float(cf['R'+str(i)+str(j)])for i in range(3)for j in range(3)],'color':color,'material':v.get('Material'),'shape':v.get('shape'),'path':'.'.join(a['name']for a in stack)})
        stack.pop()
    depth-=1
p.StartElementHandler=start;p.CharacterDataHandler=text;p.EndElementHandler=end
with src.open('rb')as f:
    for b in iter(lambda:f.read(4*1024*1024),b''):p.Parse(b,False)
p.Parse(b'',True)
out=ROOT/'work/ceiling_worker_v18/office_context.json'
out.write_text(json.dumps({'source':src.name,'note':'Geometry unchanged from v13 to v17; source name retained for provenance. SpecialMesh silhouettes are approximate bounding geometry in Blender.','parts':rows},ensure_ascii=False))
print(json.dumps({'parts':len(rows),'file':str(out),'bytes':out.stat().st_size}))
