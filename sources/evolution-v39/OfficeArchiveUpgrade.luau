--!strict
-- v43 архивные шкафы (ArchiveCabinet, по ~1800 деталей на шкаф: корпус, полки, 60 папок, две дверцы с ручками) из Blender (ассеты Roblox).
-- Корпус и полки с папками заменяются мешем ArchiveCabinet; каждая дверца получает свой меш (ArchiveDoor / зеркальный ArchiveDoorM).
-- Логика остаётся нетронутой: скрипт ArchiveMotionController двигает модель дверцы через PivotTo вокруг MotionPivot, подсказка «Открыть»
-- (MotionInteraction), угол OpenAngle, табличка IndexLabel/LabelHolder и PlacementPivot шкафа сохраняются. Коллизия корпуса: невидимые стенки
-- CabinetSide/CabinetHorizontal/CabinetBack, у дверцы добавлена невидимая плита DoorCollision. Если ассет не загрузился, шкафы не меняются.
local function attachArchiveUpgrade(office: Instance?)
	if not office then
		return
	end
	local ASSETS: {[string]: number} = {}
	-- @@ARCHIVE_ASSETS@@
	local LOOK: {[string]: Enum.Material} = {metal = Enum.Material.Metal, rubber = Enum.Material.Plastic}
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
			warn("KONTUR archive asset " .. key .. " (" .. tostring(assetId) .. ") failed")
			return nil
		end
		local template = Instance.new("Model")
		template.Name = "Arch_" .. key
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
	local function tpl(key: string): Model?
		local id = ASSETS[key]
		return if id then loadTemplate(key, id) else nil
	end
	local archiveBody, archiveL, archiveR = tpl("ArchiveCabinet"), tpl("ArchiveDoor"), tpl("ArchiveDoorM")
	local glazedBody, glazedL, glazedR = tpl("GlazedCabinet"), tpl("GlazedDoor"), tpl("GlazedDoorM")
	local rack, load = tpl("ShelfRack"), tpl("ShelfLoad")
	local lowBody, lowN, lowM = tpl("LowCabinet"), tpl("LowDoor"), tpl("LowDoorM")
	local fileBody, fileDrawer = tpl("FileCabinet"), tpl("FileDrawer")
	local sortingMesh, cornerMesh, formsMesh = tpl("SortingCabinet"), tpl("CornerShelf"), tpl("FormsCabinet")
	local kBody, sBody, cBody = tpl("KitchenBody"), tpl("SideBody"), tpl("CoffeeBody")
	local kDoor, kDoorM, sDoor, sDoorM = tpl("KitchenDoor"), tpl("KitchenDoorM"), tpl("SideDoor"), tpl("SideDoorM")
	local sinkDoor, coffeeDoor = tpl("SinkDoor"), tpl("CoffeeDoor")
	local lockerBody, lockerDoor = tpl("LockerBody"), tpl("LockerDoor")
	local faBody, faDoor = tpl("FirstAidBody"), tpl("FirstAidDoor")
	local exBody, exDoor = tpl("ExtinguisherBody"), tpl("ExtinguisherDoor")
	local fhBody, fhDoor = tpl("FireHoseBody"), tpl("FireHoseDoor")
	local doLow = lowBody ~= nil and lowN ~= nil and lowM ~= nil
	local doFile = fileBody ~= nil and fileDrawer ~= nil
	local doTypeA = archiveBody ~= nil and archiveL ~= nil and archiveR ~= nil
	local doTypeG = glazedBody ~= nil and glazedL ~= nil and glazedR ~= nil
	if not (doTypeA or doTypeG or rack or doLow or doFile or sortingMesh or cornerMesh or formsMesh or kBody or sBody or cBody or sinkDoor or lockerBody or faBody or exBody or fhBody) then
		return
	end

	-- меняем только пока нет активной аномалии (сценарии хранят позы деталей)
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

	local KEEP_BODY = {PlacementPivot = true, CabinetSide = true, CabinetHorizontal = true, CabinetBack = true}
	local KEEP_DOOR = {MotionPivot = true, MotionInteraction = true, IndexLabel = true, LabelHolder = true, CabinetGlazing = true}
	local KEEP_RACK = {PlacementPivot = true, IndexLabel = true, LabelHolder = true}

	-- шкаф с двумя дверцами: тип A (архивный, глухие дверцы) или G (застеклённый, стекло остаётся деталью игры)
	local function upgradeCabinet(cabinet: Model, body: Model, doorL: Model, doorR: Model, plateX: number, plateWidth: number)
		local pivot = cabinet:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) or cabinet:GetAttribute("ArchiveUpgraded") then
			return
		end
		for _, child in cabinet:GetChildren() do
			if child:IsA("BasePart") then
				if KEEP_BODY[child.Name] then
					if child.Name ~= "PlacementPivot" then
						child.Transparency = 1
						for _, gui in child:GetChildren() do
							if gui:IsA("SurfaceGui") then
								gui:Destroy()
							end
						end
					end
				else
					child:Destroy()
				end
			end
		end
		local copy = body:Clone()
		copy:PivotTo(pivot.CFrame)
		for _, mesh in copy:GetChildren() do
			mesh.Parent = cabinet
		end
		copy:Destroy()
		for _, door in cabinet:GetChildren() do
			if door:IsA("Model") and door:FindFirstChild("OpenAngle") and door.PrimaryPart then
				local hinge = door.PrimaryPart
				local handle = door:FindFirstChild("MotionInteraction")
				local mirrored = false
				if handle and handle:IsA("BasePart") then
					mirrored = hinge.CFrame:ToObjectSpace(handle.CFrame).X > 0
				end
				for _, part in door:GetDescendants() do
					if part:IsA("BasePart") and not KEEP_DOOR[part.Name] then
						part:Destroy()
					end
				end
				local plate = Instance.new("Part")
				plate.Name = "DoorCollision"
				plate.Size = Vector3.new(plateWidth, 7.45, 0.069)
				plate.CFrame = hinge.CFrame * CFrame.new(if mirrored then -plateX else plateX, 0, 0.119)
				plate.Anchored = true
				plate.Transparency = 1
				plate.CanCollide = true
				plate.CanTouch = false
				plate.Parent = door
				local doorCopy = (if mirrored then doorR else doorL):Clone()
				doorCopy:PivotTo(hinge.CFrame)
				for _, mesh in doorCopy:GetChildren() do
					mesh.Parent = door
				end
				doorCopy:Destroy()
			end
		end
		cabinet:SetAttribute("ArchiveUpgraded", true)
	end

	-- открытый стеллаж: каркас (+ ящики и папки у LoadedShelf), метки коробок остаются, коллизия одним невидимым блоком
	local function upgradeRack(shelf: Model, withLoad: boolean)
		local pivot = shelf:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) or shelf:GetAttribute("ArchiveUpgraded") or not rack then
			return
		end
		for _, child in shelf:GetChildren() do
			if child:IsA("BasePart") and not KEEP_RACK[child.Name] then
				child:Destroy()
			end
		end
		local block = Instance.new("Part")
		block.Name = "ShelfCollision"
		block.Size = Vector3.new(4.95, 8.0, 1.85)
		block.CFrame = pivot.CFrame * CFrame.new(0, 4.05, 0)
		block.Anchored = true
		block.Transparency = 1
		block.CanCollide = true
		block.CanTouch = false
		block.Parent = shelf
		for _, template in {rack, if withLoad then load else nil} do
			local copy = template:Clone()
			copy:PivotTo(pivot.CFrame)
			for _, mesh in copy:GetChildren() do
				mesh.Parent = shelf
			end
			copy:Destroy()
		end
		shelf:SetAttribute("ArchiveUpgraded", true)
	end

	local function stamp(template: Model, cf: CFrame, parent: Instance)
		local copy = template:Clone()
		copy:PivotTo(cf)
		for _, mesh in copy:GetChildren() do
			mesh.Parent = parent
		end
		copy:Destroy()
	end
	local function plate(parent: Instance, size: Vector3, cf: CFrame, name: string)
		local block = Instance.new("Part")
		block.Name = name
		block.Size = size
		block.CFrame = cf
		block.Anchored = true
		block.Transparency = 1
		block.CanCollide = true
		block.CanTouch = false
		block.Parent = parent
	end
	-- корпус: оставляем нужные детали (невидимыми, если collide=true), остальное удаляем, ставим меш
	local function stripBody(model: Model, keep: {[string]: boolean}, hideKept: boolean)
		for _, child in model:GetChildren() do
			if child:IsA("BasePart") and not (keep[child.Name] or string.find(child.Name, "BodyCollision")) then
				child:Destroy()
			elseif child:IsA("BasePart") and hideKept and child.Name ~= "PlacementPivot" and not string.find(child.Name, "BodyCollision") then
				child.Transparency = 1
				for _, gui in child:GetChildren() do
					if gui:IsA("SurfaceGui") then
						gui:Destroy()
					end
				end
			end
		end
	end

	-- низкий шкаф с двумя дверцами: расположение дверцы определяется по самой большой её панели относительно петли
	local function upgradeLow(cabinet: Model)
		local pivot = cabinet:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) or cabinet:GetAttribute("ArchiveUpgraded") then
			return
		end
		stripBody(cabinet, {PlacementPivot = true, LowCabinetSide = true, LowCabinetCap = true, LowCabinetBack = true}, true)
		stamp(lowBody :: Model, pivot.CFrame, cabinet)
		for _, door in cabinet:GetChildren() do
			if door:IsA("Model") and door:FindFirstChild("OpenAngle") and door.PrimaryPart then
				local hinge = door.PrimaryPart
				local biggest: BasePart? = nil
				local volume = 0
				for _, part in door:GetDescendants() do
					if part:IsA("BasePart") and string.find(part.Name, "^CabinetDoor") then
						local v = part.Size.X * part.Size.Y * part.Size.Z
						if v > volume then
							volume = v
							biggest = part
						end
					end
				end
				local rel = if biggest then hinge.CFrame:ToObjectSpace(biggest.CFrame).Position else Vector3.new(1, 0, 0.11)
				local sx = if rel.X >= 0 then 1 else -1
				local sz = if rel.Z >= 0 then 1 else -1
				for _, part in door:GetDescendants() do
					if part:IsA("BasePart") and part.Name ~= "MotionPivot" and part.Name ~= "MotionInteraction" then
						part:Destroy()
					end
				end
				plate(door, Vector3.new(1.98, 2.75, 0.07), hinge.CFrame * CFrame.new(sx * 1.0, 0, sz * 0.11), "DoorCollision")
				local cf = hinge.CFrame
				local template = if sx == 1 then lowN :: Model else lowM :: Model
				if sz < 0 then
					cf = cf * CFrame.Angles(0, math.pi, 0)
					template = if sx == 1 then lowM :: Model else lowN :: Model
				end
				stamp(template, cf, door)
			end
		end
		cabinet:SetAttribute("ArchiveUpgraded", true)
	end

	-- картотека с четырьмя выдвижными ящиками (SlideDistance); таблички и подсказки ящиков остаются
	local function upgradeFile(cabinet: Model)
		local pivot = cabinet:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) or cabinet:GetAttribute("ArchiveUpgraded") then
			return
		end
		stripBody(cabinet, {PlacementPivot = true, DrawerCabinetSide = true, DrawerCabinetCap = true, DrawerCabinetBack = true}, true)
		stamp(fileBody :: Model, pivot.CFrame, cabinet)
		for _, drawer in cabinet:GetChildren() do
			if drawer:IsA("Model") and drawer:FindFirstChild("SlideDistance") and drawer.PrimaryPart then
				local hinge = drawer.PrimaryPart
				local handle = drawer:FindFirstChild("MotionInteraction")
				local frontSign = -1
				if handle and handle:IsA("BasePart") and hinge.CFrame:ToObjectSpace(handle.CFrame).Z > 0 then
					frontSign = 1
				end
				for _, part in drawer:GetDescendants() do
					if part:IsA("BasePart") and not (part.Name == "MotionPivot" or part.Name == "MotionInteraction" or part.Name == "IndexLabel" or part.Name == "LabelHolder") then
						part:Destroy()
					end
				end
				plate(drawer, Vector3.new(1.8, 1.3, 0.3), hinge.CFrame * CFrame.new(0, 0, frontSign * 1.2), "DrawerCollision")
				stamp(fileDrawer :: Model, if frontSign < 0 then hinge.CFrame else hinge.CFrame * CFrame.Angles(0, math.pi, 0), drawer)
			end
		end
		cabinet:SetAttribute("ArchiveUpgraded", true)
	end

	-- статичный предмет: меш заменяет детали, метки остаются, коллизия блоками (CFrame в осях PlacementPivot)
	local function upgradeStatic(model: Model, mesh: Model, keep: {[string]: boolean}, blocks: {{Vector3}})
		local pivot = model:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) or model:GetAttribute("ArchiveUpgraded") then
			return
		end
		stripBody(model, keep, false)
		for i, block in blocks do
			plate(model, block[2], pivot.CFrame * CFrame.new(block[1]), "StaticCollision" .. i)
		end
		stamp(mesh, pivot.CFrame, model)
		model:SetAttribute("ArchiveUpgraded", true)
	end

	-- кухонная мебель: дверцы двигает KitchenDoorController (PivotTo вокруг HingePivot); подсказка висит на одной детали PullHandle,
	-- её оставляем невидимой. Тело меняется только у KitchenCabinets/SideCabinet/CoffeeCabinet (у SinkModule остаются раковина и кран).
	local function upgradeKitchen(model: Model, body: Model?, width: number, height: number, pickDoor: (Model, boolean) -> Model?)
		if model:GetAttribute("ArchiveUpgraded") then
			return
		end
		local pivot = model:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) then
			return
		end
		if body then
			stripBody(model, {PlacementPivot = true}, false)
			stamp(body, pivot.CFrame, model)
		end
		for _, door in model:GetChildren() do
			if door:IsA("Model") and door.PrimaryPart and door:FindFirstChild("OpenAngle") then
				local angleValue = door:FindFirstChild("OpenAngle") :: Instance
				local mirrored = angleValue:IsA("NumberValue") and (angleValue :: NumberValue).Value < 0
				local template = pickDoor(door, mirrored)
				if template then
					local hinge = door.PrimaryPart
					local doorWidth = width
					for _, part in door:GetDescendants() do
						if part:IsA("BasePart") and part ~= hinge then
							if part:FindFirstChildWhichIsA("ProximityPrompt") then
								part.Transparency = 1
								part.CanCollide = false
							else
								part:Destroy()
							end
						end
					end
					plate(door, Vector3.new(doorWidth, height, 0.08), hinge.CFrame * CFrame.new((if mirrored then -1 else 1) * doorWidth / 2, 0, 0), "DoorCollision")
					stamp(template, hinge.CFrame, door)
				end
			end
		end
		model:SetAttribute("ArchiveUpgraded", true)
	end

	-- личные шкафчики стартовой комнаты (две дверцы, скрипт DoorController двигает их вокруг HingePivot)
	local function upgradeLockers(model: Model)
		local pivot = model:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) or model:GetAttribute("ArchiveUpgraded") or not lockerBody or not lockerDoor then
			return
		end
		stripBody(model, {PlacementPivot = true, LockerSide = true, LockerHorizontal = true, LockerBack = true}, true)
		stamp(lockerBody, pivot.CFrame, model)
		for _, door in model:GetChildren() do
			if door:IsA("Model") and door.PrimaryPart and door:FindFirstChild("OpenAngle") then
				local hinge = door.PrimaryPart
				for _, part in door:GetDescendants() do
					if part:IsA("BasePart") and part ~= hinge and part.Name ~= "LockerLabel" then
						if part:FindFirstChildWhichIsA("ProximityPrompt") then
							part.Transparency = 1
							part.CanCollide = false
						else
							part:Destroy()
						end
					end
				end
				plate(door, Vector3.new(1.58, 4.24, 0.06), hinge.CFrame * CFrame.new(0.79, 0, 0), "DoorCollision")
				stamp(lockerDoor, hinge.CFrame, door)
			end
		end
		model:SetAttribute("ArchiveUpgraded", true)
	end

	-- настенные коридорные шкафы (аптечка, огнетушитель, пожарный кран): один корпус с содержимым и одна дверь с петлёй HingePivot,
	-- которую двигает CabinetDoorController. Остаются: PlacementPivot, V09WallCollision, метки-GUI (EquipmentLabel, MedicalMark, CabinetHeader,
	-- HoseHeader), стекло DoorGlazing, невидимая деталь подсказки PullHandle. Метки сдвигаются на 1 см вперёд, чтобы не мерцать на грани меша.
	local WALL_BODY_KEEP = {PlacementPivot = true, V09WallCollision = true, EquipmentLabel = true}
	local WALL_DOOR_KEEP = {MedicalMark = true, CabinetHeader = true, HoseHeader = true, DoorGlazing = true}
	local function upgradeWall(model: Model, body: Model, doorMesh: Model, doorSize: Vector3)
		local pivot = model:FindFirstChild("PlacementPivot")
		if not (pivot and pivot:IsA("BasePart")) or model:GetAttribute("ArchiveUpgraded") then
			return
		end
		stripBody(model, WALL_BODY_KEEP, false)
		for _, part in model:GetChildren() do
			if part:IsA("BasePart") and part.Name == "EquipmentLabel" then
				part.CFrame = part.CFrame + pivot.CFrame:VectorToWorldSpace(Vector3.new(0, 0, -0.012))
			end
		end
		stamp(body, pivot.CFrame, model)
		for _, door in model:GetChildren() do
			if door:IsA("Model") and door.PrimaryPart and door:FindFirstChild("OpenAngle") then
				local hinge = door.PrimaryPart
				for _, part in door:GetDescendants() do
					if part:IsA("BasePart") and part ~= hinge and not WALL_DOOR_KEEP[part.Name] then
						if part:FindFirstChildWhichIsA("ProximityPrompt") then
							part.Transparency = 1
							part.CanCollide = false
						else
							part:Destroy()
						end
					elseif part:IsA("BasePart") and part ~= hinge and part.Name ~= "DoorGlazing" then
						part.CFrame = part.CFrame + hinge.CFrame:VectorToWorldSpace(Vector3.new(0, 0, -0.012))
					end
				end
				plate(door, Vector3.new(doorSize.X, doorSize.Y, 0.06), hinge.CFrame * CFrame.new(doorSize.X / 2, 0, 0), "DoorCollision")
				stamp(doorMesh, hinge.CFrame, door)
			end
		end
		model:SetAttribute("ArchiveUpgraded", true)
	end

	local swapped = 0
	for _, item in office:GetDescendants() do
		if item:IsA("Model") then
			local did = false
			if doTypeA and string.find(item.Name, "ArchiveCabinet$") and item:FindFirstChild("ArchiveMotionController") then
				upgradeCabinet(item, archiveBody :: Model, archiveL :: Model, archiveR :: Model, -0.972, 1.92)
				did = true
			elseif doTypeG and string.find(item.Name, "GlazedCabinet$") and item:FindFirstChild("ArchiveMotionController") then
				upgradeCabinet(item, glazedBody :: Model, glazedL :: Model, glazedR :: Model, -0.831, 1.69)
				did = true
			elseif rack and string.find(item.Name, "LoadedShelf$") then
				upgradeRack(item, load ~= nil)
				did = true
			elseif rack and string.find(item.Name, "MetalShelf$") then
				upgradeRack(item, false)
				did = true
			elseif lockerBody and string.find(item.Name, "PersonalLockers$") then
				upgradeLockers(item)
				did = true
			elseif faBody and faDoor and string.find(item.Name, "FirstAidCabinet$") then
				upgradeWall(item, faBody, faDoor, Vector3.new(1.92, 2.36, 0))
				did = true
			elseif exBody and exDoor and string.find(item.Name, "ExtinguisherCabinet$") then
				upgradeWall(item, exBody, exDoor, Vector3.new(1.64, 2.92, 0))
				did = true
			elseif fhBody and fhDoor and string.find(item.Name, "FireHoseCabinet$") then
				upgradeWall(item, fhBody, fhDoor, Vector3.new(2.38, 2.96, 0))
				did = true
			elseif kDoor and kDoorM and kBody and string.find(item.Name, "KitchenCabinets$") then
				upgradeKitchen(item, kBody, 1.75, 2.2, function(_: Model, mirrored: boolean): Model? return if mirrored then kDoorM else kDoor end)
				did = true
			elseif sDoor and sDoorM and sBody and string.find(item.Name, "SideCabinet$") then
				upgradeKitchen(item, sBody, 1.5, 2.42, function(_: Model, mirrored: boolean): Model? return if mirrored then sDoorM else sDoor end)
				did = true
			elseif coffeeDoor and cBody and string.find(item.Name, "CoffeeCabinet$") then
				upgradeKitchen(item, cBody, 2.18, 2.42, function(): Model? return coffeeDoor end)
				did = true
			elseif sinkDoor and string.find(item.Name, "SinkModule$") then
				upgradeKitchen(item, nil, 2.76, 2.42, function(): Model? return sinkDoor end)
				did = true
			elseif doLow and string.find(item.Name, "LowCabinet$") then
				upgradeLow(item)
				did = true
			elseif doFile and string.find(item.Name, "FileCabinet$") and item:FindFirstChild("ArchiveMotionController") then
				upgradeFile(item)
				did = true
			elseif sortingMesh and string.find(item.Name, "SortingCabinet$") then
				upgradeStatic(item, sortingMesh, {PlacementPivot = true, IndexLabel = true, LabelHolder = true}, {{Vector3.new(0, 3.0, 0), Vector3.new(3.75, 5.8, 1.9)}})
				did = true
			elseif cornerMesh and string.find(item.Name, "CornerShelf$") then
				upgradeStatic(item, cornerMesh, {PlacementPivot = true}, {{Vector3.new(-0.025, 3.2, 0.75), Vector3.new(2.85, 6.4, 1.3)}, {Vector3.new(0.75, 3.2, -0.65), Vector3.new(1.3, 6.4, 1.5)}})
				did = true
			elseif formsMesh and string.find(item.Name, "FormsCabinet$") then
				upgradeStatic(item, formsMesh, {PlacementPivot = true, ShelfLegend = true, InspectionExample = true}, {})
				did = true
			end
			if did then
				swapped += 1
				if swapped % 2 == 0 then
					task.wait()
				end
			end
		end
	end
end

return attachArchiveUpgrade
