"""v39 check: cheap prop anomalies in one Studio client (map built with --qa).

For every scenario: force it with OfficeQANext, answer the clean round, wait for the anomaly round, check that the
scenario is active and the props really moved, take a close frame from eye level, answer, and check that every prop
returned to its start pose. Usage (repo root, repo venv): python sources/evolution-v39/studio_verify_props.py <out_dir> [Scenario ...]
studio_bridge.py lives one folder above the repo.
"""
import base64
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
SCENARIOS = {
    "ClockTilted": "WallClock",
    "ChairFacesWall": "ErgoChair",
    "MeetingChairsTurned": "MeetingChair",
    "SignBackwards": "WayfindingSigns",
    "PhotosBackwards": "PersonalPhotos",
    "RowChairsTurned": "ErgoChair",
    "RoomBlackout": "CeilingPanel",
    "PanelFlicker": "CeilingPanel",
    "NoticeBoardCrooked": "NoticeBoard",
    "ChairKnockedOver": "ErgoChair",
    "BinKnockedOver": "PedalBin",
    "PhoneOffHook": "Telephone",
    "MonitorHousingRed": "Monitor",
    "BoardMeetingTime": "NoticeBoard",
    "NewspaperWrongDay": "Newspaper",
    "SignNumberChanged": "WayfindingSigns",
    "KitchenSignWarning": "KitchenSigns",
    "BadgeNameChanged": "EmployeeBadges",
    "CalendarWrongMonth": "WallCalendar",
    "PlanningBoardNote": "PlanningBoard",
}
WANTED = sys.argv[2:] or list(SCENARIOS)

SERVER = """
local HttpService=game:GetService("HttpService")
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local char=p.Character or p.CharacterAdded:Wait()
local root=char:WaitForChild("HumanoidRootPart")
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
local function snap(suffix)
    local out={}
    for _,d in ipairs(office:GetDescendants()) do
        if d:IsA("Model") and (string.match(d.Name,"^V09_%d+_"..suffix.."$") or d.Name==suffix or (suffix=="Monitor" and string.match(d.Name,"Monitor$"))) then
            local cf=d:GetPivot()
            local bb=d:GetBoundingBox().Position
            out[d:GetFullName()]={math.round(cf.X*100)/100,math.round(cf.Y*100)/100,math.round(cf.Z*100)/100,
                math.round(cf.LookVector.X*100)/100,math.round(cf.LookVector.Z*100)/100,math.round(cf.UpVector.Y*100)/100,
                math.round(bb.X*100)/100,math.round(bb.Y*100)/100,math.round(bb.Z*100)/100,
                (function() local on=d:FindFirstChild("IsOn") if on then return on.Value and 1 or 0 end return -1 end)(),
                (function() local h=d:FindFirstChild("Housing") if h and h:IsA("BasePart") then return math.round((h.Color.R*3+h.Color.G*5+h.Color.B*7)*100) end return 0 end)(),
                (function() local hash=0 for _,c in ipairs(d:GetDescendants()) do if c:IsA("TextLabel") then for _,cp in utf8.codes(c.Text) do hash=(hash*31+cp)%1000003 end end end return hash end)()}
        end
    end
    return out
end
local function differs(a,b)
    local n=0
    for k,v in pairs(a) do
        local w=b[k]
        if w then for _,i in ipairs({1,2,3,4,5,6,7,8,9,10,11,12}) do if math.abs(v[i]-w[i])>0.02 then n+=1;break end end end
    end
    return n
end
local function centreDrift(a,b)
    local m=0
    for k,v in pairs(a) do local w=b[k]
        if w then local d=math.sqrt((v[7]-w[7])^2+(v[8]-w[8])^2+(v[9]-w[9])^2); if d>0.02 and differs({[k]=v},{[k]=w})>0 then m=math.max(m,d) end end end
    return math.round(m*100)/100
end
local function camFor(suffix,start,during)
    for k,v in pairs(during) do local s0=start[k]
        if s0 then for _,i in ipairs({1,2,3,4,5,6,7,8,9,10,11,12}) do if math.abs(v[i]-s0[i])>0.02 then
            local model=office
            for part in string.gmatch(k:gsub("^Workspace%.OfficeMap%.",""),"[^%.]+") do model=model:FindFirstChild(part) end
            local box,size=model:GetBoundingBox()
            local normal
            if size.X<=size.Y and size.X<=size.Z then normal=box.RightVector elseif size.Y<=size.Z then normal=box.UpVector else normal=box.LookVector end
            if suffix=="ErgoChair" or suffix=="MeetingChair" then normal=Vector3.new(2.5,1.2,2.5).Unit end
            if suffix=="CeilingPanel" then
                local c=box.Position
                return {pos={c.X,3.5,c.Z+7},look={c.X,8.2,c.Z-4},size={size.X,size.Y,size.Z}}
            end
            local dist=(suffix=="ErgoChair" or suffix=="MeetingChair") and 5 or 5.5
            -- choose the side with a clear line to the prop
            local best=box.Position+normal*dist
            local q=RaycastParams.new();q.FilterType=Enum.RaycastFilterType.Exclude;q.FilterDescendantsInstances={model}
            if workspace:Raycast(box.Position,normal*dist,q) then best=box.Position-normal*dist end
            return {pos={best.X,math.max(best.Y,2.4),best.Z},look={box.Position.X,box.Position.Y,box.Position.Z},size={size.X,size.Y,size.Z}}
        end end end
    end
end
local function newRound(from)
    local deadline=os.clock()+30
    repeat task.wait(.2) until (state.RoundId.Value>from and state.Phase.Value=="Active" and state.AcceptingReports.Value) or os.clock()>deadline
    return state.RoundId.Value>from
end
"""

STEP = """
local scenario="%(scenario)s"
local suffix="%(suffix)s"
ready()
local round0=state.RoundId.Value
local level0=state:GetAttribute("Level")
local offered=false
state:SetAttribute("OfficeQANext",scenario)
local start=snap(suffix)
nearButton("Clear"); qa:Invoke(p,"Clear")
local got=newRound(round0)
task.wait(1.5)
local active=game.ServerStorage:GetAttribute("KonturPackScenario") or state:GetAttribute("OfficeDetailScenario")
local during=snap(suffix)
local moved=differs(start,during)
local first
for k,v in pairs(during) do local s=start[k]; if s then for i=1,6 do if math.abs(v[i]-s[i])>0.02 then first=v;break end end end if first then break end end
return HttpService:JSONEncode({scenario=scenario,newRound=got,activeScenario=active,start=start,moved=moved,
    count=(function() local n=0 for _ in pairs(start) do n+=1 end return n end)(),pos=first,roundNow=state.RoundId.Value,
    centreDrift=centreDrift(start,during),cam=camFor(suffix,start,during)})
"""

with StudioBridge() as bridge:
    for _ in range(80):
        studios = json.loads(bridge.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(studios)
        if picked:
            studio = picked
            break
        time.sleep(.5)
    else:
        raise RuntimeError("No Studio available")

    def run(mode, code):
        result = bridge.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": code}}, timeout=240)
        assert not result.get("isError"), result
        return result["content"][0]["text"]

    def capture(name):
        time.sleep(0.3)
        for item in bridge.call("screen_capture", {"studio_id": studio, "capture_id": name})["content"]:
            if item["type"] == "image":
                (OUT / f"{name}.png").write_bytes(base64.b64decode(item["data"]))
                return True
        return False

    studio = studio_pick.start_play(bridge, studio)
    results = {}
    try:
        time.sleep(10)
        for scenario in WANTED:
            suffix = SCENARIOS[scenario]
            raw = run("Server", SERVER + STEP % {"scenario": scenario, "suffix": suffix})
            print(scenario, raw, flush=True)
            data = json.loads(raw)
            # the client must not learn the scenario: the replicated attribute stays empty for prop-module scenarios
            leak = run("Client", 'return tostring(workspace.OfficeMap.AnomalyReportState:GetAttribute("OfficeDetailScenario"))')
            data["clientSees"] = leak
            print(scenario, "client sees OfficeDetailScenario =", leak, flush=True)
            results[scenario] = data
            if scenario == "PanelFlicker":
                # flicker comes in bursts every ~2.5 s: sample the panels for 6 s and count state changes
                data["flicker"] = json.loads(run("Server", SERVER + """
local panels={}
for _,d in ipairs(office.Lighting:GetChildren()) do if string.match(d.Name,"^V09_%d+_CeilingPanel$") and d:FindFirstChild("IsOn") then panels[#panels+1]=d.IsOn end end
local last,changes,minOn=nil,0,#panels
local t0=os.clock()
while os.clock()-t0<6 do
    local on=0 for _,v in ipairs(panels) do if v.Value then on+=1 end end
    if last and on~=last then changes+=1 end
    last=on;minOn=math.min(minOn,on);task.wait(.06)
end
return HttpService:JSONEncode({panels=#panels,changes=changes,minOn=minOn,lastOn=last})
"""))
                print("flicker", data["flicker"], flush=True)
            cam = data.get("cam")
            # Teleporting the character next to tiny desk props (telephone, monitor) can wedge it inside furniture and stall
            # the server physics so the next call never returns: no frame for those, the numeric checks still run.
            if cam and suffix not in ("Telephone", "Monitor"):
                run("Server", SERVER + """
local p=game.Players:GetPlayers()[1];local c=p.Character
c:PivotTo(CFrame.new(%f,3.2,%f)) return "ok" """ % (cam["pos"][0], cam["pos"][2]))
                time.sleep(2.5)
                run("Client", """
local cam=workspace.CurrentCamera;cam.CameraType=Enum.CameraType.Scriptable
cam.CFrame=CFrame.lookAt(Vector3.new(%f,%f,%f),Vector3.new(%f,%f,%f)) return "ok" """
                    % (*cam["pos"], *cam["look"]))
                data["frame"] = capture(f"{scenario}_active")
            # answer wrongly (deterministic clean level 1): props must return to the poses recorded before the anomaly round
            start_json = json.dumps(data.pop("start"))
            run("Server", SERVER + """
-- A wrong answer sends the team back to the clean level 1: every prop must be back in its start pose.
nearButton("Clear") qa:Invoke(p,"Clear") task.wait(.3) return state.Phase.Value""")
            run("Server", SERVER + "local r=state.RoundId.Value-1 newRound(r) task.wait(1.5) return state.Phase.Value")
            back = run("Server", SERVER + """
local suffix="%s"
local start=HttpService:JSONDecode([==[%s]==])
local back=snap(suffix)
return HttpService:JSONEncode({scenarioAfter=game.ServerStorage:GetAttribute("KonturPackScenario") or state:GetAttribute("OfficeDetailScenario") or "Clear",propsNotRestored=differs(start,back)})
""" % (suffix, start_json))
            print(scenario, "after answer:", back, flush=True)
            data["afterAnswer"] = json.loads(back)
        console = bridge.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        errors = [line for line in console.splitlines() if "rror" in line or "KONTUR" in line][-25:]
        results["console_errors"] = errors
    finally:
        bridge.call("start_stop_play", {"studio_id": studio, "is_start": False})
    (OUT / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("done", OUT / "result.json")
