-- Gaze is a local visual. A second player never overwrites this player's target.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local office = workspace:WaitForChild("OfficeMap")
local round = office:WaitForChild("AnomalyReportState")
local phase = round:WaitForChild("Phase")
local Scene = require(ReplicatedStorage:WaitForChild("CeilingWorkerScene"))

local DWELL = 1.5
local LOOK_RADIUS = 28
local HOLD = 1.25

local activeScene, start
local lookSince, untilTime, carry = nil, 0, 0
local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Exclude
ray.RespectCanCollide = true

local function visibility(origin, point)
    local delta = point - origin
    return workspace:Raycast(origin, delta, ray) == nil
end

RunService:BindToRenderStep("KonturCeilingWorker", Enum.RenderPriority.Camera.Value + 5, function(dt)
    local started = round:GetAttribute("CeilingWorkerStartedAt")
    local active = started and started > 0 and phase.Value == "Active" and player:GetAttribute("KonturZone") == "Office"
    if not active then
        if activeScene then
            activeScene:Destroy()
            activeScene, start = nil, nil
            lookSince, untilTime, carry = nil, 0, 0
        end
        return
    end
    if not activeScene or started ~= start then
        if activeScene then activeScene:Destroy() end
        activeScene = Scene.new(office)
        start = started
        lookSince, untilTime, carry = nil, 0, 0
    end

    carry += dt
    if carry < 1/40 then return end
    local tick = math.min(carry, .15)
    carry = 0
    local camera = workspace.CurrentCamera
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    local eye = character and character:FindFirstChild("Head")
    if not camera or not root or not eye then return end

    local now = workspace:GetServerTimeNow()
    local head = activeScene:GetLookPoint()
    local toHead = head - camera.CFrame.Position
    if toHead.Magnitude > 40 then
        lookSince, untilTime = nil, 0
        return
    end
    local onScreen = toHead.Magnitude > .01 and toHead.Magnitude <= LOOK_RADIUS
        and camera.CFrame.LookVector:Dot(toHead.Unit) >= .977
    ray.FilterDescendantsInstances = {character, activeScene.root, office:FindFirstChild("CeilingWorkerJumpGuard")}
    local watching = onScreen and visibility(camera.CFrame.Position, head)
    lookSince = watching and (lookSince or now) or nil
    if lookSince and now - lookSince >= DWELL then
        untilTime = now + HOLD
    end
    local looking = now < untilTime
    activeScene:SetLamp(round:GetAttribute("CeilingWorkerLampOn") ~= false)
    activeScene:Update(math.max(0,now-start), looking and eye.Position or nil, tick, root.Position)
    if RunService:IsStudio() and activeScene.root:GetAttribute("TrackingLocalPlayer") ~= looking then
        activeScene.root:SetAttribute("TrackingLocalPlayer", looking)
    end
end)
