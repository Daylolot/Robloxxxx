--!strict
-- v43: MEN и WOMEN были зеркальными копиями. Теперь у каждого свой облик (всё из простых частей, папка KonturWC):
--   MEN: два писсуара с перегородкой и резиновым ковриком у восточной стены, уголок уборщика (ведро со шваброй) у западной.
--   WOMEN: зона отдыха с ковровой дорожкой (два пуфа, столик с вазой и цветами) и зеркало в рост у восточной стены.
-- Предметы лежат вне путей к дверям и кабинкам (координаты сверены с кадрами).
local function attachWcDressing(office: Instance)
	local folder = Instance.new("Folder")
	folder.Name = "KonturWC"

	local function floorAt(x: number, z: number): number
		local hit = workspace:Raycast(Vector3.new(x, 6, z), Vector3.new(0, -8, 0))
		return if hit then hit.Position.Y else 0.2
	end
	local function part(size: Vector3, cf: CFrame, color: Color3, material: Enum.Material?, shape: Enum.PartType?, solid: boolean?): Part
		local p = Instance.new("Part")
		p.Size = size
		p.CFrame = cf
		p.Color = color
		p.Material = material or Enum.Material.SmoothPlastic
		p.Anchored = true
		p.CanCollide = solid == true
		p.CanQuery = solid == true
		p.CanTouch = false
		p.CastShadow = false
		if shape then
			p.Shape = shape
		end
		p.Parent = folder
		return p
	end
	-- вертикальный цилиндр: ось Part-цилиндра по X, поворачиваем вокруг Z
	local function post(height: number, diameter: number, x: number, y: number, z: number, color: Color3, material: Enum.Material?, solid: boolean?): Part
		return part(Vector3.new(height, diameter, diameter), CFrame.new(x, y, z) * CFrame.Angles(0, 0, math.rad(90)), color, material, Enum.PartType.Cylinder, solid)
	end

	local white = Color3.fromRGB(240, 242, 244)
	local metal = Color3.fromRGB(176, 182, 188)

	-- ===== MEN: восточная стена внутри x≈1031.5 =====
	do
		local wall = 1031.45
		local fy = floorAt(wall - 1.5, 85)
		for _, z in {83.8, 86.2} do
			part(Vector3.new(0.15, 2.4, 1.2), CFrame.new(wall - 0.1, fy + 3.1, z), white)
			local bowl = part(Vector3.new(1.0, 1.7, 1.1), CFrame.new(wall - 0.5, fy + 2.5, z), white, nil, Enum.PartType.Ball, true)
			bowl.Name = "Bowl"
			post(0.15, 0.3, wall - 0.55, fy + 1.7, z, Color3.fromRGB(60, 64, 68))
			post(1.4, 0.18, wall - 0.12, fy + 4.8, z, metal, Enum.Material.Metal)
			part(Vector3.new(0.35, 0.3, 0.35), CFrame.new(wall - 0.2, fy + 3.9, z), metal, Enum.Material.Metal)
		end
		part(Vector3.new(1.4, 2.7, 0.12), CFrame.new(wall - 0.75, fy + 3.55, 85.0), Color3.fromRGB(205, 214, 216), nil, nil, true)
		part(Vector3.new(2.4, 0.06, 5.6), CFrame.new(wall - 1.45, fy + 0.03, 85.0), Color3.fromRGB(46, 50, 54), Enum.Material.Rubber)
		-- уголок уборщика у западной стены
		local bx, bz = 1009.9, 72.6
		local wy = floorAt(bx, bz)
		post(1.2, 1.05, bx, wy + 0.6, bz, Color3.fromRGB(236, 190, 40), nil, true)
		post(0.1, 1.15, bx, wy + 1.25, bz, Color3.fromRGB(180, 140, 20))
		post(4.6, 0.13, bx - 0.55, wy + 2.3, bz + 0.4, Color3.fromRGB(150, 120, 80), Enum.Material.Wood)
		part(Vector3.new(0.7, 0.35, 0.7), CFrame.new(bx - 0.55, wy + 0.2, bz + 0.4), Color3.fromRGB(190, 190, 184), Enum.Material.Fabric, Enum.PartType.Ball)
	end

	-- WOMEN: зона отдыха (столик, пуфы, ковёр) и зеркало в рост убраны по просьбе пользователя

	folder.Parent = office
end

return attachWcDressing
