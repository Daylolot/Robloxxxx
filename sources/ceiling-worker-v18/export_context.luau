local office=workspace.OfficeMap
local room=office.Rooms.CENTER
local result={parts={},removed={},officeFloor=.075,ceilingHeight=11.44,source='Kontur_Office_v17_No_Red_Lines.rbxl'}
for _,p in office:GetDescendants()do
    if not p:IsA('BasePart')or p.Transparency>.95 then continue end
    local v=p.Position
    if v.X<1008 or v.X>1043 or v.Z<35 or v.Z>61 or v.Y<-.5 or v.Y>12 then continue end
    if p.Size.Magnitude<.19 then continue end
    local model=p:FindFirstAncestorOfClass('Model')
    if not p:IsDescendantOf(room)and p.Size.Magnitude<8 then continue end
    table.insert(result.parts,{name=p.Name,model=model and model.Name or '',cf={p.CFrame:GetComponents()},size={p.Size.X,p.Size.Y,p.Size.Z},color={p.Color.R,p.Color.G,p.Color.B},material=p.Material.Name,shape=p:IsA('Part')and p.Shape.Name or 'Block'})
end
return game:GetService('HttpService'):JSONEncode(result)
