"""Play test of the final front: live flood in the real game loop, lethal-contact timing, console errors.
usage: python3 play_front.py <tag> <map-substring>"""
import sys,time,json; sys.path.insert(0,'.')
from drive import *
tag=sys.argv[1]; want=sys.argv[2]
INFO='''local shared=workspace.OfficeMap.BloodFloodState
local out={started=shared:GetAttribute("StartedAt"),now=workspace:GetServerTimeNow(),active=shared:GetAttribute("Active")}
for _,o in ipairs(shared.Regions:GetChildren()) do out[o.Name]=o:GetAttribute("start") end
return game:GetService("HttpService"):JSONEncode(out)'''
def start2(want,wait=14):
    s=S(want)
    st=[x for x in json.loads(s.b.call("list_roblox_studios",{})["content"][0]["text"])["studios"] if x["id"]==s.id][0]
    if st["mode"]=="Play":
        s.b.call("start_stop_play",{"studio_id":s.id,"is_start":False}); time.sleep(6)
    s.b.call("start_stop_play",{"studio_id":s.id,"is_start":True}); time.sleep(wait)
    return s
s=start2(want)
s.luau(SERVER_HELPERS+'''p:SetAttribute("KonturZone","Office") move(1018,3.2,33) task.wait(2) return 1''',"Server"); time.sleep(30)
print(s.luau(SERVER_HELPERS+'''p:SetAttribute("KonturZone","Office")
switch("Clear","BloodFlood") task.wait(1.5)
p:SetAttribute("KonturZone","Office")
local d=office.Doors.V09_0005_GlazedDoor8
d:SetAttribute("OpeningSerial",(d:GetAttribute("OpeningSerial") or 0)+1)
task.wait(1)
-- stand in the West corridor, far ahead of the front; remember when the character dies
char:PivotTo(CFrame.lookAt(Vector3.new(1004,3.2,62),Vector3.new(1004,3.2,40)))
root.Anchored=true
local hum=char:FindFirstChildOfClass("Humanoid")
hum.Died:Connect(function() state:SetAttribute("TestDeathAt",workspace:GetServerTimeNow()) end)
return "started "..tostring(office.BloodFloodState:GetAttribute("StartedAt"))''',"Server"),flush=True)
t0=time.time(); info={}
while True:
    try: info=json.loads(s.luau(INFO,"Client"))
    except Exception as e: print("info err",e); time.sleep(3); continue
    if "West" in info: break
    if time.time()-t0>90: break
    time.sleep(3)
st=info["started"]; W=info["West"]-st
print("West start",round(W,2),flush=True)
paths=[]; i=0
while True:
    info=json.loads(s.luau(INFO,"Client")); t=info["now"]-info["started"]
    if t>W+13: break
    if t>W-2:
        zf=max(4,min(70,4+6*(t-W)))
        cam=(1004,7.8,zf-9) if i%2==0 else (1004,3.4,min(zf+14,70))
        tgt=(1004,1.0,zf+4) if i%2==0 else (1004,2.2,zf)
        paths.append(view(s,f"front/{tag}_live{i:02d}.png",cam,tgt,pause=.5)); i+=1
    else: time.sleep(1)
res=s.luau(SERVER_HELPERS+'''local h=char:FindFirstChildOfClass("Humanoid")
return tostring(state:GetAttribute("TestDeathAt"))..","..tostring(h and h.Health)..","..tostring(office.BloodFloodState:GetAttribute("Active"))''',"Server")
print("death,health,active:",res)
death=res.split(",")[0]
if death not in("nil",""):
    d=float(death)-st; exp=W+(62-4)/6
    print("death at %.2f s after start; straight-front arrival at z=62 would be %.2f s; delta %+.2f s"%(d,exp,d-exp))
try:
    print("console:",s.b.call("get_console_output",{"studio_id":s.id})["content"][0]["text"][-1500:])
except Exception as e: print("console err",e)
stop(s)
if paths: sheet(paths[:12],3,640,360,f"front/{tag}_live_sheet.png")
print("done",len(paths))
