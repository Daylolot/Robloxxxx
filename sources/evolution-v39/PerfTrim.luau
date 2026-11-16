--!strict
-- v39 «обрезка» нагрузки: мелкие детали офиса (книги, ручки, винты, стопки бумаги) не отбрасывают тень
-- и не участвуют в запросах лучей. Выполняется один раз при старте сервера, до первого игрока,
-- поэтому клиенты получают уже итоговое состояние (разница не рассылается).
-- Блокирующие лучи и перекрытия крупных предметов (стены, столы, кнопки ответа) не затрагиваются.
local TINY = 0.6 -- диагональ габаритов, стад

local function trimTinyParts(office: Instance): (number, number)
	local all = office:GetDescendants()
	-- не трогаем части, к которым привязано взаимодействие
	local protected: {[Instance]: boolean} = {}
	local function protect(root: Instance)
		protected[root] = true
		if not root:IsA("BasePart") then
			for _, part in root:GetDescendants() do
				if part:IsA("BasePart") then
					protected[part] = true
				end
			end
		end
	end
	for _, item in all do
		if item:IsA("ProximityPrompt") or item:IsA("ClickDetector") then
			local parent = item.Parent
			if parent then
				protect(parent)
				local grand = parent.Parent
				if grand and not grand:IsA("Folder") and grand ~= office then
					protect(grand)
				end
			end
		end
	end
	local shadowOff, queryOff = 0, 0
	for _, item in all do
		if item:IsA("BasePart") and not protected[item] and item.Size.Magnitude < TINY then
			if item.CastShadow then
				item.CastShadow = false
				shadowOff += 1
			end
			if item.CanQuery and item.Transparency < 1 then
				item.CanQuery = false
				queryOff += 1
			end
		end
	end
	return shadowOff, queryOff
end

local function runPerfTrim()
	-- стартовое лобби FieldHub (спавн игроков) и офис OfficeMap
	local shadowTotal, queryTotal = 0, 0
	local started = os.clock()
	for _, name in {"FieldHub", "OfficeMap"} do
		local root = workspace:WaitForChild(name, 30)
		if root then
			local ok, shadowOff, queryOff = pcall(trimTinyParts, root)
			if ok then
				shadowTotal += shadowOff
				queryTotal += queryOff
				workspace:SetAttribute("KonturTrim" .. name .. "ShadowOff", shadowOff)
			else
				warn("KONTUR perf trim failed for " .. name .. ": " .. tostring(shadowOff))
			end
		end
	end
	workspace:SetAttribute("KonturTrimShadowOff", shadowTotal)
	workspace:SetAttribute("KonturTrimQueryOff", queryTotal)
	workspace:SetAttribute("KonturTrimSeconds", math.round((os.clock() - started) * 1000) / 1000)
end

runPerfTrim()
