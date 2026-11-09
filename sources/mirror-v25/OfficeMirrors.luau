-- Live bathroom mirrors. Local reflected scene; only nearby room geometry is copied.
local Players=game:GetService("Players")
local Run=game:GetService("RunService")
local player=Players.LocalPlayer
local office=workspace:WaitForChild("OfficeMap")
local rooms=office:WaitForChild("Rooms")
local round=office:WaitForChild("AnomalyReportState")
local phase=round:WaitForChild("Phase")
local playerGui=player:WaitForChild("PlayerGui")
local entries={}
local targetMirror="V09_0316_Mirror"
local gazeTime, normalTime, delayTime, frozenTime, blendTime=.8, 2, 3, 4, .65
local delay=.35
local function reflectPoint(point,origin,normal)
    return point-2*normal*((point-origin):Dot(normal))
end
local function reflectVector(vector,normal)
    return vector-2*normal*vector:Dot(normal)
end
local function reflectFrame(cf,origin,normal)
    return CFrame.fromMatrix(reflectPoint(cf.Position,origin,normal),
        -reflectVector(cf.RightVector,normal),reflectVector(cf.UpVector,normal),reflectVector(-cf.LookVector,normal))
end
local function clear(entry)
    if entry.world then entry.world:Destroy();entry.world=nil end
    entry.parts={};entry.characters={};entry.ready=false;entry.episode=nil
    entry.gui.Enabled=false
end
local function plainPart(size,cf,color,parent)
    local p=Instance.new("Part");p.Size=size;p.CFrame=cf;p.Color=color
    p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
    p.Material=Enum.Material.SmoothPlastic;p.Parent=parent
    return p
end
local function copyPart(source,entry)
    local clone=source:Clone()
    if not clone then return end
    for _,v in ipairs(clone:GetDescendants())do
        if v:IsA("LuaSourceContainer") or v:IsA("Sound") or v:IsA("LayerCollector")
            or v:IsA("Constraint") or v:IsA("JointInstance") or v:IsA("TouchTransmitter") then v:Destroy()end
    end
    clone.Anchored=true;clone.CanCollide=false;clone.CanQuery=false;clone.CanTouch=false
    clone.LocalTransparencyModifier=0
    clone.CFrame=reflectFrame(source.CFrame,entry.origin,entry.normal)
    clone.Parent=entry.world
    table.insert(entry.parts,{source=source,clone=clone,last=source.CFrame})
end
local function addCharacter(entry,character)
    if entry.characters[character] or not character:FindFirstChild("HumanoidRootPart") then return end
    local old=character.Archivable;character.Archivable=true
    local clone=character:Clone();character.Archivable=old
    if not clone then return end
    local pairs={}
    local function map(a,b)
        if a:IsA("BasePart") and b:IsA("BasePart")then
            b.Anchored=true;b.CanCollide=false;b.CanTouch=false;b.CanQuery=false;b.LocalTransparencyModifier=0
            table.insert(pairs,{source=a,clone=b})
        end
        local used={}
        for _,source in ipairs(a:GetChildren())do
            for _,target in ipairs(b:GetChildren())do
                if not used[target] and target.Name==source.Name and target.ClassName==source.ClassName then
                    used[target]=true;map(source,target);break
                end
            end
        end
    end
    map(character,clone)
    for _,v in ipairs(clone:GetDescendants())do
        if v:IsA("LuaSourceContainer") or v:IsA("Sound") or v:IsA("LayerCollector")
            or v:IsA("JointInstance") or v:IsA("Constraint") then v:Destroy()
        elseif v:IsA("Humanoid")then v.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.None end
    end
    clone.Name="Reflection_"..character.Name;clone.Parent=entry.world
    entry.characters[character]={model=clone,pairs=pairs}
end
local function build(entry)
    if entry.building or entry.world then return end
    entry.building=true
    entry.world=Instance.new("WorldModel");entry.world.Name="ReflectedRoom";entry.world.Parent=entry.viewport
    local list={}
    for _,part in ipairs(entry.room:GetDescendants())do
        if part:IsA("BasePart") and part.Transparency<.98 and not string.find(part.Parent.Name,"Mirror")
            and part.Size.X*part.Size.Y*part.Size.Z>=.015
            and (part.Position-entry.origin):Dot(entry.normal)>.04 then table.insert(list,part)end
    end
    -- Fine screws/curved micro-segments are omitted from the reflected LOD.
    for i,part in ipairs(list)do
        if not entry.world then entry.building=false;return end
        if part.Archivable then copyPart(part,entry)end
        if i%100==0 then Run.Heartbeat:Wait()end
    end
    local x=entry.room.Name=="MEN" and 1020 or 1044
    local shell={
        {Vector3.new(24,.18,20),CFrame.new(x,.02,78),Color3.fromRGB(107,112,108)},
        {Vector3.new(24,.18,20),CFrame.new(x,9.4,78),Color3.fromRGB(211,211,191)},
        {Vector3.new(.18,9.4,20),CFrame.new(x-12,4.7,78),Color3.fromRGB(178,194,180)},
        {Vector3.new(24,9.4,.18),CFrame.new(x,4.7,88),Color3.fromRGB(178,194,180)},
        {Vector3.new(24,9.4,.18),CFrame.new(x,4.7,68),Color3.fromRGB(178,194,180)}
    }
    for _,v in ipairs(shell)do plainPart(v[1],reflectFrame(v[2],entry.origin,entry.normal),v[3],entry.world)end
    entry.ready=true;entry.building=false
end
-- A streamed mirror frame may arrive before its glass panel. Register each panel
-- independently instead of blocking every mirror on the first WaitForChild.
local registered={}
local wanted={V09_0293_Mirror=true,V09_0294_Mirror=true,V09_0316_Mirror=true,V09_0317_Mirror=true}
local function mount(room,model,panel)
    if registered[panel]then return end
    local gui=Instance.new("SurfaceGui")
    gui.Name="LiveMirror_"..model.Name;gui.Adornee=panel;gui.Face=Enum.NormalId.Front
    gui.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
    gui.CanvasSize=Vector2.new(480,480*panel.Size.Y/panel.Size.X)
    gui.LightInfluence=0;gui.AlwaysOnTop=false;gui.ClipsDescendants=true;gui.ZOffset=.01
    gui.Enabled=false;gui.Parent=playerGui
    local clip=Instance.new("Frame");clip.Size=UDim2.fromScale(1,1);clip.BackgroundColor3=Color3.fromRGB(153,170,171)
    clip.BorderSizePixel=0;clip.ClipsDescendants=true;clip.Parent=gui
    local viewport=Instance.new("ViewportFrame")
    viewport.Name="Reflection";viewport.Size=UDim2.fromScale(1,1);viewport.BorderSizePixel=0
    viewport.BackgroundColor3=Color3.fromRGB(153,170,171)
    viewport.Ambient=Color3.fromRGB(183,190,183);viewport.LightColor=Color3.fromRGB(155,151,132)
    viewport.LightDirection=Vector3.new(-.4,-1,-.3);viewport.Parent=clip
    local camera=Instance.new("Camera");camera.Name="MirrorCamera";camera.Parent=viewport
    viewport.CurrentCamera=camera
    local entry={room=room,panel=panel,target=room.Name=="WOMEN" and model.Name==targetMirror,
        origin=panel.Position+panel.CFrame.LookVector*(panel.Size.Z*.5+.002),
        normal=panel.CFrame.LookVector,up=panel.CFrame.UpVector,width=panel.Size.X,height=panel.Size.Y,
        gui=gui,viewport=viewport,camera=camera,parts={},characters={},ready=false,lastUsed=0}
    table.insert(entries,entry)
    registered[panel]=entry
    panel.AncestryChanged:Connect(function()
        if panel:IsDescendantOf(workspace)then return end
        clear(entry);gui:Destroy();registered[panel]=nil
        local index=table.find(entries,entry);if index then table.remove(entries,index)end
    end)
end

local function lookingAtMirror(entry,camera,character)
    local eye=camera.CFrame.Position
    local direction=camera.CFrame.LookVector
    local along=-direction:Dot(entry.normal)
    if along<=0 then return false end
    local distance=(eye-entry.origin):Dot(entry.normal)/along
    local hit=eye+direction*distance
    local localHit=entry.panel.CFrame:PointToObjectSpace(hit)
    if distance>5.5 or math.abs(localHit.X)>entry.width*.5 or math.abs(localHit.Y)>entry.height*.5 then return false end
    local params=RaycastParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances={character,entry.panel.Parent}
    return workspace:Raycast(eye,hit-eye,params)==nil
end

local function recordedPose(history,when)
    for index=2,#history do
        local after=history[index]
        if after.time>=when then
            local before=history[index-1]
            return before.frames,after.frames,math.clamp((when-before.time)/(after.time-before.time),0,1)
        end
    end
    local last=history[#history].frames
    return last,last,0
end

local function anomalyPose(entry,character,record,camera,roundId,now)
    local episode=entry.episode
    if not episode or episode.record~=record or episode.round~=roundId then
        episode={record=record,round=roundId,history={}}
        entry.episode=episode
    end
    if not episode.started then
        if not lookingAtMirror(entry,camera,character) then episode.lookedAt=nil;return end
        episode.lookedAt=episode.lookedAt or now
        if now-episode.lookedAt<gazeTime then return end
        episode.started=now
    end
    local age=now-episode.started
    local freezeAt=normalTime+delayTime
    local releaseAt=freezeAt+frozenTime
    if age>=releaseAt+blendTime then return end
    if episode.frozen then
        return episode.frozen,nil,math.clamp((age-releaseAt)/blendTime,0,1)
    end
    local history=episode.history
    local frames={}
    for index,pair in ipairs(record.pairs) do frames[index]=pair.source.CFrame end
    table.insert(history,{time=age,frames=frames})
    while #history>2 and history[2].time<age-delay-.15 do table.remove(history,1) end
    if age<normalTime then return end
    if age>=freezeAt then
        local before,after,mix=recordedPose(history,freezeAt-delay)
        local frozen={}
        for index,frame in ipairs(before) do frozen[index]=frame:Lerp(after[index],mix) end
        episode.frozen=frozen
        table.clear(history)
        return frozen,nil,0
    end
    return recordedPose(history,age-delay*math.min(1,(age-normalTime)/.55))
end

for _,roomName in ipairs({"MEN","WOMEN"})do
    task.spawn(function()
        local room=rooms:WaitForChild(roomName,10)
        if not room then return end
        local function consider(panel)
            if panel.Name~="MirrorPanel" or not panel:IsA("BasePart")then return end
            local model=panel.Parent
            if model and wanted[model.Name]then mount(room,model,panel)end
        end
        room.DescendantAdded:Connect(consider)
        for i,p in ipairs(room:GetDescendants())do consider(p);if i%1000==0 then task.wait()end end
    end)
end
local elapsed=0
Run.RenderStepped:Connect(function(dt)
    elapsed+=dt;if elapsed<1/30 then return end;elapsed=0
    local camera=workspace.CurrentCamera;if not camera then return end
    local eye=camera.CFrame.Position
    local inOffice=player:GetAttribute("KonturZone")=="Office"
    local roundId=inOffice and phase.Value=="Active" and round:GetAttribute("MirrorAnomalyRound")
    local now=os.clock()
    for _,entry in ipairs(entries)do
        local delta=eye-entry.origin
        local nearby=delta.Magnitude
        local distance=delta:Dot(entry.normal)
        local close=inOffice and distance>.35 and nearby<24
        local anomaly=roundId and entry.target and nearby<7.5
        if not anomaly then entry.episode=nil end
        if close then
            entry.lastUsed=os.clock()
            if not entry.world and not entry.building then task.spawn(build,entry)end
        elseif entry.world and not entry.building and os.clock()-entry.lastUsed>4 then clear(entry)end
        local visible=close and entry.ready and camera.CFrame.LookVector:Dot(-entry.normal)>.03
        entry.gui.Enabled=visible
        if not visible and entry.episode and not entry.episode.started then entry.episode.lookedAt=nil end
        if visible then
            local right=(-entry.normal):Cross(entry.up).Unit
            local dx=delta:Dot(right)/entry.width
            local dy=-delta:Dot(entry.up)/entry.height
            local scale=math.max(1+2*math.abs(dx),1+2*math.abs(dy))
            local fov=math.deg(2*math.atan(scale*entry.height/(2*distance)))
            entry.viewport.Position=UDim2.fromScale((1-scale)*.5+dx,(1-scale)*.5+dy)
            entry.viewport.Size=UDim2.fromScale(scale,scale)
            entry.camera.FieldOfView=math.clamp(fov,1,120)
            entry.camera.CFrame=CFrame.lookAt(eye,eye-entry.normal,entry.up)
            for _,pair in ipairs(entry.parts)do
                if pair.source.Parent then
                    local cf=pair.source.CFrame
                    if cf~=pair.last then pair.clone.CFrame=reflectFrame(cf,entry.origin,entry.normal);pair.last=cf end
                    pair.clone.Transparency=pair.source.Transparency
                end
            end
            for _,p in ipairs(Players:GetPlayers())do
                local ch=p.Character;local root=ch and ch:FindFirstChild("HumanoidRootPart")
                if root and (root.Position-entry.origin).Magnitude<28 then addCharacter(entry,ch)end
            end
            for ch,record in pairs(entry.characters)do
                if not ch.Parent then record.model:Destroy();entry.characters[ch]=nil
                else
                    local before,after,mix
                    local humanoid=ch:FindFirstChildOfClass("Humanoid")
                    if anomaly and ch==player.Character and humanoid and humanoid.Health>0 then
                        before,after,mix=anomalyPose(entry,ch,record,camera,roundId,now)
                    end
                    for index,pair in ipairs(record.pairs)do
                        if pair.source.Parent and pair.clone.Parent then
                            local pose=pair.source.CFrame
                            if before then pose=before[index]:Lerp(after and after[index] or pose,mix) end
                            pair.clone.CFrame=reflectFrame(pose,entry.origin,entry.normal)
                            pair.clone.Transparency=pair.source.Transparency
                            pair.clone.LocalTransparencyModifier=0
                        end
                    end
                end
            end
        end
    end
end)
