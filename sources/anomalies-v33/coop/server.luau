local test=game:GetService("StudioTestService")
if test:GetTestArgs()~="OfficeCoop33" then return end
local Players=game:GetService("Players")
local Http=game:GetService("HttpService")
local office=workspace:WaitForChild("OfficeMap")
local state=office:WaitForChild("AnomalyReportState")
local printer=office.Rooms.CENTER.Printer
local qa=game.ServerStorage:WaitForChild("PrinterLocalQA",35)
local channel=Instance.new("RemoteEvent")
channel.Name="PrinterCoopProbe"
channel.Parent=game.ReplicatedStorage
local replies={}
channel.OnServerEvent:Connect(function(player,id,value)
    replies[id]=replies[id] or {}
    replies[id][player]=value
    if id=="ready" then player:SetAttribute("PrinterProbeReady",true) end
end)
local report={}
local function save(name,data)
    report[name]=data
    print("PRINTER_COOP "..name.." "..Http:JSONEncode(data))
end
local function await(condition,name,limit)
    local deadline=os.clock()+(limit or 10)
    repeat
        local result=condition()
        if result then return result end
        task.wait(.035)
    until os.clock()>=deadline
    error("Timeout: "..name)
end
local function request(id,list,action,at)
    for _,p in ipairs(list) do channel:FireClient(p,id,action,at) end
    local found=await(function()
        local response=replies[id]
        if not response then return end
        for _,p in ipairs(list) do if not response[p] then return end end
        return response
    end,id,16)
    local data={}
    for _,p in ipairs(list) do
        local item=found[p]
        assert(item.ok,item.error or id)
        table.insert(data,item.data)
    end
    replies[id]=nil
    return data
end
local function go(p,position)
    local char=await(function() return p.Character and p.Character:FindFirstChild("HumanoidRootPart") and p.Character end,"character")
    char:PivotTo(CFrame.new(position))
    char.HumanoidRootPart.AssemblyLinearVelocity=Vector3.zero
end
local function answer(player,choice,level)
    local start=office.Rooms.StartRoom
    local station=start.V09_0276_ReportStation
    local button=station["ReportButton_"..choice]
    local query=RaycastParams.new()
    query.FilterType=Enum.RaycastFilterType.Exclude
    query.FilterDescendantsInstances={player.Character,station,start.V09_0278_ShiftStatusBoard}
    local origin=button.Position
    for i=0,15 do
        local angle=i*math.pi/8
        local position=Vector3.new(origin.X+3*math.cos(angle),3.14,origin.Z+3*math.sin(angle))
        local eye=position+Vector3.yAxis*1.5
        if not workspace:Raycast(eye,origin-eye,query) then
            go(player,position)
            local revision=state.Revision.Value
            qa:Invoke(player,choice)
            await(function()return state.Revision.Value>revision end,"accepted report")
            if level then
                await(function() return state.Phase.Value=="Active" and state.Level.Value==level end,"round")
            end
            return
        end
    end
    error("No clear report position")
end
local function compare(id,data,expected,limit,rotationLimit)
    local a,b=table.unpack(data)
    local distance,normal=0,0
    assert(a.count==expected and b.count==expected,id.." count")
    assert(a.startsAt==b.startsAt and a.round==b.round,id.." shared time or round")
    for i,v in ipairs(a.rows) do
        local w=b.rows[i]
        distance=math.max(distance,Vector3.new(v[1]-w[1],v[2]-w[2],v[3]-w[3]).Magnitude)
        normal=math.max(normal,Vector3.new(v[4]-w[4],v[5]-w[5],v[6]-w[6]).Magnitude)
    end
    save(id,{segments=expected,clockDelta=math.abs(a.clock-b.clock),maxPositionDelta=distance,
        maxNormalDelta=normal,start=a.startsAt,level=a.level,round=a.round})
    assert(distance<=limit and normal<=rotationLimit,id.." diverged")
end
local function check()
    assert(qa,"QA unavailable")
    await(function()return replies.ready and next(replies.ready)end,"first client",48)
    task.wait(5)
    test:AddPlayers(1)
    local list=await(function()
        local active=Players:GetPlayers()
        if #active~=2 or not replies.ready then return end
        for _,p in ipairs(active) do if not replies.ready[p] then return end end
        return active
    end,"two clients",60)
    table.sort(list,function(a,b)return a.UserId<b.UserId end)
    local a,b=list[1],list[2]
    save("players",#list)
    for _,p in ipairs(list) do p:SetAttribute("KonturZone","Office") end
    await(function()return state.Phase.Value=="Active" and state.Level.Value==1 end,"clean round",20)
    state:SetAttribute("OfficeQANext","Printer")
    answer(a,"Clear",2)
    go(a,Vector3.new(1050,3.14,42))
    go(b,Vector3.new(988,3.14,64))
    await(function()return printer:GetAttribute("WarningPhase")=="Ready"end,"print ready")
    assert(qa:Invoke(a,"Read"),"read refused")
    local start=state:GetAttribute("PrinterPaperStartsAt")
    local far=request("printer_far",{b},"sample",start+1.2)[1]
    assert(far.count==0,"paper simulation ran from the arrival room")
    save("printer_far",{segments=far.count})
    go(a,Vector3.new(1033,3.14,38))
    go(b,Vector3.new(1029.5,3.14,44))
    compare("printer_reentry",request("flight",list,"sample",start+4.1),240,.85,1.2)
    compare("printer_arc",request("arc",list,"sample",start+9.35),240,.45,.9)
    state:SetAttribute("OfficeQANext","ArchiveWriting")
    answer(b,"Anomaly",3)
    task.wait(.75)
    go(a,Vector3.new(1026.9,3.14,-16.6))
    go(b,Vector3.new(1027.8,3.14,-18.25))
    local read=request("archive_read",list,"archive_read")
    assert(read[1].stage=="Read" and read[2].stage=="Read","both players must read")
    local down=request("archive_down",{a},"archive_down")[1]
    assert(down.stage=="Read","down triggered the change")
    local turn=request("archive_turn",{a},"archive_turn")[1]
    local stays=request("archive_other",{b},"archive_state")[1]
    assert(turn.stage=="Changed" and stays.stage=="Read","views are not independent")
    save("archive",{a=turn.stage,b=stays.stage,lookDown=down.stage})
    state:SetAttribute("OfficeQANext","GreenVent")
    answer(a,"Anomaly",4)
    task.wait(.75)
    go(a,Vector3.new(1004,3.14,46.7))
    go(b,Vector3.new(1085,3.14,48))
    local absent=request("vent_far",{b},"vent_far")[1]
    save("vent_far",absent)
    assert(not absent.exists,"vent particles in far wing")
    go(b,Vector3.new(1004,3.14,43.9))
    local epoch=state:GetAttribute("OfficeDetailStartedAt")
    local nextCycle=math.floor((workspace:GetServerTimeNow()-epoch)/7.3)+1
    local samples=request("vent_pressure",list,"vent",epoch+7.3*nextCycle+1.93)
    assert(samples[1].exists and samples[2].exists,"vent missing after entry")
    assert(samples[1].rate>24 and math.abs(samples[1].rate-samples[2].rate)<2,"pressure timing disagrees")
    assert(math.abs(samples[1].angle-samples[2].angle)<.002,"hinge differs")
    save("vent",{rateA=samples[1].rate,rateB=samples[2].rate,angle=samples[1].angle})
    answer(b,"Clear",1)
    local done=request("reset",list,"vent")
    assert(not done[1].exists and not done[2].exists,"effects survived reset")
    assert(math.abs(done[1].angle)<.001 and math.abs(done[2].angle)<.001,"hinge not closed")
    save("reset",{level=state.Level.Value})
end
local ok,result=xpcall(check,debug.traceback)
test:EndTest(Http:JSONEncode({ok=ok,error=not ok and result or nil,report=report}))
