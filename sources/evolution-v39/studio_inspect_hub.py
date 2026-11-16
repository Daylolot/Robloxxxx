"""10-view inspection of FieldHub (lobby) models by path, one Play session (derived from studio_inspect_objects.py).
For each model: 8 views around (every 45 deg, camera 20 deg up), 1 from above (62 deg), 1 low. The camera is pulled in when
something blocks the way (raycast ignores the model itself); views closer than 45% of the wanted distance are skipped.
The character stays at the hub spawn (anchored); a lamp follows the camera so unlit corners stay readable.
Usage (repo venv): python sources/evolution-v39/studio_inspect_hub.py <out_dir> [Equipment/Hazmat_1,Equipment/MaskStation,...]
Frames: <out_dir>/<name_with_underscores>_v<k>.png, meta.json; then run make_sheets.py (kind = name) for contact sheets."""
import base64, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick

import os
ROOT = os.environ.get("INSPECT_ROOT", "FieldHub")   # workspace child the paths are relative to (FieldHub or OfficeMap)
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
PATHS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["Equipment/Hazmat_1", "Equipment/MaskStation", "Equipment/SuitRack", "Equipment/EquipmentBench"]
LUA_PATHS = "{" + ",".join(json.dumps(p) for p in PATHS) + "}"

LIST = """
local HttpService=game:GetService("HttpService")
local out={}
for _,path in ipairs(%(paths)s) do
  local inst=workspace.%(root)s
  for part in string.gmatch(path,"[^/]+") do inst=inst and inst:FindFirstChild(part) end
  if inst and inst:IsA("Model") then
    local cf,size=inst:GetBoundingBox()
    local piv=inst:GetPivot()
    out[#out+1]={name=path,cx=cf.Position.X,cy=cf.Position.Y,cz=cf.Position.Z,sx=size.X,sy=size.Y,sz=size.Z,lx=piv.LookVector.X,lz=piv.LookVector.Z}
  end
end
return HttpService:JSONEncode(out)
""" % dict(paths=LUA_PATHS, root=ROOT)

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

VIEW = """
local center=Vector3.new(%(cx)s,%(cy)s,%(cz)s)
local base=math.atan2(%(lx)s,%(lz)s)
local a=base+math.rad(%(az)s) local e=math.rad(%(el)s)
local dir=Vector3.new(math.sin(a)*math.cos(e),math.sin(e),math.cos(a)*math.cos(e))
local params=RaycastParams.new() params.FilterType=Enum.RaycastFilterType.Exclude
local inst=workspace.%(root)s
for part in string.gmatch(%(path)s,"[^/]+") do inst=inst:FindFirstChild(part) end
local ignore={inst}
if game.Players.LocalPlayer.Character then ignore[#ignore+1]=game.Players.LocalPlayer.Character end
params.FilterDescendantsInstances=ignore
local want=%(d)s
local hit=workspace:Raycast(center,dir*(want+0.6),params)
local use=want
if hit then use=math.max(0,(hit.Position-center).Magnitude-0.6) end
workspace:SetAttribute("InspectCF",CFrame.lookAt(center+dir*use,center))
return use/want
"""


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
            print([m["name"] for m in models], flush=True)
            for n, m in enumerate(models):
                radius = max(m["sx"], m["sy"], m["sz"])
                dist = max(4.0, radius * 1.7 + 2.0)
                # stream the area around the model: character above it (alive, anchored)
                park = max(m["cy"] + m["sy"] / 2 + 8, 14.0) if ROOT == "OfficeMap" else m["cy"] + m["sy"] / 2 + 8
                zone = 'p:SetAttribute("KonturZone","Office")' if ROOT == "OfficeMap" else ""
                run("Server", f'local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait() local c=p.Character or p.CharacterAdded:Wait() local hrp=c:FindFirstChild("HumanoidRootPart") if hrp then hrp.Anchored=true end {zone} c:PivotTo(CFrame.new({m["cx"]},{park},{m["cz"]})) return "ok"')
                time.sleep(2.0)
                views = []
                for k in range(10):
                    if k < 8:
                        az, el, d = k * 45, 20, dist
                    elif k == 8:
                        az, el, d = 20, 62, dist * 0.95
                    else:
                        az, el, d = 200, 4, dist * 0.8
                    lua = VIEW % dict(cx=m["cx"], cy=m["cy"], cz=m["cz"], lx=m["lx"], lz=m["lz"], az=az, el=el, d=d, path=json.dumps(m["name"]), root=ROOT)
                    ratio = float(run("Client", lua))
                    if ratio < 0.45:
                        views.append(None)
                        continue
                    time.sleep(0.5)
                    kind = m["name"].replace("/", "_")
                    fname = f"{kind}_{n}_v{k}.png"
                    for item in b.call("screen_capture", {"studio_id": studio, "capture_id": fname[:-4]})["content"]:
                        if item["type"] == "image":
                            (OUT / fname).write_bytes(base64.b64decode(item["data"]))
                    views.append({"file": fname, "az": az, "el": el, "ratio": round(ratio, 2)})
                meta.append({"kind": m["name"].replace("/", "_"), "n": n, "model": m, "views": views})
                print(m["name"], sum(1 for v in views if v), "views", flush=True)
                (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
        finally:
            try:
                b.call("start_stop_play", {"studio_id": studio, "is_start": False})
            except Exception:
                pass


main()
