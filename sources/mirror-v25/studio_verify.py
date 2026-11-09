"""Check the saved QA map through the round service and the actual mirrored avatars."""
import base64
import json
from pathlib import Path
import sys
import time

from studio_bridge import StudioBridge

out = Path(sys.argv[1])
with StudioBridge() as bridge:
    for attempt in range(50):
        studios = json.loads(bridge.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        if len(studios) == 1:
            studio = studios[0]["id"]
            break
        time.sleep(.5)
    else:
        raise RuntimeError("A single Studio instance did not connect")

    def call(tool, **kwargs):
        result = bridge.call(tool, {"studio_id": studio, **kwargs})
        assert not result.get("isError"), result
        return result["content"]

    def run(mode, code):
        result = json.loads(call("execute_luau", datamodel_type=mode, code=code)[0]["text"])
        print(mode, result, flush=True)
        return result

    def capture(name):
        for block in call("screen_capture", capture_id="ScreenCapture_1"):
            if block["type"] == "image":
                (out / name).write_bytes(base64.b64decode(block["data"]))
                return True
        return False

    if "--playing" not in sys.argv:
        call("start_stop_play", is_start=True)
        time.sleep(5)
    report = {}
    place_at_mirror = """
local p=game.Players:GetPlayers()[1]
local char=p.Character or p.CharacterAdded:Wait()
local root=char:WaitForChild("HumanoidRootPart")
local panel=workspace.OfficeMap.Rooms.WOMEN.V09_0316_Mirror.MirrorPanel
local facing=panel.CFrame.LookVector
local eye=panel.Position+facing*4.4
local position=Vector3.new(eye.X,3.14,eye.Z)
p:SetAttribute("KonturZone","Office")
char:PivotTo(CFrame.lookAt(position,position-facing))
root.AssemblyLinearVelocity=Vector3.zero
return {position=tostring(position),normal=tostring(facing),height=panel.Size.Y,panelCenter=panel.Position.Y}
"""
    report["mirror"] = run("Server", place_at_mirror)
    setup = """
local p=game.Players.LocalPlayer
local char=p.Character
local room=workspace.OfficeMap.Rooms:WaitForChild("WOMEN")
local panel=room:WaitForChild("V09_0316_Mirror"):WaitForChild("MirrorPanel")
local neighbor=room:WaitForChild("V09_0317_Mirror"):WaitForChild("MirrorPanel")
local mirror=p.PlayerGui:WaitForChild("LiveMirror_V09_0316_Mirror")
local second=p.PlayerGui:WaitForChild("LiveMirror_V09_0317_Mirror")
local c=workspace.CurrentCamera
local start=char:GetPivot()
local normal=panel.CFrame.LookVector
local right=panel.CFrame.RightVector
c.CameraType=Enum.CameraType.Scriptable
local function aim()
    local eye=char.Head.Position
    c.CFrame=CFrame.lookAt(eye,Vector3.new(panel.Position.X,eye.Y,panel.Position.Z))
    c.Focus=panel.CFrame
end
local function clone(gui)
    local actor=gui:FindFirstChild("Reflection_"..p.Name,true)
    return actor and actor:FindFirstChild("Head")
end
local function expected(source,glass)
    local n=glass.CFrame.LookVector
    local origin=glass.Position+n*(glass.Size.Z*.5+.002)
    return source-2*n*(source-origin):Dot(n)
end
aim()
local deadline=os.clock()+6
while not (clone(mirror) and clone(second)) and os.clock()<deadline do task.wait(.05) end
assert(clone(mirror) and clone(second),"reflected characters not visible")
"""
    report["baseline"] = run("Client", setup+"""
task.wait(.15)
return {error=(clone(mirror).Position-expected(char.Head.Position,panel)).Magnitude,visible=mirror.Enabled}
""")
    report["baselineImage"] = capture("01_live.png")

    report["selected"] = run("Server", """
local p=game.Players:GetPlayers()[1]
local office=workspace.OfficeMap
local state=office.AnomalyReportState
local station=office.Rooms.StartRoom.V09_0276_ReportStation
local button=station.ReportButton_Clear
local board=office.Rooms.StartRoom.V09_0278_ShiftStatusBoard
local query=RaycastParams.new()
query.FilterType=Enum.RaycastFilterType.Exclude
query.FilterDescendantsInstances={p.Character,station,board}
local pos=button.Position
local found
for i=0,15 do
    local a=i*math.pi/8
    local target=Vector3.new(pos.X+3*math.cos(a),3.14,pos.Z+3*math.sin(a))
    local eye=target+Vector3.yAxis*1.5
    if not workspace:Raycast(eye,pos-eye,query) then found=target;break end
end
assert(found,"no clear report position")
p.Character:PivotTo(CFrame.new(found))
game.ServerStorage.MirrorLocalQA:Invoke(p,"Clear")
local deadline=os.clock()+8
while state.Level.Value~=2 or state.Phase.Value~="Active" do
    assert(os.clock()<deadline,state.ResultText.Value)
    task.wait(.1)
end
assert(state:GetAttribute("MirrorAnomalyRound")==state.RoundId.Value)
return {level=state.Level.Value,round=state.RoundId.Value,mirror=state:GetAttribute("MirrorAnomalyRound")}
""")
    run("Server", place_at_mirror)
    report["timeline"] = run("Client", setup+"""
local began=os.clock()
local stats={initial=0,delayed=0,frozenDrift=0,frozenSeparation=0,other=0,recovered=0,visible=true}
local held
local function step(offset)
    char:PivotTo(start+right*offset)
    aim()
    task.wait(.11)
end
while os.clock()-began<10.9 do
    local age=os.clock()-began
    local offset=.65*math.sin(age*5)
    step(offset)
    local reflected=clone(mirror).Position
    local live=expected(char.Head.Position,panel)
    local error=(reflected-live).Magnitude
    stats.other=math.max(stats.other,(clone(second).Position-expected(char.Head.Position,neighbor)).Magnitude)
    if age>.3 and age<2.45 then stats.initial=math.max(stats.initial,error) end
    if age>3.6 and age<5.1 then stats.delayed=math.max(stats.delayed,error) end
    if age>6.2 and age<9.35 then
        held=held or reflected
        stats.frozenDrift=math.max(stats.frozenDrift,(reflected-held).Magnitude)
        stats.frozenSeparation=math.max(stats.frozenSeparation,error)
        stats.visible=stats.visible and mirror.Enabled
    end
    if age>10.6 then stats.recovered=math.max(stats.recovered,error) end
end
return stats
""")
    report["rearm"] = run("Client", setup+"""
char:PivotTo(start+normal*4.5)
aim()
task.wait(.3)
char:PivotTo(start)
aim()
task.wait(6.25)
char:PivotTo(start+right*.85)
aim()
task.wait(.18)
return {frozen=(clone(mirror).Position-expected(char.Head.Position,panel)).Magnitude,
    neighbor=(clone(second).Position-expected(char.Head.Position,neighbor)).Magnitude}
""")
    report["frozenImage"] = capture("02_frozen.png")
    report["sameViewRestored"] = run("Client", setup+"""
task.wait(4)
return {error=(clone(mirror).Position-expected(char.Head.Position,panel)).Magnitude}
""")
    report["restoredImage"] = capture("03_restored.png")
    report["reset"] = run("Server", """
local p=game.Players:GetPlayers()[1]
local office=workspace.OfficeMap
local state=office.AnomalyReportState
local start=office.Rooms.StartRoom
local station=start.V09_0276_ReportStation
local button=station.ReportButton_Anomaly
local query=RaycastParams.new()
query.FilterType=Enum.RaycastFilterType.Exclude
query.FilterDescendantsInstances={p.Character,station,start.V09_0278_ShiftStatusBoard}
local pos=button.Position
for i=0,15 do
    local a=i*math.pi/8
    local target=Vector3.new(pos.X+3*math.cos(a),3.14,pos.Z+3*math.sin(a))
    local eye=target+Vector3.yAxis*1.5
    if not workspace:Raycast(eye,pos-eye,query) then
        p.Character:PivotTo(CFrame.new(target))
        break
    end
end
game.ServerStorage.MirrorLocalQA:Invoke(p,"Anomaly")
return {accepted=state.Phase.Value=="Transition",correct=state.LastCorrect.Value,
    cleared=state:GetAttribute("MirrorAnomalyRound")==nil}
""")
    (out / "Studio_Check.json").write_text(json.dumps(report, indent=2) + "\n")
    t = report["timeline"]
    assert abs(report["mirror"]["panelCenter"] - 5.1105) < .01, report["mirror"]
    assert report["baseline"]["error"] < .03 and report["baseline"]["visible"]
    assert t["initial"] < .1 and t["other"] < .12 and t["delayed"] > .25, t
    assert t["frozenDrift"] < .03 and t["frozenSeparation"] > .4 and t["visible"], t
    assert t["recovered"] < .1 and report["rearm"]["frozen"] > .4, report
    assert report["sameViewRestored"]["error"] < .1, report
    assert report["reset"] == {"accepted": True, "correct": True, "cleared": True}, report
    assert all(report[name] for name in ("baselineImage", "frozenImage", "restoredImage")), report
    call("start_stop_play", is_start=False)
