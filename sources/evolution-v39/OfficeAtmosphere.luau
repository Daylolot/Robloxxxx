--!strict
-- v43: фоновая атмосфера и музыкальные стингеры (собственные звуки из audio/synth_horror.py, id подставляет сборщик).
-- Комнаты: ровный гул вентиляции (Vent) в рабочих залах и коридоре, далёкий офис (OfficeFar) в CENTER, EAST и NE; в NW, туалетах и
-- стартовой тишина, чтобы звук аномалии выделялся. Стингеры 2D (SoundService): верный ответ, неверный ответ и гибель игрока.
local function attachAtmosphere(office: Instance)
	local A: {[string]: number} = {}
	-- @@ATMOS_AUDIO@@
	if next(A) == nil then
		return
	end
	task.wait(6)
	local rooms = office:FindFirstChild("Rooms")
	local folder = Instance.new("Folder")
	folder.Name = "KonturAtmos"
	local function emit(key: string, at: Vector3, volume: number, minD: number, maxD: number)
		local id = A[key]
		if not id then
			return
		end
		local host = Instance.new("Part")
		host.Name = "Part"
		host.Anchored = true
		host.CanCollide = false
		host.CanQuery = false
		host.CanTouch = false
		host.Transparency = 1
		host.Size = Vector3.one * 0.2
		host.Position = at
		host.Parent = folder
		local sound = Instance.new("Sound")
		sound.SoundId = "rbxassetid://" .. tostring(id)
		sound.Volume = volume
		sound.Looped = true
		sound.RollOffMode = Enum.RollOffMode.InverseTapered
		sound.RollOffMinDistance = minD
		sound.RollOffMaxDistance = maxD
		sound.Parent = host
		-- разные места стартуют с разного момента, чтобы петли не совпадали
		sound.TimePosition = 0
		sound:Play()
	end
	local function centre(room: Instance): Vector3?
		local lo, hi = Vector3.new(1e9, 0, 1e9), Vector3.new(-1e9, 0, -1e9)
		for _, d in room:GetDescendants() do
			if d:IsA("BasePart") then
				lo = Vector3.new(math.min(lo.X, d.Position.X), 0, math.min(lo.Z, d.Position.Z))
				hi = Vector3.new(math.max(hi.X, d.Position.X), 0, math.max(hi.Z, d.Position.Z))
			end
		end
		if lo.X > hi.X then
			return nil
		end
		return Vector3.new((lo.X + hi.X) / 2, 8.5, (lo.Z + hi.Z) / 2)
	end
	if rooms then
		for _, name in {"WEST", "CENTER", "EAST", "NE"} do
			local room = rooms:FindFirstChild(name)
			local c = if room then centre(room) else nil
			if c then
				emit("Vent", c, 0.16, 8, 34)
				if name ~= "WEST" then
					emit("OfficeFar", c + Vector3.new(6, 0, 4), 0.2, 6, 36)
				end
			end
		end
	end
	for _, at in {Vector3.new(1004, 9, 20), Vector3.new(1004, 9, 46), Vector3.new(1060, 9, 20), Vector3.new(1060, 9, 46), Vector3.new(1032, 9, 4), Vector3.new(1032, 9, 62)} do
		emit("Vent", at, 0.14, 6, 26)
	end
	folder.Parent = office

	-- стингеры
	local SoundService = game:GetService("SoundService")
	local function sting(key: string, volume: number): Sound?
		local id = A[key]
		if not id then
			return nil
		end
		local sound = Instance.new("Sound")
		sound.Name = "Sting"
		sound.SoundId = "rbxassetid://" .. tostring(id)
		sound.Volume = volume
		sound.Parent = SoundService
		return sound
	end
	local level, wrong, death = sting("StingLevel", 0.55), sting("StingWrong", 0.7), sting("StingDeath", 0.85)
	local lastDeath = 0
	local state = office:FindFirstChild("AnomalyReportState")
	local result = state and state:FindFirstChild("ResultText")
	if result and result:IsA("StringValue") then
		result.Changed:Connect(function(text: string)
			local upper = string.upper(text)
			if upper == "" then
				return
			end
			if string.find(upper, "НЕВЕРНО", 1, true) or string.find(upper, "ОШИБКА", 1, true) or string.find(upper, "ВОЗВРАТ", 1, true) then
				task.delay(0.4, function()
					if wrong and os.clock() - lastDeath > 2.5 then
						wrong:Play()
					end
				end)
			elseif string.sub(upper, 1, 6) == "ВЕРНО" or string.find(upper, "ВЕРНО", 1, true) then
				if level then
					level:Play()
				end
			end
		end)
	end
	local Players = game:GetService("Players")
	local function watch(player: Player)
		player.CharacterAdded:Connect(function(character)
			local humanoid = character:WaitForChild("Humanoid", 10)
			if humanoid and humanoid:IsA("Humanoid") then
				humanoid.Died:Connect(function()
					lastDeath = os.clock()
					if death then
						death:Play()
					end
				end)
			end
		end)
		if player.Character then
			local humanoid = player.Character:FindFirstChildOfClass("Humanoid")
			if humanoid then
				humanoid.Died:Connect(function()
					lastDeath = os.clock()
					if death then
						death:Play()
					end
				end)
			end
		end
	end
	for _, player in Players:GetPlayers() do
		watch(player)
	end
	Players.PlayerAdded:Connect(watch)
end

return attachAtmosphere
