-- One local mesh for soft wall stains, flowing streams and receiving puddles.
local Asset=game:GetService('AssetService')
local S=require(script.Parent:WaitForChild('BloodFloodSeep'))
local JetMath=require(script.Parent:WaitForChild('BloodJetMath'))
local B={};B.__index=B
local center=Vector3.new(1064,5.8,-16)
function B.New(parent,appearance)
    local mesh=assert(Asset:CreateEditableMesh(),'Local seep mesh memory unavailable')
    local self=setmetatable({mesh=mesh,nodes={},jets={}},B)
    local function node(position,normal,kind,spec,u,v,seed,alpha)
        local id=mesh:AddVertex(position-center);local n=mesh:AddNormal(normal)
        local uv=mesh:AddUV(Vector2.new(u,v));local color=mesh:AddColor(Color3.fromRGB(112,3,10),0)
        local a={id=id,n=n,uv=uv,color=color,kind=kind,spec=spec,u=u,v=v,seed=seed,alpha=alpha or 1}
        if kind~='jet'then table.insert(self.nodes,a)end;return a
    end
    local function tri(a,b,c)
        local f=mesh:AddTriangle(a.id,b.id,c.id)
        mesh:SetFaceNormals(f,{a.n,b.n,c.n});mesh:SetFaceUVs(f,{a.uv,b.uv,c.uv});mesh:SetFaceColors(f,{a.color,b.color,c.color})
    end
    -- Invisible bounds keep all animated coordinates in the same fixed space.
    local a=node(Vector3.new(1032.35,.1,-31.65),Vector3.yAxis,'anchor',nil,0,0,0,0)
    local b=node(Vector3.new(1095.65,11.5,-.35),Vector3.yAxis,'anchor',nil,1,1,0,0)
    local c=node(Vector3.new(1032.36,.1,-31.65),Vector3.yAxis,'anchor',nil,0,0,0,0);tri(a,b,c)
    -- Make the bounds triangle truly degenerate before the renderer builds its MeshPart.
    -- SurfaceAppearance ignores vertex alpha, so collapsing it afterwards can leave a red hairline.
    mesh:SetPosition(c.id,mesh:GetPosition(a.id))
    local function disc(kind,spec,seed,normal)
        local origin=spec.position
        local prev={node(origin,normal,kind,spec,0,0,seed,1)}
        local count=kind=='pool'and 16 or 32
        local radii=kind=='pool'and{.92,1.04}or{.33,.70,1,1.10}
        local alphas=kind=='pool'and{1,0}or{1,.88,.40,0}
        for ring,radius in ipairs(radii)do
            local alpha=alphas[ring]
            local row={}
            for j=0,count-1 do
                local angle=j/count*math.pi*2
                row[j+1]=node(origin+Vector3.new(math.cos(angle),0,math.sin(angle))*.01,normal,kind,spec,angle,radius,seed,alpha)
            end
            for j=1,count do
                local k=j%count+1
                if ring==1 then tri(prev[1],row[k],row[j])else tri(prev[j],row[k],row[j]);tri(prev[j],prev[k],row[k])end
            end
            prev=row
        end
    end
    for i,s in ipairs(S.Patches)do disc('patch',s,i,s.normal)end
    for i,s in ipairs(S.Pools)do disc('pool',s,i,Vector3.yAxis)end
    for i,s in ipairs(S.Streams)do
        local previous;local segments=12;local sides=8
        for j=0,segments do
            local row={}
            for k=0,sides-1 do
                local angle=k/sides*math.pi*2
                row[k+1]=node(s.position,s.normal,'stream',s,angle,j/segments,i,1)
            end
            if previous then for k=1,sides do local q=k%sides+1;tri(previous[k],row[q],row[k]);tri(previous[k],previous[q],row[q])end end
            previous=row
        end
    end
    -- Use the same cached mesh for all jets, keeping below 20,000 triangles.
    for sourceIndex,s in ipairs(S.Jets)do
        for _,falling in ipairs({false,true})do
            local g={spec=s,falling=falling,rings={},sides=8};table.insert(self.jets,g)
            local function jetNode(normal,u,angle,kind)
                local a=node(s.position,normal,'jet',s,angle,u,s.seed,1)
                a.jetKind=kind;a.radial=Vector3.new(math.cos(angle),0,math.sin(angle));mesh:SetColorAlpha(a.color,1);return a
            end
            for ring=0,5 do
                local row={};g.rings[ring+1]=row
                for k=0,7 do
                    local angle=k/8*math.pi*2
                    row[k+1]=jetNode(Vector3.new(math.cos(angle),0,math.sin(angle)),ring/5,angle,'side')
                end
                if ring>0 then
                    local prev=g.rings[ring]
                    for k=1,8 do local q=k%8+1;tri(prev[k],row[q],row[k]);tri(prev[k],prev[q],row[q])end
                end
            end
            g.top=jetNode(Vector3.yAxis,0,0,'top')
            for k=1,8 do local q=k%8+1;tri(g.top,g.rings[1][q],g.rings[1][k])end
            g.round={}
            for k=0,7 do
                local angle=k/8*math.pi*2
                g.round[k+1]=jetNode(Vector3.new(math.cos(angle)*.7071,-.7071,math.sin(angle)*.7071),1,angle,'round')
            end
            local last=g.rings[6]
            for k=1,8 do local q=k%8+1;tri(last[k],g.round[q],g.round[k]);tri(last[k],last[q],g.round[q])end
            g.tip=jetNode(-Vector3.yAxis,1,0,'tip')
            for k=1,8 do local q=k%8+1;tri(g.round[k],g.round[q],g.tip)end
        end
        if sourceIndex%5==0 then task.wait()end
    end
    local faceCount=#mesh:GetFaces()
    assert(faceCount<=20000,'Combined blood detail exceeds mesh triangle limit')
    local part=Asset:CreateMeshPartAsync(Content.fromObject(mesh));self.part=part
    part.Name='ContinuousBloodSeep';part.Size=part.MeshSize;part.CFrame=CFrame.new(center)
    part.Anchored=true;part.CanCollide=false;part.CanQuery=false;part.CanTouch=false;part.CastShadow=false
    part.DoubleSided=true;part.Material=Enum.Material.SmoothPlastic;part.Color=Color3.new(1,1,1);part.Transparency=0
    if appearance then
        local wet=appearance:Clone();wet.Color=Color3.fromRGB(112,3,10);wet.Parent=part
    else part.Color=Color3.fromRGB(112,3,10)end
    part:SetAttribute('LocalBloodTriangles',faceCount)
    part:SetAttribute('LocalBloodJetSources',#S.Jets)
    part.Parent=parent;return self
end
function B:Update(t)
    local tick=math.floor(t*45)
    if self.lastUpdateTick==tick then return end
    self.lastUpdateTick=tick;local m=self.mesh
    local staticTick=math.floor(t*12)
    if self.lastStaticTick~=staticTick then
    self.lastStaticTick=staticTick
    for _,a in ipairs(self.nodes)do
        if a.kind=='anchor'or a.kind=='jet'then continue end
        local s=a.spec;local position,normal,alpha
        if a.kind=='patch'then
            -- Detailed plaster is drawn by the separate wall film. Collapse the old discs.
            position=s.position;normal=s.normal;alpha=0
        elseif a.kind=='pool'then
            local radius=S.PoolRadius(t,s);local angle=a.u
            local irregular=1+.055*math.sin(angle*5+a.seed)+.035*math.sin(angle*11-a.seed)
            position=s.position+Vector3.new(math.cos(angle)*a.v*radius*irregular,0,math.sin(angle)*a.v*radius*s.aspect*irregular)
            if s.tabletop then
                position=Vector3.new(math.clamp(position.X,1067-2.78/.56,1067+2.78/.56),position.Y,math.clamp(position.Z,-14-1.10/.56,-14+1.10/.56))
            else position=Vector3.new(math.clamp(position.X,1032.4,1095.6),position.Y,math.clamp(position.Z,-31.6,-.4))end
            local depth=math.max(.001,s.position.Y-(s.tabletop and 3.384 or .104))
            local edge=math.clamp((a.v-.92)/.12,0,1)
            position-=Vector3.yAxis*(depth*edge)
            normal=Vector3.yAxis
            if edge>0 and radius>.035 then
                local outward=Vector3.new(math.cos(angle),0,math.sin(angle)/s.aspect).Unit
                normal=(Vector3.yAxis+outward*(depth/math.max(radius*.12,.02))).Unit
            end
            alpha=radius>.035 and a.alpha or 0
            m:SetUV(a.uv,Vector2.new(position.X/5+t*.025,position.Z/5-t*.018))
        else
            if not s.main then
                -- Replaced by thin intermittent image-space runoff; lamp jets are separate.
                position=s.position;normal=s.normal;alpha=0
            else
            local length=S.StreamLength(t,s);local feed=math.clamp((t-s.delay)/5,0,1)
            if length<=.35 then
                -- A zero-height tube still has a wide non-degenerate cross-section and renders as a line.
                -- Hide the outlet until it has enough vertical length to read as a flowing stream.
                position=s.position;normal=s.normal;alpha=0
                m:SetUV(a.uv,Vector2.new(a.u/(2*math.pi),a.v*2-t*.28))
            else
            local width=s.width*(s.main and(.35+.65*feed)or 1)
            local v=a.v;local angle=a.u;local right=s.normal:Cross(Vector3.yAxis)
            local pulse=1+.08*math.sin(v*12-t*(s.viscous and 1.1 or 2.1)+a.seed)
            local taper=1-.62*v^5
            local radial=width*.5*pulse*taper
            local depth=s.main and .26 or(s.viscous and .075 or .035)
            local wobble=right*math.sin(v*6-t*.85+a.seed)*math.min(.06,width*.20)
            position=s.position-Vector3.yAxis*(length*v)+right*(math.cos(angle)*radial)+s.normal*(math.sin(angle)*depth+(s.main and .20 or .025))+wobble
            normal=(right*math.cos(angle)+s.normal*math.sin(angle)).Unit
            alpha=length>.03 and .98 or 0
            m:SetUV(a.uv,Vector2.new(angle/(2*math.pi),v*2-t*(s.viscous and .12 or .28)))
            end
            end
        end
        m:SetPosition(a.id,position-center);m:SetNormal(a.n,normal);m:SetColorAlpha(a.color,alpha)
    end
    end
    for _,g in ipairs(self.jets)do
        local s=g.spec
        local visible,growth,distance,phase=JetMath.State(t,s,g.falling)
        local collapsed=s.position-center
        if not visible then
            for _,row in ipairs(g.rings)do for _,a in ipairs(row)do m:SetPosition(a.id,collapsed)end end
            for _,a in ipairs(g.round)do m:SetPosition(a.id,collapsed)end
            m:SetPosition(g.top.id,collapsed);m:SetPosition(g.tip.id,collapsed)
            continue
        end
        for ring,row in ipairs(g.rings)do
            local u=(ring-1)/5
            local p=JetMath.Center(t,s,u,growth,distance,not g.falling)
            local radius=JetMath.Radius(t,s,ring-1,g.falling,phase)
            if p.Y<=s.receivingY+.00001 then radius=0 end
            for _,a in ipairs(row)do
                local position=p+a.radial*radius
                m:SetPosition(a.id,position-center)
            end
        end
        local top=JetMath.Center(t,s,0,growth,distance,not g.falling)
        local last=JetMath.Center(t,s,1,growth,distance,false)
        local r=JetMath.Radius(t,s,5,g.falling,phase)
        if last.Y<=s.receivingY+.00001 then r=0 end
        m:SetPosition(g.top.id,top-center)
        for _,a in ipairs(g.round)do
            local p=last+a.radial*(r*.7071)-Vector3.yAxis*(r*.7071)
            p=Vector3.new(p.X,math.max(s.receivingY,p.Y),p.Z)
            m:SetPosition(a.id,p-center)
        end
        m:SetPosition(g.tip.id,Vector3.new(last.X,math.max(s.receivingY,last.Y-r),last.Z)-center)
    end
end
function B:Destroy()self.part:Destroy();self.mesh:Destroy()end
return B
