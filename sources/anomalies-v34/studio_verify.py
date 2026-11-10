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
        if "--walk" in sys.argv:
            s('''
    p:SetAttribute("KonturZone","Office")
    switch("Clear","Printer")
    move(1050,42)
    local deadline=os.clock()+8
    repeat task.wait(.1) until printer:GetAttribute("WarningPhase")=="Ready" or os.clock()>deadline
    assert(qa:Invoke(p,"Read"))
    local starts=state:GetAttribute("PrinterPaperStartsAt")
    move(1033,41,0,-1)
    local h=char:FindFirstChildOfClass("Humanoid")
    task.spawn(function()
        for _,step in ipairs({{-.4,32},{3.0,43},{7.0,33}}) do
            while workspace:GetServerTimeNow()<starts+step[1] do task.wait(.05) end
            h:MoveTo(Vector3.new(1033,3.14,step[2]))
        end
    end)
    return {starts=starts}
    ''')
            walk=c('''
    local f=office:WaitForChild("PrinterPaperFlight",4)
    local human=p.Character:WaitForChild("Humanoid")
    local root=p.Character:WaitForChild("HumanoidRootPart")
    local head=p.Character:WaitForChild("Head")
    local camera=workspace.CurrentCamera
    local run=game:GetService("RunService")
    run:BindToRenderStep("Office34WalkingView",Enum.RenderPriority.Last.Value,function()
        camera.CameraType=Enum.CameraType.Scriptable
        camera.CFrame=CFrame.lookAt(head.Position,head.Position+root.CFrame.LookVector)
    end)
    local cues={}
    local stats={}
    for _,sound in ipairs(f:GetDescendants()) do
        if sound:IsA("Sound") and sound.Name:find("^Rustle") then
            cues[sound.Name]=sound
            stats[sound.Name]={peak=0,inside=0,outside=0}
        end
    end
    local low,high=math.huge,-math.huge
    local started=state:GetAttribute("PrinterPaperStartsAt")
    repeat
        low=math.min(low,root.Position.Z)
        high=math.max(high,root.Position.Z)
        for name,sound in pairs(cues) do
            if not sound.IsPlaying then continue end
            local row=stats[name]
            row.peak=math.max(row.peak,sound.PlaybackLoudness)
            local distance=(camera.CFrame.Position-sound.Parent.Position).Magnitude
            if distance<sound.RollOffMaxDistance then row.inside+=1 else row.outside+=1 end
        end
        task.wait(.033)
    until workspace:GetServerTimeNow()>started+11.3
    run:UnbindFromRenderStep("Office34WalkingView")
    return {walkSpan=high-low,cues=stats,counts=#f:GetChildren()-1}
    ''')
            (out/"Walking_Audio_Check.json").write_text(json.dumps(walk,indent=2)+"\n")
            assert walk["walkSpan"]>6 and walk["counts"]==240,walk
            assert walk["cues"]["RustleArcPass"]["inside"]>0,walk
            sys.exit(0)
        report={}
        report["start"]=s('''
p:SetAttribute("KonturZone","Office")
assert(state.Level.Value==1 and state:GetAttribute("OfficeDetailScenario")=="Clear")
assert(office.MaintenanceVent and not office.Rooms.NW:FindFirstChild("BloodMessage"))
assert(not office:FindFirstChild("UnlistedServiceDoor"))
local nw=office.Rooms.NW
local plant=office.Rooms.WEST.V09_0348_WallPlanter
local function checkPlant()
    local n=0
    for _,item in ipairs(plant:GetDescendants()) do
        if item:IsA("BasePart") and item.Color.R>item.Color.G*1.5 then n+=1 end
    end
    return n
end
return {art=nw.V09_0340_WorldTrade:GetPivot().Position.Z,calendar=nw.V09_0465_WallCalendar:GetPivot().Position.X,calendarY=nw.V09_0465_WallCalendar:GetPivot().Position.Y,
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
        report["rustle"]=c('''
local f=office:WaitForChild("PrinterPaperFlight",4)
local cues={}
for _,item in ipairs(f:GetDescendants()) do
    if item:IsA("Sound") and item.Name:find("^Rustle") then cues[item.Name]=item end
end
local event={}
for name,sound in pairs(cues) do
    sound.Played:Connect(function()
        event[name]={time=workspace:GetServerTimeNow()-state:GetAttribute("PrinterPaperStartsAt"),
            range=sound.RollOffMaxDistance,x=sound.Parent.Position.X,z=sound.Parent.Position.Z}
    end)
end
_G.Office34Rustle={cues=cues,events=event}
waitAge(1.62)
local n=0
for _ in pairs(event) do n+=1 end
return {early=n,events=event}
''')
        c('view(1033,5.25,38,1033,5.25,33.75); return true')
        report["monitor"]=c('''
waitAge(4.95)
local leaf=office.PrinterPaperFlight.Sheet_17_2
return {height=leaf.Position.Y,near=(leaf.Position-Vector3.new(1020.36,5.335,47.60)).Magnitude}
''')
        report["receipt"]=c('''
waitAge(5.72)
local folder=office.PrinterPaperFlight
local receipt=folder.ReceiptEncounter
return {stage=receipt:GetAttribute("Phase"),count=#folder:GetChildren()-1,
    raised=receipt.ReceiptHalf1.Transparency<.05,deskHeight=folder.Sheet_28_2.Position.Y}
''')
        report["contact"]={"height":report["receipt"].pop("deskHeight")}
        capture("01_receipt")
        report["receiptSide"]=c('''
local receipt=office.PrinterPaperFlight.ReceiptEncounter
local leaf=receipt.ReceiptHalf1
local char=p.Character
local root=char.HumanoidRootPart
local before=leaf.CFrame.LookVector.X
local at=leaf.Position
local x=root.Position.X
local human=char.Humanoid
local previous=human.WalkSpeed
human.WalkSpeed=5
human:MoveTo(Vector3.new(x+2.45,root.Position.Y,root.Position.Z))
local deadline=os.clock()+.60
repeat
    view(root.Position.X,5.15,root.Position.Z,at.X,at.Y,at.Z)
    task.wait(.05)
until root.Position.X-x>1.39 or os.clock()>deadline
task.wait(.21)
human.WalkSpeed=previous
return {stage=receipt:GetAttribute("Phase"),delta=leaf.CFrame.LookVector.X-before,span=root.Position.X-x}
''')
        capture("13_receipt_side")
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
        report["rustleFlight"]=c('''
local tracker=_G.Office34Rustle
local loaded=0
for _,sound in pairs(tracker.cues) do if sound.IsLoaded then loaded+=1 end end
local count=0
for _ in pairs(tracker.events) do count+=1 end
return {events=tracker.events,loaded=loaded,count=count}
''')
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
        report["archivePartial"]=c('''
local ink=detail().WallInk
local blockers={}
for _,z in ipairs({-18.15,-16.05}) do
    local screen=Instance.new("Part")
    screen.Name="ArchiveTestOccluder"
    screen.Size=Vector3.new(.13,2,.45)
    screen.Position=Vector3.new(1029.5675,5.28,z)
    screen.Anchored=true
    screen.CanCollide=false
    screen.Transparency=1
    screen.Parent=workspace
    table.insert(blockers,screen)
end
view(1027.35,5.20,-17.1,1031.785,5.36,-17.1)
task.wait(1.25)
local stage=ink:GetAttribute("Stage")
for _,screen in ipairs(blockers) do screen:Destroy() end
return {stage=stage}
''')
        report["archiveRead"]=c('''
view(1026.2,5.20,-19.5,1031.785,5.36,-17.1)
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
        s('move(988,64,1,0); task.wait(.35); return true')
        s('move(1027.35,-17.1,1,0); return true')
        report["archiveReadBack"]=c('''
view(1027.35,5.20,-17.1,1031.785,5.36,-17.1)
local ink=detail().WallInk
task.wait(.15)
return {stage=ink:GetAttribute("Stage"),first=ink.WallPaint.First:FindFirstChildOfClass("TextLabel").TextTransparency}
''')
        report["archiveLookDown"]=c('''
view(1027.35,5.2,-17.1,1027.36,1.9,-17.1)
task.wait(.68)
return {stage=detail().WallInk:GetAttribute("Stage")}
''')
        report["archiveTurn"]=c('''
view(1027.35,5.2,-17.1,1016,4.7,-16.2)
task.wait(1.27)
local ink=detail().WallInk
local changed=ink:GetAttribute("Stage")
local first=ink.WallPaint.First:FindFirstChildOfClass("TextLabel").TextTransparency
local second=ink.WallPaint.Second:FindFirstChildOfClass("TextLabel").TextTransparency
view(1027.35,5.20,-17.1,1031.785,5.36,-17.1)
return {stage=changed,first=first,second=second}
''')
        capture("05_archive_return")
        s('move(1011,-30,-1,0); return true')
        s('move(988,64,1,0); task.wait(.35); return true')
        report["archiveFar"]=c('return {exists=office:FindFirstChild("OfficeDetailPresentation")~=nil}')
        s('move(1027.35,-17.1,1,0); return true')
        report["archiveBack"]=c('''
view(1027.35,5.20,-17.1,1031.785,5.36,-17.1)
local ink=detail().WallInk
task.wait(.85)
return {stage=ink:GetAttribute("Stage")}
''')
        report["art"]=s('''
switch("Anomaly","ArchiveArtSwap")
move(1024,-18,1,0)
local a=office.Rooms.NW
local one,two=a.V09_0340_WorldTrade:GetPivot(),a.V09_0341_GrowthTechnology:GetPivot()
return {first=one.Position.Z,second=two.Position.Z,firstTilt=math.deg(math.acos(one.UpVector.Y)),
    secondTilt=math.deg(math.acos(two.UpVector.Y))}
''')
        c('view(1024,5.4,-18,1031.65,7.9,-17.5); task.wait(3.0); return true')
        capture("06_static_art")
        report["calendar"]=s('''
switch("Anomaly","ArchiveCalendarShift")
local a=office.Rooms.NW
return {artRestored=a.V09_0340_WorldTrade:GetPivot().Position.Z,calendar=a.V09_0465_WallCalendar:GetPivot().Position.X,calendarY=a.V09_0465_WallCalendar:GetPivot().Position.Y,oldPin=a:FindFirstChild("OldCalendarPin")~=nil}
''')
        c('view(1010.8,5.4,-8,1010.45,5.45,-.3); task.wait(2.3); return true')
        capture("07_static_calendar")
        report["plant"]=s('''
switch("Anomaly","WestPlanterColor")
local n,redStems=0,0
for _,item in ipairs(office.Rooms.WEST.V09_0348_WallPlanter:GetDescendants()) do
    if item:IsA("BasePart") and item.Color.R>item.Color.G*1.5 then
        n+=1
        if item.Name:find("PlantStem") then redStems+=1 end
    end
end
return {red=n,redStems=redStems,calendarRestored=office.Rooms.NW.V09_0465_WallCalendar:GetPivot().Position.X,oldPin=office.Rooms.NW:FindFirstChild("OldCalendarPin")~=nil}
''')
        c('view(996.5,5.1,51.5,999.43,4.32,47.97); task.wait(3.0); return true')
        capture("08_static_plant")
        report["vent"]=s('''
switch("Anomaly","GreenVent")
move(1004,49.5,-1,0)
task.wait(.95)
local vent=office.MaintenanceVent
local hatch=vent.HingedLouvers:GetPivot()
local top,width=0,0
for _,part in ipairs(vent:GetChildren()) do
    if part.Name=="Flange" then
        top=math.max(top,part.Position.Y+part.Size.Y*.5)
        width=math.max(width,part.Size.X)
    end
end
local q=RaycastParams.new()
q.FilterType=Enum.RaycastFilterType.Exclude
q.FilterDescendantsInstances={char}
local along=workspace:Raycast(Vector3.new(1004,3,46),Vector3.new(0,0,8),q)
local ceiling=workspace:Raycast(Vector3.new(1000.65,10,49.5),Vector3.yAxis*3,q)
return {hinge=hatch.RightVector.X,passable=along==nil,width=width,top=top,
    ceilingGap=ceiling and ceiling.Position.Y-top,ceiling=ceiling and ceiling.Instance.Name}
''')
        report["ventClient"]=c('''
view(1005.9,5.15,53.45,1000.51,9.85,49.50)
task.wait(2.35)
local f=detail()
local hits=0
local low,high=100,0
local untilTime=os.clock()+7.35
local jet=f.VentVaporOrigin:FindFirstChild("GreenJet",true)
local bead=f.CondensationBead
local primary=f.FallingDrop1
local beadLow,beadHigh=1,0
local releaseGap=1
local previousBead
repeat
    low=math.min(low,jet.Rate); high=math.max(high,jet.Rate)
    for _,item in ipairs(f:GetChildren()) do
        if item.Name=="DropImpact" and item.Transparency<.85 then hits+=1 end
    end
    if bead.Transparency<1 then
        beadLow=math.min(beadLow,bead.Size.Y)
        beadHigh=math.max(beadHigh,bead.Size.Y)
        previousBead=bead.Position
    elseif previousBead and primary.Transparency<1 then
        releaseGap=math.min(releaseGap,(primary.Position-previousBead).Magnitude)
        previousBead=nil
    end
    task.wait(.03)
until os.clock()>untilTime
local wet=f.WetFootprint.MergedWetness:FindFirstChildOfClass("CanvasGroup")
local tracks=0
for _,name in ipairs({"SeepOnWall","SideRunnel1","SideRunnel2"}) do
    local runnel=f.VentVaporOrigin:FindFirstChild(name)
    if runnel and runnel.Transparency.Keypoints[1].Value<.65 then tracks+=1 end
end
return {low=low,high=high,splashSamples=hits,footprint=wet.GroupTransparency,stream=f.VentVaporOrigin.SeepOnWall.Transparency.Keypoints[1].Value,
    sourceY=f.VentVaporOrigin.Position.Y,beadLow=beadLow,beadHigh=beadHigh,releaseGap=releaseGap,tracks=tracks}
''')
        capture("09_vent_wide")
        c('view(1003.35,9.40,51.10,1000.45,10.20,49.50); return true')
        capture("10_vent_close")
        c('view(1003.15,2.14,51.05,1000.49,.43,49.9); return true')
        capture("12_vent_floor")
        report["door"]=s('''
switch("Anomaly","WhisperDoor")
move(1004.9,39.7,-1,0)
local model=office:WaitForChild("UnlistedServiceDoor",3)
local q=RaycastParams.new()
q.FilterType=Enum.RaycastFilterType.Exclude
q.FilterDescendantsInstances={char}
local crossing=workspace:Raycast(Vector3.new(1004,3,36),Vector3.zAxis*8,q)
local back=workspace:Raycast(Vector3.new(1004,4,39.7),-Vector3.xAxis*5,q)
return {pieces=#model:GetChildren(),passable=crossing==nil,wall=back and back.Instance.Name}
''')
        report["doorFar"]=c('''
view(1007.0,5.12,45.58,1000.47,4.75,39.7)
local source=detail():WaitForChild("BehindDoorAudio",3)
local stats={}
for _,item in ipairs(source:GetChildren()) do
    if not item:IsA("Sound") then continue end
    local row={plays=0,peak=0}
    item.Played:Connect(function() row.plays+=1 end)
    stats[item.Name]=row
end
_G.Office34DoorStats=stats
task.wait(3.20)
return {breath=stats.MuffledBreath.plays,knock=stats.DullKnock.plays}
''')
        capture("14_door_corridor")
        s('move(1001.40,39.7,-1,0); return true')
        report["doorNear"]=c('''
view(1001.40,4.61,39.7,1000.46,4.55,39.7)
local source=detail().BehindDoorAudio
local stats=_G.Office34DoorStats
local deadline=os.clock()+2.42
repeat
    for _,item in ipairs(source:GetChildren()) do
        local row=stats[item.Name]
        if row then row.peak=math.max(row.peak,item.PlaybackLoudness) end
    end
    task.wait(.025)
until os.clock()>deadline
return stats
''')
        c('view(1002.25,4.75,37.62,1000.56,4.58,38.30); return true')
        capture("15_door_handle")
        s('move(999.1,39.7,1,0); return true')
        report["doorBehind"]=c('''
local source=detail().BehindDoorAudio
local stats=_G.Office34DoorStats
local before=stats.MuffledBreath.plays+stats.DullKnock.plays
task.wait(1.85)
return {plays=stats.MuffledBreath.plays+stats.DullKnock.plays-before,
    playing=source.MuffledBreath.IsPlaying or source.DullKnock.IsPlaying}
''')
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
    door=office:FindFirstChild("UnlistedServiceDoor")~=nil,
    art=a.V09_0340_WorldTrade:GetPivot().Position.Z,calendar=a.V09_0465_WallCalendar:GetPivot().Position.X}
''')
        report["clientReset"]=c('return {exists=office:FindFirstChild("OfficeDetailPresentation")~=nil}')
        (out/"Studio_Check.json").write_text(json.dumps(report,indent=2)+"\n")
        assert report["print"]["delay"]>4.8
        assert report["rustle"]["early"]==5 and report["rustleFlight"]["count"]==9,report
        assert report["rustleFlight"]["loaded"]==9,report
        events=report["rustleFlight"]["events"]
        for name,when in (("RustleTray",0),("RustleMonitorBrush",4.56),("RustleDeskSlide",5.68),
                          ("RustleArcPass",8.72),("RustleFloorTurn",10.43)):
            assert abs(events[name]["time"]-when)<.30,events
        assert abs(events["RustleTray"]["x"]-events["RustleFarDesk"]["x"])>10
        assert report["archiveReadBack"]["stage"]=="Read"
        assert report["archiveReadBack"]["first"]<.1
        assert report["archiveTurn"]["first"]>.99 and report["archiveTurn"]["second"]<.1
        assert report["art"]["firstTilt"]>2 and report["art"]["secondTilt"]>1
        assert report["plant"]["redStems"]==0 and 0<report["plant"]["red"]<90
        assert .5<report["ventClient"]["footprint"]<.6
        assert report["receipt"]=={"stage":"Read","count":240,"raised":True},report
        assert report["receiptSide"]["stage"]=="Read" and report["receiptSide"]["delta"]>.16 and report["receiptSide"]["span"]>1,report["receiptSide"]
        assert 3.3<report["contact"]["height"]<3.85
        assert report["monitor"]["near"]<.24 and report["floor"]["near"]<.24
        assert report["arc"]["bands"]==9
        assert report["archiveGlance"]["stage"]=="Hidden"
        assert report["archivePartial"]["stage"]=="Hidden"
        assert report["archiveRead"]["stage"]=="Read" and not report["archiveRead"]["legacy"]
        assert report["archiveLookDown"]["stage"]=="Read" and report["archiveTurn"]["stage"]=="Changed"
        assert not report["archiveFar"]["exists"] and report["archiveBack"]["stage"]=="Changed"
        assert abs(report["calendar"]["calendarY"]-report["start"]["calendarY"]+.51)<.02
        assert report["calendar"]["oldPin"] and not report["plant"]["oldPin"]
        assert abs(report["art"]["second"]-report["start"]["art"])<.025
        assert abs(report["calendar"]["calendar"]-report["start"]["calendar"]-2.45)<.025
        assert abs(report["calendar"]["artRestored"]-report["start"]["art"])<.025
        assert report["plant"]["red"]>report["start"]["planter"]
        assert abs(report["plant"]["calendarRestored"]-report["start"]["calendar"])<.025
        assert abs(report["vent"]["hinge"])>.2 and report["vent"]["passable"]
        assert 1.30<report["vent"]["width"]<1.39 and .16<report["vent"]["ceilingGap"]<.36,report["vent"]
        assert report["ventClient"]["stream"]<.5
        assert report["ventClient"]["tracks"]==3
        assert report["ventClient"]["low"]<7 and report["ventClient"]["high"]>15
        assert report["ventClient"]["splashSamples"]>0
        assert report["ventClient"]["beadHigh"]-report["ventClient"]["beadLow"]>.02
        assert report["ventClient"]["releaseGap"]<.055
        assert report["door"]["pieces"]>=25 and report["door"]["passable"] and report["door"]["wall"].startswith("WallCore")
        assert report["doorFar"]=={"breath":0,"knock":0},report["doorFar"]
        assert all(row["plays"]>0 and row["peak"]>0 for row in report["doorNear"].values()),report["doorNear"]
        assert report["doorBehind"]=={"plays":0,"playing":False},report["doorBehind"]
        assert not report["reset"]["door"]
        assert report["reset"]["level"]==1 and abs(report["reset"]["hinge"])<.001
        assert report["reset"]["plant"]==report["start"]["planter"] and not report["clientReset"]["exists"]
    finally:
        call("start_stop_play",is_start=False)
