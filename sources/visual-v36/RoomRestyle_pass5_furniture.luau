local O=workspace.OfficeMap
local C=Color3.fromRGB
local stats={} local function count(k) stats[k]=(stats[k] or 0)+1 end
local accents={WEST=C(30,108,122),CENTER=C(54,82,128),EAST=C(34,118,108),NW=C(92,104,128),NE=C(40,102,138),MEN=C(64,86,100),WOMEN=C(72,100,116),StartRoom=C(30,96,116)}
local function modelName(p) local m=p:FindFirstAncestorWhichIsA("Model") while m and m.Parent and m.Parent:IsA("Model") do m=m.Parent end return m and m.Name:gsub("^V%d+_%d+_","") or "" end
for _,room in ipairs(O.Rooms:GetChildren()) do
 local acc=accents[room.Name] or C(40,100,120)
 for _,p in ipairs(room:GetDescendants()) do
  if p:IsA("BasePart") and p.Material==Enum.Material.Leather then
   local n=modelName(p)
   local h,s,v=p.Color:ToHSV()
   if n=="SofaThree" or n=="SofaTwo" then p.Color=C(54,72,96) count("sofa")
   elseif n=="Armchair" then p.Color=C(200,150,74) count("armchair")
   elseif n=="VisitorBench" then p.Color=C(34,92,106) count("bench")
   elseif n=="MeetingChair" then p.Color=acc count("meetchair")
   elseif n=="VisitorChair" then p.Color=C(198,146,70) count("visitor") end
  end
 end
end
local out={} for k,v in pairs(stats) do table.insert(out,k.."="..v) end table.sort(out)
return table.concat(out," ")
