--!strict
-- v42 хаб FieldHub: костюмы Hazmat и станция респираторов заменены моделями из Blender (загруженные ассеты Roblox).
-- Старые детали (сотни частей с эллипсоидными филе) удаляются, кроме носителей игровой логики: надпись на груди костюма
-- (ChestPatch с SurfaceGui) и у станции Header, MaskControl (ProximityPrompt, ClickDetector, экран), InventoryTag с их подложками
-- LiveSurface; их ставят на места новой модели. Невидимые коллизии станции остаются. Если ассет не загрузился, хаб не меняется.
-- Подключает сборщик build_place.py: attachHubUpgrade(workspace.FieldHub) в отдельном потоке, id ассетов подставляются вместо метки ниже.
local function attachHubUpgrade(hub: Instance?)
	if not hub then
		return
	end
	local equipment = hub:FindFirstChild("Equipment")
	if not equipment then
		return
	end
	local HUB_ASSETS: {[string]: number} = {}
	-- @@HUB_ASSETS@@
	local LOOK: {[string]: {material: Enum.Material, transparency: number}} = {
		wood_dark = {material = Enum.Material.Wood, transparency = 0}, wood_mid = {material = Enum.Material.Wood, transparency = 0},
		wood_light = {material = Enum.Material.Wood, transparency = 0}, metal = {material = Enum.Material.Metal, transparency = 0},
		metal_dark = {material = Enum.Material.Metal, transparency = 0}, brass = {material = Enum.Material.Metal, transparency = 0},
		steel = {material = Enum.Material.Metal, transparency = 0}, tape = {material = Enum.Material.Metal, transparency = 0},
		glass_blue = {material = Enum.Material.Glass, transparency = 0.35}, glass_clear = {material = Enum.Material.Glass, transparency = 0.7},
		shade = {material = Enum.Material.Neon, transparency = 0.12},
	}

	local function loadTemplate(key: string, assetId: number): Model?
		local container: Instance? = nil
		local lastError: any = nil
		for _ = 1, 4 do -- сеть иногда отвечает 503
			local ok, result = pcall(function()
				return game:GetService("InsertService"):LoadAsset(assetId)
			end)
			if ok and result then
				container = result
				break
			end
			lastError = result
			task.wait(4)
		end
		if not container then
			warn("KONTUR hub asset " .. key .. " (" .. tostring(assetId) .. ") failed: " .. tostring(lastError))
			return nil
		end
		local template = Instance.new("Model")
		template.Name = "Hub_" .. key
		for _, mesh in container:GetDescendants() do
			if mesh:IsA("MeshPart") then
				-- имя детали: <Предмет>_<материал>_<цвет hex>
				local suffix, hex = string.match(mesh.Name, "^" .. key .. "_(.+)_(%x%x%x%x%x%x)$")
				suffix = suffix or mesh.Name
				if hex then
					mesh.Color = Color3.fromHex(hex)
				end
				local look = LOOK[suffix]
				mesh.Anchored = true
				mesh.CanCollide = false
				mesh.CanTouch = false
				mesh.CanQuery = false
				mesh.Material = if look then look.material else Enum.Material.SmoothPlastic
				mesh.Transparency = if look then look.transparency else 0
				mesh.DoubleSided = suffix == "shade" or suffix == "visor"
				mesh.CastShadow = suffix ~= "glass_blue" and suffix ~= "glass_clear"
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

	-- основание модели: центр основания габарита, перед по направлению взгляда исходной модели
	local function baseFrame(model: Model): CFrame
		local box, size = model:GetBoundingBox()
		local pivot = model:GetPivot()
		local origin = Vector3.new(pivot.X, box.Position.Y - size.Y / 2, pivot.Z)
		local look = pivot.LookVector
		return CFrame.lookAt(origin, origin + Vector3.new(look.X, 0, look.Z))
	end
	local function placeMeshes(model: Model, template: Model, base: CFrame)
		local copy = template:Clone()
		copy:PivotTo(base)
		for _, item in copy:GetChildren() do
			item.Parent = model
		end
		copy:Destroy()
	end

	local suitTemplate = if HUB_ASSETS.HazmatSuit then loadTemplate("HazmatSuit", HUB_ASSETS.HazmatSuit) else nil
	if suitTemplate then
		for _, suit in equipment:GetChildren() do
			if suit:IsA("Model") and string.find(suit.Name, "^Hazmat_%d+$") and not suit:GetAttribute("HubUpgraded") then
				local base = baseFrame(suit)
				local patch: BasePart? = nil
				for _, item in suit:GetDescendants() do
					if item:IsA("BasePart") then
						if item.Name == "ChestPatch" and item:FindFirstChildWhichIsA("SurfaceGui") then
							patch = item
						else
							item:Destroy()
						end
					end
				end
				if patch then
					patch.CFrame = base * CFrame.new(-0.42, 4.74, -0.62)
					local gui = patch:FindFirstChildWhichIsA("SurfaceGui")
					if gui and gui.Adornee ~= patch then
						gui.Adornee = patch -- надпись могла быть привязана к удалённой подложке
					end
				end
				placeMeshes(suit, suitTemplate, base)
				suit:SetAttribute("HubUpgraded", true)
				task.wait()
			end
		end
		suitTemplate:Destroy()
	end

	local station = equipment:FindFirstChild("MaskStation")
	local stationTemplate = if HUB_ASSETS.MaskStation then loadTemplate("MaskStation", HUB_ASSETS.MaskStation) else nil
	if stationTemplate and station and station:IsA("Model") and not station:GetAttribute("HubUpgraded") then
		local base = baseFrame(station)
		-- носители логики и их подложки: новые места на фронте витрины
		local targets: {[string]: CFrame} = {
			Header = base * CFrame.new(0, 5.725, -0.42),
			MaskControl = base * CFrame.new(0, 2.01, -1.27),
			InventoryTag = base * CFrame.new(0, 1.0, -1.29),
		}
		local carriers: {[string]: BasePart} = {}
		local backers: {BasePart} = {}
		for _, item in station:GetDescendants() do
			if item:IsA("BasePart") then
				if targets[item.Name] and item:FindFirstChildWhichIsA("SurfaceGui") then
					carriers[item.Name] = item
				elseif item.Name == "LiveSurface" then
					table.insert(backers, item)
				end
			end
		end
		local keep: {[BasePart]: boolean} = {}
		for name, carrier in carriers do
			local old = carrier.CFrame
			local new = targets[name]
			local delta = new * old:Inverse()
			-- подложка: ближайшая LiveSurface к исходному месту носителя
			local nearest: BasePart? = nil
			local nearestDistance = 0.4
			for _, backer in backers do
				local distance = (backer.Position - old.Position).Magnitude
				if distance < nearestDistance and not keep[backer] then
					nearest = backer
					nearestDistance = distance
				end
			end
			if nearest then
				nearest.CFrame = delta * nearest.CFrame
				keep[nearest] = true
			end
			carrier.CFrame = new
			keep[carrier] = true
		end
		for _, item in station:GetDescendants() do
			if item:IsA("BasePart") and not keep[item] then
				if item.CanCollide then
					item.Transparency = 1 -- невидимая коллизия остаётся
				else
					item:Destroy()
				end
			end
		end
		placeMeshes(station, stationTemplate, base)
		station:SetAttribute("HubUpgraded", true)
		stationTemplate:Destroy()
	elseif stationTemplate then
		stationTemplate:Destroy()
	end

	-- нижняя точка модели в мире (по углам деталей): габарит модели может быть повёрнут (стойка костюмов лежит боком по осям)
	local function worldBottom(model: Model): number
		local low = math.huge
		for _, item in model:GetDescendants() do
			if item:IsA("BasePart") then
				local half = item.Size / 2
				for sx = -1, 1, 2 do
					for sy = -1, 1, 2 do
						for sz = -1, 1, 2 do
							local point = item.CFrame:PointToWorldSpace(Vector3.new(half.X * sx, half.Y * sy, half.Z * sz))
							low = math.min(low, point.Y)
						end
					end
				end
			end
		end
		return low
	end
	local function groundFrame(model: Model): CFrame
		local pivot = model:GetPivot()
		local origin = Vector3.new(pivot.X, worldBottom(model), pivot.Z)
		local look = pivot.LookVector
		return CFrame.lookAt(origin, origin + Vector3.new(look.X, 0, look.Z))
	end
	-- стойка костюмов и скамья оборудования: видимые детали заменяются мешем, невидимая коллизия остаётся
	for _, entry in {{"SuitRack", "SuitRack"}, {"EquipmentBench", "EquipmentBench"}} do
		local modelName, key = entry[1], entry[2]
		local model = equipment:FindFirstChild(modelName)
		local template = if HUB_ASSETS[key] then loadTemplate(key, HUB_ASSETS[key]) else nil
		if template and model and model:IsA("Model") and not model:GetAttribute("HubUpgraded") then
			local base = groundFrame(model)
			for _, item in model:GetDescendants() do
				if item:IsA("BasePart") then
					if item.CanCollide then
						item.Transparency = 1
					else
						item:Destroy()
					end
				end
			end
			placeMeshes(model, template, base)
			model:SetAttribute("HubUpgraded", true)
		end
		if template then
			template:Destroy()
		end
	end

	-- складной стул у стола миссии (656 деталей): чисто визуальный, меш встаёт на пол по повороту модели
	local deskFolder = hub:FindFirstChild("MissionDesk")
	local foldingChair = deskFolder and deskFolder:FindFirstChild("FoldingChair")
	local chairTemplate = if HUB_ASSETS.FoldingChair then loadTemplate("FoldingChair", HUB_ASSETS.FoldingChair) else nil
	if chairTemplate and foldingChair and foldingChair:IsA("Model") and not foldingChair:GetAttribute("HubUpgraded") then
		local base = groundFrame(foldingChair)
		for _, item in foldingChair:GetDescendants() do
			if item:IsA("BasePart") then
				if item.CanCollide then
					item.Transparency = 1
				else
					item:Destroy()
				end
			end
		end
		placeMeshes(foldingChair, chairTemplate, base)
		foldingChair:SetAttribute("HubUpgraded", true)
	end
	if chairTemplate then
		chairTemplate:Destroy()
	end

	-- кейсы: один меш на все (корпус и крышка перекрашиваются под цвет исходного корпуса), бирка InventoryTag с логикой остаётся
	local cases = hub:FindFirstChild("Cases")
	local caseTemplate = if HUB_ASSETS.HubCase then loadTemplate("HubCase", HUB_ASSETS.HubCase) else nil
	local medicalTemplate = if HUB_ASSETS.HubCaseMed then loadTemplate("HubCaseMed", HUB_ASSETS.HubCaseMed) else nil
	if cases then
		for _, case in cases:GetChildren() do
			local template = if case.Name == "Medical_07" then medicalTemplate else caseTemplate
			if template and case:IsA("Model") and not case:GetAttribute("HubUpgraded") then
				local base = baseFrame(case)
				local bodyColor = Color3.fromRGB(58, 74, 70)
				local bestVolume = 0
				for _, item in case:GetDescendants() do
					if item:IsA("BasePart") and item.Name == "Body" then
						local volume = item.Size.X * item.Size.Y * item.Size.Z
						if volume > bestVolume then
							bestVolume = volume
							bodyColor = item.Color
						end
					end
				end
				local depthToLabel = if case.Name == "Medical_07" then 1.39 else 1.59
				for _, item in case:GetDescendants() do
					if item:IsA("BasePart") then
						if item.Name == "InventoryTag" and item:FindFirstChildWhichIsA("SurfaceGui") then
							item.CFrame = base * CFrame.new(0, 0.6, -depthToLabel)
							-- тёмный текст бирки читается на светлом ярлыке: носитель надписи делаем видимым (на невидимой детали надпись не рисовалась)
							item.Transparency = 0
							item.Color = Color3.fromRGB(226, 222, 204)
							item.Material = Enum.Material.SmoothPlastic
							item.CastShadow = false
							local gui = item:FindFirstChildWhichIsA("SurfaceGui")
							if gui then
								gui.Adornee = item -- у кейсов надпись была привязана к подложке LiveSurface, которой больше нет
							end
						elseif item.CanCollide then
							item.Transparency = 1
						else
							item:Destroy()
						end
					end
				end
				placeMeshes(case, template, base)
				for _, mesh in case:GetChildren() do
					if mesh:IsA("MeshPart") then
						local part = string.match(mesh.Name, "^%w+_(%a+)_%x%x%x%x%x%x$")
						if part == "shell" then
							mesh.Color = bodyColor
						elseif part == "lid" then
							mesh.Color = bodyColor:Lerp(Color3.new(1, 1, 1), 0.06)
						elseif part == "paper" and string.sub(mesh.Name, -6) == "d9d6c8" then
							mesh.Color = Color3.fromRGB(38, 55, 63) -- тёмная табличка под светлым текстом бирки (как подложка LiveSurface у старых кейсов)
						end
					end
				end
				case:SetAttribute("HubUpgraded", true)
			end
		end
	end
	if caseTemplate then
		caseTemplate:Destroy()
	end
	if medicalTemplate then
		medicalTemplate:Destroy()
	end
end

return attachHubUpgrade
