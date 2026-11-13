-- One local atlas on two precisely cut wall films. No uploads or remote image IDs.
local Asset=game:GetService('AssetService')
local Data=require(script.Parent:WaitForChild('BloodWallData'))
local Field=require(script.Parent:WaitForChild('BloodWallField'))
local B={};B.__index=B
local size=Vector2.new(Data.Width,Data.Height)
local center=Vector3.new(1079.49,5.85,-15.49)
local function smooth(a,b,x)local t=math.clamp((x-a)/(b-a),0,1);return t*t*(3-2*t)end

function B.New(parent,cancelled)
    local self=setmetatable({images={},tracks={},complete=0,active=0,lastTick=nil},B)
    local function yieldBuild()
        if cancelled and cancelled()then error('Wall film creation cancelled')end
        task.wait()
    end
    local function populate()
        self.control=Field.Control();self.base=Data.Colors()
        assert(buffer.len(self.base)==Data.Width*Data.Height*4,'Invalid wall color field')
        self.pixels=buffer.create(buffer.len(self.base));buffer.copy(self.pixels,0,self.base)
        local count=Data.Width*Data.Height
        local buckets={};local maximum=0;local total=0
        for i=0,count-1 do
            local p=i*4
            if buffer.readu8(self.control,p+3)>0 then
                local bin=math.floor(buffer.readu16(self.control,p)/10)+1
                buckets[bin]=(buckets[bin]or 0)+1;maximum=math.max(maximum,bin);total+=1
            end
            if i%32768==0 then yieldBuild()end
        end
        self.indices=buffer.create(total*4);self.total=total
        local offsets={};local cursor=0
        for bin=1,maximum do offsets[bin]=cursor;cursor+=buckets[bin]or 0 end
        for i=0,count-1 do
            local p=i*4
            if buffer.readu8(self.control,p+3)>0 then
                local bin=math.floor(buffer.readu16(self.control,p)/10)+1
                buffer.writeu32(self.indices,offsets[bin]*4,i);offsets[bin]+=1
            end
            if i%32768==0 then yieldBuild()end
        end
        for _,s in Data.Tracks do
            local packed=Data.DecodeTrack(s.packed)
            table.insert(self.tracks,{start=s.start,length=s.length,cycle=s.cycle,speed=s.speed,packed=packed,count=buffer.len(packed)/7})
        end
        local function image(pixels)
            local value=assert(Asset:CreateEditableImage({Size=size}),'Local wall image memory unavailable')
            table.insert(self.images,value);value:WritePixelsBuffer(Vector2.zero,size,pixels);yieldBuild();return value
        end
        self.colorImage=image(self.pixels)
        local normal=image(Data.Normal())
        local roughness=image(Data.Roughness())
        local appearance=Asset:CreateSurfaceAppearanceAsync({ColorMap=Content.fromObject(self.colorImage),
            NormalMap=Content.fromObject(normal),RoughnessMap=Content.fromObject(roughness)})
        self.appearance=appearance
        appearance.Name='PorousPlasterSurface';appearance.AlphaMode=Enum.AlphaMode.Transparency;appearance.Color=Color3.new(1,1,1)
        local mesh=assert(Asset:CreateEditableMesh(),'Local wall mesh memory unavailable');self.mesh=mesh
        local function wall(side,rects)
            local normalDirection=side==0 and Vector3.zAxis or -Vector3.xAxis
            for _,r in rects do
                local vertices={};local corners={{r[1],r[3]},{r[2],r[3]},{r[2],r[4]},{r[1],r[4]}}
                for _,v in corners do
                    local c,y=v[1],v[2]
                    local point=side==0 and Vector3.new(1095.49+c,y,-31.465)or Vector3.new(1095.465,y,-31.49+c)
                    local u=side==0 and(c+32)/32 or c/32
                    local uv=Vector2.new((.5+u*(Data.Width-1))/Data.Width,(side*(Data.Height/2)+.5+(11.45-y)/11.2*(Data.Height/2-1))/Data.Width)
                    table.insert(vertices,{id=mesh:AddVertex(point-center),uv=mesh:AddUV(uv),n=mesh:AddNormal(normalDirection)})
                end
                for _,order in{{1,2,3},{1,3,4}}do
                    local a,b,c=vertices[order[1]],vertices[order[2]],vertices[order[3]]
                    local face=mesh:AddTriangle(a.id,b.id,c.id);mesh:SetFaceUVs(face,{a.uv,b.uv,c.uv});mesh:SetFaceNormals(face,{a.n,b.n,c.n})
                end
            end
        end
        wall(0,{{-32,-21.44,.25,11.45},{-9.54,0,.25,11.45},{-21.44,-9.54,.25,3.53},{-21.44,-9.54,9.75,11.45}})
        wall(1,{{0,9.54,.25,11.45},{21.44,31.09,.25,11.45},{9.54,21.44,.25,3.53},{9.54,21.44,9.75,11.45}})
        local part=Asset:CreateMeshPartAsync(Content.fromObject(mesh));self.part=part
        part.Name='PorousBloodWalls';part.Size=part.MeshSize;part.CFrame=CFrame.new(center)
        part.Anchored=true;part.CanCollide=false;part.CanTouch=false;part.CanQuery=false;part.CastShadow=false
        part.DoubleSided=true;part.Material=Enum.Material.SmoothPlastic;part.Color=Color3.new(1,1,1)
        appearance.Parent=part;part:SetAttribute('LocalWallTriangles',#mesh:GetFaces())
        part:SetAttribute('LocalWallAtlasSize',Data.Width);part.Parent=parent
        assert(#mesh:GetFaces()==16,'Wall film geometry budget changed')
    end
    local ok,err=pcall(populate)
    if not ok then self:Destroy();error(err)end
    return self
end

function B:Update(t)
    if self.destroyed then return end
    if self.lastTime and t<self.lastTime then self.complete=0;buffer.copy(self.pixels,0,self.base);self.lastTick=nil end
    self.lastTime=t
    local tick=math.floor(t*10)
    if self.lastTick==tick then return end
    self.lastTick=tick
    local began=os.clock()
    local control,pixels=self.control,self.pixels
    -- Commit old pixels once, then touch only the advancing absorption edge.
    while self.complete<self.total do
        local index=buffer.readu32(self.indices,self.complete*4);local p=index*4
        if buffer.readu16(control,p)*.01+6.4>t then break end
        buffer.writeu8(pixels,p+3,buffer.readu8(control,p+3));self.complete+=1
    end
    local cursor=self.complete
    while cursor<self.total do
        local index=buffer.readu32(self.indices,cursor*4);local p=index*4
        if buffer.readu16(control,p)*.01>t+.1 then break end
        local alpha=Field.Alpha(index,t)
        buffer.writeu8(pixels,p+3,math.floor(alpha*255+.5));cursor+=1
    end
    self.active=cursor-self.complete
    for _,s in self.tracks do
        local elapsed=t-s.start;local travel=(elapsed%s.cycle)*s.speed
        local enabled=elapsed>=0 and travel<=s.length+.24
        local begin=smooth(0,.35,elapsed)
        for i=0,s.count-1 do
            local p=i*7;local index=buffer.readu32(s.packed,p);local q=buffer.readu16(s.packed,p+4)/128
            local amount=0
            if enabled then
                local behind=travel-q
                amount=buffer.readu8(s.packed,p+6)/255*begin*(.72*math.exp(-((q-travel)/.105)^2)+(behind>=0 and .19*math.exp(-behind/.48)or 0))
            end
            local alpha=Field.Alpha(index,t);local composite=amount+alpha*(1-amount);local offset=index*4
            if composite>.00001 then
                for channel,fresh in{76,5,12}do
                    local base=buffer.readu8(self.base,offset+channel-1)
                    local value=(fresh*amount+base*alpha*(1-amount))/composite
                    buffer.writeu8(pixels,offset+channel-1,math.clamp(math.floor(value+.5),0,255))
                end
            else
                for channel=0,2 do buffer.writeu8(pixels,offset+channel,buffer.readu8(self.base,offset+channel))end
            end
            buffer.writeu8(pixels,offset+3,math.clamp(math.floor(composite*255+.5),0,255))
        end
    end
    self.colorImage:WritePixelsBuffer(Vector2.zero,size,pixels)
    self.lastUpdateMs=(os.clock()-began)*1000
end

function B:Destroy()
    if self.destroyed then return end
    self.destroyed=true
    if self.part then self.part:Destroy()elseif self.appearance then self.appearance:Destroy()end
    if self.mesh then self.mesh:Destroy()end
    for _,value in self.images do value:Destroy()end
    self.pixels=nil;self.base=nil;self.indices=nil;self.tracks={}
end
return B
