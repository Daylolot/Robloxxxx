"""Access check: can a character walk from the office spawn to every chair and every interactive cabinet/sink?
Uses PathfindingService on the open Play server. Run on the baseline map and on the map with decor and compare the
failures: decor must not close any route. Usage (repo root, repo venv): python sources/evolution-v39/studio_verify_access.py <out.json>"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
CODE = """
local PS=game:GetService("PathfindingService")
local office=workspace.OfficeMap
local spawn=workspace:FindFirstChild("OfficeSpawn")
local start=(spawn and spawn.Position or Vector3.new(988,0.2,61))+Vector3.new(0,3,0)
local targets={}
local function add(kind,room,name,pos) targets[#targets+1]={kind=kind,room=room,name=name,pos=Vector3.new(pos.X,3.2,pos.Z)} end
for _,room in ipairs(office.Rooms:GetChildren()) do
  for _,d in ipairs(room:GetChildren()) do
    if d:IsA("Model") and (string.find(d.Name,"ErgoChair",1,true) or string.find(d.Name,"VisitorChair",1,true) or string.find(d.Name,"MeetingChair",1,true)) then add("chair",room.Name,d.Name,d:GetPivot().Position) end
  end
  for _,d in ipairs(room:GetDescendants()) do
    if d:IsA("ProximityPrompt") and d.Parent:IsA("BasePart") then add("prompt",room.Name,d.Parent.Parent.Name,d.Parent.Position) end
  end
end
local decor=office:FindFirstChild("KonturDecor")
if decor then
  for _,m in ipairs(decor:GetChildren()) do
    if m.Name=="KD_Workstation" then for _,c in ipairs(m:GetChildren()) do if string.find(c.Name,"ErgoChair",1,true) then add("chair","decor",c.Name,c:GetPivot().Position) end end end
  end
end
local ok,fail,failed=0,0,{}
local params={AgentRadius=1.5,AgentHeight=5,AgentCanJump=false,AgentCanClimb=false}
for i,t in ipairs(targets) do
  local path=PS:CreatePath(params)
  local good=pcall(function() path:ComputeAsync(start,t.pos) end) and path.Status==Enum.PathStatus.Success
  if good then ok+=1 else fail+=1 failed[#failed+1]=t.kind..":"..t.room..":"..t.name end
  if i%6==0 then task.wait() end
end
return game:GetService("HttpService"):JSONEncode({total=#targets,ok=ok,fail=fail,failed=failed})
"""
with StudioBridge() as b:
    for _ in range(80):
        s = studio_pick.mine(studio_pick.studios(b))
        if s: studio = s; break
        time.sleep(.5)
    studio = studio_pick.start_play(b, studio)
    time.sleep(16)
    try:
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": "Server", "code": CODE}}, timeout=400)
        text = r["content"][0]["text"]
        Path(sys.argv[1]).write_text(text)
        d = json.loads(text)
        print("total", d["total"], "ok", d["ok"], "fail", d["fail"]); print(d["failed"][:12])
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
