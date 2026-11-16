--!strict
-- Мышь и коврик из Blender (уровень 5). Ассет MouseSetV2 (Roblox) заменяет детали Mat и Mouse модели MouseAndMat на рабочих местах
-- (и в копиях KE_MouseAndMat, которые OfficeEastDressing делает для восточного зала). Расположение берётся от коврика (начало ассета лежит
-- на 0.077 над центром коврика), поэтому ориентация модели любая. Если ассет не загрузился, остаётся прежний вид.
-- Клавиатуры меняет OfficeFurnitureUpgrade (слой подставляет туда id нового ассета Keyboard).
-- Подключает слой sources/input-devices/build_place.py: функция вставляется перед attachFurnitureUpgrade, запуск в отдельном потоке.
local function attachMouseUpgrade(office: Instance?)
	if not office then
		return
	end
	local ASSETS: {[string]: number} = {}
	-- @@INPUT_ASSETS@@
	local assetId = ASSETS.MouseSetV2
	if not assetId then
		warn("KONTUR mouse upgrade: no asset id")
		return
	end
	local LOOK: {[string]: Enum.Material} = {
		mat_fabric = Enum.Material.Plastic, mat_edge = Enum.Material.Plastic, mat_label = Enum.Material.Plastic, mouse_led = Enum.Material.Neon,
	}
	local container: Instance? = nil
	local lastError: any = nil
	for attempt = 1, 4 do
		local ok, result = pcall(function()
			return game:GetService("InsertService"):LoadAsset(assetId)
		end)
		if ok and result then
			container = result
			break
		end
		lastError = result
		if attempt < 4 then
			task.wait(4)
		end
	end
	if not container then
		warn("KONTUR mouse asset " .. tostring(assetId) .. " failed: " .. tostring(lastError))
		return
	end
	local template = Instance.new("Model")
	template.Name = "MouseSetTemplate"
	local broken = false
	for _, mesh in container:GetDescendants() do
		if mesh:IsA("MeshPart") then
			if mesh.MeshId == "" then
				broken = true
			end
			local suffix, hex = string.match(mesh.Name, "^MouseSetV2_(.+)_(%x%x%x%x%x%x)$")
			if hex then
				mesh.Color = Color3.fromHex(hex)
			end
			mesh:ClearAllChildren()
			mesh.Anchored = true
			mesh.CanCollide = false
			mesh.CanTouch = false
			mesh.CanQuery = false
			mesh.Material = LOOK[suffix or ""] or Enum.Material.SmoothPlastic
			mesh.Parent = template
		end
	end
	container:Destroy()
	if broken or #template:GetChildren() == 0 then
		warn("KONTUR mouse asset has no usable meshes")
		template:Destroy()
		return
	end
	template.WorldPivot = CFrame.new()
	local swapped = 0
	local function swapIn(root: Instance)
		for _, model in root:GetDescendants() do
			if model:IsA("Model") and (model.Name == "MouseAndMat" or model.Name == "KE_MouseAndMat") and not model:GetAttribute("InputUpgraded") then
				local mat, mouse = model:FindFirstChild("Mat"), model:FindFirstChild("Mouse")
				if mat and mouse and mat:IsA("BasePart") and mouse:IsA("BasePart") then
					if math.abs(mat.Size.X - 0.551) < 0.02 and math.abs(mat.Size.Z - 0.72) < 0.02 then
						local pivot = model:GetPivot()
						local copy = template:Clone()
						copy:PivotTo(mat.CFrame * CFrame.new(0, 0.077, 0))
						for _, mesh in copy:GetChildren() do
							mesh.Parent = model
						end
						copy:Destroy()
						mat:Destroy()
						mouse:Destroy()
						if not model.PrimaryPart then
							model.WorldPivot = pivot
						end
						model:SetAttribute("InputUpgraded", true)
						swapped += 1
						if swapped % 4 == 0 then
							task.wait()
						end
					else
						warn("KONTUR mouse upgrade: unexpected mat size at " .. model:GetFullName())
					end
				end
			end
		end
	end
	local ok1, err1 = pcall(swapIn, office)
	if not ok1 then
		warn("KONTUR mouse upgrade failed: " .. tostring(err1))
	end
	-- копии рабочих мест восточного зала появляются позже (OfficeEastDressing): второй проход
	local east = office:WaitForChild("KonturEast", 120)
	if east then
		task.wait(4)
		local ok2, err2 = pcall(swapIn, east)
		if not ok2 then
			warn("KONTUR mouse upgrade (east) failed: " .. tostring(err2))
		end
	end
	template:Destroy()
end

