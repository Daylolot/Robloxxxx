-- VENT_SPEC
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
            if part:IsA("BasePart") and part.Color.G>part.Color.R*1.2 and part.Color.G>part.Color.B*1.17 then
                colors[part]=part.Color
            end
        end
    end
    local firstPose=first and first:GetPivot()
    local secondPose=second and second:GetPivot()
    local calendarPose=calendar and calendar:GetPivot()
    local names={"ArchiveWriting","GreenVent"}
    if first and second then table.insert(names,"ArchiveArtSwap") end
    if calendar then table.insert(names,"ArchiveCalendarShift") end
    if next(colors) then table.insert(names,"WestPlanterColor") end

    local origin=CFrame.fromMatrix(Vector3.new(1000.2,4.82,45.8),Vector3.zAxis,Vector3.yAxis,-Vector3.xAxis)
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
        part.Size=Vector3.new(w,h,d)
        part.Color=Color3.fromRGB(r,g,b)
        part.Material=name=="DuctShadow" and Enum.Material.SmoothPlastic or Enum.Material.Metal
        part.Anchored=true
        part.CanCollide=false
        part.CanTouch=false
        part.CanQuery=false
        part.CastShadow=false
        part.CFrame=origin*CFrame.new(x,y,-z)*CFrame.Angles(angle,0,0)
        part.Parent=moving and hinge or housing
    end
    local hingePose=origin*CFrame.new(-.97,0,-.17)
    hinge.WorldPivot=hingePose
    local front=Instance.new("Part")
    front.Name="MaintenanceLabel"
    front.Anchored=true
    front.CanQuery=false; front.CanCollide=false; front.CanTouch=false
    front.Size=Vector3.new(.96,.22,.025)
    front.Material=Enum.Material.Metal
    front.Color=Color3.fromRGB(182,182,159)
    front.CFrame=origin*CFrame.new(-.27,-1.185,-.095)
    front.Parent=housing
    local tag=Instance.new("SurfaceGui")
    tag.Face=Enum.NormalId.Front; tag.CanvasSize=Vector2.new(280,64); tag.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
    tag.LightInfluence=.78; tag.MaxDistance=18; tag.Parent=front
    local text=Instance.new("TextLabel")
    text.Size=UDim2.fromScale(1,1); text.BackgroundTransparency=1
    text.Text="ВЫТЯЖКА   В-04"; text.TextColor3=Color3.fromRGB(41,53,47)
    text.TextScaled=true; text.Font=Enum.Font.GothamBold; text.Parent=tag

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
            first:PivotTo(swapped and secondPose or firstPose)
            second:PivotTo(swapped and firstPose or secondPose)
        end
        if calendar then
            local displaced=calendarPose+Vector3.new(2.45,.58,0)
            calendar:PivotTo(scenario=="ArchiveCalendarShift" and displaced or calendarPose)
        end
        for part,color in pairs(colors) do
            part.Color=scenario=="WestPlanterColor" and Color3.fromRGB(math.clamp(88+color.G*240,0,255),24+color.R*65,78+color.B*85) or color
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
