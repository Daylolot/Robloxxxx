-- Bounded local detail pool: eight nearby impacts, one mesh, no uploaded assets.
local Asset=game:GetService('AssetService')
local Seep=require(script.Parent:WaitForChild('BloodFloodSeep'))
local Motion=require(script.Parent:WaitForChild('BloodImpactMath'))
local B={};B.__index=B
local center=Vector3.new(1064,5.8,-16)
local radialProfile={{.8,-.4,-1},{1,1,0},{1.2,-.4,1}}
function B.New(parent,appearance)
    local mesh=assert(Asset:CreateEditableMesh(),'Local impact mesh memory unavailable')
    local self=setmetatable({mesh=mesh,slots={},sources={},candidates={},normalUpdates=0},B)
    local function vertex(position,normal)
        return {id=mesh:AddVertex(position-center),n=mesh:AddNormal(normal)}
    end
    local color=mesh:AddColor(Color3.new(1,1,1),1)
    local function triangle(a,b,c)
        local f=mesh:AddTriangle(a.id,b.id,c.id)
        mesh:SetFaceNormals(f,{a.n,b.n,c.n});mesh:SetFaceColors(f,{color,color,color})
    end
    local bounds={vertex(Vector3.new(1031,.1,-33),Vector3.yAxis),vertex(Vector3.new(1097,11.5,1),Vector3.yAxis),vertex(Vector3.new(1031.001,.1,-33),Vector3.yAxis)}
    triangle(bounds[1],bounds[2],bounds[3])
    for _,s in Seep.Jets do
        local first=Motion.FirstHit(s)
        local pool
        if s.tabletop then pool=Seep.Pools[3]
        elseif s.id:match('^MeetingTable_Overflow_')then pool=Seep.Pools[tonumber(s.id:match('_(%d+)$'))+3]
        else
            for _,p in Seep.Pools do
                if p.jetPool and math.abs(p.position.X-s.position.X)<.001 and math.abs(p.position.Z-s.position.Z)<.001 then pool=p;break end
            end
        end
        local data={spec=s,first=first,pool=pool,drops={}}
        for i=0,3 do data.drops[i+1]=Motion.Drop(s,i)end
        table.insert(self.sources,data)
    end
    for slotIndex=1,Motion.MaximumSlots do
        local slot={rings={},drops={},nodes={},hidden=true}
        self.slots[slotIndex]=slot
        local function node(normal)
            local v=vertex(center,normal);table.insert(slot.nodes,v);return v
        end
        for ringIndex=1,2 do
            local rings={}
            slot.rings[ringIndex]=rings
            for rowIndex=1,3 do
                local row={};rings[rowIndex]=row
                for j=0,23 do
                    local angle=j/24*math.pi*2
                    local v=node(Vector3.yAxis)
                    v.radial=Vector3.new(math.cos(angle),0,math.sin(angle))
                    row[j+1]=v
                end
                if rowIndex>1 then
                    local previous=rings[rowIndex-1]
                    for j=1,24 do local k=j%24+1;triangle(previous[j],row[k],row[j]);triangle(previous[j],previous[k],row[k])end
                end
            end
        end
        for dropIndex=1,4 do
            local drop={rows={},nodes={}}
            slot.drops[dropIndex]=drop
            for latitude=1,3 do
                local row={};drop.rows[latitude]=row
                local phi=(latitude-2)*math.pi/3
                for j=0,5 do
                    local angle=j/6*math.pi*2
                    local shape=Vector3.new(math.cos(phi)*math.cos(angle),math.sin(phi),math.cos(phi)*math.sin(angle))
                    local v=node(shape);v.shape=shape;table.insert(drop.nodes,v);row[j+1]=v
                end
                if latitude>1 then
                    local previous=drop.rows[latitude-1]
                    for j=1,6 do local k=j%6+1;triangle(previous[j],previous[k],row[k]);triangle(previous[j],row[k],row[j])end
                end
            end
            drop.bottom=node(-Vector3.yAxis);drop.bottom.shape=-Vector3.yAxis;table.insert(drop.nodes,drop.bottom)
            drop.top=node(Vector3.yAxis);drop.top.shape=Vector3.yAxis;table.insert(drop.nodes,drop.top)
            for j=1,6 do local k=j%6+1;triangle(drop.bottom,drop.rows[1][k],drop.rows[1][j]);triangle(drop.rows[3][j],drop.rows[3][k],drop.top)end
        end
        if slotIndex%2==0 then task.wait()end
    end
    local faces=#mesh:GetFaces()
    assert(faces==2689 and faces<20000,'Impact detail exceeded fixed mesh budget')
    local part=Asset:CreateMeshPartAsync(Content.fromObject(mesh));self.part=part
    mesh:SetPosition(bounds[2].id,mesh:GetPosition(bounds[1].id));mesh:SetPosition(bounds[3].id,mesh:GetPosition(bounds[1].id))
    part.Name='BloodImpactDetails';part.Size=part.MeshSize;part.CFrame=CFrame.new(center)
    part.Anchored=true;part.CanCollide=false;part.CanQuery=false;part.CanTouch=false;part.CastShadow=false
    part.DoubleSided=true;part.Material=Enum.Material.SmoothPlastic;part.Transparency=.02
    if appearance then local wet=appearance:Clone();wet.Color=Color3.fromRGB(112,3,10);wet.Parent=part;part.Color=Color3.new(1,1,1)
    else part.Color=Color3.fromRGB(112,3,10)end
    part:SetAttribute('LocalBloodImpactTriangles',faces)
    part:SetAttribute('LocalBloodImpactSlotLimit',Motion.MaximumSlots)
    part:SetAttribute('LocalBloodActiveImpacts',0)
    part.Parent=parent
    return self
end
function B:Hide(slot)
    if slot.hidden then return end
    for _,v in slot.nodes do self.mesh:SetPosition(v.id,Vector3.zero)end
    slot.hidden=true
end
function B:Update(t,camera)
    local tick=math.floor(t*Motion.Frequency)
    if self.lastTick==tick then return end
    self.lastTick=tick
    local choices=self.candidates;table.clear(choices)
    if camera and t<Motion.HideAfter then
        local eye=camera.CFrame.Position
        for _,data in self.sources do
            if t<data.first then continue end
            local s=data.spec
            local point=Vector3.new(s.position.X,s.receivingY,s.position.Z)
            local delta=point-eye
            local distance=delta:Dot(delta)
            if distance>Motion.Distance^2 then continue end
            if distance>16 and camera.CFrame.LookVector:Dot(delta)<0 then continue end
            local active=false
            for _,r in Motion.Rings do if Motion.Age(t,data.first,s.cycle,r.lag,r.duration)then active=true;break end end
            if not active then continue end
            data.distance=distance;table.insert(choices,data)
        end
        table.sort(choices,function(a,b)return a.distance<b.distance end)
    end
    local count=math.min(#choices,Motion.MaximumSlots)
    for index,slot in self.slots do
        local data=choices[index]
        if index>count then self:Hide(slot);continue end
        slot.hidden=false
        local s=data.spec
        local poolRadius=data.pool and Seep.PoolRadius(t,data.pool)or 0
        for ringIndex,rings in slot.rings do
            local preset=Motion.Rings[ringIndex]
            local age=Motion.Age(t,data.first,s.cycle,preset.lag,preset.duration)
            local origin=age and Motion.HitPoint(t-age-preset.lag,s)or s.position
            local clearance=Motion.WetClearance(t,data.pool,origin,poolRadius)
            local radius=age and math.min((.009+.105*age/preset.duration)/.28,clearance)or 0
            local height=age and preset.height*(1-age/preset.duration)or 0
            for rowIndex,row in rings do
                local profile=radialProfile[rowIndex]
                for _,v in row do
                    if radius<.015 then self.mesh:SetPosition(v.id,Vector3.zero)
                    else
                        local point=origin+v.radial*(radius*profile[1])+Vector3.yAxis*(height*profile[2]-.0001/.28)
                        self.mesh:SetPosition(v.id,point-center)
                        local slope=profile[3]*7*height/math.max(radius,.015)
                        self.mesh:SetNormal(v.n,(Vector3.yAxis+v.radial*slope).Unit)
                    end
                end
            end
        end
        for dropIndex,drop in slot.drops do
            local d=data.drops[dropIndex]
            local age=Motion.Age(t,data.first,s.cycle,d.lag,d.flight)
            local point=age and Motion.DropPoint(Motion.HitPoint(t-age-d.lag,s),age,d)or nil
            for _,v in drop.nodes do
                local position=point and(point+Vector3.new(v.shape.X,v.shape.Y*1.45,v.shape.Z)*d.radius-center)or Vector3.zero
                self.mesh:SetPosition(v.id,position)
            end
        end
    end
    if self.activeCount~=count then self.activeCount=count;self.part:SetAttribute('LocalBloodActiveImpacts',count)end
end
function B:Destroy()
    self.part:Destroy();self.mesh:Destroy()
end
return B
