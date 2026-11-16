--!strict
-- v43: оформление коридора (кольцо вокруг комнат, стены были голыми): скамьи у стен, горшечные растения, рамки с плакатами, доски объявлений,
-- таблички у дверей с названием комнаты, длинные ковровые дорожки. Всё из простых деталей, лежит в папке KonturCorridor.
-- Места подбираются лучами от оси каждого участка до стен; предмет ставится, только если рядом нет коллизии и на стене нет чужих предметов.
local function attachCorridorDressing(office: Instance)
	task.wait(8) -- ждём фоновые апгрейды (шкафы, мебель)
	local folder = Instance.new("Folder")
	folder.Name = "KonturCorridor"
	local overlap = OverlapParams.new()
	local rng = Random.new(1507)
	local ROOM_NAMES: {[string]: string} = {
		WEST = "ОТДЕЛ «ЗАПАД»", CENTER = "ЦЕНТРАЛЬНЫЙ ЗАЛ", EAST = "ОТДЕЛ «ВОСТОК»", NW = "АРХИВ И СКЛАД", NE = "ПЕРЕГОВОРНАЯ", MEN = "МУЖСКОЙ ТУАЛЕТ", WOMEN = "ЖЕНСКИЙ ТУАЛЕТ", StartRoom = "ПРИЁМНАЯ",
	}

	local function part(size: Vector3, cf: CFrame, color: Color3, material: Enum.Material?, shape: Enum.PartType?, solid: boolean?): Part
		local p = Instance.new("Part")
		p.Size = size
		p.CFrame = cf
		p.Color = color
		p.Material = material or Enum.Material.SmoothPlastic
		p.Anchored = true
		p.CanCollide = solid == true
		p.CanQuery = solid == true
		p.CanTouch = false
		p.CastShadow = solid == true
		if shape then
			p.Shape = shape
		end
		p.Parent = folder
		return p
	end
	local function label(host: BasePart, face: Enum.NormalId, canvas: Vector2, text: string, color: Color3, bg: Color3?, font: Enum.Font?)
		local gui = Instance.new("SurfaceGui")
		gui.Face = face
		gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
		gui.CanvasSize = canvas
		gui.LightInfluence = 0.5
		gui.Parent = host
		local t = Instance.new("TextLabel")
		t.Size = UDim2.fromScale(1, 1)
		t.BackgroundColor3 = bg or Color3.new(1, 1, 1)
		t.BackgroundTransparency = if bg then 0 else 1
		t.TextColor3 = color
		t.Font = font or Enum.Font.GothamMedium
		t.TextScaled = true
		t.Text = text
		t.Parent = gui
	end
	local function freeSpace(at: Vector3, radius: number): boolean
		for _, p in workspace:GetPartBoundsInRadius(at, radius, overlap) do
			if p.CanCollide and p.Transparency < 1 and not p:IsDescendantOf(folder) and not string.find(p.Name, "^Wall") and not string.find(p.Name, "Floor") and not string.find(p.Name, "Ceiling") and not string.find(p.Name, "Roof") then
				return false
			end
		end
		return true
	end
	local function isWall(inst: Instance?): boolean
		return inst ~= nil and string.find(inst.Name, "^Wall") ~= nil
	end

	-- участки: ось и направление вдоль, длина от a до b
	local strips = {
		{axis = Vector3.new(1004.1, 0, 0), dir = Vector3.zAxis, from = 11, to = 50},
		{axis = Vector3.new(1059.9, 0, 0), dir = Vector3.zAxis, from = 11, to = 50},
		{axis = Vector3.new(0, 0, 4.1), dir = Vector3.xAxis, from = 1011, to = 1053},
		{axis = Vector3.new(0, 0, 56.2), dir = Vector3.xAxis, from = 1011, to = 1053},
	}
	local posters = {"ЭВАКУАЦИОННЫЙ ПЛАН", "ОХРАНА ТРУДА", "ПРАВИЛА ВНУТРЕННЕГО РАСПОРЯДКА", "СОТРУДНИК МЕСЯЦА", "ПРОВЕРЬ СВОЁ РАБОЧЕЕ МЕСТО", "ТИШИНА В АРХИВЕ", "РЕЗУЛЬТАТЫ КВАРТАЛА"}
	local notes = {"ГРАФИК УБОРКИ", "НЕ ЗАБЫВАЙТЕ ВЫКЛЮЧАТЬ СВЕТ", "ПРОПУСК НА ПОДПИСЬ", "ВСТРЕЧА В 15:00", "НАЙДЕН ЗОНТ", "КЛЮЧИ — У ОХРАНЫ"}

	local function plant(pos: Vector3, floorY: number)
		-- растение ставит OfficeUserCleanup новой моделью (фикус из Blender): здесь только невидимая метка места
		local spot = part(Vector3.new(0.2, 0.2, 0.2), CFrame.new(pos.X, floorY + 0.1, pos.Z), Color3.new(), nil, nil, false)
		spot.Name = "PlantSpot"
		spot.Transparency = 1
	end
	local function bench(pos: Vector3, floorY: number, inward: Vector3)
		local base = CFrame.lookAt(Vector3.new(pos.X, floorY, pos.Z), Vector3.new(pos.X, floorY, pos.Z) + inward)
		local wood, metal = Color3.fromRGB(150, 104, 66), Color3.fromRGB(58, 64, 70)
		part(Vector3.new(4.4, 0.18, 1.3), base * CFrame.new(0, 1.55, 0), wood, Enum.Material.Wood, nil, true)
		part(Vector3.new(4.4, 1.0, 0.14), base * CFrame.new(0, 2.25, 0.62) * CFrame.Angles(math.rad(-8), 0, 0), wood, Enum.Material.Wood, nil, false)
		for _, x in {-1.95, 1.95} do
			for _, z in {-0.5, 0.5} do
				part(Vector3.new(0.12, 1.5, 0.12), base * CFrame.new(x, 0.75, z), metal, Enum.Material.Metal, nil, true)
			end
		end
		part(Vector3.new(4.2, 0.1, 0.1), base * CFrame.new(0, 0.7, 0), metal, Enum.Material.Metal, nil, false)
	end
	local function frame(wallPos: Vector3, normal: Vector3, text: string)
		local cf = CFrame.lookAt(wallPos + normal * 0.06, wallPos + normal * 2)
		local w, h = 2.6, 1.8
		local border = part(Vector3.new(w + 0.3, h + 0.3, 0.1), cf, Color3.fromRGB(96, 66, 42), Enum.Material.Wood, nil, false)
		border.Name = "Frame"
		local canvas = part(Vector3.new(w, h, 0.05), cf * CFrame.new(0, 0, -0.045), Color3.fromRGB(240, 240, 232), nil, nil, false)
		local band = part(Vector3.new(w, 0.62, 0.05), cf * CFrame.new(0, h / 2 - 0.31, -0.07), Color3.fromRGB(40, 100, 110), nil, nil, false)
		label(band, Enum.NormalId.Front, Vector2.new(260, 62), text, Color3.fromRGB(240, 246, 246), Color3.fromRGB(40, 100, 110), Enum.Font.GothamBold)
		local colors = {Color3.fromRGB(226, 160, 52), Color3.fromRGB(46, 110, 150), Color3.fromRGB(84, 150, 110), Color3.fromRGB(190, 70, 60)}
		for i = 1, 4 do
			local bh = 0.25 + (i * 0.27) % 0.7
			part(Vector3.new(0.32, bh, 0.04), cf * CFrame.new(-0.9 + (i - 1) * 0.58, -h / 2 + 0.15 + bh / 2, -0.075), colors[i], nil, nil, false)
		end
	end
	local function noticeBoard(wallPos: Vector3, normal: Vector3)
		local cf = CFrame.lookAt(wallPos + normal * 0.07, wallPos + normal * 2)
		part(Vector3.new(3.4, 2.3, 0.12), cf, Color3.fromRGB(92, 64, 40), Enum.Material.Wood, nil, false)
		part(Vector3.new(3.15, 2.05, 0.06), cf * CFrame.new(0, 0, -0.04), Color3.fromRGB(176, 128, 84), Enum.Material.Wood, nil, false)
		local used = 0
		for i = 1, 5 do
			local x = -1.1 + ((i - 1) % 3) * 1.1 + rng:NextNumber(-0.08, 0.08)
			local y = if i <= 3 then 0.45 else -0.5
			local note = part(Vector3.new(0.85, 0.95, 0.02), cf * CFrame.new(x, y, -0.085) * CFrame.Angles(0, 0, math.rad(rng:NextNumber(-5, 5))), Color3.fromRGB(246, 242, 220 - i * 8), nil, nil, false)
			label(note, Enum.NormalId.Front, Vector2.new(85, 95), notes[(used % #notes) + 1], Color3.fromRGB(50, 50, 60), Color3.fromRGB(246, 242, 226), Enum.Font.GothamMedium)
			used += 1
			part(Vector3.new(0.07, 0.07, 0.04), cf * CFrame.new(x, y + 0.4, -0.11), Color3.fromRGB(200, 50, 40), nil, Enum.PartType.Ball, false)
		end
	end
	local function runner(center: Vector3, dir: Vector3, length: number, floorY: number)
		local cf = CFrame.lookAt(Vector3.new(center.X, floorY + 0.03, center.Z), Vector3.new(center.X, floorY + 0.03, center.Z) + dir)
		part(Vector3.new(2.0, 0.04, length), cf, Color3.fromRGB(34, 74, 82), Enum.Material.Fabric, nil, false)
		part(Vector3.new(1.7, 0.045, length - 0.3), cf, Color3.fromRGB(46, 92, 100), Enum.Material.Fabric, nil, false)
		for _, x in {-0.93, 0.93} do
			part(Vector3.new(0.08, 0.05, length), cf * CFrame.new(x, 0, 0), Color3.fromRGB(190, 160, 98), Enum.Material.Fabric, nil, false)
		end
	end

	local placed = 0
	for si, strip in strips do
		local dir: Vector3 = strip.dir
		local side = Vector3.new(-dir.Z, 0, dir.X)
		local axis: Vector3 = strip.axis
		-- пол и стены относительно оси на середине участка
		local mid = (strip.from + strip.to) / 2
		local midPos = axis + dir * mid
		local floorHit = workspace:Raycast(midPos + Vector3.new(0, 6, 0), Vector3.new(0, -9, 0))
		local floorY = if floorHit then floorHit.Position.Y else 0.1
		-- ковровые дорожки убраны по просьбе пользователя
		local step = 0
		local t = strip.from + 2
		local kind = si % 3
		while t < strip.to - 1 do
			local origin = axis + dir * t
			for _, sgn in {1, -1} do
				local sideDir = side * sgn
				local params = RaycastParams.new()
				params.FilterType = Enum.RaycastFilterType.Exclude
				params.FilterDescendantsInstances = {folder}
				local at = Vector3.new(origin.X, 4.6, origin.Z)
				local hit = workspace:Raycast(at, sideDir * 6, params)
				if hit and isWall(hit.Instance) and math.abs(hit.Normal:Dot(sideDir)) > 0.95 then
					local normal = hit.Normal
					local lowHit = workspace:Raycast(Vector3.new(origin.X, 2.2, origin.Z), sideDir * 6, params)
					local wallClear = lowHit ~= nil and isWall(lowHit.Instance)
					local choice = (step + (if sgn == 1 then 0 else 2) + kind) % 5
					if false and wallClear and choice == 0 and freeSpace(Vector3.new(hit.Position.X, 3.2, hit.Position.Z) + normal * 1.6, 1.5) then
						bench(Vector3.new(hit.Position.X, 0, hit.Position.Z) + normal * 0.85, floorY, normal)
						placed += 1
					elseif false and wallClear and choice == 1 then
						frame(Vector3.new(hit.Position.X, 5.0, hit.Position.Z), normal, posters[(placed % #posters) + 1])
						placed += 1
					elseif wallClear and choice == 2 and freeSpace(Vector3.new(hit.Position.X, 3.4, hit.Position.Z) + normal * 1.2, 1.1) then
						plant(Vector3.new(hit.Position.X, 0, hit.Position.Z) + normal * 0.9, floorY)
						placed += 1
					elseif false and wallClear and choice == 3 then
						noticeBoard(Vector3.new(hit.Position.X, 4.6, hit.Position.Z), normal)
						placed += 1
					end
				end
			end
			step += 1
			t += 4.6
		end
	end

	-- таблички у дверей: название комнаты за дверью
	local rooms = office:FindFirstChild("Rooms")
	local doors = office:FindFirstChild("Doors")
	local extents: {[string]: {lo: Vector3, hi: Vector3}} = {}
	if rooms then
		for _, room in rooms:GetChildren() do
			local lo, hi = Vector3.new(1e9, 0, 1e9), Vector3.new(-1e9, 0, -1e9)
			for _, d in room:GetDescendants() do
				if d:IsA("BasePart") then
					lo = Vector3.new(math.min(lo.X, d.Position.X), 0, math.min(lo.Z, d.Position.Z))
					hi = Vector3.new(math.max(hi.X, d.Position.X), 0, math.max(hi.Z, d.Position.Z))
				end
			end
			extents[room.Name] = {lo = lo, hi = hi}
		end
	end
	if doors then
		for _, door in doors:GetChildren() do
			local ok, cf = pcall(function()
				return door:GetPivot()
			end)
			if ok then
				local found: string? = nil
				local roomDir: Vector3? = nil
				for _, d in {cf.LookVector, -cf.LookVector, cf.RightVector, -cf.RightVector} do
					local probe = cf.Position + d * 4
					for name, box in extents do
						if probe.X > box.lo.X and probe.X < box.hi.X and probe.Z > box.lo.Z and probe.Z < box.hi.Z then
							found, roomDir = name, d
						end
					end
				end
				if found and roomDir then
					local label1 = ROOM_NAMES[found] or found
					local corridorDir = -roomDir
					local along = Vector3.new(-roomDir.Z, 0, roomDir.X)
					local params = RaycastParams.new()
					params.FilterType = Enum.RaycastFilterType.Exclude
					params.FilterDescendantsInstances = {folder}
					for _, sgn in {2.8, -2.8, 3.6, -3.6} do
						local from = Vector3.new(cf.Position.X, 4.7, cf.Position.Z) + corridorDir * 1.6 + along * sgn
						local hit = workspace:Raycast(from, roomDir * 3, params)
						if hit and hit.Instance.CanCollide and not hit.Instance:IsDescendantOf(door) and math.abs(hit.Normal:Dot(corridorDir)) > 0.95 then
							local plate = CFrame.lookAt(hit.Position + corridorDir * 0.05, hit.Position + corridorDir * 2)
							local board = part(Vector3.new(2.3, 0.55, 0.08), plate, Color3.fromRGB(26, 36, 44), Enum.Material.SmoothPlastic, nil, false)
							board.Name = "RoomPlate"
							label(board, Enum.NormalId.Front, Vector2.new(230, 55), label1, Color3.fromRGB(225, 236, 238), Color3.fromRGB(26, 36, 44), Enum.Font.GothamBold)
							break
						end
					end
				end
			end
		end
	end
	folder.Parent = office
	office:SetAttribute("CorridorItems", placed)
end

return attachCorridorDressing
