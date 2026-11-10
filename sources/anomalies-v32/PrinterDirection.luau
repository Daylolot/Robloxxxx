local function ease(t)
    t = math.clamp(t, 0, 1)
    return t*t*(3-2*t)
end

local contactPoses = {
    [17] = {Vector3.new(1020.36,5.335,47.60), 4.5, 1.16, .12, .43},
    [28] = {Vector3.new(1022.16,3.366,46.05), 5.55, 1.35, .009, .11},
    [43] = {Vector3.new(1048.1,.68,40), 10.2, .61, .15, .63},
}
local arcRanks = {[3]=1,[6]=2,[12]=3,[16]=4,[22]=5,[31]=6,[39]=7,[46]=8,[55]=9}
local rustleCues = {
    {1,"rbxassetid://9125724963",0,.33,1.16},
    {35,"rbxassetid://9117233449",.38,.28,1.14},
    {27,"rbxassetid://9125724963",.63,.29,.94},
    {17,"rbxassetid://9117233449",.77,.25,1.28},
    {8,"rbxassetid://9117233311",1.13,.32,1.12},
}

local function directPaper(index, age, base, curl, bow)
    local contact = contactPoses[index]
    if contact then
        local spot, start, hold, tilt, crease = table.unpack(contact)
        local weight = ease((age-start+1.30)/1.30)*(1-ease((age-start-hold)/1.45))
        if weight>0 then
            local slip = index==28 and .20*ease((age-start)/hold) or 0
            local landing = CFrame.new(spot+Vector3.new(slip,0,0))
                * CFrame.Angles(tilt+.027*math.sin(age*16),index==17 and math.pi or 0,0)
            base = base:Lerp(landing,weight)
            curl += (crease + .13*math.sin(age*20) - curl)*weight
            bow += (.24-bow)*weight
        end
    end
    local rank = arcRanks[index]
    if rank then
        local weight = ease((age-7.35-rank*.075)/1.35)*(1-ease((age-10.55-rank*.065)/1.25))
        if weight>0 then
            local a = (rank-5)*.17 + (age-9.1)*.063
            local position = Vector3.new(1033.3-6.7*(1-math.cos(a)), 7.5-.85*math.abs(a),
                36+11.4*math.sin(a))
            local arc = CFrame.new(position)*CFrame.Angles(.12*math.sin(age*5+rank),a+1.15,.19)
            base = base:Lerp(arc,weight)
            curl += (.36+.19*math.sin(age*7+rank)-curl)*weight
        end
    end
    return base,curl,bow
end
