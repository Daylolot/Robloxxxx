"""Edit-mode front test: no Play, no server wait. Builds the liquid surface in Edit mode from either the v38 modules
(before) or the new blood-front modules (after), drives Surface:Update at frozen moments and photographs the front.
usage: python3 edit_front.py <tag> <map-substring> [variants=before,after] [shots=all|quick]"""
import sys,time,json; sys.path.insert(0,'.')
from sb import S
from PIL import Image
ROOT='/Users/nikitakorcagin/Desktop/Claude/Robloxxxx_work/Robloxxxx/sources/blood-front/'
tag=sys.argv[1]; want=sys.argv[2]
variants=(sys.argv[3] if len(sys.argv)>3 else "after").split(",")
quick=len(sys.argv)>4 and sys.argv[4]=="quick"
import re
def tweak(math,**kw):
    for name,val in kw.items():
        math,n=re.subn(r"local %s=[0-9.]+"%name,"local %s=%s"%(name,val),math,count=1); assert n==1,name
    return math
_after=(open(ROOT+'BloodLiquidMath.luau').read(),open(ROOT+'BloodLiquidSurface.luau').read())
SRC={"before":(open(ROOT+'original/BloodLiquidMath.luau').read(),open(ROOT+'original/BloodLiquidSurface.luau').read()),
     "after":_after,
     "r45":(tweak(_after[0],CHANNEL_RAMP=4.5),_after[1]),
     "r60":(tweak(_after[0],CHANNEL_RAMP=6.0),_after[1]),
     "A":(tweak(_after[0],CHANNEL_RAMP=4.5,BULGE_MAX=1.4,BULGE_FRAC=.4,LOBE_A=.3,LOBE_B=.15),_after[1]),
     "B":(tweak(_after[0],CHANNEL_RAMP=6.0,BULGE_MAX=2.0,BULGE_FRAC=.55,LOBE_A=.4,LOBE_B=.2),_after[1])}
SETUP='''local RS=game:GetService("ReplicatedStorage")
shared.FT=shared.FT or {}
local FT=shared.FT
if FT.surface then pcall(function()FT.surface:Destroy()end) FT.surface=nil end
local old=workspace:FindFirstChild("FrontTest") if old then old:Destroy() end
local function swap(name,src)
    local o=RS:FindFirstChild(name) if o then o:Destroy() end
    local n=Instance.new("ModuleScript");n.Name=name;n.Source=src;n.Parent=RS
end
swap("BloodLiquidMath",[==[__MATH__]==])
swap("BloodLiquidSurface",[==[__SURF__]==])
local Surface=require(RS.BloodLiquidSurface)
local config=table.clone(require(RS.BloodFloodConfig))
local Topo=require(RS.BloodFloodTopology)
local t0=Topo.New(config);t0:Start(0,0);t0:Step(100,function()return true end,function()end)
local defs={}
for id,r in pairs(t0.regions)do
    if id~="SourceEast"then
        r=table.clone(r)
        if id=="West"or id=="East"then r.z0=7.65 end
        if id=="SouthW"or id=="SouthE"then r.x0=1007.65;r.x1=1056.35 end
        if id=="Entry"then r.z1=.35 end
        if id=="NW"then r.z1=.35 end
        if id=="WEST"then r.x1=1000.35 end
        if id=="CENTER"then r.x0=1007.65 end
        if id=="EAST"then r.x0=1063.65 end
        if id=="MEN"or id=="WOMEN"then r.z0=67.65 end
        if id=="ReceptionEntry"then r.x1=1000.35 end
        table.insert(defs,r)
    end
end
local t1=Topo.New(config);t1:Start(1000,0);t1:Step(1100,function()return true end,function()end)
local regions={}
for id,r in pairs(t1.regions)do if id~="SourceEast"then table.insert(regions,table.clone(r))end end
local folder=Instance.new("Folder");folder.Name="FrontTest";folder.Parent=workspace
local appearance
for _,o in ipairs(RS.BloodFloodAssets:GetDescendants())do if o:IsA("MeshPart")and o.Name=="Blood_Body"then appearance=o:FindFirstChildOfClass("SurfaceAppearance")end end
local t=os.clock()
local surface=Surface.New(defs,folder,appearance,config)
FT.surface=surface;FT.regions=regions;FT.config=config
local out={_build=os.clock()-t,_points=#surface.points}
for _,r in ipairs(regions)do out[r.id]=r.start-1000 end
return game:GetService("HttpService"):JSONEncode(out)'''
FRAME='''local FT=shared.FT
FT.surface.lastUpdate=nil
FT.surface:Update(1000+__F__,1000,FT.regions)
local cam=workspace.CurrentCamera
cam.CFrame=CFrame.lookAt(Vector3.new(__CX__,__CY__,__CZ__),Vector3.new(__TX__,__TY__,__TZ__))
cam.Focus=cam.CFrame*CFrame.new(0,0,-20)
return 1'''
PERF='''local FT=shared.FT
local f=__F__
local N=30
local t=os.clock()
for i=1,N do FT.surface.lastUpdate=nil;FT.surface:Update(1000+f+i*.001,1000,FT.regions)end
return string.format("%.3f ms/update",(os.clock()-t)/N*1000)'''
s=S(want)
print("studio",s.id,flush=True)
def mode():
    st=[x for x in json.loads(s.b.call("list_roblox_studios",{})["content"][0]["text"])["studios"] if x["id"]==s.id]
    return st[0]["mode"] if st else None
def ensure_edit():
    for _ in range(6):
        m=mode()
        if m=="Edit": return True
        if m=="Play":
            print("studio is in Play (someone else started it): stopping",flush=True)
            s.b.call("start_stop_play",{"studio_id":s.id,"is_start":False}); time.sleep(6)
        else: time.sleep(3)
    return False
def luau(code):
    for attempt in range(3):
        ensure_edit()
        out=s.luau(code,"Edit")
        if "not available in Play mode" in out: continue
        return out
    return out
ensure_edit()
def shot(path,delay=1.6):
    for attempt in range(4):
        ensure_edit(); time.sleep(delay)
        try:
            r=s.shot(path)
        except Exception as e:
            print("shot error",e,flush=True); r=None
        if r: return r
    return None
allpaths={}
for v in variants:
    m,sf=SRC[v]
    out=luau(SETUP.replace("__MATH__",m).replace("__SURF__",sf))
    print(v,"setup:",out[:600],flush=True)
    R=json.loads(out)
    W=R["West"]; C=R.get("CENTER",W+8)
    shots=[]
    zs=(3.0,6.0) if quick else (3.0,6.0,9.0)
    for k,dz in enumerate(zs):
        f=W+dz; zf=4+6*dz
        shots+=[(f"w{k}_eye",f,(1004,3.4,zf+14),(1004,2.2,zf)),
                (f"w{k}_top",f,(1004,7.8,zf-9),(1004,1.0,zf+4)),
                (f"w{k}_side",f,(1007.2,4.5,zf+9),(1002,1.2,zf))]
    for k,dt in enumerate((1.0,3.0) if quick else (1.0,3.0,5.0)):
        shots+=[(f"c{k}_room",C+dt,(1030,7.5,22),(1014,1.0,33))]
    paths=[]
    time.sleep(6)
    for name,f,cam,tgt in shots:
        code=FRAME
        for key,val in (("__F__",f),("__CX__",cam[0]),("__CY__",cam[1]),("__CZ__",cam[2]),("__TX__",tgt[0]),("__TY__",tgt[1]),("__TZ__",tgt[2])):
            code=code.replace(key,str(val))
        luau(code); p=shot(f"front/{tag}_{v}_{name}.png")
        if p: paths.append(p)
    allpaths[v]=paths
    for name,f in (("corridor_front",W+4),("rooms_filling",R["WOMEN"]+4),("all_wet_steady",R["WOMEN"]+25)):
        print(v,"perf",name,luau(PERF.replace("__F__",str(f))),flush=True)
    cols=3; w,h=640,360
    rows=(len(paths)+cols-1)//cols
    sh=Image.new("RGB",(cols*w,rows*h))
    for i,p in enumerate(paths): sh.paste(Image.open(p).convert("RGB").resize((w,h)),((i%cols)*w,(i//cols)*h))
    sh.save(f"front/{tag}_{v}_sheet.png")
PERFV=[v for v in ("before","after") ]
import statistics
res={}
for rep in range(3):
    for v in PERFV:
        m,sf=SRC[v]; out=luau(SETUP.replace("__MATH__",m).replace("__SURF__",sf)); R=json.loads(out)
        for name,f in (("corridor_front",R["West"]+4),("steady",R["WOMEN"]+25)):
            val=float(luau(PERF.replace("__F__",str(f))).split()[0]); res.setdefault((v,name),[]).append(val)
for k,vals in sorted(res.items()): print("perfAB",k,"median %.2f"%statistics.median(vals),[round(x,2) for x in vals],flush=True)
s.close()
print("done")
