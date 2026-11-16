"""v39 mirror check: stand in front of a bathroom mirror, count reflected parts, capture a frame (map built with --qa).
Usage (repo root, repo venv): python sources/evolution-v39/studio_verify_mirror.py <out_dir>"""
import base64, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SERVER = """
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local char=p.Character or p.CharacterAdded:Wait()
p:SetAttribute("KonturZone","Office")
local room=workspace.OfficeMap.Rooms:WaitForChild("%s")
local panel
for _,d in ipairs(room:GetDescendants()) do if d.Name=="MirrorPanel" and d.Parent.Name=="%s" then panel=d break end end
local n=panel.CFrame.LookVector
local eye=panel.Position+n*3.2
char:PivotTo(CFrame.lookAt(Vector3.new(eye.X,3.14,eye.Z),Vector3.new(panel.Position.X,3.14,panel.Position.Z)))
return game:GetService("HttpService"):JSONEncode({eye={eye.X,eye.Y,eye.Z},panel={panel.Position.X,panel.Position.Y,panel.Position.Z}})
"""
CLIENT_AIM = """
local cam=workspace.CurrentCamera;cam.CameraType=Enum.CameraType.Scriptable
cam.CFrame=CFrame.lookAt(Vector3.new(%f,%f,%f),Vector3.new(%f,%f,%f)) return "ok" """
CLIENT_COUNT = """
local gui=game.Players.LocalPlayer.PlayerGui
local total,mirrors=0,0
local t=os.clock()
for _,g in ipairs(gui:GetChildren()) do
  if string.sub(g.Name,1,11)=="LiveMirror_" then
    local vp=g:FindFirstChild("Reflection",true)
    local world=vp and vp:FindFirstChild("ReflectedRoom")
    if world then mirrors+=1 local n=0 for _,d in ipairs(world:GetDescendants()) do if d:IsA("BasePart") then n+=1 end end total+=n end
  end
end
return game:GetService("HttpService"):JSONEncode({mirrorsBuilt=mirrors,reflectedParts=total})
"""
with StudioBridge() as b:
    for _ in range(80):
        s = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(s)
        if picked: studio = picked; break
        time.sleep(.5)
    else: raise RuntimeError("no studio")
    def run(mode, code):
        r = b.call("execute_luau", {"studio_id": studio, "datamodel_type": mode, "code": code}); assert not r.get("isError"), r
        return r["content"][0]["text"]
    b.call("start_stop_play", {"studio_id": studio, "is_start": True})
    out = {}
    try:
        time.sleep(10)
        for room, model in (("WOMEN", "V09_0316_Mirror"), ("MEN", "V09_0293_Mirror")):
            info = json.loads(run("Server", SERVER % (room, model)))
            time.sleep(4)
            e, pn = info["eye"], info["panel"]
            run("Client", CLIENT_AIM % (e[0], 5.0, e[2], pn[0], pn[1], pn[2]))
            time.sleep(3)
            t0 = time.time(); counts = json.loads(run("Client", CLIENT_COUNT)); counts["probe_s"] = round(time.time() - t0, 2)
            time.sleep(0.4)
            for item in b.call("screen_capture", {"studio_id": studio, "capture_id": f"mirror_{room}"})["content"]:
                if item["type"] == "image": (OUT / f"mirror_{room}.png").write_bytes(base64.b64decode(item["data"]))
            out[room] = counts; print(room, counts, flush=True)
        console = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        out["console_errors"] = [l for l in console.splitlines() if "rror" in l or "KONTUR" in l][-20:]
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
    (OUT / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2)); print("errors:", out["console_errors"])
