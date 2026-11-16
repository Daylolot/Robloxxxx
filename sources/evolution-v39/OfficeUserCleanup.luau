--!strict
-- v43 правки по замечаниям пользователя (15.11): убирает и переставляет готовые предметы карты по имени. Запускается после остальных модулей.
--   Стартовая комната: убраны интерком диспетчера, четырёхэкранный пост наблюдения (остаётся один монитор), висящие в воздухе неоновые планки над
--   стойками и зелёная/красная подсветка (PointLight), цветок перенесён в угол.
--   Туалеты: убраны лишняя раковина и вешалка у западной стены (MEN) / у восточной (WOMEN), сушилка для рук (ставится новой моделью из Blender).
--   Архив (NW): убраны тележка уборщика, подставки-ступеньки, кабельный лоток на стене, центральный стол с картотекой; вместо стола два стеллажа.
--   Переговорная (NE): ковров нет.
local function attachUserCleanup(office: Instance)
	-- ждём конца расстановки настенного декора (атрибут ставит OfficeWallDecor), но не дольше 150 с; минимум 30 с на остальные модули
	task.wait(30)
	local waited = 0
	while not office:GetAttribute("KonturWallDecorDone") and waited < 120 do
		task.wait(1)
		waited += 1
	end
	if office:GetAttribute("KonturCleanupDone") then
		return
	end
	office:SetAttribute("KonturCleanupDone", true)
	local rooms = office:WaitForChild("Rooms", 30)
	if not rooms then
		warn("KONTUR user cleanup: нет Rooms")
		return
	end
	local function kill(room: Instance?, pattern: string, filter: ((Model) -> boolean)?)
		if not room then
			return 0
		end
		local n = 0
		for _, m in room:GetChildren() do
			if string.find(m.Name, pattern) and (not filter or (m:IsA("Model") and filter(m))) then
				m:Destroy()
				n += 1
			end
		end
		return n
	end
	local function pos(m: Model): Vector3
		return m:GetPivot().Position
	end

	-- ===== зеркала в туалетах: плоский серый лист заменён моделью из Blender (рама, стекло с отражением комнаты, зажимы)
	local MIRROR_ID: number? = nil
	-- @@MIRROR_ASSET@@
	if MIRROR_ID then
		local container: Instance? = nil
		for _ = 1, 4 do
			local ok, result = pcall(function()
				return game:GetService("InsertService"):LoadAsset(MIRROR_ID :: number)
			end)
			if ok and result then
				container = result
				break
			end
			task.wait(3)
		end
		if container then
			for _, roomName in {"MEN", "WOMEN"} do
				local room = rooms:FindFirstChild(roomName)
				if room then
					for _, m in room:GetChildren() do
						local panelInst = m:FindFirstChild("MirrorPanel")
						if m:IsA("Model") and string.find(m.Name, "^V09_%d+_Mirror$") and panelInst and panelInst:IsA("BasePart") and not m:GetAttribute("KonturWcFrame") then
							-- модель и MirrorPanel остаются (по ним клиент рисует живое отражение и сервер включает аномалию Mirror): меняется только рама
							local panel = panelInst :: BasePart
							local c = (m:GetBoundingBox()).Position
							-- нормаль стены: к центру комнаты по доминирующей оси
							local roomCentre = Vector3.new(if roomName == "MEN" then 1020 else 1044, c.Y, 78)
							local d = roomCentre - c
							local normal = if math.abs(d.X) > math.abs(d.Z) then Vector3.new(math.sign(d.X), 0, 0) else Vector3.new(0, 0, math.sign(d.Z))
							local wallPoint = c - normal * (panel.Size.Z / 2 + 0.02)
							local frame = Instance.new("Model")
							for _, mesh in (container :: Instance):GetDescendants() do
								if mesh:IsA("MeshPart") then
									local suffix, hex = string.match(mesh.Name, "^WcMirror_(.+)_(%x%x%x%x%x%x)$")
									-- стекло и отражение рисует MirrorPanel, поэтому нарисованные слои (plastic, stain) не берутся: остаются рама, зажимы, винты
									if suffix == "metal" then
										local mc = mesh:Clone()
										if hex then
											mc.Color = Color3.fromHex(hex)
										end
										mc.Anchored = true
										mc.CanCollide = false
										mc.CanTouch = false
										mc.CanQuery = false
										mc.Material = Enum.Material.Metal
										mc.Parent = frame
									end
								end
							end
							if #frame:GetChildren() > 0 then
								for _, old in m:GetChildren() do
									if old:IsA("MeshPart") and string.find(old.Name, "^MirrorFrame") then
										old:Destroy()
									end
								end
								frame.Parent = m
								frame:PivotTo(CFrame.lookAt(wallPoint, wallPoint + normal))
								for _, mp in frame:GetChildren() do
									mp.Parent = m
								end
								frame:Destroy()
								-- стекло: серебристый градиент с бликами и отражённым окном (рисуется SurfaceGui на лицевой грани MirrorPanel; живое отражение,
								-- когда клиент его монтирует, ложится сверху)
								panel.Material = Enum.Material.SmoothPlastic
								panel.Color = Color3.fromRGB(170, 192, 200)
								panel.Reflectance = 0
								local gui = Instance.new("SurfaceGui")
								gui.Name = "KonturMirrorShine"
								gui.Face = if panel.CFrame.LookVector:Dot(normal) > 0 then Enum.NormalId.Front else Enum.NormalId.Back
								gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
								gui.PixelsPerStud = 40
								gui.LightInfluence = 0.55
								gui.Parent = panel
								local base = Instance.new("Frame")
								base.Size = UDim2.fromScale(1, 1)
								base.BorderSizePixel = 0
								base.ClipsDescendants = true
								base.BackgroundColor3 = Color3.new(1, 1, 1)
								base.Parent = gui
								local grad = Instance.new("UIGradient")
								grad.Rotation = 90
								grad.Color = ColorSequence.new({
									ColorSequenceKeypoint.new(0, Color3.fromRGB(176, 194, 202)),
									ColorSequenceKeypoint.new(0.45, Color3.fromRGB(214, 228, 233)),
									ColorSequenceKeypoint.new(0.78, Color3.fromRGB(150, 176, 186)),
									ColorSequenceKeypoint.new(1, Color3.fromRGB(104, 138, 150)),
								})
								grad.Parent = base
								local function glint(x: number, y: number, w: number, h: number, rot: number, color: Color3, alpha: number)
									local f = Instance.new("Frame")
									f.AnchorPoint = Vector2.new(0.5, 0.5)
									f.Position = UDim2.fromScale(x, y)
									f.Size = UDim2.fromScale(w, h)
									f.Rotation = rot
									f.BorderSizePixel = 0
									f.BackgroundColor3 = color
									f.BackgroundTransparency = alpha
									f.Parent = base
								end
								glint(0.66, 0.3, 0.34, 0.3, 0, Color3.fromRGB(232, 242, 246), 0.12)          -- отражённое окно
								glint(0.66, 0.3, 0.012, 0.3, 0, Color3.fromRGB(150, 172, 180), 0.2)
								glint(0.66, 0.3, 0.34, 0.01, 0, Color3.fromRGB(150, 172, 180), 0.2)
								glint(0.3, 0.5, 0.07, 1.4, 22, Color3.fromRGB(236, 244, 247), 0.55)           -- диагональные блики
								glint(0.43, 0.5, 0.025, 1.4, 22, Color3.fromRGB(236, 244, 247), 0.6)
								glint(0.82, 0.5, 0.04, 1.4, 22, Color3.fromRGB(236, 244, 247), 0.65)
								m:SetAttribute("KonturWcFrame", true)
							else
								frame:Destroy()
								warn("KONTUR WcMirror: в ассете нет металлических деталей рамы")
							end
						end
					end
				end
			end
			(container :: Instance):Destroy()
		end
	end

	-- бутыль кулера: стекло на фоне ночного окна выглядело чёрным, делаем голубой полупрозрачный пластик
	for _, d in office:GetDescendants() do
		if d:IsA("BasePart") and string.find(d.Name, "^WaterCooler_glass_blue_") then
			d.Material = Enum.Material.SmoothPlastic
			d.Transparency = 0.22
		end
	end
	-- электрощиток в коридоре убран (часть 2, пункты 11 и 22)
	local corridorF = rooms.Parent and rooms.Parent:FindFirstChild("Corridor")
	if corridorF then
		for _, d in corridorF:GetChildren() do
			if d:IsA("Model") and string.find(d.Name, "ElectricalPanel$") then
				d:Destroy()
			end
		end
	end
	-- «ковры», нарисованные плитками пола: бордовый в NE и бирюзовый в EAST перекрашены в цвет остального ковролина комнаты
	local floorsF = office:FindFirstChild("Floors")
	if floorsF then
		local ne = floorsF:FindFirstChild("NE")
		local east = floorsF:FindFirstChild("EAST")
		if ne then
			for _, t in ne:GetChildren() do
				if t:IsA("BasePart") and t.Material == Enum.Material.Carpet and t.Color.R > 0.35 then
					t.Color = Color3.new(0.27, 0.29, 0.34)
				end
			end
		end
		if east then
			for _, t in east:GetChildren() do
				if t:IsA("BasePart") and t.Material == Enum.Material.Carpet and t.Color.G > t.Color.R + 0.1 then
					t.Color = Color3.new(0.29, 0.31, 0.37)
				end
			end
		end
	end
	-- ковры стиля (KonturV36: Rug, RugBorder, RugBorder2, RugInlay: по одному на комнату) убраны полностью
	local styleF = office:FindFirstChild("KonturV36")
	if styleF then
		for _, d in styleF:GetChildren() do
			if string.find(d.Name, "^Rug") then
				d:Destroy()
			end
		end
	end
	-- все оставшиеся ковры убраны (пользователь неоднократно просил: стартовая, переговорная, коридоры, центр комнаты)
	for _, d in office:GetDescendants() do
		if d:IsA("Model") and (string.find(d.Name, "Rug$") or string.find(d.Name, "Runner$") or string.find(d.Name, "Carpet$")) then
			d:Destroy()
		end
	end
	-- доска объявлений интерьера (TeamNoticeboard) убрана; V09_NoticeBoard остаются: на них завязаны аномалии NoticeBoardCrooked и BoardMeetingTime
	for _, d in rooms:GetDescendants() do
		if d:IsA("Model") and d.Name == "TeamNoticeboard" then
			d:Destroy()
		end
	end

	-- ===== стартовая комната
	local start = rooms:FindFirstChild("StartRoom")
	kill(start, "DispatchIntercom$")
	if start then
		for _, d in start:GetDescendants() do
			if d:IsA("Model") and string.find(d.Name, "ReceptionPhoto$") then
				d:Destroy()
			end
		end
	end
	-- один монитор вместо поста из четырёх: клон готового монитора из других комнат ставится на то же место стола
	local function frontDir(m: Model): Vector3
		local c, _ = m:GetBoundingBox()
		local sum = Vector3.zero
		local n = 0
		for _, p in m:GetDescendants() do
			if p:IsA("BasePart") and p.Name == "LCD" then
				sum += Vector3.new(p.Position.X - c.Position.X, 0, p.Position.Z - c.Position.Z)
				n += 1
			end
		end
		return if n > 0 and sum.Magnitude > 0.05 then sum.Unit else Vector3.new(0, 0, -1)
	end
	-- второй стол (ресепшен) убран по просьбе пользователя вместе с лампой и бумагами на нём; табличка на стене остаётся
	if start then
		for _, m in start:GetDescendants() do
			if m:IsA("Model") and (string.find(m.Name, "ReceptionDesk$") or string.find(m.Name, "ReceptionLamp$") or string.find(m.Name, "LooseSheets$")) then
				m:Destroy()
			elseif m:IsA("Model") and string.find(m.Name, "ReceptionOfficeSign$") and not m:GetAttribute("KonturShifted") then
				-- табличка без стола: по центру под часами (часы на x=988)
				m:SetAttribute("KonturShifted", true)
				m:PivotTo(m:GetPivot() + Vector3.new(5, 0, 0))
			end
		end
	end
	local plantsF0 = office:FindFirstChild("KonturPlants")
	local stack0 = plantsF0 and plantsF0:FindFirstChild("DecorBookStack_13")
	if stack0 then
		stack0:Destroy()
	end
	-- единственный монитор стоит на оставшемся рабочем столе (с клавиатурой и системным блоком), экраном к стулу (на +X)
	if start then
		for _, m in start:GetChildren() do
			if m:IsA("Model") and string.find(m.Name, "SecurityMonitors$") then
				m:Destroy()
			end
		end
		local workDesk: Model? = nil
		local keyboard: Model? = nil
		for _, m in start:GetChildren() do
			if m:IsA("Model") and string.find(m.Name, "StraightDesk$") then
				workDesk = m
			elseif m:IsA("Model") and m.Name == "Keyboard" then
				keyboard = m
			end
		end
		local template: Model? = nil
		for _, room in rooms:GetChildren() do
			if room.Name ~= "StartRoom" and not template then
				for _, cand in room:GetChildren() do
					if cand:IsA("Model") and string.find(cand.Name, "Monitor$") and not string.find(cand.Name, "Monitors$") and cand:FindFirstChild("LCD") then
						template = cand
						break
					end
				end
			end
		end
		if template and workDesk and not start:FindFirstChild("KonturStartMonitor") then
			local dc, dsz = (workDesk :: Model):GetBoundingBox()
			local deskTop = dc.Position.Y + dsz.Y / 2
			local kb = if keyboard then (keyboard :: Model):GetPivot().Position else dc.Position
			-- монитор у стены за клавиатурой: стена с розетками на 976, клавиатура на 978,2, значит монитор на ~977,3
			local target = Vector3.new(kb.X - 0.95, deskTop, kb.Z)
			local copy = (template :: Model):Clone()
			copy.Name = "KonturStartMonitor"
			for _, d in copy:GetDescendants() do
				if d:IsA("Script") or d:IsA("LocalScript") then
					d:Destroy()
				end
			end
			copy.Parent = start
			local f = frontDir(copy)
			local yaw = math.pi / 2 - math.atan2(f.X, f.Z)
			local p0 = copy:GetPivot()
			copy:PivotTo(CFrame.new(p0.Position) * CFrame.Angles(0, yaw, 0) * p0.Rotation)
			local bc, bsz = copy:GetBoundingBox()
			copy:PivotTo(copy:GetPivot() + Vector3.new(target.X - bc.Position.X, deskTop - (bc.Position.Y - bsz.Y / 2), target.Z - bc.Position.Z))
			for _, d in copy:GetDescendants() do
				if d:IsA("BasePart") then
					d.Anchored = true
				end
			end
		end
	end
	-- извещатель не должен перекрывать табличку над бывшим столом (табличка на x 986..990, низ рамки около y 5,4)
	do
		local wdA = office:FindFirstChild("KonturWallDecor")
		if wdA then
			for _, m in wdA:GetChildren() do
				if m:IsA("Model") and m.Name == "WD_FireAlarm" and m:GetAttribute("Area") == "START" then
					local pp = m:GetPivot().Position
					if pp.Z > 74 and pp.X > 984.5 and pp.X < 991.5 then
						m:PivotTo(m:GetPivot() + Vector3.new(995.5 - pp.X, 0, 0))
					end
				end
			end
		end
	end

	-- ===== камера стартовой: по просьбе пользователя перенесена в угол комнаты (к шву стен у потолка) и повёрнута к центру комнаты
	local CAMC_ID: number? = nil
	-- @@CAMC_ASSET@@
	local wd = office:FindFirstChild("KonturWallDecor")
	if wd and CAMC_ID then
		local oldCam: Model? = nil
		for _, m in wd:GetChildren() do
			if m:IsA("Model") and m.Name == "WD_CamBullet" and m:GetAttribute("Area") == "START" then
				oldCam = m
			end
		end
		-- декор ставится случайно, поэтому угол задан явно: северо-восточный (шов восточной стены x=1000 и северной z=56), камера на восточной стене
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Exclude
		params.FilterDescendantsInstances = {wd}
		local probe = Vector3.new(990, 10.2, 62)
		local hitE = workspace:Raycast(probe, Vector3.new(30, 0, 0), params)
		local hitN = workspace:Raycast(probe, Vector3.new(0, 0, -30), params)
		local container: Instance? = nil
		if oldCam or hitE then
			for _ = 1, 4 do
				local ok, result = pcall(function()
					return game:GetService("InsertService"):LoadAsset(CAMC_ID :: number)
				end)
				if ok and result then
					container = result
					break
				end
				task.wait(3)
			end
		end
		if hitE and hitN and container then
			local normal = Vector3.new(-1, 0, 0)
			local pos = Vector3.new(hitE.Position.X, 10.2, hitN.Position.Z + 0.58)
			local cam = Instance.new("Model")
			cam.Name = "WD_CamCorner"
			local frame = CFrame.lookAt(pos + normal * 0.02, pos + normal * 0.02 + normal)
			for _, mesh in (container :: Instance):GetDescendants() do
				if mesh:IsA("MeshPart") then
					local suffix, hex = string.match(mesh.Name, "^CamCorner_(.+)_(%x%x%x%x%x%x)$")
					local mc = mesh:Clone()
					if hex then
						mc.Color = Color3.fromHex(hex)
					end
					mc.Anchored = true
					mc.CanCollide = false
					mc.CanTouch = false
					mc.CanQuery = false
					mc.Material = if suffix == "metal" then Enum.Material.Metal elseif suffix == "glow" then Enum.Material.Neon else Enum.Material.SmoothPlastic
					mc.CFrame = frame * mesh.CFrame
					mc.Parent = cam
				end
			end
			if #cam:GetChildren() > 0 then
				cam.Parent = wd
				if oldCam then
					(oldCam :: Model):Destroy()
				end
			else
				cam:Destroy()
			end
		end
		if container then
			(container :: Instance):Destroy()
		end
	end

	-- принтер: щель крышки перечёркивала голубой дисплей, бумага тонула в лотке
	for _, d in rooms:GetDescendants() do
		if d:IsA("Model") and d.Name == "Printer" then
			for _, p in d:GetDescendants() do
				if p:IsA("BasePart") then
					if string.find(p.Name, "^Printer_display_69e0ee") or p.Name == "Display" then
						-- чёрная щель крышки торчала сквозь экран: экран выдвинут вперёд на 6 сотых
						p.CFrame = p.CFrame + d:GetPivot().LookVector * 0.07
					elseif string.find(p.Name, "^Printer_paper_f2efe4") then
						p.CFrame = p.CFrame + Vector3.new(0, 0.04, 0)
					end
				end
			end
		end
	end
	-- личные шкафчики не открываются (по просьбе пользователя)
	for _, d in office:GetDescendants() do
		if d:IsA("ProximityPrompt") then
			local m: Instance? = d.Parent
			while m and m ~= office and not string.find(m.Name, "PersonalLockers$") do
				m = m.Parent
			end
			if m and m ~= office then
				d.Enabled = false
				d:Destroy()
			end
		end
	end
	local marks = start and start:FindFirstChild("KonturStartMarks")
	if marks then
		for _, d in marks:GetDescendants() do
			if d:IsA("Light") then
				d:Destroy()
			elseif d:IsA("BasePart") and d.Position.Y > 3 then
				d:Destroy() -- неоновые планки в воздухе перед стеной
			end
		end
	end
	local plants = office:FindFirstChild("KonturPlants")
	local flower = plants and plants:FindFirstChild("Plant_8")
	if flower and flower:IsA("Model") then
		local p = pos(flower)
		if p.X < 1000 and p.Z > 54 then
			flower:PivotTo(CFrame.new(977.9, p.Y, 57.7) * flower:GetPivot().Rotation)
		end
	end

	-- ===== туалеты
	for _, wc in {"MEN", "WOMEN"} do
		local room = rooms:FindFirstChild(wc)
		kill(room, "WallBasin$")
		kill(room, "HookRail$", function(m)
			local z = pos(m).Z
			return z > 74 and z < 80 -- вешалки кабинок на z≈84 остаются
		end)
		kill(room, "HandDryer$")
	end

	-- ===== кабинки туалетов без зазоров: общая перегородка между двумя кабинками, боковые стенки и задняя панель доходят до стены
	local structure = office:FindFirstChild("Structure")
	local wallParts: {Instance} = {}
	if structure then
		for _, d in structure:GetDescendants() do
			if d:IsA("BasePart") and string.match(d.Name, "^WallCore%d+_%d+") then
				table.insert(wallParts, d)
			end
		end
	end
	local wallParams = RaycastParams.new()
	wallParams.FilterType = Enum.RaycastFilterType.Include
	wallParams.FilterDescendantsInstances = wallParts
	for _, wc in {"MEN", "WOMEN"} do
		local room = rooms:FindFirstChild(wc)
		if room then
			local cubicles: {Model} = {}
			for _, m in room:GetChildren() do
				if m:IsA("Model") and string.find(m.Name, "Cubicle$") then
					table.insert(cubicles, m)
				end
			end
			table.sort(cubicles, function(a: Model, b: Model)
				return a:GetPivot().Position.X < b:GetPivot().Position.X
			end)
			local function part(m: Model, name: string, pick: ((BasePart) -> boolean)?): {BasePart}
				local out: {BasePart} = {}
				for _, p in m:GetChildren() do
					if p:IsA("BasePart") and p.Name == name and (not pick or pick(p)) then
						table.insert(out, p)
					end
				end
				return out
			end
			for i, m in cubicles do
				local pivot = m:GetPivot().Position
				local hit = workspace:Raycast(Vector3.new(pivot.X, 5, pivot.Z + 2), Vector3.new(0, 0, 8), wallParams)
				local wallZ = if hit then hit.Position.Z else pivot.Z + 3.1
				local sides = part(m, "CubicleSide")
				for _, side in sides do
					local frontZ = side.Position.Z - side.Size.Z / 2
					side.Size = Vector3.new(side.Size.X, side.Size.Y, wallZ - frontZ)
					side.Position = Vector3.new(side.Position.X, side.Position.Y, (frontZ + wallZ) / 2)
				end
				for _, back in part(m, "CubicleBack") do
					back.Position = Vector3.new(back.Position.X, back.Position.Y, wallZ - back.Size.Z / 2)
				end
				-- общая перегородка со следующей кабинкой
				local nextM = cubicles[i + 1]
				if nextM then
					local mine = part(m, "CubicleSide")
					local theirs = part(nextM, "CubicleSide")
					table.sort(mine, function(a: BasePart, b: BasePart) return a.Position.X < b.Position.X end)
					table.sort(theirs, function(a: BasePart, b: BasePart) return a.Position.X < b.Position.X end)
					if #mine >= 1 and #theirs == 2 then
						local sharedX = mine[#mine].Position.X
						local shift = theirs[1].Position.X - sharedX -- на сколько ближе придвигаем соседнюю кабинку
						theirs[1]:Destroy()
						for _, name in {"CubicleBack", "CubicleTopRail"} do
							for _, p in part(nextM, name) do
								p.Size = Vector3.new(p.Size.X + shift, p.Size.Y, p.Size.Z)
								p.Position = Vector3.new(p.Position.X - shift / 2, p.Position.Y, p.Position.Z)
							end
						end
						for _, name in {"CubicleFrontInfill", "CubicleJamb"} do
							local list = part(nextM, name)
							table.sort(list, function(a: BasePart, b: BasePart) return a.Position.X < b.Position.X end)
							if list[1] then
								list[1].Position = Vector3.new(list[1].Position.X - shift, list[1].Position.Y, list[1].Position.Z)
							end
						end
					end
				end
			end
		end
	end

	-- ===== архив
	local nw = rooms:FindFirstChild("NW")
	kill(nw, "CleaningTrolley$")
	kill(nw, "StepStool$")
	kill(nw, "CableTray$")
	local tablePos: Vector3? = nil
	if nw then
		for _, m in nw:GetChildren() do
			if string.find(m.Name, "ArchiveTable$") and m:IsA("Model") then
				tablePos = pos(m)
			end
		end
		kill(nw, "ArchiveTable$")
		kill(nw, "CardIndex$")
		kill(nw, "ArchiveBoxes$")
		local template: Model? = nil
		for _, m in nw:GetChildren() do
			if string.find(m.Name, "LoadedShelf$") and m:IsA("Model") and not template then
				template = m
			end
		end
		if template and tablePos then
			local look = (template :: Model):GetPivot().Rotation
			local y = (template :: Model):GetPivot().Position.Y
			for i, x in {-3.2, 3.2} do
				local copy = (template :: Model):Clone()
				copy.Name = "KonturLoadedShelf" .. i
				copy:PivotTo(CFrame.new(tablePos.X + x, y, tablePos.Z) * look)
				copy.Parent = nw
			end
		end
	end

	-- ===== пожарные шкафы коридора: выше (по просьбе пользователя), чтобы низ шкафа был на уровне пояса
	for _, d in office:GetDescendants() do
		if d:IsA("Model") and (string.find(d.Name, "FireHoseCabinet$") or string.find(d.Name, "ExtinguisherCabinet$")) and not d:GetAttribute("KonturRaised") then
			d:SetAttribute("KonturRaised", true)
			d:PivotTo(d:GetPivot() + Vector3.new(0, 1.3, 0))
			-- шкаф со шлангом стоял в нише стены (CabinetRecess) на старой высоте: после подъёма верх шкафа врезался в штукатурку, она
			-- просвечивала сквозь стекло. Шкаф выносится вперёд до касания стены на уровне его верха (навесной вместо встроенного).
			if string.find(d.Name, "FireHoseCabinet$") then
				local piv = d:GetPivot()
				local look = piv.LookVector
				local cb, cs = d:GetBoundingBox()
				local backmost = math.huge
				for _, p in d:GetDescendants() do
					if p:IsA("BasePart") and p.Transparency < 1 then
						local dd = (p.Position - piv.Position):Dot(look)
						local h = 0.5 * (math.abs(p.CFrame.LookVector:Dot(look)) * p.Size.Z + math.abs(p.CFrame.RightVector:Dot(look)) * p.Size.X + math.abs(p.CFrame.UpVector:Dot(look)) * p.Size.Y)
						backmost = math.min(backmost, dd - h)
					end
				end
				local params = RaycastParams.new()
				params.FilterType = Enum.RaycastFilterType.Exclude
				params.FilterDescendantsInstances = {d}
				local origin = Vector3.new(piv.X, cb.Position.Y + cs.Y / 2 + 1.2, piv.Z) + look * 2.5
				-- пустая ниша под поднятым шкафом закрывается заподлицо панелью цвета стены (нижняя часть ниши видна как белая дыра)
				local nicheParts: {BasePart} = {}
				for _, np in office:GetDescendants() do
					if np:IsA("BasePart") and string.find(np.Name, "^CabinetRecess") and (Vector3.new(np.Position.X, 0, np.Position.Z) - Vector3.new(piv.X, 0, piv.Z)).Magnitude < 3 then
						table.insert(nicheParts, np)
					end
				end
				if #nicheParts > 0 then
					local lo, hi = Vector3.new(math.huge, math.huge, math.huge), Vector3.new(-math.huge, -math.huge, -math.huge)
					local wallPaint: BasePart? = nil
					for _, np in nicheParts do
						lo = Vector3.new(math.min(lo.X, np.Position.X - np.Size.X / 2), math.min(lo.Y, np.Position.Y - np.Size.Y / 2), math.min(lo.Z, np.Position.Z - np.Size.Z / 2))
						hi = Vector3.new(math.max(hi.X, np.Position.X + np.Size.X / 2), math.max(hi.Y, np.Position.Y + np.Size.Y / 2), math.max(hi.Z, np.Position.Z + np.Size.Z / 2))
						np:Destroy()
					end
					for _, wp in workspace:GetPartBoundsInBox(CFrame.new(piv.X, 1.5, piv.Z), Vector3.new(6, 3, 3)) do
						if string.find(wp.Name, "^WallCore%d_%d+PaintLower") or string.find(wp.Name, "^WallCore0_") then
							wallPaint = wp
						end
					end
					local filler = Instance.new("Part")
					filler.Name = "KonturNicheFiller"
					filler.Anchored = true
					filler.CanCollide = true
					filler.Material = Enum.Material.SmoothPlastic
					filler.Color = if wallPaint then (wallPaint :: BasePart).Color else Color3.fromRGB(34, 87, 97)
					-- лицевая плоскость стены: отступ 0,08 от переднего края ниши внутрь, толщина 0,4 (как у стены)
					if math.abs(look.Z) > 0.5 then
						local front = if look.Z < 0 then lo.Z + 0.08 else hi.Z - 0.08
						local cz = front - look.Z * 0.2
						filler.Size = Vector3.new(hi.X - lo.X, 3.64 - 0.5, 0.4)
						filler.CFrame = CFrame.new((hi.X + lo.X) / 2, (3.64 + 0.5) / 2, cz)
					else
						local front = if look.X < 0 then lo.X + 0.08 else hi.X - 0.08
						local cx = front - look.X * 0.2
						filler.Size = Vector3.new(0.4, 3.64 - 0.5, hi.Z - lo.Z)
						filler.CFrame = CFrame.new(cx, (3.64 + 0.5) / 2, (hi.Z + lo.Z) / 2)
					end
					filler.Parent = d.Parent
					-- цоколь (плинтус) перед панелью: такой же, как слева и справа от ниши
					local skirt = Instance.new("Part")
					skirt.Name = "KonturNicheSkirting"
					skirt.Anchored = true
					skirt.Material = Enum.Material.Wood
					skirt.Color = Color3.fromRGB(46, 69, 74)
					if math.abs(look.Z) > 0.5 then
						skirt.Size = Vector3.new(hi.X - lo.X, 0.35, 0.07)
						skirt.CFrame = CFrame.new((hi.X + lo.X) / 2, 0.28, if look.Z < 0 then lo.Z + 0.035 else hi.Z - 0.035)
					else
						skirt.Size = Vector3.new(0.07, 0.35, hi.Z - lo.Z)
						skirt.CFrame = CFrame.new(if look.X < 0 then lo.X + 0.035 else hi.X - 0.035, 0.28, (hi.Z + lo.Z) / 2)
					end
					skirt.Parent = d.Parent
				end
				local hit = workspace:Raycast(origin, -look * 5, params)
				if hit then
					local surface = (hit.Position - piv.Position):Dot(look)
					if surface > backmost + 0.03 then
						d:PivotTo(d:GetPivot() + look * (surface - backmost + 0.02))
					end
				end
			end
		end
	end

	-- ===== архив: аккуратные ряды книг на шкафах заменены небрежно лежащими документами (модель DocPile из Blender)
	local DOC_ID: number? = nil
	-- @@DOC_ASSET@@
	local plantsFolder = office:FindFirstChild("KonturPlants")
	if plantsFolder and DOC_ID then
		local container: Instance? = nil
		for attempt = 1, 4 do
			local ok, result = pcall(function()
				return game:GetService("InsertService"):LoadAsset(DOC_ID :: number)
			end)
			if ok and result then
				container = result
				break
			end
			task.wait(3)
		end
		for _, row in plantsFolder:GetChildren() do
			if container and string.find(row.Name, "^DecorBookRow") and row:IsA("Model") then
				local cf = row:GetPivot()
				if cf.Z < 0 and cf.Y > 4 then
					local copy = Instance.new("Model")
					copy.Name = "KonturDocPile"
					for _, mesh in (container :: Instance):GetDescendants() do
						if mesh:IsA("MeshPart") then
							local c = mesh:Clone()
							local suffix, hex = string.match(mesh.Name, "^DocPile_(.+)_(%x%x%x%x%x%x)$")
							if hex then
								c.Color = Color3.fromHex(hex)
							end
							c.Anchored = true
							c.CanCollide = false
							c.CanQuery = false
							c.CanTouch = false
							c.Material = Enum.Material.SmoothPlastic
							c.Parent = copy
						end
					end
					copy:PivotTo(CFrame.new(cf.X, cf.Y + 0.2, cf.Z) * CFrame.Angles(0, math.rad(10), 0))
					copy.Parent = plantsFolder
					row:Destroy()
				end
			end
		end
		if container then
			(container :: Instance):Destroy()
		end
	end

	-- ===== торшеры: свет в углах был слишком ярким (выжигал стену и плакаты), приглушаем вдвое и сужаем
	local decorFolder = office:FindFirstChild("KonturDecor")
	if decorFolder then
		for _, lamp in decorFolder:GetChildren() do
			if string.find(lamp.Name, "FloorLamp") then
				for _, l in lamp:GetDescendants() do
					if l:IsA("Light") then
						l.Brightness *= 0.45
						if l:IsA("PointLight") then
							l.Range = math.min(l.Range, 14)
						end
					end
				end
			end
		end
	end

	-- ===== коридорные растения: вместо кустов из шаров ставится фикус из Blender (метки PlantSpot из OfficeCorridorDressing)
	local FIG_ID: number? = nil
	-- @@FIG_ASSET@@
	local corridor = office:FindFirstChild("KonturCorridor")
	if corridor and FIG_ID then
		local container: Instance? = nil
		for _ = 1, 4 do
			local ok, result = pcall(function()
				return game:GetService("InsertService"):LoadAsset(FIG_ID :: number)
			end)
			if ok and result then
				container = result
				break
			end
			task.wait(3)
		end
		if container then
			for _, spot in corridor:GetChildren() do
				if spot:IsA("BasePart") and spot.Name == "PlantSpot" then
					local model = Instance.new("Model")
					model.Name = "KonturCorridorPlant"
					for _, mesh in (container :: Instance):GetDescendants() do
						if mesh:IsA("MeshPart") then
							local c = mesh:Clone()
							local _, hex = string.match(mesh.Name, "^PlantFig_(.+)_(%x%x%x%x%x%x)$")
							if hex then
								c.Color = Color3.fromHex(hex)
							end
							c.Anchored = true
							c.CanCollide = false
							c.CanQuery = false
							c.CanTouch = false
							c.Material = Enum.Material.SmoothPlastic
							c.DoubleSided = true
							c.Parent = model
						end
					end
					if #model:GetChildren() == 0 then
						model:Destroy()
						continue
					end
					model:ScaleTo(0.8)
					model:PivotTo(CFrame.new(spot.Position.X, spot.Position.Y, spot.Position.Z) * CFrame.Angles(0, math.rad((spot.Position.X * 37 + spot.Position.Z * 11) % 360), 0))
					-- опорная точка модели в центре габарита: опускаем так, чтобы дно горшка стояло на полу
					local bc, bsz = model:GetBoundingBox()
					model:PivotTo(model:GetPivot() + Vector3.new(spot.Position.X - bc.Position.X, (spot.Position.Y - 0.1) - (bc.Position.Y - bsz.Y / 2), spot.Position.Z - bc.Position.Z))
					local hit = Instance.new("Part")
					hit.Name = "PotCollision"
					hit.Shape = Enum.PartType.Cylinder
					hit.Size = Vector3.new(1.2, 1.9, 1.9)
					hit.CFrame = CFrame.new(spot.Position.X, spot.Position.Y + 0.6, spot.Position.Z) * CFrame.Angles(0, 0, math.rad(90))
					hit.Anchored = true
					hit.Transparency = 1
					hit.CanTouch = false
					hit.CanQuery = false
					hit.Parent = model
					model.Parent = corridor
					spot:Destroy()
				end
			end
			(container :: Instance):Destroy()
		end
	end

	-- Plant_7 (NE) стоит вплотную к радиатору и кулеру: уменьшен, листья больше не заходят на радиатор
	local plantSeven = office:FindFirstChild("KonturPlants") and (office:FindFirstChild("KonturPlants") :: Instance):FindFirstChild("Plant_7")
	if plantSeven and plantSeven:IsA("Model") then
		local before = plantSeven:GetPivot()
		plantSeven:ScaleTo(0.82)
		plantSeven:PivotTo(before)
	end

	-- ===== подушки диванов: плоский овал заменён набитой подушкой из Blender (окантовка, пуговица, складки), цвет берётся с исходной детали
	local CUSHION_ID: number? = nil
	-- @@CUSHION_ASSET@@
	if CUSHION_ID then
		local container: Instance? = nil
		for _ = 1, 4 do
			local ok, result = pcall(function()
				return game:GetService("InsertService"):LoadAsset(CUSHION_ID :: number)
			end)
			if ok and result then
				container = result
				break
			end
			task.wait(3)
		end
		if container then
			local list: {Model} = {}
			for _, d in rooms:GetDescendants() do
				if d:IsA("Model") and string.find(d.Name, "^SofaCushion_") and d:FindFirstChild("SoftCushion") then
					table.insert(list, d)
				end
			end
			for _, old in list do
				local soft = old:FindFirstChild("SoftCushion") :: BasePart
				local base = soft.Color
				local copy = Instance.new("Model")
				copy.Name = "KonturSofaCushion"
				for _, mesh in (container :: Instance):GetDescendants() do
					if mesh:IsA("MeshPart") then
						local _, hex = string.match(mesh.Name, "^SofaCushion_(.+)_(%x%x%x%x%x%x)$")
						local mc = mesh:Clone()
						local piping = hex == "8a8a8a"
						mc.Color = if piping then base:Lerp(Color3.new(0, 0, 0), 0.25) else base:Lerp(Color3.new(1, 1, 1), 0.12)
						mc.Material = Enum.Material.SmoothPlastic
						mc.DoubleSided = true
						mc.Anchored = true
						mc.CanCollide = false
						mc.CanTouch = false
						mc.CanQuery = false
						mc.Parent = copy
					end
				end
				if #copy:GetChildren() > 0 then
					copy.Parent = old.Parent
					copy:PivotTo(soft.CFrame)
					old:Destroy()
				else
					copy:Destroy()
					warn("KONTUR sofa cushion: пустая модель, подушка оставлена старой")
				end
			end
			(container :: Instance):Destroy()
		end
	end

	-- ===== горшки KD_Planter (цилиндр с палками-«травой» и чёрными точками) заменены растениями из Blender (лилия, монстера, фикус)
	local LILY_ID: number? = nil
	local MONSTERA_ID: number? = nil
	-- @@PLANTS_ASSET@@
	local decorF = office:FindFirstChild("KonturDecor")
	if decorF then
		local function loadContainer(id: number?): Instance?
			if not id then
				return nil
			end
			for _ = 1, 4 do
				local ok, result = pcall(function()
					return game:GetService("InsertService"):LoadAsset(id :: number)
				end)
				if ok and result then
					return result
				end
				task.wait(3)
			end
			return nil
		end
		local species: {{key: string, container: Instance?, pot: {number}}} = {
			{key = "PlantLily", container = loadContainer(LILY_ID), pot = {2.1, 1.4}},
			{key = "PlantMonstera", container = loadContainer(MONSTERA_ID), pot = {2.4, 1.5}},
			{key = "PlantFig", container = loadContainer(FIG_ID), pot = {2.3, 1.5}},
		}
		local idx = 0
		for _, planter in decorF:GetChildren() do
			if planter:IsA("Model") and planter.Name == "KD_Planter" then
				idx += 1
				local sp = species[((idx - 1) % #species) + 1]
				if sp.container then
					local pc = planter:GetPivot().Position
					local model = Instance.new("Model")
					model.Name = "KonturPlanterPlant"
					for _, mesh in (sp.container :: Instance):GetDescendants() do
						if mesh:IsA("MeshPart") then
							local _, hex = string.match(mesh.Name, "^" .. sp.key .. "_(.+)_(%x%x%x%x%x%x)$")
							local c = mesh:Clone()
							if hex then
								c.Color = Color3.fromHex(hex)
							end
							c.Anchored = true
							c.CanCollide = false
							c.CanQuery = false
							c.CanTouch = false
							c.Material = Enum.Material.SmoothPlastic
							c.DoubleSided = true
							c.Parent = model
						end
					end
					if #model:GetChildren() == 0 then
						model:Destroy()
						warn("KONTUR planter plant: пустая модель, горшок оставлен старым")
						continue
					end
					model.Parent = decorF
					model:PivotTo(CFrame.new(pc.X, 0.1, pc.Z) * CFrame.Angles(0, math.rad((pc.X * 53 + pc.Z * 17) % 360), 0))
					local bc, bsz = model:GetBoundingBox()
					model:PivotTo(model:GetPivot() + Vector3.new(pc.X - bc.Position.X, 0.1 - (bc.Position.Y - bsz.Y / 2), pc.Z - bc.Position.Z))
					local hit = Instance.new("Part")
					hit.Name = "PotCollision"
					hit.Shape = Enum.PartType.Cylinder
					hit.Size = Vector3.new(sp.pot[2], sp.pot[1], sp.pot[1])
					hit.CFrame = CFrame.new(pc.X, 0.1 + sp.pot[2] / 2, pc.Z) * CFrame.Angles(0, 0, math.rad(90))
					hit.Anchored = true
					hit.Transparency = 1
					hit.CanTouch = false
					hit.CanQuery = false
					hit.Parent = model
					planter:Destroy()
				end
			end
		end
		for _, sp in species do
			if sp.container then
				(sp.container :: Instance):Destroy()
			end
		end
	end

	-- ===== переговорная
	local decor = office:FindFirstChild("KonturDecor")
	if decor then
		for _, m in decor:GetChildren() do
			if string.find(m.Name, "Rug") and m:IsA("Model") then
				local p = pos(m)
				if p.Z < 0 and p.X > 1032 then
					m:Destroy()
				end
			end
		end
	end
	-- ===== листы и подписи нулевой толщины (Part с SurfaceGui) не должны тонуть в лотках и крышках: поднимаем на верх детали под ними
	local lifted = 0
	local scanned = 0
	for _, sheet in office:GetDescendants() do
		scanned += 1
		if sheet:IsA("BasePart") and sheet.Size.Y < 0.012 and sheet.Transparency < 1 and sheet.CFrame.UpVector.Y > 0.9 and sheet:FindFirstChildWhichIsA("SurfaceGui") then
			local model = sheet:FindFirstAncestorWhichIsA("Model")
			if model and sheet.Name == "InspectionExample" then
				-- бланк лежит на стопке листов в лотке (верх стопки на 2,833 над полом модели); лоток полый, поэтому по его рамке высоту не искать
				-- бланк был наклонён на 12° (один край торчал над лотком, казалось, что лист висит): кладём плашмя, сохраняя поворот вокруг вертикали
				-- и по центру лотка: лотки стоят на x = ±1,05 от оси шкафа (бланк был смещён к центру шкафа, на ±0,84), глубина по центру (0)
				local _, yaw = sheet.CFrame:ToOrientation()
				local piv = model:GetPivot()
				local lp = piv:PointToObjectSpace(sheet.Position)
				local centre = piv:PointToWorldSpace(Vector3.new(if lp.X < 0 then -1.05 else 1.05, 0, 0))
				sheet.CFrame = CFrame.new(centre.X, piv.Position.Y + 2.830, centre.Z) * CFrame.fromOrientation(0, yaw, 0)
				lifted += 1
			elseif model then
				local bestTop: number? = nil
				for _, c in model:GetDescendants() do
					if c.ClassName == "Part" and c ~= sheet and c.Transparency < 1 and c.Size.Y >= 0.012 then
						local l = c.CFrame:PointToObjectSpace(sheet.Position)
						if math.abs(l.X) <= c.Size.X / 2 and math.abs(l.Y) <= c.Size.Y / 2 + 0.005 and math.abs(l.Z) <= c.Size.Z / 2 then
							local top = c.CFrame:PointToWorldSpace(Vector3.new(l.X, c.Size.Y / 2, l.Z)).Y
							if not bestTop or top > bestTop then
								bestTop = top
							end
						end
					end
				end
				if bestTop and bestTop > sheet.Position.Y - 0.004 and bestTop - sheet.Position.Y < 0.04 then
					sheet.Position = Vector3.new(sheet.Position.X, bestTop + 0.006, sheet.Position.Z)
					lifted += 1
				end
			end
		end
		if scanned % 4000 == 0 then
			task.wait()
		end
	end

end

return attachUserCleanup
