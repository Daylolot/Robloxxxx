-- Close the open corridor ends (they looked out into the void) with finished wall caps.
local O=workspace.OfficeMap
local C=Color3.fromRGB
local F=O:FindFirstChild("KonturV36") or Instance.new("Folder") F.Name="KonturV36" F.Parent=O
local function slab(name,size,pos,color,mat)
 local p=Instance.new("Part") p.Name=name p.Anchored=true p.Size=size p.Position=pos p.Color=color p.Material=mat or Enum.Material.SmoothPlastic
 p.TopSurface=Enum.SurfaceType.Smooth p.BottomSurface=Enum.SurfaceType.Smooth p.Parent=F return p
end
local W=7.6
for _,end_ in ipairs({{x=999.8,dir=1},{x=1064.3,dir=-1}}) do
 local x=end_.x local inward=end_.dir
 slab("CapUpper",Vector3.new(0.4,11.6,W),Vector3.new(x,5.9,4),C(240,243,245))
 slab("CapLower",Vector3.new(0.42,3.72,W),Vector3.new(x+inward*0.01,1.96,4),C(34,86,98))
 slab("CapSkirting",Vector3.new(0.46,0.35,W),Vector3.new(x+inward*0.03,0.28,4),C(30,38,46))
 slab("CapDado",Vector3.new(0.46,0.14,W),Vector3.new(x+inward*0.03,3.81,4),C(196,170,120),Enum.Material.Metal)
 local strip=slab("CapCove",Vector3.new(0.24,0.07,W-0.2),Vector3.new(x+inward*0.1,11.0,4),C(205,232,255),Enum.Material.Neon)
 strip.CanCollide=false strip.CastShadow=false
 -- end-of-hall sign panel and lamp so the cap reads as a designed wall
 local board=slab("CapSign",Vector3.new(0.12,1.0,3.6),Vector3.new(x+inward*0.28,6.6,4),C(20,34,42))
 local line=slab("CapSignLine",Vector3.new(0.05,0.12,3.1),Vector3.new(x+inward*0.36,6.3,4),C(196,170,120),Enum.Material.Neon)
 line.CanCollide=false
end
return "caps ok"
