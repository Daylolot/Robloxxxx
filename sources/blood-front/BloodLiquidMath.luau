-- Shared surface height for rendering and server contact; no crest or curl.
-- KONTUR v39F: in corridor-width channels the wave front bulges in the middle (it lags along the walls)
-- and wanders a little along its edge. FrontShift is the single definition used by this module and by
-- BloodLiquidSurface, so what is drawn and what the server tests for contact always agree.
local Data=require(script.Parent:WaitForChild('BloodLiquidData'))
local Topology=require(script.Parent:WaitForChild('BloodFloodTopology'))
local M={}
local CHANNEL_HALF_WIDTH=4.6 -- regions narrower than 9.2 studs without a fan are channels (corridors, doorways)
local CHANNEL_RAMP=6.0       -- long, gentle toe for channels (the original wave was a 2.5-stud wall)
local BULGE_MAX=2.0         -- most the front may lag at the walls (studs)
local BULGE_FRAC=.55        -- ... as a fraction of the channel half width
local LOBE_A=.4             -- slow lateral wander of the edge (studs)
local LOBE_B=.2             -- faster, smaller wander
local ROOM_RAMP=4.5          -- rooms: gentler than the original 2.5-stud toe
local SHIFT_RAMP=3          -- studs of travel over which the front shift grows in
-- The front (travel+shift) must keep moving forward at every lateral position, or a column would flicker wet/dry
-- and the server's contact test would step back. Worst case is the wall column just before the ramp ends.
assert(BULGE_MAX+LOBE_A+LOBE_B+SHIFT_RAMP*(.12*LOBE_A+.192*LOBE_B)<SHIFT_RAMP,'blood front shift too large')
function M.Ripple(x,z,t)
    return .53*math.sin(x*.25+z*.15-t*1.10)+.31*math.sin(x*.40-z*.27-t*1.70)+.16*math.sin(x*.90+z*.70-t*3.0)
end
-- Half width of a channel region, or nil when the region is a room or the source basin.
function M.ChannelHalfWidth(r)
    if (r.fan or 0)>0 or r.id=='Source' or r.id=='SourceEast' then return nil end
    local half=(r.axis=='X' and (r.z1-r.z0) or (r.x1-r.x0))/2
    if half<=0 or half>CHANNEL_HALF_WIDTH then return nil end
    return half
end
-- Front displacement for a channel of half width `half` whose lateral range starts at `lo`.
local function shiftOf(half,lo,lat,travel)
    if travel<=0 then return 0 end
    local w=(lat-(lo+half))/half
    local phase=travel*.12
    local bulge=-math.min(BULGE_MAX,half*BULGE_FRAC)*w*w
    local lobes=LOBE_A*math.sin(lat*1.15+phase)+LOBE_B*math.sin(lat*2-phase*1.6+1.7)
    return (bulge+lobes)*math.min(1,travel/SHIFT_RAMP)
end
-- How far (studs, along the flow) the front at lateral coordinate `lat` is moved from the straight line.
-- `travel` is the distance the straight front has covered; the shift grows in over the first SHIFT_RAMP studs.
function M.FrontShift(r,lat,travel)
    local half=M.ChannelHalfWidth(r)
    if not half then return 0 end
    return shiftOf(half,r.axis=='X' and r.z0 or r.x0,lat,travel)
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
        local travel=(now-r.start)*config.WaveSpeed
        -- Inlined channel test (this runs about 20 000 times per frame while the flood is on screen).
        local lat,lo,hi
        if r.axis=='X' then lat,lo,hi=z,r.z0,r.z1 else lat,lo,hi=x,r.x0,r.x1 end
        local half=(hi-lo)*.5
        local dist=Topology.Distance(r,x,z)
        -- The shift never exceeds LOBE_A+LOBE_B, so points further ahead than that are dry without evaluating it.
        if travel+LOBE_A+LOBE_B<=dist then return 0 end
        local ramp,shift=ROOM_RAMP,0
        if half>0 and half<=CHANNEL_HALF_WIDTH and (r.fan or 0)<=0 then ramp=CHANNEL_RAMP;shift=shiftOf(half,lo,lat,travel) end
        local depth=travel+shift-dist
        if depth<=0 then return 0 end
        local a=math.clamp(depth/ramp,0,1)
        h=level*a*a*(3-2*a)
    end
    if h<.035 then return 0 end
    return math.max(0,h+M.Ripple(x,z,now-started)*math.clamp(h,0,1))
end
return M
