-- KONTUR v36: richer plants. Replaces the simple RubberPlant_* models with potted plants built from many leaves.
local O=workspace.OfficeMap
local C=Color3.fromRGB
local F=O:FindFirstChild("KonturV36") or Instance.new("Folder") F.Name="KonturV36" F.Parent=O
local PF=F:FindFirstChild("Plants") if PF then PF:Destroy() end
PF=Instance.new("Folder") PF.Name="Plants" PF.Parent=F
local function part(parent,name,shape,size,cf,color,mat)
 local p=Instance.new("Part") p.Name=name p.Shape=shape p.Size=size p.CFrame=cf p.Color=color p.Material=mat or Enum.Material.SmoothPlastic
 p.Anchored=true p.CanCollide=false p.CanTouch=false p.CanQuery=false p.CastShadow=false p.TopSurface=Enum.SurfaceType.Smooth p.BottomSurface=Enum.SurfaceType.Smooth p.Parent=parent return p
end
local function stem(parent,a,b,thick,color)
 local d=(b-a).Magnitude if d<0.02 then return end
 part(parent,"Stem",Enum.PartType.Block,Vector3.new(thick,thick,d),CFrame.lookAt((a+b)/2,b),color,Enum.Material.Grass)
end
local potColors={C(236,238,240),C(52,66,82),C(196,170,120),C(30,38,46)}
local function makePlant(base,height,seed,kind)
 local rnd=Random.new(seed)
 local m=Instance.new("Model") m.Name="Plant_"..kind
 local potH=height*0.2 local potR=height*0.1
 local potCol=potColors[rnd:NextInteger(1,#potColors)]
 -- tapered pot from stacked cylinders
 for i=0,2 do
  local r=potR*(0.82+0.09*i) local h=potH/3
  part(m,"Pot",Enum.PartType.Cylinder,Vector3.new(h*1.02,r*2,r*2),CFrame.new(base+Vector3.new(0,h*(i+0.5),0))*CFrame.Angles(0,0,math.pi/2),potCol,Enum.Material.Marble)
 end
 part(m,"PotRim",Enum.PartType.Cylinder,Vector3.new(potH*0.08,potR*2.16,potR*2.16),CFrame.new(base+Vector3.new(0,potH,0))*CFrame.Angles(0,0,math.pi/2),potCol:Lerp(C(255,255,255),0.15),Enum.Material.Marble)
 part(m,"Soil",Enum.PartType.Cylinder,Vector3.new(0.06,potR*1.75,potR*1.75),CFrame.new(base+Vector3.new(0,potH*1.01,0))*CFrame.Angles(0,0,math.pi/2),C(38,30,26),Enum.Material.Ground)
 local top=base+Vector3.new(0,potH,0)
 local trunkTop=top+Vector3.new(0,height*0.5,0)
 if kind=="Tree" then
  stem(m,top,trunkTop,0.13,C(92,70,50))
  local n=44
  for i=1,n do
   local t=i/n
   local ang=i*2.39996+rnd:NextNumber(-0.2,0.2)
   local y=height*(0.3+0.62*t)
   local attach=top+Vector3.new(0,y-potH,0)
   if attach.Y>trunkTop.Y then attach=Vector3.new(trunkTop.X,attach.Y,trunkTop.Z) end
   local attachOnTrunk=Vector3.new(top.X,math.min(attach.Y,trunkTop.Y),top.Z)
   local dir=Vector3.new(math.cos(ang),0,math.sin(ang))
   local reach=(0.35+0.6*(1-math.abs(t-0.45)*1.3))*height*0.3
   local tip=attachOnTrunk+dir*reach+Vector3.new(0,rnd:NextNumber(0.05,0.35)*height*0.1,0)
   stem(m,attachOnTrunk,tip,0.04,C(80,104,60))
   local size=height*rnd:NextNumber(0.17,0.24)
   local ld=(dir+Vector3.new(0,rnd:NextNumber(-0.25,0.45),0)).Unit
   local center=tip+ld*size*0.5
   local g=rnd:NextNumber(0,1)
   local col=C(30,84,52):Lerp(C(78,138,76),g)
   part(m,"Leaf",Enum.PartType.Ball,Vector3.new(size*0.55,0.05,size),CFrame.lookAt(center,center+ld)*CFrame.Angles(rnd:NextNumber(-0.2,0.2),0,rnd:NextNumber(-0.5,0.5)),col,Enum.Material.Grass)
   part(m,"LeafVein",Enum.PartType.Block,Vector3.new(0.012,0.06,size*0.85),CFrame.lookAt(center,center+ld),col:Lerp(C(190,214,160),0.4),Enum.Material.Grass)
  end
 elseif kind=="Bush" then
  for i=1,70 do
   local ang=i*2.39996
   local rr=rnd:NextNumber(0.1,1)*potR*1.6
   local a=top+Vector3.new(math.cos(ang)*potR*0.3,0,math.sin(ang)*potR*0.3)
   local lean=Vector3.new(math.cos(ang),rnd:NextNumber(1.6,3.2),math.sin(ang)).Unit
   local len=height*rnd:NextNumber(0.35,0.78)
   local tip=a+lean*len
   stem(m,a,tip,0.03,C(70,102,58))
   local size=height*rnd:NextNumber(0.16,0.24)
   local ld=(lean+Vector3.new(math.cos(ang)*0.5,-0.2,math.sin(ang)*0.5)).Unit
   local center=tip+ld*size*0.45
   local col=C(34,92,58):Lerp(C(96,152,84),rnd:NextNumber(0,1))
   part(m,"Leaf",Enum.PartType.Ball,Vector3.new(size*0.5,0.05,size),CFrame.lookAt(center,center+ld)*CFrame.Angles(0,0,rnd:NextNumber(-0.6,0.6)),col,Enum.Material.Grass)
  end
 else -- Flowering
  local petals={C(250,248,244),C(240,150,170),C(250,208,96),C(176,150,232)}
  local pc=petals[rnd:NextInteger(1,#petals)]
  for i=1,26 do
   local ang=i*2.39996
   local a=top+Vector3.new(math.cos(ang)*potR*0.4,0,math.sin(ang)*potR*0.4)
   local lean=Vector3.new(math.cos(ang),rnd:NextNumber(1.8,3.6),math.sin(ang)).Unit
   local tip=a+lean*height*rnd:NextNumber(0.4,0.72)
   stem(m,a,tip,0.03,C(70,112,60))
   local mid=a:Lerp(tip,0.45)
   local size=height*0.18
   local ld=(lean+Vector3.new(math.cos(ang)*0.9,-0.1,math.sin(ang)*0.9)).Unit
   local c2=mid+ld*size*0.5
   part(m,"Leaf",Enum.PartType.Ball,Vector3.new(size*0.5,0.05,size),CFrame.lookAt(c2,c2+ld),C(40,104,60):Lerp(C(100,158,84),rnd:NextNumber(0,1)),Enum.Material.Grass)
   if i%2==0 then
    for k=0,4 do
     local pa=k*math.pi*2/5
     local pc3=tip+Vector3.new(math.cos(pa)*0.09,0.02,math.sin(pa)*0.09)
     part(m,"Petal",Enum.PartType.Ball,Vector3.new(0.14,0.04,0.14),CFrame.new(pc3)*CFrame.Angles(0.3*math.cos(pa),0,0.3*math.sin(pa)),pc,Enum.Material.SmoothPlastic)
    end
    part(m,"Bud",Enum.PartType.Ball,Vector3.new(0.09,0.09,0.09),CFrame.new(tip+Vector3.new(0,0.05,0)),C(250,214,100),Enum.Material.SmoothPlastic)
   end
  end
 end
 m.Parent=PF
 return m
end
local kinds={"Tree","Bush","Flowering"}
local n=0
for _,room in ipairs(O.Rooms:GetChildren()) do end
local olds={}
for _,d in ipairs(O:GetDescendants()) do if d:IsA("Model") and d.Name:find("^RubberPlant_") then table.insert(olds,d) end end
for i,d in ipairs(olds) do
 local cf,sz=d:GetBoundingBox()
 local h=math.max(sz.X,sz.Y,sz.Z)
 local base=Vector3.new(cf.X,0.1,cf.Z)
 makePlant(base,math.clamp(h,3.6,5.6),i*97,kinds[(i-1)%3+1])
 d:Destroy() n+=1
end
return "plants replaced "..n
