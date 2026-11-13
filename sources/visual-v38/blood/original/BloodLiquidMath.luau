-- Shared surface height for rendering and server contact; no crest or curl.
local Data=require(script.Parent:WaitForChild('BloodLiquidData'))
local Topology=require(script.Parent:WaitForChild('BloodFloodTopology'))
local M={}
function M.Ripple(x,z,t)
    return .53*math.sin(x*.25+z*.15-t*1.10)+.31*math.sin(x*.40-z*.27-t*1.70)+.16*math.sin(x*.90+z*.70-t*3.0)
end
function M.Height(r,x,z,now,started,config)
    if not started or started<=0 then return 0 end
    local h
    local level=math.min(config.MaximumLevel,config.BodyHeight+math.max(0,now-started-config.RiseBeginsAt)*config.RiseRate)
    if r.id=='Source' or r.id=='SourceEast' then
        local elapsed=now-started
        local flow=elapsed-config.SourceBeginsAt
        if flow<=0 then return 0 end
        local duration=math.max(1,config.WarningSeconds-config.SourceBeginsAt)
        -- Fans start at the two visible wall outlets, then steadily spread sideways.
        local northDistance=z+31.65+.65*math.max(0,math.abs(x-1090.5)-4.5)
        local eastDistance=1095.65-x+.65*math.max(0,math.abs(z+25)-4)
        local depth=math.max(flow*57.975/duration-northDistance,flow*64.3/duration-eastDistance)
        if depth<=0 then return 0 end
        local a=math.clamp(depth/3.5,0,1)
        local physical=Data.Height(x,z,Data.Begin+flow*.6)
        local variation=math.clamp(physical-config.BodyHeight,-.3,.3)*math.clamp((-z-.35)/2,0,1)
        h=(level+variation)*a*a*(3-2*a)
    else
        local depth=(now-r.start)*config.WaveSpeed-Topology.Distance(r,x,z)
        if depth<=0 then return 0 end
        local a=math.clamp(depth/2.5,0,1)
        h=level*a*a*(3-2*a)
    end
    if h<.035 then return 0 end
    return math.max(0,h+M.Ripple(x,z,now-started)*math.clamp(h,0,1))
end
return M
