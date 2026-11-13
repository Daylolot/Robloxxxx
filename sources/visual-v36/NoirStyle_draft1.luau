local L=game:GetService("Lighting")
L.Ambient=Color3.fromRGB(26,36,46); L.OutdoorAmbient=Color3.fromRGB(26,36,46)
L.Brightness=1.0; L.ExposureCompensation=-0.3; L.EnvironmentDiffuseScale=0.35; L.ShadowSoftness=0.2
L.FogColor=Color3.fromRGB(8,14,20); L.FogStart=45; L.FogEnd=170
local cc=L:FindFirstChild("FieldGrade"); cc.Contrast=0.24; cc.Saturation=-0.25; cc.Brightness=-0.03; cc.TintColor=Color3.fromRGB(205,228,255)
local bl=L:FindFirstChild("PracticalBloom"); bl.Intensity=0.4; bl.Size=30; bl.Threshold=1.0
local n=0
for _,d in ipairs(workspace.OfficeMap:GetDescendants()) do
 if d.Name=="CeilingPanelLight" and d:IsA("SurfaceLight") then
  n+=1; d.Color=Color3.fromRGB(190,225,255); d.Brightness=(n%3==0) and 0.35 or 0.8
 end
end
local walls=0
for _,p in ipairs(workspace.OfficeMap.Rooms:GetDescendants()) do
 if p:IsA("BasePart") and p.Transparency<0.5 and p.Material~=Enum.Material.Neon and p.Material~=Enum.Material.Glass then
  local h,s,v=p.Color:ToHSV()
  if v>0.62 and s<0.35 then p.Color=p.Color:Lerp(Color3.fromRGB(34,52,64),0.62); walls+=1 end
 end
end
return "lights "..n.." recolored "..walls
