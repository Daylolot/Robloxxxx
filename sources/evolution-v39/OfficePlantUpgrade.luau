--!strict
-- v42 растения и декор столов из Blender (загруженные ассеты Roblox) вместо клиентского EditableMesh, который не рисовался
-- (у клиента всего 3 слота, и после Destroy меш пропадает). Повторяет расстановку старого RoomPlants.client: RubberPlant_* получают фикус,
-- лилию или монстеру по кругу; на журнальные, переговорные, боковые столы, шкафчики и ресепшен ставятся ваза, раскрытая книга, стопка и ряд
-- книг (если место свободно); в свободные углы комнат ставятся напольные растения. Старые детали RubberPlant_* заменяются.
-- Подключает сборщик build_place.py: attachPlantUpgrade(office) в отдельном потоке, id ассетов подставляются вместо метки.
local function attachPlantUpgrade(office: Instance?)
	if not office then
		return
	end
	local rooms = office:FindFirstChild("Rooms")
	if not rooms then
		return
	end
	local ASSETS: {[string]: number} = {}
	-- @@PLANT_ASSETS@@
	if next(ASSETS) == nil then
		return
	end
	local function loadTemplate(key: string, assetId: number): Model?
		local container: Instance? = nil
		local lastError: any = nil
		for _ = 1, 4 do
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
			warn("KONTUR plant asset " .. key .. " (" .. tostring(assetId) .. ") failed: " .. tostring(lastError))
			return nil
		end
		local template = Instance.new("Model")
		template.Name = "Plant_" .. key
		for _, mesh in container:GetDescendants() do
			if mesh:IsA("MeshPart") then
				local _, hex = string.match(mesh.Name, "^" .. key .. "_(.+)_(%x%x%x%x%x%x)$")
				if hex then
					mesh.Color = Color3.fromHex(hex)
				end
				mesh.Anchored = true
				mesh.CanCollide = false
				mesh.CanTouch = false
				mesh.CanQuery = false
				mesh.Material = Enum.Material.SmoothPlastic
				mesh.DoubleSided = true -- листья это односторонние сетки
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
	local templates: {[string]: Model} = {}
	local pending = 0
	for key, assetId in ASSETS do
		pending += 1
		task.spawn(function()
			local template = loadTemplate(key, assetId)
			if template then
				templates[key] = template
			end
			pending -= 1
		end)
	end
	local waited = 0
	while pending > 0 and waited < 120 do
		task.wait(0.5)
		waited += 0.5
	end

	local folder = Instance.new("Folder")
	folder.Name = "KonturPlants"
	folder.Parent = office
	local SPECIES = {"PlantFig", "PlantLily", "PlantMonstera"}
	local SCALE: {[string]: number} = {PlantFig = 1.0, PlantLily = 1.0, PlantMonstera = 1.0}
	-- столкновение по горшку: невидимый цилиндр по форме горшка с блюдцем (диаметр, высота), а не по всему кусту
	local POT: {[string]: {number}} = {PlantFig = {2.3, 1.5}, PlantLily = {2.1, 1.4}, PlantMonstera = {2.4, 1.5}}
	local function put(key: string, cframe: CFrame, scale: number?, name: string): Model?
		local template = templates[key]
		if not template then
			return nil
		end
		local copy = template:Clone()
		if scale and scale ~= 1 then
			copy:ScaleTo(scale)
		end
		copy:PivotTo(cframe)
		copy.Name = name
		copy.Parent = folder
		local pot = POT[key]
		if pot then
			local hit = Instance.new("Part")
			hit.Name = "PotCollision"
			hit.Shape = Enum.PartType.Cylinder
			hit.Size = Vector3.new(pot[2] :: number, pot[1] :: number, pot[1] :: number)
			hit.CFrame = CFrame.new(cframe.Position + Vector3.new(0, (pot[2] :: number) / 2, 0)) * CFrame.Angles(0, 0, math.rad(90))
			hit.Anchored = true
			hit.Transparency = 1
			hit.CanCollide = true
			hit.CanTouch = false
			hit.CanQuery = false
			hit.CastShadow = false
			hit.Parent = copy
		end
		return copy
	end

	-- RubberPlant_*: старый вид (13–25 простых деталей) заменяется
	local index = 0
	for _, model in office:GetDescendants() do
		if model:IsA("Model") and string.find(model.Name, "^RubberPlant_") and not model:IsDescendantOf(folder) then
			index += 1
			local key = SPECIES[(index - 1) % 3 + 1]
			if templates[key] then
				local box = model:GetBoundingBox()
				local yaw = math.rad((index * 137) % 360)
				local px, pz = box.X, box.Position.Z
				-- выход из стартовой комнаты (проём в восточной стене, z 70–75): растение не должно стоять перед ним
				if px > 986 and px < 1002 and pz > 67 and pz < 78 then
					px, pz = 979.4, 60.8
				end
				put(key, CFrame.new(px, 0.1, pz) * CFrame.Angles(0, yaw, 0), SCALE[key], "Plant_" .. index)
				for _, item in model:GetDescendants() do
					if item:IsA("BasePart") then
						if item.CanCollide then
							item.Transparency = 1
						else
							item:Destroy()
						end
					end
				end
			end
		end
	end

	-- декор столов
	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = {folder}
	local PLACEMENTS = {
		{names = {"CoffeeTable"}, key = "DecorVase", fx = 0.28, fz = 0, yaw = 20, foot = Vector3.new(0.9, 2.0, 0.9)},
		{names = {"MeetingTable"}, key = "DecorVase", fx = 0.3, fz = 0, yaw = 40, foot = Vector3.new(0.9, 2.0, 0.9)},
		{names = {"SideTable"}, key = "DecorVase", fx = 0.0, fz = 0, yaw = 70, foot = Vector3.new(0.9, 2.0, 0.9)},
		{names = {"CoffeeTable"}, key = "DecorOpenBook", fx = -0.2, fz = 0.12, yaw = 15, foot = Vector3.new(1.7, 0.35, 1.2)},
		{names = {"MeetingTable"}, key = "DecorOpenBook", fx = -0.3, fz = 0.18, yaw = -12, foot = Vector3.new(1.7, 0.35, 1.2)},
		{names = {"MeetingTable"}, key = "DecorBookStack", fx = 0.05, fz = -0.2, yaw = 25, foot = Vector3.new(1.1, 0.9, 1.1)},
		{names = {"SideTable"}, key = "DecorBookStack", fx = -0.25, fz = 0, yaw = 10, foot = Vector3.new(1.1, 0.9, 1.1)},
		{names = {"LowCabinet", "SideCabinet", "FileCabinet"}, key = "DecorBookRow", fx = -0.15, fz = 0, yaw = 0, foot = Vector3.new(2.3, 1.3, 0.9)},
		{names = {"ReceptionDesk"}, key = "DecorBookStack", fx = 0.0, fz = 0.1, yaw = -8, foot = Vector3.new(1.1, 0.9, 1.1)},
	}
	local count = 0
	for _, model in rooms:GetDescendants() do
		if model:IsA("Model") and not model:IsDescendantOf(folder) then
			local stripped = string.gsub(model.Name, "^V%d+_%d+_", "")
			for _, placement in PLACEMENTS do
				if table.find(placement.names, stripped) and templates[placement.key] and model:FindFirstAncestor("Rooms") and (model:FindFirstAncestor("Rooms") :: Instance).Parent == office then
					local box, size = model:GetBoundingBox()
					local chosen: CFrame? = nil
					for _, multiplier in {1, -1, 0, 0.5, -0.5} do
						local top = box * CFrame.new(size.X * placement.fx * multiplier, size.Y / 2, size.Z * placement.fz)
						local probe = CFrame.new(top.Position + Vector3.new(0, placement.foot.Y / 2 + 0.08, 0)) * (top - top.Position)
						local blocked = false
						for _, hit in workspace:GetPartBoundsInBox(probe, placement.foot, params) do
							if hit.Transparency < 1 and not hit:IsDescendantOf(model) then
								blocked = true
								break
							end
						end
						if not blocked then
							chosen = top
							break
						end
					end
					if chosen then
						count += 1
						put(placement.key, CFrame.new(chosen.Position) * CFrame.Angles(0, math.atan2(-chosen.LookVector.X, -chosen.LookVector.Z) + math.rad(placement.yaw + count * 7), 0), 1, placement.key .. "_" .. count)
					end
				end
			end
		end
	end

	-- напольные растения в свободных углах комнат
	local ROOM_CORNERS = {
		{x0 = 961.5, x1 = 1002.5, z0 = 8, z1 = 52, n = 3}, {x0 = 1006, x1 = 1058, z0 = 7, z1 = 59, n = 3}, {x0 = 1062, x1 = 1116, z0 = 8, z1 = 60, n = 3},
		{x0 = 996, x1 = 1034, z0 = -32, z1 = 0, n = 2}, {x0 = 1030, x1 = 1100, z0 = -32, z1 = 0, n = 3}, {x0 = 974, x1 = 1002, z0 = 53.5, z1 = 76.5, n = 1},
	}
	local extra = 0
	local order = {"PlantMonstera", "PlantFig", "PlantLily"}
	for _, corner in ROOM_CORNERS do
		local inset = 3.1
		local candidates = {
			Vector2.new(corner.x0 + inset, corner.z0 + inset), Vector2.new(corner.x1 - inset, corner.z0 + inset),
			Vector2.new(corner.x0 + inset, corner.z1 - inset), Vector2.new(corner.x1 - inset, corner.z1 - inset),
		}
		local placedHere = 0
		for _, candidate in candidates do
			if placedHere >= corner.n then
				break
			end
			-- не у выхода из стартовой комнаты (проём в восточной стене, z 70–75)
			local blocked = candidate.X > 990 and candidate.X < 1002 and candidate.Y > 66 and candidate.Y < 78
			for _, hit in workspace:GetPartBoundsInBox(CFrame.new(candidate.X, 3.2, candidate.Y), Vector3.new(3.2, 4, 3.2), params) do
				if hit.Transparency < 1 then
					blocked = true
					break
				end
			end
			if not blocked then
				extra += 1
				placedHere += 1
				local key = order[(extra - 1) % 3 + 1]
				put(key, CFrame.new(candidate.X, 0.1, candidate.Y) * CFrame.Angles(0, math.rad((extra * 53) % 360), 0), SCALE[key], "PlantExtra_" .. extra)
			end
		end
	end
	for _, template in templates do
		template:Destroy()
	end
	if game:GetService("RunService"):IsStudio() then
		office:SetAttribute("KonturPlantsPlaced", index .. " plants, " .. count .. " decor, " .. extra .. " extra")
	end
end

return attachPlantUpgrade
