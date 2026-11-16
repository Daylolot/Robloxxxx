--!strict
-- Стартовая комната: панель отчёта V09_0276_ReportStation несла обе кнопки на одной стойке (расстояние 1,2 стада).
-- Теперь две стойки и две кнопки: «Без изменений» остаётся на исходной стойке (кнопка по центру), «Есть аномалия» переезжает на
-- вторую стойку, копию первой, в 11 стадах слева (под табло уровня). Кнопка с ProximityPrompt остаётся потомком исходной модели:
-- сервис отчёта держит подписки на неё, а исходная модель исключена из проверки прямой видимости.
-- Игрок пока не должен управлять светом и лампами: подсказку «Переключить настольную лампу» (раунд с существом на потолке) убираем,
-- она создаётся сервисом отчёта при старте, поэтому следим за новыми потомками
local function removeLightPrompts(office: Instance)
	local function check(item: Instance)
		if item:IsA("ProximityPrompt") and (item.Name == "CeilingAnomalyLampSwitch" or string.find(item.ObjectText, "лампа") ~= nil and item.ActionText == "Переключить") then
			item:Destroy()
		end
	end
	for _, item in office:GetDescendants() do
		check(item)
	end
	office.DescendantAdded:Connect(check)
end

local function fixStartRoom(office: Instance?)
	if not office then
		return
	end
	removeLightPrompts(office)
	local rooms = office:FindFirstChild("Rooms")
	local start = rooms and rooms:FindFirstChild("StartRoom")
	local station = start and start:FindFirstChild("V09_0276_ReportStation")
	if not (start and station and station:IsA("Model")) or station:GetAttribute("StationSplit") then
		return
	end
	local pivot = station:GetPivot()
	local function cluster(model: Model, base: CFrame, sign: number): {BasePart}
		local list: {BasePart} = {}
		for _, item in model:GetDescendants() do
			if item:IsA("BasePart") then
				local rel = base:PointToObjectSpace(item.Position)
				if math.abs(rel.X - sign * 0.6) < 0.05 and rel.Y > 2.85 and rel.Y < 3.6 and rel.Z < -0.3 then
					table.insert(list, item)
				end
			end
		end
		return list
	end
	local anomalyParts = cluster(station, pivot, -1)
	local clearParts = cluster(station, pivot, 1)
	if #anomalyParts == 0 or #clearParts == 0 then
		warn("KONTUR start room: кластеры кнопок не найдены")
		return
	end
	local twin = station:Clone()
	twin.Name = "V09_0276_ReportStation_Anomaly"
	for _, sign in {-1, 1} do
		for _, item in cluster(twin, pivot, sign) do
			item:Destroy()
		end
	end
	local twinPivot = pivot - Vector3.new(pivot.X - 984, 0, 0)
	twin:PivotTo(twinPivot)
	-- экран копии: статический текст вместо копии строки состояния
	local display = twin:FindFirstChild("ReportDisplay", true)
	local gui = display and display:FindFirstChildWhichIsA("SurfaceGui")
	if gui then
		gui:ClearAllChildren()
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundTransparency = 1
		label.Text = "АНОМАЛИЯ?"
		label.TextColor3 = Color3.fromRGB(235, 170, 140)
		label.Font = Enum.Font.GothamBold
		label.TextScaled = true
		label.Parent = gui
	end
	twin.Parent = start
	-- кнопка «Есть аномалия» и её окружение встают на вторую стойку по центру; «Без изменений» центрируется на первой
	for _, part in anomalyParts do
		local rel = pivot:ToObjectSpace(part.CFrame)
		part.CFrame = twinPivot * (rel + Vector3.new(0.6, 0, 0))
	end
	for _, part in clearParts do
		part.CFrame = part.CFrame + pivot:VectorToWorldSpace(Vector3.new(-0.6, 0, 0))
	end
	station:SetAttribute("StationSplit", true)

	-- разметка постов: цветная площадка перед каждой стойкой со стрелкой к кнопке, неоновая полоса над кнопкой и подсветка
	-- (зелёный «БЕЗ ИЗМЕНЕНИЙ», красный «АНОМАЛИЯ»), чтобы два поста не выглядели одинаково
	local marks = Instance.new("Folder")
	marks.Name = "KonturStartMarks"
	local function mark(x: number, z: number, color: Color3, text: string)
		local floorHit = workspace:Raycast(Vector3.new(x, 6, z + 2), Vector3.new(0, -8, 0))
		local fy = if floorHit then floorHit.Position.Y else 0.1
		local function part(size: Vector3, cf: CFrame, c: Color3, material: Enum.Material?, trans: number?): Part
			local p = Instance.new("Part")
			p.Size = size
			p.CFrame = cf
			p.Color = c
			p.Material = material or Enum.Material.SmoothPlastic
			p.Transparency = trans or 0
			p.Anchored = true
			p.CanCollide = false
			p.CanQuery = false
			p.CanTouch = false
			p.CastShadow = false
			p.Parent = marks
			return p
		end
		local pad = part(Vector3.new(3.6, 0.04, 2.8), CFrame.new(x, fy + 0.03, z + 2.0), color:Lerp(Color3.new(0, 0, 0), 0.55), Enum.Material.SmoothPlastic)
		for _, dx in {-1.74, 1.74} do
			part(Vector3.new(0.1, 0.05, 2.8), CFrame.new(x + dx, fy + 0.035, z + 2.0), color, Enum.Material.Neon)
		end
		part(Vector3.new(3.6, 0.05, 0.1), CFrame.new(x, fy + 0.035, z + 3.35), color, Enum.Material.Neon)
		-- стрелка к стойке (в сторону -Z): стержень и два крыла
		local base = CFrame.new(x, fy + 0.05, z + 2.4)
		part(Vector3.new(0.22, 0.04, 1.2), base, color, Enum.Material.Neon)
		part(Vector3.new(0.22, 0.04, 0.8), base * CFrame.new(-0.28, 0, -0.5) * CFrame.Angles(0, math.rad(-45), 0), color, Enum.Material.Neon)
		part(Vector3.new(0.22, 0.04, 0.8), base * CFrame.new(0.28, 0, -0.5) * CFrame.Angles(0, math.rad(45), 0), color, Enum.Material.Neon)
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Top
		gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
		gui.CanvasSize = Vector2.new(280, 360)
		gui.LightInfluence = 0
		gui.Parent = pad
		local t = Instance.new("TextLabel")
		t.AnchorPoint = Vector2.new(0.5, 0.5)
		t.Position = UDim2.fromScale(0.86, 0.5)
		t.Size = UDim2.fromOffset(300, 62)
		t.Rotation = 90
		t.BackgroundTransparency = 1
		t.Font = Enum.Font.GothamBold
		t.TextScaled = true
		t.TextColor3 = color
		t.Text = text
		t.Parent = gui
		local strip = part(Vector3.new(2.8, 0.14, 0.08), CFrame.new(x, 5.35, z + 0.6), color, Enum.Material.Neon)
		local light = Instance.new("PointLight")
		light.Color = color
		light.Range = 12
		light.Brightness = 1.2
		light.Shadows = false
		light.Parent = strip
	end
	mark(995.0, 57.1, Color3.fromRGB(70, 220, 120), "БЕЗ ИЗМЕНЕНИЙ")
	mark(984.0, 57.1, Color3.fromRGB(255, 80, 70), "АНОМАЛИЯ")
	marks.Parent = start
end

return fixStartRoom
