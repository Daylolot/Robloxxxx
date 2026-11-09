"""One Studio client, six rounds, gameplay reset and rendered checkpoints."""
import base64
import json
from pathlib import Path
import sys
import time

from studio_bridge import StudioBridge

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
with StudioBridge() as bridge:
    for _ in range(65):
        studios=json.loads(bridge.call("list_roblox_studios",{})["content"][0]["text"])["studios"]
        if len(studios)==1:
            studio=studios[0]["id"]
            break
        time.sleep(.5)
    else:
        raise RuntimeError("No Studio available")

    def call(tool, **kwargs):
        result=bridge.call(tool, {"studio_id":studio, **kwargs})
        assert not result.get("isError"), result
        return result["content"]

    def run(mode, code):
        raw=call("execute_luau",datamodel_type=mode,code=code)[0]["text"]
        value=json.loads(raw)
        print(mode,value,flush=True)
        return value

    def capture(name):
        time.sleep(.20)
        for item in call("screen_capture",capture_id=name):
            if item["type"]=="image":
                (out/f"{name}.png").write_bytes(base64.b64decode(item["data"]))
                return
        raise AssertionError("No screenshot")

    server="""
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local char=p.Character or p.CharacterAdded:Wait()
local root=char:WaitForChild("HumanoidRootPart")
local office=workspace.OfficeMap
local state=office.AnomalyReportState
local printer=office.Rooms.CENTER.Printer
local qa=game.ServerStorage:WaitForChild("PrinterLocalQA",12)
local function move(x,z,dx,dz)
    local at=Vector3.new(x,3.14,z)
    char:PivotTo(CFrame.lookAt(at,at+Vector3.new(dx or 1,0,dz or 0)))
    root.AssemblyLinearVelocity=Vector3.zero
end
local function answer(choice)
    local start=office.Rooms.StartRoom
    local station=start.V09_0276_ReportStation
    local button=station["ReportButton_"..choice]
    local q=RaycastParams.new()
    q.FilterType=Enum.RaycastFilterType.Exclude
    q.FilterDescendantsInstances={char,station,start.V09_0278_ShiftStatusBoard}
    local pos=button.Position
    for i=0,15 do
        local a=i*math.pi/8
        local at=Vector3.new(pos.X+3*math.cos(a),3.14,pos.Z+3*math.sin(a))
        local eye=at+Vector3.yAxis*1.5
        if not workspace:Raycast(eye,pos-eye,q) then
            char:PivotTo(CFrame.new(at))
            qa:Invoke(p,choice)
            return
        end
    end
    error("No report line of sight")
end
local function switch(choice,scenario)
    local previous=state.RoundId.Value
    state:SetAttribute("OfficeQANext",scenario)
    answer(choice)
    local deadline=os.clock()+10
    repeat task.wait(.1) until (state.RoundId.Value>previous and state.Phase.Value=="Active") or os.clock()>deadline
    assert(state.RoundId.Value>previous and state:GetAttribute("OfficeDetailScenario")==scenario,state.ResultText.Value)
end
"""
    client="""
local p=game.Players.LocalPlayer
local office=workspace.OfficeMap
local state=office.AnomalyReportState
local function view(x,y,z,tx,ty,tz)
    local c=workspace.CurrentCamera
    c.CameraType=Enum.CameraType.Scriptable
    c.CFrame=CFrame.lookAt(Vector3.new(x,y,z),Vector3.new(tx,ty,tz))
    c.Focus=CFrame.new(tx,ty,tz)
    local service=game:GetService("RunService")
    service:UnbindFromRenderStep("OfficeQACamera")
    local pose=c.CFrame
    service:BindToRenderStep("OfficeQACamera",Enum.RenderPriority.Last.Value,function()
        c.CameraType=Enum.CameraType.Scriptable
        c.CFrame=pose
        c.Focus=CFrame.new(tx,ty,tz)
    end)
end
local function waitAge(age)
    local starts=state:GetAttribute("PrinterPaperStartsAt")
    while workspace:GetServerTimeNow()<starts+age do task.wait(.025) end
end
local function detail() return office:WaitForChild("OfficeDetailPresentation",4) end
"""
    def s(code):
        return run("Server", server+code)
    def c(code):
        return run("Client", client+code)

    call("start_stop_play",is_start=True)
    try:
        report={}
        report["start"]=s('''
p:SetAttribute("KonturZone","Office")
assert(state.Level.Value==1 and state:GetAttribute("OfficeDetailScenario")=="Clear")
assert(office.MaintenanceVent and not office.Rooms.NW:FindFirstChild("BloodMessage"))
local nw=office.Rooms.NW
local plant=office.Rooms.WEST.V09_0348_WallPlanter
local function checkPlant()
    local n=0
    for _,item in ipairs(plant:GetDescendants()) do
        if item:IsA("BasePart") and item.Color.R>item.Color.G*1.5 then n+=1 end
    end
    return n
end
return {art=nw.V09_0340_WorldTrade:GetPivot().Position.Z,calendar=nw.V09_0465_WallCalendar:GetPivot().Position.X,
    planter=checkPlant()}
''')
        report["print"]=s('''
switch("Clear","Printer")
move(1050,42)
local deadline=os.clock()+8
repeat task.wait(.1) until printer:GetAttribute("WarningPhase")=="Ready" or os.clock()>deadline
assert(printer:GetAttribute("WarningPhase")=="Ready")
assert(qa:Invoke(p,"Read"))
local delay=state:GetAttribute("PrinterPaperStartsAt")-workspace:GetServerTimeNow()
move(1033,38,0,-1)
return {delay=delay}
''')
        report["monitor"]=c('''
view(1023.5,5.8,48,1020.36,5.335,47.60)
waitAge(4.95)
local leaf=office.PrinterPaperFlight.Sheet_17_2
return {height=leaf.Position.Y,near=(leaf.Position-Vector3.new(1020.36,5.335,47.60)).Magnitude}
''')
        report["receipt"]=c('''
view(1033,5.25,38,1033,5.25,29)
waitAge(5.85)
local folder=office.PrinterPaperFlight
local receipt=folder.ReceiptEncounter
return {stage=receipt:GetAttribute("Phase"),count=#folder:GetChildren()-1,
    raised=receipt.ReceiptHalf1.Transparency<.05}
''')
        capture("01_receipt")
        time.sleep(.04)
        report["contact"]=c('''
local p=office.PrinterPaperFlight.Sheet_28_2
view(1024.2,4.85,45.5,1022.23,3.37,46.05)
return {height=p.Position.Y}
''')
        capture("02_contact")
        report["arc"]=c('''
waitAge(9.35)
view(1030.5,5.23,48,1032,7.05,33)
local root=office.PrinterPaperFlight
local bands=0
for _,i in ipairs({3,6,12,16,22,31,39,46,55}) do
    local v=root[("Sheet_%02d_2"):format(i)].Position
    if math.abs(v.X-1033.3)<2 and v.Y>6.8 then bands+=1 end
end
return {bands=bands,receipt=root.ReceiptEncounter:GetAttribute("Phase")}
''')
        capture("03_arc")
        report["floor"]=c('''
waitAge(10.48)
local leaf=office.PrinterPaperFlight.Sheet_43_2
view(1045.4,2.15,40,1048.1,.68,40)
return {height=leaf.Position.Y,near=(leaf.Position-Vector3.new(1048.1,.68,40)).Magnitude}
''')
        capture("11_floor_sheet")
        report["archive"]=s('''
switch("Anomaly","ArchiveWriting")
task.wait(.6)
move(1027.35,-17.1,1,0)
return {scenario=state:GetAttribute("OfficeDetailScenario")}
''')
        report["archiveGlance"]=c('''
view(1027.35,5.2,-17.1,1016,4.7,-16.2)
task.wait(1.35)
view(1027.35,5.20,-17.1,1031.785,5.36,-17.1)
task.wait(.26)
view(1027.35,5.2,-17.1,1016,4.7,-16.2)
task.wait(.59)
return {stage=detail().WallInk:GetAttribute("Stage")}
''')
        report["archiveRead"]=c('''
view(1027.35,5.20,-17.1,1031.785,5.36,-17.1)
task.wait(1.5)
local ink=detail().WallInk
local q=RaycastParams.new()
q.FilterType=Enum.RaycastFilterType.Exclude
q.FilterDescendantsInstances={p.Character,detail()}
local cam=workspace.CurrentCamera.CFrame
local hit=workspace:Raycast(cam.Position,ink.Position-cam.Position,q)
return {stage=ink:GetAttribute("Stage"),legacy=office:FindFirstChild("PrinterPaperFlight")~=nil,
    head=tostring(p.Character.Head.Position),hit=hit and hit.Instance:GetFullName() or "none"}
''')
        capture("04_archive_read")
        report["archiveTurn"]=c('''
view(1027.35,5.2,-17.1,1016,4.7,-16.2)
task.wait(.66)
local changed=detail().WallInk:GetAttribute("Stage")
view(1027.35,5.20,-17.1,1031.785,5.36,-17.1)
task.wait(1.28)
return {stage=changed}
''')
        capture("05_archive_return")
        report["art"]=s('''
switch("Anomaly","ArchiveArtSwap")
move(1024,-18,1,0)
local a=office.Rooms.NW
return {first=a.V09_0340_WorldTrade:GetPivot().Position.Z,second=a.V09_0341_GrowthTechnology:GetPivot().Position.Z}
''')
        c('view(1024,5.4,-18,1031.65,7.9,-17.5); return true')
        capture("06_static_art")
        report["calendar"]=s('''
switch("Anomaly","ArchiveCalendarShift")
local a=office.Rooms.NW
return {artRestored=a.V09_0340_WorldTrade:GetPivot().Position.Z,calendar=a.V09_0465_WallCalendar:GetPivot().Position.X}
''')
        c('view(1010.8,5.4,-8,1010.45,6.2,-.3); return true')
        capture("07_static_calendar")
        report["plant"]=s('''
switch("Anomaly","WestPlanterColor")
local n=0
for _,item in ipairs(office.Rooms.WEST.V09_0348_WallPlanter:GetDescendants()) do
    if item:IsA("BasePart") and item.Color.R>item.Color.G*1.5 then n+=1 end
end
return {red=n,calendarRestored=office.Rooms.NW.V09_0465_WallCalendar:GetPivot().Position.X}
''')
        c('view(996.5,5.1,51.5,999.43,4.32,47.97); return true')
        capture("08_static_plant")
        report["vent"]=s('''
switch("Anomaly","GreenVent")
move(1004,45.8,-1,0)
task.wait(.95)
local hatch=office.MaintenanceVent.HingedLouvers:GetPivot()
local q=RaycastParams.new()
q.FilterType=Enum.RaycastFilterType.Exclude
q.FilterDescendantsInstances={char}
local along=workspace:Raycast(Vector3.new(1004,3,42),Vector3.new(0,0,8),q)
return {hinge=hatch.RightVector.X,passable=along==nil}
''')
        report["ventClient"]=c('''
view(1005.9,5.35,49.45,1000.51,4.0,45.9)
task.wait(2.35)
local f=detail()
return {stream=f.VentVaporOrigin.SeepOnWall.Transparency.Keypoints[1].Value,drops=#f:GetChildren(),smoke=f.VentVaporOrigin:FindFirstChild("GreenJet",true).Rate}
''')
        capture("09_vent_wide")
        c('view(1003.35,4.92,47.85,1000.54,4.5,45.8); return true')
        capture("10_vent_close")
        report["reset"]=s('''
state:SetAttribute("OfficeQANext","ArchiveWriting")
answer("Clear")
local deadline=os.clock()+9
repeat task.wait(.1) until state.Level.Value==1 and state.Phase.Value=="Active" or os.clock()>deadline
local a=office.Rooms.NW
local plant=0
for _,item in ipairs(office.Rooms.WEST.V09_0348_WallPlanter:GetDescendants()) do
    if item:IsA("BasePart") and item.Color.R>item.Color.G*1.5 then plant+=1 end
end
return {level=state.Level.Value,scenario=state:GetAttribute("OfficeDetailScenario"),
    hinge=office.MaintenanceVent.HingedLouvers:GetPivot().RightVector.X,plant=plant,
    art=a.V09_0340_WorldTrade:GetPivot().Position.Z,calendar=a.V09_0465_WallCalendar:GetPivot().Position.X}
''')
        report["clientReset"]=c('return {exists=office:FindFirstChild("OfficeDetailPresentation")~=nil}')
        (out/"Studio_Check.json").write_text(json.dumps(report,indent=2)+"\n")
        assert report["print"]["delay"]>4.8
        assert report["receipt"]=={"stage":"Read","count":240,"raised":True},report
        assert 3.3<report["contact"]["height"]<3.85
        assert report["monitor"]["near"]<.24 and report["floor"]["near"]<.24
        assert report["arc"]["bands"]==9
        assert report["archiveGlance"]["stage"]=="Hidden"
        assert report["archiveRead"]["stage"]=="Read" and not report["archiveRead"]["legacy"]
        assert report["archiveTurn"]["stage"]=="Changed"
        assert abs(report["art"]["second"]-report["start"]["art"])<.025
        assert abs(report["calendar"]["calendar"]-report["start"]["calendar"]-2.45)<.025
        assert abs(report["calendar"]["artRestored"]-report["start"]["art"])<.025
        assert report["plant"]["red"]>report["start"]["planter"]
        assert abs(report["plant"]["calendarRestored"]-report["start"]["calendar"])<.025
        assert abs(report["vent"]["hinge"])>.2 and report["vent"]["passable"]
        assert report["ventClient"]["stream"]<.5 and report["ventClient"]["smoke"]>15
        assert report["reset"]["level"]==1 and abs(report["reset"]["hinge"])<.001
        assert report["reset"]["plant"]==report["start"]["planter"] and not report["clientReset"]["exists"]
    finally:
        call("start_stop_play",is_start=False)
