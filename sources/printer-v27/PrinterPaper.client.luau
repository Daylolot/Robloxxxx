-- The round's server timestamp gives every client the same sheet paths.
task.spawn(function()
    local players=game:GetService("Players")
    local run=game:GetService("RunService")
    local player=players.LocalPlayer
    local office=workspace:WaitForChild("OfficeMap")
    local state=office:WaitForChild("AnomalyReportState")
    local phase=state:WaitForChild("Phase")
    local randomSeed=2705
    local sources={
        Vector3.new(1053.40,3.711,42),
        Vector3.new(1037.24,4.23,47.68),
        Vector3.new(1022.28,3.484,47.69),
        Vector3.new(1017.84,3.526,46.49),
        Vector3.new(1036.83,3.472,17.49),
    }
    local count=42
    local scene,sheets,sounds
    local activeAt
    local soundSlots={
        {sheet=1,id="rbxassetid://9125724963",at=0,volume=.33,speed=1.16},
        {sheet=4,id="rbxassetid://9117233449",at=.65,volume=.23,speed=1.18},
        {sheet=8,id="rbxassetid://9117233311",at=1.55,volume=.24,speed=1.17},
    }

    local function ease(value)
        local t=math.clamp(value,0,1)
        return t*t*(3-2*t)
    end

    local function makeScene()
        scene=Instance.new("Folder")
        scene.Name="PrinterPaperFlight"
        scene.Parent=office
        sheets=table.create(count)
        local random=Random.new(randomSeed)
        for index=1,count do
            local originIndex=(index-1)%#sources+1
            local origin=sources[originIndex]+Vector3.new(random:NextNumber(-.32,.32),index*.001,random:NextNumber(-.18,.18))
            local width=random:NextNumber(.52,.74)
            local length=random:NextNumber(.73,1.03)
            local tone=random:NextInteger(0,24)
            local parts=table.create(2)
            for face=1,2 do
                local part=Instance.new("Part")
                part.Name=("Sheet_%02d_%d"):format(index,face)
                part.Size=Vector3.new(width,.012,length*.5)
                part.Color=Color3.fromRGB(244-tone,242-tone,225-tone)
                part.Material=Enum.Material.SmoothPlastic
                part.Anchored=true
                part.CanCollide=false
                part.CanTouch=false
                part.CanQuery=false
                part.CastShadow=false
                parts[face]=part
            end
            local column=(index-1)%6
            local row=math.floor((index-1)/6)
            local target=Vector3.new(1013+column*7.35+random:NextNumber(-1.2,1.2),
                random:NextNumber(6.5,8),13+row*6.5+random:NextNumber(-1.5,1.5))
            local drop=0
            if column==2 and row%2==1 then
                target=Vector3.new(1030,6.7,target.Z)
                drop=random:NextNumber(.85,1.45)
            end
            local delay=(originIndex-1)*.31+random:NextNumber(0,.55)
            local drift=random:NextNumber(4.2,6.9)
            local angle=random:NextNumber(0,math.pi*2)
            sheets[index]={origin=origin,target=target,length=length,parts=parts,
                delay=delay,drift=drift,angle=angle,drop=drop}
        end
        sounds={}
        local preload={}
        for index,spec in ipairs(soundSlots) do
            local sound=Instance.new("Sound")
            sound.Name="PaperRustle"
            sound.SoundId=spec.id
            sound.Volume=spec.volume
            sound.PlaybackSpeed=spec.speed
            sound.RollOffMinDistance=3
            sound.RollOffMaxDistance=26
            sound.Parent=sheets[spec.sheet].parts[1]
            sounds[index]={sound=sound,last=-1}
            table.insert(preload,sound)
        end
        task.spawn(function()
            pcall(game:GetService("ContentProvider").PreloadAsync,game:GetService("ContentProvider"),preload)
        end)
    end

    local function placeSheet(sheet,age)
        local t=age-sheet.delay
        local start=sheet.origin
        local a=sheet.angle
        local lift=ease((t-.72)/1.85)
        local spread=ease((t-1.9)/sheet.drift)
        local flutter=math.sin(t*8+a)
        local shake=math.sin(t*28+a)
        local center=start:Lerp(Vector3.new(start.X,7,start.Z),lift):Lerp(sheet.target,spread)
        local float=lift*(.45+.55*spread)
        center+=Vector3.new(math.sin(t*.7+a)*1.1*float,
            .012*math.abs(shake)*(1-lift)+math.sin(t*1.4+a)*.28*float-sheet.drop*ease((spread-.84)/.16),
            math.cos(t*.83+a)*1.35*float)
        local rotation=CFrame.Angles(.024*shake*(1-lift)+float*(.28+flutter*.42),
            a+t*.44*lift,.018*flutter*(1-lift)+float*math.sin(t*2.1+a)*.62)
        local frame=CFrame.new(center)*rotation
        local bend=.045*shake*(1-lift)+float*flutter*.24
        for face,part in ipairs(sheet.parts) do
            local side=face==1 and -1 or 1
            part.CFrame=frame*CFrame.Angles(side*bend,0,0)*CFrame.new(0,0,side*sheet.length*.25)
            if not part.Parent then part.Parent=scene end
        end
    end

    local accumulated=0
    run.RenderStepped:Connect(function(dt)
        accumulated+=dt
        if accumulated<1/30 then return end
        accumulated=0
        local startsAt=phase.Value=="Active" and player:GetAttribute("KonturZone")=="Office"
            and state:GetAttribute("PrinterPaperStartsAt")
        if startsAt~=activeAt then
            if scene then
                for _,sheet in ipairs(sheets) do
                    for _,part in ipairs(sheet.parts) do part:Destroy() end
                end
                scene:Destroy()
                scene,sheets,sounds=nil,nil,nil
            end
            activeAt=startsAt
        end
        if not startsAt then return end
        local age=workspace:GetServerTimeNow()-startsAt
        if age< -2 then return end
        if not scene then makeScene() end
        if age<0 then return end
        for _,sheet in ipairs(sheets) do placeSheet(sheet,age) end
        for index,spec in ipairs(soundSlots) do
            local item=sounds[index]
            local elapsed=age-spec.at
            if elapsed>=0 then
                local cycle=math.floor(elapsed/7.4)
                if cycle~=item.last and item.sound.IsLoaded then
                    item.last=cycle
                    if elapsed%7.4<.8 then item.sound:Play() end
                end
            end
        end
    end)
end)
