-- KONTUR v37: inspection guard. One answer still moves the whole crew, but not in the very first seconds of a round.
-- Only a short time limit remains (no walking distance): it stops accidental and instant troll answers.
-- The constant is filled in by build_place.py (zero in QA builds so automated checks can answer at once).
local INSPECT_MIN_SECONDS=__INSPECT_MIN_SECONDS__
local roundActiveAt=os.clock()
local activeRound=modelState.round
local lastHint:{[number]:number}={}
phaseValue:GetPropertyChangedSignal("Value"):Connect(function()
    if phaseValue.Value=="Active" then roundActiveAt=os.clock();activeRound=modelState.round end
end)
-- Returns nil when enough time has passed, otherwise a short hint for the answer screen.
local function inspectionHint(player)
    -- A stale round token (the phase value has not caught up yet) counts as "too early".
    if activeRound~=modelState.round then return "ОСМОТРИТЕ ОФИС · РАУНД НАЧИНАЕТСЯ" end
    local left=INSPECT_MIN_SECONDS-(os.clock()-roundActiveAt)
    if left>0 then return "ОСМОТРИТЕ ОФИС · ЕЩЁ "..math.ceil(left).." С" end
    return nil
end
-- Sends a hint at most twice per second per player.
local function sendInspectionHint(player,hint,requestId)
    local now=os.clock()
    if now-(lastHint[player.UserId] or -math.huge)<.5 then return end
    lastHint[player.UserId]=now
    feedback:FireClient(player,hint,false,requestId,nil)
end
local function forgetInspection(player)
    lastHint[player.UserId]=nil
end
