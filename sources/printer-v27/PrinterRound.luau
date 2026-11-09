local function createPrinter(office,round,phase)
    local room=office.Rooms:FindFirstChild("CENTER")
    local printer=room and room:FindFirstChild("Printer")
    local slot=printer and printer:FindFirstChild("OutputSlot")
    local original=printer and printer:FindFirstChild("Paper")
    if not slot or not slot:IsA("BasePart") or not original or not original:IsA("BasePart") then
        return nil
    end

    local tweenService=game:GetService("TweenService")
    local facing=slot.CFrame.LookVector
    local paper=Instance.new("Part")
    paper.Name="AnomalyPrintout"
    paper.Size=original.Size
    paper.Color=original.Color
    paper.Material=Enum.Material.SmoothPlastic
    paper.Anchored=true
    paper.CanCollide=false
    paper.CanQuery=false
    paper.CanTouch=false
    local top=Instance.new("SurfaceGui")
    top.Name="Ink"
    top.Face=Enum.NormalId.Top
    top.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
    top.CanvasSize=Vector2.new(540,240)
    top.LightInfluence=.75
    top.Parent=paper
    local ink=Instance.new("TextLabel")
    ink.Size=UDim2.fromScale(.9,.8)
    ink.Position=UDim2.fromScale(.05,.1)
    ink.BackgroundTransparency=1
    ink.TextColor3=Color3.fromRGB(28,36,38)
    ink.Font=Enum.Font.RobotoMono
    ink.TextScaled=true
    ink.TextWrapped=true
    ink.Parent=top

    local savedTransparency=original.Transparency
    local feed
    local function reset()
        if feed then feed:Cancel();feed=nil end
        paper.Parent=nil
        original.Transparency=savedTransparency
    end

    local function printSheet(text)
        reset()
        original.Transparency=1
        ink.Text=text
        top.Enabled=false
        local length=original.Size.Z
        local start=slot.Position+facing*.025-Vector3.yAxis*.055
        local finish=slot.Position+facing*(length*.5+.023)
        finish=Vector3.new(finish.X,original.Position.Y,finish.Z)
        paper.Size=Vector3.new(original.Size.X,original.Size.Y,.016)
        paper.CFrame=CFrame.new(start)*original.CFrame.Rotation
        paper.Parent=printer
        local motion=tweenService:Create(paper,TweenInfo.new(1.5,Enum.EasingStyle.Linear),{
            CFrame=CFrame.new(finish)*original.CFrame.Rotation,Size=original.Size,
        })
        feed=motion
        motion:Play()
        local state=motion.Completed:Wait()
        if feed~=motion or state~=Enum.PlaybackState.Completed then return false end
        feed=nil
        top.Enabled=true
        return true
    end
    local anchor=Instance.new("Attachment")
    anchor.Name="PrinterWarningAnchor"
    anchor.Position=Vector3.new(0,-.09,-.49)
    anchor.Parent=slot
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="ReadPrinterWarning"
    prompt.ActionText="Прочитать предупреждение"
    prompt.ObjectText="Принтер"
    prompt.MaxActivationDistance=4.5
    prompt.Enabled=false
    prompt.Parent=anchor

    local board=Instance.new("BillboardGui")
    board.Name="PrinterWarningCard"
    board.Size=UDim2.fromOffset(330,92)
    board.StudsOffsetWorldSpace=Vector3.new(0,1.65,0)
    board.MaxDistance=11
    board.LightInfluence=0
    board.Enabled=false
    board.Parent=anchor
    local heading=Instance.new("TextLabel")
    heading.Size=UDim2.fromScale(1,1)
    heading.BackgroundColor3=Color3.fromRGB(233,228,207)
    heading.BackgroundTransparency=.05
    heading.BorderSizePixel=0
    heading.Font=Enum.Font.RobotoMono
    heading.TextSize=17
    heading.TextColor3=Color3.fromRGB(36,46,47)
    heading.TextWrapped=true
    heading.Parent=board

    local function eligible(player,limit)
        if phase.Value~="Active" or player:GetAttribute("KonturZone")~="Office" then return false end
        local character=player.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        local human=character and character:FindFirstChildOfClass("Humanoid")
        if not root or not human or human.Health<=0 then return false end
        local delta=root.Position-anchor.WorldPosition
        if delta.Magnitude>limit or delta:Dot(facing)<0 then return false end
        local eye=character:FindFirstChild("Head")
        if not eye then return false end
        local query=RaycastParams.new()
        query.FilterType=Enum.RaycastFilterType.Exclude
        query.FilterDescendantsInstances={character,printer}
        return workspace:Raycast(eye.Position,anchor.WorldPosition-eye.Position,query)==nil
    end

    local warning="ЧЕРЕЗ 5 СЕКУНД БУМАГА ПОДНИМЕТСЯ"
    local mode,revision="Off",0
    local function setMode(value)
        mode=value
        printer:SetAttribute("WarningPhase",value)
        prompt.Enabled=value=="Ready"
    end
    local function read(player)
        if mode~="Ready" or not eligible(player,4.8) then return false end
        setMode("Countdown")
        local ticket=revision
        local at=workspace:GetServerTimeNow()+5
        round:SetAttribute("PrinterPaperStartsAt",at)
        task.spawn(function()
            while revision==ticket do
                local seconds=math.ceil(at-workspace:GetServerTimeNow())
                if seconds<=0 then break end
                heading.Text=("ПРЕДУПРЕЖДЕНИЕ / %02d\nБумага поднимется со столов"):format(seconds)
                task.wait(.12)
            end
            if revision~=ticket then return end
            setMode("Paper")
            board.Enabled=false
        end)
        return true
    end
    prompt.Triggered:Connect(read)

    local function activate(on)
        revision+=1
        local ticket=revision
        board.Enabled=false
        round:SetAttribute("PrinterPaperStartsAt",nil)
        reset()
        setMode(on and "Waiting" or "Off")
        if not on then return end
        task.spawn(function()
            local seenAt
            while revision==ticket do
                local nearby=false
                for _,player in ipairs(game:GetService("Players"):GetPlayers()) do
                    if eligible(player,10) then nearby=true;break end
                end
                if nearby then
                    seenAt=seenAt or os.clock()
                    if os.clock()-seenAt>=.6 then break end
                else
                    seenAt=nil
                end
                task.wait(.15)
            end
            if revision~=ticket then return end
            setMode("Printing")
            if not printSheet("ПРЕДУПРЕЖДЕНИЕ\n"..warning) or revision~=ticket then return end
            heading.Text="ПРЕДУПРЕЖДЕНИЕ\n"..warning
            board.Enabled=true
            setMode("Ready")
        end)
    end
    return {activate=activate,read=read}
end
