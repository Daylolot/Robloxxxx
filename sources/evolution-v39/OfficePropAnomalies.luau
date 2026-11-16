--!strict
-- v39: подключается сборкой sources/evolution-v39/build_place.py; проверка: sources/evolution-v39/studio_verify_props.py.
-- Дешёвые «смысловые» аномалии: сервер поворачивает, роняет, перекрашивает уже стоящие предметы, включает и выключает свет панелей и меняет надписи на SurfaceGui; ничего тяжёлого не добавляет.
-- Подключение (делает сборщик build_place.py): перед `return {activate=activate,names=names}` в OfficeObjects.server
--   local pack = attachPropAnomalies(office, names)
-- и обёртка activate: `handled = pack(scenario, round)`; если handled, базовая логика получает "Clear" вместо имени
-- сценария (атрибуты OfficeDetail* реплицируются всем и выдавали бы ответ раунда), иначе имя как раньше.
-- Имена сценариев попадают в `names` только когда нужные предметы найдены на карте.
local function attachPropAnomalies(office: Instance, names: {string}): (string?, number?) -> boolean
	local originals: {[Model]: CFrame} = {}
	local groups: {[string]: {Model}} = {} -- по суффиксу имени предмета
	local SUFFIXES: {[string]: string} = {
		ClockTilted = "WallClock",
		ChairFacesWall = "ErgoChair",
		RowChairsTurned = "ErgoChair",
		MeetingChairsTurned = "MeetingChair",
		SignBackwards = "WayfindingSigns",
		PhotosBackwards = "PersonalPhotos",
		NoticeBoardCrooked = "NoticeBoard",
		ChairKnockedOver = "ErgoChair",
		BinKnockedOver = "PedalBin",
		PhoneOffHook = "Telephone",
		MonitorHousingRed = "Monitor", -- любой предмет, чьё имя оканчивается на Monitor
		-- текстовые: меняется надпись на SurfaceGui (подробности в TEXT_EDITS)
		BoardMeetingTime = "NoticeBoard",
		NewspaperWrongDay = "Newspaper",
		SignNumberChanged = "WayfindingSigns",
		KitchenSignWarning = "KitchenSigns",
		BadgeNameChanged = "EmployeeBadges",
		CalendarWrongMonth = "WallCalendar",
		PlanningBoardNote = "PlanningBoard",
	}
	-- сценарий -> {часть исходного текста (простой поиск), функция новой надписи}
	local TEXT_EDITS: {[string]: {find: string, edit: (string) -> string}} = {
		BoardMeetingTime = {find = "СОБРАНИЕ", edit = function(text: string): string
			local changed, count = string.gsub(text, "%d%d:%d%d", "03:33", 1)
			return if count > 0 then changed else text .. "\n03:33"
		end},
		NewspaperWrongDay = {find = "ВТОРНИК", edit = function(text: string): string
			return (string.gsub(text, "ВТОРНИК", "ЧЕТВЕРГ"))
		end},
		SignNumberChanged = {find = "АРХИВ", edit = function(text: string): string
			local changed, count = string.gsub(text, "%d+%s*$", "13")
			return if count > 0 then changed else text .. " / 13"
		end},
		KitchenSignWarning = {find = "СПАСИБО", edit = function(_: string): string
			return "НЕ ОГЛЯДЫВАЙТЕСЬ"
		end},
		BadgeNameChanged = {find = "АЛЕКСЕЙ", edit = function(text: string): string
			return (string.gsub(text, "[^\n]*АЛЕКСЕЙ[^\n]*", "ВАША ФАМИЛИЯ"))
		end},
		CalendarWrongMonth = {find = "ОКТЯБРЬ", edit = function(text: string): string
			return (string.gsub(text, "ОКТЯБРЬ", "НОЯБРЬ"))
		end},
		PlanningBoardNote = {find = "Проверить отчёты", edit = function(_: string): string
			return "Проверить, кто в здании"
		end},
	}
	for _, suffix in SUFFIXES do
		groups[suffix] = {}
	end

	-- Предметы лежат прямыми потомками комнат и коридора: обходим только детей этих контейнеров
	-- (без GetDescendants по всей карте) и делаем это синхронно, до открытия раундов.
	local containers: {Instance} = {office}
	local rooms = office:FindFirstChild("Rooms")
	if rooms then
		for _, room in rooms:GetChildren() do
			table.insert(containers, room)
		end
	end
	local corridor = office:FindFirstChild("Corridor")
	if corridor then
		table.insert(containers, corridor)
	end
	for _, container in containers do
		for _, item in container:GetChildren() do
			if item:IsA("Model") then
				local suffix = string.match(item.Name, "^V09_%d+_(%w+)$") or item.Name
				if string.match(suffix, "Monitor$") then
					suffix = "Monitor"
				end
				local list = groups[suffix]
				if list then
					table.insert(list, item)
					originals[item] = item:GetPivot()
				end
			end
		end
	end
	-- оставляем только предметы с нужными частями (иначе раунд прошёл бы без видимой аномалии)
	local requires: {[string]: (Model) -> boolean} = {
		Telephone = function(model: Model): boolean
			return model:FindFirstChild("Receiver", true) ~= nil
		end,
		Monitor = function(model: Model): boolean
			return model:FindFirstChild("Housing") ~= nil
		end,
	}
	for suffix, check in requires do
		local kept: {Model} = {}
		for _, model in groups[suffix] or {} do
			if check(model) then
				table.insert(kept, model)
			end
		end
		groups[suffix] = kept
	end
	-- текстовые сценарии: берём только предметы, у которых действительно есть нужная надпись
	local textTargets: {[string]: {Model}} = {}
	for scenario, edit in TEXT_EDITS do
		local targets: {Model} = {}
		for _, model in groups[SUFFIXES[scenario]] or {} do
			for _, item in model:GetDescendants() do
				if item:IsA("TextLabel") and string.find(item.Text, edit.find, 1, true) and edit.edit(item.Text) ~= item.Text then
					table.insert(targets, model)
					break
				end
			end
		end
		textTargets[scenario] = targets
	end
	-- в пул попадают только сценарии с целью; порядок фиксирован (сортировка), чтобы не менять выбор по номеру раунда
	local pending: {string} = {}
	for scenario, suffix in SUFFIXES do
		local available = if TEXT_EDITS[scenario] then #textTargets[scenario] > 0 else #groups[suffix] > 0
		if available and not table.find(names, scenario) then
			table.insert(pending, scenario)
		end
	end
	table.sort(pending)
	for _, scenario in pending do
		table.insert(names, scenario)
	end
	-- Свет: у каждой потолочной панели есть BoolValue IsOn, его читает FixtureController панели.
	local panels: {Model} = {}
	local panelOriginal: {[Model]: boolean} = {}
	local lighting = office:FindFirstChild("Lighting")
	if lighting then
		for _, item in lighting:GetChildren() do
			if item:IsA("Model") and string.match(item.Name, "^V09_%d+_CeilingPanel$") then
				local on = item:FindFirstChild("IsOn")
				if on and on:IsA("BoolValue") then
					table.insert(panels, item)
					panelOriginal[item] = on.Value
				end
			end
		end
	end
	-- Границы комнат по положению их деталей (один раз при старте сервера, игроков ещё нет).
	-- Каждая панель относится ровно к одной комнате: из всех границ, где она лежит, берём наименьшую по площади.
	local roomPanels: {[string]: {Model}} = {}
	if rooms and #panels > 0 then
		type Extent = {name: string, lowX: number, lowZ: number, highX: number, highZ: number, area: number}
		local extents: {Extent} = {}
		for _, room in rooms:GetChildren() do
			local lowX, lowZ, highX, highZ = math.huge, math.huge, -math.huge, -math.huge
			for _, item in room:GetDescendants() do
				if item:IsA("BasePart") then
					local position = item.Position
					lowX, highX = math.min(lowX, position.X), math.max(highX, position.X)
					lowZ, highZ = math.min(lowZ, position.Z), math.max(highZ, position.Z)
				end
			end
			if lowX < highX and lowZ < highZ then
				table.insert(extents, {name = room.Name, lowX = lowX, lowZ = lowZ, highX = highX, highZ = highZ,
					area = (highX - lowX) * (highZ - lowZ)})
			end
		end
		for _, panel in panels do
			local position = panel:GetPivot().Position
			local best: Extent? = nil
			for _, extent in extents do
				if position.X >= extent.lowX and position.X <= extent.highX
					and position.Z >= extent.lowZ and position.Z <= extent.highZ
					and (best == nil or extent.area < best.area) then
					best = extent
				end
			end
			-- панели стартовой комнаты (стойка ответа) и коридора не трогаем
			if best and best.name ~= "StartRoom" then
				local list = roomPanels[best.name]
				if not list then
					list = {}
					roomPanels[best.name] = list
				end
				table.insert(list, panel)
			end
		end
		for roomName, list in roomPanels do
			if #list < 2 then
				roomPanels[roomName] = nil
			end
		end
	end
	local darkRooms: {string} = {}
	for roomName in roomPanels do
		table.insert(darkRooms, roomName)
	end
	table.sort(darkRooms)
	if #darkRooms > 0 then
		for _, scenario in {"RoomBlackout", "PanelFlicker"} do
			if not table.find(names, scenario) then
				table.insert(names, scenario)
			end
		end
	end
	local flickerToken = 0
	local touchedPanels: {[Model]: boolean} = {} -- панели, которые менял именно этот модуль
	-- торшеры декора (KonturDecor/KD_FloorLamp с атрибутом KonturRoom) гаснут и мигают вместе с панелями своей комнаты
	local touchedLamps: {[Model]: boolean} = {}
local lampBulbOriginal: {[BasePart]: {material: Enum.Material, color: Color3}} = {}
	local lampShadeOriginal: {[BasePart]: {material: Enum.Material, color: Color3}} = {}
	local function setLamp(lamp: Model, on: boolean)
		local light = lamp:FindFirstChild("LampLight", true)
		if light and light:IsA("PointLight") then
			light.Enabled = on
		end
		-- нить (Bulb, Neon) гаснет вместе со светом: иначе торшер «выключен» только светом
		local bulb = lamp:FindFirstChild("Bulb")
		if bulb and bulb:IsA("BasePart") then
			if not lampBulbOriginal[bulb] then
				lampBulbOriginal[bulb] = {material = bulb.Material, color = bulb.Color}
			end
			local original = lampBulbOriginal[bulb]
			bulb.Material = if on then original.material else Enum.Material.SmoothPlastic
			bulb.Color = if on then original.color else Color3.fromRGB(70, 66, 60)
		end
		-- абажур из меша Blender (FloorLamp_shade): гаснет вместе со светом
		local shade = lamp:FindFirstChild("FloorLamp_shade")
		if shade and shade:IsA("MeshPart") then
			if not lampShadeOriginal[shade] then
				lampShadeOriginal[shade] = {material = shade.Material, color = shade.Color}
			end
			local original = lampShadeOriginal[shade]
			shade.Material = if on then original.material else Enum.Material.SmoothPlastic
			shade.Color = if on then original.color else Color3.fromRGB(150, 138, 118)
		end
		touchedLamps[lamp] = true
	end
	local function lampsOfRoom(roomName: string): {Model}
		local found: {Model} = {}
		local decor = office:FindFirstChild("KonturDecor")
		if decor then
			for _, item in decor:GetChildren() do
				if item:IsA("Model") and item.Name == "KD_FloorLamp" and item:GetAttribute("KonturRoom") == roomName then
					table.insert(found, item)
				end
			end
		end
		return found
	end
	local salt = os.time() % 100000 -- цель не повторяется между сессиями и не заучивается

	local textOriginals: {[TextLabel]: string} = {}
	local textApplied: {[TextLabel]: string} = {} -- что поставили мы: чужие правки текста не затираем
	local movedParts: {[BasePart]: CFrame} = {}
	local recoloured: {[BasePart]: Color3} = {}
	local moved: {Model} = {}
	local function restoreAll()
		for part, frame in movedParts do
			if part.Parent then
				part.CFrame = frame
			end
		end
		table.clear(movedParts)
		for label, text in textOriginals do
			if label.Parent and label.Text == textApplied[label] then
				label.Text = text
			end
		end
		table.clear(textOriginals)
		table.clear(textApplied)
		for part, color in recoloured do
			if part.Parent then
				part.Color = color
			end
		end
		table.clear(recoloured)
		for _, model in moved do
			local pivot = originals[model]
			if pivot and model.Parent then
				model:PivotTo(pivot)
			end
		end
		table.clear(moved)
		flickerToken += 1
		for panel in touchedPanels do
			local on = panel:FindFirstChild("IsOn")
			local wasOn = panelOriginal[panel]
			if on and on:IsA("BoolValue") and wasOn ~= nil and on.Value ~= wasOn then
				on.Value = wasOn
			end
		end
table.clear(touchedPanels)
for lamp in touchedLamps do
if lamp.Parent then
setLamp(lamp, true)
end
end
		table.clear(touchedLamps)
	end

	-- Поворот вокруг центра габаритов, ось задана в мировых координатах.
	local function rotateAboutCenter(model: Model, worldAxis: Vector3, angle: number)
		local center = model:GetBoundingBox().Position
		local turn = CFrame.new(center) * CFrame.fromAxisAngle(worldAxis, angle) * CFrame.new(-center)
		if originals[model] and not table.find(moved, model) then
			table.insert(moved, model)
		end
		model:PivotTo(turn * model:GetPivot())
	end

	-- Нижняя точка модели в мире по углам всех деталей (не зависит от PrimaryPart, в отличие от GetBoundingBox).
	local function lowestY(model: Model): number
		local lowest = math.huge
		for _, part in model:GetDescendants() do
			if part:IsA("BasePart") then
				local frame, size = part.CFrame, part.Size
				local half = (math.abs(frame.RightVector.Y) * size.X + math.abs(frame.UpVector.Y) * size.Y
					+ math.abs(frame.LookVector.Y) * size.Z) * 0.5
				lowest = math.min(lowest, frame.Position.Y - half)
			end
		end
		return lowest
	end

	-- Предмет заваливается на бок и остаётся лежать на полу (нижняя точка остаётся на прежней высоте).
	local function knockOver(model: Model, rng: Random)
		local floorY = lowestY(model)
		local axis = if rng:NextInteger(0, 1) == 0 then Vector3.xAxis else Vector3.zAxis
		rotateAboutCenter(model, axis, math.pi / 2)
		model:PivotTo(model:GetPivot() + Vector3.new(0, floorY - lowestY(model), 0))
	end

	-- Нормаль лицевой стороны часов: самая тонкая ось габаритов.
	local function faceNormal(model: Model): Vector3
		local box, size = model:GetBoundingBox()
		if size.X <= size.Y and size.X <= size.Z then
			return box.RightVector
		elseif size.Y <= size.Z then
			return box.UpVector
		end
		return box.LookVector
	end

	local function pick(list: {Model}, rng: Random): Model?
		local alive: {Model} = {}
		for _, model in list do
			if model.Parent and model:IsDescendantOf(office) then
				table.insert(alive, model)
			end
		end
		if #alive == 0 then
			warn("KONTUR prop anomaly: no live target")
			return nil
		end
		local chosen = alive[rng:NextInteger(1, #alive)]
		if game:GetService("RunService"):IsStudio() then
			office:SetAttribute("QATargetPos", chosen:GetPivot().Position)
			office:SetAttribute("QATargetLook", chosen:GetPivot().LookVector) -- только Studio: куда вести тестировщика к выбранному предмету
		end
		return chosen
	end

	local function apply(scenario: string?, round: number?)
		restoreAll()
		if scenario == "RoomBlackout" or scenario == "PanelFlicker" then
			if #darkRooms == 0 then
				warn("KONTUR light anomaly: no rooms with panels")
				return
			end
			local rng = Random.new((round or 0) * 7919 + salt)
local roomName = darkRooms[rng:NextInteger(1, #darkRooms)]
local roomPicked = roomPanels[roomName]
local roomLamps = lampsOfRoom(roomName)
if scenario == "RoomBlackout" then
for _, lamp in roomLamps do
setLamp(lamp, false)
end
				for _, panel in roomPicked do
					local on = panel:FindFirstChild("IsOn")
					if on and on:IsA("BoolValue") then
						touchedPanels[panel] = true
						on.Value = false
					end
				end
			else
				local token = flickerToken
				task.spawn(function()
					-- серии быстрого мерцания каждые ~2,5 с, пока идёт раунд
					while token == flickerToken do
						for _ = 1, 8 do
							for _, panel in roomPicked do
								local on = panel:FindFirstChild("IsOn")
								if on and on:IsA("BoolValue") and token == flickerToken then
touchedPanels[panel] = true
on.Value = rng:NextNumber() < 0.5
end
end
if token == flickerToken then
local lampOn = rng:NextNumber() < 0.5
for _, lamp in roomLamps do
setLamp(lamp, lampOn)
end
end
task.wait(0.11)
						end
						for _, panel in roomPicked do
							local on = panel:FindFirstChild("IsOn")
							if on and on:IsA("BoolValue") and token == flickerToken then
on.Value = panelOriginal[panel]
end
end
if token == flickerToken then
for _, lamp in roomLamps do
setLamp(lamp, true)
end
end
task.wait(2.4)
					end
				end)
			end
			return
		end
		if scenario == nil or SUFFIXES[scenario] == nil then
			return
		end
		local textEdit = TEXT_EDITS[scenario]
		if textEdit then
			local board = pick(textTargets[scenario], Random.new((round or 0) * 7919 + salt))
			if board then
				-- меняем все подходящие надписи модели (обе стороны знака, дубли), чтобы правка не выглядела артефактом
				for _, item in board:GetDescendants() do
					if item:IsA("TextLabel") and string.find(item.Text, textEdit.find, 1, true) then
						local newText = textEdit.edit(item.Text)
						if newText ~= item.Text then
							textOriginals[item] = item.Text
							textApplied[item] = newText
							item.Text = newText
						end
					end
				end
			end
			return
		end
		local rng = Random.new((round or 0) * 7919 + salt)
		local list = groups[SUFFIXES[scenario]]
		if scenario == "ClockTilted" then
			-- перекошенные часы читаются на стене сразу (перевёрнутый безцифирный циферблат почти не виден)
			local clock = pick(list, rng)
			if clock then
				rotateAboutCenter(clock, faceNormal(clock), math.rad(28))
			end
		elseif scenario == "NoticeBoardCrooked" then
			local board = pick(list, rng)
			if board then
				rotateAboutCenter(board, faceNormal(board), math.rad(9))
			end
		elseif scenario == "ChairKnockedOver" or scenario == "BinKnockedOver" then
			local item = pick(list, rng)
			if item then
				knockOver(item, rng)
			end
		elseif scenario == "PhoneOffHook" then
			local phone = pick(list, rng)
			if phone then
				-- трубка (Receiver и концы) движется как одно тело вокруг Receiver; исходные позы собираем до сдвига
				local handset: {BasePart} = {}
				local receiver: BasePart? = nil
				for _, part in phone:GetDescendants() do
					if part:IsA("BasePart") and (part.Name == "Receiver" or part.Name == "ReceiverEnd") then
						table.insert(handset, part)
						movedParts[part] = part.CFrame
						if part.Name == "Receiver" then
							receiver = part
						end
					end
				end
				if receiver then
					local base = receiver.CFrame
					local delta = CFrame.new(0, 0.5, 0) * CFrame.Angles(0, 0, math.rad(28))
					for _, part in handset do
						part.CFrame = base * delta * base:ToObjectSpace(movedParts[part])
					end
				end
			end
		elseif scenario == "MonitorHousingRed" then
			local monitor = pick(list, rng)
			local housing = monitor and monitor:FindFirstChild("Housing")
			if housing and housing:IsA("BasePart") then
				recoloured[housing] = housing.Color
				housing.Color = Color3.fromRGB(176, 38, 38)
			end
		elseif scenario == "RowChairsTurned" then
			-- все кресла одной комнаты повёрнуты в одну сторону
			local chair = pick(list, rng)
			if chair then
				for _, other in list do
					if other.Parent == chair.Parent and other.Parent ~= nil and other:IsDescendantOf(office) then
						rotateAboutCenter(other, Vector3.yAxis, math.pi)
					end
				end
			end
		elseif scenario == "PhotosBackwards" then
			local photo = pick(list, rng)
			if photo then
				rotateAboutCenter(photo, Vector3.yAxis, math.pi)
			end
		elseif scenario == "ChairFacesWall" then
			local chair = pick(list, rng)
			if chair then
				rotateAboutCenter(chair, Vector3.yAxis, math.pi)
			end
		elseif scenario == "MeetingChairsTurned" then
			for _, chair in list do
				if chair.Parent and chair:IsDescendantOf(office) then
					rotateAboutCenter(chair, Vector3.yAxis, math.pi)
				end
			end
		elseif scenario == "SignBackwards" then
			local sign = pick(list, rng)
			if sign then
				rotateAboutCenter(sign, Vector3.yAxis, math.pi)
			end
		end
	end

	-- Возвращает true, если сценарий обслуживает этот модуль. Тогда вызывающий код НЕ публикует сценарий клиентам
	-- (атрибуты OfficeDetail* на AnomalyReportState реплицируются всем и выдавали бы ответ раунда): клиенту
	-- этих аномалий знать сценарий не нужно, он видит только результат на карте. Для тестов сценарий лежит в
	-- ServerStorage (не реплицируется).
	return function(scenario: string?, round: number?): boolean
		local ok, err = pcall(apply, scenario, round)
		if not ok then
			warn("KONTUR prop anomaly failed: " .. tostring(err))
		end
		local handled = scenario ~= nil
			and (SUFFIXES[scenario] ~= nil or scenario == "RoomBlackout" or scenario == "PanelFlicker")
		if game:GetService("RunService"):IsStudio() then -- нужен только тестам; ServerStorage клиентам не реплицируется
			game:GetService("ServerStorage"):SetAttribute("KonturPackScenario", if handled then scenario else nil)
		end
		return handled
	end
end

return attachPropAnomalies
