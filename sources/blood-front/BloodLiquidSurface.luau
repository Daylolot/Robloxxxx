-- Continuous front geometry: rows move with the liquid instead of appearing in tiles.
-- KONTUR v39F: channel regions (corridors, doorways) use a fine lateral grid so the curved, wandering wave front
-- from BloodLiquidMath.FrontShift is drawn smoothly instead of as a straight 3-stud-faceted wall.
local Asset=game:GetService('AssetService')
local Math=require(script.Parent:WaitForChild('BloodLiquidMath'))
local Surface={};Surface.__index=Surface
-- KONTUR v38: shade the liquid from its own wave normals. Shades come from a 32-step palette (no per-vertex allocation);
-- normals use forward differences (2 height samples per vertex instead of 4), which pays for the extra SetColor.
local SHADE_LIGHT=Vector3.new(.38,.84,.34).Unit
local SHADE_FLAT=SHADE_LIGHT.Y
local SKIRT_COLOR=Color3.new(.52,.44,.44)
local BODY_COLOR=Color3.fromRGB(138,5,11)
local LATERAL_STEP=1.2 -- grid spacing across a channel
local SHADES={}
for i=0,31 do local k=i/31;SHADES[i]=Color3.new(k,k*.92,k*.92)end
function Surface.New(defs,parent,appearance,config)
    local mesh=assert(Asset:CreateEditableMesh(),'Local liquid mesh memory unavailable')
    local self=setmetatable({mesh=mesh,config=config,points={},seamBases={},bounds={},center=Vector3.new(1038,5.8,28)},Surface)
    for _,r in ipairs(defs)do self.bounds[r.id]=r end
    local function node(r,u,v,base)
        local x=r.x0+(r.x1-r.x0)*u;local z=r.z0+(r.z1-r.z0)*v
        local y=config.FloorY+(base and 0 or config.BodyHeight)
        local a={r=r,u=u,v=v,base=base}
        a.id=mesh:AddVertex(Vector3.new(x,y,z)-self.center);a.n=mesh:AddNormal(Vector3.yAxis)
        a.uv=mesh:AddUV(Vector2.new(x/7,z/7));a.color=mesh:AddColor(Color3.new(1,1,1),0)
        table.insert(self.points,a);return a
    end
    local function tri(a,b,c,normal)
        local f=mesh:AddTriangle(a.id,b.id,c.id)
        mesh:SetFaceNormals(f,{normal or a.n,normal or b.n,normal or c.n})
        mesh:SetFaceUVs(f,{a.uv,b.uv,c.uv});mesh:SetFaceColors(f,{a.color,b.color,c.color})
    end
    local zero=mesh:AddColor(Color3.new(1,1,1),0)
    local a=mesh:AddVertex(Vector3.new(0,11.5,0)-self.center)
    local b=mesh:AddVertex(Vector3.new(.001,11.5,0)-self.center)
    local c=mesh:AddVertex(Vector3.new(0,.1,.001)-self.center)
    -- The X/Z coordinates of invisible anchors must stay inside the office bounds.
    mesh:SetPosition(a,Vector3.new(0,5.7,0));mesh:SetPosition(b,Vector3.new(.001,5.7,0));mesh:SetPosition(c,Vector3.new(0,-5.7,.001))
    local f=mesh:AddTriangle(a,b,c);mesh:SetFaceColors(f,{zero,zero,zero})
    for _,r in ipairs(defs)do
        local step=r.id=='Source'and 2 or 3
        local fine=Math.ChannelHalfWidth(r)~=nil -- front moves along `axis`; refine only across it
        local nx=math.max(2,math.ceil((r.x1-r.x0)/((fine and r.axis=='Z')and LATERAL_STEP or step)))
        local nz=math.max(2,math.ceil((r.z1-r.z0)/((fine and r.axis=='X')and LATERAL_STEP or step)))
        local grid={}
        for j=0,nz do grid[j]={};for i=0,nx do grid[j][i]=node(r,i/nx,j/nz,false)end end
        for j=0,nz-1 do for i=0,nx-1 do
            local a,b,c,d=grid[j][i],grid[j][i+1],grid[j+1][i+1],grid[j+1][i]
            tri(a,d,c);tri(a,c,b)
        end end
        local perimeter={}
        for i=0,nx do table.insert(perimeter,grid[0][i])end
        for j=1,nz do table.insert(perimeter,grid[j][nx])end
        for i=nx-1,0,-1 do table.insert(perimeter,grid[nz][i])end
        for j=nz-1,1,-1 do table.insert(perimeter,grid[j][0])end
        for i=1,#perimeter do
            local j=i%#perimeter+1;local first,last=perimeter[i],perimeter[j]
            local edge=Vector3.new((last.u-first.u)*(r.x1-r.x0),0,(last.v-first.v)*(r.z1-r.z0))
            local outward=Vector3.yAxis:Cross(edge).Unit
            local baseA,baseB=node(r,first.u,first.v,true),node(r,last.u,last.v,true)
            baseA.follow=first;baseB.follow=last;baseA.outward=outward;baseB.outward=outward
            table.insert(self.seamBases,baseA);table.insert(self.seamBases,baseB)
            local normal=mesh:AddNormal(outward)
            tri(first,last,baseB,normal);tri(first,baseB,baseA,normal)
        end
        task.wait()
    end
    local p=Asset:CreateMeshPartAsync(Content.fromObject(mesh));self.part=p
    mesh:SetPosition(b,mesh:GetPosition(a))
    p.Name='FlowingLiquid_Office';p.Size=p.MeshSize;p.CFrame=CFrame.new(self.center)
    p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false;p.DoubleSided=true;p.CastShadow=false
    p.Material=Enum.Material.SmoothPlastic;p.Color=BODY_COLOR;p.Transparency=1;p.Reflectance=0
    if appearance then
        local wet=appearance:Clone();wet.Color=BODY_COLOR;wet.Parent=p
    end
    p.Parent=parent;return self
end
local function pointFor(p,r,all,now,start,c)
    local d=p.r;local x,z=d.x0+(d.x1-d.x0)*p.u,d.z0+(d.z1-d.z0)*p.v
    if not r or not start or start<=0 then return x,z,false end
    if r.id=='Source'then
        local flow=now-start-c.SourceBeginsAt
        if flow<=0 then return d.x1,d.z0,false end
        local duration=math.max(1,c.WarningSeconds-c.SourceBeginsAt)
        local n=flow*57.975/duration;local e=flow*64.3/duration
        local last=math.min(d.z1,math.max(d.z0+n,-21+e/.65))
        z=d.z0+(last-d.z0)*p.v
        local east=d.x1-e+.65*math.max(0,math.abs(z+25)-4)
        local north=n>=z+31.65 and(1086-(n-(z+31.65))/.65)or(d.x1+1)
        local front=math.clamp(math.min(east,north),d.x0,d.x1)
        x=front+(d.x1-front)*p.u*p.u
        return x,z,d.x1-front>.015
    end
    local travel=(now-r.start)*c.WaveSpeed
    if travel<=0 then return x,z,false end
    if r.axis=='X'then
        if r.fan>0 then
            local reach=2.15+travel/r.fan
            local lo=math.max(d.z0,r.entry-reach);local hi=math.min(d.z1,r.entry+reach)
            z=lo+math.max(0,hi-lo)*p.v
        end
        local fan=r.fan*math.max(0,math.abs(z-r.entry)-2.15)
        local near=r.sign==1 and d.x0 or d.x1
        local front=math.clamp(r.origin+r.sign*(travel+((r.fan or 0)==0 and Math.FrontShift(r,z,travel) or 0)-fan),d.x0,d.x1)
        if r.id=='SouthW'or r.id=='SouthE'then
            local w,e=all.SouthW,all.SouthE
            if w and e then
                local left=math.clamp(w.origin+(now-w.start)*c.WaveSpeed,d.x0,d.x1)
                local right=math.clamp(e.origin-(now-e.start)*c.WaveSpeed,d.x0,d.x1)
                if left>=right then local meet=(left+right)/2;front=r.sign==1 and math.min(front,meet)or math.max(front,meet)end
            end
        end
        if r.sign==1 then x=front-(front-near)*(1-p.u)^2 else x=front+(near-front)*p.u^2 end
        return x,z,math.abs(front-near)>.015
    end
    if r.fan>0 then
        local reach=2.15+travel/r.fan
        local lo=math.max(d.x0,r.entry-reach);local hi=math.min(d.x1,r.entry+reach)
        x=lo+math.max(0,hi-lo)*p.u
    end
    local fan=r.fan*math.max(0,math.abs(x-r.entry)-2.15)
    local near=r.sign==1 and d.z0 or d.z1
    local front=math.clamp(r.origin+r.sign*(travel+((r.fan or 0)==0 and Math.FrontShift(r,x,travel) or 0)-fan),d.z0,d.z1)
    if r.sign==1 then z=front-(front-near)*(1-p.v)^2 else z=front+(near-front)*p.v^2 end
    return x,z,math.abs(front-near)>.015
end
function Surface:Update(now,started,regions)
    if self.lastUpdate and now-self.lastUpdate<1/40 then return end
    self.lastUpdate=now
    local all={};for _,r in ipairs(regions)do all[r.id]=r end
    local m=self.mesh;local c=self.config
    local function height(r,x,z)
        local h=Math.Height(r,x,z,now,started,c)
        if r.id=='SouthW'and all.SouthE then h=math.max(h,Math.Height(all.SouthE,x,z,now,started,c))end
        if r.id=='SouthE'and all.SouthW then h=math.max(h,Math.Height(all.SouthW,x,z,now,started,c))end
        return h
    end
    local anyWet=false
    for _,p in ipairs(self.points)do
        local r=all[p.r.id];local x,z,wet=pointFor(p,r,all,now,started,c)
        -- Skirt bases sit on the floor: they never need a height sample.
        local h=wet and not p.base and height(r,x,z)or 0
        anyWet=anyWet or wet
        local flipped=p.wet_a~=wet
        p.wet=wet
        -- Dry vertices sit at a fixed parking spot: touch the mesh for them only when the state flips.
        if wet or flipped then
            local position=wet and Vector3.new(x,c.FloorY+(p.base and 0 or h),z)or Vector3.new(p.r.x0,c.FloorY-.05,p.r.z0)
            p.position=position
            m:SetPosition(p.id,position-self.center)
        end
        if flipped then p.wet_a=wet;m:SetColorAlpha(p.color,wet and 1 or 0)end -- only when the state flips
        if wet and p.base and not p.shaded then p.shaded=true;m:SetColor(p.color,SKIRT_COLOR)end
        if wet and not p.base then
            local e=.3;local dx=2*(height(r,x+e,z)-h);local dz=2*(height(r,x,z+e)-h)
            local n=Vector3.new(-dx,2*e,-dz).Unit
            m:SetNormal(p.n,n)
            local t=now-started;m:SetUV(p.uv,Vector2.new(x/7+t*.12,z/7-t*.085))
            -- Crests catch the light, troughs and clots stay dark; slow mottling keeps the mass from reading as paint.
            local lit=math.clamp(.8+1.7*(n:Dot(SHADE_LIGHT)-SHADE_FLAT),.36,1)
            local mottle=.9+.1*math.sin(x*.33+t*.21)*math.sin(z*.29-t*.17)
            -- A thin film at the leading edge catches the light: the toe of the wave is paler than the body.
            local body=lit*mottle
            local foam=h<.7 and(.7-h)/.7*.55 or 0
            local shade=math.floor((body+(1-body)*foam)*31+.5)
            if p.shade~=shade then p.shade=shade;m:SetColor(p.color,SHADES[shade])end
        end
    end
    -- Remove submerged internal skirts once both sides meet at an open doorway.
    -- Moving fronts and outer walls retain their full receiving volume.
    -- Which other regions overlap a skirt sample only changes when the sample moves or a region appears,
    -- so the candidate list is cached per skirt vertex (the old code walked every region for every vertex, every update).
    local regionCount=#regions
    for _,p in ipairs(self.seamBases)do
        local top=p.follow
        if not top.wet then continue end
        local sample=top.position+p.outward*.06
        local sx,sz=sample.X,sample.Z
        local list=p.cands
        if not list or p.cn~=regionCount or math.abs(sx-p.cx)>.001 or math.abs(sz-p.cz)>.001 then
            if list then table.clear(list)else list={};p.cands=list end
            p.cx=sx;p.cz=sz;p.cn=regionCount
            for id,r in pairs(all)do
                if id~=p.r.id then
                    local bounds=self.bounds[id]or r
                    if sx>=bounds.x0-.001 and sx<=bounds.x1+.001 and sz>=bounds.z0-.001 and sz<=bounds.z1+.001 then table.insert(list,r)end
                end
            end
        end
        for _,r in ipairs(list)do
            local other=height(r,sx,sz)
            if other>.14 and math.abs(other-(top.position.Y-c.FloorY))<.65 then
                m:SetPosition(p.id,top.position-self.center);break
            end
        end
    end
    self.part.Transparency=anyWet and .02 or 1
end
function Surface:Destroy()self.part:Destroy();self.mesh:Destroy()end
return Surface
