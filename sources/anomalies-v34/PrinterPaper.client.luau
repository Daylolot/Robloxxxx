-- PRINTER_FLIGHT_DATA
-- PRINTER_DIRECTION
task.spawn(function()
    local RunService = game:GetService("RunService")
    local Players = game:GetService("Players")
    local ContentProvider = game:GetService("ContentProvider")
    local office = workspace:WaitForChild("OfficeMap")
    local state = office:WaitForChild("AnomalyReportState")
    local phase = state:WaitForChild("Phase")
    local player = Players.LocalPlayer
    local ribbonCount = 4
    local paperThickness = .007
    local printedSheets = {
        [1] = "СМЕНА", [7] = "АРХИВ", [8] = "ЖУРНАЛ", [12] = "СМЕНА",
        [16] = "ЖУРНАЛ", [18] = "АРХИВ", [21] = "СМЕНА", [25] = "АРХИВ",
        [29] = "ЖУРНАЛ", [33] = "СМЕНА", [36] = "АРХИВ", [40] = "ЖУРНАЛ",
        [43] = "АРХИВ", [46] = "ЖУРНАЛ", [54] = "СМЕНА", [58] = "ЖУРНАЛ",
    }
    local formFields = {
        ["СМЕНА"] = {{"СЕКТОР", "04"}, {"ОБХОД", "17:40"}, {"СТАТУС", "ПРИНЯТО"}},
        ["АРХИВ"] = {{"ПАПКА", "В-17"}, {"КОПИЯ", "02 / 03"}, {"ХРАНЕНИЕ", "СТЕЛЛАЖ 4"}},
        ["ЖУРНАЛ"] = {{"ЗАПИСЬ", "№ 118"}, {"ОТДЕЛ", "КОНТРОЛЬ"}, {"ВРЕМЯ", "19:05"}},
    }
    local unpacked
    local scene, parts, frames, sounds
    local message, messageLeaves, encounter, receiptRound
    local receiptQuery=RaycastParams.new()
    receiptQuery.FilterType=Enum.RaycastFilterType.Exclude
    local receiptBounds=OverlapParams.new()
    receiptBounds.FilterType=Enum.RaycastFilterType.Exclude
    receiptBounds.MaxParts=1
    local retryAt=0
    local officeCenter=Vector3.new(1032,5,34)
    local chords = table.create(ribbonCount)

    local function printSection(part, title, ribbon)
        local ink = Instance.new("SurfaceGui")
        ink.Name = "FormInk"
        ink.Face = Enum.NormalId.Top
        ink.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
        ink.CanvasSize = Vector2.new(54, 168)
        ink.MaxDistance = 14
        ink.LightInfluence = .8
        local layout = Instance.new("Frame")
        layout.AnchorPoint = Vector2.new(.5, .5)
        layout.Position = UDim2.fromScale(.5, .5)
        layout.Size = UDim2.fromOffset(168, 54)
        layout.Rotation = -90
        layout.BackgroundTransparency = 1
        layout.Parent = ink

        local function line(y, color)
            local mark = Instance.new("Frame")
            mark.BackgroundColor3 = color
            mark.BorderSizePixel = 0
            mark.Position = UDim2.fromScale(.12, y)
            mark.Size = UDim2.new(.76, 0, 0, 2)
            mark.Parent = layout
        end

        local function label(text, x, y, width, color, size)
            local label = Instance.new("TextLabel")
            label.BackgroundTransparency = 1
            label.Position = UDim2.fromScale(x, y)
            label.Size = UDim2.fromScale(width, .55)
            label.Font = Enum.Font.GothamMedium
            label.Text = text
            label.TextColor3 = color
            label.TextSize = size
            label.TextXAlignment = Enum.TextXAlignment.Left
            label.Parent = layout
        end

        local accent = Color3.fromRGB(65, 92, 90)
        local gray = Color3.fromRGB(122, 125, 117)
        if ribbon == 1 then
            label("КОНТУР  /  " .. title, .12, .08, .76, accent, 12)
            line(.76, accent)
        else
            local fields = formFields[title][ribbon - 1]
            label(fields[1], .12, .12, .35, gray, 10)
            label(fields[2], .48, .12, .4, accent, 11)
            line(.73, gray)
        end
        ink.Parent = part
    end

    local function makeScene()
        if not unpacked then
            unpacked = table.create(#flight.sheets)
            for index, sheet in ipairs(flight.sheets) do
                unpacked[index] = buffer.fromstring((sheet.data:gsub("..", function(hex)
                    return string.char(tonumber(hex, 16))
                end)))
            end
        end
        scene = Instance.new("Folder")
        scene.Name = "PrinterPaperFlight"
        scene.Parent = office
        parts = table.create(#flight.sheets * ribbonCount)
        frames = table.create(#flight.sheets * ribbonCount)
        for index, sheet in ipairs(flight.sheets) do
            local tone = (index % 5) * 4
            for ribbon = 1, ribbonCount do
                local part = Instance.new("Part")
                part.Name = ("Sheet_%02d_%d"):format(index, ribbon)
                part.Size = Vector3.new(sheet.width, paperThickness, sheet.length / ribbonCount + .002)
                part.Color = Color3.fromRGB(244 - tone, 241 - tone, 226 - tone)
                part.Material = Enum.Material.SmoothPlastic
                part.Anchored = true
                part.CanCollide = false
                part.CanTouch = false
                part.CanQuery = false
                part.CastShadow = false
                part.CFrame = CFrame.new(1032, -2, 34)
                if printedSheets[index] then
                    printSection(part, printedSheets[index], ribbon)
                end
                part.Parent = scene
                table.insert(parts, part)
            end
        end
        message = Instance.new("Folder")
        message.Name = "ReceiptEncounter"
        message.Parent = scene
        messageLeaves = {}
        for i,text in ipairs({"ПОДТВЕРДИТЕ","ПОЛУЧЕНИЕ"}) do
            local leaf=Instance.new("Part")
            leaf.Name="ReceiptHalf"..i
            leaf.Size=Vector3.new(1.14,.34,.008)
            leaf.Color=Color3.fromRGB(232,226,205)
            leaf.Anchored=true; leaf.CanCollide=false; leaf.CanQuery=false; leaf.CanTouch=false
            leaf.CastShadow=false; leaf.Transparency=1
            leaf.Parent=message
            local gui=Instance.new("SurfaceGui")
            gui.Face=Enum.NormalId.Front
            gui.LightInfluence=.45
            gui.CanvasSize=Vector2.new(344,104)
            gui.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
            gui.Enabled=false
            gui.Parent=leaf
            local function printLine(value,x,y,w,h,font,color)
                local label=Instance.new("TextLabel")
                label.Size=UDim2.fromScale(w,h)
                label.Position=UDim2.fromScale(x,y)
                label.BackgroundTransparency=1
                label.Font=font
                label.TextScaled=true
                label.Text=value
                label.TextColor3=color
                label.Parent=gui
                return label
            end
            local ink=Color3.fromRGB(35,55,53)
            local seal=Color3.fromRGB(136,57,47)
            printLine(text,.08,i==1 and .47 or .04,.84,.47,Enum.Font.GothamBold,ink)
            if i==1 then
                printLine("ВХОДЯЩЕЕ",.09,.10,.40,.29,Enum.Font.GothamBold,ink)
                printLine("№ 047",.70,.10,.23,.29,Enum.Font.GothamBold,ink)
            else
                local stamp=printLine("ОЖИДАЕТСЯ",.54,.58,.36,.30,Enum.Font.GothamBold,seal)
                stamp.Rotation=-5
                local border=Instance.new("UIStroke")
                border.ApplyStrokeMode=Enum.ApplyStrokeMode.Border
                border.Color=seal; border.Thickness=1.4; border.Transparency=.24; border.Parent=stamp
                local signature=Instance.new("Frame")
                signature.BackgroundColor3=ink; signature.BackgroundTransparency=.32; signature.BorderSizePixel=0
                signature.Position=UDim2.fromScale(.11,.81); signature.Size=UDim2.new(.32,0,0,1)
                signature.Parent=gui
            end
            messageLeaves[i]={leaf,gui}
        end
        sounds = {}
        local preload = {}
        for index, spec in ipairs(rustleCues) do
            local name,sheet,asset,_,volume,speed,distance=table.unpack(spec)
            local sound = Instance.new("Sound")
            sound.Name = "Rustle"..name
            sound.SoundId = asset
            sound.Volume = volume
            sound.PlaybackSpeed = speed
            sound.RollOffMode = Enum.RollOffMode.LinearSquare
            sound.RollOffMinDistance = 2.8
            sound.RollOffMaxDistance = distance
            sound.Parent = parts[(sheet - 1) * ribbonCount + 1]
            sounds[index] = {sound = sound, last = -1}
            preload[index] = sound
        end
        task.spawn(function()
            pcall(ContentProvider.PreloadAsync, ContentProvider, preload)
        end)
    end

    local function component(bytes, offset, index, blend)
        local a = buffer.readi16(bytes, offset + index * 2)
        local b = buffer.readi16(bytes, offset + index * 2 + 20)
        return a + (b - a) * blend
    end

    local function fillFrames(age)
        local sample = math.max(0, age + flight.lead) * flight.rate
        local left = math.min(math.floor(sample), flight.count - 2)
        local offset = left * 20
        local endAge = math.max(0, sample - (flight.count - 1)) / flight.rate
        for index, sheet in ipairs(flight.sheets) do
            local blend = sample - left
            if endAge > 0 then
                local frequency = 1.8 + index % 7 * .23
                blend = 1 + math.sin(endAge * frequency) * flight.rate / frequency
            end
            local bytes = unpacked[index]
            local x = component(bytes, offset, 0, blend) / 1024
            local y = component(bytes, offset, 1, blend) / 1024
            local z = component(bytes, offset, 2, blend) / 1024
            if endAge > 0 then
                local t = math.min(1, endAge / 1.4)
                local envelope = t*t*(3 - 2*t)
                x += envelope * .36 * math.sin(endAge * 1.3 + index)
                z += envelope * .38 * math.cos(endAge * 1.17 + index)
            end
            local pitch = component(bytes, offset, 3, blend) / 2048
            local roll = component(bytes, offset, 4, blend) / 2048
            local yaw = component(bytes, offset, 5, blend) / 2048
            local curl = component(bytes, offset, 6, blend) / 4096
            local bow = component(bytes, offset, 7, blend) / 4096
            local fold = component(bytes, offset, 8, blend) / 4096
            local twist = component(bytes, offset, 9, blend) / 4096
            local base = CFrame.new(1032 + x, y, 34 + z)
                * CFrame.Angles(0, yaw, 0) * CFrame.Angles(0, 0, -roll)
                * CFrame.Angles(pitch, 0, twist * .11 + curl * .024)
            base,curl,bow = directPaper(index,age,base,curl,bow)
            local segmentLength = sheet.length / ribbonCount
            for ribbon = 1, ribbonCount do
                local a = (ribbon - 1) / ribbonCount - .5
                local b = ribbon / ribbonCount - .5
                local startHeight = curl * .164 * (a + .5)^3 + bow * .25 * a*a
                local endHeight = curl * .164 * (b + .5)^3 + bow * .25 * b*b
                chords[ribbon] = Vector3.new(0, endHeight - startHeight, -segmentLength).Unit * segmentLength
            end
            -- Keep the middle crease at the baked pose. Each edge is shared by both panels.
            local middle = Vector3.new(0, curl * .164 * .5^3 + fold * .29/12, 0)
            local edge = middle - chords[1] - chords[2]
            for ribbon = 1, ribbonCount do
                local chord = chords[ribbon]
                local along = chord / segmentLength
                local up = Vector3.xAxis:Cross(along)
                frames[(index - 1) * ribbonCount + ribbon] = base * CFrame.fromMatrix(
                    edge + chord * .5, Vector3.xAxis, up, -along)
                edge += chord
            end
        end
        workspace:BulkMoveTo(parts, frames, Enum.BulkMoveMode.FireCFrameChanged)
    end

    local function updateReceipt(age,startsAt)
        local camera = workspace.CurrentCamera
        local character = player.Character
        local head = character and character:FindFirstChild("Head")
        if not head or not camera then return end
        if not encounter and receiptRound~=startsAt and age>=4.65 and age<=9.3 and age>=retryAt then
            retryAt=age+.13
            local eye = head.Position
            if eye.X<1012 or eye.X>1051 or eye.Z<13 or eye.Z>54 then return end
            local look = camera.CFrame.LookVector
            local direction=Vector3.new(look.X,0,look.Z)
            if direction.Magnitude<.6 then return end
            direction=direction.Unit
            local finish=eye+direction*4.25
            local side=direction:Cross(Vector3.yAxis)
            local exit=finish+direction*.9+Vector3.yAxis*1.9
            local exclude={character,scene}
            receiptQuery.FilterDescendantsInstances=exclude
            receiptBounds.FilterDescendantsInstances=exclude
            if #workspace:GetPartBoundsInRadius(finish,.60,receiptBounds)>0 or workspace:Raycast(eye,finish-eye,receiptQuery)
                or workspace:Spherecast(finish,.59,exit-finish,receiptQuery) then return end
            local entry
            for _,sign in ipairs({1,-1}) do
                local candidate=finish+direction*1.5+side*(sign*2)+Vector3.yAxis*.7
                if not workspace:Spherecast(finish,.59,candidate-finish,receiptQuery) then
                    entry=candidate
                    break
                end
            end
            if not entry then return end
            receiptRound=startsAt
            encounter={age=age,entry=entry,finish=finish,exit=exit,eye=eye,turn=0,lastAge=age}
        end
        if not encounter then return end
        local t=age-encounter.age
        if message:GetAttribute("Phase")=="Done" then return end
        local finish=encounter.finish
        local distance=(head.Position-finish).Magnitude
        if not encounter.departed and t>=.86 and (distance<1.35 or distance>7.4) then
            encounter.departed=math.min(t,2.78)
        end
        local exitTime=encounter.departed or 2.78
        local leaving=t-exitTime
        local visible=leaving<.84
        local position=encounter.entry:Lerp(encounter.finish,ease(t/.86))
            :Lerp(encounter.exit,ease((leaving-.16)/.68))
        local base=CFrame.lookAt(position,encounter.eye)
        local eyeOffset=base:PointToObjectSpace(head.Position)
        local targetTurn=math.clamp(math.atan2(-eyeOffset.X,-eyeOffset.Z),-.36,.36)
        encounter.turn+=(targetTurn-encounter.turn)*(1-math.exp(-8*(age-encounter.lastAge)))
        encounter.lastAge=age
        local tracking=encounter.turn*ease(t/.86)*(1-ease(leaving/.48))
        local pose=base*CFrame.Angles(0,.91*(1-ease(t/.86))+tracking,.055*math.sin(t*4.1))
        local close=ease(leaving/.42)
        local fold=close*1.41+(1-close)*(.055+.025*math.sin(t*3.6))
        for index,item in ipairs(messageLeaves) do
            local side=index==1 and 1 or -1
            local leaf,gui=table.unpack(item)
            leaf.Transparency=visible and (1-ease(t/.19)+ease((leaving-.56)/.28)) or 1
            gui.Enabled=visible and t>.19 and leaving<.61
            leaf.CFrame=pose*CFrame.Angles(side*fold,0,0)*CFrame.new(0,side*.17,0)
        end
        message:SetAttribute("Phase",not visible and "Done" or t<.86 and "Approach" or leaving<0 and "Read" or "Fold")
    end

    local accumulated = 0
    local interval = 1/30
    local lastAge
    RunService.RenderStepped:Connect(function(dt)
        accumulated += dt
        if accumulated < interval then return end
        accumulated %= interval
        local active = phase.Value == "Active" and player:GetAttribute("KonturZone") == "Office"
            and state:GetAttribute("PrinterPaperPrimed")
        local character=player.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        local distance=root and (root.Position-officeCenter).Magnitude or math.huge
        if not active or distance>(scene and 53 or 47) then
            if scene then
                scene:Destroy()
                scene, parts, frames, sounds, lastAge = nil, nil, nil, nil, nil
                message, messageLeaves, encounter, retryAt = nil, nil, nil, 0
            end
            interval=1/12
            return
        end
        interval=distance>38 and 1/20 or 1/30
        if not scene then makeScene() end
        local startsAt = state:GetAttribute("PrinterPaperStartsAt")
        local age = startsAt and math.max(0, workspace:GetServerTimeNow() - startsAt) or 0
        if age == lastAge then return end
        lastAge = age
        fillFrames(age)
        if not startsAt or workspace:GetServerTimeNow() < startsAt then return end
        updateReceipt(age,startsAt)
        for index, spec in ipairs(rustleCues) do
            local item = sounds[index]
            local sinceCue=age-spec[4]
            if item.last<0 and sinceCue>=0 then
                if sinceCue>.36 then
                    item.last=1
                elseif item.sound.IsLoaded then
                    item.last=1
                    local offset=sinceCue*item.sound.PlaybackSpeed
                    if offset<item.sound.TimeLength then
                        item.sound.TimePosition=offset
                        item.sound:Play()
                    end
                end
            end
        end
    end)
end)
