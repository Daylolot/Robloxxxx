--!strict
-- v43 память вступительного окна: хранит в DataStore, что игрок уже видел инструкцию (ключ = UserId). Клиент ждёт атрибут IntroReady,
-- и если IntroSeen уже true, окно не показывается сразу (остаётся кнопка «?»). Закрытие окна клиент сообщает RemoteEvent'ом KonturIntroClosed.
-- Надёжность: чтение с повторами (pcall, до 3 попыток); если прочитать не удалось, окно просто показывается, а запись в хранилище
-- пропускается, чтобы не затереть данные. Запись тоже с повторами. Клиентскому сообщению доверяем только как «игрок закрыл окно» (флаг, не данные).
local function attachIntroMemory()
	local RS = game:GetService("ReplicatedStorage")
	local Players = game:GetService("Players")
	local DataStoreService = game:GetService("DataStoreService")
	local store: DataStore? = nil
	pcall(function()
		store = DataStoreService:GetDataStore("KonturIntro_v1")
	end)
	local remote = Instance.new("RemoteEvent")
	remote.Name = "KonturIntroClosed"
	remote.Parent = RS
	local readable: {[Player]: boolean} = {}
	local lastClose: {[Player]: number} = {}

	local function load(player: Player)
		local seen = false
		local ok = false
		if store then
			for attempt = 1, 3 do
				local success, value = pcall(function()
					return (store :: DataStore):GetAsync(tostring(player.UserId))
				end)
				if success then
					ok = true
					seen = value == true
					break
				end
				task.wait(2 * attempt)
			end
		end
		if player.Parent then
			readable[player] = ok
			player:SetAttribute("IntroSeen", seen)
			player:SetAttribute("IntroReady", true)
		end
	end
	Players.PlayerAdded:Connect(function(player)
		task.spawn(load, player)
	end)
	for _, player in Players:GetPlayers() do
		task.spawn(load, player)
	end
	Players.PlayerRemoving:Connect(function(player)
		readable[player] = nil
		lastClose[player] = nil
	end)
	remote.OnServerEvent:Connect(function(player: Player)
		local now = os.clock()
		if lastClose[player] and now - lastClose[player] < 5 then
			return
		end
		lastClose[player] = now
		if player:GetAttribute("IntroSeen") == true then
			return
		end
		player:SetAttribute("IntroSeen", true)
		if store and readable[player] then
			task.spawn(function()
				for attempt = 1, 3 do
					local success = pcall(function()
						(store :: DataStore):SetAsync(tostring(player.UserId), true)
					end)
					if success then
						return
					end
					task.wait(2 * attempt)
				end
			end)
		end
	end)
end

return attachIntroMemory
