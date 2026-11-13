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
    part.Anchored=true part.CanCollide=false part.CanTouch=false part.CanQuery=false
    part.DoubleSided=true part.Material=Enum.Material.SmoothPlastic part.Color=Color3.new(1,1,1)
    return part
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
                    local ok,part=pcall(build,spec)
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
end)
end
