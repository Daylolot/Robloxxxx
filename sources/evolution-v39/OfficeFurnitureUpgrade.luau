--!strict
-- v42 офисная мебель основной карты из Blender (загруженные ассеты Roblox): кресла ErgoChair, MeetingChair и VisitorChair (десятки и сотни
-- деталей на кресло) заменяются одним набором мешей. PlacementPivot (начало и «перёд» кресла) и невидимая коллизия CollisionProxy остаются; аномалии кресел (поворот, падение)
-- двигают модель целиком и подхватывают меши как обычные детали. Если ассет не загрузился, кресла не меняются.
-- Подключает сборщик build_place.py: attachFurnitureUpgrade(office) в отдельном потоке, id ассетов подставляются вместо метки.
local function attachFurnitureUpgrade(office: Instance?)
	if not office then
		return
	end
	local ASSETS: {[string]: number} = {}
	-- @@FURNITURE_ASSETS@@
	local LOOK: {[string]: Enum.Material} = {
		leather = Enum.Material.Leather, metal = Enum.Material.Metal, metal_dark = Enum.Material.Metal, alu = Enum.Material.Metal,
	}
	local function loadTemplate(key: string, assetId: number): Model?
		local container: Instance? = nil
		for attempt = 1, 4 do
			local ok, result = pcall(function()
				return game:GetService("InsertService"):LoadAsset(assetId)
			end)
			if ok and result then
				container = result
				break
			end
			if attempt < 4 then
				task.wait(4)
			end
		end
		if not container then
			warn("KONTUR furniture asset " .. key .. " (" .. tostring(assetId) .. ") failed")
			return nil
		end
		local template = Instance.new("Model")
		template.Name = "Furn_" .. key
		for _, mesh in container:GetDescendants() do
			if mesh:IsA("MeshPart") then
				local suffix, hex = string.match(mesh.Name, "^" .. key .. "_(.+)_(%x%x%x%x%x%x)$")
				if hex then
					mesh.Color = Color3.fromHex(hex)
				end
				mesh.Anchored = true
				mesh.CanCollide = false
				mesh.CanTouch = false
				mesh.CanQuery = false
				mesh.Material = LOOK[suffix or ""] or Enum.Material.SmoothPlastic
				mesh.Parent = template
			end
		end
		container:Destroy()
		if #template:GetChildren() == 0 then
			template:Destroy()
			return nil
		end
		template.WorldPivot = CFrame.new()
		return template
	end

	-- ключ ассета -> окончание имени модели в карте
	local KINDS: {{string}} = {{"ErgoChair", "ErgoChair$"}, {"MeetingChair", "MeetingChair$"}, {"VisitorChair", "VisitorChair$"}, {"Toilet", "Toilet$"}, {"WallSockets", "WallSockets$"}}
	local templates: {[string]: Model} = {}
	for _, kind in KINDS do
		local id = ASSETS[kind[1]]
		if id then
			local template = loadTemplate(kind[1], id)
			if template then
				templates[kind[1]] = template
			end
		end
	end
	if next(templates) == nil then
		return
	end
	-- кресла меняются только пока нет активной аномалии: сценарии кресел (поворот, падение) хранят исходные позы деталей
	local reportState = office:FindFirstChild("AnomalyReportState")
	if reportState then
		for _ = 1, 150 do
			local scenario = reportState:GetAttribute("OfficeDetailScenario")
			if scenario == nil or scenario == "Clear" then
				break
			end
			task.wait(1)
		end
	end
	local jobs: {{model: Model, key: string}} = {}
	for _, item in office:GetDescendants() do
		if item:IsA("Model") then
			for _, kind in KINDS do
				if templates[kind[1]] and string.find(item.Name, kind[2]) then
					table.insert(jobs, {model = item, key = kind[1]})
				end
			end
		end
	end
	local swapped = 0
	for _, job in jobs do
		local chair = job.model
		local pivot = chair:FindFirstChild("PlacementPivot")
		if pivot and pivot:IsA("BasePart") and not chair:GetAttribute("FurnitureUpgraded") then
			local base = pivot.CFrame
			for _, part in chair:GetDescendants() do
				if part:IsA("BasePart") and part.Name ~= "PlacementPivot" and part.Name ~= "CollisionProxy" and not part:FindFirstChildWhichIsA("SurfaceGui") then
					part:Destroy()
				end
			end
			local copy = templates[job.key]:Clone()
			copy:PivotTo(base)
			for _, mesh in copy:GetChildren() do
				mesh.Parent = chair
			end
			copy:Destroy()
			chair:SetAttribute("FurnitureUpgraded", true)
			swapped += 1
			if swapped % 4 == 0 then
				task.wait()
			end
		end
	end

	-- мониторы (корпус Housing, подставка Stand + Base) и клавиатуры (Body + 40 Key): размеры у экземпляров разные, поэтому меши
	-- масштабируются по осям под размеры исходных деталей; экран LCD с GUI, светодиод и остальное не трогаются
	local function loadLocal(key: string): Model?
		local id = ASSETS[key]
		return if id then loadTemplate(key, id) else nil
	end
	local shellL, shellP, footT, keyT = loadLocal("MonitorShell"), loadLocal("MonitorShellP"), loadLocal("MonitorFoot"), loadLocal("Keyboard")
	local function placeScaled(model: Instance, template: Model, base: CFrame, k: Vector3): {Instance}
		local made: {Instance} = {}
		local copy = template:Clone()
		copy:PivotTo(base)
		for _, mesh in copy:GetChildren() do
			if mesh:IsA("BasePart") then
				local rel = base:PointToObjectSpace(mesh.Position)
				local rot = base:ToObjectSpace(mesh.CFrame).Rotation
				mesh.Size = mesh.Size * k
				mesh.CFrame = base * CFrame.new(rel * k) * rot
				mesh.Parent = model
				table.insert(made, mesh)
			end
		end
		copy:Destroy()
		return made
	end
	local desks: {Model} = {}
	for _, item in office:GetDescendants() do
		if item:IsA("Model") and not item:GetAttribute("FurnitureUpgraded") and (item:FindFirstChild("LCD") or item:FindFirstChild("Key")) then
			table.insert(desks, item)
		end
	end
	local deskSwapped = 0
	for _, model in desks do
		local housing = model:FindFirstChild("Housing")
		local lcd = model:FindFirstChild("LCD")
		local body = model:FindFirstChild("Body")
		if housing and housing:IsA("BasePart") and lcd and (shellL or shellP) then
			local size = housing.Size
			local portrait = size.Y > size.X * 1.2
			local shell = if portrait then shellP else shellL
			if shell then
				local nomW, nomH = if portrait then 1.06 else 2.5, if portrait then 2.55 else 1.62
				local color, material = housing.Color, housing.Material
				local made = placeScaled(model, shell, housing.CFrame, Vector3.new(size.X / nomW, size.Y / nomH, size.Z / 0.15))
				housing:Destroy()
				for _, mesh in made do
					if mesh:IsA("MeshPart") and string.find(mesh.Name, "_263336$") then
						mesh.Name = "Housing" -- аномалия MonitorHousingRed красит деталь с этим именем
						mesh.Color = color
						mesh.Material = material
					end
				end
			end
			local stand, base = model:FindFirstChild("Stand"), model:FindFirstChild("Base")
			if footT and stand and base and stand:IsA("BasePart") and base:IsA("BasePart") then
				local total = base.Size.Y + stand.Size.Y
				local centre = base.CFrame * CFrame.new(0, -base.Size.Y / 2 + total / 2, 0)
				placeScaled(model, footT, centre, Vector3.new(base.Size.X / 1.08, total / 0.83, base.Size.Z / 0.57))
				stand:Destroy()
				base:Destroy()
			end
			model:SetAttribute("FurnitureUpgraded", true)
			deskSwapped += 1
		elseif body and body:IsA("BasePart") and keyT and model:FindFirstChild("Key") then
			local keep = {}
			for _, part in model:GetChildren() do
				if part:IsA("BasePart") and (part.Name == "Key" or part == body) then
					table.insert(keep, part)
				end
			end
			local ky = body.Size.Y / 0.10
			placeScaled(model, keyT, body.CFrame * CFrame.new(0, 0.015 * ky, 0), Vector3.new(body.Size.X / 1.87, ky, body.Size.Z / 0.58))
			for _, part in keep do
				part:Destroy()
			end
			model:SetAttribute("FurnitureUpgraded", true)
			deskSwapped += 1
		end
		if deskSwapped % 4 == 0 then
			task.wait()
		end
	end
	for _, template in {shellL, shellP, footT, keyT} do
		template:Destroy()
	end
	for _, template in templates do
		template:Destroy()
	end
end

return attachFurnitureUpgrade
