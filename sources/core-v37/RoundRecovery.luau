-- KONTUR v37: safe recovery. If a round change throws or stalls, open a clean round instead of freezing the game.
-- roundEpoch makes a late, slow round change give up after the recovery has already opened a round.
local roundEpoch=0
local pendingRecord=nil
local function forceOpenRound()
    roundEpoch+=1
    local function try(label,fn)
        local ok,err=pcall(fn)
        if not ok then warn("KONTUR safe reset ("..label.."): "..tostring(err)) end
    end
    try("objects",function()officeObjects.activate(nil,nil)end)
    try("flood",function()flood:Stop()end)
    try("ceiling",function()ceiling:SetActive(false)end)
    try("mirror",function()state:SetAttribute("MirrorAnomalyRound",nil)end)
    try("printer",function()if printer then printer.activate(false)end end)
    try("lights",function()
        resetEvent:Fire()
        for v,on in pairs(lightStates)do if v.Parent then v.Value=on end end
    end)
    try("round",function()
        if modelState.phase=="Transition" and pendingRecord and Logic.BeginNextRound(modelState,pendingRecord) then
            -- The answer is honoured: level and round token advanced exactly as in a normal change.
        elseif modelState.phase=="Transition" or modelState.phase=="Preparing" then
            modelState.round+=1;modelState.busyUntil=0
        end
        pendingRecord=nil
    end)
    try("crew",returnCrew)
    try("state",function()
        Logic.Activate(modelState,false)
        local hasSubmitted=value("HasSubmitted");if hasSubmitted then hasSubmitted.Value=false end
        levelValue.Value=modelState.level
        local roundId=value("RoundId");if roundId then roundId.Value=modelState.round end
        resultValue.Value=""
        local accepting=value("AcceptingReports");if accepting then accepting.Value=true end
        refresh()
    end)
    -- Publish last, whatever failed above, so clients never see a stuck phase.
    phaseValue.Value="Active"
end
