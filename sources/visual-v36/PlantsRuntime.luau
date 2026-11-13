-- KONTUR v36 plants: Blender-modelled meshes built locally as EditableMesh (no uploaded assets). Client only.
do
local AssetService=game:GetService("AssetService")
local PLANTS=PLANT_DATA
local B64={} do
    local chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    for i=1,#chars do B64[chars:byte(i)]=i-1 end
end
local function decode(text)
    local out=buffer.create(math.floor(#text*3/4))
    local o=0
    for i=1,#text,4 do
        local a,b,c,d=B64[text:byte(i)] or 0,B64[text:byte(i+1)] or 0,B64[text:byte(i+2)],B64[text:byte(i+3)]
        local n=a*262144+b*4096+(c or 0)*64+(d or 0)
        if o<buffer.len(out) then buffer.writeu8(out,o,bit32.rshift(n,16)%256) o+=1 end
        if c and o<buffer.len(out) then buffer.writeu8(out,o,bit32.rshift(n,8)%256) o+=1 end
        if d and o<buffer.len(out) then buffer.writeu8(out,o,n%256) o+=1 end
    end
    return out
end
local function build(spec)
    local editable=AssetService:CreateEditableMesh()
    if not editable then return nil end
    local pos,nor,col,tri=decode(spec.v),decode(spec.n),decode(spec.c),decode(spec.t)
    local ids,nids,cids,palette={},{},{},{}
    for i=0,spec.nv-1 do
        ids[i+1]=editable:AddVertex(Vector3.new(buffer.readi16(pos,i*6),buffer.readi16(pos,i*6+2),buffer.readi16(pos,i*6+4))*.001)
        local n=Vector3.new(buffer.readi8(nor,i*3),buffer.readi8(nor,i*3+1),buffer.readi8(nor,i*3+2))
        nids[i+1]=editable:AddNormal(n.Magnitude>.1 and n.Unit or Vector3.yAxis)
        local r,g,b=buffer.readu8(col,i*3),buffer.readu8(col,i*3+1),buffer.readu8(col,i*3+2)
        local key=r*1024+g*32+b
        if not palette[key] then palette[key]=editable:AddColor(Color3.new(r/31,g/31,b/31),1) end
        cids[i+1]=palette[key]
    end
    for i=0,spec.nt-1 do
        local a,b,c=buffer.readu16(tri,i*6)+1,buffer.readu16(tri,i*6+2)+1,buffer.readu16(tri,i*6+4)+1
        local f=editable:AddTriangle(ids[a],ids[b],ids[c])
        editable:SetFaceNormals(f,{nids[a],nids[b],nids[c]})
        editable:SetFaceColors(f,{cids[a],cids[b],cids[c]})
    end
    local part=AssetService:CreateMeshPartAsync(Content.fromObject(editable))
    editable:Destroy() -- free the editable-mesh memory budget (the blood liquid needs it)
    part.Anchored=true part.CanCollide=false part.CanTouch=false part.CanQuery=false
    part.DoubleSided=true part.Material=Enum.Material.SmoothPlastic part.Color=Color3.new(1,1,1)
    return part
end
local templates={}
local function instance(key)
    local spec=PLANTS[key]
    if not templates[key] then templates[key]=build(spec) end
    local t=templates[key]
    if not t then error("no template "..key) end
    local c=t:Clone()
    if c.Size.Magnitude<0.01 then c:Destroy() return build(spec) end
    return c
end
task.spawn(function()
    local office=workspace:WaitForChild("OfficeMap",60)
    if not office then return end
    local folder=Instance.new("Folder") folder.Name="KonturV36Plants" folder.Parent=office
    local order={"fig","lily","monstera"}
    local scale={fig=1.0,lily=1.25,monstera=1.2}
    local done,index={},0
    local deadline=os.clock()+90
    local lastNew=os.clock()
    while os.clock()<deadline and (index<8 or os.clock()-lastNew<6) do
        for _,model in ipairs(office:GetDescendants()) do
            if model:IsA("Model") and model.Name:find("^RubberPlant_") and not done[model] then
                local hasParts=false
                for _,d in ipairs(model:GetDescendants()) do if d:IsA("BasePart") then hasParts=true break end end
                if hasParts then
                    done[model]=true index+=1 lastNew=os.clock()
                    local key=order[(index-1)%3+1]
                    local spec=PLANTS[key]
                    local cf=model:GetBoundingBox()
                    local ok,part=pcall(instance,key)
                    if ok and part then
                        local yaw=(index*137)%360
                        local s=scale[key]
                        part.Size=part.Size*s
                        part.CFrame=CFrame.new(cf.X,0.1,cf.Z)*CFrame.Angles(0,math.rad(yaw),0)*CFrame.new(spec.center*s)
                        part.Name="Plant_"..key.."_"..index
                        part.Parent=folder
                        for _,d in ipairs(model:GetDescendants()) do if d:IsA("BasePart") then d.LocalTransparencyModifier=1 end end
                    else
                        warn("KonturV36 plant failed: "..tostring(part))
                    end
                end
            end
        end
        task.wait(1)
    end

    -- decor from Blender meshes on furniture tops
    local placements={
        {names={"CoffeeTable"},key="vase",fx=0.28,fz=0,yaw=20},
        {names={"MeetingTable"},key="vase",fx=0.3,fz=0,yaw=40},
        {names={"SideTable"},key="vase",fx=0.0,fz=0,yaw=70},
        {names={"CoffeeTable"},key="openbook",fx=-0.2,fz=0.12,yaw=15},
        {names={"MeetingTable"},key="openbook",fx=-0.3,fz=0.18,yaw=-12},
        {names={"MeetingTable"},key="bookstack",fx=0.05,fz=-0.2,yaw=25},
        {names={"SideTable"},key="bookstack",fx=-0.25,fz=0,yaw=10},
        {names={"LowCabinet","SideCabinet","FileCabinet"},key="bookrow",fx=-0.15,fz=0,yaw=0},
        {names={"ReceptionDesk"},key="bookstack",fx=0.0,fz=0.1,yaw=-8},
    }
    local params=OverlapParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances={folder}
    local placed={}
    local vdeadline=os.clock()+60
    local count=0
    while os.clock()<vdeadline do
        local found=0
        for _,model in ipairs(office.Rooms:GetDescendants()) do
            if model:IsA("Model") then
                local n=model.Name:gsub("^V%d+_%d+_","")
                for pi,pl in ipairs(placements) do
                    if table.find(pl.names,n) and not (placed[model] and placed[model][pi]) then
                        local hasParts=false
                        for _,d in ipairs(model:GetDescendants()) do if d:IsA("BasePart") then hasParts=true break end end
                        if hasParts then
                            placed[model]=placed[model] or {} placed[model][pi]=true found+=1 count+=1
                            local cf,sz=model:GetBoundingBox()
                            local footprint=({vase=Vector3.new(0.9,2.0,0.9),openbook=Vector3.new(1.7,0.35,1.2),bookstack=Vector3.new(1.1,0.9,1.1),bookrow=Vector3.new(2.3,1.3,0.9)})[pl.key]
                            local chosen
                            for _,mul in ipairs({1,-1,0,0.5,-0.5}) do
                                local fxx=pl.fx*mul
                                local top0=cf*CFrame.new(sz.X*fxx,sz.Y/2,sz.Z*pl.fz)
                                local boxCf=CFrame.new(top0.Position+Vector3.new(0,footprint.Y/2+0.08,0))*(top0-top0.Position)
                                local blocked=false
                                for _,h in ipairs(workspace:GetPartBoundsInBox(boxCf,footprint,params)) do
                                    if h.Transparency<1 and not h:IsDescendantOf(model) then blocked=true break end
                                end
                                if not blocked then chosen=top0 break end
                            end
                            local ok,part
                            if chosen then ok,part=pcall(instance,pl.key) else ok,part=true,nil end
                            if ok and part then
                                local top=chosen
                                part.CFrame=CFrame.new(top.Position)*CFrame.Angles(0,math.atan2(-top.LookVector.X,-top.LookVector.Z)+math.rad(pl.yaw+count*7),0)*CFrame.new(PLANTS[pl.key].center)
                                part.Name=pl.key
                                part.Parent=folder
                            else warn("KonturV36 decor failed: "..tostring(part)) end
                        end
                    end
                end
            end
        end
        if found==0 and next(placed) then break end
        task.wait(1)
    end
    -- extra floor plants in free room corners (overlap-checked)
    local roomCorners={
        {x0=961.5,x1=1002.5,z0=8,z1=52,n=3},{x0=1006,x1=1058,z0=7,z1=59,n=3},{x0=1062,x1=1116,z0=8,z1=60,n=3},
        {x0=996,x1=1034,z0=-32,z1=0,n=2},{x0=1030,x1=1100,z0=-32,z1=0,n=3},{x0=974,x1=1002,z0=53.5,z1=76.5,n=1},
    }
    local params=OverlapParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances={folder}
    local order2={"monstera","fig","lily"}
    local extra=0
    for _,rc in ipairs(roomCorners) do
        local inset=2.7
        local cands={Vector2.new(rc.x0+inset,rc.z0+inset),Vector2.new(rc.x1-inset,rc.z0+inset),Vector2.new(rc.x0+inset,rc.z1-inset),Vector2.new(rc.x1-inset,rc.z1-inset)}
        local placedHere=0
        for _,c in ipairs(cands) do
            if placedHere>=rc.n then break end
            local hits=workspace:GetPartBoundsInBox(CFrame.new(c.X,3.2,c.Y),Vector3.new(3.2,4,3.2),params)
            local blocked=false
            for _,h in ipairs(hits) do if h.Transparency<1 then blocked=true break end end
            if not blocked then
                extra+=1 placedHere+=1
                local key=order2[(extra-1)%3+1]
                local ok,part=pcall(instance,key)
                if ok and part then
                    local s=({fig=1.0,lily=1.25,monstera=1.2})[key]
                    part.Size=part.Size*s
                    part.CFrame=CFrame.new(c.X,0.1,c.Y)*CFrame.Angles(0,math.rad((extra*53)%360),0)*CFrame.new(PLANTS[key].center*s)
                    part.Name="Plant_"..key.."_extra"..extra
                    part.Parent=folder
                end
            end
        end
    end
    -- redesigned printer shell (Blender): replaces the plain body and lid visually on this client
    task.spawn(function()
        local deadline=os.clock()+60
        while os.clock()<deadline do
            local printerModel=office.Rooms:FindFirstChild("CENTER") and office.Rooms.CENTER:FindFirstChild("Printer")
            local body=printerModel and printerModel:FindFirstChild("PrinterBody")
            if body then
                local ok,part=pcall(instance,"printer")
                if ok and part then
                    part.CFrame=body.CFrame*CFrame.new(PLANTS.printer.center)
                    part.Name="PrinterShell"
                    part.Parent=folder
                    body.LocalTransparencyModifier=1
                    local lid=printerModel:FindFirstChild("ScannerLid")
                    if lid then lid.LocalTransparencyModifier=1 end
                else warn("KonturV36 printer shell failed: "..tostring(part)) end
                return
            end
            task.wait(1)
        end
    end)
    -- ceiling worker's inverted desk and chair: same finish as the rest of the office (client-built model)
    task.spawn(function()
        local function restyle(ws)
            task.wait(1.5)
            for _,p in ipairs(ws:GetDescendants()) do
                if p:IsA("BasePart") then
                    local n=p.Name
                    if n=="Ceiling desk" then p.Color=Color3.fromRGB(214,186,146) p.Material=Enum.Material.Wood
                    elseif n=="Walnut edge" then p.Color=Color3.fromRGB(186,156,116) p.Material=Enum.Material.Wood
                    elseif n=="Steel desk leg" or n=="Ceiling mount" or n=="Cross rail" then p.Color=Color3.fromRGB(236,238,240) p.Material=Enum.Material.Metal
                    elseif n=="Seat cushion" or n=="Chair back" then p.Color=Color3.fromRGB(34,92,106) p.Material=Enum.Material.Leather end
                end
            end
        end
        for _,c in ipairs(office:GetChildren()) do if c.Name=="CeilingWorkstation" then task.spawn(restyle,c) end end
        office.ChildAdded:Connect(function(c) if c.Name=="CeilingWorkstation" then task.spawn(restyle,c) end end)
    end)
end)
end
