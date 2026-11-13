-- KONTUR v37: watchdog. A round change normally takes a few seconds; if the state stays stuck, recover.
-- "Stuck" means: the phase is Transition/Preparing, or the phase says Active while the round logic is still in Transition
-- (finishRound failed before it could publish the transition).
task.spawn(function()
    local since:number?=nil
    local seen=""
    while true do
        task.wait(2)
        local phase=phaseValue.Value
        local stuck=phase=="Transition" or phase=="Preparing" or (phase=="Active" and modelState.phase=="Transition")
        -- Any change of round, revision or phase restarts the clock, so quick rounds never accumulate stuck time.
        local key=modelState.round..":"..modelState.revision..":"..phase..":"..modelState.phase
        if key~=seen then seen=key;since=nil end
        if stuck then
            since=since or os.clock()
            if os.clock()-since>Logic.TransitionDuration+25 then
                warn("KONTUR watchdog: round stuck in "..phase.."/"..modelState.phase..", opening a clean round")
                forceOpenRound()
                since=nil
            end
        else
            since=nil
        end
    end
end)
