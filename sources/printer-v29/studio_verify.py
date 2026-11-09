"""Exercise the printer through a local Play session and save the three phases."""
import base64
import json
from pathlib import Path
import sys
import time

from studio_bridge import StudioBridge


out = Path(sys.argv[1])
with StudioBridge() as bridge:
    for _ in range(60):
        available = json.loads(bridge.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        if len(available) == 1:
            studio = available[0]["id"]
            break
        time.sleep(.5)
    else:
        raise RuntimeError("No single Studio instance connected")

    def call(tool, **kwargs):
        result = bridge.call(tool, {"studio_id": studio, **kwargs})
        assert not result.get("isError"), result
        return result["content"]

    def run(mode, code):
        value = json.loads(call("execute_luau", datamodel_type=mode, code=code)[0]["text"])
        print(mode, value, flush=True)
        return value

    def capture(name):
        for item in call("screen_capture", capture_id="ScreenCapture_1"):
            if item["type"] == "image":
                (out / f"{name}.png").write_bytes(base64.b64decode(item["data"]))
                return
        raise AssertionError("Studio did not return a screenshot")

    if "--playing" not in sys.argv:
        call("start_stop_play", is_start=True)
    try:
        report = {}
        server = """
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local char=p.Character or p.CharacterAdded:Wait()
local root=char:WaitForChild("HumanoidRootPart")
local office=workspace.OfficeMap
local state=office.AnomalyReportState
local printer=office.Rooms.CENTER.Printer
local qa=game.ServerStorage:WaitForChild("PrinterLocalQA",12)
assert(qa,"printer QA not loaded")
local function move(x,z)
    local at=Vector3.new(x,3.14,z)
    char:PivotTo(CFrame.lookAt(at,Vector3.new(1054,3.14,42)))
    root.AssemblyLinearVelocity=Vector3.zero
end
local function answer(choice)
    local start=office.Rooms.StartRoom
    local station=start.V09_0276_ReportStation
    local button=station["ReportButton_"..choice]
    local query=RaycastParams.new()
    query.FilterType=Enum.RaycastFilterType.Exclude
    query.FilterDescendantsInstances={char,station,start.V09_0278_ShiftStatusBoard}
    local pos=button.Position
    for i=0,15 do
        local a=i*math.pi/8
        local target=Vector3.new(pos.X+3*math.cos(a),3.14,pos.Z+3*math.sin(a))
        local eye=target+Vector3.yAxis*1.5
        if not workspace:Raycast(eye,pos-eye,query) then
            char:PivotTo(CFrame.new(target))
            qa:Invoke(p,choice)
            return
        end
    end
    error("no clear report position")
end
"""
        report["clear"] = run("Server", server+"""
p:SetAttribute("KonturZone","Office")
move(1050,42)
task.wait(.45)
return {level=state.Level.Value,mode=printer:GetAttribute("WarningPhase"),
    paper=printer:FindFirstChild("AnomalyPrintout")~=nil}
""")
        report["second"] = run("Server", server+"""
answer("Clear")
local deadline=os.clock()+8
while state.Level.Value~=2 or state.Phase.Value~="Active" do
    assert(os.clock()<deadline,state.ResultText.Value)
    task.wait(.1)
end
move(1050,42)
deadline=os.clock()+8
while printer:GetAttribute("WarningPhase")~="Ready" do
    assert(os.clock()<deadline,printer:GetAttribute("WarningPhase"))
    task.wait(.1)
end
return {mode=printer:GetAttribute("WarningPhase"),level=state.Level.Value,
    paper=printer.AnomalyPrintout.Ink.Enabled,notStarted=state:GetAttribute("PrinterPaperStartsAt")==nil,
    display=printer.Display.PrinterStatusDisplay.TextLabel.Text}
""")
        client = """
local p=game.Players.LocalPlayer
local office=workspace.OfficeMap
local state=office.AnomalyReportState
local c=workspace.CurrentCamera
local function view(position,target)
    c.CameraType=Enum.CameraType.Scriptable
    c.CFrame=CFrame.lookAt(position,target)
    c.Focus=CFrame.new(target)
end
local function papers()
    local scene=office:FindFirstChild("PrinterPaperFlight")
    return scene and scene:GetChildren() or {}
end
"""
        time.sleep(1.4)
        report["staged"] = run("Client", client+"""
view(Vector3.new(1051.15,4.81,41.1),Vector3.new(1053.65,4.01,42))
local scene=office:WaitForChild("PrinterPaperFlight",5)
return {parts=scene and #scene:GetChildren() or 0}
""")
        capture("01_warning")
        run("Client", client+"""
view(Vector3.new(1051.6,5.46,42.38),Vector3.new(1053.51,4.34,42.38))
return {camera=true}
""")
        capture("05_printout")
        report["started"] = run("Server", server+"""
local accepted=qa:Invoke(p,"Read")
local duplicate=qa:Invoke(p,"Read")
local at=state:GetAttribute("PrinterPaperStartsAt")
return {accepted=accepted,duplicate=duplicate,delay=at and at-workspace:GetServerTimeNow()}
""")
        report["time"] = run("Client", client+"""
local at=state:GetAttribute("PrinterPaperStartsAt")
local parts=papers()
local before=#parts
local sheet=office.PrinterPaperFlight.Sheet_01_4
local start=sheet.CFrame
while workspace:GetServerTimeNow()<at-.14 do task.wait(.025) end
local still=(sheet.Position-start.Position).Magnitude
while workspace:GetServerTimeNow()<at+.34 do task.wait(.025) end
local edge=(sheet.Position-start.Position).Magnitude
local low,high=0,0
for _,part in ipairs(papers()) do
    if part.Position.Y<4.5 then low+=1 else high+=1 end
end
view(Vector3.new(1051.55,4.08,40.2),Vector3.new(1053.4,3.77,41.76))
return {before=before,stirLow=low,stirHigh=high,still=still,edge=edge}
""")
        capture("02_stirring")
        report["lift"] = run("Client", client+"""
local at=state:GetAttribute("PrinterPaperStartsAt")
while workspace:GetServerTimeNow()<at+3.1 do task.wait(.03) end
view(Vector3.new(1050.1,5.05,41.8),Vector3.new(1033,6.65,38))
local count=0
for _,part in ipairs(papers()) do if part.Position.Y>5.2 then count+=1 end end
return {lifted=count}
""")
        capture("03_lifting")
        report["room"] = run("Client", client+"""
local at=state:GetAttribute("PrinterPaperStartsAt")
while workspace:GetServerTimeNow()<at+11.65 do task.wait(.05) end
view(Vector3.new(1050,5.65,44),Vector3.new(1027,6.75,33))
local lo=Vector3.new(math.huge,math.huge,math.huge)
local hi=-lo
local parts=papers()
for _,part in ipairs(parts) do
    local v=part.Position
    lo=Vector3.new(math.min(lo.X,v.X),math.min(lo.Y,v.Y),math.min(lo.Z,v.Z))
    hi=Vector3.new(math.max(hi.X,v.X),math.max(hi.Y,v.Y),math.max(hi.Z,v.Z))
end
local before=parts[1] and parts[1].Position
task.wait(.28)
local audio=0
local folder=office:FindFirstChild("PrinterPaperFlight")
if folder then
    for _,item in ipairs(folder:GetDescendants()) do
        if item:IsA("Sound") and item.IsLoaded then audio+=1 end
    end
end
return {count=#parts,x=hi.X-lo.X,z=hi.Z-lo.Z,low=lo.Y,high=hi.Y,
    drift=before and (parts[1].Position-before).Magnitude,loadedSounds=audio}
""")
        capture("04_room")
        report["continues"] = run("Client", client+"""
local at=state:GetAttribute("PrinterPaperStartsAt")
while workspace:GetServerTimeNow()<at+14.1 do task.wait(.05) end
local part=office.PrinterPaperFlight.Sheet_01_4
local start=part.Position
task.wait(.48)
return {drift=(part.Position-start).Magnitude,count=#papers()}
""")
        report["cleanup"] = run("Server", server+"""
answer("Anomaly")
return {correct=state.LastCorrect.Value,mode=printer:GetAttribute("WarningPhase"),
    inactive=state:GetAttribute("PrinterPaperStartsAt")==nil,
    noPrintout=printer:FindFirstChild("AnomalyPrintout")==nil}
""")
        report["clientCleanup"] = run("Client", client+"""
task.wait(.3)
return {parts=#papers()}
""")
        (out / "Studio_Check.json").write_text(json.dumps(report,indent=2)+"\n")
        assert report["clear"] == {"level":1,"mode":"Off","paper":False}, report
        assert report["second"]["paper"] and report["second"]["notStarted"], report
        assert report["second"]["display"]=="ЧИТАТЬ" and report["staged"]["parts"]==168, report
        assert report["started"]["accepted"] and not report["started"]["duplicate"] and report["started"]["delay"]>4.8, report
        assert report["time"]["before"]==168 and report["time"]["stirLow"]==168 and report["time"]["stirHigh"]==0, report
        assert report["time"]["still"]<.001 and report["time"]["edge"]>.01, report
        assert report["lift"]["lifted"]>30, report
        assert report["room"]["count"]==168 and report["room"]["x"]>33 and report["room"]["z"]>36, report
        assert 4.8<report["room"]["low"]<6 and report["room"]["high"]<8.7 and report["room"]["drift"]>.05, report
        assert report["cleanup"]["correct"] and report["cleanup"]["inactive"] and report["cleanup"]["noPrintout"], report
        assert report["continues"]["count"]==168 and report["continues"]["drift"]>.03, report
        assert report["clientCleanup"]["parts"]==0, report
    finally:
        call("start_stop_play", is_start=False)
