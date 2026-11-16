--!strict
-- v41 декор: дополнительная мебель и детали, чтобы комнаты не выглядели полупустыми.
-- Сервер при старте строит сетку каждой комнаты (1 стад), находит сплошные участки стен и свободные клетки у стен,
-- ставит подробные модели из деталей (книжные шкафы с книгами, кулер, вешалки с пальто, торшеры, коробки,
-- картины и плакаты на стенах). Не занимает двери, стойку ответа, принтер и места аномалий.
-- Подключение делает сборщик sources/evolution-v39/build_place.py: attachOfficeDecor(office, {ventMount, doorMount}).
local function attachOfficeDecor(office: Instance, avoidPoints: {Vector3})
	local random = Random.new(20261114)
	local rooms = office:FindFirstChild("Rooms")
	local structure = office:FindFirstChild("Structure")
	if not rooms or not structure then
		return
	end
	-- Модели из Blender (sources/evolution-v39/blender/*.py) загружены в Roblox как ассеты; сборщик подставляет их id вместо метки ниже.
	local HERO_ASSETS: {[string]: number} = {}
	-- @@HERO_ASSETS@@
	local isStudio = game:GetService("RunService"):IsStudio()
	local folder = Instance.new("Folder")
	folder.Name = "KonturDecor"
	folder.Parent = office

	local FLOOR_Y = 0.1
	local queryParams = OverlapParams.new()
	queryParams.FilterType = Enum.RaycastFilterType.Exclude
	local ignore: {Instance} = {folder}
	for _, name in {"Floors", "Ceiling"} do
		local item = office:FindFirstChild(name)
		if item then
			table.insert(ignore, item)
		end
	end
	queryParams.FilterDescendantsInstances = ignore
	-- как queryParams, но видит и уже поставленный декор (для картин и полосы над шкафами)
	local probeParams = OverlapParams.new()
	probeParams.FilterType = Enum.RaycastFilterType.Exclude
	local probeIgnore: {Instance} = {}
	for _, name in {"Floors", "Ceiling"} do
		local item = office:FindFirstChild(name)
		if item then
			table.insert(probeIgnore, item)
		end
	end
	probeParams.FilterDescendantsInstances = probeIgnore
	local wallParams = RaycastParams.new()
	wallParams.FilterType = Enum.RaycastFilterType.Include
	wallParams.FilterDescendantsInstances = {structure}

	-- зоны, которые нельзя занимать: двери, стойка ответа, принтер, точки аномалий
	local forbidden: {{point: Vector3, radius: number}} = {}
	local doorPoints: {Vector3} = {}
	local doors = office:FindFirstChild("Doors")
	if doors then
		for _, door in doors:GetChildren() do
			if door:IsA("Model") then
				table.insert(forbidden, {point = door:GetPivot().Position, radius = 4.5})
				table.insert(doorPoints, door:GetPivot().Position)
			end
		end
	end
	-- места, где играет аномалия или нужен подход игрока: картины и календарь архива, надпись, растение, зеркала,
	-- рабочее место сотрудника на потолке и его лампа; вокруг них ничего не ставим
	local ANOMALY_SPOTS = {"V09_0340_WorldTrade", "V09_0341_GrowthTechnology", "V09_0465_WallCalendar", "V09_0348_WallPlanter",
		"V09_0098_StraightDesk", "V09_0440_SlimDeskLamp", "V09_0293_Mirror", "V09_0294_Mirror", "V09_0316_Mirror", "V09_0317_Mirror", "BloodMessage"}
	for _, name in ANOMALY_SPOTS do
		local spot = rooms:FindFirstChild(name, true)
		if spot and spot:IsA("Model") then
			table.insert(forbidden, {point = spot:GetPivot().Position, radius = 8})
		elseif spot and spot:IsA("BasePart") then
			table.insert(forbidden, {point = spot.Position, radius = 8})
		end
	end
	-- всё, к чему игрок подходит и нажимает (шкафы, ящики, раковины): подход должен остаться свободным
	for _, item in rooms:GetDescendants() do
		if item:IsA("ProximityPrompt") then
			local holder = item.Parent
			if holder and holder:IsA("BasePart") then
				table.insert(forbidden, {point = holder.Position, radius = 3.4})
			end
		end
	end
	for _, item in rooms:GetDescendants() do
		if item:IsA("Model") and (string.find(item.Name, "ReportStation", 1, true) or item.Name == "Printer") then
			table.insert(forbidden, {point = item:GetPivot().Position, radius = 7})
		end
	end
	for _, point in avoidPoints do
		table.insert(forbidden, {point = point, radius = 5.5})
	end
	local function isForbidden(x: number, z: number): boolean
		for _, zone in forbidden do
			local dx, dz = x - zone.point.X, z - zone.point.Z
			if dx * dx + dz * dz < zone.radius * zone.radius then
				return true
			end
		end
		return false
	end

	local counts: {[string]: number} = {}
	local function count(name: string)
		counts[name] = (counts[name] or 0) + 1
	end

	----------------------------------------------------------------- детали
	local WOOD = Enum.Material.Wood
	local PLASTIC = Enum.Material.SmoothPlastic
	local function part(parent: Instance, name: string, size: Vector3, frame: CFrame, color: Color3, material: Enum.Material?, collide: boolean?): Part
		local p = Instance.new("Part")
		p.Name = name
		p.Size = size
		p.CFrame = frame
		p.Color = color
		p.Material = material or PLASTIC
		p.Anchored = true
		p.CanCollide = collide == true
		p.CanTouch = false
		p.Parent = parent
		return p
	end
	-- вертикальный цилиндр (ось Part.Cylinder идёт по X): высота h, диаметр d
	local function cylinder(parent: Instance, name: string, d: number, h: number, frame: CFrame, color: Color3, material: Enum.Material?): Part
		local p = part(parent, name, Vector3.new(h, d, d), frame * CFrame.Angles(0, 0, math.pi / 2), color, material)
		p.Shape = Enum.PartType.Cylinder
		return p
	end
	local function hitbox(parent: Instance, size: Vector3, frame: CFrame)
		local p = part(parent, "Hitbox", size, frame, Color3.new(1, 1, 1), PLASTIC, true)
		p.Transparency = 1
		p.CanQuery = false
	end
	local function newModel(name: string): Model
		local model = Instance.new("Model")
		model.Name = name
		return model
	end

	----------------------------------------------------------------- модели из Blender (загруженные ассеты)
	-- Сначала предметы ставятся запасным видом из деталей (с тегами HeroKey/HeroCF), старт не ждёт сети. Затем фоновый поток
	-- подгружает ассеты (InsertService:LoadAsset) и заменяет вид: детали выбрасываются, меши встают на место. Если ассет не
	-- загрузился, остаётся вариант из деталей. Меш на материал: имя детали <Предмет>_<материал>.
	local HERO_LOOK: {[string]: {material: Enum.Material, transparency: number}} = {
		wood_dark = {material = Enum.Material.Wood, transparency = 0}, wood_mid = {material = Enum.Material.Wood, transparency = 0},
		wood_light = {material = Enum.Material.Wood, transparency = 0}, metal = {material = Enum.Material.Metal, transparency = 0},
		metal_dark = {material = Enum.Material.Metal, transparency = 0}, brass = {material = Enum.Material.Metal, transparency = 0},
		steel = {material = Enum.Material.Metal, transparency = 0}, glass_blue = {material = Enum.Material.Glass, transparency = 0.35},
		glass_clear = {material = Enum.Material.Glass, transparency = 0.7}, shade = {material = Enum.Material.Neon, transparency = 0.12},
	}
	local function tagHero(model: Model, key: string, base: CFrame): Model
		model:SetAttribute("HeroKey", key)
		model:SetAttribute("HeroCF", base)
		return model
	end
	local function loadHeroTemplate(key: string, assetId: number): Model?
		local container: Instance? = nil
		local lastError: any = nil
		for attempt = 1, 3 do -- сеть иногда отвечает 503: повтор с паузой
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
			warn("KONTUR hero asset " .. key .. " (" .. tostring(assetId) .. ") failed: " .. tostring(lastError))
			return nil
		end
		local template = Instance.new("Model")
		template.Name = "Hero_" .. key
		for _, mesh in container:GetDescendants() do
			if mesh:IsA("MeshPart") then
				-- имя детали: <Предмет>_<материал>_<цвет hex>: цвет ставим на MeshPart.Color (вершинные цвета в мешах белые)
				local suffix, hex = string.match(mesh.Name, "^" .. key .. "_(.+)_(%x%x%x%x%x%x)$")
				suffix = suffix or mesh.Name
				if hex then
					mesh.Color = Color3.fromHex(hex)
				end
				local look = HERO_LOOK[suffix]
				mesh.Anchored = true
				mesh.CanCollide = false
				mesh.CanTouch = false
				mesh.CanQuery = false
				mesh.Material = if look then look.material else PLASTIC
				mesh.Transparency = if look then look.transparency else 0
				mesh.DoubleSided = suffix == "shade" or suffix == "leaf"
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
	local function swapHeroModels(templates: {[string]: Model}): number
		local swapped = 0
		for _, model in folder:GetChildren() do
			local key = model:GetAttribute("HeroKey")
			local base = model:GetAttribute("HeroCF")
			local template = if type(key) == "string" then templates[key] else nil
			if template and typeof(base) == "CFrame" and model:IsA("Model") and not model:GetAttribute("HeroApplied") then
				for _, item in model:GetDescendants() do
					if item:IsA("BasePart") and item.Name ~= "Hitbox" then
						if item.Name == "Bulb" then
							item.Transparency = 1 -- нить остаётся носителем света, внутри абажура её не видно
						else
							item:Destroy()
						end
					end
				end
				local copy = template:Clone()
				copy:PivotTo(base)
				for _, item in copy:GetChildren() do
					item.Parent = model
				end
				copy:Destroy()
				model:SetAttribute("HeroApplied", true)
				swapped += 1
				if swapped % 8 == 0 then
					task.wait()
				end
			end
		end
		return swapped
	end
	local function applyHeroMeshes()
		local templates: {[string]: Model} = {}
		local total = 0
		for round = 1, 6 do -- сеть иногда отвечает 503: недогруженное добираем следующими кругами
			local pending = 0
			local missing = 0
			for key, assetId in HERO_ASSETS do
				if not templates[key] then
					missing += 1
					pending += 1
					task.spawn(function()
						local template = loadHeroTemplate(key, assetId)
						if template then
							templates[key] = template
						end
						pending -= 1
					end)
				end
			end
			if missing == 0 then
				break
			end
			local waited = 0
			while pending > 0 and waited < 90 do
				task.wait(0.5)
				waited += 0.5
			end
			total += swapHeroModels(templates)
			local done = true
			for key in HERO_ASSETS do
				if not templates[key] then
					done = false
				end
			end
			if done then
				break
			end
			task.wait(20)
		end
		for _, template in templates do
			template:Destroy()
		end
		if isStudio then
			office:SetAttribute("KonturDecorHeroSwapped", total)
		end
	end

	local BOOK_COLORS = {
		Color3.fromRGB(122, 44, 44), Color3.fromRGB(44, 82, 112), Color3.fromRGB(58, 98, 70), Color3.fromRGB(196, 168, 92),
		Color3.fromRGB(88, 62, 110), Color3.fromRGB(214, 206, 188), Color3.fromRGB(70, 74, 84), Color3.fromRGB(150, 96, 56),
		Color3.fromRGB(38, 56, 64), Color3.fromRGB(176, 120, 76),
	}
	local WOOD_COLORS = {Color3.fromRGB(122, 92, 64), Color3.fromRGB(96, 70, 50), Color3.fromRGB(152, 120, 84)}

	-- Книжный шкаф. Локальная система: перед = -Z (на зрителя), задняя стенка у +Z.
	local function bookcaseParts(base: CFrame): Model
		local model = newModel("KD_Bookcase")
		local W, D, H = 3.6, 1.1, 7.0
		local wood = WOOD_COLORS[random:NextInteger(1, #WOOD_COLORS)]
		part(model, "SideL", Vector3.new(0.12, H, D), base * CFrame.new(-W / 2 + 0.06, H / 2, 0), wood, WOOD)
		part(model, "SideR", Vector3.new(0.12, H, D), base * CFrame.new(W / 2 - 0.06, H / 2, 0), wood, WOOD)
		part(model, "Back", Vector3.new(W - 0.24, H - 0.2, 0.05), base * CFrame.new(0, H / 2 + 0.05, D / 2 - 0.03), wood:Lerp(Color3.new(0, 0, 0), 0.25), WOOD)
		part(model, "Plinth", Vector3.new(W - 0.24, 0.35, D - 0.12), base * CFrame.new(0, 0.175, -0.04), wood:Lerp(Color3.new(0, 0, 0), 0.15), WOOD)
		part(model, "Top", Vector3.new(W + 0.1, 0.12, D + 0.06), base * CFrame.new(0, H - 0.06, -0.01), wood, WOOD)
		part(model, "Crown", Vector3.new(W + 0.2, 0.08, D + 0.12), base * CFrame.new(0, H + 0.04, -0.02), wood:Lerp(Color3.new(1, 1, 1), 0.1), WOOD)
		local shelves = 5
		local span = (H - 0.35 - 0.12) / shelves
		for i = 0, shelves - 1 do
			local y = 0.35 + i * span
			if i > 0 then
				part(model, "Shelf", Vector3.new(W - 0.24, 0.07, D - 0.08), base * CFrame.new(0, y, -0.02), wood, WOOD)
			end
			-- книги и мелочи на полке
			local x = -W / 2 + 0.2
			local limit = W / 2 - 0.2
			local topOfShelf = y + (if i > 0 then 0.035 else 0)
			while x < limit - 0.1 do
				local roll = random:NextNumber()
				if roll < 0.06 then
					x += random:NextNumber(0.2, 0.5) -- просвет
				elseif roll < 0.1 and limit - x > 0.45 then
					-- коробка-архивная папка с этикеткой
					local bw, bh = random:NextNumber(0.3, 0.4), span - 0.18
					part(model, "ArchiveBox", Vector3.new(bw, bh, D - 0.3), base * CFrame.new(x + bw / 2, topOfShelf + bh / 2, -0.04), Color3.fromRGB(176, 150, 112), Enum.Material.Cardboard)
					part(model, "BoxLabel", Vector3.new(bw * 0.7, 0.14, 0.01), base * CFrame.new(x + bw / 2, topOfShelf + bh * 0.62, -(D - 0.3) / 2 - 0.045), Color3.fromRGB(238, 234, 220), PLASTIC)
					x += bw + 0.03
				else
					local bw = random:NextNumber(0.1, 0.28)
					local bh = random:NextNumber(0.72, span - 0.14)
					local color = BOOK_COLORS[random:NextInteger(1, #BOOK_COLORS)]
					local bd = random:NextNumber(0.55, D - 0.25)
					if random:NextNumber() < 0.04 and limit - x > 0.6 then
						-- книга лежит набок
						part(model, "Book", Vector3.new(bh * 0.8, bw, bd), base * CFrame.new(x + bh * 0.4, topOfShelf + bw / 2, -0.04), color, PLASTIC)
						x += bh * 0.8 + 0.03
					else
						local book = part(model, "Book", Vector3.new(bw, bh, bd), base * CFrame.new(x + bw / 2, topOfShelf + bh / 2, -0.03 - (D - 0.25 - bd) / 2 + 0.05), color, PLASTIC)
						part(model, "Spine", Vector3.new(bw * 0.85, 0.05, 0.012), book.CFrame * CFrame.new(0, bh * 0.25, -bd / 2 - 0.006), Color3.fromRGB(226, 214, 168), PLASTIC)
						x += bw + 0.012
					end
				end
			end
		end
		hitbox(model, Vector3.new(W, H, D), base * CFrame.new(0, H / 2, 0))
		return model
	end

	-- Кулер для воды.
	local function waterCoolerParts(base: CFrame): Model
		local model = newModel("KD_WaterCooler")
		local white = Color3.fromRGB(226, 230, 232)
		part(model, "Body", Vector3.new(1.1, 2.9, 1.1), base * CFrame.new(0, 1.55, 0.1), white, PLASTIC)
		part(model, "BodyFace", Vector3.new(1.0, 1.0, 0.04), base * CFrame.new(0, 2.15, -0.46), Color3.fromRGB(196, 204, 210), PLASTIC)
		part(model, "TapCold", Vector3.new(0.14, 0.14, 0.18), base * CFrame.new(-0.2, 2.3, -0.58), Color3.fromRGB(70, 130, 200), PLASTIC)
		part(model, "TapHot", Vector3.new(0.14, 0.14, 0.18), base * CFrame.new(0.2, 2.3, -0.58), Color3.fromRGB(196, 70, 60), PLASTIC)
		part(model, "DripTray", Vector3.new(0.9, 0.06, 0.32), base * CFrame.new(0, 1.85, -0.58), Color3.fromRGB(70, 76, 82), Enum.Material.Metal)
		part(model, "Grille", Vector3.new(0.7, 0.4, 0.03), base * CFrame.new(0, 0.55, -0.45), Color3.fromRGB(96, 102, 108), Enum.Material.Metal)
		part(model, "Plinth", Vector3.new(1.16, 0.14, 1.16), base * CFrame.new(0, 0.07, 0.1), Color3.fromRGB(88, 94, 100), PLASTIC)
		part(model, "TopRing", Vector3.new(1.12, 0.12, 1.12), base * CFrame.new(0, 3.05, 0.1), Color3.fromRGB(205, 210, 214), PLASTIC)
		local jug = cylinder(model, "Jug", 0.95, 1.5, base * CFrame.new(0, 3.85, 0.1), Color3.fromRGB(150, 196, 232), Enum.Material.Glass)
		jug.Transparency = 0.45
		local water = cylinder(model, "Water", 0.86, 1.05, base * CFrame.new(0, 3.7, 0.1), Color3.fromRGB(120, 176, 226), PLASTIC)
		water.Transparency = 0.55
		cylinder(model, "JugCap", 0.55, 0.12, base * CFrame.new(0, 4.66, 0.1), Color3.fromRGB(70, 120, 190), PLASTIC)
		-- стаканчики
		local tube = cylinder(model, "CupTube", 0.34, 1.0, base * CFrame.new(0.68, 2.4, 0.1), Color3.fromRGB(214, 218, 222), PLASTIC)
		tube.Transparency = 0.2
		cylinder(model, "Cups", 0.26, 0.9, base * CFrame.new(0.68, 2.4, 0.1), Color3.fromRGB(240, 240, 236), PLASTIC)
		hitbox(model, Vector3.new(1.5, 4.8, 1.2), base * CFrame.new(0, 2.4, 0.1))
		return model
	end

	-- Вешалка-стойка с пальто.
	local function coatRackParts(base: CFrame): Model
		local model = newModel("KD_CoatRack")
		local dark = Color3.fromRGB(58, 52, 48)
		cylinder(model, "Base", 1.2, 0.12, base * CFrame.new(0, 0.06, 0), dark, Enum.Material.Metal)
		cylinder(model, "Pole", 0.12, 5.6, base * CFrame.new(0, 2.9, 0), dark, Enum.Material.Metal)
		for level = 0, 1 do
			local y = 5.0 - level * 0.45
			for k = 0, 3 do
				local angle = k * math.pi / 2 + level * math.pi / 4
				local arm = CFrame.new(0, y, 0) * CFrame.Angles(0, angle, 0)
				part(model, "Hook", Vector3.new(0.5, 0.07, 0.07), base * arm * CFrame.new(0.28, 0, 0) * CFrame.Angles(0, 0, math.rad(20)), dark, Enum.Material.Metal)
				part(model, "HookTip", Vector3.new(0.07, 0.2, 0.07), base * arm * CFrame.new(0.52, 0.1, 0), dark, Enum.Material.Metal)
			end
		end
		-- два пальто
		local coatColors = {Color3.fromRGB(52, 58, 72), Color3.fromRGB(96, 74, 56), Color3.fromRGB(70, 70, 74)}
		for k = 0, 1 do
			local angle = k * math.pi + 0.4
			local arm = base * CFrame.new(0, 4.9, 0) * CFrame.Angles(0, angle, 0) * CFrame.new(0.56, -1.1, 0)
			local color = coatColors[random:NextInteger(1, #coatColors)]
			part(model, "CoatBody", Vector3.new(0.3, 1.9, 0.9), arm, color, Enum.Material.Fabric)
			part(model, "CoatSleeveA", Vector3.new(0.18, 1.5, 0.22), arm * CFrame.new(0.06, -0.1, 0.52), color, Enum.Material.Fabric)
			part(model, "CoatSleeveB", Vector3.new(0.18, 1.5, 0.22), arm * CFrame.new(0.06, -0.1, -0.52), color, Enum.Material.Fabric)
			part(model, "CoatCollar", Vector3.new(0.34, 0.2, 0.6), arm * CFrame.new(0, 1.0, 0), color:Lerp(Color3.new(0, 0, 0), 0.2), Enum.Material.Fabric)
		end
		hitbox(model, Vector3.new(1.2, 5.6, 1.2), base * CFrame.new(0, 2.8, 0))
		return model
	end

	-- Торшер с тёплым светом (без теней, чтобы не утяжелять сцену).
	local function floorLampParts(base: CFrame): Model
		local model = newModel("KD_FloorLamp")
		local brass = Color3.fromRGB(176, 140, 84)
		cylinder(model, "Base", 0.9, 0.1, base * CFrame.new(0, 0.05, 0), Color3.fromRGB(50, 50, 54), Enum.Material.Metal)
		cylinder(model, "Pole", 0.09, 4.6, base * CFrame.new(0, 2.4, 0), brass, Enum.Material.Metal)
		local shade = cylinder(model, "Shade", 1.1, 0.95, base * CFrame.new(0, 5.0, 0), Color3.fromRGB(238, 222, 190), PLASTIC)
		shade.Transparency = 0.25
		local bulb = part(model, "Bulb", Vector3.new(0.4, 0.4, 0.4), base * CFrame.new(0, 4.95, 0), Color3.fromRGB(255, 232, 180), Enum.Material.Neon)
		bulb.Shape = Enum.PartType.Ball
		local light = Instance.new("PointLight")
		light.Name = "LampLight"
		light.Color = Color3.fromRGB(255, 214, 150)
		light.Brightness = 0.9
		light.Range = 15
		light.Shadows = false
		light.Parent = bulb
		hitbox(model, Vector3.new(0.9, 5.4, 0.9), base * CFrame.new(0, 2.7, 0))
		return model
	end

	-- Стопка коробок с этикетками.
	local function boxStack(base: CFrame): Model
		local model = newModel("KD_Boxes")
		local labels = {"ХРУПКОЕ", "АРХИВ 07", "ДЕЛО Nº 118", "НЕ КАНТОВАТЬ", "ВЕРХ", "ДОКУМЕНТЫ"}
		local function box(frame: CFrame, size: Vector3)
			local tone = random:NextNumber(0.9, 1.08)
			local color = Color3.fromRGB(math.min(255, 168 * tone), math.min(255, 132 * tone), math.min(255, 92 * tone))
			local b = part(model, "Box", size, frame, color, Enum.Material.Cardboard)
			part(model, "Tape", Vector3.new(size.X + 0.02, 0.01, size.Z * 0.18), frame * CFrame.new(0, size.Y / 2 + 0.006, 0), Color3.fromRGB(206, 178, 126), PLASTIC)
			local label = part(model, "Label", Vector3.new(size.X * 0.55, size.Y * 0.32, 0.012), frame * CFrame.new(0, size.Y * 0.05, -size.Z / 2 - 0.007), Color3.fromRGB(238, 234, 220), PLASTIC)
			local gui = Instance.new("SurfaceGui")
			gui.Face = Enum.NormalId.Front
			gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			gui.PixelsPerStud = 80
			gui.MaxDistance = 14
			gui.Parent = label
			local text = Instance.new("TextLabel")
			text.Size = UDim2.fromScale(1, 1)
			text.BackgroundTransparency = 1
			text.Font = Enum.Font.GothamBold
			text.TextScaled = true
			text.TextColor3 = Color3.fromRGB(52, 46, 40)
			text.Text = labels[random:NextInteger(1, #labels)]
			text.Parent = gui
			return b
		end
		local turn = math.rad(random:NextNumber(-8, 8))
		box(base * CFrame.new(-0.5, 0.55, 0.1) * CFrame.Angles(0, turn, 0), Vector3.new(1.3, 1.1, 1.0))
		box(base * CFrame.new(0.65, 0.45, 0.0) * CFrame.Angles(0, -turn, 0), Vector3.new(1.0, 0.9, 0.9))
		box(base * CFrame.new(-0.45, 1.5, 0.1) * CFrame.Angles(0, turn * 0.5 + 0.1, 0), Vector3.new(1.1, 0.9, 0.9))
		if random:NextNumber() < 0.6 then
			box(base * CFrame.new(0.6, 1.2, 0.0) * CFrame.Angles(0, -turn, 0), Vector3.new(0.8, 0.7, 0.7))
		end
		hitbox(model, Vector3.new(2.2, 2.2, 1.6), base * CFrame.new(0, 1.1, 0.05))
		return model
	end

	-- Картины и плакаты на стене. Локальная система как у остальных: перед = -Z.
	local POSTERS = {
		{"БЕЗОПАСНОСТЬ\nПРЕЖДЕ ВСЕГО", Color3.fromRGB(224, 196, 84), Color3.fromRGB(46, 46, 52)},
		{"ТИШИНА\nВ АРХИВЕ", Color3.fromRGB(214, 218, 220), Color3.fromRGB(46, 70, 84)},
		{"ОТЧЁТ\nСДАН?", Color3.fromRGB(176, 60, 56), Color3.fromRGB(244, 238, 226)},
		{"КОНТУР\n/ 2026", Color3.fromRGB(38, 92, 106), Color3.fromRGB(226, 232, 230)},
		{"НЕ ОСТАВЛЯЙТЕ\nЛИСТЫ БЕЗ\nПРИСМОТРА", Color3.fromRGB(234, 228, 214), Color3.fromRGB(88, 44, 44)},
		{"ПОРЯДОК\nЭТО ЗАБОТА", Color3.fromRGB(88, 120, 100), Color3.fromRGB(240, 238, 226)},
	}
	local function wallFrame(base: CFrame, width: number, height: number): Model
		local model = newModel("KD_Frame")
		local frameColor = if random:NextNumber() < 0.5 then Color3.fromRGB(44, 40, 38) else Color3.fromRGB(122, 92, 64)
		local t = 0.14
		part(model, "FrameTop", Vector3.new(width, t, 0.12), base * CFrame.new(0, height / 2 - t / 2, 0), frameColor, WOOD)
		part(model, "FrameBottom", Vector3.new(width, t, 0.12), base * CFrame.new(0, -height / 2 + t / 2, 0), frameColor, WOOD)
		part(model, "FrameLeft", Vector3.new(t, height - 2 * t, 0.12), base * CFrame.new(-width / 2 + t / 2, 0, 0), frameColor, WOOD)
		part(model, "FrameRight", Vector3.new(t, height - 2 * t, 0.12), base * CFrame.new(width / 2 - t / 2, 0, 0), frameColor, WOOD)
		part(model, "Mat", Vector3.new(width - 2 * t, height - 2 * t, 0.04), base * CFrame.new(0, 0, 0.03), Color3.fromRGB(236, 232, 220), PLASTIC)
		local art = part(model, "Art", Vector3.new(width - 4 * t, height - 4 * t, 0.02), base * CFrame.new(0, 0, 0.0), Color3.fromRGB(240, 236, 226), PLASTIC)
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 90
		gui.MaxDistance = 70
		gui.Parent = art
		local style = random:NextInteger(1, 4)
		local function block(x: number, y: number, w: number, h: number, color: Color3, round: boolean?)
			local f = Instance.new("Frame")
			f.AnchorPoint = Vector2.new(0, 0)
			f.Position = UDim2.fromScale(x, y)
			f.Size = UDim2.fromScale(w, h)
			f.BackgroundColor3 = color
			f.BorderSizePixel = 0
			if round then
				local c = Instance.new("UICorner")
				c.CornerRadius = UDim.new(1, 0)
				c.Parent = f
			end
			f.Parent = gui
		end
		if style == 1 then -- абстрактный пейзаж: небо, холмы, солнце
			block(0, 0, 1, 0.55, Color3.fromRGB(176, 206, 220))
			block(0.62, 0.12, 0.2, 0.28, Color3.fromRGB(246, 214, 120), true)
			block(0, 0.5, 1, 0.5, Color3.fromRGB(86, 128, 98))
			block(0, 0.62, 1, 0.38, Color3.fromRGB(62, 104, 84))
			block(0.1, 0.46, 0.5, 0.2, Color3.fromRGB(100, 140, 104), true)
		elseif style == 2 then -- диаграмма
			block(0, 0, 1, 1, Color3.fromRGB(244, 240, 230))
			for i = 0, 5 do
				local h = 0.2 + random:NextNumber() * 0.55
				block(0.1 + i * 0.14, 0.88 - h, 0.1, h, if i % 2 == 0 then Color3.fromRGB(46, 100, 116) else Color3.fromRGB(216, 150, 70))
			end
			block(0.06, 0.88, 0.88, 0.02, Color3.fromRGB(70, 70, 76))
		else -- плакат с надписью
			local poster = POSTERS[random:NextInteger(1, #POSTERS)]
			block(0, 0, 1, 1, poster[2])
			local label = Instance.new("TextLabel")
			label.Size = UDim2.fromScale(0.86, 0.7)
			label.Position = UDim2.fromScale(0.07, 0.15)
			label.BackgroundTransparency = 1
			label.Font = Enum.Font.GothamBold
			label.TextScaled = true
			label.TextColor3 = poster[3]
			label.Text = poster[1]
			label.Parent = gui
		end
		return model
	end

	-- Напольное растение в горшке (листья из эллипсоидов разных оттенков зелени).
	local function planter(base: CFrame): Model
		local model = newModel("KD_Planter")
		local potColor = ({Color3.fromRGB(196, 190, 176), Color3.fromRGB(58, 66, 76), Color3.fromRGB(150, 98, 70)})[random:NextInteger(1, 3)]
		cylinder(model, "Pot", 1.25, 1.15, base * CFrame.new(0, 0.62, 0), potColor, Enum.Material.Concrete)
		cylinder(model, "PotRim", 1.4, 0.12, base * CFrame.new(0, 1.2, 0), potColor:Lerp(Color3.new(1, 1, 1), 0.12), Enum.Material.Concrete)
		cylinder(model, "Soil", 1.08, 0.06, base * CFrame.new(0, 1.2, 0), Color3.fromRGB(52, 40, 32), Enum.Material.Ground)
		local greens = {Color3.fromRGB(58, 112, 70), Color3.fromRGB(78, 134, 82), Color3.fromRGB(44, 92, 62), Color3.fromRGB(98, 148, 90)}
		local stems = random:NextInteger(5, 7)
		for i = 1, stems do
			local angle = (i / stems) * math.pi * 2 + random:NextNumber(-0.3, 0.3)
			local lean = random:NextNumber(0.15, 0.55)
			local height = random:NextNumber(1.6, 2.7)
			local tilt = CFrame.Angles(0, angle, 0) * CFrame.Angles(0, 0, lean)
			local stem = part(model, "Stem", Vector3.new(0.05, height, 0.05), base * CFrame.new(0, 1.2, 0) * tilt * CFrame.new(0, height / 2, 0), Color3.fromRGB(70, 104, 62), PLASTIC)
			local tip = base * CFrame.new(0, 1.2, 0) * tilt * CFrame.new(0, height, 0)
			for k = 1, 3 do
				local leaf = part(model, "Leaf", Vector3.new(random:NextNumber(0.5, 0.8), 0.06, random:NextNumber(0.9, 1.4)), tip * CFrame.Angles(random:NextNumber(-0.7, 0.2), random:NextNumber(0, 6.28), random:NextNumber(-0.5, 0.5)) * CFrame.new(0, -0.1 * k, -0.3), greens[random:NextInteger(1, #greens)], Enum.Material.Grass)
				leaf.Shape = Enum.PartType.Ball
			end
		end
		hitbox(model, Vector3.new(1.4, 3.2, 1.4), base * CFrame.new(0, 1.6, 0))
		return model
	end

	-- Ковёр: основа, кайма, внутреннее поле и два узких кантa. Размеры в стадах.
	local RUG_SCHEMES = { -- основа, кайма и орнамент, внутреннее поле: светлее пола, в цвет стен и дерева офиса
		{Color3.fromRGB(196, 176, 138), Color3.fromRGB(44, 110, 116), Color3.fromRGB(226, 212, 182)},
		{Color3.fromRGB(70, 128, 132), Color3.fromRGB(228, 214, 180), Color3.fromRGB(46, 96, 102)},
		{Color3.fromRGB(176, 98, 70), Color3.fromRGB(236, 220, 186), Color3.fromRGB(150, 76, 56)},
		{Color3.fromRGB(122, 140, 154), Color3.fromRGB(232, 232, 224), Color3.fromRGB(86, 106, 124)},
		{Color3.fromRGB(206, 170, 96), Color3.fromRGB(52, 96, 104), Color3.fromRGB(232, 208, 150)},
	}
	local function rug(centre: Vector3, width: number, depth: number, along: Vector3): Model
		local model = newModel("KD_Rug")
		local scheme = RUG_SCHEMES[random:NextInteger(1, #RUG_SCHEMES)]
		local base = CFrame.lookAt(Vector3.new(centre.X, FLOOR_Y + 0.02, centre.Z), Vector3.new(centre.X, FLOOR_Y + 0.02, centre.Z) + along)
		local function layer(w: number, d: number, y: number, color: Color3)
			local rugPart = part(model, "Layer", Vector3.new(w, 0.04, d), base * CFrame.new(0, y, 0), color, Enum.Material.Fabric)
			rugPart.CanQuery = false
			rugPart.CastShadow = false
		end
		layer(width, depth, 0, scheme[1])
		layer(width - 0.5, depth - 0.5, 0.012, scheme[2])
		layer(width - 0.7, depth - 0.7, 0.024, scheme[1])
		layer(width - 1.5, depth - 1.5, 0.036, scheme[3])
		-- центральный орнамент: ромб из трёх прямоугольников
		layer(width * 0.34, depth * 0.34, 0.048, scheme[2])
		layer(width * 0.26, depth * 0.26, 0.06, scheme[1])
		return model
	end

	----------------------------------------------------------------- предметы с мешами Blender (запасной вид из деталей + теги для клиента)
	local function bookcase(base: CFrame): Model
		return tagHero(bookcaseParts(base), "Bookcase", base)
	end
	local function waterCooler(base: CFrame): Model
		return tagHero(waterCoolerParts(base), "WaterCooler", base)
	end
	local function coatRack(base: CFrame): Model
		return tagHero(coatRackParts(base), "CoatRack", base)
	end
	local function floorLamp(base: CFrame): Model
		return tagHero(floorLampParts(base), "FloorLamp", base)
	end
	local function armchair(base: CFrame): Model
		local model = newModel("KD_Armchair")
		local fabric = Color3.fromRGB(47, 107, 106)
		part(model, "Frame", Vector3.new(2.3, 0.2, 2.1), base * CFrame.new(0, 0.55, 0), Color3.fromRGB(70, 50, 40), WOOD)
		part(model, "Seat", Vector3.new(1.9, 0.6, 1.9), base * CFrame.new(0, 0.95, -0.05), fabric, Enum.Material.Fabric)
		part(model, "Back", Vector3.new(2.2, 1.9, 0.6), base * CFrame.new(0, 1.65, 0.8), fabric, Enum.Material.Fabric)
		part(model, "ArmL", Vector3.new(0.5, 1.35, 2.15), base * CFrame.new(-1.1, 1.25, 0), fabric, Enum.Material.Fabric)
		part(model, "ArmR", Vector3.new(0.5, 1.35, 2.15), base * CFrame.new(1.1, 1.25, 0), fabric, Enum.Material.Fabric)
		hitbox(model, Vector3.new(2.7, 2.9, 2.3), base * CFrame.new(0, 1.45, 0))
		return tagHero(model, "Armchair", base)
	end
	local function filingCabinet(base: CFrame): Model
		local model = newModel("KD_FilingCabinet")
		local steel = Color3.fromRGB(138, 146, 153)
		part(model, "Body", Vector3.new(1.6, 4.1, 2.0), base * CFrame.new(0, 2.25, 0), steel, Enum.Material.Metal)
		part(model, "Plinth", Vector3.new(1.5, 0.2, 1.9), base * CFrame.new(0, 0.1, 0), Color3.fromRGB(46, 50, 56), PLASTIC)
		for k = 0, 3 do
			part(model, "Drawer", Vector3.new(1.4, 0.9, 0.06), base * CFrame.new(0, 0.7 + k * 1.0, -1.03), steel:Lerp(Color3.new(1, 1, 1), 0.08), Enum.Material.Metal)
			part(model, "Handle", Vector3.new(0.7, 0.07, 0.07), base * CFrame.new(0, 1.0 + k * 1.0, -1.1), Color3.fromRGB(46, 50, 56), PLASTIC)
		end
		hitbox(model, Vector3.new(1.6, 4.3, 2.0), base * CFrame.new(0, 2.15, 0))
		return tagHero(model, "FilingCabinet", base)
	end

	----------------------------------------------------------------- сетка и поиск мест
	-- клетки: 0 свободно, 1 мебель, 2 стена, 3 занято декором
	local totalPlaced = 0

	local function queryCell(x: number, z: number): number
		local hits = workspace:GetPartBoundsInBox(CFrame.new(x, 1.5, z), Vector3.new(0.9, 2.4, 0.9), queryParams)
		local wall, furniture = false, false
		for _, hit in hits do
			if hit:IsDescendantOf(structure) then
				wall = true
			elseif string.find(hit.Name, "^Skirting") or string.find(hit.Name, "^DadoRail") then
				-- плинтус и молдинг не мебель: иначе клетка у стены меняется от фазы сетки и стена теряет пригодность
				continue
			elseif hit.Transparency < 1 or hit.CanCollide then
				furniture = true
			end
		end
		return if wall then 2 elseif furniture then 1 else 0
	end

	-- квоты: {большие комнаты}, {малые комнаты}
	local QUOTA_BIG: {[string]: number} = {bookcase = 2, cooler = 1, coat = 1, lamp = 2, boxes = 3, frames = 0, planter = 2, workstation = 2, rug = 0, armchair = 1, cabinet = 3}
	local QUOTA_SMALL: {[string]: number} = {bookcase = 1, cooler = 0, coat = 1, lamp = 1, boxes = 1, frames = 0, planter = 2, workstation = 0, rug = 0, armchair = 0, cabinet = 1}
	local QUOTA_WC: {[string]: number} = {bookcase = 0, cooler = 0, coat = 0, lamp = 0, boxes = 0, frames = 0, planter = 0, workstation = 0, rug = 0, armchair = 0, cabinet = 0}
	local FOOT: {[string]: {number}} = { -- ширина вдоль стены, глубина от стены (в клетках), запас спереди
		bookcase = {4, 2}, cooler = {2, 2}, coat = {2, 2}, lamp = {2, 2}, boxes = {3, 2}, planter = {2, 2}, armchair = {3, 3}, cabinet = {2, 2},
	}
	local BUILD: {[string]: (CFrame) -> Model} = {bookcase = bookcase, cooler = waterCooler, coat = coatRack, lamp = floorLamp, boxes = boxStack, planter = planter, armchair = armchair, cabinet = filingCabinet}
	-- расстояние от стены до начала координат модели (центр основания); у моделей из Blender считано по их габаритам
	local BACK_OFFSET: {[string]: number} = {bookcase = 0.64, cooler = 0.64, coat = 0.8, lamp = 1.02, boxes = 0.82, planter = 0.72, armchair = 1.16, cabinet = 1.04}
	local NEIGHBORS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}
	local DIRS = {Vector3.new(1, 0, 0), Vector3.new(-1, 0, 0), Vector3.new(0, 0, 1), Vector3.new(0, 0, -1)}

local function processRoom(room: Instance)
	local lowX, lowZ, highX, highZ = math.huge, math.huge, -math.huge, -math.huge
		for _, item in room:GetDescendants() do
			if item:IsA("BasePart") then
				local p = item.Position
				lowX, highX = math.min(lowX, p.X), math.max(highX, p.X)
				lowZ, highZ = math.min(lowZ, p.Z), math.max(highZ, p.Z)
			end
		end
		if lowX < highX and lowZ < highZ then
			local pad = 4
			local x0, z0 = math.floor(lowX) - pad, math.floor(lowZ) - pad
			local nx, nz = math.ceil(highX - lowX) + 2 * pad, math.ceil(highZ - lowZ) + 2 * pad
			local grid: {[number]: number} = {}
			local function idx(ix: number, iz: number): number
				return ix * 4096 + iz
			end
			local counter = 0
			for ix = 0, nx - 1 do
				for iz = 0, nz - 1 do
					grid[idx(ix, iz)] = queryCell(x0 + ix + 0.5, z0 + iz + 0.5)
					counter += 1
					if counter % 600 == 0 then
						task.wait()
					end
				end
			end
			local function get(ix: number, iz: number): number
				return grid[idx(ix, iz)] or 1
			end
			-- клетки внутри комнаты: между краями AABB, иначе "свободно" снаружи не берём
			local function inside(ix: number, iz: number): boolean
				return ix >= pad - 1 and ix <= nx - pad and iz >= pad - 1 and iz <= nz - pad
			end
			local function centre(ix: number, iz: number): Vector3
				return Vector3.new(x0 + ix + 0.5, FLOOR_Y, z0 + iz + 0.5)
			end

			local small = (nx - 2 * pad) * (nz - 2 * pad) < 700
			local quota = if room.Name == "MEN" or room.Name == "WOMEN" then QUOTA_WC elseif small then QUOTA_SMALL else QUOTA_BIG
			if room.Name == "NE" then -- по просьбе пользователя в переговорной ковров нет
				quota = table.clone(quota)
				quota.rug = 0
			end
			local order = {"bookcase", "cooler", "coat", "armchair", "cabinet", "lamp", "boxes", "planter"}

			-- сиденья и кухонная техника комнаты (для логики размещения)
			local seats: {Vector3} = {}
			local kitchens: {Vector3} = {}
local storage: {Vector3} = {}
			local desks: {Vector3} = {}
			for _, item in room:GetChildren() do
				if item:IsA("Model") then
					local n = item.Name
					if string.find(n, "Sofa", 1, true) or string.find(n, "Armchair", 1, true) or string.find(n, "Bench", 1, true) or string.find(n, "Couch", 1, true) then
						table.insert(seats, item:GetPivot().Position)
					elseif string.find(n, "Kitchen", 1, true) or string.find(n, "Coffee", 1, true) then
						table.insert(kitchens, item:GetPivot().Position)
elseif string.find(n, "Cabinet", 1, true) or string.find(n, "Shelf", 1, true) then
table.insert(storage, item:GetPivot().Position)
elseif string.find(n, "Desk", 1, true) then
table.insert(desks, item:GetPivot().Position)
end
				end
			end
			-- резерв проходов: от каждой двери комнаты к её центру, шириной 3 клетки
			do
				local roomCx, roomCz = (nx - 1) / 2, (nz - 1) / 2
				for _, door in doorPoints do
					local dix, diz = math.floor(door.X - x0), math.floor(door.Z - z0)
					if dix >= 0 and dix < nx and diz >= 0 and diz < nz then
						local steps = math.max(math.abs(roomCx - dix), math.abs(roomCz - diz))
						for step = 0, steps do
							local t = if steps > 0 then step / steps else 0
							local px, pz = math.floor(dix + (roomCx - dix) * t), math.floor(diz + (roomCz - diz) * t)
							for a = -1, 1 do
								for b = -1, 1 do
									if grid[idx(px + a, pz + b)] == 0 then
										grid[idx(px + a, pz + b)] = 6
									end
								end
							end
						end
					end
				end
			end
local roomDoors: {Vector3} = {}
			for _, door in doorPoints do
				local dix, diz = math.floor(door.X - x0), math.floor(door.Z - z0)
				if dix >= 0 and dix < nx and diz >= 0 and diz < nz then
					table.insert(roomDoors, door)
				end
			end
			if #roomDoors == 0 then
				roomDoors = doorPoints
			end
			local function nearest(list: {Vector3}, pos: Vector3): number
				local best = math.huge
				for _, point in list do
					local dx, dz = point.X - pos.X, point.Z - pos.Z
					best = math.min(best, math.sqrt(dx * dx + dz * dz))
				end
				return best
			end
			-- логика: где предмет уместен (nil = не ставить). corners: сколько торцов предмета упирается в стену
			local function scoreFor(kind: string, pos: Vector3, corners: number): number?
local doorDistance = nearest(roomDoors, pos)
				if kind == "coat" then -- вешалка у входа
					if doorDistance < 3.5 or doorDistance > 12 then
						return nil
					end
					return 10 - math.abs(doorDistance - 6)
				elseif kind == "cooler" then -- кулер у кухонной зоны, иначе у входа в проходной части
					local kitchenDistance = nearest(kitchens, pos)
					if kitchenDistance > 2 and kitchenDistance < 9 then
						return 12 - kitchenDistance
					end
					if #kitchens == 0 and doorDistance >= 4.5 and doorDistance <= 10 then
						return 4 - math.abs(doorDistance - 7)
					end
					return nil
				elseif kind == "lamp" then -- торшер рядом с сиденьями, иначе в углу
					local seatDistance = nearest(seats, pos)
					if seatDistance > 1.5 and seatDistance < 5.5 then
						return 10 - seatDistance
					end
					if corners > 0 then
						return 3 + corners
					end
					return nil
elseif kind == "armchair" then -- кресло: у журнального столика или кухонной зоны (беседа), иначе в углу большой комнаты
if doorDistance < 5 then
return nil
end
local tableDistance = nearest(kitchens, pos)
if tableDistance > 2.5 and tableDistance < 8 then
return 11 - tableDistance
end
if corners > 0 then
return 4 + corners
end
return nil
elseif kind == "cabinet" then -- картотека: недалеко от рабочих столов (бумаги под рукой), не у самой двери
if doorDistance < 5 then
return nil
end
local deskDistance = nearest(desks, pos)
if deskDistance > 2.5 and deskDistance < 9 then
return 8 - deskDistance / 2
end
return 1
elseif kind == "boxes" then -- коробки: в углу или у шкафов и стеллажей (там, где хранят)
					if corners > 0 then
						return 5 + corners * 2
					end
					local storageDistance = nearest(storage, pos)
					if storageDistance > 2.5 and storageDistance < 7.5 then
						return 3 - storageDistance / 4
					end
					return nil
				elseif kind == "planter" then -- растение: в углу или у входа сбоку от прохода
					if corners > 0 then
						return 5 + corners * 2
					end
					if doorDistance >= 4.5 and doorDistance <= 9 then
						return 3 - math.abs(doorDistance - 6.5) / 4
					end
					return nil
				end
				if doorDistance < 6 then -- шкаф не у самой двери
					return nil
				end
				return 1
			end
			-- вокруг предмета не должно быть мебели вплотную (проход и доступ к соседним предметам)
			local function ringClear(ix: number, iz: number, w: number, d: number, tx: number, tz: number, dx: number, dz: number): boolean
				for a = -1, w do
					for depth = 0, d + 1 do
						local edge = a == -1 or a == w or depth == d + 1
						if edge then
							local cx, cz = ix + tx * a + dx * depth, iz + tz * a + dz * depth
							if get(cx, cz) == 1 then
								return false
							end
						end
					end
				end
				return true
			end
			local kindPositions: {[string]: {Vector3}} = {}

			-- Доступность: от дверей по свободным клеткам (0 свободно, 4 ковёр, 6 проход). Цели: места у стульев и у шкафов/ящиков
			-- с подходом. Всё, что было достижимо до декора, должно остаться достижимым после каждого предмета.
			local function passable(flag: number): boolean
				return flag == 0 or flag == 4 or flag == 6
			end
			local sourceCells: {{number}} = {}
			for _, door in doorPoints do
				local dix, diz = math.floor(door.X - x0), math.floor(door.Z - z0)
				if dix >= 0 and dix < nx and diz >= 0 and diz < nz then
					table.insert(sourceCells, {dix, diz})
				end
			end
			if #sourceCells == 0 then
				table.insert(sourceCells, {(nx - 1) // 2, (nz - 1) // 2})
			end
			local function reachableSet(): {[number]: boolean}
				local seen: {[number]: boolean} = {}
				local queue: {number} = {}
				local head = 1
				for _, source in sourceCells do
					for a = -3, 3 do
						for b = -3, 3 do
							local ix, iz = source[1] + a, source[2] + b
							if passable(get(ix, iz)) and not seen[idx(ix, iz)] then
								seen[idx(ix, iz)] = true
								table.insert(queue, ix * 4096 + iz)
							end
						end
					end
				end
				while head <= #queue do
					local key = queue[head]
					head += 1
					local ix, iz = key // 4096, key % 4096
					for _, step in NEIGHBORS do
						local jx, jz = ix + step[1], iz + step[2]
						local jk = idx(jx, jz)
						if jx >= 0 and jx < nx and jz >= 0 and jz < nz and not seen[jk] and passable(get(jx, jz)) then
							seen[jk] = true
							table.insert(queue, jk)
						end
					end
				end
				return seen
			end
			local targetCells: {{number}} = {}
			for _, item in room:GetDescendants() do
				local position: Vector3? = nil
				if item:IsA("Model") and (string.find(item.Name, "ErgoChair", 1, true) or string.find(item.Name, "VisitorChair", 1, true) or string.find(item.Name, "MeetingChair", 1, true)) then
					position = item:GetPivot().Position
elseif item:IsA("ProximityPrompt") then
local holder = item.Parent
if holder and holder:IsA("BasePart") then
position = holder.Position
end
				end
				if position then
					table.insert(targetCells, {math.floor(position.X - x0), math.floor(position.Z - z0)})
				end
			end
			local function accessible(set: {[number]: boolean}, target: {number}): boolean
				for a = -2, 2 do
					for b = -2, 2 do
						if set[idx(target[1] + a, target[2] + b)] then
							return true
						end
					end
				end
				return false
			end
			local requiredTargets: {{number}} = {}
			do
				local before = reachableSet()
				for _, target in targetCells do
					if accessible(before, target) then
						table.insert(requiredTargets, target)
					end
				end
			end
			if isStudio then
				office:SetAttribute("KonturDecorTargets_" .. string.gsub(room.Name, "[^%w_]", "_"), tostring(#requiredTargets) .. "/" .. tostring(#targetCells))
			end
			local function accessOk(): boolean
				local after = reachableSet()
				for _, target in requiredTargets do
					if not accessible(after, target) then
						return false
					end
				end
				return true
			end

			for _, kind in order do
				local want = quota[kind] or 0
				if want > 0 then
					local candidates: {{ix: number, iz: number, dir: Vector3, tangent: Vector3, score: number}} = {}
					local foot = FOOT[kind]
					local w, d = foot[1], foot[2]
					for _, dir in DIRS do
						local tangent = Vector3.new(-dir.Z, 0, dir.X) -- вдоль стены
						local dx, dz = math.round(dir.X), math.round(dir.Z)
						local tx, tz = math.round(tangent.X), math.round(tangent.Z)
						for ix = 0, nx - 1 do
							for iz = 0, nz - 1 do
								if inside(ix, iz) then
									local ok = true
									-- за спиной сплошная стена, перед ней свободный прямоугольник и клетка прохода
									for a = 0, w - 1 do
										if get(ix + tx * a - dx, iz + tz * a - dz) ~= 2 then
											ok = false
											break
										end
										for depth = 0, d do
											local cx, cz = ix + tx * a + dx * depth, iz + tz * a + dz * depth
											if get(cx, cz) ~= 0 or not inside(cx, cz) then
												ok = false
												break
											end
											local pos = centre(cx, cz)
											if isForbidden(pos.X, pos.Z) then
												ok = false
												break
											end
										end
										if not ok then
											break
										end
									end
									if ok and ringClear(ix, iz, w, d, tx, tz, dx, dz) then
										-- угол: за торцом предмета (на первых двух рядах глубины) стоит перпендикулярная стена
										local corners = 0
										local startWall, endWall = false, false
										for depth = 0, 1 do
											if get(ix - tx + dx * depth, iz - tz + dz * depth) == 2 or get(ix - 2 * tx + dx * depth, iz - 2 * tz + dz * depth) == 2 then
												startWall = true
											end
											if get(ix + tx * w + dx * depth, iz + tz * w + dz * depth) == 2 or get(ix + tx * (w + 1) + dx * depth, iz + tz * (w + 1) + dz * depth) == 2 then
												endWall = true
											end
										end
										if startWall then
											corners += 1
										end
										if endWall then
											corners += 1
										end
										local pos = centre(ix, iz) + Vector3.new(tangent.X, 0, tangent.Z) * ((w - 1) / 2)
										local score = scoreFor(kind, pos, corners)
										if score then
											table.insert(candidates, {ix = ix, iz = iz, dir = dir, tangent = tangent, score = score + random:NextNumber(0, 0.6)})
										end
									end
								end
							end
						end
					end
					if isStudio then
						office:SetAttribute("KonturDecorCand_" .. string.gsub(room.Name, "[^%w_]", "_") .. "_" .. kind, #candidates)
					end
					table.sort(candidates, function(a, b)
						return a.score > b.score
					end)
					local placed = 0
					local attempts = 0
					for _, c in candidates do
						if placed >= want or attempts >= 80 then
							break
						end
						attempts += 1
						local dx, dz = math.round(c.dir.X), math.round(c.dir.Z)
						local tx, tz = math.round(c.tangent.X), math.round(c.tangent.Z)
						-- ещё свободно? (предыдущие предметы могли занять клетки)
						local free = true
						for a = 0, w - 1 do
							for depth = 0, d do
								if get(c.ix + tx * a + dx * depth, c.iz + tz * a + dz * depth) ~= 0 then
									free = false
								end
							end
						end
						-- не ближе 7 стадов к такому же предмету в этой комнате (равномерно, без кучи)
						local lateral = (w - 1) / 2
						local centreCell = centre(c.ix, c.iz) + c.tangent * lateral
						for _, other in kindPositions[kind] or {} do
							if (other - centreCell).Magnitude < 7 then
								free = false
							end
						end
						if free then
							-- точная плоскость стены лучом от первой клетки
							local origin = centre(c.ix, c.iz) + Vector3.new(0, 2.5, 0)
local hit = workspace:Raycast(origin, -c.dir * 2.5, wallParams)
if hit then
local alongNormal = centreCell:Dot(c.dir) - hit.Position:Dot(c.dir)
local wallPoint = centreCell - c.dir * alongNormal -- точка плоскости стены напротив центра предмета
-- высокие предметы не закрывают окна и стенные приборы (часы, доски, знаки): от плоскости стены на 0.9 вглубь пусто в полосе предмета
local blockedBand = false
local bandHeight = if kind == "bookcase" or kind == "coat" then 4.4 elseif kind == "cabinet" then 1.4 else 0
if bandHeight > 0 then
local bandY = if kind == "cabinet" then 3.9 else 5.4
local bandCentre = Vector3.new(wallPoint.X + c.dir.X * 0.45, bandY, wallPoint.Z + c.dir.Z * 0.45)
local band = workspace:GetPartBoundsInBox(CFrame.lookAt(bandCentre, bandCentre + c.dir), Vector3.new(w + 0.3, bandHeight, 0.9), probeParams)
									for _, blocker in band do
										-- молдинг по стене (DadoRail на высоте ~3.3) и плинтус не считаются: шкаф встаёт перед ними
										if not blocker:IsDescendantOf(structure) and not string.find(blocker.Name, "^DadoRail") and not string.find(blocker.Name, "^Skirting") then
											if isStudio then
												local key = "KonturDecorBand_" .. string.sub(string.gsub(string.gsub(blocker.Name, "%d+", "N"), "[^%w]", "_"), 1, 30)
												office:SetAttribute(key, (office:GetAttribute(key) or 0) + 1)
											end
											blockedBand = true
											break
										end
									end
								end
if not blockedBand then
local position = wallPoint + c.dir * (BACK_OFFSET[kind] + 0.03)
									position = Vector3.new(position.X, FLOOR_Y, position.Z)
									local base = CFrame.lookAt(position, position + c.dir)
									local ok, model = pcall(BUILD[kind], base)
									if ok then
local built = model :: Model
built.Parent = folder
built:SetAttribute("KonturRoom", room.Name)
-- помечаем занятые клетки (с запасом в одну по бокам) и проверяем, что подходы остались
										local changed: {number} = {}
										for a = -1, w do
											for depth = -1, d do
												local cx, cz = c.ix + tx * a + dx * depth, c.iz + tz * a + dz * depth
												if grid[idx(cx, cz)] == 0 then
													grid[idx(cx, cz)] = 3
													table.insert(changed, idx(cx, cz))
												end
											end
										end
										if accessOk() then
											totalPlaced += 1
											count(kind)
											placed += 1
											kindPositions[kind] = kindPositions[kind] or {}
											table.insert(kindPositions[kind], centreCell)
										else
											built:Destroy()
											for _, key in changed do
												grid[key] = 0
											end
											count("rolledBack")
										end
									else
										warn("KONTUR decor build failed (" .. kind .. "): " .. tostring(model))
									end
								end
							end
						end
					end
				end
			end

			-- картины и плакаты: на сплошные участки стен без других предметов в полосе 3..6.2
			local framesWanted = quota.frames or 0
			local framesPlaced = 0
			local wallSpots: {{cell: Vector3, dir: Vector3, tangent: Vector3}} = {}
			for ix = 0, nx - 1 do
				for iz = 0, nz - 1 do
if inside(ix, iz) and get(ix, iz) ~= 2 and get(ix, iz) ~= 3 then
						for _, dir in DIRS do
							local dx, dz = math.round(dir.X), math.round(dir.Z)
							if get(ix - dx, iz - dz) == 2 then
								local pos = centre(ix, iz)
								if not isForbidden(pos.X, pos.Z) then
									table.insert(wallSpots, {cell = pos, dir = dir, tangent = Vector3.new(-dir.Z, 0, dir.X)})
								end
							end
						end
					end
				end
			end
			-- свободный прямоугольник w x d клеток во внутренней области (с запасом в 1 клетку прохода)
local function findFree(w: number, d: number, margin: number, tries: number, avoid: {{number}}?, allowPath: boolean?): (number?, number?)
				if nx - pad - w < pad or nz - pad - d < pad then
					return nil, nil
				end
				local roomCx, roomCz = (nx - 1) / 2, (nz - 1) / 2
				local bestX: number? = nil
				local bestZ: number? = nil
				local bestDist = math.huge
				for _ = 1, tries do
					local ix = random:NextInteger(pad, nx - pad - w)
					local iz = random:NextInteger(pad, nz - pad - d)
					local ok = true
					for a = -margin, w - 1 + margin do
						for b = -margin, d - 1 + margin do
local flag = get(ix + a, iz + b)
if flag ~= 0 and not (allowPath and flag == 6) then
ok = false
end
						end
					end
if ok and avoid then
for _, rect in avoid do
if x0 + ix - 0.5 < rect[2] and x0 + ix + w + 0.5 > rect[1] and z0 + iz - 0.5 < rect[4] and z0 + iz + d + 0.5 > rect[3] then
ok = false
break
end
end
end
if ok then
local pos = centre(ix + w // 2, iz + d // 2)
if not isForbidden(pos.X, pos.Z) then
							local dist = (ix + w / 2 - roomCx) ^ 2 + (iz + d / 2 - roomCz) ^ 2
							if dist < bestDist then
								bestDist = dist
								bestX, bestZ = ix, iz
							end
						end
					end
				end
				return bestX, bestZ
			end
-- границы деталей модели в мире (по углам каждой детали, не по ориентированному ящику модели): minX, maxX, minZ, maxZ, minY
local function worldExtents(model: Model): (number, number, number, number, number)
local lx, hx, lz, hz, ly = math.huge, -math.huge, math.huge, -math.huge, math.huge
for _, d in model:GetDescendants() do
if d:IsA("BasePart") then
local half = d.Size / 2
for sx = -1, 1, 2 do
for sy = -1, 1, 2 do
for sz = -1, 1, 2 do
local point = d.CFrame:PointToWorldSpace(Vector3.new(half.X * sx, half.Y * sy, half.Z * sz))
lx, hx = math.min(lx, point.X), math.max(hx, point.X)
lz, hz = math.min(lz, point.Z), math.max(hz, point.Z)
ly = math.min(ly, point.Y)
end
end
end
end
end
return lx, hx, lz, hz, ly
end
-- ковры RoomStyle (под журнальным и переговорным столами, в кабинете) создаются позже на высоте 0.12: наши не кладём рядом с этими столами
local rugAvoid: {{number}} = {}
for _, item in room:GetChildren() do
if item:IsA("Model") and (string.find(item.Name, "CoffeeTable", 1, true) or string.find(item.Name, "MeetingTable", 1, true) or string.find(item.Name, "ExecutiveDesk", 1, true)) then
local lx, hx, lz, hz = worldExtents(item)
if lx < hx then
table.insert(rugAvoid, {lx - 2.4, hx + 2.4, lz - 2.4, hz + 2.4})
end
end
end

			-- дополнительные рабочие места: клон готового комплекта (стол, кресло, монитор, блок, мелочи) из этой же комнаты.
			-- Габариты комплекта считаются по исходному столу, место ищем под весь комплект с запасом на проход.
			for _ = 1, (quota.workstation or 0) do
				local sources: {Model} = {}
				for _, item in room:GetChildren() do
if item:IsA("Model") and string.find(item.Name, "StraightDesk", 1, true) and not isForbidden(item:GetPivot().Position.X, item:GetPivot().Position.Z) then
table.insert(sources, item)
					end
				end
				if #sources > 0 then
					local source = sources[random:NextInteger(1, #sources)]
					local deskCentre = source:GetPivot().Position
					local pieces: {Model} = {}
					local minX, maxX, minZ, maxZ = math.huge, -math.huge, math.huge, -math.huge
					for _, item in room:GetChildren() do
						if item:IsA("Model") and item.Archivable then
local centreOfItem = item:GetPivot().Position
local dx, dz = centreOfItem.X - deskCentre.X, centreOfItem.Z - deskCentre.Z
if dx * dx + dz * dz < 3.8 * 3.8 then
local excluded = string.find(item.Name, "Plant", 1, true) or string.find(item.Name, "Cabinet", 1, true)
or string.find(item.Name, "Printer", 1, true) or string.find(item.Name, "Mirror", 1, true)
or string.find(item.Name, "Rug", 1, true) or string.find(item.Name, "Carpet", 1, true)
local scripted = item:FindFirstChildWhichIsA("BaseScript", true) or item:FindFirstChildWhichIsA("ProximityPrompt", true)
if not excluded and not scripted then
local lx, hx, lz, hz, ly = worldExtents(item)
-- на стене висящее (часы, доски, знаки: низ выше 4.2) и слишком большое в комплект не берём
if lx < hx and ly < 4.2 and hx - lx < 7.5 and hz - lz < 7.5 then
table.insert(pieces, item)
minX, maxX = math.min(minX, lx), math.max(maxX, hx)
minZ, maxZ = math.min(minZ, lz), math.max(maxZ, hz)
end
end
end
						end
					end
					if #pieces > 0 then
						local cellsW, cellsD = math.ceil(maxX - minX) + 1, math.ceil(maxZ - minZ) + 1
						local ix, iz = findFree(cellsW, cellsD, 2, 160)
						if ix and iz then
							-- комплект своим углом (minX, minZ) встаёт в угол найденной свободной области
							local cornerTarget = centre(ix, iz)
							local delta = CFrame.new(cornerTarget.X - 0.5 - minX, 0, cornerTarget.Z - 0.5 - minZ)
							local group = newModel("KD_Workstation")
							for _, item in pieces do
local copy = item:Clone() :: Model
copy.Parent = group
								copy:PivotTo(delta * item:GetPivot())
							end
							group.Parent = folder
							local changed: {number} = {}
							for a = -1, cellsW do
								for b = -1, cellsD do
									if grid[idx(ix + a, iz + b)] == 0 then
										grid[idx(ix + a, iz + b)] = 3
										table.insert(changed, idx(ix + a, iz + b))
									end
								end
							end
							if accessOk() then
								totalPlaced += 1
								count("workstation")
							else
								group:Destroy()
								for _, key in changed do
									grid[key] = 0
								end
								count("rolledBack")
							end
						end
					end
				end
			end

			-- ковёр в самой открытой части комнаты
			for _ = 1, (quota.rug or 0) do
				local rw, rd = if small then 6 else 8, if small then 4 else 6
local ix, iz = findFree(rw, rd, 0, 160, rugAvoid, true)
				if ix and iz then
					local centreCell = centre(ix, iz) + Vector3.new(rw / 2 - 0.5, 0, rd / 2 - 0.5)
local rugModel = rug(centreCell, rw - 0.4, rd - 0.4, Vector3.new(0, 0, 1))
					rugModel.Parent = folder
					totalPlaced += 1
					count("rug")
					for a = 0, rw - 1 do
						for b = 0, rd - 1 do
							-- ковёр не блокирует расстановку других предметов сверху, но второй ковёр сюда не ляжет
							if grid[idx(ix + a, iz + b)] == 0 then
								grid[idx(ix + a, iz + b)] = 4
							end
						end
					end
				end
			end

			local attempts = 0
			local framePositions: {Vector3} = {}
			while framesPlaced < framesWanted and #wallSpots > 0 and attempts < 200 do
				attempts += 1
				local pickIndex = random:NextInteger(1, #wallSpots)
				local spot = wallSpots[pickIndex]
				table.remove(wallSpots, pickIndex)
				local width = ({1.6, 2.2, 2.8, 1.2, 3.2})[random:NextInteger(1, 5)]
				local height = ({1.2, 1.6, 1.9, 1.5})[random:NextInteger(1, 4)]
				local origin = spot.cell + Vector3.new(0, 4.9 - FLOOR_Y, 0)
				local hit = workspace:Raycast(origin, -spot.dir * 2, wallParams)
				if hit then
					local centrePoint = hit.Position + spot.dir * 0.09
					local frame = CFrame.lookAt(centrePoint, centrePoint + spot.dir)
					-- вокруг должна быть пустая стена: ни мебели, ни окон, ни других картин
					local probe = CFrame.lookAt(hit.Position + spot.dir * 0.3, hit.Position + spot.dir * 0.3 + spot.dir) * CFrame.new(0, 0, 0)
local blockers = workspace:GetPartBoundsInBox(probe, Vector3.new(width + 0.6, height + 0.6, 0.5), probeParams)
					local clear = true
					for _, blocker in blockers do
						if not blocker:IsDescendantOf(structure) then
							clear = false
							break
						end
					end
					-- стена должна продолжаться по обе стороны картины (не висеть над дверным проёмом)
					for _, side in {-1, 1} do
						local edge = workspace:Raycast(origin + spot.tangent * (side * (width / 2 + 0.1)), -spot.dir * 2, wallParams)
						if not edge or math.abs((edge.Position - hit.Position):Dot(spot.dir)) > 0.25 then
							clear = false
						end
					end
					for _, other in framePositions do
						if (other - centrePoint).Magnitude < width + 1.2 then
							clear = false
							break
						end
					end
					-- не ближе 4 стадов к дверям и точкам аномалий (на высоте стены тоже)
					if clear and not isForbidden(centrePoint.X, centrePoint.Z) then
						local ok, model = pcall(wallFrame, frame, width, height)
						if ok then
							local built = model :: Model
							built.Parent = folder
							framesPlaced += 1
							totalPlaced += 1
							count("frames")
							table.insert(framePositions, centrePoint)
						else
							warn("KONTUR decor frame failed: " .. tostring(model))
						end
					end
				end
			end
		end
end
	for _, room in rooms:GetChildren() do
		local ok, err = pcall(processRoom, room)
		if not ok then
			warn("KONTUR decor room " .. room.Name .. " failed: " .. tostring(err))
		end
		task.wait()
	end
	if next(HERO_ASSETS) ~= nil then
		task.spawn(applyHeroMeshes)
	end
	if isStudio then
		office:SetAttribute("KonturDecorCount", totalPlaced)
		for name, n in counts do
			office:SetAttribute("KonturDecor_" .. name, n)
		end
	end
end

return attachOfficeDecor
