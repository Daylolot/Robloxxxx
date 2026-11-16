--!strict
-- v42 аномалии основной карты: статичные объекты заменены моделями из Blender (загруженные ассеты Roblox).
-- Принтер (Rooms.CENTER.Printer): невидимая коллизия PrinterBody остаётся, остальные детали заменяются мешем.
-- Зеркала (V09_0293/0294 в MEN, V09_0316/0317 в WOMEN): MirrorPanel (живое отражение), MirrorBacking и PlacementPivot остаются,
-- рама из ~90 мелких деталей заменяется мешем. Если ассет не загрузился, объект не меняется.
-- Подключает сборщик build_place.py: attachAnomalyUpgrade(office) в отдельном потоке, id ассетов подставляются вместо метки.
local function attachAnomalyUpgrade(office: Instance?)
	if not office then
		return
	end
	local rooms = office:FindFirstChild("Rooms")
	if not rooms then
		return
	end
	local ASSETS: {[string]: number} = {}
	-- @@ANOMALY_ASSETS@@
	local LOOK: {[string]: {material: Enum.Material, transparency: number}} = {
		alu = {material = Enum.Material.Metal, transparency = 0}, metal = {material = Enum.Material.Metal, transparency = 0},
		metal_dark = {material = Enum.Material.Metal, transparency = 0},
		display = {material = Enum.Material.Neon, transparency = 0}, glass = {material = Enum.Material.Glass, transparency = 0.5},
	}
	local function loadTemplate(key: string, assetId: number): Model?
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
			warn("KONTUR anomaly asset " .. key .. " (" .. tostring(assetId) .. ") failed: " .. tostring(lastError))
			return nil
		end
		local template = Instance.new("Model")
		template.Name = "Anom_" .. key
		for _, mesh in container:GetDescendants() do
			if mesh:IsA("MeshPart") then
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
	-- после удаления деталей пивот модели без PrimaryPart мог бы сдвинуться: возвращаем прежний
	local function keepPivot(model: Model, pivot: CFrame)
		if (model:GetPivot().Position - pivot.Position).Magnitude > 0.01 then
			model.WorldPivot = pivot
		end
	end
	local function placeMeshes(model: Model, template: Model, base: CFrame)
		local copy = template:Clone()
		copy:PivotTo(base)
		for _, item in copy:GetChildren() do
			item.Parent = model
		end
		copy:Destroy()
	end

	-- подмена идёт только пока активной аномалии нет: сценарий не теряет детали, которые он двигает или красит
	local reportState = office:FindFirstChild("AnomalyReportState")
	local function waitIdle()
		if not reportState then
			return
		end
		for _ = 1, 150 do
			local scenario = reportState:GetAttribute("OfficeDetailScenario")
			if scenario == nil or scenario == "Clear" then
				return
			end
			task.wait(1)
		end
	end

	-- принтер: начало меша = центр основания корпуса (корпус на 0,6 стада ниже центра модели), перед по взгляду модели
	local printerModel = rooms:FindFirstChild("CENTER") and rooms.CENTER:FindFirstChild("Printer")
	local printerTemplate = if ASSETS.Printer then loadTemplate("Printer", ASSETS.Printer) else nil
	if printerTemplate and printerModel and printerModel:IsA("Model") and not printerModel:GetAttribute("AnomalyUpgraded") then
		waitIdle()
		local pivot = printerModel:GetPivot()
		local look = pivot.LookVector
		local origin = Vector3.new(pivot.X, pivot.Y - 0.6, pivot.Z)
		local base = CFrame.lookAt(origin, origin + Vector3.new(look.X, 0, look.Z))
		-- логику аномалии держат детали OutputSlot (метка подсказки, карточка, направление), Paper (размер и цвет листа) и Display
		-- (SurfaceGui со статусом): они остаются невидимыми, иначе PrinterRound теряет подсказку и табло
		local logicParts = {OutputSlot = true, Paper = true, Display = true}
		for _, item in printerModel:GetDescendants() do
			if item:IsA("BasePart") then
				if item.CanCollide or logicParts[item.Name] or item:FindFirstChildWhichIsA("SurfaceGui") or item:FindFirstChildWhichIsA("Attachment") then
					item.Transparency = 1 -- корпус остаётся невидимой коллизией
				else
					item:Destroy()
				end
			end
		end
		placeMeshes(printerModel, printerTemplate, base)
		-- статус «ГОТОВ / ПЕЧАТЬ / ЧИТАТЬ» ложится на экран меша: чуть впереди него и с тем же наклоном панели
		local display = printerModel:FindFirstChild("Display")
		if display and display:IsA("BasePart") then
			display.CFrame = base * CFrame.new(0.48, 1.13, -0.64) * CFrame.Angles(0.22, 0, 0)
		end
		local paperPart = printerModel:FindFirstChild("Paper")
		if paperPart and paperPart:IsA("BasePart") then
			-- PrinterRound.reset() возвращает сохранённую прозрачность листа; лист уже есть в меше, поэтому снова прячем
			paperPart:GetPropertyChangedSignal("Transparency"):Connect(function()
				if paperPart.Transparency ~= 1 then
					paperPart.Transparency = 1
				end
			end)
		end
		printerModel:SetAttribute("AnomalyUpgraded", true)
	end
	if printerTemplate then
		printerTemplate:Destroy()
	end

	-- зеркала
	local mirrorTemplate = if ASSETS.MirrorFrame then loadTemplate("MirrorFrame", ASSETS.MirrorFrame) else nil
	if mirrorTemplate then
		local keepNames = {MirrorPanel = true, MirrorBacking = true, PlacementPivot = true}
		local mirrorIds = {V09_0293 = true, V09_0294 = true, V09_0316 = true, V09_0317 = true}
		for _, roomName in {"MEN", "WOMEN"} do
			local room = rooms:FindFirstChild(roomName)
			if room then
				for _, model in room:GetChildren() do
					local mirrorId = string.match(model.Name, "^(V09_%d+)_Mirror$")
					if model:IsA("Model") and mirrorId and mirrorIds[mirrorId] and not model:GetAttribute("AnomalyUpgraded") then
						waitIdle()
						local pivot = model:GetPivot()
						for _, item in model:GetDescendants() do
							if item:IsA("BasePart") and not keepNames[item.Name] then
								item:Destroy()
							end
						end
						placeMeshes(model, mirrorTemplate, pivot)
						keepPivot(model, pivot)
						model:SetAttribute("AnomalyUpgraded", true)
					end
				end
			end
		end
		mirrorTemplate:Destroy()
	end

	-- картины архива (ArchiveArtSwap двигает модели целиком): рама, подложка, винты и бамперы заменяются мешем; полотно, паспарту,
	-- надпись сзади (GUI) и PlacementPivot остаются
	local frameTemplate = if ASSETS.ArtFrame then loadTemplate("ArtFrame", ASSETS.ArtFrame) else nil
	local archive = rooms:FindFirstChild("NW")
	if frameTemplate and archive then
		local keepFrame = {EditableArtwork = true, ArchivalMat = true, RearInventoryLabel = true, PlacementPivot = true}
		for _, name in {"V09_0340_WorldTrade", "V09_0341_GrowthTechnology"} do
			local model = archive:FindFirstChild(name)
			if model and model:IsA("Model") and not model:GetAttribute("AnomalyUpgraded") then
				waitIdle()
				local pivot = model:GetPivot()
				for _, item in model:GetDescendants() do
					if item:IsA("BasePart") and not keepFrame[item.Name] and not item:FindFirstChildWhichIsA("SurfaceGui") then
						item:Destroy()
					end
				end
				placeMeshes(model, frameTemplate, pivot)
				keepPivot(model, pivot)
				model:SetAttribute("AnomalyUpgraded", true)
			end
		end
	end
	if frameTemplate then
		frameTemplate:Destroy()
	end

	-- настенный календарь (ArchiveCalendarShift двигает модель и берёт HangingLoop_Joint для булавки): подложка, листы, спираль и петля
	-- заменяются мешем; печатная страница WallCalendarPrint (даты), три HangingLoop_Joint и PlacementPivot остаются
	local calendarTemplate = if ASSETS.WallCalendar then loadTemplate("WallCalendar", ASSETS.WallCalendar) else nil
	local calendar = archive and archive:FindFirstChild("V09_0465_WallCalendar")
	if calendarTemplate and calendar and calendar:IsA("Model") and not calendar:GetAttribute("AnomalyUpgraded") then
		waitIdle()
		local pivot = calendar:GetPivot()
		local keepCalendar = {WallCalendarPrint = true, HangingLoop_Joint = true, PlacementPivot = true}
		for _, item in calendar:GetDescendants() do
			if item:IsA("BasePart") and not keepCalendar[item.Name] and not item:FindFirstChildWhichIsA("SurfaceGui") then
				item:Destroy()
			end
		end
		placeMeshes(calendar, calendarTemplate, pivot)
		keepPivot(calendar, pivot)
		calendar:SetAttribute("AnomalyUpgraded", true)
	end
	if calendarTemplate then
		calendarTemplate:Destroy()
	end

	-- настенное кашпо WEST (WestPlanterColor перекрашивает детали LeafBlade): корпус, почва, стебли и листья заменяются мешем; группы листьев
	-- получают имя LeafBlade, сервер аномалии перечитывает их после замены (OfficeObjects.server, атрибут AnomalyUpgraded)
	local planterTemplate = if ASSETS.WallPlanter then loadTemplate("WallPlanter", ASSETS.WallPlanter) else nil
	local west = rooms:FindFirstChild("WEST")
	local planter = west and west:FindFirstChild("V09_0348_WallPlanter")
	if planterTemplate and planter and planter:IsA("Model") and not planter:GetAttribute("AnomalyUpgraded") then
		waitIdle()
		local pivot = planter:GetPivot()
		for _, item in planter:GetDescendants() do
			if item:IsA("BasePart") and item.Name ~= "PlacementPivot" then
				item:Destroy()
			end
		end
		placeMeshes(planter, planterTemplate, pivot)
		keepPivot(planter, pivot)
		for _, mesh in planter:GetChildren() do
			if mesh:IsA("MeshPart") and string.find(mesh.Name, "^WallPlanter_leaf_") then
				mesh.Name = "LeafBlade"
			end
		end
		planter:SetAttribute("AnomalyUpgraded", true)
	end
	if planterTemplate then
		planterTemplate:Destroy()
	end

	-- люк вентиляции (MaintenanceVent строит OfficeObjects.server, масштаб .6): неподвижная рама заменяется VentFrame, створка HingedLouvers
	-- (её вращает сервер аномалии вокруг своего WorldPivot) получает VentLeaf; табличка MaintenanceLabel (GUI) остаётся
	local ventFrameTemplate = if ASSETS.VentFrame then loadTemplate("VentFrame", ASSETS.VentFrame) else nil
	local ventLeafTemplate = if ASSETS.VentLeaf then loadTemplate("VentLeaf", ASSETS.VentLeaf) else nil
	local housing = office:FindFirstChild("MaintenanceVent")
	if ventFrameTemplate and ventLeafTemplate and housing and housing:IsA("Model") and not housing:GetAttribute("AnomalyUpgraded") then
		local shadow = housing:FindFirstChild("DuctShadow")
		local hinge = housing:FindFirstChild("HingedLouvers")
		if shadow and shadow:IsA("BasePart") and hinge and hinge:IsA("Model") and math.abs(shadow.Size.X - 1.2) < 0.01 then
			waitIdle()
			-- начало меша = центр люка на стене; DuctShadow стоит на 0,031 * 0,6 перед ним
			local origin = shadow.CFrame * CFrame.new(0, 0, 0.031 * 0.6)
			local hingePivot = hinge:GetPivot() -- текущая поза створки (если подмена застала открытую)
			for _, item in housing:GetDescendants() do
				if item:IsA("BasePart") and not item:FindFirstChildWhichIsA("SurfaceGui") then
					item:Destroy()
				end
			end
			placeMeshes(housing, ventFrameTemplate, origin)
			placeMeshes(hinge, ventLeafTemplate, origin)
			-- меш ставится в закрытом положении, ось петли x = -0,97, n = 0,17 (в масштабе .6); затем створка возвращается в текущую позу
			hinge.WorldPivot = origin * CFrame.new(-0.97 * 0.6, 0, -0.17 * 0.6)
			hinge:PivotTo(hingePivot)
			housing:SetAttribute("AnomalyUpgraded", true)
		else
			warn("KONTUR anomaly: люк MaintenanceVent не подменён (нет DuctShadow или HingedLouvers, или масштаб не .6)")
		end
	end
	if ventFrameTemplate then
		ventFrameTemplate:Destroy()
	end
	if ventLeafTemplate then
		ventLeafTemplate:Destroy()
	end

	-- служебная дверь (WhisperDoor): сервер аномалии каждый раз заново создаёт UnlistedServiceDoor из ~28 деталей; пока аномалия не активна,
	-- её нет, поэтому меши ждут в памяти и подставляются при появлении двери. SignPlate с надписью (GUI) и винты таблички остаются,
	-- ручка DoorLever (её качает клиент вокруг RestPose) получает меш DoorLever, остальное заменяется ServiceDoor
	local doorTemplate = if ASSETS.ServiceDoor then loadTemplate("ServiceDoor", ASSETS.ServiceDoor) else nil
	local leverTemplate = if ASSETS.DoorLever then loadTemplate("DoorLever", ASSETS.DoorLever) else nil
	if doorTemplate and leverTemplate then
		local function upgradeDoor(door: Instance)
			if not door:IsA("Model") or door:GetAttribute("AnomalyUpgraded") or not door:IsDescendantOf(office) then
				return
			end
			local sign = door:FindFirstChild("SignPlate")
			local lever = door:FindFirstChild("DoorLever")
			if not (sign and sign:IsA("BasePart") and lever and lever:IsA("Model")) then
				return
			end
			-- SignPlate стоит в точке (0; 6,34; n = 0,101) системы двери
			local basis = sign.CFrame * CFrame.new(0, -6.34, 0.101)
			local leverPivot = lever.WorldPivot
			for _, item in door:GetDescendants() do
				if item:IsA("BasePart") and item.Name ~= "SignPlate" and item.Name ~= "SignScrew" then
					item:Destroy()
				end
			end
			placeMeshes(door, doorTemplate, basis)
			placeMeshes(lever, leverTemplate, basis)
			lever.WorldPivot = leverPivot
			local arm: MeshPart? = nil
			for _, mesh in lever:GetChildren() do
				if mesh:IsA("MeshPart") and (not arm or mesh.Size.Magnitude > arm.Size.Magnitude) then
					arm = mesh
				end
			end
			if arm then
				arm.Name = "Lever" -- рукоятка (самый длинный меш): имя, которое ждут проверки и клиент
			end
			door:SetAttribute("AnomalyUpgraded", true)
		end
		local existing = office:FindFirstChild("UnlistedServiceDoor")
		if existing then
			upgradeDoor(existing)
		end
		office.ChildAdded:Connect(function(child: Instance)
			if child.Name == "UnlistedServiceDoor" then
				upgradeDoor(child)
			end
		end)
	else
		if doorTemplate then
			doorTemplate:Destroy()
		end
		if leverTemplate then
			leverTemplate:Destroy()
		end
	end
end

return attachAnomalyUpgrade
