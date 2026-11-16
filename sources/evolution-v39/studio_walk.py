"""Player walkthrough: eye-level frames along a route (hub, each room from its four corners, corridor) in one Play session of OUR window.
The character is parked above the ceiling at each viewpoint (streams the area, never blocks the view); the camera is held by BindToRenderStep.
Usage (repo venv): python sources/evolution-v39/studio_walk.py <out_dir> [wait_seconds_after_play=35]"""
import base64, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
WAIT = float(sys.argv[2]) if len(sys.argv) > 2 else 35
BIND = """
local RunService=game:GetService("RunService")
pcall(function() RunService:UnbindFromRenderStep("WalkCam") end)
workspace:SetAttribute("WalkCF",workspace.CurrentCamera.CFrame)
RunService:BindToRenderStep("WalkCam",Enum.RenderPriority.Last.Value+10,function()
  local cam=workspace.CurrentCamera cam.CameraType=Enum.CameraType.Scriptable cam.FieldOfView=70
  local cf=workspace:GetAttribute("WalkCF") if cf then cam.CFrame=cf end
end)
return "bound"
"""
ROOMS = """
local out={}
for _,room in ipairs(workspace.OfficeMap.Rooms:GetChildren()) do
  local lx,lz,hx,hz=math.huge,math.huge,-math.huge,-math.huge
  for _,d in ipairs(room:GetDescendants()) do if d:IsA("BasePart") and d.Transparency<1 then local p=d.Position lx=math.min(lx,p.X) hx=math.max(hx,p.X) lz=math.min(lz,p.Z) hz=math.max(hz,p.Z) end end
  if lx<hx then out[#out+1]={name=room.Name,lx=lx,hx=hx,lz=lz,hz=hz} end
end
return game:GetService("HttpService"):JSONEncode(out)
"""
with StudioBridge() as b:
    studio = None
    for _ in range(150):
        lst = studio_pick.studios(b)
        studio = studio_pick.mine(lst)
        if studio and any((x.get("file") or "").endswith("v42_QA.rbxl") for x in lst):
            break
        time.sleep(1)
    studio = studio_pick.start_play(b, studio)

    def run(mode, code, timeout=180):
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": code}}, timeout=timeout)
        return r["content"][0]["text"]

    meta = []
    try:
        time.sleep(WAIT)
        print(run("Client", BIND), flush=True)
        status = run("Server", 'local f=workspace.OfficeMap.KonturDecor local t,a=0,0 for _,m in ipairs(f:GetChildren()) do if m:GetAttribute("HeroKey") then t+=1 if m:GetAttribute("HeroApplied") then a+=1 end end end local s=0 for _,m in ipairs(workspace.FieldHub.Equipment:GetChildren()) do if m:GetAttribute("HubUpgraded") then s+=1 end end local c=0 for _,m in ipairs(workspace.FieldHub.Cases:GetChildren()) do if m:GetAttribute("HubUpgraded") then c+=1 end end return "decor="..#f:GetChildren().." hero="..a.."/"..t.." hubEquip="..s.." cases="..c')
        print("status:", status, flush=True)
        rooms = json.loads(run("Server", ROOMS))
        views = []
        for hx, hz, name in ((0, -25, "hub_spawn"),):
            for k, (dx, dz) in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
                views.append((f"{name}_{k}", hx, 4.6, hz, hx + dx * 10, 4.2, hz + dz * 10, "Hub"))
        views.append(("hub_suits", 0, 4.6, -4, 16, 4.6, 5, "Hub"))
        views.append(("hub_cases", -2, 4.6, -20, -14, 3.5, -28, "Hub"))
        views.append(("hub_door", 0, 4.6, 8, 0, 4.2, 40, "Hub"))
        for r in rooms:
            w, d = r["hx"] - r["lx"], r["hz"] - r["lz"]
            cx, cz = (r["lx"] + r["hx"]) / 2, (r["lz"] + r["hz"]) / 2
            for k, (fx, fz) in enumerate(((0.22, 0.22), (0.78, 0.22), (0.78, 0.78), (0.22, 0.78))):
                views.append((f"{r['name']}_{k}", r["lx"] + fx * w, 4.6, r["lz"] + fz * d, cx, 3.6, cz, "Office"))
        for name, ex, ey, ez, lx, ly, lz, zone in views:
            run("Server", f'local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait() local c=p.Character or p.CharacterAdded:Wait() local hrp=c:FindFirstChild("HumanoidRootPart") if hrp then hrp.Anchored=true end p:SetAttribute("KonturZone","{zone}") c:PivotTo(CFrame.new({ex},14,{ez})) return "ok"')
            time.sleep(2.2)
            run("Client", f'workspace:SetAttribute("WalkCF",CFrame.lookAt(Vector3.new({ex},{ey},{ez}),Vector3.new({lx},{ly},{lz}))) return "cam"')
            time.sleep(0.9)
            for item in b.call("screen_capture", {"studio_id": studio, "capture_id": name})["content"]:
                if item["type"] == "image":
                    (OUT / f"{name}.png").write_bytes(base64.b64decode(item["data"]))
            meta.append(name)
            print(name, flush=True)
        con = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        warns = [l[:220] for l in con.splitlines() if "KONTUR" in l or "rror" in l]
        (OUT / "console.txt").write_text("\n".join(warns[-40:]))
        print("console:", warns[-6:])
    finally:
        try:
            b.call("start_stop_play", {"studio_id": studio, "is_start": False})
        except Exception:
            pass
