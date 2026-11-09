if not game:GetService("RunService"):IsStudio() then return end
local player=game.Players.LocalPlayer
local run=game:GetService("RunService")
local office=workspace:WaitForChild("OfficeMap")
local state=office:WaitForChild("AnomalyReportState")
local channel=game.ReplicatedStorage:WaitForChild("PrinterCoopProbe",50)
if not channel then return end
print("PRINTER_COOP_CLIENT "..player.Name)
local target=Vector3.new(1030,6.3,39)
local aim
run:BindToRenderStep("PrinterCoopCamera",Enum.RenderPriority.Camera.Value+20,function()
    local char=player.Character
    local head=char and char:FindFirstChild("Head")
    if head then
        local camera=workspace.CurrentCamera
        camera.CameraType=Enum.CameraType.Scriptable
        camera.CFrame=CFrame.lookAt(head.Position,aim or target)
        camera.Focus=CFrame.new(aim or target)
    end
end)
local function snapshot(at)
    if at then
        repeat run.RenderStepped:Wait() until workspace:GetServerTimeNow()>=at
        run.RenderStepped:Wait()
    end
    local visual=office:FindFirstChild("PrinterPaperFlight")
    local rows={}
    if visual then
        local ordered=visual:GetChildren()
        table.sort(ordered,function(a,b)return a.Name<b.Name end)
        for i,part in ipairs(ordered) do
            local p=part.Position
            local u=part.CFrame.UpVector
            rows[i]={p.X,p.Y,p.Z,u.X,u.Y,u.Z}
        end
    end
    return {clock=workspace:GetServerTimeNow(),startsAt=state:GetAttribute("PrinterPaperStartsAt"),
        count=#rows,rows=rows,level=state.Level.Value,round=state.RoundId.Value}
end
channel.OnClientEvent:Connect(function(id,action,at)
    local ok,result=pcall(function()
        if action=="read" then
            local printer=office.Rooms.CENTER:WaitForChild("Printer")
            local prompt=assert(printer:FindFirstChild("ReadPrinterWarning",true))
            aim=prompt.Parent.WorldPosition
            task.wait(.55)
            local enabled=prompt.Enabled
            prompt:InputHoldBegin()
            task.wait(math.max(.4,prompt.HoldDuration+.1))
            prompt:InputHoldEnd()
            task.wait(.3)
            aim=nil
            return {enabled=enabled,startsAt=state:GetAttribute("PrinterPaperStartsAt")}
        end
        return snapshot(at)
    end)
    channel:FireServer(id,{ok=ok,data=ok and result or nil,error=not ok and tostring(result) or nil})
end)
task.spawn(function()
    repeat
        channel:FireServer("ready",{ok=true})
        task.wait(.5)
    until player:GetAttribute("PrinterProbeReady")
end)
