-- KONTUR v42: мебель из моделей Blender, клиентская часть. Сервер публикует данные в ReplicatedStorage.KonturHeroData
-- (OfficeDecor.luau) и тегирует модели декора атрибутами HeroKey/HeroCF. Клиент строит EditableMesh сам (серверный клиент не
-- рисует), ставит меши на модель и прячет запасные детали у себя (LocalTransparencyModifier). Если сборка меша не удалась,
-- остаётся запасной вид из деталей. Ассеты в Roblox не загружаются. Блок встраивается сборщиком в KonturScenePresentation.
do
local AssetService=game:GetService("AssetService")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local B64={}
do
    local chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    for i=1,#chars do B64[chars:byte(i)]=i-1 end
end
local function decode(text)
    local length=(#text//4)*3
    if text:sub(-1)=="=" then length-=1 end
    if text:sub(-2)=="==" then length-=1 end
    local out=buffer.create(length)
    local o=0
    for i=1,#text,4 do
        local a,b=B64[text:byte(i)] or 0,B64[text:byte(i+1)] or 0
        local c,d=B64[text:byte(i+2)],B64[text:byte(i+3)]
        local n=a*262144+b*4096+(c or 0)*64+(d or 0)
        if o<length then buffer.writeu8(out,o,(n//65536)%256) o+=1 end
        if c and o<length then buffer.writeu8(out,o,(n//256)%256) o+=1 end
        if d and o<length then buffer.writeu8(out,o,n%256) o+=1 end
    end
    return out
end
local LOOK={
    wood_dark={Enum.Material.Wood,0},wood_mid={Enum.Material.Wood,0},wood_light={Enum.Material.Wood,0},
    metal={Enum.Material.Metal,0},metal_dark={Enum.Material.Metal,0},brass={Enum.Material.Metal,0},
    glass_blue={Enum.Material.Glass,0.35},shade={Enum.Material.Neon,0.12}, -- ткань: гладкий пластик, зернистая текстура Fabric на таких размерах шумит

}
local data
local templates={}
local building={}
local ops=0
local function field(group,name)
    local pieces={}
    local i=1
    while true do
        local chunk=group:FindFirstChild(name..i)
        if not chunk then break end
        pieces[i]=chunk.Value
        i+=1
    end
    return table.concat(pieces)
end
local function buildTemplate(key)
    local item=data:FindFirstChild(key)
    if not item then return nil end
    local model=Instance.new("Model")
    model.Name="Hero_"..key
    local groups=item:GetChildren()
    table.sort(groups,function(a,b) return tonumber(a.Name)<tonumber(b.Name) end)
    for _,group in ipairs(groups) do
        local editable=AssetService:CreateEditableMesh()
        if not editable then model:Destroy() return nil end
        local pos,nor,col,tri=decode(field(group,"v")),decode(field(group,"n")),decode(field(group,"c")),decode(field(group,"t"))
        local nv,nt=group:GetAttribute("nv"),group:GetAttribute("nt")
        local vids,nids,cids,palette={},{},{},{}
        for i=0,nv-1 do
            vids[i+1]=editable:AddVertex(Vector3.new(buffer.readi16(pos,i*6),buffer.readi16(pos,i*6+2),buffer.readi16(pos,i*6+4))*0.001)
            local n=Vector3.new(buffer.readi8(nor,i*3),buffer.readi8(nor,i*3+1),buffer.readi8(nor,i*3+2))
            nids[i+1]=editable:AddNormal(n.Magnitude>0.1 and n.Unit or Vector3.yAxis)
            local packed=buffer.readu16(col,i*2)
            local cid=palette[packed]
            if not cid then
                cid=editable:AddColor(Color3.new(bit32.extract(packed,10,5)/31,bit32.extract(packed,5,5)/31,bit32.extract(packed,0,5)/31),1)
                palette[packed]=cid
            end
            cids[i+1]=cid
            ops+=1 if ops%5000==0 then task.wait() end
        end
        for i=0,nt-1 do
            local a,b,c=buffer.readu16(tri,i*6)+1,buffer.readu16(tri,i*6+2)+1,buffer.readu16(tri,i*6+4)+1
            local face=editable:AddTriangle(vids[a],vids[b],vids[c])
            editable:SetFaceNormals(face,{nids[a],nids[b],nids[c]})
            editable:SetFaceColors(face,{cids[a],cids[b],cids[c]})
            ops+=1 if ops%5000==0 then task.wait() end
        end
        local meshPart=AssetService:CreateMeshPartAsync(Content.fromObject(editable))
        -- editable не уничтожаем: после Destroy меш у MeshPart пропадает (проверено в Studio; и у оригинала, и у клонов)
        local mat=group:GetAttribute("mat")
        local look=LOOK[mat]
        meshPart.Name=mat
        meshPart.Anchored=true meshPart.CanCollide=false meshPart.CanTouch=false meshPart.CanQuery=false
        meshPart.Color=Color3.new(1,1,1)
        meshPart.DoubleSided=(mat=="shade" or mat=="leaf")
        meshPart.Material=look and look[1] or Enum.Material.SmoothPlastic
        meshPart.Transparency=look and look[2] or 0
        meshPart.CFrame=CFrame.new(group:GetAttribute("center"))
        meshPart.Parent=model
    end
    model.WorldPivot=CFrame.new()
    return model
end
local function getTemplate(key)
    if templates[key] then return templates[key] end
    if building[key] then
        while building[key] do task.wait() end
        return templates[key]
    end
    building[key]=true
    local lastError
    for attempt=1,3 do
        local ok,result=pcall(buildTemplate,key)
        if ok and result then
            templates[key]=result
            break
        end
        lastError=ok and "no data or EditableMesh unavailable" or result
        task.wait(2)
    end
    building[key]=nil
    if not templates[key] then warn("KONTUR hero mesh failed ("..key.."): "..tostring(lastError)) end
    return templates[key]
end
local attached=setmetatable({},{__mode="k"})
local function attach(model)
    if attached[model] then return end
    local key,cf=model:GetAttribute("HeroKey"),model:GetAttribute("HeroCF")
    if not key or typeof(cf)~="CFrame" then return end
    attached[model]=true
    local template=getTemplate(key)
    if not template or not model.Parent then return end
    local copy=template:Clone()
    for _,item in ipairs(copy:GetChildren()) do
        if item:IsA("MeshPart") and item.Size.Magnitude<0.01 then copy:Destroy() return end -- клон потерял меш: остаётся запасной вид
    end
    for _,item in ipairs(model:GetDescendants()) do
        if item:IsA("BasePart") and item.Name~="Hitbox" then item.LocalTransparencyModifier=1 end
    end
    copy:PivotTo(cf)
    copy.Parent=model
    -- торшер: абажур гаснет вместе с лампой (аномалии света меняют PointLight.Enabled на сервере)
    local light=model:FindFirstChild("LampLight",true)
    local shade=copy:FindFirstChild("shade")
    if light and shade and light:IsA("PointLight") then
        local function sync() shade.Material=light.Enabled and Enum.Material.Neon or Enum.Material.SmoothPlastic end
        light:GetPropertyChangedSignal("Enabled"):Connect(sync)
        sync()
    end
end
task.spawn(function()
    data=ReplicatedStorage:WaitForChild("KonturHeroData",120)
    if not data then return end
    local deadline=os.clock()+60
    while os.clock()<deadline do -- дети папки могут прийти позже самой папки: ждём все куски
        local count=0
        for _,item in ipairs(data:GetDescendants()) do if item:IsA("StringValue") then count+=1 end end
        if count>0 and count>=(data:GetAttribute("Chunks") or math.huge) then break end
        task.wait(0.25)
    end
    local office=workspace:WaitForChild("OfficeMap",120)
    local decor=office and office:WaitForChild("KonturDecor",120)
    if not decor then return end
    local function consider(model)
        if model:IsA("Model") and model:GetAttribute("HeroKey") then task.spawn(attach,model) end
    end
    decor.ChildAdded:Connect(consider)
    for _,model in ipairs(decor:GetChildren()) do consider(model) end
    for _,key in ipairs({"Bookcase","WaterCooler","CoatRack","FloorLamp","Armchair","FilingCabinet"}) do -- шаблоны заранее, пока игрок не дошёл
        task.spawn(getTemplate,key)
        task.wait()
    end
end)
end
