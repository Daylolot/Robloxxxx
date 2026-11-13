local O=workspace.OfficeMap
local C=Color3.fromRGB
local stats={} local function count(k) stats[k]=(stats[k] or 0)+1 end
local old=O:FindFirstChild("KonturV36") if old then old:Destroy() end
local F=Instance.new("Folder") F.Name="KonturV36" F.Parent=O
-- window infill matches new wall
for _,p in ipairs(O.V09_Joinery:GetDescendants()) do
 if p:IsA("BasePart") and p.Name:find("^WindowInfill") then p.Color=C(240,243,245) count("infill") end
end
-- cove light strips under cornices
for _,p in ipairs(O.ArchitecturalDetails:GetDescendants()) do
 if p:IsA("BasePart") and p.Name:find("^Cornice") then
  local s=Instance.new("Part") s.Name="CoveStrip" s.Anchored=true s.CanCollide=false s.CanTouch=false s.CanQuery=false s.CastShadow=false
  s.Material=Enum.Material.Neon s.Color=C(205,232,255)
  local long=math.max(p.Size.X,p.Size.Z)-0.1
  if p.Size.X>p.Size.Z then s.Size=Vector3.new(long,0.07,0.22) else s.Size=Vector3.new(0.22,0.07,long) end
  s.CFrame=CFrame.new(p.Position.X,p.Position.Y-0.26,p.Position.Z)
  s.Parent=F count("cove")
 end
end
-- rugs under tables / lounge
local rugColor={WEST=C(36,96,108),CENTER=C(52,70,104),EAST=C(40,104,98),NW=C(86,96,120),NE=C(44,92,122),MEN=C(60,80,94),WOMEN=C(70,92,108),StartRoom=C(34,88,108)}
for _,room in ipairs(O.Rooms:GetChildren()) do
 for _,m in ipairs(room:GetChildren()) do
  if m:IsA("Model") and (m.Name:find("CoffeeTable") or m.Name:find("MeetingTable") or m.Name:find("ExecutiveDesk")) then
   local cf,sz=m:GetBoundingBox()
   local pad=m.Name:find("Coffee") and 3.2 or 4.2
   local r=Instance.new("Part") r.Name="Rug" r.Anchored=true r.CanCollide=false r.CanQuery=false r.CastShadow=false
   r.Material=Enum.Material.Fabric r.Color=rugColor[room.Name] or C(50,80,100)
   r.Size=Vector3.new(sz.X+pad,0.04,sz.Z+pad)
   r.CFrame=CFrame.new(cf.X,0.12,cf.Z)*(cf-cf.Position):Inverse()*CFrame.Angles(0,select(2,cf:ToEulerAnglesYXZ()),0)
   r.Parent=F count("rug")
   local b=r:Clone() b.Name="RugBorder" b.Size=Vector3.new(r.Size.X-0.8,0.05,r.Size.Z-0.8) b.Color=r.Color:Lerp(C(235,238,240),0.22) b.CFrame=r.CFrame+Vector3.new(0,0.002,0) b.Parent=F
  end
 end
end
local out={} for k,v in pairs(stats) do table.insert(out,k.."="..v) end table.sort(out)
return table.concat(out," ")
