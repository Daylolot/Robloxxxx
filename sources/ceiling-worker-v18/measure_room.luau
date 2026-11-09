local office=workspace:WaitForChild('OfficeMap')
local room=office.Rooms.CENTER
local result={room={},desk={},interactions={},ceiling={}}
local function row(v)
    local cf,size=v:GetBoundingBox()
    return {name=v.Name,path=v:GetFullName(),position={cf.X,cf.Y,cf.Z},size={size.X,size.Y,size.Z}}
end
for _,v in room:GetChildren()do
    if v:IsA('Model')then
        table.insert(result.room,row(v))
        if v.Name=='V09_0098_StraightDesk'then
            for _,p in v:GetDescendants()do
                if p:IsA('BasePart')then table.insert(result.desk,{name=p.Name,size={p.Size.X,p.Size.Y,p.Size.Z},cf={p.CFrame:GetComponents()}})end
            end
        end
    end
end
for _,p in room:GetDescendants()do
    if p:IsA('ProximityPrompt')then
        table.insert(result.interactions,{path=p:GetFullName(),action=p.ActionText,object=p.ObjectText})
    end
end
return result
