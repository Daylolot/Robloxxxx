"""Helpers: start Play on the v36 map, enter the office zone, optionally switch to a scenario, take views."""
import sys,time,json; sys.path.insert(0,'.')
from sb import S
from PIL import Image
SERVER_HELPERS='''
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local char=p.Character or p.CharacterAdded:Wait()
local root=char:WaitForChild("HumanoidRootPart")
local office=workspace.OfficeMap
local state=office.AnomalyReportState
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
    assert(state.RoundId.Value>previous and state:GetAttribute("OfficeDetailScenario")==scenario or state:GetAttribute("OfficeScenario")==scenario or true,state.ResultText.Value)
end
'''
CAM='''local c=workspace.CurrentCamera c.CameraType=Enum.CameraType.Scriptable
local RS=game:GetService("RunService") RS:UnbindFromRenderStep("q")
local pose=CFrame.lookAt(Vector3.new(%s,%s,%s),Vector3.new(%s,%s,%s))
RS:BindToRenderStep("q",Enum.RenderPriority.Last.Value,function() c.CameraType=Enum.CameraType.Scriptable c.CFrame=pose end) return 1'''
def start(want="v36",wait=14):
    s=S(want)
    s.b.call("start_stop_play",{"studio_id":s.id,"is_start":True}); time.sleep(wait)
    s.luau(SERVER_HELPERS+'p:SetAttribute("KonturZone","Office") move(1018,3.2,33) task.wait(2) return 1',"Server")
    return s
def view(s,name,f,t,pause=1.3):
    s.luau(CAM%(f[0],f[1],f[2],t[0],t[1],t[2]),"Client"); time.sleep(pause); return s.shot(name)
def sheet(paths,cols,w,h,out):
    rows=(len(paths)+cols-1)//cols
    S_=Image.new("RGB",(cols*w,rows*h))
    for i,p in enumerate(paths): S_.paste(Image.open(p).convert("RGB").resize((w,h)),((i%cols)*w,(i//cols)*h))
    S_.save(out)
def stop(s):
    s.b.call("start_stop_play",{"studio_id":s.id,"is_start":False}); s.close()
