--!strict
-- v43: у каждой комнаты свой пол (раньше везде одинаковый серо-синий ковёр): перекрашиваем плитки FloorTile в папках Floors/<комната>
-- с лёгкой разницей тона между плитками. Кухонные зоны EAST и NE получают паркет, склад NW бетон, туалеты плитку разного цвета,
-- переговорная NE бордовый ковёр, зона отдыха EAST бирюзовый. Только цвет и материал существующих деталей, геометрия не меняется.
local function attachFloors(office: Instance)
	task.wait(14) -- RoomStyle.server красит полы при старте и перетёр бы наши цвета
	local floors = office:FindFirstChild("Floors")
	if not floors then
		return
	end
	local function tint(base: Color3, seed: number, amount: number): Color3
		local k = ((seed * 7919) % 13) / 13 - 0.5
		return Color3.new(math.clamp(base.R * (1 + k * amount), 0, 1), math.clamp(base.G * (1 + k * amount), 0, 1), math.clamp(base.B * (1 + k * amount), 0, 1))
	end
	local function rgb(r: number, g: number, b: number): Color3
		return Color3.fromRGB(r, g, b)
	end
	-- правило: функция (комната, позиция плитки) -> цвет, материал
	local function rule(room: string, pos: Vector3): (Color3?, Enum.Material?)
		if room == "WEST" then
			return rgb(58, 80, 104), nil
		elseif room == "CENTER" then
			return rgb(86, 84, 92), nil
		elseif room == "EAST" then
			if pos.Z < 22 then
				return rgb(158, 120, 82), Enum.Material.WoodPlanks
			elseif pos.Z > 50 then
				return rgb(52, 98, 104), nil
			end
			return rgb(74, 78, 94), nil
		elseif room == "NE" then
			if pos.X > 1088 and pos.Z < -16 then
				return rgb(158, 120, 82), Enum.Material.WoodPlanks
			elseif pos.X > 1048 and pos.X < 1082 and pos.Z > -24 and pos.Z < -4 then
				return rgb(104, 58, 66), nil
			end
			return rgb(68, 74, 86), nil
		elseif room == "NW" then
			return rgb(124, 126, 130), Enum.Material.Concrete
		elseif room == "MEN" then
			return rgb(150, 184, 206), nil
		elseif room == "WOMEN" then
			return rgb(228, 204, 192), nil
		elseif room == "START" then
			return rgb(80, 72, 88), nil
		end
		return nil, nil
	end
	local count = 0
	for _, folder in floors:GetChildren() do
		if folder:IsA("Model") or folder:IsA("Folder") then
			for _, tile in folder:GetChildren() do
				if tile:IsA("BasePart") then
					local color, material = rule(folder.Name, tile.Position)
					if color then
						tile.Color = tint(color, math.floor(tile.Position.X * 3 + tile.Position.Z * 5), if material == Enum.Material.WoodPlanks then 0.1 else 0.05)
						if material then
							tile.Material = material
						end
						count += 1
					end
				end
			end
		end
	end
	office:SetAttribute("FloorTilesRecolored", count)
end

return attachFloors
