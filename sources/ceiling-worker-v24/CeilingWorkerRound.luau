-- The room interaction is authoritative. Each client's visual gaze is independent.
local Round = {}
Round.__index = Round
local deskProps = {
    BudgetMonitor = true, Keyboard = true, MouseAndMat = true, Calculator = true,
    V09_0103_DocumentStacks = true, V09_0104_OpenFolder = true, V09_0105_Pencils = true,
    V09_0106_Rulers = true, V09_0107_ErgoChair = true,
}

local function conceal(self, item)
    local properties
    if item:IsA("BasePart") then
        properties = {Transparency = 1, CanCollide = false, CanQuery = false, CanTouch = false}
    elseif item:IsA("SurfaceGui") or item:IsA("BillboardGui") or item:IsA("Light") then
        properties = {Enabled = false}
    elseif item:IsA("Decal") or item:IsA("Texture") then
        properties = {Transparency = 1}
    end
    if not properties or self.concealed[item] then return end
    local original = {}
    for property in properties do original[property] = item[property] end
    self.concealed[item] = original
    if item:IsA("BasePart") then item.CanCollide = false end
    for property, value in properties do item[property] = value end
end

function Round.new(office, state)
    local room = office.Rooms:FindFirstChild("CENTER")
    local self = setmetatable({
        office = office,
        state = state,
        available = room ~= nil and room:FindFirstChild("V09_0098_StraightDesk") ~= nil,
        room = room,
        concealed = {},
    }, Round)

    local lamp = room and room:FindFirstChild("V09_0440_SlimDeskLamp")
    local on = lamp and lamp:FindFirstChild("IsOn", true)
    local base = lamp and lamp:FindFirstChild("OvalDeskBase_Core", true)
    self.lamp = lamp
    if on and on:IsA("BoolValue") and base then
        self.lampOn = on
        on:GetPropertyChangedSignal("Value"):Connect(function()
            state:SetAttribute("CeilingWorkerLampOn", on.Value)
            -- The original fixture controller also reacts to IsOn.
            task.defer(function()
                if not self.active then return end
                for item in self.concealed do
                    if item:IsDescendantOf(lamp) then
                        if item:IsA("Light") then item.Enabled = false end
                        if item:IsA("BasePart") then item.Transparency = 1 end
                    end
                end
            end)
        end)
        local prompt = Instance.new("ProximityPrompt")
        prompt.Name = "CeilingAnomalyLampSwitch"
        prompt.ActionText = "Переключить"
        prompt.ObjectText = "Настольная лампа"
        prompt.MaxActivationDistance = 4
        prompt.RequiresLineOfSight = false
        prompt.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
        prompt.Enabled = false
        prompt.Parent = base
        self.lampSwitch = prompt
        prompt.Triggered:Connect(function(player)
            if not prompt.Enabled or player:GetAttribute("KonturZone") ~= "Office" then return end
            if state.Phase.Value ~= "Active" then return end
            local character = player.Character
            local root = character and character:FindFirstChild("HumanoidRootPart")
            local humanoid = character and character:FindFirstChildOfClass("Humanoid")
            if root and humanoid and humanoid.Health > 0 and (root.Position - base.Position).Magnitude <= 4.8 then
                on.Value = not on.Value
            end
        end)
    end
    return self
end

function Round:IsAvailable()
    return self.available
end

function Round:SetActive(active)
    if active == self.active then return end
    self.active = active
    if self.lampSwitch then self.lampSwitch.Enabled = active end
    if active and self.room then
        self.previousLampOn = self.lampOn and self.lampOn.Value
        for _, item in self.room:GetChildren() do
            if not deskProps[item.Name] or not item:IsA("PVInstance") then continue end
            local position = item:GetPivot().Position
            if math.abs(position.X - 1020) > 3.6 or position.Z < 41 or position.Z > 49 then continue end
            conceal(self, item)
            for _, descendant in item:GetDescendants() do conceal(self, descendant) end
        end
        if self.lamp then
            for _, item in self.lamp:GetDescendants() do
                if item:IsA("Light") or item:IsA("BasePart") and not item.Name:find("^OvalDeskBase") then
                    conceal(self, item)
                end
            end
        end
    else
        for item, properties in self.concealed do
            if not item.Parent then continue end
            for property, value in properties do item[property] = value end
        end
        table.clear(self.concealed)
        if self.lampOn and self.previousLampOn ~= nil then
            self.lampOn.Value = self.previousLampOn
            self.previousLampOn = nil
        end
    end
    self.state:SetAttribute("CeilingWorkerLampOn", not self.lampOn or self.lampOn.Value)
    if self.guard then
        self.guard:Destroy()
        self.guard = nil
    end
    if active then
        local guard = Instance.new("Part")
        guard.Name = "CeilingWorkerJumpGuard"
        guard.Anchored = true
        guard.Size = Vector3.new(1.13, .25, 1.02)
        guard.CFrame = CFrame.new(1021.64, 7.59, 45.87)
        guard.Transparency = 1
        guard.CanCollide = true
        guard.CanTouch = false
        guard.CanQuery = false
        guard.CastShadow = false
        guard.Parent = self.office
        self.guard = guard
    end
    self.state:SetAttribute("CeilingWorkerStartedAt", active and workspace:GetServerTimeNow() or 0)
end

return Round
