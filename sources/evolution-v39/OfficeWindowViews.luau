--!strict
-- v43: за стеклом окон стоит глухая плоскость NightBackdrop (однотонный серо-голубой фон). Каждому окну на эту плоскость кладётся
-- SurfaceGui с видом на вечерний город: градиент неба от тёмно-синего к закатному, луна, два слоя силуэтов зданий и тёплые окошки.
-- Свет не используется (LightInfluence 0), панель просто светится как картинка за стеклом.
local function attachWindowViews(office: Instance)
	local details = office:FindFirstChild("ArchitecturalDetails")
	if not details then
		return
	end
	local rng = Random.new(2026)
	local function rect(parent: Instance, x: number, y: number, w: number, h: number, color: Color3, anchorBottom: boolean?): Frame
		local f = Instance.new("Frame")
		f.BackgroundColor3 = color
		f.BorderSizePixel = 0
		f.Position = UDim2.fromScale(x, y)
		f.Size = UDim2.fromScale(w, h)
		if anchorBottom then
			f.AnchorPoint = Vector2.new(0, 1)
		end
		f.Parent = parent
		return f
	end
	local function faceToward(part: BasePart, dir: Vector3): Enum.NormalId
		local best, bestDot = Enum.NormalId.Front, -2
		for _, face in {Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Top, Enum.NormalId.Bottom, Enum.NormalId.Left, Enum.NormalId.Right} do
			local d = part.CFrame:VectorToWorldSpace(Vector3.fromNormalId(face)):Dot(dir)
			if d > bestDot then
				best, bestDot = face, d
			end
		end
		return best
	end
	local done = 0
	for _, m in details:GetChildren() do
		if m:IsA("Model") and string.find(m.Name, "^Window%d+$") then
			local backdrop = m:FindFirstChild("NightBackdrop")
			if backdrop and backdrop:IsA("BasePart") and not backdrop:FindFirstChild("CityView") then
				local look = m:GetPivot().LookVector
				local gui = Instance.new("SurfaceGui")
				gui.Name = "CityView"
				gui.Face = faceToward(backdrop, look)
				gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
				gui.CanvasSize = Vector2.new(690, 340)
				gui.LightInfluence = 0
				gui.Brightness = 1.15
				gui.Parent = backdrop
				backdrop.Color = Color3.fromRGB(30, 28, 50)
				-- материал Glass рисуется поверх SurfaceGui и скрывает вид: стекло делаем обычным полупрозрачным пластиком
				local glass = m:FindFirstChild("Glazing")
				if glass and glass:IsA("BasePart") then
					glass.Material = Enum.Material.SmoothPlastic
					glass.Transparency = 0.55
				end
				local sky = rect(gui, 0, 0, 1, 1, Color3.new(1, 1, 1))
				local grad = Instance.new("UIGradient")
				grad.Rotation = 90
				grad.Color = ColorSequence.new({
					ColorSequenceKeypoint.new(0, Color3.fromRGB(12, 16, 40)),
					ColorSequenceKeypoint.new(0.45, Color3.fromRGB(62, 46, 100)),
					ColorSequenceKeypoint.new(0.75, Color3.fromRGB(214, 112, 96)),
					ColorSequenceKeypoint.new(1, Color3.fromRGB(246, 168, 92)),
				})
				grad.Parent = sky
				local moon = rect(gui, rng:NextNumber(0.1, 0.8), 0.1, 0.05, 0.1, Color3.fromRGB(240, 238, 214))
				local corner = Instance.new("UICorner")
				corner.CornerRadius = UDim.new(1, 0)
				corner.Parent = moon
				for layer = 1, 2 do
					local x = -0.02
					while x < 1 do
						local w = rng:NextNumber(0.06, 0.14)
						local h = rng:NextNumber(0.2, 0.5) * (if layer == 1 then 0.8 else 1)
						local shade = if layer == 1 then Color3.fromRGB(78, 60, 98) else Color3.fromRGB(20, 22, 36)
						local b = rect(gui, x, 1, w, h, shade, true)
						if layer == 2 then
							for r = 1, 4 do
								for c = 1, 2 do
									if rng:NextNumber() < 0.4 then
										rect(b, (c - 0.5) / 2 - 0.12, (r - 0.5) / 4 - 0.06, 0.24, 0.09, Color3.fromRGB(255, 214, 128))
									end
								end
							end
						end
						x += w + rng:NextNumber(0.004, 0.02)
					end
				end
				done += 1
			end
		end
	end
	office:SetAttribute("WindowViews", done)
end

return attachWindowViews
