local test=game:GetService("StudioTestService")
if test:GetTestArgs()~="PrinterCoop29" then return end
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
    assert(qa,"Printer QA not available")
    Players.PlayerAdded:Connect(function(player)print("PRINTER_COOP_JOIN "..player.Name) end)
    await(function()return replies.ready and next(replies.ready)end,"first client",45)
    test:AddPlayers(1)
    local list=await(function()
        local active=Players:GetPlayers()
        if #active~=2 or not replies.ready then return end
        for _,p in ipairs(active) do if not replies.ready[p] then return end end
        return active
    end,"two clients",70)
    table.sort(list,function(a,b)return a.UserId<b.UserId end)
    local a,b=list[1],list[2]
    save("players",{a.Name,b.Name})
    for _,p in ipairs(list) do p:SetAttribute("KonturZone","Office") end
    await(function()return state.Phase.Value=="Active" and state.Level.Value==1 end,"clean round",20)
    answer(a,"Clear",2)
    go(a,Vector3.new(1050,3.14,42))
    go(b,Vector3.new(1031,3.14,43))
    await(function()return printer:GetAttribute("WarningPhase")=="Ready"end,"print ready")
    task.wait(.65)
    compare("at_rest",request("rest",list,"sample"),168,.001,.001)

    local reader=request("physical_read",{a},"read")[1]
    local start=state:GetAttribute("PrinterPaperStartsAt")
    save("physical_read",{prompt=reader.enabled,startedByPrompt=start~=nil})
    if not start then
        assert(qa:Invoke(a,"Read"),"read refused")
        start=state:GetAttribute("PrinterPaperStartsAt")
    end
    assert(start and not qa:Invoke(a,"Read"),"duplicate changed countdown")
    compare("countdown",request("count",list,"sample",start-1.2),168,.001,.001)
    assert(state:GetAttribute("PrinterPaperStartsAt")==start)
    answer(b,"Clear",1)
    local clean=request("early_cancel",list,"sample",start+.75)
    compare("cancelled",clean,0,.001,.001)
    assert(not clean[1].startsAt,"cancelled countdown survived")
    assert(state.LastCorrect.Value==false)

    b:SetAttribute("KonturZone","Hub")
    go(b,Vector3.new(0,3.14,0))
    answer(a,"Clear",2)
    go(a,Vector3.new(1050,3.14,42))
    await(function()return printer:GetAttribute("WarningPhase")=="Ready"end,"second print")
    assert(qa:Invoke(a,"Read"),"second read refused")
    start=assert(state:GetAttribute("PrinterPaperStartsAt"))
    await(function()return workspace:GetServerTimeNow()>=start+1.35 end,"flight starts")
    local away=request("away",{b},"sample")[1]
    assert(away.count==0 and away.startsAt==start,"paper created in hub")
    go(b,Vector3.new(1031,3.14,44))
    b:SetAttribute("KonturZone","Office")
    compare("late_office_entry",request("late",list,"sample",start+4.3),168,.8,1)
    compare("levitation",request("float",list,"sample",start+12.2),168,.3,.7)
    compare("continuation",request("extended",list,"sample",start+15),168,.3,.7)
    task.wait(3)
    answer(b,"Anomaly")
    task.wait(.35)
    local done=request("completed",list,"sample")
    compare("cleared",done,0,.001,.001)
    assert(not done[1].startsAt and state.LastCorrect.Value and not printer:FindFirstChild("AnomalyPrintout"))
end
local ok,result=xpcall(check,debug.traceback)
local resultText=Http:JSONEncode({ok=ok,error=not ok and result or nil,report=report})
print("PRINTER_COOP_RESULT "..resultText)
test:EndTest(resultText)
