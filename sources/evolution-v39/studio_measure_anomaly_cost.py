"""Per-anomaly load counters (client view) in one Studio Play session on a QA map.
For each scenario: force it with OfficeQANext, enter its round, stand where the player sees it, wait, count objects,
subtract a clean-round baseline taken at the same spot. FPS is not measurable in the automation window (15 fps cap),
so the numbers are object counts, not frame times. Usage (repo root, repo venv):
  python sources/evolution-v39/studio_measure_anomaly_cost.py <out.json> [Scenario ...]"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick

ORDER = ["Printer", "Mirror", "CeilingWorker", "BloodFlood", "GreenVent", "WhisperDoor", "ArchiveWriting",
         "ArchiveArtSwap", "ArchiveCalendarShift", "WestPlanterColor", "ClockTilted", "ChairFacesWall",
         "RowChairsTurned", "MeetingChairsTurned", "SignBackwards", "PhotosBackwards", "RoomBlackout", "PanelFlicker"]
WANTED = sys.argv[2:] or ORDER
WAIT = {"Printer": 11, "Mirror": 6, "CeilingWorker": 8, "BloodFlood": 10, "GreenVent": 6, "WhisperDoor": 6}

SERVER = """
local HttpService=game:GetService("HttpService")
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local char=p.Character or p.CharacterAdded:Wait()
local office=workspace.OfficeMap
local state=office.AnomalyReportState
local qa=game.ServerStorage:WaitForChild("PrinterLocalQA",12)
p:SetAttribute("KonturZone","Office")
local function ready() repeat task.wait(.2) until state.Phase.Value=="Active" and state.AcceptingReports.Value end
local function nearButton(choice)
    local start=office.Rooms.StartRoom
    local station=start.V09_0276_ReportStation
    local button=station["ReportButton_"..choice]
    local q=RaycastParams.new();q.FilterType=Enum.RaycastFilterType.Exclude
    q.FilterDescendantsInstances={char,station,start.V09_0278_ShiftStatusBoard}
    local pos=button.Position
    for i=0,15 do
        local a=i*math.pi/8
        local at=Vector3.new(pos.X+3*math.cos(a),3.14,pos.Z+3*math.sin(a))
        local eye=at+Vector3.yAxis*1.5
        if not workspace:Raycast(eye,pos-eye,q) then char:PivotTo(CFrame.new(at));return end
    end
    error("No report line of sight")
end
local function newRound(from)
    local deadline=os.clock()+40
    repeat task.wait(.2) until (state.RoundId.Value>from and state.Phase.Value=="Active" and state.AcceptingReports.Value) or os.clock()>deadline
    return state.RoundId.Value>from
end
local function mirrorSpot()
    local room=office.Rooms.WOMEN
    for _,d in ipairs(room:GetDescendants()) do if d.Name=="MirrorPanel" and d.Parent.Name=="V09_0316_Mirror" then
        local e=d.Position+d.CFrame.LookVector*3.2
        return Vector3.new(e.X,3.14,e.Z),Vector3.new(d.Position.X,3.14,d.Position.Z)
    end end
end
"""
COUNT = """
local S=game:GetService("Stats")
local n={parts=0,lights=0,emitters=0,sounds=0,gui=0,viewports=0,casting=0,shadowLights=0}
for _,d in ipairs(workspace:GetDescendants()) do
  if d:IsA("BasePart") then n.parts+=1 if d.CastShadow then n.casting+=1 end
  elseif d:IsA("Light") then if d.Enabled then n.lights+=1 if d.Shadows then n.shadowLights+=1 end end
  elseif d:IsA("ParticleEmitter") then if d.Enabled then n.emitters+=1 end
  elseif d:IsA("Sound") then if d.IsPlaying then n.sounds+=1 end end
end
for _,d in ipairs(game.Players.LocalPlayer.PlayerGui:GetDescendants()) do
  if d:IsA("GuiObject") then n.gui+=1 end
  if d:IsA("ViewportFrame") then n.viewports+=1 end
end
n.instances=S.InstanceCount
return game:GetService("HttpService"):JSONEncode(n)
"""

with StudioBridge() as b:
    for _ in range(80):
        s = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(s)
        if picked: studio = picked; break
        time.sleep(.5)
    else: raise RuntimeError("no studio")
    def run(mode, code, timeout=90):
        global studio
        for attempt in range(8):
            r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": code}}, timeout=timeout)
            if r.get("isError") and "not connected" in r["content"][0]["text"]:
                time.sleep(3)  # the bridge loses a freshly started window: pick the id again and retry
                found = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
                picked = studio_pick.mine(found)
                if picked: studio = picked
                continue
            assert not r.get("isError"), r
            return r["content"][0]["text"]
        raise RuntimeError("Studio window not reachable")
    def where(x, z, lookx=None, lookz=None):
        look = f"CFrame.lookAt(Vector3.new({x},3.14,{z}),Vector3.new({lookx},3.14,{lookz}))" if lookx is not None else f"CFrame.new({x},3.14,{z})"
        run("Server", SERVER + f"char:PivotTo({look}) return 'ok'")
    out = {}
    b.call("start_stop_play", {"studio_id": studio, "is_start": True})
    try:
        time.sleep(10)
        # baselines (clean level-1 round)
        where(1032, 34); time.sleep(3); base_center = json.loads(run("Client", COUNT))
        spot = json.loads(run("Server", SERVER + "local a,b=mirrorSpot() return HttpService:JSONEncode({a.X,a.Z,b.X,b.Z})"))
        where(spot[0], spot[1], spot[2], spot[3]); time.sleep(3); base_mirror = json.loads(run("Client", COUNT))
        out["baseline"] = {"center": base_center, "mirror": base_mirror}; print("baseline", out["baseline"], flush=True)
        in_forced = None   # scenario whose round is currently active, or None when on a clean level-1 round
        for i, scenario in enumerate(WANTED):
            if in_forced != scenario:
                # clean level 1: set scenario and answer correctly to enter its round
                run("Server", SERVER + f"""ready() local r=state.RoundId.Value state:SetAttribute("OfficeQANext",{('nil' if scenario=='Printer' else repr(scenario).replace("'", '"'))})
nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok" """)
            if scenario == "Mirror": where(spot[0], spot[1], spot[2], spot[3])
            elif scenario == "Printer":
                # the paper only starts after the warning sheet is read (QA hook "Read"): stand at the printer, read, step back
                run("Server", SERVER + """
local printer=office.Rooms.CENTER.Printer
char:PivotTo(CFrame.lookAt(Vector3.new(1050,3.14,42),Vector3.new(1051,3.14,42)))
local deadline=os.clock()+10
repeat task.wait(.1) until printer:GetAttribute("WarningPhase")=="Ready" or os.clock()>deadline
local ok=qa:Invoke(p,"Read")
task.wait(.3)
char:PivotTo(CFrame.lookAt(Vector3.new(1033,3.14,41),Vector3.new(1033,3.14,40)))
return tostring(ok)""")
            else: where(1032, 34)
            time.sleep(WAIT.get(scenario, 5))
            c = json.loads(run("Client", COUNT))
            base = base_mirror if scenario == "Mirror" else base_center
            info = json.loads(run("Server", SERVER + """
local a={} for k,v in pairs(state:GetAttributes()) do if type(v)~="table" and type(v)~="userdata" then a[k]=v end end
return HttpService:JSONEncode({detail=state:GetAttribute("OfficeDetailScenario"),mirror=state:GetAttribute("MirrorAnomalyRound"),printer=state:GetAttribute("PrinterPaperPrimed")})"""))
            out[scenario] = {"counts": c, "delta": {k: c[k] - base[k] for k in c}, "state": info}
            print(scenario, out[scenario]["delta"], info, flush=True)
            # advance: next scenario forced, answer "Anomaly" (right when this round was an anomaly)
            nxt = WANTED[i + 1] if i + 1 < len(WANTED) else "None"
            res = run("Server", SERVER + f"""local r=state.RoundId.Value state:SetAttribute("OfficeQANext",{('nil' if nxt=='Printer' else '"'+nxt+'"')})
nearButton("Anomaly") qa:Invoke(p,"Anomaly") task.wait(.6) local text=state.ResultText.Value newRound(r) task.wait(1) return text""")
            in_forced = nxt if "НЕВЕРНО" not in res.upper() else None
            out[scenario]["answerResult"] = res
        console = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        out["console_errors"] = [l for l in console.splitlines() if "rror" in l or "KONTUR" in l][-15:]
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
        Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("done")
