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
    local soundSpecs = {
        {1, "rbxassetid://9125724963", 0, .33, 1.16},
        {35, "rbxassetid://9117233449", .38, .23, 1.18},
        {8, "rbxassetid://9117233311", 1.13, .24, 1.17},
    }
    local unpacked
    local scene, parts, frames, sounds

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
                part.Size = Vector3.new(sheet.width, .009, sheet.length / ribbonCount + .012)
                part.Color = Color3.fromRGB(244 - tone, 241 - tone, 226 - tone)
                part.Material = Enum.Material.SmoothPlastic
                part.Anchored = true
                part.CanCollide = false
                part.CanTouch = false
                part.CanQuery = false
                part.CastShadow = false
                part.CFrame = CFrame.new(1032, -2, 34)
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
                * CFrame.Angles(0, yaw, 0) * CFrame.Angles(0, 0, -roll) * CFrame.Angles(pitch, 0, 0)
            for ribbon = 1, ribbonCount do
                local a = (ribbon - 1) / ribbonCount - .5
                local b = ribbon / ribbonCount - .5
                local mid = (a + b) * .5
                local startHeight = curl * .164 * (a + .5)^3 + bow * .25 * a*a
                local endHeight = curl * .164 * (b + .5)^3 + bow * .25 * b*b
                local crossSlope = (curl * .06 * (mid + .5)^3 + twist * .26 * mid) / sheet.width
                local along = Vector3.new(0, endHeight - startHeight, -(b - a) * sheet.length).Unit
                local up = Vector3.new(1, crossSlope, 0):Cross(along).Unit
                local right = along:Cross(up)
                frames[(index - 1) * ribbonCount + ribbon] = base * CFrame.fromMatrix(
                    Vector3.new(0, (startHeight + endHeight) * .5 + fold * .29/12, -mid * sheet.length),
                    right, up, -along)
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
