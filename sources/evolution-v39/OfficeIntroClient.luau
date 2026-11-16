-- v43 вступительное окно: при заходе показывает короткую инструкцию (что делать, как отвечать, что бывает при ошибке).
-- Закрывается кнопкой «НАЧАТЬ» (или Enter / пробелом); потом остаётся маленькая кнопка «?» слева снизу, чтобы открыть снова.
-- Только интерфейс: ни на что в раундах не влияет, ничего не отправляет на сервер.
do
	local Players = game:GetService("Players")
	local TweenService = game:GetService("TweenService")
	local ContextActionService = game:GetService("ContextActionService")
	local UserInputService = game:GetService("UserInputService")
	local player = Players.LocalPlayer
	local gui = Instance.new("ScreenGui")
	gui.Name = "KonturIntro"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = 100
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	local ACCENT = Color3.fromRGB(114, 229, 208)
	local PANEL = Color3.fromRGB(17, 30, 36)
	local TEXT = Color3.fromRGB(214, 232, 232)
	local DIM = Color3.fromRGB(150, 178, 180)
	local RED = Color3.fromRGB(255, 96, 84)
	local GREEN = Color3.fromRGB(86, 224, 132)

	-- вся тёмная подложка кнопка: нажатие в любом месте закрывает окно; Modal освобождает курсор, даже если игра держит его в центре
	-- (камера от первого лица); иначе нажать «НАЧАТЬ» было бы нечем
	local dim = Instance.new("TextButton")
	dim.Name = "Dim"
	dim.Text = ""
	dim.AutoButtonColor = false
	dim.Modal = true
	dim.Size = UDim2.fromScale(1, 1)
	dim.BackgroundColor3 = Color3.fromRGB(4, 10, 14)
	dim.BackgroundTransparency = 1
	dim.BorderSizePixel = 0
	dim.Visible = false
	dim.Parent = gui

	local card = Instance.new("Frame")
	card.Name = "Card"
	card.AnchorPoint = Vector2.new(0.5, 0.5)
	card.Position = UDim2.fromScale(0.5, 0.5)
	card.Size = UDim2.fromOffset(640, 470)
	card.BackgroundColor3 = PANEL
	card.BorderSizePixel = 0
	card.Parent = dim
	local scale = Instance.new("UIScale")
	scale.Parent = card
	local function fit()
		local view = gui.AbsoluteSize
		scale.Scale = math.clamp(math.min(view.X / 700, view.Y / 540), 0.5, 1.15)
	end
	gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
	local cardCorner = Instance.new("UICorner")
	cardCorner.CornerRadius = UDim.new(0, 18)
	cardCorner.Parent = card
	local stroke = Instance.new("UIStroke")
	stroke.Color = ACCENT
	stroke.Transparency = 0.55
	stroke.Thickness = 1.5
	stroke.Parent = card
	local glow = Instance.new("UIGradient")
	glow.Rotation = 90
	glow.Color = ColorSequence.new({ColorSequenceKeypoint.new(0, Color3.fromRGB(26, 52, 60)), ColorSequenceKeypoint.new(1, Color3.fromRGB(12, 22, 28))})
	glow.Parent = card

	local function label(parent: Instance, text: string, y: number, h: number, size: number, color: Color3, font: Enum.Font, x: number?, w: number?): TextLabel
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.Position = UDim2.new(0, x or 36, 0, y)
		t.Size = UDim2.new(0, w or 568, 0, h)
		t.Font = font
		t.Text = text
		t.TextSize = size
		t.TextColor3 = color
		t.TextXAlignment = Enum.TextXAlignment.Left
		t.TextYAlignment = Enum.TextYAlignment.Top
		t.TextWrapped = true
		t.RichText = true
		t.Parent = parent
		return t
	end

	local tag = label(card, "КОНТУР  /  ПОЛЕВОЙ ШТАБ 07", 26, 20, 15, ACCENT, Enum.Font.GothamMedium)
	tag.TextTransparency = 0.1
	label(card, "Найдите аномалию в офисе", 50, 44, 32, TEXT, Enum.Font.GothamBold)
	local rule = Instance.new("Frame")
	rule.Position = UDim2.new(0, 36, 0, 104)
	rule.Size = UDim2.new(0, 568, 0, 2)
	rule.BackgroundColor3 = ACCENT
	rule.BackgroundTransparency = 0.7
	rule.BorderSizePixel = 0
	rule.Parent = card

	local steps = {
		{"1", ACCENT, "Запомните офис", "Пройдите по комнатам и осмотритесь. Что-то может измениться: предмет, звук, свет."},
		{"2", ACCENT, "Вернитесь к постам", "В стартовой комнате два поста. <font color=\"#ff6054\"><b>Красный (E)</b></font>: аномалия есть. <font color=\"#56e084\"><b>Зелёный (F)</b></font>: всё как было."},
		{"3", ACCENT, "Верный ответ ведёт дальше", "Ошибка или гибель возвращает на <b>1-й уровень</b>. Чем выше уровень, тем тише аномалии."},
	}
	local y = 124
	for _, s in steps do
		local badge = Instance.new("Frame")
		badge.Position = UDim2.new(0, 36, 0, y + 2)
		badge.Size = UDim2.fromOffset(40, 40)
		badge.BackgroundColor3 = Color3.fromRGB(24, 62, 66)
		badge.BorderSizePixel = 0
		badge.Parent = card
		local bc = Instance.new("UICorner")
		bc.CornerRadius = UDim.new(1, 0)
		bc.Parent = badge
		local bs = Instance.new("UIStroke")
		bs.Color = ACCENT
		bs.Transparency = 0.4
		bs.Parent = badge
		local num = label(badge, s[1], 0, 40, 22, ACCENT, Enum.Font.GothamBold, 0, 40)
		num.TextXAlignment = Enum.TextXAlignment.Center
		num.TextYAlignment = Enum.TextYAlignment.Center
		label(card, s[3], y, 24, 20, TEXT, Enum.Font.GothamBold, 92, 512)
		label(card, s[4], y + 26, 56, 15, DIM, Enum.Font.GothamMedium, 92, 512)
		y += 92
	end

	local button = Instance.new("TextButton")
	button.Name = "Start"
	button.AnchorPoint = Vector2.new(0.5, 1)
	button.Position = UDim2.new(0.5, 0, 1, -26)
	button.Size = UDim2.fromOffset(250, 50)
	button.BackgroundColor3 = ACCENT
	button.TextColor3 = Color3.fromRGB(8, 24, 28)
	button.Font = Enum.Font.GothamBold
	button.Text = "НАЧАТЬ"
	button.TextSize = 20
	button.AutoButtonColor = false
	button.Selectable = true
	button.Parent = card
	local btnCorner = Instance.new("UICorner")
	btnCorner.CornerRadius = UDim.new(0, 12)
	btnCorner.Parent = button
	local hint = label(card, "Закрыть: клик, Enter или пробел. Показать снова: кнопка «?» или клавиша H.", 0, 18, 12, DIM, Enum.Font.GothamMedium, 36, 568)
	hint.Position = UDim2.new(0, 36, 1, -92)
	hint.TextXAlignment = Enum.TextXAlignment.Center
	hint.TextTransparency = 0.25

	local help = Instance.new("TextButton")
	help.Name = "Help"
	help.AnchorPoint = Vector2.new(0, 1)
	help.Position = UDim2.new(0, 18, 1, -86)
	help.Size = UDim2.fromOffset(40, 40)
	help.BackgroundColor3 = PANEL
	help.BackgroundTransparency = 0.15
	help.TextColor3 = ACCENT
	help.Font = Enum.Font.GothamBold
	help.Text = "?"
	help.Name = "Help"
	help.TextSize = 22
	help.AutoButtonColor = true
	help.Visible = false
	help.Parent = gui
	local hc = Instance.new("UICorner")
	hc.CornerRadius = UDim.new(1, 0)
	hc.Parent = help
	local hs = Instance.new("UIStroke")
	hs.Color = ACCENT
	hs.Transparency = 0.5
	hs.Parent = help

	local open = false
	local bindKeys: (boolean) -> ()
	local function setOpen(on: boolean)
		if open == on then
			return
		end
		open = on
		bindKeys(on)
		if on then
			dim.Visible = true
			help.Visible = false
			dim.BackgroundTransparency = 1
			card.Position = UDim2.fromScale(0.5, 0.54)
			TweenService:Create(dim, TweenInfo.new(0.35), {BackgroundTransparency = 0.45}):Play()
			TweenService:Create(card, TweenInfo.new(0.45, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {Position = UDim2.fromScale(0.5, 0.5)}):Play()
		else
			local fade = TweenService:Create(dim, TweenInfo.new(0.25), {BackgroundTransparency = 1})
			TweenService:Create(card, TweenInfo.new(0.25, Enum.EasingStyle.Quad), {Position = UDim2.fromScale(0.5, 0.56)}):Play()
			fade:Play()
			fade.Completed:Connect(function()
				if not open then
					dim.Visible = false
					help.Visible = true
				end
			end)
		end
	end
	local closedRemote: Instance? = nil
	local reported = false
	local function reportClosed()
		if not reported then
			reported = true
			if closedRemote and closedRemote:IsA("RemoteEvent") then
				closedRemote:FireServer()
			end
		end
	end
	button.MouseButton1Click:Connect(function()
		setOpen(false)
		reportClosed()
	end)
	button.MouseEnter:Connect(function()
		button.BackgroundColor3 = Color3.fromRGB(150, 245, 226)
	end)
	button.MouseLeave:Connect(function()
		button.BackgroundColor3 = ACCENT
	end)
	help.MouseButton1Click:Connect(function()
		setOpen(true)
	end)
	-- повторный показ клавишей H (при камере от первого лица курсор спрятан, и нажать «?» нечем)
	UserInputService.InputBegan:Connect(function(input, processed)
		if not processed and input.KeyCode == Enum.KeyCode.H and not open then
			setOpen(true)
		end
	end)
	dim.MouseButton1Click:Connect(function()
		setOpen(false)
		reportClosed()
	end)
	-- клавиши закрытия перехватываются (Sink), чтобы пробел не заставлял персонажа прыгать, а Enter не открывал чат
	local function onKey(_: string, state: Enum.UserInputState): Enum.ContextActionResult
		if state == Enum.UserInputState.Begin and open then
			setOpen(false)
			reportClosed()
		end
		return Enum.ContextActionResult.Sink
	end
	bindKeys = function(on: boolean)
		if on then
			ContextActionService:BindActionAtPriority("KonturIntroClose", onKey, false, 3000, Enum.KeyCode.Return, Enum.KeyCode.Space, Enum.KeyCode.ButtonA, Enum.KeyCode.Escape)
		else
			ContextActionService:UnbindAction("KonturIntroClose")
		end
	end

	fit()
	gui.Parent = player:WaitForChild("PlayerGui")
	closedRemote = game:GetService("ReplicatedStorage"):WaitForChild("KonturIntroClosed", 10)
	-- ждём ответ сервера о том, видел ли игрок окно раньше (до 8 с); не удалось узнать: показываем
	local waited = 0
	while not player:GetAttribute("IntroReady") and waited < 8 do
		task.wait(0.25)
		waited += 0.25
	end
	if player:GetAttribute("IntroSeen") == true then
		reported = true
		help.Visible = true
	else
		task.wait(1)
		setOpen(true)
	end

	-- подсказка после первой ошибки за сессию
	task.spawn(function()
		local office = workspace:WaitForChild("OfficeMap", 60)
		local state = office and office:WaitForChild("AnomalyReportState", 60)
		local result = state and state:WaitForChild("ResultText", 60)
		if not (result and result:IsA("StringValue")) then
			return
		end
		local shown = false
		result.Changed:Connect(function(text: string)
			if shown or not string.find(text, "ОШИБКА", 1, true) then
				return
			end
			shown = true
			local toast = Instance.new("Frame")
			toast.Name = "ErrorHint"
			toast.AnchorPoint = Vector2.new(0.5, 0)
			toast.Position = UDim2.new(0.5, 0, 0, -160)
			toast.Size = UDim2.fromOffset(540, 132)
			toast.BackgroundColor3 = PANEL
			toast.BorderSizePixel = 0
			toast.Parent = gui
			local ts = Instance.new("UIScale")
			ts.Scale = math.clamp(math.min(gui.AbsoluteSize.X / 640, 1.1), 0.55, 1.1)
			ts.Parent = toast
			local tc = Instance.new("UICorner")
			tc.CornerRadius = UDim.new(0, 14)
			tc.Parent = toast
			local tstroke = Instance.new("UIStroke")
			tstroke.Color = RED
			tstroke.Transparency = 0.35
			tstroke.Thickness = 1.5
			tstroke.Parent = toast
			label(toast, "Ошибка: начинаем с 1-го уровня", 14, 24, 20, RED, Enum.Font.GothamBold, 22, 496)
			local body = "Запоминайте комнаты: предметы на столах, надписи, свет, звуки. Что-то из этого однажды изменится."
			label(toast, body, 46, 60, 15, TEXT, Enum.Font.GothamMedium, 22, 496)
			local ok = label(toast, "Понятно (Enter)", 104, 20, 13, ACCENT, Enum.Font.GothamBold, 22, 496)
			ok.TextXAlignment = Enum.TextXAlignment.Right
			local function dismiss()
				if toast.Parent then
					local tw = TweenService:Create(toast, TweenInfo.new(0.3, Enum.EasingStyle.Quad), {Position = UDim2.new(0.5, 0, 0, -170)})
					tw:Play()
					tw.Completed:Connect(function()
						toast:Destroy()
					end)
				end
			end
			TweenService:Create(toast, TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = UDim2.new(0.5, 0, 0, 90)}):Play()
			local conn
			conn = UserInputService.InputBegan:Connect(function(input, processed)
				if not processed and (input.KeyCode == Enum.KeyCode.Return or input.KeyCode == Enum.KeyCode.ButtonA) then
					conn:Disconnect()
					dismiss()
				end
			end)
			task.delay(14, function()
				if conn.Connected then
					conn:Disconnect()
				end
				dismiss()
			end)
		end)
	end)
end
