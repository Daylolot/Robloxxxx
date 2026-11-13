-- VENT_SPEC
-- DOOR_SPEC
local function createOfficeObjects(office, state)
    local TweenService=game:GetService("TweenService")
    local rooms=office:WaitForChild("Rooms")
    local archive=rooms:WaitForChild("NW")
    local west=rooms:WaitForChild("WEST")
    local first=archive:FindFirstChild("V09_0340_WorldTrade")
    local second=archive:FindFirstChild("V09_0341_GrowthTechnology")
    local calendar=archive:FindFirstChild("V09_0465_WallCalendar")
    local plant=west:FindFirstChild("V09_0348_WallPlanter")
    local colors={}
    if plant then
        for _,part in ipairs(plant:GetDescendants()) do
            if part:IsA("BasePart") and (part.Name=="LeafBlade" or part.Name=="TerminalLeaf" or part.Name=="LeafMidrib_Wire") then
                local color=part.Color
                colors[part]={color,Color3.fromRGB(83+color.G*185,18+color.R*95,54+color.B*118)}
            end
        end
    end
    local firstPose=first and first:GetPivot()
    local secondPose=second and second:GetPivot()
    local calendarPose=calendar and calendar:GetPivot()
    local hook
    if calendar then
        local loop=calendar:FindFirstChild("HangingLoop_Joint",true)
        if loop and loop:IsA("BasePart") then
            hook=Instance.new("Part")
            hook.Name="OldCalendarPin"
            hook.Shape=Enum.PartType.Cylinder
            hook.Material=Enum.Material.Metal
            hook.Color=Color3.fromRGB(86,82,69)
            hook.Size=Vector3.new(.022,.064,.064)
            hook.Anchored=true
            hook.CanCollide=false; hook.CanQuery=false; hook.CanTouch=false
            hook.CFrame=CFrame.new(calendarPose.Position.X,6.74,-.223)*CFrame.Angles(0,math.pi/2,0)
        end
    end
    local names={"ArchiveWriting","GreenVent","WhisperDoor"}
    if first and second then table.insert(names,"ArchiveArtSwap") end
    if calendar then table.insert(names,"ArchiveCalendarShift") end
    if next(colors) then table.insert(names,"WestPlanterColor") end

    local origin=CFrame.fromMatrix(ventMount,Vector3.zAxis,Vector3.yAxis,-Vector3.xAxis)
    local housing=Instance.new("Model")
    housing.Name="MaintenanceVent"
    housing.Parent=office
    local hinge=Instance.new("Model")
    hinge.Name="HingedLouvers"
    hinge.Parent=housing
    for _,spec in ipairs(ventParts) do
        local name,x,y,z,w,h,d,r,g,b,moving,angle=table.unpack(spec)
        local part=Instance.new("Part")
        part.Name=name
        part.Size=Vector3.new(w,h,d)*ventScale
        part.Color=Color3.fromRGB(r,g,b)
        part.Material=name=="DuctShadow" and Enum.Material.SmoothPlastic or Enum.Material.Metal
        part.Anchored=true
        part.CanCollide=false
        part.CanTouch=false
        part.CanQuery=false
        part.CastShadow=false
        part.CFrame=origin*CFrame.new(x*ventScale,y*ventScale,-z*ventScale)*CFrame.Angles(angle,0,0)
        part.Parent=moving and hinge or housing
    end
    local hingePose=origin*CFrame.new(-.97*ventScale,0,-.17*ventScale)
    hinge.WorldPivot=hingePose
    local front=Instance.new("Part")
    front.Name="MaintenanceLabel"
    front.Anchored=true
    front.CanQuery=false; front.CanCollide=false; front.CanTouch=false
    front.Size=Vector3.new(.96,.22,.025)*ventScale
    front.Material=Enum.Material.Metal
    front.Color=Color3.fromRGB(182,182,159)
    front.CFrame=origin*CFrame.new(-.27*ventScale,-1.185*ventScale,-.095*ventScale)
    front.Parent=housing
    local tag=Instance.new("SurfaceGui")
    tag.Face=Enum.NormalId.Front; tag.CanvasSize=Vector2.new(280,64); tag.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
    tag.LightInfluence=.78; tag.MaxDistance=18; tag.Parent=front
    local text=Instance.new("TextLabel")
    text.Size=UDim2.fromScale(1,1); text.BackgroundTransparency=1
    text.Text="ВЫТЯЖКА   В-04"; text.TextColor3=Color3.fromRGB(41,53,47)
    text.TextScaled=true; text.Font=Enum.Font.GothamBold; text.Parent=tag

    local door
    local function setDoor(present)
        if not present then
            if door then door:Destroy(); door=nil end
            return
        end
        door=Instance.new("Model")
        door.Name="UnlistedServiceDoor"
        local basis=CFrame.fromMatrix(doorMount,Vector3.zAxis,Vector3.yAxis,-Vector3.xAxis)
        local lever=Instance.new("Model")
        lever.Name="DoorLever"
        lever.WorldPivot=basis*CFrame.new(-1.48,4.43,-.236)
        lever:SetAttribute("RestPose",lever.WorldPivot)
        lever.Parent=door
        for _,spec in ipairs(doorParts) do
            local name,u,y,n,w,h,d,r,g,b,metal=table.unpack(spec)
            local piece=Instance.new("Part")
            piece.Name=name
            piece.Size=Vector3.new(w,h,d)
            piece.CFrame=basis*CFrame.new(u,y,-n)
            piece.Color=Color3.fromRGB(r,g,b)
            piece.Material=metal and Enum.Material.Metal or Enum.Material.SmoothPlastic
            piece.Anchored=true
            piece.CanCollide=false; piece.CanQuery=false; piece.CanTouch=false
            piece.Parent=(name=="Lever" or name=="LeverTip") and lever or door
        end
        local tag=Instance.new("SurfaceGui")
        tag.Name="ServiceLabel"; tag.Face=Enum.NormalId.Front
        tag.CanvasSize=Vector2.new(400,86); tag.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
        tag.LightInfluence=.8; tag.MaxDistance=18; tag.Parent=door.SignPlate
        local text=Instance.new("TextLabel")
        text.Size=UDim2.fromScale(.86,.78); text.Position=UDim2.fromScale(.07,.11)
        text.BackgroundTransparency=1; text.Font=Enum.Font.GothamMedium
        text.Text="СЛУЖЕБНАЯ"; text.TextColor3=Color3.fromRGB(38,52,47)
        text.TextScaled=true; text.Parent=tag
        door.Parent=office
    end

    local angle=Instance.new("NumberValue")
    local move
    angle:GetPropertyChangedSignal("Value"):Connect(function()
        hinge:PivotTo(hingePose*CFrame.Angles(0,angle.Value,0))
    end)
    local activeScenario
    local function activate(scenario, round)
        if scenario==activeScenario and scenario~=nil then return end
        if first and second then
            local swapped=scenario=="ArchiveArtSwap"
            first:PivotTo(swapped and secondPose*CFrame.Angles(0,0,math.rad(-2.7)) or firstPose)
            second:PivotTo(swapped and firstPose*CFrame.Angles(0,0,math.rad(1.8)) or secondPose)
        end
        if calendar then
            local displaced=calendarPose+Vector3.new(2.45,-.51,0)
            local moved=scenario=="ArchiveCalendarShift"
            calendar:PivotTo(moved and displaced or calendarPose)
            if hook then hook.Parent=moved and archive or nil end
        end
        for part,finish in pairs(colors) do
            part.Color=scenario=="WestPlanterColor" and finish[2] or finish[1]
        end
        if scenario=="WhisperDoor" or activeScenario=="WhisperDoor" then
            setDoor(scenario=="WhisperDoor")
        end
        if scenario=="GreenVent" or activeScenario=="GreenVent" then
            if move then move:Cancel() end
            move=TweenService:Create(angle,TweenInfo.new(.75,Enum.EasingStyle.Sine),{Value=scenario=="GreenVent" and math.rad(16) or 0})
            move:Play()
        end
        activeScenario=scenario
        state:SetAttribute("OfficeDetailStartedAt",scenario and workspace:GetServerTimeNow() or nil)
        state:SetAttribute("OfficeDetailRound",round)
        state:SetAttribute("OfficeDetailScenario",scenario)
    end
    return {activate=activate,names=names}
end
