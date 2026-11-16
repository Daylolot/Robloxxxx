-- v43 клиентская часть «реагирующих» аномалий: сообщает серверу, смотрит ли игрок прямо на фигуру с тегом KonturWatch
-- и куда направлена камера. Сервер проверяет данные (тип, длина вектора, частота), сам считает видимость и использует их только
-- чтобы замирать/исчезать фигуре; ничего важного клиент не решает.
do
	local RS = game:GetService("ReplicatedStorage")
	local Run = game:GetService("RunService")
	task.spawn(function()
		local remote = RS:WaitForChild("KonturSync", 180)
		if not remote or not remote:IsA("RemoteEvent") then
			return
		end
		-- клиент присылает только направление камеры (раз в 0,25 с); «видит ли игрок фигуру» сервер вычисляет сам
		local acc = 0
		Run.Heartbeat:Connect(function(dt)
			acc += dt
			if acc < 0.25 then
				return
			end
			acc = 0
			local cam = workspace.CurrentCamera
			if cam then
				remote:FireServer(false, cam.CFrame.LookVector)
			end
		end)
	end)
end
