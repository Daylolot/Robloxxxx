"""10-view inspection of every decor model (KonturDecor/KD_*) in one Play session.

For each selected model: 8 views around it (every 45 degrees, camera 20 deg above the horizon), 1 view from above (60 deg)
and 1 low view (near the floor, looking slightly up). The camera is pulled in when a wall or other furniture is in the way
(raycast, the model itself is ignored); views that would end up closer than 45% of the wanted distance are skipped (a
picture frame cannot be seen from behind a wall).
Usage (repo venv): python sources/evolution-v39/studio_inspect_objects.py <out_dir> [kinds=all] [max_per_kind=6]
  kinds: comma list of KD_ names without the prefix, e.g. Bookcase,WaterCooler. Frames/boxes are sampled evenly.
Frames go to <out_dir>/<kind>_<n>_v<k>.png, meta to <out_dir>/meta.json. Then run make_sheets.py for contact sheets."""
import base64, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
KINDS = [] if len(sys.argv) < 3 or sys.argv[2] == "all" else sys.argv[2].split(",")
MAXPER = int(sys.argv[3]) if len(sys.argv) > 3 else 6

LIST = """
local HttpService=game:GetService("HttpService")
local f=workspace.OfficeMap:FindFirstChild("KonturDecor")
local out={}
if f then
  for _,m in ipairs(f:GetChildren()) do
    if m:IsA("Model") and m.Name:sub(1,3)=="KD_" then
      local cf,size=m:GetBoundingBox()
      local room=m:GetAttribute("Room")
      out[#out+1]={name=m.Name,id=m:GetFullName(),cx=cf.Position.X,cy=cf.Position.Y,cz=cf.Position.Z,sx=size.X,sy=size.Y,sz=size.Z,
        px=m:GetPivot().Position.X,pz=m:GetPivot().Position.Z,lx=m:GetPivot().LookVector.X,lz=m:GetPivot().LookVector.Z,room=room}
    end
  end
end
return HttpService:JSONEncode(out)
"""


BIND = """
local RunService=game:GetService("RunService")
pcall(function() RunService:UnbindFromRenderStep("KonturInspectCam") end)
workspace:SetAttribute("InspectCF",workspace.CurrentCamera.CFrame)
local lamp=Instance.new("Part") lamp.Name="KonturInspectLamp" lamp.Size=Vector3.new(.2,.2,.2) lamp.Transparency=1 lamp.Anchored=true lamp.CanCollide=false lamp.CanQuery=false lamp.CanTouch=false lamp.Parent=workspace
local light=Instance.new("PointLight") light.Range=34 light.Brightness=1.6 light.Shadows=false light.Color=Color3.fromRGB(255,244,225) light.Parent=lamp
RunService:BindToRenderStep("KonturInspectCam",Enum.RenderPriority.Last.Value+10,function()
  local cam=workspace.CurrentCamera
  cam.CameraType=Enum.CameraType.Scriptable cam.FieldOfView=58
  local cf=workspace:GetAttribute("InspectCF")
  if cf then cam.CFrame=cf lamp.CFrame=cf*CFrame.new(0.6,0.8,0) end
end)
return "bound"
"""

def sample(items, n):
    if len(items) <= n:
        return items
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


def main():
    with StudioBridge() as b:
        studio = None
        for _ in range(80):
            studio = studio_pick.mine(studio_pick.studios(b))
            if studio:
                break
            time.sleep(.5)
        studio = studio_pick.start_play(b, studio)

        def run(mode, code, timeout=120):
            r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": code}}, timeout=timeout)
            assert not r.get("isError"), r
            return r["content"][0]["text"]

        meta = []
        try:
            time.sleep(14)
            print(run("Client", BIND), flush=True)
            models = json.loads(run("Server", LIST))
            by_kind = {}
            for m in models:
                by_kind.setdefault(m["name"][3:], []).append(m)
            print({k: len(v) for k, v in by_kind.items()}, flush=True)
            for kind, items in by_kind.items():
                if KINDS and kind not in KINDS:
                    continue
                for n, m in enumerate(sample(items, MAXPER)):
                    cx, cy, cz = m["cx"], m["cy"], m["cz"]
                    radius = max(m["sx"], m["sy"], m["sz"])
                    dist = max(4.0, radius * 1.7 + 2.0)
                    # park the (alive, anchored) character above the ceiling over the model: streams the area, never blocks the view
                    run("Server", f'local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait() local c=p.Character or p.CharacterAdded:Wait() p:SetAttribute("KonturZone","Office") local hrp=c:FindFirstChild("HumanoidRootPart") if hrp then hrp.Anchored=true end c:PivotTo(CFrame.new({cx},14,{cz})) return "ok"')
                    time.sleep(2.0)
                    views = []
                    for k in range(10):
                        if k < 8:
                            az, el, d = k * 45, 20, dist
                        elif k == 8:
                            az, el, d = 20, 62, dist * 0.95
                        else:
                            az, el, d = 200, 4, dist * 0.8
                        lua = f"""
local center=Vector3.new({cx},{cy},{cz})
local base=math.atan2({m['lx']},{m['lz']})
local a=base+math.rad({az}) local e=math.rad({el})
local dir=Vector3.new(math.sin(a)*math.cos(e),math.sin(e),math.cos(a)*math.cos(e))
local params=RaycastParams.new() params.FilterType=Enum.RaycastFilterType.Exclude
local ignore={{}}
for _,mm in ipairs(workspace.OfficeMap.KonturDecor:GetChildren()) do if mm.Name=="{m['name']}" and (mm:GetPivot().Position-Vector3.new({m['px']},mm:GetPivot().Position.Y,{m['pz']})).Magnitude<0.05 then ignore[#ignore+1]=mm end end
if game.Players.LocalPlayer.Character then ignore[#ignore+1]=game.Players.LocalPlayer.Character end
params.FilterDescendantsInstances=ignore
local want={d}
local hit=workspace:Raycast(center,dir*(want+0.6),params)
local use=want
if hit then use=math.max(0,(hit.Position-center).Magnitude-0.6) end
workspace:SetAttribute("InspectCF",CFrame.lookAt(center+dir*use,center))
return use/want
"""
                        ratio = float(run("Client", lua))
                        if ratio < 0.45:
                            views.append(None)
                            continue
                        time.sleep(0.5)
                        fname = f"{kind}_{n}_v{k}.png"
                        for item in b.call("screen_capture", {"studio_id": studio, "capture_id": fname[:-4]})["content"]:
                            if item["type"] == "image":
                                (OUT / fname).write_bytes(base64.b64decode(item["data"]))
                        views.append({"file": fname, "az": az, "el": el, "ratio": round(ratio, 2)})
                    meta.append({"kind": kind, "n": n, "model": m, "views": views})
                    print(kind, n, sum(1 for v in views if v), "views", flush=True)
                    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
        finally:
            try:
                b.call("start_stop_play", {"studio_id": studio, "is_start": False})
            except Exception:
                pass


main()
