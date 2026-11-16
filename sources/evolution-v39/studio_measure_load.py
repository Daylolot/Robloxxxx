"""Static load counters of the open map in Studio Play (server), for before/after tables.
Usage (repo root, repo venv): python sources/evolution-v39/studio_measure_load.py <out.json>"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
CODE = """
local office=workspace:WaitForChild("OfficeMap")
task.wait(4)
local n,cast,query,tiny,tinyCast,tinyQuery,shadowLights=0,0,0,0,0,0,0
for _,d in ipairs(office:GetDescendants()) do
  if d:IsA("BasePart") then n+=1
    local t=d.Size.Magnitude<0.6
    if d.CastShadow then cast+=1 end
    if d.CanQuery then query+=1 end
    if t then tiny+=1 if d.CastShadow then tinyCast+=1 end if d.CanQuery then tinyQuery+=1 end end
  elseif d:IsA("Light") and d.Shadows then shadowLights+=1 end
end
local S=game:GetService("Stats")
return game:GetService("HttpService"):JSONEncode({parts=n,castShadow=cast,canQuery=query,tiny=tiny,tinyCastShadow=tinyCast,tinyCanQuery=tinyQuery,
 shadowLights=shadowLights,trimShadowOff=workspace:GetAttribute("KonturTrimShadowOff"),trimQueryOff=workspace:GetAttribute("KonturTrimQueryOff"),
 trimSeconds=workspace:GetAttribute("KonturTrimSeconds"),
 hub=(function() local h=workspace:FindFirstChild("FieldHub") local c,q,t=0,0,0 if h then for _,d in ipairs(h:GetDescendants()) do if d:IsA("BasePart") then t+=1 if d.CastShadow then c+=1 end if d.CanQuery then q+=1 end end end end return {parts=t,castShadow=c,canQuery=q} end)(),memMB=math.round(S:GetTotalMemoryUsageMb()),instances=S.InstanceCount,primitives=S.PrimitivesCount})
"""
with StudioBridge() as b:
    for _ in range(80):
        s = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(s)
        if picked: studio = picked; break
        time.sleep(.5)
    for _ in range(12):  # a freshly started window is sometimes not connected yet
        r = b.call("start_stop_play", {"studio_id": studio, "is_start": True})
        if not r.get("isError"): break
        time.sleep(3)
        found = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(found)
        if picked: studio = picked
    for _ in range(30):  # wait until the Server datamodel exists (Play really started)
        state = b.call("get_studio_state", {"studio_id": studio})["content"][0]["text"]
        if "Server" in state: break
        time.sleep(2)
        if _ in (8, 16):
            b.call("start_stop_play", {"studio_id": studio, "is_start": True})
    try:
        time.sleep(12)
        r = b.call("execute_luau", {"studio_id": studio, "datamodel_type": "Server", "code": CODE})
        text = r["content"][0]["text"]; print(text)
        Path(sys.argv[1]).write_text(text)
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
