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
    entry.parts={};entry.characters={};entry.ready=false;entry.hanging=false
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
    if entry.characters[character] then return entry.characters[character] end
    if not character:FindFirstChild("HumanoidRootPart") then return end
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
    local record={model=clone,pairs=pairs}
    entry.characters[character]=record
    return record
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

local corner=Vector3.new(1033.4,9.30,74)

local function hangingPose(entry,character,record)
    local root=character:FindFirstChild("HumanoidRootPart")
    local joints={}
    for _,joint in ipairs(character:GetDescendants()) do
        if joint:IsA("JointInstance") and joint.Part0 and joint.Part1 then
            joints[joint.Part1]=joint
        end
    end
    local frames={[root]=CFrame.identity}
    local function rest(part)
        if frames[part] then return frames[part] end
        -- A detached accessory can still use its current offset from the avatar.
        frames[part]=root.CFrame:ToObjectSpace(part.CFrame)
        local joint=joints[part]
        if joint and joint.Part0:IsDescendantOf(character) then
            local offset=joint.C0
            local side=part.Name=="LeftUpperArm" and -1 or part.Name=="RightUpperArm" and 1
                or part.Name=="Left Arm" and -1 or part.Name=="Right Arm" and 1
            if side then
                offset=CFrame.new(offset.Position)*CFrame.Angles(0,0,side*math.rad(152))*offset.Rotation
            end
            frames[part]=rest(joint.Part0)*offset*joint.C1:Inverse()
        end
        return frames[part]
    end
    local rotation=CFrame.lookAt(Vector3.zero,-entry.normal)*CFrame.Angles(0,0,math.pi)
    local poses={}
    local top=-math.huge
    for index,pair in ipairs(record.pairs) do
        local pose=rotation*rest(pair.source)
        local size=pair.source.Size
        local extent=(math.abs(pose.RightVector.Y)*size.X+math.abs(pose.UpVector.Y)*size.Y
            +math.abs(pose.LookVector.Y)*size.Z)*.5
        if pair.source.Name=="LeftFoot" or pair.source.Name=="RightFoot"
            or pair.source.Name=="Left Leg" or pair.source.Name=="Right Leg" then
            top=math.max(top,pose.Position.Y+extent)
        end
        poses[index]=pose
    end
    if top==-math.huge then return false end
    local anchor=corner-Vector3.yAxis*top
    for index,pair in ipairs(record.pairs) do
        pair.clone.CFrame=reflectFrame(poses[index]+anchor,entry.origin,entry.normal)
        pair.clone.Transparency=pair.source.Transparency
    end
    return true
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
    local anomalyActive=inOffice and phase.Value=="Active" and round:GetAttribute("MirrorAnomalyRound")~=nil
    for _,entry in ipairs(entries)do
        local delta=eye-entry.origin
        local nearby=delta.Magnitude
        local distance=delta:Dot(entry.normal)
        local close=inOffice and distance>.35 and nearby<24
        if close then
            entry.lastUsed=os.clock()
            if not entry.world and not entry.building then task.spawn(build,entry)end
        elseif entry.world and not entry.building and os.clock()-entry.lastUsed>4 then clear(entry)end
        local visible=close and entry.ready and camera.CFrame.LookVector:Dot(-entry.normal)>.03
        entry.gui.Enabled=visible
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
            local hanging=anomalyActive and entry.target
            if entry.hanging~=hanging then
                for _,record in pairs(entry.characters) do record.model:Destroy() end
                table.clear(entry.characters)
                entry.hanging=hanging
            end
            if hanging then
                local ch=player.Character
                for other,record in pairs(entry.characters) do
                    if other~=ch then record.model:Destroy();entry.characters[other]=nil end
                end
                if ch and ch:FindFirstChild("HumanoidRootPart") then
                    local record=addCharacter(entry,ch)
                    if record and not record.hanging then
                        record.hanging=hangingPose(entry,ch,record)
                        if not record.hanging then
                            record.model:Destroy()
                            entry.characters[ch]=nil
                        end
                    end
                end
            else
                for _,p in ipairs(Players:GetPlayers())do
                    local ch=p.Character;local root=ch and ch:FindFirstChild("HumanoidRootPart")
                    if root and (root.Position-entry.origin).Magnitude<28 then addCharacter(entry,ch)end
                end
                for ch,record in pairs(entry.characters)do
                    if not ch.Parent then record.model:Destroy();entry.characters[ch]=nil
                    else
                        for _,pair in ipairs(record.pairs)do
                            if pair.source.Parent and pair.clone.Parent then
                                pair.clone.CFrame=reflectFrame(pair.source.CFrame,entry.origin,entry.normal)
                                pair.clone.Transparency=pair.source.Transparency
                                pair.clone.LocalTransparencyModifier=0
                            end
                        end
                    end
                end
            end
        end
    end
end)
