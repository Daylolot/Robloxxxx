"""KONTUR v37 core-protection check in one Studio client (needs the map built with --qa --keep-guard).

Checks: (A) an instant answer is rejected, (B) an answer after the time limit is accepted,
(C) an error during the round change recovers instead of freezing the game.
Run from the repository root with the repo's venv python; studio_bridge.py lives one folder above.
"""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge

SERVER = """
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
local function walk(steps)
    local origin=root.Position
    for i=1,steps do
        local d=(i%2==1) and 8 or -8
        char:PivotTo(CFrame.new(origin+Vector3.new(d,0,0)))
        task.wait(.6)
    end
end
"""

CHECKS = {
    "B_accept_after_wait": """
ready(); local round=state.RoundId.Value
task.wait(7); nearButton("Clear"); qa:Invoke(p,"Clear"); task.wait(.5)
return {submitted=state.HasSubmitted.Value,result=state.ResultText.Value,phaseNow=state.Phase.Value}
""",
    "A_reject_too_early_after_B": """
ready() -- answer right away, before the time limit
local round=state.RoundId.Value
nearButton("Clear"); qa:Invoke(p,"Clear"); task.wait(.5)
return {zone=p:GetAttribute("KonturZone"),submitted=state.HasSubmitted.Value,round=state.RoundId.Value==round,phase=state.Phase.Value}
""",
    "C_recover_from_error": """
ready(); local before=state.RoundId.Value
local config=game.ReplicatedStorage:FindFirstChild("BloodFloodConfig")
if config then config.Parent=nil end -- chooseEnvironment now throws during the round change
task.wait(7); nearButton("Clear"); qa:Invoke(p,"Clear")
local deadline=os.clock()+20
repeat task.wait(.2) until (state.RoundId.Value>before and state.Phase.Value=="Active") or os.clock()>deadline
local out={recovered=state.RoundId.Value>before and state.Phase.Value=="Active",phase=state.Phase.Value,accepting=state.AcceptingReports.Value}
if config then config.Parent=game.ReplicatedStorage end
return out
""",
}

with StudioBridge() as bridge:
    for _ in range(65):
        studios = json.loads(bridge.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        match = [s for s in studios if "GuardQA" in (s.get("file") or "")]
        if match:
            studio = match[0]["id"]
            break
        time.sleep(.5)
    else:
        raise RuntimeError("Guard QA map is not open in Studio")

    def run(mode, code):
        result = bridge.call("execute_luau", {"studio_id": studio, "datamodel_type": mode, "code": code})
        assert not result.get("isError"), result
        return result["content"][0]["text"]

    bridge.call("start_stop_play", {"studio_id": studio, "is_start": True})
    try:
        time.sleep(8)
        for name, body in CHECKS.items():
            print(name, run("Server", SERVER + body), flush=True)
    finally:
        bridge.call("start_stop_play", {"studio_id": studio, "is_start": False})
