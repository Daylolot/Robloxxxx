-- PRINTER_FLIGHT_DATA
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
    local soundSpecs = {
        {1, "rbxassetid://9125724963", 0, .33, 1.16},
        {35, "rbxassetid://9117233449", .38, .23, 1.18},
        {8, "rbxassetid://9117233311", 1.13, .24, 1.17},
    }
    local unpacked
    local scene, parts, frames, sounds
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
        sounds = {}
        local preload = {}
        for index, spec in ipairs(soundSpecs) do
            local sound = Instance.new("Sound")
            sound.Name = "PaperRustle"
            sound.SoundId = spec[2]
            sound.Volume = spec[4]
            sound.PlaybackSpeed = spec[5]
            sound.RollOffMinDistance = 3
            sound.RollOffMaxDistance = 26
            sound.Parent = parts[(spec[1] - 1) * ribbonCount + 1]
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

    local accumulated = 0
    local lastAge
    RunService.RenderStepped:Connect(function(dt)
        accumulated += dt
        if accumulated < 1/30 then return end
        accumulated %= 1/30
        local active = phase.Value == "Active" and player:GetAttribute("KonturZone") == "Office"
            and state:GetAttribute("PrinterPaperPrimed")
        if not active then
            if scene then
                scene:Destroy()
                scene, parts, frames, sounds, lastAge = nil, nil, nil, nil, nil
            end
            return
        end
        if not scene then makeScene() end
        local startsAt = state:GetAttribute("PrinterPaperStartsAt")
        local age = startsAt and math.max(0, workspace:GetServerTimeNow() - startsAt) or 0
        if age == lastAge then return end
        lastAge = age
        fillFrames(age)
        if not startsAt or workspace:GetServerTimeNow() < startsAt then return end
        for index, spec in ipairs(soundSpecs) do
            local item = sounds[index]
            local elapsed = age - spec[3]
            if elapsed >= 0 then
                local cycle = math.floor(elapsed / 7.4)
                if cycle ~= item.last and item.sound.IsLoaded then
                    item.last = cycle
                    if elapsed % 7.4 < .8 then item.sound:Play() end
                end
            end
        end
    end)
end)
