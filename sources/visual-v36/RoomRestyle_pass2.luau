local O=workspace.OfficeMap
local C=Color3.fromRGB
local stats={} local function count(k) stats[k]=(stats[k] or 0)+1 end
local accents={WEST=C(30,108,122),CENTER=C(54,82,128),EAST=C(34,118,108),NW=C(92,104,128),NE=C(40,102,138),MEN=C(64,86,100),WOMEN=C(72,100,116),StartRoom=C(30,96,116)}
for _,p in ipairs(O.Ceiling:GetDescendants()) do
 if p:IsA("BasePart") and p.Name:find("SeamlessGrid") then p.Color=C(188,198,206) count("grid") end
end
for _,p in ipairs(O.Structure:GetDescendants()) do
 if p:IsA("BasePart") and p.Name=="CabinetRecessBack" then p.Color=C(240,243,245) p.Material=Enum.Material.SmoothPlastic count("recess") end
end
for _,room in ipairs(O.Rooms:GetChildren()) do
 local acc=accents[room.Name] or C(40,100,120)
 for _,p in ipairs(room:GetDescendants()) do
  if p:IsA("BasePart") then
   local m=p:FindFirstAncestorWhichIsA("Model")
   local mn=m and m.Name or ""
   if mn:find("Chair") and p.Material==Enum.Material.Fabric then p.Material=Enum.Material.Leather p.Color=acc count("chair") end
   if mn:find("Desk") or mn:find("Table") or mn:find("Cubicle") then
    local h,s,v=p.Color:ToHSV()
    if h>0.04 and h<0.12 and s>0.3 and v>0.25 and v<0.75 and p.Material~=Enum.Material.Neon then p.Color=C(214,186,146) p.Material=Enum.Material.Wood count("brownfix") end
   end
   if mn=="NoticeBoard" and p.Name:find("^Frame") then p.Color=C(34,44,54) count("boardframe") end
  end
 end
end
local out={} for k,v in pairs(stats) do table.insert(out,k.."="..v) end table.sort(out)
return table.concat(out," ")
