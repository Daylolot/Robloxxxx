-- The bake is embedded in the local place and loaded only in Studio.
local Portrait = {}
local AssetService = game:GetService("AssetService")
local portraitColors = {
    face=Color3.fromRGB(179,132,107), hands=Color3.fromRGB(181,134,110),
    shirt=Color3.fromRGB(217,214,201), trousers=Color3.fromRGB(47,49,53),
    hair=Color3.fromRGB(46,34,31), eyes=Color3.fromRGB(221,216,201),
    iris=Color3.fromRGB(43,51,48), tie=Color3.fromRGB(92,41,47),
}
local headGroups = {face=true,hair=true,eyes=true,iris=true}

local function decode(hex)
    return buffer.fromstring((hex:gsub("..",function(pair)
        return string.char(tonumber(pair,16))
    end)))
end

local function makeMesh(state,name,data,origin)
    local editable=assert(AssetService:CreateEditableMesh(),"Editable mesh budget exhausted")
    table.insert(state.editables,editable)
    local positions,normals,triangles=decode(data.vertices),decode(data.normals),decode(data.triangles)
    local ids,normalIds,points={},{},{}
    local colors=data.colors and decode(data.colors)
    local colorIds,palette={},{}
    for offset=0,buffer.len(positions)-1,6 do
        local index=offset/6+1
        local point=Vector3.new(buffer.readi16(positions,offset),buffer.readi16(positions,offset+2),
            buffer.readi16(positions,offset+4))*.0001
        points[index]=point
        ids[index]=editable:AddVertex(point)
        local at=(index-1)*3
        local normal=Vector3.new(buffer.readi8(normals,at),buffer.readi8(normals,at+1),buffer.readi8(normals,at+2))
        normalIds[index]=editable:AddNormal(normal.Magnitude>.1 and normal.Unit or Vector3.yAxis)
        if colors then
            local r,g,b=buffer.readu8(colors,at),buffer.readu8(colors,at+1),buffer.readu8(colors,at+2)
            local tone=r*1024+g*32+b
            if not palette[tone] then palette[tone]=editable:AddColor(Color3.new(r/31,g/31,b/31),1) end
            colorIds[index]=palette[tone]
        end
    end
    for offset=0,buffer.len(triangles)-1,6 do
        local a,b,c=buffer.readu16(triangles,offset)+1,buffer.readu16(triangles,offset+2)+1,
            buffer.readu16(triangles,offset+4)+1
        local face=editable:AddTriangle(ids[a],ids[b],ids[c])
        editable:SetFaceNormals(face,{normalIds[a],normalIds[b],normalIds[c]})
        if colors then editable:SetFaceColors(face,{colorIds[a],colorIds[b],colorIds[c]}) end
    end
    local part=AssetService:CreateMeshPartAsync(Content.fromObject(editable))
    part.Name="Anatomy / "..name
    part.Anchored=true
    part.CanCollide=false
    part.CanTouch=false
    part.CanQuery=false
    part.DoubleSided=true
    part.Material=Enum.Material.SmoothPlastic
    part.Color=colors and Color3.new(1,1,1) or portraitColors[name]
    part.CFrame=origin*CFrame.new(data.center)
    part.Parent=state.model
    state.meshes[name]={part=part,editable=editable,ids=ids,points=points,center=data.center,size=part.Size}
end

local function motion(encoded)
    local bytes=decode(encoded)
    local delta={}
    for offset=0,buffer.len(bytes)-1,8 do
        local index=buffer.readu16(bytes,offset)+1
        delta[index]=Vector3.new(buffer.readi16(bytes,offset+2),
            buffer.readi16(bytes,offset+4),buffer.readi16(bytes,offset+6))*.0001
    end
    return delta
end

function Portrait.destroy(state)
    state.model:Destroy()
    for _,mesh in state.editables do mesh:Destroy() end
end

function Portrait.build(origin)
    local state={
        model=Instance.new("Model"),editables={},meshes={},keys={},motions={},hits={},
        time=0,poseTime=0,head=CFrame.identity,activeVertices={},
    }
    state.model.Name="Anatomical ceiling worker"
    local ok,problem=pcall(function()
        for name,data in portraitData.meshes do makeMesh(state,name,data,origin) end
        local lastFrame=1
        local time=0
        for _,hit in portraitData.hits do
            time+=math.min(.28,(hit[1]-lastFrame)/24)
            table.insert(state.hits,{time=time,key=hit[2]})
            lastFrame=hit[1]
        end
        state.cycle=time+.32
        for key,encoded in portraitData.deltas do state.motions[key]=motion(encoded) end
        state.blink=motion(portraitData.blink)
        state.previousBlink=0
        for name,key in portraitData.keys do
            local part=Instance.new("Part")
            part.Name="Portrait / "..name
            part.Size=key.size
            part.CFrame=origin*CFrame.new(key.position)
            part.Anchored=true
            part.CanCollide=false
            part.CanTouch=false
            part.CanQuery=false
            part.Material=Enum.Material.SmoothPlastic
            part.Color=name=="Keyboard shell" and Color3.fromRGB(30,36,37) or Color3.fromRGB(214,207,187)
            part.Parent=state.model
            state.keys[name]=part
        end
    end)
    if not ok then
        Portrait.destroy(state)
        return nil,tostring(problem)
    end
    return state
end

local function smooth(value)
    local x=math.clamp(value,0,1)
    return x*x*(3-2*x)
end

function Portrait.update(state,origin,target,dt,activity)
    state.time=(state.time+dt*activity)%state.cycle
    state.poseTime+=dt
    local idle=state.poseTime
    local pitch=-.08+.024*math.sin(idle*2.1)
    local yaw=.055+.025*math.sin(idle*1.4)
    if target then
        local direction=origin:PointToObjectSpace(target)-portraitData.pivot
        if direction.Magnitude>.01 then
            local unit=direction.Unit
            yaw=math.clamp(math.atan2(-unit.X,-unit.Z),-.69,.69)
            pitch=math.clamp(math.asin(unit.Y),-.49,.49)
        end
    end
    local wanted=CFrame.Angles(0,yaw,0)*CFrame.Angles(pitch,0,.015*math.sin(idle*1.9))
    state.head=state.head:Lerp(wanted,1-math.exp(-dt*(target and 4 or 3)))
    local pivot=portraitData.pivot
    local motion=origin*CFrame.new(pivot)*state.head*CFrame.new(-pivot)
    for name in headGroups do
        local mesh=state.meshes[name]
        mesh.part.CFrame=motion*CFrame.new(mesh.center)
    end
    local phase=idle%6.35
    local blink=smooth((phase-2.64)/.075)*(1-smooth((phase-2.73)/.12))
    if blink~=state.previousBlink then
        local face=state.meshes.face
        for vertex,delta in state.blink do
            face.editable:SetPosition(face.ids[vertex],face.points[vertex]+delta*blink)
        end
        state.previousBlink=blink
    end
    local shirt=state.meshes.shirt
    local breath=math.sin(idle*1.72)
    shirt.part.Size=shirt.size*Vector3.new(1+.003*breath,1,1+.010*breath)

    local weights={}
    for _,hit in state.hits do
        local elapsed=state.time-hit.time
        if elapsed<-.12 then elapsed+=state.cycle end
        local amount=smooth((elapsed+.083)/.083)*(1-smooth((elapsed-.041)/.125))*activity
        if amount>.001 then weights[hit.key]=math.max(weights[hit.key] or 0,amount) end
    end
    local offsets={}
    for key,deltas in state.motions do
        local amount=weights[key] or 0
        local cap=portraitData.keys[key]
        state.keys[key].CFrame=origin*CFrame.new(cap.position-Vector3.yAxis*(.0025*2.64*amount))
        if amount>.001 then
            for vertex,delta in deltas do
                offsets[vertex]=(offsets[vertex] or Vector3.zero)+delta*amount
            end
        end
    end
    local hands=state.meshes.hands
    for vertex in state.activeVertices do
        if not offsets[vertex] then hands.editable:SetPosition(hands.ids[vertex],hands.points[vertex]) end
    end
    for vertex,delta in offsets do
        hands.editable:SetPosition(hands.ids[vertex],hands.points[vertex]+delta)
    end
    state.activeVertices=offsets
end
