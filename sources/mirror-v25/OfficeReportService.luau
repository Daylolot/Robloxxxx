-- One server authority: crew answer, level progression, environment reset and arrival.
local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local Storage=game:GetService("ServerStorage")
local resetEvent=Storage:FindFirstChild("OfficeRoundReset")
if not resetEvent then resetEvent=Instance.new("BindableEvent");resetEvent.Name="OfficeRoundReset";resetEvent.Parent=Storage end
local Logic=require(RS:WaitForChild("OfficeReportLogic"))
local office=workspace:WaitForChild("OfficeMap")
local start=office:WaitForChild("Rooms"):WaitForChild("StartRoom")
local feedback=RS:WaitForChild("ReportFeedback")
local state=office:WaitForChild("AnomalyReportState")
local submittedEvent=state:WaitForChild("ReportSubmitted")
local modelState=Logic.New()
local ceiling=require(script.Parent:WaitForChild("CeilingWorkerRound")).new(office,state)
local flood
local women=office.Rooms:FindFirstChild("WOMEN")
local mirror=women and women:FindFirstChild("V09_0316_Mirror")
local mirrorPanel=mirror and mirror:FindFirstChild("MirrorPanel")
local mirrorAvailable=mirrorPanel and mirrorPanel:IsA("BasePart")
if mirrorAvailable then
    -- Lower the pair in every round so the player's shoulders are visible.
    mirror:PivotTo(mirror:GetPivot()-Vector3.yAxis*.55)
    local other=women:FindFirstChild("V09_0317_Mirror")
    if other and other:IsA("Model") then other:PivotTo(other:GetPivot()-Vector3.yAxis*.55) end
end
local devices={start:WaitForChild("V09_0276_ReportStation"),start:WaitForChild("V09_0278_ShiftStatusBoard")}
local random=Random.new()
local function ensure(class,name,initial)
    local v=state:FindFirstChild(name)
    if not v then v=Instance.new(class);v.Name=name;v.Value=initial;v.Parent=state end
    return v
end
local levelValue=ensure("IntValue","Level",1)
local phaseValue=ensure("StringValue","Phase","Preparing")
local resultValue=ensure("StringValue","ResultText","")
local correctValue=ensure("BoolValue","LastCorrect",false)
local function value(name)return state:FindFirstChild(name)end
local function character(player)
    local ch=player.Character
    return ch,ch and ch:FindFirstChild("HumanoidRootPart"),ch and ch:FindFirstChildOfClass("Humanoid")
end
local function inside(root)
    if not root then return false end
    local p=root.Position
    return p.X>=963 and p.X<=1113 and p.Z>=-33 and p.Z<=89 and p.Y>=-1 and p.Y<=13
end
local function context(player,button)
    local ch,root,h=character(player)
    local near=button and root and(root.Position-button.Position).Magnitude<=8.5
    local sight=false
    if near then
        local q=RaycastParams.new();q.FilterType=Enum.RaycastFilterType.Exclude
        q.FilterDescendantsInstances={ch,devices[1],devices[2]}
        local eye=root.Position+Vector3.new(0,1.5,0)
        sight=workspace:Raycast(eye,button.Position-eye,q)==nil
    end
    return {inOffice=player:GetAttribute("KonturZone")=="Office",alive=h~=nil and h.Health>0,
        inBounds=inside(root),near=near==true,lineOfSight=sight,
        userId=player.UserId,playerName=player.Name,now=os.clock()}
end

-- Only scenarios with complete activation/reset paths participate in the pool.
local blood=office.Rooms:WaitForChild("NW"):FindFirstChild("BloodMessage")
local bloodDefaults={}
if blood then
    for _,v in ipairs(blood:GetDescendants())do
        if v:IsA("BasePart")then bloodDefaults[v]={trans=v.Transparency,collide=v.CanCollide,query=v.CanQuery,touch=v.CanTouch}
        elseif v:IsA("SurfaceGui")or v:IsA("BillboardGui")then bloodDefaults[v]={enabled=v.Enabled}
        elseif v:IsA("Decal")or v:IsA("Texture")then bloodDefaults[v]={trans=v.Transparency}end
    end
end
local function showBlood(on)
    for v,b in pairs(bloodDefaults)do
        if v:IsA("BasePart")then
            v.Transparency=on and b.trans or 1
            v.CanCollide=on and b.collide or false;v.CanQuery=on and b.query or false;v.CanTouch=on and b.touch or false
        elseif b.enabled~=nil then v.Enabled=on and b.enabled or false
        else v.Transparency=on and b.trans or 1 end
    end
end
local preview=RS:FindFirstChild("KonturOfficePreview")
local previewPlate=preview and preview:FindFirstChild("Scene")and preview.Scene:FindFirstChild("BloodWritingPlate")
if previewPlate then
    previewPlate.Transparency=1
    for _,v in ipairs(previewPlate:GetDescendants())do if v:IsA("SurfaceGui")then v.Enabled=false end end
end
local lightStates={}
for i,v in ipairs(office:GetDescendants())do
    if v:IsA("BoolValue")and v.Name=="IsOn"and v.Parent:FindFirstChild("FixtureController")then lightStates[v]=v.Value end
    if i%2000==0 then task.wait()end
end
local function chooseEnvironment()
    local pool={}
    if blood then table.insert(pool,"ArchiveWriting")end
    if flood:IsAvailable()then table.insert(pool,"BloodFlood")end
    if ceiling:IsAvailable()then table.insert(pool,"CeilingWorker")end
    if mirrorAvailable then table.insert(pool,"Mirror")end
    local active=#pool>0 and random:NextNumber()<Logic.AnomalyChance(modelState.level)
    local scenario=active and pool[random:NextInteger(1,#pool)]or "Clear"
    local config=require(RS.BloodFloodConfig)
    if active and game:GetService("RunService"):IsStudio()then
        if script:GetAttribute("ForceMirrorInStudio") and mirrorAvailable then
            scenario="Mirror"
        elseif script:GetAttribute("ForceCeilingInStudio") and ceiling:IsAvailable()then
            scenario="CeilingWorker"
        elseif config.ForceBloodInStudio and flood:IsAvailable()then
            scenario="BloodFlood"
        end
    end
    showBlood(scenario=="ArchiveWriting")
    flood:SetActive(scenario=="BloodFlood",modelState.round)
    ceiling:SetActive(scenario=="CeilingWorker")
    state:SetAttribute("MirrorAnomalyRound",scenario=="Mirror" and modelState.round or nil)
    Logic.Activate(modelState,active)
end
local levelScreen=devices[2]:WaitForChild("ShiftDisplay"):WaitForChild("Display")
for _,v in ipairs(levelScreen:GetChildren())do if v:IsA("GuiObject") then v:Destroy()end end
local function screenLabel(name,text,y,height,size,color)
    local t=Instance.new("TextLabel");t.Name=name;t.Text=text
    t.Position=UDim2.fromScale(.04,y);t.Size=UDim2.fromScale(.92,height)
    t.BackgroundTransparency=1;t.TextColor3=color;t.Font=Enum.Font.SourceSansBold
    t.TextScaled=true;t.TextWrapped=true;t.Parent=levelScreen
    local c=Instance.new("UITextSizeConstraint");c.MinTextSize=12;c.MaxTextSize=size;c.Parent=t
    return t
end
levelScreen.LightInfluence=0;levelScreen.CanvasSize=Vector2.new(334,151)
screenLabel("Header","ТЕКУЩИЙ УРОВЕНЬ",.04,.18,24,Color3.fromRGB(195,222,221))
local screenNumber=screenLabel("LevelNumber","1",.23,.49,100,Color3.fromRGB(114,229,208))
screenLabel("Instructions","ОСМОТРИТЕ ОФИС → ВЕРНИТЕСЬ К КНОПКАМ",.78,.16,14,Color3.fromRGB(195,222,221))
local function refresh(message)
    screenNumber.Text=tostring(modelState.level)
    local text=message or "ОСМОТРИТЕ ОФИС · ВЫБЕРИТЕ РЕШЕНИЕ"
    for _,device in ipairs(devices)do
        for _,item in ipairs(device:GetDescendants())do
            if item:IsA("TextLabel")and item.Name=="StatusLine"then item.Text=text end
            if item:IsA("TextLabel")and item.Name=="RoundLine"then item.Text="УРОВЕНЬ / "..modelState.level end
            if item:IsA("ProximityPrompt")and item:FindFirstChild("Decision")then item.Enabled=modelState.accepting and modelState.phase=="Active"end
        end
    end
end
local function arrivals()
    local travel=workspace:FindFirstChild("KonturTravelPoints")
    local folder=travel and travel:FindFirstChild("OfficeTerminal")
    local points={}
    if folder then for _,v in ipairs(folder:GetChildren())do if v:IsA("CFrameValue")then table.insert(points,v)end end end
    table.sort(points,function(a,b)return a.Name<b.Name end)
    return points
end
local function returnCrew()
    local points=arrivals()
    local crew={}
    for _,p in ipairs(Players:GetPlayers())do if p:GetAttribute("KonturZone")=="Office"then table.insert(crew,p)end end
    table.sort(crew,function(a,b)return a.UserId<b.UserId end)
    -- Respawn dead office crew in parallel. HubController preserves their Office zone.
    local pending={}
    for _,p in ipairs(crew)do
        local _,root,h=character(p)
        if not root or not h or h.Health<=0 then
            pending[p]=true
            task.spawn(function()
                local ok,err=pcall(function()p:LoadCharacterAsync()end)
                if not ok then warn("Office crew respawn: "..tostring(err))end
                pending[p]=nil
            end)
        end
    end
    local deadline=os.clock()+10
    while next(pending) and os.clock()<deadline do task.wait(.05)end
    for i,p in ipairs(crew)do
        local ch,root,h=character(p)
        if root and h and h.Health>0 then
            local target=points[i]and points[i].Value or CFrame.lookAt(Vector3.new(988+((i-1)%3)*3,3.12,65+math.floor((i-1)/3)*3),Vector3.new(988,3.12,57))
            ch:PivotTo(target);root.AssemblyLinearVelocity=Vector3.zero;root.AssemblyAngularVelocity=Vector3.zero
            p:SetAttribute("OfficeArrivalIndex",i)
            p:SetAttribute("FacingCFrame",target);p:SetAttribute("FacingRevision",(p:GetAttribute("FacingRevision")or 0)+1)
            local notice=RS:FindFirstChild("HubNotice");if notice then notice:FireClient(p,"FaceDirection",target)end
        end
    end
end
local function finishRound(player,message,record,deadHumanoid)
    -- Lock before any event, replication or deferred work can yield to another answer.
    flood:Stop()
    ceiling:SetActive(false)
    state:SetAttribute("MirrorAnomalyRound",nil)
    value("AcceptingReports").Value=false
    value("HasSubmitted").Value=true
    value("ReportChoice").Value=record.Choice;value("ReporterName").Value=record.Reporter
    value("ReportRoom").Value=record.Room;value("ReportCategory").Value=record.Category
    value("Revision").Value=record.Revision
    resultValue.Value=message;correctValue.Value=record.Correct
    phaseValue.Value="Transition"
    if deadHumanoid and deadHumanoid.Parent and deadHumanoid.Health>0 then deadHumanoid.Health=0 end
    refresh(message)
    for _,p in ipairs(Players:GetPlayers())do if p~=player and p:GetAttribute("KonturZone")=="Office"then feedback:FireClient(p,message,true,nil,record.Correct)end end
    submittedEvent:Fire(player,record.Choice,record.RoundId,record)
    task.delay(Logic.TransitionDuration,function()
        if not Logic.BeginNextRound(modelState,record)then return end
        resetEvent:Fire()
        for v,on in pairs(lightStates)do if v.Parent then v.Value=on end end
        showBlood(false)
        task.wait() -- Let cancelled furniture motions release their drivers.
        returnCrew()
        chooseEnvironment()
        value("HasSubmitted").Value=false
        levelValue.Value=modelState.level
        value("RoundId").Value=modelState.round
        resultValue.Value=""
        value("AcceptingReports").Value=true
        refresh()
        phaseValue.Value="Active" -- Publish last, after geometry and arrivals are ready.
    end)
end
local function submit(player,request,button,requestId)
    modelState.accepting=value("AcceptingReports").Value and modelState.phase=="Active"
    local accepted,message,record=Logic.TrySubmit(modelState,context(player,button),request)
    feedback:FireClient(player,message,accepted,requestId,record and record.Correct)
    if not accepted then return end
    finishRound(player,message,record)
end

flood=require(script.Parent:WaitForChild("BloodFloodService")).New(office,phaseValue,function(player,h,roundId)
    local accepted,message,record=Logic.TryHazardFail(modelState,{
        inOffice=player:GetAttribute("KonturZone")=="Office",alive=h.Health>0,
        playerName=player.Name,userId=player.UserId,now=os.clock()},roundId)
    if not accepted then return false end
    finishRound(player,message,record,h)
    feedback:FireClient(player,message,true,nil,false)
    return true
end)

for _,device in ipairs(devices)do
    for _,item in ipairs(device:GetDescendants())do
        if item:IsA("ProximityPrompt")and item:FindFirstChild("Decision")then
            item.Exclusivity=Enum.ProximityPromptExclusivity.OnePerButton
            local decision=item.Decision.Value;local button=item.Parent
            local function invoke(player)
                submit(player,{Choice=decision,Room="ВЕСЬ ОФИС",Category="ОБЩАЯ ПРОВЕРКА",Source="Console",RoundId=modelState.round},button)
            end
            item.Triggered:Connect(invoke)
            local click=button:FindFirstChild("ReportClick");if click then click.MouseClick:Connect(invoke)end
        end
    end
end
Players.PlayerRemoving:Connect(function(p)modelState.lastByPlayer[p.UserId]=nil end)
chooseEnvironment()
levelValue.Value=1;value("RoundId").Value=1;value("HasSubmitted").Value=false
value("AcceptingReports").Value=true;phaseValue.Value="Active"
refresh()
