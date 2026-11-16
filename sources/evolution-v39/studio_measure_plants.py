"""Plants/decor placed by the client runtime over time (Studio Play, client view). Compare builds.
Usage (repo root, repo venv): python sources/evolution-v39/studio_measure_plants.py <out.json>"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
CODE = """
local f=workspace.OfficeMap:FindFirstChild("KonturV36Plants")
local folders=0 for _,c in ipairs(workspace.OfficeMap:GetChildren()) do if c.Name=="KonturV36Plants" then folders+=1 end end
local char=game.Players.LocalPlayer.Character
local hp=char and char:FindFirstChildOfClass("Humanoid") and char.Humanoid.Health or -1
local n,names=0,{}
if f then for _,c in ipairs(f:GetChildren()) do n+=1 local k=c.Name:match("^(%a+)") names[k]=(names[k] or 0)+1 end end
return game:GetService("HttpService"):JSONEncode({placed=n,kinds=names,folders=folders,health=hp,t=os.clock()})
"""
with StudioBridge() as b:
    for _ in range(80):
        s = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(s)
        if picked: studio = picked; break
        time.sleep(.5)
    b.call("start_stop_play", {"studio_id": studio, "is_start": True})
    out = {}
    TELEPORT = """
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local c=p.Character or p.CharacterAdded:Wait()
local plant
for _,d in ipairs(workspace.OfficeMap:GetDescendants()) do if d:IsA("Model") and d.Name=="RubberPlant_NorthWest" then plant=d break end end
local pos=plant:GetBoundingBox().Position
c:PivotTo(CFrame.new(pos.X+3,3.2,pos.Z+3)) return "moved" """
    try:
        time.sleep(8)
        print(b.call("execute_luau", {"studio_id": studio, "datamodel_type": "Server", "code": TELEPORT})["content"][0]["text"])
        t0 = time.time()
        for at in (20, 40, 60, 80, 100, 120):
            time.sleep(max(0, at - (time.time() - t0)))
            r = b.call("execute_luau", {"studio_id": studio, "datamodel_type": "Client", "code": CODE})
            out[f"t{at}s"] = json.loads(r["content"][0]["text"]); print(at, out[f"t{at}s"], flush=True)
        console = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        out["console"] = [l for l in console.splitlines() if "KonturV36" in l or "rror" in l][-10:]
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
    Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=2))
