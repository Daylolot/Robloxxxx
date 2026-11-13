if not game:GetService("RunService"):IsStudio() then return end
local player=game.Players.LocalPlayer
local run=game:GetService("RunService")
local office=workspace:WaitForChild("OfficeMap")
local state=office:WaitForChild("AnomalyReportState")
local channel=game.ReplicatedStorage:WaitForChild("PrinterCoopProbe",55)
if not channel then return end
local aim=Vector3.new(1033,4.9,29)
local wall=Vector3.new(1031.785,5.36,-17.1)
run:BindToRenderStep("OfficeCoop35Camera",Enum.RenderPriority.Last.Value,function()
    local head=player.Character and player.Character:FindFirstChild("Head")
    if head then
        local camera=workspace.CurrentCamera
        camera.CameraType=Enum.CameraType.Scriptable
        camera.CFrame=CFrame.lookAt(head.Position,aim)
        camera.Focus=CFrame.new(aim)
    end
end)
local function snapshot()
    local folder=office:FindFirstChild("PrinterPaperFlight")
    local rows={}
    if folder then
        local children=folder:GetChildren()
        table.sort(children,function(a,b)return a.Name<b.Name end)
        for _,part in ipairs(children) do
            if part:IsA("BasePart") then
                local p,u=part.Position,part.CFrame.UpVector
                table.insert(rows,{p.X,p.Y,p.Z,u.X,u.Y,u.Z})
            end
        end
    end
    return {clock=workspace:GetServerTimeNow(),startsAt=state:GetAttribute("PrinterPaperStartsAt"),
        count=#rows,rows=rows,level=state.Level.Value,round=state.RoundId.Value}
end
local function probe(action,at)
    if at then
        repeat run.RenderStepped:Wait() until workspace:GetServerTimeNow()>=at
        run.RenderStepped:Wait()
    end
    if action=="sample" then return snapshot() end
    if action=="door_audio" then
        local source=office:WaitForChild("OfficeDetailPresentation",4):WaitForChild("BehindDoorAudio",4)
        local lever=office.UnlistedServiceDoor.DoorLever
        local rest=lever:GetAttribute("RestPose")
        local max,angle=0,0
        for _=1,59 do
            max=math.max(max,source.MuffledBreath.PlaybackLoudness,source.DullKnock.PlaybackLoudness)
            angle=math.max(angle,math.deg(math.acos(math.clamp(rest:ToObjectSpace(lever:GetPivot()).RightVector.X,-1,1))))
            task.wait(.037)
        end
        return {peak=max,angle=angle}
    end
    if action=="vent" or action=="vent_far" then
        local root=player.Character:WaitForChild("HumanoidRootPart",3)
        assert(root,"missing client root")
        if action=="vent_far" then
            local destination=Vector3.new(1085,3.14,48)
            local deadline=os.clock()+3
            while (root.Position-destination).Magnitude>5 and os.clock()<deadline do
                run.RenderStepped:Wait()
            end
            assert((root.Position-destination).Magnitude<=5,"far position not replicated")
            task.wait(.18)
        end
        local visual=office:FindFirstChild("OfficeDetailPresentation")
        local jet=visual and visual:FindFirstChild("GreenJet",true)
        local drop=visual and visual:FindFirstChild("FallingDrop1")
        local second=visual and visual:FindFirstChild("FallingDrop2")
        return {exists=jet~=nil,rate=jet and jet.Rate,x=root.Position.X,
            dropY=drop and drop.Transparency<1 and drop.Position.Y or nil,
            sideY=second and second.Transparency<1 and second.Position.Y or nil,
            angle=office.MaintenanceVent.HingedLouvers:GetPivot().RightVector.X}
    end
    local folder=office:WaitForChild("OfficeDetailPresentation",5)
    local ink=assert(folder and folder:FindFirstChild("WallInk"),"archive missing")
    if action=="archive_read" then
        aim=wall;task.wait(1.42)
    elseif action=="archive_down" then
        local head=player.Character.Head
        aim=head.Position+Vector3.new(.008,-3,0)
        task.wait(.62)
    elseif action=="archive_turn" then
        aim=Vector3.new(1018,4.8,-16.5);task.wait(.65)
    end
    local newInk=ink.WallPaint.Second:FindFirstChildOfClass("TextLabel")
    return {stage=ink:GetAttribute("Stage"),second=newInk.TextTransparency}
end
channel.OnClientEvent:Connect(function(id,action,at)
    local ok,result=pcall(probe,action,at)
    channel:FireServer(id,{ok=ok,data=ok and result or nil,error=not ok and tostring(result) or nil})
end)
task.spawn(function()
    repeat
        channel:FireServer("ready",{ok=true})
        task.wait(.5)
    until player:GetAttribute("PrinterProbeReady")
end)
