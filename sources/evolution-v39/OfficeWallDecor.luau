--!strict
-- v43 настенный декор: кондиционеры, потёки и пятна от воды, трещины, облупленная краска, щиты и трубы, пожарная сигнализация, камеры,
-- указатели выхода, схемы эвакуации, вентиляция, полки и мелкие причуды (мышиная нора, дыра в стене, зарубки). Все модели сделаны в Blender
-- (sources/evolution-v39/blender/wall_hero.py), загружены в Roblox, id подставляет сборщик. Папка KonturWallDecor.
-- Места подбираются так: по периметру каждой комнаты и коридора лучами находятся участки сплошной стены (WallCoreN_M), у предмета проверяется,
-- что вся его площадь лежит на одной плоскости стены, нет окна, двери, шкафа, плаката или другого предмета (по границам всех видимых деталей карты),
-- и что вокруг дверей остаётся свободный проём. План на каждую комнату свой (архив с трубами и щитами, туалеты с вентиляцией и сыростью, залы
-- с кондиционерами и трещинами), поэтому комнаты не повторяют друг друга. Предметы без коллизии и без запросов лучей.
local function attachWallDecorInner(office: Instance)
	task.wait(26) -- ждём остальные модули (шкафы, мебель, коридор)
	local ASSETS: {[string]: number} = {}
	-- @@WALL_ASSETS@@
	if next(ASSETS) == nil then
		warn("KONTUR wall decor: no assets")
		return
	end
	local rng = Random.new(20261115)
	local folder = Instance.new("Folder")
	folder.Name = "KonturWallDecor"
	local LOOK: {[string]: Enum.Material} = {
		metal = Enum.Material.Metal, copper = Enum.Material.Metal, brass = Enum.Material.Metal, rubber = Enum.Material.Plastic,
		glow = Enum.Material.Neon, brick = Enum.Material.Brick, wood_mid = Enum.Material.Wood, wood_dark = Enum.Material.Wood,
	}

	type Bounds = {minX: number, maxX: number, minY: number, maxY: number, minZ: number}
	type Template = {model: Model, b: Bounds}
	type Site = {pos: Vector3, n: Vector3, t: Vector3, color: Color3, area: string}

	----------------------------------------------------------------- шаблоны
	local function loadTemplate(key: string, assetId: number): Template?
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
			warn("KONTUR wall decor asset " .. key .. " (" .. tostring(assetId) .. ") failed")
			return nil
		end
		local model = Instance.new("Model")
		model.Name = "Wall_" .. key
		local b: Bounds = {minX = math.huge, maxX = -math.huge, minY = math.huge, maxY = -math.huge, minZ = math.huge}
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
				mesh.CastShadow = suffix ~= "stain" and suffix ~= "tint"
				mesh:SetAttribute("WallDecorMat", suffix or "")
				local p, s = mesh.Position, mesh.Size / 2
				b.minX = math.min(b.minX, p.X - s.X)
				b.maxX = math.max(b.maxX, p.X + s.X)
				b.minY = math.min(b.minY, p.Y - s.Y)
				b.maxY = math.max(b.maxY, p.Y + s.Y)
				b.minZ = math.min(b.minZ, p.Z - s.Z)
				mesh.Parent = model
			end
		end
		container:Destroy()
		if #model:GetChildren() == 0 then
			model:Destroy()
			return nil
		end
		return {model = model, b = b}
	end

	local templates: {[string]: Template} = {}
	for key, id in ASSETS do
		local tpl = loadTemplate(key, id)
		if tpl then
			templates[key] = tpl
		end
		task.wait()
	end

	----------------------------------------------------------------- участки: комнаты, коридоры, двери
	local areas: {{name: string, lo: Vector3, hi: Vector3}} = {}
	local floors = office:FindFirstChild("Floors")
	if floors then
		for _, room in floors:GetChildren() do
			if room.Name ~= "V09FloorSupport" then
				local lo, hi = Vector3.new(math.huge, 0, math.huge), Vector3.new(-math.huge, 0, -math.huge)
				for _, d in room:GetDescendants() do
					if d:IsA("BasePart") then
						lo = Vector3.new(math.min(lo.X, d.Position.X - d.Size.X / 2), 0, math.min(lo.Z, d.Position.Z - d.Size.Z / 2))
						hi = Vector3.new(math.max(hi.X, d.Position.X + d.Size.X / 2), 0, math.max(hi.Z, d.Position.Z + d.Size.Z / 2))
					end
				end
				if lo.X < hi.X then
					table.insert(areas, {name = room.Name, lo = lo, hi = hi})
				end
			end
		end
	end
	local function areaAt(p: Vector3): string
		for _, a in areas do
			if p.X > a.lo.X and p.X < a.hi.X and p.Z > a.lo.Z and p.Z < a.hi.Z then
				return a.name
			end
		end
		return "?"
	end

	-- сплошные стены: только WallCoreN_M (плинтусы, кронштейны и прочее «Wall...» не годятся как основание)
	local wallParts: {Instance} = {}
	local structure = office:FindFirstChild("Structure")
	if structure then
		for _, d in structure:GetDescendants() do
			if d:IsA("BasePart") and (string.match(d.Name, "^WallCore%d+_%d+PlasterUpper$") or string.match(d.Name, "^WallCore%d+_%d+PaintLower$")) then
				table.insert(wallParts, d)
			end
		end
	end
	local wallParams = RaycastParams.new()
	wallParams.FilterType = Enum.RaycastFilterType.Include
	wallParams.FilterDescendantsInstances = wallParts

	----------------------------------------------------------------- занятость: границы всех видимых деталей у стен
	local CELL = 6
	local grid: {[number]: {{number}}} = {}
	local function cellKey(ix: number, iz: number): number
		return (ix + 64) * 1024 + (iz + 64)
	end
	local function addBox(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, furniture: boolean?)
		local box = {x0, x1, y0, y1, z0, z1, if furniture then 1 else 0}
		for ix = math.floor(x0 / CELL), math.floor(x1 / CELL) do
			for iz = math.floor(z0 / CELL), math.floor(z1 / CELL) do
				local k = cellKey(ix, iz)
				local list = grid[k]
				if not list then
					list = {}
					grid[k] = list
				end
				table.insert(list, box)
			end
		end
	end
	local function partBox(d: BasePart): {number}?
		local cf, s = d.CFrame, d.Size
		local rx, ry, rz = cf.RightVector, cf.UpVector, cf.LookVector
		local hx = (math.abs(rx.X) * s.X + math.abs(ry.X) * s.Y + math.abs(rz.X) * s.Z) / 2
		local hy = (math.abs(rx.Y) * s.X + math.abs(ry.Y) * s.Y + math.abs(rz.Y) * s.Z) / 2
		local hz = (math.abs(rx.Z) * s.X + math.abs(ry.Z) * s.Y + math.abs(rz.Z) * s.Z) / 2
		if hx > 30 or hz > 30 or cf.Y + hy < 0.4 then
			return nil -- пол, ковры, стены целиком
		end
		return {cf.X - hx, cf.X + hx, cf.Y - hy, cf.Y + hy, cf.Z - hz, cf.Z + hz}
	end
	-- мебель и вещи комнат: то, что стоит на полу у стены и просто закрывает собой пятно (двери, окна и отделка сюда не входят)
	local FURNITURE: {[string]: boolean} = {Rooms = true, KonturDecor = true, KonturEast = true, KonturWC = true}
	local scanned = 0
	for _, top in office:GetChildren() do
		if top ~= folder and top.Name ~= "Structure" and top.Name ~= "Floors" and top.Name ~= "Ceiling" and top.Name ~= "AnomalyReportState" then
			for _, d in top:GetDescendants() do
				-- карнизы, поручни-«дадо» и плинтусы это отделка самой стены: предмет может лежать поверх (на 5 см)
				if d:IsA("BasePart") and d.Transparency < 0.95 and not string.match(d.Name, "^Cornice") and not string.match(d.Name, "^DadoRail")
					and not string.match(d.Name, "^Skirting") and not string.match(d.Name, "^CoveStrip") then
					local box = partBox(d)
					if box then
						addBox(box[1], box[2], box[3], box[4], box[5], box[6], FURNITURE[top.Name] == true)
					end
				end
				scanned += 1
				if scanned % 2500 == 0 then
					task.wait()
				end
			end
		end
	end
	-- relaxed: стоящее на полу (шкафы, стеллажи) не мешает пятнам и трещинам: стена за ним просто не видна
	local function blocked(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, relaxed: boolean): boolean
		for ix = math.floor(x0 / CELL), math.floor(x1 / CELL) do
			for iz = math.floor(z0 / CELL), math.floor(z1 / CELL) do
				local list = grid[cellKey(ix, iz)]
				if list then
					for _, b in list do
						if b[1] < x1 and b[2] > x0 and b[3] < y1 and b[4] > y0 and b[5] < z1 and b[6] > z0 and not (relaxed and b[7] == 1 and b[3] < 1.2) then
							return true
						end
					end
				end
			end
		end
		return false
	end

	----------------------------------------------------------------- участки стены по периметру
	local sitesByArea: {[string]: {Site}} = {}
	local function addSite(areaName: string, from: Vector3, dir: Vector3, maxDist: number)
		local hit = workspace:Raycast(from, dir * maxDist, wallParams)
		if hit and math.abs(hit.Normal.Y) < 0.05 and math.abs(hit.Normal:Dot(-dir)) > 0.97 then
			local n = hit.Normal
			local sites = sitesByArea[areaName]
			if not sites then
				sites = {}
				sitesByArea[areaName] = sites
			end
			local inst = hit.Instance :: BasePart
			table.insert(sites, {pos = hit.Position, n = n, t = Vector3.new(-n.Z, 0, n.X), color = inst.Color, area = areaName})
		end
	end
	for _, a in areas do
		local STEP = 1.6
		local INSET = 1.0
		local x = a.lo.X + 1.5
		while x < a.hi.X - 1.5 do
			addSite(a.name, Vector3.new(x, 7, a.lo.Z + INSET), -Vector3.zAxis, INSET + 0.9)
			addSite(a.name, Vector3.new(x, 7, a.hi.Z - INSET), Vector3.zAxis, INSET + 0.9)
			x += STEP
		end
		local z = a.lo.Z + 1.5
		while z < a.hi.Z - 1.5 do
			addSite(a.name, Vector3.new(a.lo.X + INSET, 7, z), -Vector3.xAxis, INSET + 0.9)
			addSite(a.name, Vector3.new(a.hi.X - INSET, 7, z), Vector3.xAxis, INSET + 0.9)
			z += STEP
		end
		task.wait()
	end

	local doorBoxes: {{pos: Vector3, look: Vector3, size: Vector3}} = {}
	local doors = office:FindFirstChild("Doors")
	if doors then
		for _, door in doors:GetChildren() do
			local ok, cf, size = pcall(function()
				local c, s = (door :: Model):GetBoundingBox()
				return c, s
			end)
			if ok then
				table.insert(doorBoxes, {pos = (cf :: CFrame).Position, look = (cf :: CFrame).LookVector, size = size :: Vector3})
			end
		end
	end

	----------------------------------------------------------------- размещение
	local FLOOR_Y = 0.05
	local TOP_Y = 10.9
	local CEIL_Y = 11.12 -- верх стены под карнизом (карниз Cornice лежит с 11,1): пятна от потолка начинаются вплотную к нему
	local RAY_LO, RAY_HI = 0.3, 10.8 -- стена стоит на 0,1 и кончается около 11,2: лучи вне этой полосы промахиваются
	local rejects: {[string]: number} = {}
	local function reject(key: string, why: string): boolean
		local k = key .. "_" .. why
		rejects[k] = (rejects[k] or 0) + 1
		return false
	end
	-- высота начала координат модели: y = центр; top = верх по потолку; floor = низ на полу
	local HEIGHT: {[string]: {y: number?, top: boolean?, floor: boolean?}} = {
		AcSplit = {y = 9.1}, AcSplitOld = {y = 9.1}, AcSplitWide = {y = 9.2},
		StainBloom = {top = true}, StainStreaks = {top = true}, StainTide = {y = 7.6}, RustDrip = {y = 7.4}, DampLow = {floor = true},
		CrackLong = {y = 6.6}, CrackStar = {y = 6.0}, CrackStep = {y = 7.4}, PeelPatch = {y = 6.4}, PaintBlister = {y = 7.0},
		ElecPanel = {y = 6.1}, ElecPanelOpen = {y = 6.1}, PipeRun = {y = 7.6}, PipeRiser = {floor = true},
		FireAlarm = {y = 4.9}, FireHorn = {y = 8.7}, Thermostat = {y = 5.0}, CamBullet = {y = 9.3}, CamDome = {y = 9.6},
		EmergencyLamp = {y = 8.6}, WallLadder = {floor = true}, CableLoops = {y = 8.6},
		ExitSign = {y = 10.3}, EvacPlan = {y = 5.7}, VentGrille = {top = true}, FanVent = {y = 8.2}, VentDuct = {y = 8.6},
		Sanitizer = {y = 5.0}, LightSwitch = {y = 4.6}, Keypad = {y = 4.9}, ShelfBooks = {y = 6.4}, ShelfDecor = {y = 6.0}, ShelfDecorB = {y = 6.0}, ShelfDecorC = {y = 6.0}, HandDryer = {y = 4.2},
		MouseHole = {floor = true}, WallHole = {y = 5.2}, TallyMarks = {y = 5.3},
	}
	local DECAL: {[string]: boolean} = {
		StainBloom = true, StainStreaks = true, StainTide = true, RustDrip = true, DampLow = true, CrackLong = true, CrackStar = true, CrackStep = true,
		PeelPatch = true, PaintBlister = true, TallyMarks = true,
	}
	-- по просьбе пользователя убраны: потёки и пятна, трещины, облупленная краска и пузыри, пролом, зарубки, открытый щит, лестница, дозатор,
	-- кодовая панель; в туалетах (MEN, WOMEN) нового декора нет. Модели остаются в репозитории и не ставятся.
	local REMOVED: {[string]: boolean} = {
		StainBloom = true, StainStreaks = true, StainTide = true, RustDrip = true, DampLow = true, CrackLong = true, CrackStar = true, CrackStep = true,
		PeelPatch = true, PaintBlister = true, WallHole = true, TallyMarks = true, ElecPanelOpen = true, WallLadder = true, Sanitizer = true, Keypad = true,
		ElecPanel = true, Thermostat = true, EmergencyLamp = true, FanVent = true, MouseHole = true,
	}
	local NO_DECOR_AREAS: {[string]: boolean} = {MEN = true, WOMEN = true}
	local counts: {[string]: number} = {}
	local placedAt: {[string]: {Vector3}} = {}
	local total = 0

	local function originHeight(key: string, b: Bounds): number
		local h = HEIGHT[key] or {y = 6.0}
		if h.top then
			return CEIL_Y - b.maxY
		elseif h.floor then
			return FLOOR_Y - b.minY
		end
		return h.y or 6.0
	end

	local LATERAL = {-1, 0, 1}
	local ALONG = {0, 0.33, 0.66, 1}
	local function flatWall(site: Site, y: number, b: Bounds): boolean
		local halfW = math.max(math.abs(b.minX), math.abs(b.maxX))
		local base = Vector3.new(site.pos.X, 0, site.pos.Z)
		for _, k in LATERAL do
			for _, fy in ALONG do
				local yy = math.clamp(y + b.minY + (b.maxY - b.minY) * fy, RAY_LO, RAY_HI)
				local on = base + site.t * (halfW * k) + Vector3.new(0, yy, 0)
				local hit = workspace:Raycast(on + site.n * 0.6, -site.n * 1.2, wallParams)
				if not hit or math.abs((hit.Position - on):Dot(site.n)) > 0.1 then
					return false
				end
			end
		end
		return true
	end

	local function nearDoor(site: Site, halfW: number): boolean
		for _, d in doorBoxes do
			local dp = site.pos - d.pos
			if math.abs(dp:Dot(site.n)) < 1.2 and math.abs(dp:Dot(site.t)) < d.size.X / 2 + halfW + 0.8 then
				return true
			end
		end
		return false
	end

	local function textOverlay(model: Model, key: string, cf: CFrame)
		if key ~= "EvacPlan" then
			return
		end
		local p = Instance.new("Part")
		p.Name = "HeaderText"
		p.Size = Vector3.new(3.3, 0.4, 0.02)
		p.CFrame = cf * CFrame.new(0, 1.02, -0.205)
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.CastShadow = false
		p.Transparency = 1
		p.Parent = model
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
		gui.CanvasSize = Vector2.new(330, 40)
		gui.LightInfluence = 0.5
		gui.Parent = p
		local t = Instance.new("TextLabel")
		t.Size = UDim2.fromScale(1, 1)
		t.BackgroundTransparency = 1
		t.TextColor3 = Color3.fromRGB(240, 250, 244)
		t.Font = Enum.Font.GothamBold
		t.TextScaled = true
		t.Text = "ПЛАН ЭВАКУАЦИИ"
		t.Parent = gui
	end

	-- ставит предмет на участок, если там ровная стена и пусто; возвращает true при успехе
	local function tryPlace(key: string, site: Site, ignoreDoors: boolean?): boolean
		local tpl = templates[key]
		if not tpl or REMOVED[key] or (NO_DECOR_AREAS[site.area] and key ~= "HandDryer") then
			return false
		end
		local b = tpl.b
		local y = originHeight(key, b)
		local halfW = math.max(math.abs(b.minX), math.abs(b.maxX))
		if not ignoreDoors and nearDoor(site, halfW) then
			return reject(key, "door")
		end
		local gap = if ignoreDoors then 3 else 12 -- у дверей предметы разных проёмов могут стоять близко, но не вплотную
		for _, other in placedAt[key] or {} do
			if (other - site.pos).Magnitude < gap then
				return reject(key, "near")
			end
		end
		-- трубы-стояки доходят до потолка (подпотолочная плита на 11,5): им разрешён верх до 11,6, остальным 11,3
		local topLimit = if key == "PipeRiser" or key == "PipeRun" then 11.6 else TOP_Y + 0.4
		if y + b.minY < FLOOR_Y - 0.2 or y + b.maxY > topLimit then
			return reject(key, "height")
		end
		local origin = Vector3.new(site.pos.X, y, site.pos.Z) + site.n * 0.02
		local cf = CFrame.lookAt(origin, origin + site.n)
		-- коробка предмета в мире: от плоскости стены до выноса плюс запас (за стену не заходит: по ту сторону своя комната), вдоль стены с запасом
		local depth = -b.minZ
		local m = 0.3
		local mv = 0.2 -- по вертикали запас меньше: стены высокие, а полосы под потолком и над поручнем узкие
		local far = origin + site.n * (depth + m)
		local wx, wz = math.abs(site.t.X) * (halfW + m), math.abs(site.t.Z) * (halfW + m)
		local x0, x1 = math.min(origin.X, far.X) - wx, math.max(origin.X, far.X) + wx
		local z0, z1 = math.min(origin.Z, far.Z) - wz, math.max(origin.Z, far.Z) + wz
		-- настенные приборы не должны упираться в мебель под ними: свободно от пояса до верха (иначе извещатель торчит из шкафа)
		local lowY = if (key == "FireAlarm" or key == "LightSwitch" or key == "FireHorn") then 0.5 else y + b.minY - mv
		if blocked(x0, x1, lowY, y + b.maxY + mv, z0, z1, DECAL[key] == true) then
			return reject(key, "busy")
		end
		if not flatWall(site, y, b) then
			return reject(key, "flat")
		end
		local model = Instance.new("Model")
		model.Name = "WD_" .. (string.gsub(key, "Shelf", "Ledge")) -- без слова Shelf: у декора комнат есть поиск по имени «Shelf»
		for _, part in tpl.model:GetChildren() do
			local c = part:Clone() :: MeshPart
			c.CFrame = cf * (part :: MeshPart).CFrame
			if c:GetAttribute("WallDecorMat") == "tint" then
				c.Color = site.color
			end
			c.Parent = model
		end
		textOverlay(model, key, cf)
		model:SetAttribute("Area", site.area)
		model:SetAttribute("Mount", cf)
		model:SetAttribute("WallPoint", site.pos)
		model.Parent = folder
		local tip = origin + site.n * depth
		local tx, tz = math.abs(site.t.X) * halfW, math.abs(site.t.Z) * halfW
		addBox(math.min(origin.X, tip.X) - tx, math.max(origin.X, tip.X) + tx, y + b.minY, y + b.maxY, math.min(origin.Z, tip.Z) - tz, math.max(origin.Z, tip.Z) + tz)
		local list = placedAt[key]
		if not list then
			list = {}
			placedAt[key] = list
		end
		table.insert(list, site.pos)
		counts[key] = (counts[key] or 0) + 1
		total += 1
		return true
	end

	local function shuffled(list: {Site}): {Site}
		local out = table.clone(list)
		for i = #out, 2, -1 do
			local j = rng:NextInteger(1, i)
			out[i], out[j] = out[j], out[i]
		end
		return out
	end

	-- любой из участков комнаты, по порядку случайной перестановки
	local function placeIn(areaNames: {string}, key: string): boolean
		local pool: {Site} = {}
		for _, name in areaNames do
			for _, s in sitesByArea[name] or {} do
				table.insert(pool, s)
			end
		end
		local tries = 0
		for _, site in shuffled(pool) do
			if tryPlace(key, site) then
				return true
			end
			tries += 1
			if tries % 12 == 0 then
				task.wait()
			end
			if tries > 260 then
				break
			end
		end
		return false
	end

	----------------------------------------------------------------- у дверей: указатель выхода, выключатель, кодовая панель, дезинфектор
	local function doorSite(d: {pos: Vector3, look: Vector3, size: Vector3}, side: number, lateral: number, y: number): Site?
		local flat = Vector3.new(d.look.X, 0, d.look.Z)
		if flat.Magnitude < 0.5 then
			return nil
		end
		local n = flat.Unit * side
		local t = Vector3.new(-n.Z, 0, n.X)
		local from = Vector3.new(d.pos.X, y, d.pos.Z) + t * lateral + n * 1.0
		local hit = workspace:Raycast(from, -n * 2.0, wallParams)
		if hit and math.abs(hit.Normal:Dot(n)) > 0.97 then
			local inst = hit.Instance :: BasePart
			return {pos = hit.Position, n = hit.Normal, t = Vector3.new(-hit.Normal.Z, 0, hit.Normal.X), color = inst.Color, area = areaAt(hit.Position + hit.Normal * 3)}
		end
		return nil
	end
	local function isHall(name: string): boolean
		return string.sub(name, 1, 4) == "HALL"
	end
	for i, d in doorBoxes do
		for _, side in {1, -1} do
			local lookFlat = Vector3.new(d.look.X, 0, d.look.Z)
			local probe = if lookFlat.Magnitude < 0.5 then "?" else areaAt(d.pos + lookFlat.Unit * side * 3)
			local roomSide = not isHall(probe) and probe ~= "?"
			-- указатель выхода над дверью: со стороны комнаты всегда, со стороны коридора иногда
			if roomSide or rng:NextNumber() < 0.35 then
				local s = doorSite(d, side, 0, 10.3)
				if s then
					tryPlace("ExitSign", s, true)
				end
			end
			if roomSide then
				local s = doorSite(d, side, if rng:NextNumber() < 0.5 then 4.3 else -4.3, 4.6)
				if s then
					tryPlace("LightSwitch", s, true)
				end
				if probe == "WEST" or probe == "CENTER" or probe == "EAST" or probe == "NE" then -- схема эвакуации у двери комнаты (по просьбе пользователя)
					for _, lat in {8.4, -8.4, 10.4, -10.4} do
						local plan = doorSite(d, side, lat, 5.7)
						if plan and tryPlace("EvacPlan", plan, true) then
							break
						end
					end
				end
			elseif i % 2 == 0 then
				local s = doorSite(d, side, 6.2, 4.9)
				if s then
					tryPlace("Keypad", s, true)
				end
			else
				local s = doorSite(d, side, -6.2, 5.0)
				if s then
					tryPlace("Sanitizer", s, true)
				end
			end
		end
		task.wait()
	end

	----------------------------------------------------------------- планы комнат
	local HALLS = {"HALL_W", "HALL_N", "HALL_E", "HALL_S"}
	-- План после правок пользователя (15.11): в комнате один кондиционер (в больших залах два), камеры по одной в углу, вентрешётка под потолком,
	-- без термостатов, аварийных ламп, круглых вентиляторов, мышиных нор, электрощитов; схемы эвакуации стоят только у дверей (см. ниже).
	local PLAN: {{areas: {string}, items: {{string | number}}}} = {
		{areas = {"WEST"}, items = {{"EvacPlan", 1}, {"AcSplit", 1}, {"CamBullet", 1}, {"ShelfBooks", 1}, {"VentGrille", 1}, {"CableLoops", 1}}},
		{areas = {"CENTER"}, items = {{"EvacPlan", 1}, {"AcSplitWide", 1}, {"AcSplit", 1}, {"CamDome", 1}, {"FireAlarm", 1}, {"ShelfDecor", 1}, {"ShelfDecorB", 1}, {"VentGrille", 1}}},
		{areas = {"EAST"}, items = {{"EvacPlan", 1}, {"AcSplit", 1}, {"AcSplitOld", 1}, {"CamBullet", 1}, {"ShelfDecorC", 1}, {"ShelfBooks", 1}, {"VentDuct", 1}, {"PipeRun", 1}, {"CableLoops", 1}}},
		{areas = {"NW"}, items = {{"PipeRun", 1}, {"PipeRiser", 2}, {"CamBullet", 1}, {"VentDuct", 1}, {"CableLoops", 1}}},
		{areas = {"NE"}, items = {{"EvacPlan", 1}, {"AcSplitWide", 1}, {"AcSplit", 1}, {"ShelfBooks", 1}, {"ShelfDecorB", 1}, {"VentGrille", 1}, {"FireAlarm", 1}, {"CamDome", 1}}},
		{areas = {"START"}, items = {{"AcSplit", 1}, {"ShelfDecor", 1}, {"FireAlarm", 1}, {"FireHorn", 1}, {"CamBullet", 1}}},
		{areas = HALLS, items = {{"FireAlarm", 1}, {"FireHorn", 2}, {"CamDome", 2}, {"PipeRiser", 1}, {"PipeRun", 1}, {"CableLoops", 1}, {"VentGrille", 1}}},
	}
	for _, room in PLAN do
		for _, entry in room.items do
			local key, want = entry[1] :: string, entry[2] :: number
			if not REMOVED[key] and not (#room.areas == 1 and NO_DECOR_AREAS[room.areas[1]]) then
				for _ = 1, want do
					placeIn(room.areas, key)
				end
			end
		end
		task.wait()
	end

	-- сушилки для рук в туалетах: у восточной стены рядом с раковиной, без подписи (старая убрана модулем OfficeUserCleanup)
	for _, wc in {{"MEN", 1031.0}, {"WOMEN", 1055.0}} do
		local name, wallX = wc[1] :: string, wc[2] :: number
		local hit = workspace:Raycast(Vector3.new(wallX - 1.5, 4.5, 71.4), Vector3.new(3, 0, 0), wallParams)
		if hit and math.abs(hit.Normal.X) > 0.9 then
			local n = hit.Normal
			tryPlace("HandDryer", {pos = hit.Position, n = n, t = Vector3.new(-n.Z, 0, n.X), color = (hit.Instance :: BasePart).Color, area = name}, true)
		end
	end
	if not office:IsDescendantOf(game) then
		folder:Destroy()
		return
	end
	folder.Parent = office
	office:SetAttribute("WallDecorItems", total)
	if game:GetService("RunService"):IsStudio() then -- счётчики и причины отказов нужны только при разработке
		for key, n in counts do
			folder:SetAttribute("N_" .. key, n)
		end
		for k, n in rejects do
			folder:SetAttribute("R_" .. k, n)
		end
	end
end

-- OfficeUserCleanup ждёт этот атрибут (а не фиксированное время), чтобы переставлять мебель и сдвигать извещатель уже после расстановки декора
local function attachWallDecor(office: Instance)
	local ok, err = pcall(attachWallDecorInner, office)
	if not ok then
		warn("KONTUR wall decor failed: " .. tostring(err))
	end
	office:SetAttribute("KonturWallDecorDone", true)
end

return attachWallDecor
