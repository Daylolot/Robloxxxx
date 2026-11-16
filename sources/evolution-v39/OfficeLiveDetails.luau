--!strict
-- v43: «живые мелочи» офиса, чтобы карта не стояла застывшей: пар над кофемашиной (периодические облачка при «заваривании»),
-- мигающие индикаторы системных блоков (случайные короткие мигания), часы в строках состояния мониторов (время идёт: игровая минута
-- = 10 секунд). Всё серверное и дешёвое: пара-тройка свойств в секунду на всю карту.
local function attachLiveDetails(office: Instance)
	task.wait(10)
	local rng = Random.new(77)
	local token = 0

	-- пар: на каждой кофемашине эмиттер у носика
	for _, m in office:GetDescendants() do
		if m:IsA("Model") and string.find(m.Name, "CoffeeMachine$") then
			local spout = m:FindFirstChild("CoffeeSpout")
			if spout and spout:IsA("BasePart") then
				local emitter = Instance.new("ParticleEmitter")
				emitter.Texture = "rbxasset://textures/particles/smoke_main.dds"
				emitter.Rate = 0
				emitter.Lifetime = NumberRange.new(1.4, 2.2)
				emitter.Speed = NumberRange.new(0.5, 1.1)
				emitter.SpreadAngle = Vector2.new(12, 12)
				emitter.Size = NumberSequence.new({NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 0.7)})
				emitter.Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 0.7), NumberSequenceKeypoint.new(1, 1)})
				emitter.Color = ColorSequence.new(Color3.fromRGB(240, 240, 240))
				emitter.EmissionDirection = Enum.NormalId.Top
				emitter.Acceleration = Vector3.new(0, 0.6, 0)
				emitter.Parent = spout
				task.spawn(function()
					while emitter.Parent do
						task.wait(rng:NextNumber(9, 22))
						for _ = 1, rng:NextInteger(6, 12) do
							emitter:Emit(2)
							task.wait(0.25)
						end
					end
				end)
			end
		end
	end

	-- индикаторы системных блоков: у большинства ровное свечение, периодически короткое мигание
	for _, m in office:GetDescendants() do
		if m:IsA("Model") and string.find(m.Name, "^ClosedPC") then
			local led = m:FindFirstChild("PCPower")
			if led and led:IsA("BasePart") then
				local base = led.Color
				task.spawn(function()
					while led.Parent do
						task.wait(rng:NextNumber(2, 7))
						for _ = 1, rng:NextInteger(1, 4) do
							led.Color = Color3.fromRGB(30, 50, 46)
							task.wait(rng:NextNumber(0.05, 0.12))
							led.Color = base
							task.wait(rng:NextNumber(0.06, 0.2))
						end
					end
				end)
			end
		end
	end

	-- часы на мониторах
	local clocks: {{label: TextLabel, before: string, after: string}} = {}
	for _, l in office:GetDescendants() do
		if l:IsA("TextLabel") and l:FindFirstAncestorWhichIsA("SurfaceGui") then
			local a, b = string.find(l.Text, "%d%d:%d%d")
			if a and b and (l.Text:match("^%a") or #l.Text > 8) and not string.find(l.Text, "%d%d:%d%d:") then
				table.insert(clocks, {label = l, before = string.sub(l.Text, 1, a - 1), after = string.sub(l.Text, b + 1)})
			end
		end
	end
	if #clocks > 0 then
		task.spawn(function()
			local minute = 10 * 60 + 10
			while true do
				task.wait(10)
				minute = (minute + 1) % (24 * 60)
				local stamp = string.format("%02d:%02d", math.floor(minute / 60), minute % 60)
				for _, c in clocks do
					if c.label.Parent and not c.label:GetAttribute("KonturLocked") then
						c.label.Text = c.before .. stamp .. c.after
					end
				end
			end
		end)
	end
	office:SetAttribute("LiveClocks", #clocks)
end

return attachLiveDetails
