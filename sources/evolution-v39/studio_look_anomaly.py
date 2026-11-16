"""Frames of client-built anomalies (ceiling worker, blood, mirror) from eye level, in one Play session on a QA map.
Same scenario switching as studio_measure_anomaly_cost.py (SERVER header is reused from it). Usage (repo venv, PYTHONPATH = folder above the repo):
  python sources/evolution-v39/studio_look_anomaly.py <out_dir> [CeilingWorker BloodFlood Mirror]
Frames: <out_dir>/<scenario>_<k>.png"""
import base64, json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
WANTED = sys.argv[2:] or ["CeilingWorker", "BloodFlood", "Mirror"]
SERVER = re.search(r'SERVER = """(.*?)"""', (Path(__file__).parent / "studio_measure_anomaly_cost.py").read_text(), re.S).group(1)
VIEW = """
local c=workspace.CurrentCamera
local RunService=game:GetService("RunService")
pcall(function() RunService:UnbindFromRenderStep("KonturLookCam") end)
local pose=CFrame.lookAt(Vector3.new(%s,%s,%s),Vector3.new(%s,%s,%s))
c.FieldOfView=%s
RunService:BindToRenderStep("KonturLookCam",Enum.RenderPriority.Last.Value+10,function() c.CameraType=Enum.CameraType.Scriptable c.CFrame=pose end)
return "ok"
"""
# (eye x,y,z, target x,y,z, fov) per scenario and frame; the player stands at (1032, 34) like in the cost measurement
SHOTS = {
    "CeilingWorker": [(1030, 4.6, 36, 1020, 10.4, 45.7, 60), (1026, 5.0, 41, 1020, 10.2, 45.7, 45), (1022.5, 5.2, 43.5, 1020, 10.8, 45.7, 36)],
    "BloodFlood": [(1086, 4.6, -12, 1090, 1.2, -27, 70), (1078, 5.5, -2, 1090, 1.0, -27, 75)],
    "Mirror": [None],
}

with StudioBridge() as b:
    for _ in range(80):
        studio = studio_pick.mine(studio_pick.studios(b))
        if studio: break
        time.sleep(.5)
    studio = studio_pick.start_play(b, studio)
    def run(mode, code, timeout=120):
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": code}}, timeout=timeout)
        assert not r.get("isError"), r
        return r["content"][0]["text"]
    def shot(name):
        time.sleep(.4)
        for item in b.call("screen_capture", {"studio_id": studio, "capture_id": name})["content"]:
            if item["type"] == "image":
                (OUT / f"{name}.png").write_bytes(base64.b64decode(item["data"])); return
    try:
        time.sleep(10)
        in_forced = None
        for i, scenario in enumerate(WANTED):
            if in_forced != scenario:
                run("Server", SERVER + f"""ready() local r=state.RoundId.Value state:SetAttribute("OfficeQANext","{scenario}")
nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok" """)
            if scenario == "BloodFlood":
                run("Server", SERVER + "char:PivotTo(CFrame.new(1086,3.14,-12)) return 'ok'")
                time.sleep(14)
                info = run("Client", """
local f=workspace:FindFirstChild("BloodFloodVisuals")
if not f then return "no visuals" end
local mn,mx,n=Vector3.new(1e9,1e9,1e9),Vector3.new(-1e9,-1e9,-1e9),0
for _,d in ipairs(f:GetDescendants()) do if d:IsA("BasePart") then n+=1 mn=Vector3.new(math.min(mn.X,d.Position.X),math.min(mn.Y,d.Position.Y),math.min(mn.Z,d.Position.Z)) mx=Vector3.new(math.max(mx.X,d.Position.X),math.max(mx.Y,d.Position.Y),math.max(mx.Z,d.Position.Z)) end end
return n.." "..mn.X..","..mn.Y..","..mn.Z.." "..mx.X..","..mx.Y..","..mx.Z""")
                print("blood visuals:", info, flush=True)
                try:
                    n, a, bb = info.split(" ")
                    a = [float(x) for x in a.split(",")]; bb = [float(x) for x in bb.split(",")]
                    cx, cz = (a[0] + bb[0]) / 2, (a[2] + bb[2]) / 2
                    for k, (dx, dz, h) in enumerate([(0, 14, 6), (12, 0, 5), (0, 5, 4)]):
                        run("Server", SERVER + f"char:PivotTo(CFrame.new({cx},3.14,{cz + dz})) return 'ok'")
                        time.sleep(2.5)
                        run("Client", VIEW % (cx, h, cz + dz, cx, 0.5, cz, 70))
                        time.sleep(2); shot(f"{scenario}_c{k}")
                except Exception as e:
                    print("blood view failed", e, flush=True)
            elif scenario == "Mirror":
                spot = json.loads(run("Server", SERVER + "local a,b=mirrorSpot() return HttpService:JSONEncode({a.X,a.Z,b.X,b.Z})"))
                run("Server", SERVER + f"char:PivotTo(CFrame.lookAt(Vector3.new({spot[0]},3.14,{spot[1]}),Vector3.new({spot[2]},3.14,{spot[3]}))) return 'ok'")
                time.sleep(6)
                run("Client", VIEW % (spot[0], 4.6, spot[1], spot[2], 4.6, spot[3], 60))
                for k in range(4):
                    time.sleep(2.0); shot(f"{scenario}_m{k}")
            else:
                spot = (1086, -12) if scenario == "BloodFlood" else (1032, 34)
                run("Server", SERVER + f"char:PivotTo(CFrame.new({spot[0]},3.14,{spot[1]})) return 'ok'")
                time.sleep(4)
                for k, v in enumerate(SHOTS[scenario]):
                    run("Client", VIEW % (v[0], v[1], v[2], v[3], v[4], v[5], v[6]))
                    for t in range(4):
                        time.sleep(3.0); shot(f"{scenario}_{k}_{t}")
            run("Client", 'pcall(function() game:GetService("RunService"):UnbindFromRenderStep("KonturLookCam") end) return "ok"')
            nxt = WANTED[i + 1] if i + 1 < len(WANTED) else "None"
            res = run("Server", SERVER + f"""local r=state.RoundId.Value state:SetAttribute("OfficeQANext","{nxt}")
nearButton("Anomaly") qa:Invoke(p,"Anomaly") task.wait(.6) local text=state.ResultText.Value newRound(r) task.wait(1) return text""")
            in_forced = nxt if "НЕВЕРНО" not in res.upper() else None
        console = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        print("\n".join(l for l in console.splitlines() if "rror" in l or "KONTUR" in l)[-900:])
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
print("done")
