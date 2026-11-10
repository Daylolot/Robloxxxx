"""Sample the authored contacts and arc paths against surveyed office solids."""
import collections
import json
import math
from pathlib import Path
import re
import struct
import sys

import numpy as np
from mathutils import Matrix

room,flight,code,destination=map(Path,sys.argv[sys.argv.index("--")+1:])
parts=[]
for row in json.loads(room.read_text()):
    pos=np.array(row["cf"][:3])
    if not (1008<pos[0]<1057 and .0<pos[1]<9.7 and 8<pos[2]<60):
        continue
    if row["transparency"]>=.38 or math.prod(row["size"])<.012:
        continue
    parts.append((row["group"]+"/"+row["name"],pos,np.array(row["cf"][3:]).reshape(3,3),np.array(row["size"])/2))
positions=np.array([v[1] for v in parts])
rotations=np.array([v[2] for v in parts])
sizes=np.array([v[3] for v in parts])
support_radius=np.linalg.norm(sizes,axis=1)

def ease(x):
    x=max(0,min(1,x))
    return x*x*(3-2*x)

def ranges(samples):
    return [{"at":round(age,3),"solid":name} for age,name in samples]

raw=[(float(w),float(l),bytes.fromhex(x)) for w,l,x in
     re.findall(r'width=([.\d]+),length=([.\d]+),data="([0-9a-f]+)"',flight.read_text())]
specs={int(i):(np.array([float(v) for v in spot.split(',')]),*[float(v) for v in fields.split(',')])
       for i,spot,fields in re.findall(r"\[(\d+)\] = \{Vector3.new\(([^)]+)\), ([^}]+)\}",code.read_text())}
arc_table=code.read_text().split("local arcRanks = {")[1].split("}")[0]
arcs={int(i):int(rank) for i,rank in re.findall(r"\[(\d+)\]=(\d+)",arc_table)}
results={}
for i in specs.keys() | arcs.keys():
    rank=arcs.get(i)
    if rank:
        begin,end=7.35+rank*.075,10.55+rank*.065+1.25
    else:
        at,start,hold,tilt,crease=specs[i]
        begin,end=start-1.30,start+hold+1.45
    width,length,payload=raw[i-1]
    track=np.array(list(struct.iter_unpack("<10h",payload)),dtype=float)
    track[:,:3]=track[:,:3]/1024+[1032,0,34]
    track[:,3:6]/=2048
    track[:,6:]/=4096
    issues=[]
    samples=range(math.floor(begin*48),math.ceil(end*48)+1)
    for frame in samples:
        age=frame/48
        sample=(age+1/30)*12
        left=min(int(sample),len(track)-2)
        base=track[left]+(track[left+1]-track[left])*(sample-left)
        pitch,roll,yaw,curl,bow,fold,twist=base[3:]
        orientation=(Matrix.Rotation(yaw,3,"Y") @ Matrix.Rotation(-roll,3,"Z")
                     @ Matrix.Rotation(pitch,3,"X") @ Matrix.Rotation(twist*.11+curl*.024,3,"Z")).to_quaternion()
        if rank:
            weight=ease((age-7.35-rank*.075)/1.35)*(1-ease((age-10.55-rank*.065)/1.25))
            a=(rank-5)*.17+(age-9.1)*.063
            spot=np.array([1033.3-6.7*(1-math.cos(a)),7.5-.85*abs(a),36+11.4*math.sin(a)])
            target=(Matrix.Rotation(.12*math.sin(age*5+rank),3,"X") @
                    Matrix.Rotation(a+1.15,3,"Y") @ Matrix.Rotation(.19,3,"Z")).to_quaternion()
            curl+=(.36+.19*math.sin(age*7+rank)-curl)*weight
        else:
            weight=ease((age-start+1.30)/1.30)*(1-ease((age-start-hold)/1.45))
            spot=at+[.20*ease((age-start)/hold) if i==28 else 0,0,0]
            target=(Matrix.Rotation(tilt+.027*math.sin(age*16),3,"X") @
                    Matrix.Rotation(math.pi if i==17 else 0,3,"Y")).to_quaternion()
            curl+=(crease+.13*math.sin(age*20)-curl)*weight
            bow+=(.24-bow)*weight
        pos=base[:3]+(spot-base[:3])*weight
        rotation=np.array(orientation.slerp(target,weight).to_matrix())
        y=[curl*.164*(k/4)**3+bow*.25*(k/4-.5)**2 for k in range(5)]
        chords=np.column_stack((np.zeros(4),np.diff(y),np.full(4,-length/4)))
        chords=chords/np.linalg.norm(chords,axis=1)[:,None]*length/4
        edge=np.array([0,curl*.164*.5**3+fold*.29/12,0])-chords[:2].sum(axis=0)
        tips=np.vstack((edge,edge+np.cumsum(chords,axis=0)))
        points=np.array([tip+[x,0,0] for tip in tips for x in (-width/2,0,width/2)])@rotation.T+pos
        near=np.linalg.norm(positions-pos,axis=1)<support_radius+.64
        ids=np.nonzero(near)[0]
        coords=np.einsum("pni,nij->pnj",points[:,None,:]-positions[ids],rotations[ids])
        for j in ids[np.any(np.all(np.abs(coords)<sizes[ids]-.008,axis=2),axis=0)]:
            issues.append((age,parts[j][0]))
    results[str(i)]={"kind":"arc" if rank else "contact","timeSamples":len(samples),
                     "pointsPerSample":15,"issues":ranges(issues),"count":len(issues)}
destination.write_text(json.dumps(results,indent=2)+"\n")
print({i:dict(collections.Counter(s["solid"] for s in v["issues"])) for i,v in results.items()})
