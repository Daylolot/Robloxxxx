local O=workspace.OfficeMap
local C=Color3.fromRGB
local function set(p,col,mat) p.Color=col if mat then p.Material=mat end end
local function lerpv(c,a,b,t) return c:Lerp(a,t) end
local stats={}
local function count(k) stats[k]=(stats[k] or 0)+1 end
-- room accent palette (chairs/soft furniture)
local accents={
 WEST=C(34,92,104), CENTER=C(44,62,92), EAST=C(36,100,96), NW=C(70,78,96), NE=C(40,84,110),
 MEN=C(52,70,82), WOMEN=C(60,84,96), StartRoom=C(30,76,92)}
-- structure
for _,p in ipairs(O.Structure:GetDescendants()) do
 if p:IsA("BasePart") then
  if p.Name:find("PlasterUpper") then set(p,C(240,243,245)) count("upper")
  elseif p.Name:find("PaintLower") or p.Name:find("CabinetRecessWallReturn") then set(p,C(34,86,98),Enum.Material.SmoothPlastic) count("lower") end
 end
end
-- floors: deep slate carpet, keep tile-to-tile variation
for _,p in ipairs(O.Floors:GetDescendants()) do
 if p:IsA("BasePart") and p.Name=="FloorTile" and p.Transparency<1 then
  local h,s,v=p.Color:ToHSV()
  if p.Material==Enum.Material.Carpet then
   local n=(v-0.36)*1.6
   p.Color=C(58,72,88):Lerp(C(76,90,106),math.clamp(n*4+0.2,0,1)) count("carpet")
  else
   p.Material=Enum.Material.Marble p.Color=C(206,212,214):Lerp(C(232,236,238),math.clamp((v-0.58)*5,0,1)) count("hardfloor")
  end
 end
end
-- ceiling
for _,p in ipairs(O.Ceiling:GetDescendants()) do
 if p:IsA("BasePart") then
  if p.Name:find("^Tile") then set(p,C(246,248,249)) count("ctile")
  elseif p.Name:find("SeamlessGrid") then set(p,C(52,60,68),Enum.Material.Metal) count("cgrid") end
 end
end
-- architectural details
for _,p in ipairs(O.ArchitecturalDetails:GetDescendants()) do
 if p:IsA("BasePart") then
  if p.Name:find("^Skirting") then set(p,C(30,38,46),Enum.Material.SmoothPlastic) count("skirt")
  elseif p.Name:find("^DadoRail") then set(p,C(196,170,120),Enum.Material.Metal) count("dado")
  elseif p.Name:find("^Cornice") then set(p,C(250,251,252)) count("cornice")
  elseif p.Name=="BlindSlat" then set(p,C(214,220,226)) count("blind") end
 end
end
-- doors
for _,p in ipairs(O.Doors:GetDescendants()) do
 if p:IsA("BasePart") and (p.Name:find("DoorBody_")) then set(p,C(34,60,72)) count("door") end
end
-- furniture
for _,room in ipairs(O.Rooms:GetChildren()) do
 local acc=accents[room.Name] or C(40,80,96)
 for _,p in ipairs(room:GetDescendants()) do
  if p:IsA("BasePart") then
   local n=p.Name
   if n:find("^Desktop_") then set(p,C(214,186,146),Enum.Material.Wood) count("desktop")
   elseif n=="TableLeg" or n=="TableApron" or n=="CableTrayFloor" then set(p,C(236,238,240),Enum.Material.Metal) count("deskframe")
   elseif n=="ModestyPanel" then set(p,C(226,230,232)) count("modesty")
   elseif p.Material==Enum.Material.Leather and (n:find("Cushion") or n:find("Pad") or n:find("Headrest")) and p:FindFirstAncestorWhichIsA("Model") and p:FindFirstAncestorWhichIsA("Model").Name:find("Chair") then
    set(p,acc,Enum.Material.Fabric) count("chairfabric")
   elseif n:find("^BackFrame") or n:find("^ArmPad") then set(p,C(26,32,38)) count("chairframe") end
  end
 end
end
local out={} for k,v in pairs(stats) do table.insert(out,k.."="..v) end table.sort(out)
return table.concat(out," ")
