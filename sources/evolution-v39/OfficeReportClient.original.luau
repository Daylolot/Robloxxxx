-- Station-only reporting. Temporary level announcement, no portable report menu.
local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local Run=game:GetService("RunService")
local Prompts=game:GetService("ProximityPromptService")
local GuiService=game:GetService("GuiService")
local Actions=game:GetService("ContextActionService")
local TweenService=game:GetService("TweenService")
local player=Players.LocalPlayer
local state=workspace:WaitForChild("OfficeMap"):WaitForChild("AnomalyReportState")
local level=state:WaitForChild("Level")
local phase=state:WaitForChild("Phase")
local result=state:WaitForChild("ResultText")
local correct=state:WaitForChild("LastCorrect")
local gui=Instance.new("ScreenGui")
gui.Name="KonturOfficeReports";gui.ResetOnSpawn=false;gui.DisplayOrder=50
gui.Parent=player:WaitForChild("PlayerGui")

local toast=Instance.new("TextLabel")
toast.Name="ReportFeedback";toast.AnchorPoint=Vector2.new(.5,0)
toast.Position=UDim2.fromScale(.5,.13);toast.Size=UDim2.new(.86,0,0,68)
toast.BackgroundColor3=Color3.fromRGB(17,37,43);toast.BorderSizePixel=0
toast.TextColor3=Color3.fromRGB(210,242,234);toast.TextSize=22
toast.Font=Enum.Font.SourceSansBold;toast.TextWrapped=true;toast.Visible=false;toast.Parent=gui
local max=Instance.new("UISizeConstraint");max.MaxSize=Vector2.new(850,90);max.Parent=toast
local toastEpoch=0
RS:WaitForChild("ReportFeedback").OnClientEvent:Connect(function(message,accepted,_,wasCorrect)
    toastEpoch+=1;local epoch=toastEpoch
    toast.Text=tostring(message)
    local positive=wasCorrect;if positive==nil then positive=accepted end
    toast.TextColor3=positive and Color3.fromRGB(128,220,187) or Color3.fromRGB(240,162,133)
    toast.Visible=phase.Value=="Active"
    task.delay(3.5,function()if epoch==toastEpoch then toast.Visible=false end end)
end)

local transition=Instance.new("TextButton")
transition.Name="LevelTransition";transition.Text="";transition.Size=UDim2.fromScale(1,1)
transition.BackgroundColor3=Color3.fromRGB(5,12,17);transition.BackgroundTransparency=.08
transition.BorderSizePixel=0;transition.AutoButtonColor=false;transition.Active=true
transition.Modal=true;transition.Visible=false;transition.ZIndex=100;transition.Parent=gui
local resultLabel=Instance.new("TextLabel")
resultLabel.Name="Result";resultLabel.BackgroundTransparency=1;resultLabel.Position=UDim2.fromScale(.08,.32)
resultLabel.Size=UDim2.fromScale(.84,.2);resultLabel.TextWrapped=true;resultLabel.TextScaled=true
resultLabel.Font=Enum.Font.SourceSansBold;resultLabel.ZIndex=101;resultLabel.Parent=transition
local limit=Instance.new("UITextSizeConstraint");limit.MinTextSize=20;limit.MaxTextSize=42;limit.Parent=resultLabel
local transitionHint=Instance.new("TextLabel")
transitionHint.Name="Hint";transitionHint.BackgroundTransparency=1;transitionHint.Position=UDim2.fromScale(.1,.55)
transitionHint.Size=UDim2.fromScale(.8,.12);transitionHint.Text="Возвращаемся в приёмную…"
transitionHint.TextWrapped=true;transitionHint.TextColor3=Color3.fromRGB(190,212,216)
transitionHint.Font=Enum.Font.SourceSans;transitionHint.TextSize=24;transitionHint.ZIndex=101;transitionHint.Parent=transition

local announcement=Instance.new("CanvasGroup")
announcement.Name="LevelAnnouncement";announcement.AnchorPoint=Vector2.new(.5,.5)
announcement.Position=UDim2.fromScale(.5,.45);announcement.Size=UDim2.new(.84,0,.18,0)
announcement.BackgroundTransparency=1;announcement.Visible=false;announcement.GroupTransparency=1
announcement.ZIndex=90;announcement.Parent=gui
local number=Instance.new("TextLabel")
number.Name="Level";number.BackgroundTransparency=1;number.Size=UDim2.fromScale(1,.65)
number.TextScaled=true;number.Font=Enum.Font.SourceSansBold;number.TextColor3=Color3.fromRGB(180,241,226)
number.TextStrokeColor3=Color3.fromRGB(9,26,29);number.TextStrokeTransparency=.35;number.ZIndex=91;number.Parent=announcement
local ns=Instance.new("UITextSizeConstraint");ns.MinTextSize=28;ns.MaxTextSize=64;ns.Parent=number
local caption=Instance.new("TextLabel")
caption.Name="Hint";caption.BackgroundTransparency=1;caption.Position=UDim2.fromScale(0,.68)
caption.Size=UDim2.fromScale(1,.32);caption.Text="Осмотрите офис и вернитесь к двум кнопкам"
caption.Font=Enum.Font.SourceSansSemibold;caption.TextSize=20;caption.TextWrapped=true
caption.TextColor3=Color3.fromRGB(225,239,235);caption.TextStrokeTransparency=.5;caption.ZIndex=91;caption.Parent=announcement
local announceEpoch=0
local announceTween
local function hideAnnouncement()
    announceEpoch+=1
    if announceTween then announceTween:Cancel();announceTween=nil end
    announcement.Visible=false;announcement.GroupTransparency=1
end
local function announce()
    hideAnnouncement();local epoch=announceEpoch
    number.Text="УРОВЕНЬ "..level.Value
    announcement.Position=UDim2.fromScale(.5,.45);announcement.Visible=true
    announceTween=TweenService:Create(announcement,TweenInfo.new(.35,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),{GroupTransparency=0})
    announceTween:Play()
    task.delay(1.8,function()
        if epoch~=announceEpoch then return end
        announceTween=TweenService:Create(announcement,TweenInfo.new(1.1,Enum.EasingStyle.Quad,Enum.EasingDirection.In),{GroupTransparency=1,Position=UDim2.fromScale(.5,.42)})
        announceTween:Play()
        task.delay(1.15,function()if epoch==announceEpoch then announcement.Visible=false end end)
    end)
end
local pausedPrompts,lastRound
local round=state:WaitForChild("RoundId")
local function refresh()
    local inOffice=player:GetAttribute("KonturZone")=="Office"
    local waiting=inOffice and phase.Value~="Active"
    if waiting then
        hideAnnouncement();toast.Visible=false
        if pausedPrompts==nil then
            pausedPrompts=Prompts.Enabled;Prompts.Enabled=false
            Actions:BindActionAtPriority("KonturLevelPause",function()return Enum.ContextActionResult.Sink end,
                false,3000,Enum.KeyCode.E,Enum.KeyCode.F,table.unpack(Enum.PlayerActions:GetEnumItems()))
        end
        resultLabel.Text=result.Value~="" and result.Value or "ПОДГОТОВКА ОФИСА"
        resultLabel.TextColor3=correct.Value and Color3.fromRGB(128,220,187) or Color3.fromRGB(240,162,133)
    elseif pausedPrompts~=nil then
        Prompts.Enabled=pausedPrompts;pausedPrompts=nil;Actions:UnbindAction("KonturLevelPause")
    end
    transition.Visible=waiting
    if not inOffice then lastRound=nil;hideAnnouncement();toast.Visible=false
    elseif not waiting and lastRound~=round.Value then lastRound=round.Value;announce() end
end
phase.Changed:Connect(refresh);result.Changed:Connect(refresh);correct.Changed:Connect(refresh)
player:GetAttributeChangedSignal("KonturZone"):Connect(refresh)
player.CharacterAdded:Connect(function()lastRound=nil;task.defer(refresh)end)
Run:BindToRenderStep("KonturLevelPause",Enum.RenderPriority.Input.Value+1,function()
    local tl,br=GuiService:GetGuiInset()
    transition.Position=UDim2.fromOffset(-tl.X,-tl.Y)
    transition.Size=UDim2.new(1,tl.X+br.X,1,tl.Y+br.Y)
    if transition.Visible then
        local h=player.Character and player.Character:FindFirstChildOfClass("Humanoid")
        if h then h:Move(Vector3.zero,false);h.Jump=false end
    end
end)
refresh()

