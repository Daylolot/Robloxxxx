--!strict
-- v43: десять хоррор-аномалий со звуком. Серверный модуль в духе OfficePropAnomalies: сценарий включается/выключается функцией
-- (scenario, round) -> handled; имена сценариев добавляются в `names`, пока для них найдены нужные предметы/комнаты.
-- Всё созданное лежит в папке KonturHorror внутри карты и убирается при смене сценария; изменённые предметы возвращаются.
-- Звуки: встроенные rbxasset://sounds/* (дыхание = плавание, шаги, гул = взрыв на скорости 0,1–0,5, стон = oof на скорости 0,2–0,35),
-- к каждому подключены Reverb и Equalizer (глухо и гулко). Свои аудиофайлы не загружались.
local function attachHorrorAnomalies(office: Instance, names: {string}): (string?, number?) -> boolean
	local TweenService = game:GetService("TweenService")
	local rooms = office:FindFirstChild("Rooms")
	local rng = Random.new()
	local folder = Instance.new("Folder")
	folder.Name = "Misc" -- нейтральное имя: папка реплицируется клиентам
	folder.Parent = office
	local SND = {
		breath = "rbxasset://sounds/action_swim.mp3",
		step = "rbxasset://sounds/action_footsteps_plastic.mp3",
		boom = "rbxasset://sounds/impact_explosion_03.mp3",
		groan = "rbxasset://sounds/oof.ogg",
		drop = "rbxasset://sounds/impact_water.mp3",
		blip = "rbxasset://sounds/volume_slider.ogg",
	}
	local AUDIO: {[string]: number} = {}
	-- @@HORROR_AUDIO@@
	local token = 0
	local undo: {() -> ()} = {}
	local isStudio = game:GetService("RunService"):IsStudio()

	local findCache: {[string]: {Model}} = {}
	local function find(pattern: string): {Model}
		local cached = findCache[pattern]
		if not cached then
			cached = {}
			for _, item in office:GetDescendants() do
				if item:IsA("Model") and string.find(item.Name, pattern) and not item:IsDescendantOf(folder) then
					table.insert(cached, item)
				end
			end
			findCache[pattern] = cached
		end
		local list: {Model} = {}
		for _, item in cached do
			if item.Parent then
				table.insert(list, item)
			end
		end
		return list
	end
	local function mark(position: Vector3)
		if isStudio then
			office:SetAttribute("QATargetPos", position) -- только Studio: куда вести тестировщика
			office:SetAttribute("QATargetLook", Vector3.zAxis)
		end
	end
	local function newPart(parent: Instance, name: string, size: Vector3, cframe: CFrame, color: Color3, transparency: number?): Part
		local part = Instance.new("Part")
		part.Name = "Part" -- нейтральное имя: части реплицируются клиентам, тип аномалии по имени не должен читаться
		part.Size = size
		part.CFrame = cframe
		part.Color = color
		part.Material = Enum.Material.SmoothPlastic
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
		part.Transparency = transparency or 0
		part.Parent = parent
		return part
	end
	-- Звуки аномалий слышно только тому, кто находится в той же комнате, что и источник (стены в Roblox звук не глушат, поэтому громкость
	-- гасится вручную: раз в 0,25 с источник сопоставляется с комнатой по полу, а игроки с комнатами по положению). Громкость задаёт атрибут Gain
	-- (скрипты сближения меняют его, а не Volume), итоговая Volume = Gain * плавный коэффициент комнаты.
	local roomBoxes: {{name: string, x0: number, x1: number, z0: number, z1: number}} = {}
	local floorsFolder = office:FindFirstChild("Floors")
	if floorsFolder then
		for _, room in floorsFolder:GetChildren() do
			if room.Name ~= "V09FloorSupport" then
				local x0, x1, z0, z1 = math.huge, -math.huge, math.huge, -math.huge
				for _, d in room:GetDescendants() do
					if d:IsA("BasePart") then
						x0, x1 = math.min(x0, d.Position.X - d.Size.X / 2), math.max(x1, d.Position.X + d.Size.X / 2)
						z0, z1 = math.min(z0, d.Position.Z - d.Size.Z / 2), math.max(z1, d.Position.Z + d.Size.Z / 2)
					end
				end
				if x0 < x1 then
					table.insert(roomBoxes, {name = room.Name, x0 = x0, x1 = x1, z0 = z0, z1 = z1})
				end
			end
		end
	end
	local function roomNameAt(p: Vector3): string?
		for _, r in roomBoxes do
			if p.X >= r.x0 and p.X <= r.x1 and p.Z >= r.z0 and p.Z <= r.z1 then
				return r.name
			end
		end
		return nil
	end
	local gated: {{sound: Sound, level: number}} = {}
	local gateRunning = false
	local function startGate()
		if gateRunning then
			return
		end
		gateRunning = true
		task.spawn(function()
			while true do
				local here: {[string]: boolean} = {}
				for _, player in game:GetService("Players"):GetPlayers() do
					local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
					if root and root:IsA("BasePart") then
						local name = roomNameAt(root.Position)
						if name then
							here[name] = true
						end
					end
				end
				for i = #gated, 1, -1 do
					local entry = gated[i]
					local sound = entry.sound
					local host = sound.Parent
					if not host or not sound:IsDescendantOf(workspace) then
						table.remove(gated, i)
					else
						local pos = if host:IsA("BasePart") then host.Position else nil
						local name = if pos then roomNameAt(pos) else nil
						local target = if name == nil or here[name] then 1 else 0
						entry.level += (target - entry.level) * 0.4
						local gain = sound:GetAttribute("Gain")
						sound.Volume = (if type(gain) == "number" then gain else 1) * entry.level
					end
				end
				task.wait(0.25)
			end
		end)
	end
	local function makeSound(parent: Instance, id: string, volume: number, speed: number, looped: boolean, raw: boolean?): Sound
		local sound = Instance.new("Sound")
		sound.SoundId = id
		sound.Volume = 0 -- до первой проверки комнаты не слышно
		sound:SetAttribute("Gain", volume)
		table.insert(gated, {sound = sound, level = 0})
		task.defer(startGate) -- после того как звук получит родителя (иначе первый проход считает его удалённым)
		sound.PlaybackSpeed = speed
		sound.Looped = looped
		sound.RollOffMode = Enum.RollOffMode.InverseTapered
		sound.RollOffMinDistance = 10
		sound.RollOffMaxDistance = 45
		if raw then
			sound.Parent = parent -- собственные звуки уже обработаны (гулкие, тёмные): эффекты не нужны
			return sound
		end
		local reverb = Instance.new("ReverbSoundEffect")
		reverb.DecayTime = 4
		reverb.Density = 0.9
		reverb.Diffusion = 0.9
		reverb.DryLevel = -4
		reverb.WetLevel = 2
		reverb.Parent = sound
		local eq = Instance.new("EqualizerSoundEffect")
		eq.LowGain = 4
		eq.MidGain = -8
		eq.HighGain = -18
		eq.Parent = sound
		sound.Parent = parent
		return sound
	end

	-- свой звук (синтез из audio/synth_horror.py) или встроенный запасной
	local function voice(parent: Instance, key: string, builtin: string, bVol: number, bSpeed: number, cVol: number, cSpeed: number, looped: boolean): Sound
		local custom = AUDIO[key]
		if custom then
			return makeSound(parent, "rbxassetid://" .. tostring(custom), cVol, cSpeed, looped, true)
		end
		return makeSound(parent, builtin, bVol, bSpeed, looped)
	end
	-- сердцебиение растёт при приближении игрока, у порога срабатывает резкий удар (раз за раунд)
	local function armProximity(myToken: number, pos: Vector3, radius: number)
		if not (AUDIO.Heartbeat or AUDIO.Stinger) then
			return
		end
		local anchor = newPart(folder, "Part", Vector3.one * 0.2, CFrame.new(pos), Color3.new(), 1)
		local beat = if AUDIO.Heartbeat then makeSound(anchor, "rbxassetid://" .. tostring(AUDIO.Heartbeat), 0, 1, true, true) else nil
		local sting = if AUDIO.Stinger then makeSound(anchor, "rbxassetid://" .. tostring(AUDIO.Stinger), 0.5, 1, false, true) else nil
		if beat then
			beat.RollOffMaxDistance = 50
			beat:Play()
		end
		if sting then
			sting.RollOffMaxDistance = 50
		end
		task.spawn(function()
			local fired = false
			while token == myToken do
				local nearest = math.huge
				for _, player in game:GetService("Players"):GetPlayers() do
					local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
					if root and root:IsA("BasePart") then
						nearest = math.min(nearest, (root.Position - pos).Magnitude)
					end
				end
				if beat then
					beat:SetAttribute("Gain", math.clamp((radius * 2 - nearest) / (radius * 2), 0, 1) * 0.6)
				end
				if sting and not fired and nearest < radius then
					fired = true
					sting:Play()
				end
				task.wait(0.2)
			end
		end)
	end

	-- комнаты лежат в папках (не в Model): границы считаем по центрам их частей один раз и запоминаем
	local extents: {[Instance]: {lo: Vector3, hi: Vector3}} = {}
	local function roomBox(room: Instance): {lo: Vector3, hi: Vector3}
		local cached = extents[room]
		if cached then
			return cached
		end
		local lo, hi = Vector3.new(1e9, 0, 1e9), Vector3.new(-1e9, 0, -1e9)
		for _, part in room:GetDescendants() do
			if part:IsA("BasePart") then
				lo = Vector3.new(math.min(lo.X, part.Position.X), 0, math.min(lo.Z, part.Position.Z))
				hi = Vector3.new(math.max(hi.X, part.Position.X), 0, math.max(hi.Z, part.Position.Z))
			end
		end
		local box = {lo = lo, hi = hi}
		if lo.X <= hi.X then -- комнату без частей не запоминаем и не используем
			extents[room] = box
		end
		return box
	end
	local function roomCentre(room: Instance): Vector3
		local box = roomBox(room)
		return (box.lo + box.hi) / 2
	end

	-- свободная точка пола в комнате (или любой, кроме стартовой): нет крупных предметов и стен в радиусе 1,9
	local overlap = OverlapParams.new()
	local function floorSpot(): (Vector3?, Instance?)
		if not rooms then
			return nil, nil
		end
		local list: {Instance} = {}
		for _, room in rooms:GetChildren() do
			if room.Name ~= "StartRoom" then
				table.insert(list, room)
			end
		end
		for _ = 1, 40 do
			if #list == 0 then
				break
			end
			local room = list[rng:NextInteger(1, #list)]
			local box = roomBox(room)
			if box.lo.X > box.hi.X then
				table.remove(list, table.find(list, room))
				continue
			end
			local x = box.lo.X + 3 + rng:NextNumber() * math.max(box.hi.X - box.lo.X - 6, 1)
			local z = box.lo.Z + 3 + rng:NextNumber() * math.max(box.hi.Z - box.lo.Z - 6, 1)
			local hit = workspace:Raycast(Vector3.new(x, 9, z), Vector3.new(0, -12, 0))
			if hit and hit.Position.Y < 0.6 then
				local clear = true
				for _, part in workspace:GetPartBoundsInRadius(Vector3.new(x, 2.6, z), 1.9, overlap) do
					if part.CanCollide and part.Transparency < 1 and part.Size.Y > 0.6 and part.Size.Y < 20 and not part:IsDescendantOf(folder) then
						clear = false
						break
					end
				end
				if clear then
					return Vector3.new(x, hit.Position.Y, z), room
				end
			end
		end
		return nil, nil
	end

	-- тёмная фигура из частей (рост около 6,5 стада), лицом к точке
	local function buildFigure(parent: Instance, position: Vector3, lookAt: Vector3, lift: number): Model
		local model = Instance.new("Model")
		model.Name = "Model"
		local black = Color3.fromRGB(8, 8, 10)
		local origin = position + Vector3.new(0, lift, 0)
		local flat = Vector3.new(lookAt.X - position.X, 0, lookAt.Z - position.Z)
		local base = if flat.Magnitude > 0.1 then CFrame.lookAt(origin, origin + flat) else CFrame.new(origin)
		local function limb(name: string, size: Vector3, offset: Vector3)
			newPart(model, name, size, base * CFrame.new(offset), black, 0.04)
		end
		limb("LegL", Vector3.new(0.7, 3.1, 0.7), Vector3.new(-0.5, 1.55, 0))
		limb("LegR", Vector3.new(0.7, 3.1, 0.7), Vector3.new(0.5, 1.55, 0))
		limb("Torso", Vector3.new(1.9, 2.7, 0.95), Vector3.new(0, 4.45, 0))
		limb("ArmL", Vector3.new(0.5, 3.0, 0.5), Vector3.new(-1.25, 4.1, 0))
		limb("ArmR", Vector3.new(0.5, 3.0, 0.5), Vector3.new(1.25, 4.1, 0))
		local head = newPart(model, "Head", Vector3.new(1.25, 1.35, 1.25), base * CFrame.new(0, 6.5, 0), black, 0.04)
		head.Shape = Enum.PartType.Ball
		for _, x in {-0.28, 0.28} do
			local eye = newPart(model, "Eye", Vector3.new(0.16, 0.1, 0.05), base * CFrame.new(x, 6.55, -0.6), Color3.fromRGB(235, 235, 220))
			eye.Material = Enum.Material.Neon
		end
		model.Parent = parent
		return model
	end

	local function clear()
		token += 1
		for i = #undo, 1, -1 do
			local ok, err = pcall(undo[i])
			if not ok then
				warn("KONTUR horror undo failed: " .. tostring(err))
			end
		end
		table.clear(undo)
		folder:ClearAllChildren()
	end

	-- цикл на потоке, живёт, пока токен не изменился
	local function loop(myToken: number, interval: number, step: (number) -> ())
		task.spawn(function()
			local elapsed = 0
			while token == myToken do
				step(elapsed)
				local dt = task.wait(interval)
				elapsed += dt
			end
		end)
	end

	local scenarios: {[string]: (number) -> boolean} = {}

	-- 1. Дыхание из шкафа: красноватый пульсирующий свет и глухое дыхание
	scenarios.BreathingCabinet = function(myToken: number): boolean
		local cabinets = find("ArchiveCabinet$")
		for _, extra in find("FormsCabinet$") do
			table.insert(cabinets, extra)
		end
		if #cabinets == 0 then
			return false
		end
		local cabinet = cabinets[rng:NextInteger(1, #cabinets)]
		local position = cabinet:GetBoundingBox().Position
		mark(position)
		local anchor = newPart(folder, "BreathSource", Vector3.one * 0.2, CFrame.new(position), Color3.new(), 1)
		voice(anchor, "Breath", SND.breath, 1.2, 0.3, 0.9, 1, true):Play()
		local light = Instance.new("PointLight")
		light.Color = Color3.fromRGB(255, 70, 50)
		light.Range = 9
		light.Shadows = false
		light.Parent = anchor
		loop(myToken, 0.1, function(t: number)
			light.Brightness = 0.35 + 0.35 * (0.5 + 0.5 * math.sin(t * 1.7))
		end)
		return true
	end

	-- 2. Медленные шаги без шагающего: источник звука ходит по комнате
	scenarios.SlowFootsteps = function(myToken: number): boolean
		local a, room = floorSpot()
		if not (a and room) then
			return false
		end
		local b: Vector3? = nil
		for _ = 1, 8 do
			local candidate = floorSpot()
			if candidate and (candidate - a).Magnitude > 14 then
				b = candidate
				break
			end
		end
		if not b then
			return false
		end
		mark(a)
		local anchor = newPart(folder, "StepSource", Vector3.one * 0.2, CFrame.new(a + Vector3.new(0, 1, 0)), Color3.new(), 1)
		local stepSound = voice(anchor, "Footstep", SND.step, 1.4, 0.55, 1.2, 0.9, AUDIO.Footstep == nil)
		stepSound:Play()
		if AUDIO.Footstep then
			task.spawn(function()
				while token == myToken do
					stepSound:Play()
					task.wait(1.15)
				end
			end)
		end
		task.spawn(function()
			local going = true
			while token == myToken do
				local target = if going then b else a
				local tween = TweenService:Create(anchor, TweenInfo.new(((target :: Vector3) - anchor.Position).Magnitude / 2.2, Enum.EasingStyle.Linear), {Position = (target :: Vector3) + Vector3.new(0, 1, 0)})
				table.insert(undo, function()
					tween:Cancel()
				end)
				tween:Play()
				tween.Completed:Wait()
				going = not going
				task.wait(2.5)
			end
		end)
		return true
	end

	-- 3. Тёмный силуэт в углу комнаты, смотрит на вход, низкий гул
	scenarios.ShadowFigure = function(myToken: number): boolean
		local spot, room = floorSpot()
		if not (spot and room) then
			return false
		end
		mark(spot)
		local centre = roomCentre(room)
		local model = buildFigure(folder, spot, centre, 0)
		local anchor = newPart(folder, "HumSource", Vector3.one * 0.2, CFrame.new(spot + Vector3.new(0, 4, 0)), Color3.new(), 1)
		voice(anchor, "Drone", SND.boom, 0.9, 0.12, 0.8, 1, true):Play()
		armProximity(myToken, spot + Vector3.new(0, 3, 0), 11)
		return true
	end

	-- 4. Повешенная фигура под потолком, качается, скрип
	scenarios.HangingFigure = function(myToken: number): boolean
		local spot, room = floorSpot()
		if not (spot and room) then
			return false
		end
		mark(spot + Vector3.new(0, 5, 0))
		local centre = roomCentre(room)
		local pivotPoint = Vector3.new(spot.X, 10.6, spot.Z)
		local holder = Instance.new("Model")
		holder.Name = "Model"
		holder.Parent = folder
		local rope = newPart(holder, "Rope", Vector3.new(0.12, 3.2, 0.12), CFrame.new(pivotPoint - Vector3.new(0, 1.6, 0)), Color3.fromRGB(70, 60, 45))
		local figure = buildFigure(holder, Vector3.new(spot.X, 0, spot.Z), centre, 0)
		-- подтянуть фигуру вверх: ступни на 1,3 над полом, шея у верёвки
		local lowered = pivotPoint.Y - 3.1 - 6.7
		figure:PivotTo(figure:GetPivot() + Vector3.new(0, lowered, 0))
		local anchor = newPart(folder, "CreakSource", Vector3.one * 0.2, CFrame.new(pivotPoint), Color3.new(), 1)
		voice(anchor, "Creak", SND.groan, 0.9, 0.22, 0.9, 1, true):Play()
		armProximity(myToken, pivotPoint - Vector3.new(0, 3.5, 0), 10)
		local restRope, restFigure = rope:GetPivot(), figure:GetPivot()
		loop(myToken, 0.05, function(t: number)
			local swing = CFrame.new(pivotPoint) * CFrame.Angles(0, 0, math.rad(7) * math.sin(t * 0.9)) * CFrame.new(-pivotPoint)
			rope:PivotTo(swing * restRope)
			figure:PivotTo(swing * restFigure)
		end)
		return true
	end

	-- 5. Красные глаза в чёрном сгустке тьмы: пара светящихся глаз смотрит в центр комнаты, моргает, низкий рык
	scenarios.RedEyes = function(myToken: number): boolean
		local spot, room = floorSpot()
		if not (spot and room) then
			return false
		end
		local centre = roomCentre(room)
		local at = spot + Vector3.new(0, 2.2, 0)
		mark(at)
		local toCentre = Vector3.new(centre.X - at.X, 0, centre.Z - at.Z)
		local facing = if toCentre.Magnitude > 0.1 then toCentre.Unit else Vector3.zAxis
		local base = CFrame.lookAt(at, at + facing)
		local blobs: {Part} = {}
		local offsets: {Vector3} = {}
		for i = 1, 7 do
			local radius = rng:NextNumber(1.2, 2.0)
			local off = Vector3.new(rng:NextNumber(-0.45, 0.45), rng:NextNumber(-0.9, 0.9), rng:NextNumber(-0.45, 0.45))
			local blob = newPart(folder, "Void", Vector3.one * radius, CFrame.new(at + off), Color3.fromRGB(2, 2, 3), rng:NextNumber(0.2, 0.5))
			blob.Shape = Enum.PartType.Ball
			table.insert(blobs, blob)
			table.insert(offsets, off)
		end
		local void = blobs[1]
		loop(myToken, 0.06, function(t: number)
			for i, blob in blobs do
				local off = offsets[i]
				blob.Position = at + off + Vector3.new(math.sin(t * 1.3 + i) * 0.25, math.sin(t * 0.9 + i * 2) * 0.35, math.cos(t * 1.1 + i) * 0.25)
			end
		end)
		local pair: {Part} = {}
		for _, x in {-0.42, 0.42} do
			local eye = newPart(folder, "Eye", Vector3.new(0.4, 0.22, 0.12), base * CFrame.new(x, 0.45, -1.75), Color3.fromRGB(255, 25, 15))
			eye.Material = Enum.Material.Neon
			table.insert(pair, eye)
		end
		local light = Instance.new("PointLight")
		light.Color = Color3.fromRGB(255, 20, 10)
		light.Range = 6
		light.Brightness = 0.8
		light.Shadows = false
		light.Parent = pair[1]
		voice(void, "Breath", SND.breath, 1.0, 0.18, 1.0, 0.75, true):Play()
		armProximity(myToken, at, 9)
		task.spawn(function()
			while token == myToken do
				task.wait(rng:NextNumber(2, 6))
				if token ~= myToken then
					return
				end
				for _, eye in pair do
					eye.Transparency = 1
				end
				light.Enabled = false
				task.wait(0.18)
				for _, eye in pair do
					eye.Transparency = 0
				end
				light.Enabled = true
			end
		end)
		return true
	end

	-- 6. Телефон на столе звонит сам: серия быстрых сигналов, пауза
	scenarios.PhoneRingsAlone = function(myToken: number): boolean
		local phones = find("Telephone$")
		if #phones == 0 then
			return false
		end
		local phone = phones[rng:NextInteger(1, #phones)]
		local position = phone:GetBoundingBox().Position
		mark(position)
		local anchor = newPart(folder, "RingSource", Vector3.one * 0.2, CFrame.new(position), Color3.new(), 1)
		local blip = makeSound(anchor, SND.blip, 1.6, 3.4, false)
		blip.RollOffMaxDistance = 80
		task.spawn(function()
			while token == myToken do
				for _ = 1, 3 do
					for _ = 1, 7 do
						if token ~= myToken then
							return
						end
						blip:Play()
						task.wait(0.085)
					end
					task.wait(0.22)
				end
				task.wait(2.4)
			end
		end)
		return true
	end

	-- 7. Три глухих удара сверху: тёмное пятно на плитке вздрагивает, сыплется пыль
	scenarios.CeilingKnocks = function(myToken: number): boolean
		local spot = floorSpot()
		if not spot then
			return false
		end
		local at = Vector3.new(spot.X, 10.4, spot.Z)
		mark(at)
		local stain = newPart(folder, "Stain", Vector3.new(3.4, 0.08, 3.4), CFrame.new(at - Vector3.new(0, 0.03, 0)), Color3.fromRGB(58, 46, 36), 0.3)
		stain.Shape = Enum.PartType.Cylinder
		stain.Orientation = Vector3.new(0, 0, 90)
		stain.Size = Vector3.new(0.08, 2.6, 2.6)
		local anchor = newPart(folder, "KnockSource", Vector3.one * 0.2, CFrame.new(at), Color3.new(), 1)
		local knock = voice(anchor, "Knock", SND.boom, 1.0, 0.7, 1.0, 1, false)
		local dust = Instance.new("ParticleEmitter")
		dust.Rate = 0
		dust.Lifetime = NumberRange.new(1.2, 2)
		dust.Speed = NumberRange.new(0.5, 1.5)
		dust.Size = NumberSequence.new(0.6, 1.4)
		dust.Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 1)})
		dust.Color = ColorSequence.new(Color3.fromRGB(190, 190, 180))
		dust.Acceleration = Vector3.new(0, -2, 0)
		dust.EmissionDirection = Enum.NormalId.Bottom
		dust.Parent = anchor
		task.spawn(function()
			while token == myToken do
				task.wait(rng:NextNumber(5, 9))
				for _ = 1, 3 do
					if token ~= myToken then
						return
					end
					knock:Play()
					dust:Emit(10)
					stain.Position = at - Vector3.new(0, 0.2, 0)
					task.wait(0.12)
					stain.Position = at - Vector3.new(0, 0.03, 0)
					task.wait(0.83)
				end
			end
		end)
		return true
	end

	-- 8. С потолка капает тёмно-красное, лужа растёт, звук капель
	scenarios.DrippingCeiling = function(myToken: number): boolean
		local spot = floorSpot()
		if not spot then
			return false
		end
		mark(spot)
		local top = Vector3.new(spot.X, 10.5, spot.Z)
		local blood = Color3.fromRGB(125, 6, 8)
		local puddle = newPart(folder, "Puddle", Vector3.new(0.03, 0.6, 0.6), CFrame.new(spot + Vector3.new(0, 0.1, 0)), blood)
		puddle.Shape = Enum.PartType.Cylinder
		puddle.Orientation = Vector3.new(0, 0, 90)
		puddle.Material = Enum.Material.SmoothPlastic
		puddle.Reflectance = 0.15
		local anchor = newPart(folder, "DripSource", Vector3.one * 0.2, CFrame.new(spot + Vector3.new(0, 0.3, 0)), Color3.new(), 1)
		local splash = makeSound(anchor, SND.drop, 0.9, 1.5, false)
		task.spawn(function()
			local drops = 0
			while token == myToken do
				local drop = newPart(folder, "Drop", Vector3.new(0.22, 0.32, 0.22), CFrame.new(top), blood)
				drop.Shape = Enum.PartType.Ball
				local fall = TweenService:Create(drop, TweenInfo.new(0.75, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {Position = spot + Vector3.new(0, 0.15, 0)})
				fall:Play()
				fall.Completed:Wait()
				drop:Destroy()
				splash:Play()
				drops += 1
				local radius = math.min(0.6 + drops * 0.14, 2.6)
				puddle.Size = Vector3.new(0.03, radius * 2, radius * 2)
				task.wait(rng:NextNumber(1.2, 2.0))
			end
		end)
		return true
	end

	-- 9. Кресло само качается из стороны в сторону, скрип
	scenarios.RockingChair = function(myToken: number): boolean
		local chairs = find("ErgoChair$")
		if #chairs == 0 then
			return false
		end
		local chair = chairs[rng:NextInteger(1, #chairs)]
		local rest = chair:GetPivot()
		mark(rest.Position)
		table.insert(undo, function()
			if chair.Parent then
				chair:PivotTo(rest)
			end
		end)
		local anchor = newPart(folder, "CreakSource", Vector3.one * 0.2, CFrame.new(rest.Position + Vector3.new(0, 2, 0)), Color3.new(), 1)
		voice(anchor, "Creak", SND.groan, 0.6, 0.3, 0.55, 0.9, true):Play()
		loop(myToken, 0.05, function(t: number)
			if chair.Parent then
				chair:PivotTo(rest * CFrame.Angles(0, math.rad(32) * math.sin(t * 1.1), 0))
			end
		end)
		return true
	end

	-- 10. Монитор шепчет: чёрный экран с мигающей надписью, гул и стоны на фоне
	scenarios.WhisperMonitor = function(myToken: number): boolean
		local monitors: {Model} = {}
		for _, item in find("Monitor$") do
			if item:FindFirstChild("LCD") and (item:FindFirstChild("LCD") :: Instance):IsA("BasePart") then
				table.insert(monitors, item)
			end
		end
		if #monitors == 0 then
			return false
		end
		local monitor = monitors[rng:NextInteger(1, #monitors)]
		local lcdItem = monitor:FindFirstChild("LCD")
		if not (lcdItem and lcdItem:IsA("BasePart")) then
			return false
		end
		local lcd: BasePart = lcdItem
		mark(lcd.Position)
		local gui = Instance.new("SurfaceGui")
		gui.Name = "Display"
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
		gui.CanvasSize = Vector2.new(400, 240)
		gui.LightInfluence = 0
		gui.ZOffset = 5
		gui.Parent = lcd
		local back = Instance.new("Frame")
		back.Size = UDim2.fromScale(1, 1)
		back.BackgroundColor3 = Color3.fromRGB(4, 4, 5)
		back.BorderSizePixel = 0
		back.Parent = gui
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundTransparency = 1
		label.TextColor3 = Color3.fromRGB(190, 20, 20)
		label.Font = Enum.Font.RobotoMono
		label.TextScaled = true
		label.Text = "ПОДОЙДИ БЛИЖЕ"
		label.Parent = back
		table.insert(undo, function()
			gui:Destroy()
		end)
		local anchor = newPart(folder, "WhisperSource", Vector3.one * 0.2, CFrame.new(lcd.Position), Color3.new(), 1)
		voice(anchor, "Drone", SND.breath, 0.9, 0.2, 0.6, 1, true):Play()
		local whisper = voice(anchor, "Whisper", SND.groan, 0.45, 0.42, 0.8, 1, AUDIO.Whisper ~= nil)
		if AUDIO.Whisper then
			whisper:Play()
		end
		task.spawn(function()
			local phrases = {"ПОДОЙДИ БЛИЖЕ", "Я ВИЖУ ТЕБЯ", "НЕ ОГЛЯДЫВАЙСЯ", "ТЫ НЕ ОДИН"}
			local i = 0
			while token == myToken do
				i += 1
				label.Text = phrases[(i - 1) % #phrases + 1]
				label.Visible = true
				whisper:Play()
				task.wait(rng:NextNumber(1.6, 2.6))
				label.Visible = false
				task.wait(rng:NextNumber(0.2, 0.7))
			end
		end)
		return true
	end

	-- ===================== ТИХИЕ АНОМАЛИИ (без звука, мелкие детали) =====================
	local function freeAt(x: number, z: number, radius: number): number?
		local hit = workspace:Raycast(Vector3.new(x, 9, z), Vector3.new(0, -12, 0))
		if not (hit and hit.Position.Y < 0.6) then
			return nil
		end
		for _, p in workspace:GetPartBoundsInRadius(Vector3.new(x, 2.6, z), radius, overlap) do
			if p.CanCollide and p.Transparency < 1 and p.Size.Y > 0.6 and p.Size.Y < 20 and not p:IsDescendantOf(folder) then
				return nil
			end
		end
		return hit.Position.Y
	end
	local function pick(list: {Model}): Model
		return list[rng:NextInteger(1, #list)]
	end
	local function hideModel(model: Model)
		local parent = model.Parent
		model.Parent = nil
		table.insert(undo, function()
			if parent and parent:IsDescendantOf(office) then
				model.Parent = parent
			else
				warn("KONTUR hidden model could not be restored: " .. model.Name)
			end
		end)
	end
	local function lcdOf(model: Model): BasePart?
		local item = model:FindFirstChild("LCD")
		return if item and item:IsA("BasePart") then item else nil
	end

	-- 11. Пистолет под столом: тёмный предмет на полу в глубине под столешницей
	scenarios.HiddenPistol = function(_: number): boolean
		local desks = find("StraightDesk$")
		if #desks == 0 then
			return false
		end
		for _ = 1, 20 do
			local desk = pick(desks)
			local cf, size = desk:GetBoundingBox()
			local alongX = size.X > size.Z
			local long = math.max(size.X, size.Z)
			local s = rng:NextNumber(-1, 1) * (long / 2 - 0.8)
			local t = rng:NextNumber(-0.5, 0.5)
			local at = cf.Position + Vector3.new(if alongX then s else t, 0, if alongX then t else s)
			local x, z = at.X, at.Z
			local hit = workspace:Raycast(Vector3.new(x, 1.6, z), Vector3.new(0, -3, 0))
			local cover = workspace:Raycast(Vector3.new(x, 0.5, z), Vector3.new(0, 4, 0))
			if hit and hit.Position.Y < 0.6 and cover and cover.Instance:IsDescendantOf(desk) then
				local blocked = false
				for _, p in workspace:GetPartBoundsInRadius(Vector3.new(x, hit.Position.Y + 0.8, z), 0.45, overlap) do
					if p.CanCollide and p.Size.Y > 0.3 and not p:IsDescendantOf(folder) then
						blocked = true
						break
					end
				end
				if not blocked then
					local base = CFrame.new(x, hit.Position.Y + 0.09, z) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
					newPart(folder, "Part", Vector3.new(1.25, 0.2, 0.22), base, Color3.fromRGB(66, 70, 78)).Material = Enum.Material.Metal
					newPart(folder, "Part", Vector3.new(0.16, 0.14, 0.16), base * CFrame.new(0.66, 0, 0), Color3.fromRGB(20, 20, 22))
					newPart(folder, "Part", Vector3.new(0.28, 0.2, 0.6), base * CFrame.new(-0.4, 0, 0.38) * CFrame.Angles(0, math.rad(-12), 0), Color3.fromRGB(34, 34, 38))
					newPart(folder, "Part", Vector3.new(0.26, 0.14, 0.05), base * CFrame.new(-0.06, 0, 0.26), Color3.fromRGB(50, 52, 58))
					mark(Vector3.new(x, hit.Position.Y, z))
					return true
				end
			end
		end
		return false
	end

	-- 12. Капли крови у шкафа: цепочка тёмно-красных пятен уходит от шкафа
	scenarios.BloodDrops = function(_: number): boolean
		local cabinets = find("Cabinet$")
		if #cabinets == 0 then
			return false
		end
		local dirs = {Vector3.xAxis, -Vector3.xAxis, Vector3.zAxis, -Vector3.zAxis}
		for _ = 1, 25 do
			local cabinet = pick(cabinets)
			local origin = cabinet:GetPivot().Position
			local dir = dirs[rng:NextInteger(1, 4)]
			local start = origin + dir * 2.4
			local fy = freeAt(start.X, start.Z, 0.8)
			local clearTrail = fy ~= nil
			for i = 1, 6 do
				if clearTrail and not freeAt(start.X + dir.X * i * 0.8, start.Z + dir.Z * i * 0.8, 0.5) then
					clearTrail = false
				end
			end
			if fy and clearTrail then
				local blood = Color3.fromRGB(112, 6, 8)
				for i = 0, 6 do
					local d = 0.55 - i * 0.05
					local p = start + dir * (i * 0.8) + Vector3.new(rng:NextNumber(-0.15, 0.15), 0, rng:NextNumber(-0.15, 0.15))
					local drop = newPart(folder, "Part", Vector3.new(0.03, d, d), CFrame.new(p.X, fy + 0.04, p.Z) * CFrame.Angles(0, 0, math.rad(90)), blood)
					drop.Shape = Enum.PartType.Cylinder
					drop.Reflectance = 0.12
				end
				mark(Vector3.new(start.X, fy, start.Z))
				return true
			end
		end
		return false
	end

	-- 13. Красная кружка на столе, которой там не было
	scenarios.RedMug = function(_: number): boolean
		local desks = find("StraightDesk$")
		if #desks == 0 then
			return false
		end
		for _ = 1, 30 do
			local desk = pick(desks)
			local cf, size = desk:GetBoundingBox()
			local x = cf.Position.X + rng:NextNumber(-0.5, 0.5) * math.max(size.X - 0.6, 0.2)
			local z = cf.Position.Z + rng:NextNumber(-0.5, 0.5) * math.max(size.Z - 0.6, 0.2)
			local hit = workspace:Raycast(Vector3.new(x, 7, z), Vector3.new(0, -8, 0))
			local crowded = false
			if hit then
				for _, p in workspace:GetPartBoundsInRadius(Vector3.new(x, hit.Position.Y + 0.45, z), 0.4, overlap) do
					if not p:IsDescendantOf(desk) and not p:IsDescendantOf(folder) and p.Size.Y > 0.05 then
						crowded = true
						break
					end
				end
			end
			if hit and not crowded and hit.Instance:IsDescendantOf(desk) and hit.Normal.Y > 0.9 and hit.Position.Y > 2.5 then
				local y = hit.Position.Y
				local red = Color3.fromRGB(196, 28, 30)
				local body = newPart(folder, "Part", Vector3.new(0.5, 0.44, 0.44), CFrame.new(x, y + 0.25, z) * CFrame.Angles(0, 0, math.rad(90)), red)
				body.Shape = Enum.PartType.Cylinder
				local coffee = newPart(folder, "Part", Vector3.new(0.02, 0.36, 0.36), CFrame.new(x, y + 0.505, z) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(52, 30, 18))
				coffee.Shape = Enum.PartType.Cylinder
				newPart(folder, "Part", Vector3.new(0.09, 0.3, 0.07), CFrame.new(x + 0.27, y + 0.25, z), red)
				newPart(folder, "Part", Vector3.new(0.12, 0.07, 0.07), CFrame.new(x + 0.24, y + 0.38, z), red)
				newPart(folder, "Part", Vector3.new(0.12, 0.07, 0.07), CFrame.new(x + 0.24, y + 0.12, z), red)
				mark(Vector3.new(x, y, z))
				return true
			end
		end
		return false
	end

	-- 14. С одного стола пропала клавиатура
	scenarios.KeyboardGone = function(_: number): boolean
		local boards = find("^Keyboard$")
		if #boards == 0 then
			return false
		end
		local board = pick(boards)
		mark(board:GetPivot().Position)
		hideModel(board)
		return true
	end

	-- 15. Дверца архивного шкафа приоткрыта на узкую щель (закрытая поза запоминается один раз; подсказки дверцы выключены на время аномалии)
	local closedPose: {[Model]: CFrame} = {}
	local function ajarDoors(): {Model}
		local doors: {Model} = {}
		for _, cabinet in find("ArchiveCabinet$") do
			for _, child in cabinet:GetChildren() do
				if child:IsA("Model") and child.PrimaryPart then
					local angle = child:FindFirstChild("OpenAngle")
					if angle and (angle:IsA("NumberValue") or angle:IsA("IntValue")) then
						if not closedPose[child] then
							closedPose[child] = child:GetPivot()
						end
						if (child:GetPivot().Position - closedPose[child].Position).Magnitude < 0.05 then
							table.insert(doors, child)
						end
					end
				end
			end
		end
		return doors
	end
	scenarios.CabinetAjar = function(_: number): boolean
		local doors = ajarDoors()
		if #doors == 0 then
			return false
		end
		local door = pick(doors)
		local closed = closedPose[door]
		local angleValue = door:FindFirstChild("OpenAngle")
		if not (angleValue and (angleValue:IsA("NumberValue") or angleValue:IsA("IntValue"))) then
			return false
		end
		local angle = angleValue.Value
		local prompts: {ProximityPrompt} = {}
		for _, d in door:GetDescendants() do
			if d:IsA("ProximityPrompt") and d.Enabled then
				d.Enabled = false
				table.insert(prompts, d)
			end
		end
		table.insert(undo, function()
			for _, d in prompts do
				d.Enabled = true
			end
			if door.Parent then
				door:PivotTo(closed)
			end
		end)
		door:PivotTo(closed * CFrame.Angles(0, math.rad(angle * 0.16), 0))
		mark(door:GetPivot().Position)
		return true
	end

	-- 16. Со стены пропала картина: на её месте светлее прямоугольник
	scenarios.FrameMissing = function(_: number): boolean
		local frames = find("KD_Frame")
		if #frames == 0 then
			return false
		end
		for _ = 1, 20 do
			local frame = pick(frames)
			local cf, size = frame:GetBoundingBox()
			local alongX = size.Z < size.X
			local normal = if alongX then Vector3.zAxis else Vector3.xAxis
			local params = RaycastParams.new()
			params.FilterType = Enum.RaycastFilterType.Exclude
			params.FilterDescendantsInstances = {frame, folder}
			for _, sign in {1, -1} do
				local hit = workspace:Raycast(cf.Position, normal * sign * 1.2, params)
				if hit and (hit.Position - cf.Position).Magnitude < 0.9 and math.abs(hit.Normal:Dot(normal)) > 0.9 then
					local w = if alongX then size.X else size.Z
					local patchCf = CFrame.lookAt(hit.Position + hit.Normal * 0.012, hit.Position + hit.Normal * 2)
					local patch = newPart(folder, "Part", Vector3.new(w, size.Y, 0.02), patchCf, Color3.fromRGB(255, 255, 250), 0.4)
					patch.Material = Enum.Material.SmoothPlastic
					mark(cf.Position)
					hideModel(frame)
					return true
				end
			end
		end
		return false
	end

	-- 17. Грязные следы на ковре: цепочка отпечатков ботинок
	scenarios.MuddyFootprints = function(_: number): boolean
		for _ = 1, 12 do
			local a = floorSpot()
			if a then
				local ang = rng:NextNumber(0, math.pi * 2)
				local dir = Vector3.new(math.cos(ang), 0, math.sin(ang))
				local side = Vector3.new(-dir.Z, 0, dir.X)
				local points: {Vector3} = {}
				local okAll = true
				for i = 0, 9 do
					local p = a + dir * (i * 0.95) + side * (if i % 2 == 0 then 0.22 else -0.22)
					local fy = freeAt(p.X, p.Z, 0.5)
					if not fy then
						okAll = false
						break
					end
					table.insert(points, Vector3.new(p.X, fy, p.Z))
				end
				if okAll then
					for _, p in points do
						local at = CFrame.lookAt(p + Vector3.new(0, 0.03, 0), p + Vector3.new(0, 0.03, 0) + dir)
						local mud = Color3.fromRGB(72, 50, 34)
						newPart(folder, "Part", Vector3.new(0.3, 0.025, 0.5), at * CFrame.new(0, 0, -0.1), mud)
						newPart(folder, "Part", Vector3.new(0.22, 0.025, 0.2), at * CFrame.new(0, 0, 0.35), mud)
					end
					mark(a)
					return true
				end
			end
		end
		return false
	end

	-- 18. Жёлтая записка приклеена к монитору
	scenarios.StickyNote = function(_: number): boolean
		local screens: {BasePart} = {}
		for _, item in find("Monitor$") do
			local screen = lcdOf(item)
			if screen then
				table.insert(screens, screen)
			end
		end
		if #screens == 0 then
			return false
		end
		local lcd = screens[rng:NextInteger(1, #screens)]
		local note = newPart(folder, "Part", Vector3.new(0.55, 0.55, 0.02), lcd.CFrame * CFrame.new(lcd.Size.X / 2 - 0.38, lcd.Size.Y / 2 - 0.32, -(lcd.Size.Z / 2 + 0.012)) * CFrame.Angles(0, 0, math.rad(8)), Color3.fromRGB(250, 232, 100))
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
		gui.CanvasSize = Vector2.new(110, 110)
		gui.LightInfluence = 0.4
		gui.Parent = note
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundTransparency = 1
		label.TextColor3 = Color3.fromRGB(150, 24, 24)
		label.Font = Enum.Font.PermanentMarker
		label.TextScaled = true
		label.Text = "ПОМОГИ\nТЕ"
		label.Parent = gui
		mark(lcd.Position)
		return true
	end

	-- 19. В умывальнике течёт вода: тонкая струя из крана, лужица и тихий шум
	scenarios.FaucetRunning = function(_: number): boolean
		local basins = find("DoubleVanity$")
		for _, extra in find("WallBasin$") do
			table.insert(basins, extra)
		end
		local spouts: {BasePart} = {}
		for _, basin in basins do
			for _, d in basin:GetDescendants() do
				if d:IsA("BasePart") and d.Name == "Aerator" then
					table.insert(spouts, d)
				end
			end
		end
		if #spouts == 0 then
			return false
		end
		local spout = spouts[rng:NextInteger(1, #spouts)]
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Exclude
		params.FilterDescendantsInstances = {spout, folder}
		local hit = workspace:Raycast(spout.Position - Vector3.new(0, 0.1, 0), Vector3.new(0, -3, 0), params)
		if not hit then
			return false
		end
		local length = spout.Position.Y - hit.Position.Y - 0.05
		if length < 0.15 then
			return false
		end
		local stream = newPart(folder, "Part", Vector3.new(length, 0.09, 0.09), CFrame.new(spout.Position.X, spout.Position.Y - length / 2 - 0.02, spout.Position.Z) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(186, 222, 244), 0.45)
		stream.Shape = Enum.PartType.Cylinder
		local foam = newPart(folder, "Part", Vector3.new(0.02, 0.4, 0.4), CFrame.new(hit.Position + Vector3.new(0, 0.02, 0)) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(235, 245, 250), 0.5)
		foam.Shape = Enum.PartType.Cylinder
		local sound = makeSound(stream, SND.drop, 0.3, 2.6, true)
		sound.RollOffMaxDistance = 28
		sound:Play()
		mark(spout.Position)
		return true
	end

	-- 20. Брошенный портфель на полу
	scenarios.AbandonedBriefcase = function(_: number): boolean
		local spot = floorSpot()
		if not spot then
			return false
		end
		local base = CFrame.new(spot.X, spot.Y + 0.24, spot.Z) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
		local body = newPart(folder, "Part", Vector3.new(1.45, 0.42, 0.98), base, Color3.fromRGB(70, 48, 34))
		body.Material = Enum.Material.Leather
		newPart(folder, "Part", Vector3.new(0.5, 0.06, 0.08), base * CFrame.new(0, 0.24, 0), Color3.fromRGB(40, 28, 20))
		for _, x in {-0.45, 0.45} do
			newPart(folder, "Part", Vector3.new(0.1, 0.06, 0.1), base * CFrame.new(x, 0.22, 0.46), Color3.fromRGB(186, 150, 70)).Material = Enum.Material.Metal
		end
		body.CanCollide = true
		body.CanQuery = true
		mark(spot)
		return true
	end

	-- ===================== ЕЩЁ ДЕСЯТЬ ТИХИХ АНОМАЛИЙ (мелкие отличия) =====================
	local SMALL_ITEMS = {"DocumentStacks$", "OpenFolder$", "WorkNotebooks$", "Calculator$", "LooseSheets$", "Newspaper$", "Markers$", "Pencils$", "Rulers$", "EmployeeResume$"}
	local function smallItem(): Model?
		local list: {Model} = {}
		for _, pattern in SMALL_ITEMS do
			for _, item in find(pattern) do
				table.insert(list, item)
			end
		end
		return if #list > 0 then pick(list) else nil
	end
	local function movePivot(model: Model, cf: CFrame)
		local rest = model:GetPivot()
		table.insert(undo, function()
			if model.Parent then
				model:PivotTo(rest)
			end
		end)
		model:PivotTo(cf)
	end
	local function colorOfPlant(part: BasePart): boolean
		local c = part.Color
		return c.G > c.R * 1.15 and c.G > c.B * 1.15 and part.Name ~= "PlacementPivot"
	end

	-- 21. Предмет на столе повёрнут на 180°
	scenarios.ItemRotated = function(_: number): boolean
		local item = smallItem()
		if not item then
			return false
		end
		mark(item:GetPivot().Position)
		movePivot(item, item:GetPivot() * CFrame.Angles(0, math.pi, 0))
		return true
	end

	-- 22. Предмет на столе сдвинут на ширину ладони
	scenarios.ItemShifted = function(_: number): boolean
		local item = smallItem()
		if not item then
			return false
		end
		local pivot = item:GetPivot()
		mark(pivot.Position)
		local dir = if rng:NextNumber() < 0.5 then pivot.RightVector else pivot.LookVector
		movePivot(item, pivot + dir * (if rng:NextNumber() < 0.5 then 0.9 else -0.9))
		return true
	end

	-- 23. Растение другого цвета: листья фиолетовые
	scenarios.PlantColor = function(_: number): boolean
		local plants: {Model} = {}
		for _, pattern in {"DeskPlants$", "Planter$", "Plant"} do
			for _, item in find(pattern) do
				table.insert(plants, item)
			end
		end
		if #plants == 0 then
			return false
		end
		local plant = pick(plants)
		local saved: {[BasePart]: Color3} = {}
		for _, d in plant:GetDescendants() do
			if d:IsA("BasePart") and colorOfPlant(d) then
				saved[d] = d.Color
				d.Color = Color3.fromRGB(150, 62, 168)
			end
		end
		if next(saved) == nil then
			return false
		end
		table.insert(undo, function()
			for part, color in saved do
				if part.Parent then
					part.Color = color
				end
			end
		end)
		mark(plant:GetPivot().Position)
		return true
	end

	-- 24. Лишняя тень на стене: тёмный силуэт человека у стены
	scenarios.ShadowOnWall = function(_: number): boolean
		for _ = 1, 15 do
			local spot = floorSpot()
			if spot then
				local dirs = {Vector3.xAxis, -Vector3.xAxis, Vector3.zAxis, -Vector3.zAxis}
				local origin = Vector3.new(spot.X, 3.4, spot.Z)
				local params = RaycastParams.new()
				params.FilterType = Enum.RaycastFilterType.Exclude
				params.FilterDescendantsInstances = {folder}
				for _, d in dirs do
					local hit = workspace:Raycast(origin, d * 7, params)
					if hit and math.abs(hit.Normal:Dot(d)) > 0.95 and hit.Instance.Name:find("^Wall") then
						local base = CFrame.lookAt(hit.Position + hit.Normal * 0.03, hit.Position + hit.Normal * 2) * CFrame.new(0, -0.2, 0)
						local ink = Color3.fromRGB(4, 4, 6)
						local function shadow(size: Vector3, cf: CFrame, shape: Enum.PartType?)
							local p = newPart(folder, "Part", size, cf, ink, 0.45)
							if shape then
								p.Shape = shape
							end
						end
						shadow(Vector3.new(1.2, 2.2, 0.03), base * CFrame.new(0, 0.2, 0))
						shadow(Vector3.new(0.9, 1.0, 0.03), base * CFrame.new(0, 1.7, 0), Enum.PartType.Ball)
						shadow(Vector3.new(0.4, 2.4, 0.03), base * CFrame.new(-0.85, 0.1, 0) * CFrame.Angles(0, 0, math.rad(-6)))
						shadow(Vector3.new(0.4, 2.4, 0.03), base * CFrame.new(0.85, 0.1, 0) * CFrame.Angles(0, 0, math.rad(6)))
						mark(hit.Position)
						return true
					end
				end
			end
		end
		return false
	end

	-- 25. На экране монитора неправильное время (03:33)
	local function timeLabel(): TextLabel?
		local labels: {TextLabel} = {}
		for _, item in find("Monitor$") do
			local lcd = lcdOf(item)
			if lcd then
				for _, d in lcd:GetDescendants() do
					if d:IsA("TextLabel") and string.find(d.Text, "%d%d:%d%d") then
						table.insert(labels, d)
					end
				end
			end
		end
		return if #labels > 0 then labels[rng:NextInteger(1, #labels)] else nil
	end
	scenarios.MonitorWrongTime = function(_: number): boolean
		local label = timeLabel()
		if not label then
			return false
		end
		local original = label.Text
		label:SetAttribute("KonturLocked", true)
		label.Text = string.gsub(original, "%d%d:%d%d", "03:33")
		table.insert(undo, function()
			label:SetAttribute("KonturLocked", nil)
			label.Text = original
		end)
		local host = label:FindFirstAncestorWhichIsA("BasePart")
		if host then
			mark(host.Position)
		end
		return true
	end

	-- 26. Опрокинутая кружка с пролитым кофе
	scenarios.MugSpilled = function(_: number): boolean
		local mugs: {Model} = {}
		for _, pattern in {"CoffeeMugs$", "KitchenMugs$"} do
			for _, item in find(pattern) do
				table.insert(mugs, item)
			end
		end
		if #mugs == 0 then
			return false
		end
		local mug = pick(mugs)
		local pivot = mug:GetPivot()
		local hit = workspace:Raycast(pivot.Position + Vector3.new(0, 1, 0), Vector3.new(0, -3, 0))
		movePivot(mug, pivot * CFrame.Angles(0, 0, math.rad(90)) * CFrame.new(0, -0.1, 0))
		if hit then
			local puddle = newPart(folder, "Part", Vector3.new(0.02, 1.1, 0.8), CFrame.new(hit.Position + Vector3.new(0, 0.015, 0)) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(56, 32, 18), 0.05)
			puddle.Shape = Enum.PartType.Cylinder
			puddle.Material = Enum.Material.Glass
			puddle.Reflectance = 0.12
		end
		mark(pivot.Position)
		return true
	end

	-- 27. У стола пропало кресло
	scenarios.ChairGone = function(_: number): boolean
		local chairs = find("ErgoChair$")
		if #chairs == 0 then
			return false
		end
		local chair = pick(chairs)
		mark(chair:GetPivot().Position)
		hideModel(chair)
		return true
	end

	-- 28. Табличка у двери называет не ту комнату
	scenarios.PlateWrongName = function(_: number): boolean
		local corridor = office:FindFirstChild("KonturCorridor")
		if not corridor then
			return false
		end
		local plates: {BasePart} = {}
		for _, d in corridor:GetChildren() do
			if d:IsA("BasePart") and d.Name == "RoomPlate" then
				table.insert(plates, d)
			end
		end
		if #plates == 0 then
			return false
		end
		local plate = plates[rng:NextInteger(1, #plates)]
		local gui = plate:FindFirstChildWhichIsA("SurfaceGui")
		local label = gui and gui:FindFirstChildWhichIsA("TextLabel")
		if not label then
			return false
		end
		local original = label.Text
		local others = {"БУХГАЛТЕРИЯ", "ОТДЕЛ КАДРОВ", "ТЕХНИЧЕСКИЙ ЭТАЖ", "КОМНАТА ОТДЫХА", "СЕРВЕРНАЯ", "ПОДСОБНОЕ ПОМЕЩЕНИЕ"}
		label.Text = others[rng:NextInteger(1, #others)]
		table.insert(undo, function()
			label.Text = original
		end)
		mark(plate.Position)
		return true
	end

	-- 29. Бумаги разбросаны на полу
	scenarios.PapersOnFloor = function(_: number): boolean
		local spot = floorSpot()
		if not spot then
			return false
		end
		for i = 1, 8 do
			local offset = Vector3.new(rng:NextNumber(-1.4, 1.4), 0, rng:NextNumber(-1.4, 1.4))
			local at = spot + offset
			local fy = freeAt(at.X, at.Z, 0.4)
			if fy then
				newPart(folder, "Part", Vector3.new(0.85, 0.012, 1.15), CFrame.new(at.X, fy + 0.02 + i * 0.002, at.Z) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0), Color3.fromRGB(242, 240, 232 - i * 3))
			end
		end
		mark(spot)
		return true
	end

	-- 30. Один монитор выключен: чёрный экран
	scenarios.ScreenOff = function(_: number): boolean
		local screens: {BasePart} = {}
		for _, item in find("Monitor$") do
			local lcd = lcdOf(item)
			if lcd and lcd:FindFirstChildWhichIsA("SurfaceGui") then
				table.insert(screens, lcd)
			end
		end
		if #screens == 0 then
			return false
		end
		local lcd = screens[rng:NextInteger(1, #screens)]
		local guis: {SurfaceGui} = {}
		for _, g in lcd:GetChildren() do
			if g:IsA("SurfaceGui") and g.Enabled then
				g.Enabled = false
				table.insert(guis, g)
			end
		end
		table.insert(undo, function()
			for _, g in guis do
				g.Enabled = true
			end
		end)
		mark(lcd.Position)
		return true
	end

	-- ===================== РЕАГИРУЮЩИЕ НА ИГРОКА АНОМАЛИИ =====================
	-- Клиент (OfficeReactiveClient.luau) раз в 0,2 с сообщает, смотрит ли игрок прямо на фигуру с тегом KonturWatch, и направление камеры.
	local Players = game:GetService("Players")
	local ReplicatedStorage = game:GetService("ReplicatedStorage")
	local sync = ReplicatedStorage:FindFirstChild("KonturSync")
	if not (sync and sync:IsA("RemoteEvent")) then
		sync = Instance.new("RemoteEvent")
		sync.Name = "KonturSync"
		sync.Parent = ReplicatedStorage
	end
	local gaze: {[Player]: {t: number, seen: boolean, look: Vector3}} = {}
	local remote = sync :: RemoteEvent
	remote.OnServerEvent:Connect(function(player: Player, seen: any, look: any)
		if typeof(seen) ~= "boolean" or typeof(look) ~= "Vector3" then
			return
		end
		local length = look.Magnitude
		if not (length >= 0.9 and length <= 1.1) then -- NaN тоже отбрасывается
			return
		end
		local now = os.clock()
		local prev = gaze[player]
		if prev and now - prev.t < 0.1 then
			return
		end
		gaze[player] = {t = now, seen = seen, look = look.Unit}
	end)
	Players.PlayerRemoving:Connect(function(player: Player)
		gaze[player] = nil
	end)
	-- «видит ли кто-то фигуру» считает сервер: по голове живого персонажа, присланному направлению камеры и лучу без преград;
	-- клиентскому флагу seen не доверяем (его могли подделать), он игнорируется
	local function anyoneSees(model: Model): boolean
		local now = os.clock()
		local target = model:GetPivot().Position + Vector3.new(0, 3, 0)
		for player, g in gaze do
			local character = player.Character
			local head = character and character:FindFirstChild("Head")
			local humanoid = character and character:FindFirstChildOfClass("Humanoid")
			if now - g.t < 1.5 and head and head:IsA("BasePart") and humanoid and humanoid.Health > 0 then
				local offset = target - head.Position
				local dist = offset.Magnitude
				if dist <= 90 and dist > 0.1 and g.look:Dot(offset.Unit) > 0.6 then
					local params = RaycastParams.new()
					params.FilterType = Enum.RaycastFilterType.Exclude
					params.FilterDescendantsInstances = {model, character :: Instance, folder}
					if not workspace:Raycast(head.Position, offset, params) then
						return true
					end
				end
			end
		end
		return false
	end
	local function nearestRoot(pos: Vector3): (BasePart?, number)
		local best: BasePart? = nil
		local bestDist = math.huge
		for _, player in Players:GetPlayers() do
			local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
			local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
			if root and root:IsA("BasePart") and humanoid and humanoid.Health > 0 and not (root.Position.X < 1000 and root.Position.Z > 56) then
				local d = (root.Position - pos).Magnitude
				if d < bestDist then
					best, bestDist = root, d
				end
			end
		end
		return best, bestDist
	end
	local function farFloorSpot(minDist: number): (Vector3?, Instance?)
		for _ = 1, 8 do
			local spot, room = floorSpot()
			if spot then
				local _, d = nearestRoot(spot)
				if d >= minDist then
					return spot, room
				end
			end
		end
		return nil, nil
	end
	-- 31. Статуя: стоит далеко, шагает к игроку, пока на неё не смотрят; замирает под взглядом; не подходит ближе 5
	scenarios.StatueWalks = function(myToken: number): boolean
		local spot, room = farFloorSpot(20)
		if not (spot and room) then
			return false
		end
		mark(spot)
		local model = buildFigure(folder, spot, roomCentre(room), 0)
		local hum = voice(model:FindFirstChildWhichIsA("BasePart") :: Instance, "Drone", SND.boom, 0.8, 0.12, 0.7, 1, true)
		hum:Play()
		local beat = if AUDIO.Heartbeat then makeSound(model:FindFirstChildWhichIsA("BasePart") :: Instance, "rbxassetid://" .. tostring(AUDIO.Heartbeat), 0, 1, true, true) else nil
		if beat then
			beat:Play()
		end
		local sting = if AUDIO.Stinger then makeSound(model:FindFirstChildWhichIsA("BasePart") :: Instance, "rbxassetid://" .. tostring(AUDIO.Stinger), 0.5, 1, false, true) else nil
		local fired = false
		task.spawn(function()
			local last = os.clock()
			while token == myToken and model.Parent do
				local now = os.clock()
				local dt = now - last
				last = now
				local root, dist = nearestRoot(model:GetPivot().Position)
				if beat then
					beat:SetAttribute("Gain", math.clamp((26 - dist) / 26, 0, 1) * 0.6)
				end
				if root and not anyoneSees(model) and dist > 5 then
					local p = model:GetPivot().Position
					local dir = Vector3.new(root.Position.X - p.X, 0, root.Position.Z - p.Z)
					if dir.Magnitude > 0.1 then
						local step = dir.Unit * math.min(2.2 * dt, dist - 5)
						model:PivotTo(CFrame.lookAt(p + step, p + step + dir.Unit))
					end
				end
				if sting and not fired and dist < 9 then
					fired = true
					sting:Play()
				end
				task.wait(0.1)
			end
		end)
		return true
	end

	-- 32. Фигура исчезает, когда на неё смотрят прямо дольше секунды
	scenarios.VanishWhenSeen = function(myToken: number): boolean
		local spot, room = farFloorSpot(14)
		if not (spot and room) then
			return false
		end
		mark(spot)
		local model = buildFigure(folder, spot, roomCentre(room), 0)
		voice(model:FindFirstChildWhichIsA("BasePart") :: Instance, "Drone", SND.boom, 0.7, 0.12, 0.55, 1, true):Play()
		task.spawn(function()
			local seenFor = 0
			while token == myToken and model.Parent do
				if anyoneSees(model) then
					seenFor += 0.1
				else
					seenFor = math.max(0, seenFor - 0.05)
				end
				if seenFor >= 1.2 then
					model:Destroy()
					break
				end
				task.wait(0.1)
			end
		end)
		return true
	end

	-- 33. Через 7-15 секунд движения игрока фигура появляется у него за спиной и исчезает, как только он обернулся
	scenarios.BehindYou = function(myToken: number): boolean
		task.spawn(function()
			task.wait(rng:NextNumber(7, 15))
			for _ = 1, 40 do
				if token ~= myToken then
					return
				end
				-- кандидаты: живые игроки вне стартовой комнаты со свежим направлением камеры
				local candidates: {{root: BasePart, look: Vector3}} = {}
				local now = os.clock()
				for player, data in gaze do
					local character = player.Character
					local root = character and character:FindFirstChild("HumanoidRootPart")
					local humanoid = character and character:FindFirstChildOfClass("Humanoid")
					if now - data.t < 1.5 and root and root:IsA("BasePart") and humanoid and humanoid.Health > 0 and not (root.Position.X < 1000 and root.Position.Z > 56) then
						table.insert(candidates, {root = root, look = data.look})
					end
				end
				local placed: Vector3? = nil
				local target: BasePart? = nil
				if #candidates > 0 then
					local chosen = candidates[rng:NextInteger(1, #candidates)]
					local look = Vector3.new(chosen.look.X, 0, chosen.look.Z)
					if look.Magnitude > 0.2 then
						local back = -look.Unit
						for _, ang in {0, 0.5, -0.5, 1.0, -1.0} do
							local dir = CFrame.Angles(0, ang, 0):VectorToWorldSpace(back)
							local at = chosen.root.Position + dir * 6.5
							local fy = freeAt(at.X, at.Z, 1.2)
							if fy then
								placed = Vector3.new(at.X, fy, at.Z)
								target = chosen.root
								break
							end
						end
					end
				end
				if placed and target then
					mark(placed)
					local model = buildFigure(folder, placed, target.Position, 0)
					local base = model:FindFirstChildWhichIsA("BasePart") :: Instance
					if AUDIO.Stinger then
						local sting = makeSound(base, "rbxassetid://" .. tostring(AUDIO.Stinger), 0.5, 1, false, true)
						sting.RollOffMaxDistance = 45
						sting:Play()
					else
						makeSound(base, SND.boom, 0.45, 0.3, false):Play()
					end
					local seenFor = 0
					while token == myToken and model.Parent do
						if anyoneSees(model) then
							seenFor += 0.1
						end
						if seenFor >= 0.6 then
							model:Destroy()
							break
						end
						task.wait(0.1)
					end
					return
				end
				task.wait(1)
			end
		end)
		return true
	end

	-- 34..39. Парные аномалии: два связанных события в одном раунде
	local PAIRS: {[string]: {string}} = {
		PairPhoneChair = {"PhoneRingsAlone", "ChairGone"},
		PairKnocksDrip = {"CeilingKnocks", "DrippingCeiling"},
		PairBreathPistol = {"BreathingCabinet", "HiddenPistol"},
		PairWhisperScreen = {"WhisperMonitor", "ScreenOff"},
		PairStepsShadow = {"SlowFootsteps", "ShadowFigure"},
		PairMugPapers = {"MugSpilled", "PapersOnFloor"},
	}
	for pairName, parts in PAIRS do
		scenarios[pairName] = function(myToken: number): boolean
			local first = scenarios[parts[1]](myToken)
			local second = scenarios[parts[2]](myToken)
			return first or second
		end
	end

	-- какие сценарии доступны на этой карте: пробуем на сухую
	local available: {string} = {}
	for name in scenarios do
		table.insert(available, name)
	end
	table.sort(available)
	local function isPossible(name: string): boolean
		if name == "BreathingCabinet" then
			return #find("ArchiveCabinet$") + #find("FormsCabinet$") > 0
		elseif name == "PhoneRingsAlone" then
			return #find("Telephone$") > 0
		elseif name == "RockingChair" then
			return #find("ErgoChair$") > 0
		elseif PAIRS[name] then
			return isPossible(PAIRS[name][1]) and isPossible(PAIRS[name][2])
		elseif name == "StatueWalks" or name == "VanishWhenSeen" or name == "BehindYou" then
			return rooms ~= nil
		elseif name == "ItemRotated" or name == "ItemShifted" then
			return smallItem() ~= nil
		elseif name == "PlantColor" then
			return #find("DeskPlants$") + #find("Planter$") + #find("Plant") > 0
		elseif name == "MonitorWrongTime" then
			return timeLabel() ~= nil
		elseif name == "MugSpilled" then
			return #find("CoffeeMugs$") + #find("KitchenMugs$") > 0
		elseif name == "ChairGone" then
			return #find("ErgoChair$") > 0
		elseif name == "PlateWrongName" then
			return false -- добавляется позже, когда появятся таблички
		elseif name == "ScreenOff" then
			for _, item in find("Monitor$") do
				local lcd = lcdOf(item)
				if lcd and lcd:FindFirstChildWhichIsA("SurfaceGui") then
					return true
				end
			end
			return false
		elseif name == "HiddenPistol" or name == "RedMug" then
			return #find("StraightDesk$") > 0
		elseif name == "BloodDrops" then
			return #find("Cabinet$") > 0
		elseif name == "KeyboardGone" then
			return #find("^Keyboard$") > 0
		elseif name == "CabinetAjar" then
			return #ajarDoors() > 0
		elseif name == "StickyNote" then
			for _, item in find("Monitor$") do
				if lcdOf(item) then
					return true
				end
			end
			return false
		elseif name == "FrameMissing" then
			return #find("KD_Frame") > 0
		elseif name == "FaucetRunning" then
			for _, kind in {"DoubleVanity$", "WallBasin$"} do
				for _, basin in find(kind) do
					if basin:FindFirstChild("Aerator", true) then
						return true
					end
				end
			end
			return false
		elseif name == "WhisperMonitor" then
			for _, item in find("Monitor$") do
				local lcdItem = item:FindFirstChild("LCD")
				if lcdItem and lcdItem:IsA("BasePart") then
					return true
				end
			end
			return false
		end
		return rooms ~= nil
	end
	for _, name in available do
		if isPossible(name) and not table.find(names, name) then
			table.insert(names, name)
		end
	end

	-- таблички коридора строятся отдельным модулем с задержкой: сценарий добавляется, когда они появились
	task.spawn(function()
		for _ = 1, 40 do
			task.wait(3)
			local corridor = office:FindFirstChild("KonturCorridor")
			if corridor and corridor:FindFirstChild("RoomPlate") then
				if not table.find(names, "PlateWrongName") then
					table.insert(names, "PlateWrongName")
				end
				break
			end
		end
	end)

	-- ложные тревоги: безобидные предметы, которые выглядят странно, но в «чистом» раунде это норма (правильный ответ «без изменений»)
	local function decoy()
		local pick1 = rng:NextInteger(1, 3)
		local spot = floorSpot()
		if not spot then
			return
		end
		if pick1 == 1 then -- жёлтая табличка «мокрый пол» и лужица
			local base = CFrame.new(spot.X, spot.Y, spot.Z) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
			local yellow = Color3.fromRGB(246, 200, 36)
			newPart(folder, "Part", Vector3.new(1.0, 1.8, 0.1), base * CFrame.new(-0.2, 0.95, 0) * CFrame.Angles(0, 0, math.rad(8)), yellow)
			newPart(folder, "Part", Vector3.new(1.0, 1.8, 0.1), base * CFrame.new(0.2, 0.95, 0) * CFrame.Angles(0, 0, math.rad(-8)), yellow)
			local puddle = newPart(folder, "Part", Vector3.new(0.02, 2.4, 2.4), CFrame.new(spot.X + 1.1, spot.Y + 0.1, spot.Z) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(150, 190, 214), 0.35)
			puddle.Shape = Enum.PartType.Cylinder
			puddle.Material = Enum.Material.Glass
		elseif pick1 == 2 then -- ведро со шваброй
			local bucket = newPart(folder, "Part", Vector3.new(1.3, 1.1, 1.1), CFrame.new(spot.X, spot.Y + 0.65, spot.Z) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(46, 120, 190))
			bucket.Shape = Enum.PartType.Cylinder
			newPart(folder, "Part", Vector3.new(0.12, 5.0, 0.12), CFrame.new(spot.X + 0.5, spot.Y + 3.0, spot.Z + 0.2) * CFrame.Angles(math.rad(8), 0, math.rad(-10)), Color3.fromRGB(150, 120, 80))
			newPart(folder, "Part", Vector3.new(0.7, 0.5, 0.7), CFrame.new(spot.X + 0.75, spot.Y + 0.35, spot.Z + 0.2), Color3.fromRGB(190, 190, 180))
		else -- стопка коробок
			for i = 1, 3 do
				newPart(folder, "Part", Vector3.new(1.6, 1.1, 1.3), CFrame.new(spot.X + (i - 2) * 0.1, spot.Y + 0.6 + (i - 1) * 1.12, spot.Z) * CFrame.Angles(0, math.rad((i - 2) * 6), 0), Color3.fromRGB(176, 136, 90)).Material = Enum.Material.Cardboard
			end
		end
	end

	return function(scenario: string?, _: number?): boolean
		clear()
		if scenario == "Clear" and rng:NextNumber() < 0.4 then
			decoy()
		end
		table.clear(findCache) -- модели могли появиться или смениться после запуска (фоновые апгрейды)
		if scenario == nil then
			return false
		end
		local run = scenarios[scenario]
		if not run then
			return false
		end
		local ok = run(token)
		if not ok then
			-- сценарий свой: возвращаем true в любом случае, иначе базовая логика опубликует его имя всем клиентам
			warn("KONTUR horror anomaly could not be placed: " .. scenario)
		end
		return true
	end
end

return attachHorrorAnomalies
