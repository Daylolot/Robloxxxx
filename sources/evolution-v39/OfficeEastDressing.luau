--!strict
-- v43 (EAST и NE): комната EAST имела пустую середину (≈40×20 ковра). Здесь ставим рабочие места (копии готовых кластеров из WEST: стол, монитор,
-- клавиатура, кресло, системный блок и мелочи) . Копии лежат в папке KonturEast и не участвуют в аномалиях.
-- Копируем только после того, как OfficeFurnitureUpgrade заменил кресла/мониторы мешами из Blender (иначе клоны остались бы из частей).
local function attachEastDressing(office: Instance)
	local rooms = office:WaitForChild("Rooms")
	local west = rooms:WaitForChild("WEST")
	local folder = Instance.new("Folder")
	folder.Name = "KonturEast"

	-- кластер = стол с предметами вокруг (в пределах стола ±4,2 по X и ±3,4 по Z), без телефона (у него подсказка)
	local function findDesk(label: string): Model?
		for _, item in west:GetChildren() do
			if item:IsA("Model") and string.find(item.Name, label .. "$") then
				return item
			end
		end
		return nil
	end
	local function clusterOf(desk: Model): {Model}
		local centre = desk:GetPivot().Position
		local list: {Model} = {}
		for _, item in west:GetChildren() do
			if item:IsA("Model") then
				local p = item:GetPivot().Position
				if math.abs(p.X - centre.X) <= 4.2 and math.abs(p.Z - centre.Z) <= 3.4 and not string.find(item.Name, "Telephone", 1, true) then
					table.insert(list, item)
				end
			end
		end
		return list
	end

	-- ждём замену кресел мешами (в исходной комнате); потолок ожидания 60 с
	local sample = nil
	for _, item in west:GetChildren() do
		if item:IsA("Model") and string.find(item.Name, "ErgoChair$") then
			sample = item
			break
		end
	end
	local deadline = os.clock() + 60
	while sample and os.clock() < deadline do
		local swapped = false
		for _, d in sample:GetDescendants() do
			if d:IsA("MeshPart") then
				swapped = true
				break
			end
		end
		if swapped then
			break
		end
		task.wait(1)
	end
	task.wait(2)

	local function place(deskLabel: string, target: Vector3, flip: boolean)
		local desk = findDesk(deskLabel)
		if not desk then
			return
		end
		local deskPos = desk:GetPivot().Position
		local group = clusterOf(desk)
		local turn = if flip then CFrame.Angles(0, math.pi, 0) else CFrame.identity
		local shift = CFrame.new(Vector3.new(target.X, deskPos.Y, target.Z)) * turn * CFrame.new(-deskPos)
		for _, source in group do
			local copy = source:Clone()
			copy.Name = "KE_" .. source.Name
			copy:PivotTo(shift * source:GetPivot())
			copy.Parent = folder
		end
	end
	-- левая сторона: два рабочих места у стены (кресло к западу от стола, лицом на восток)
	place("0037_StraightDesk", Vector3.new(1074, 0, 37), false)
	place("0047_StraightDesk", Vector3.new(1074, 0, 45), false)
	-- правая сторона: зеркальное место (кресло к востоку, лицом на запад)
	place("0008_StraightDesk", Vector3.new(1099, 0, 36), true)
	-- середина: два рабочих места спинами друг к другу (между ними проход к кухне)
	place("0037_StraightDesk", Vector3.new(1085, 0, 48), false)
	place("0047_StraightDesk", Vector3.new(1097, 0, 48), true)
	-- NE: пустые участки по бокам переговорного стола (у стола уже стоят два рабочих места из декора)
	place("0037_StraightDesk", Vector3.new(1045, 0, -14), false)
	place("0047_StraightDesk", Vector3.new(1089, 0, -14), true)
	folder.Parent = office
end

return attachEastDressing
