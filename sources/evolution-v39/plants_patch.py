"""v39 plants client patch: apply(plants_code, replace) -> plants_code.

The v36 runtime polled the whole office (153k instances) with GetDescendants every second for up to 90 s
(plants) and 60 s (decor) at client start. v39 scans once (yielding every 20k items) and then listens to
DescendantAdded; the loops keep their logic but walk short candidate lists. A failed mesh build is remembered
for 15 s so ~30 placements do not each repeat the heavy decode and vertex build.
`replace(source, anchor, text)` is the build helper that asserts the anchor occurs exactly once.
"""

SETUP_ANCHOR = "    local deadline=os.clock()+90\n    local lastNew=os.clock()\n"
SETUP_NEW = """    -- v39: one scan plus DescendantAdded instead of polling GetDescendants every second.
    local plantModels,decorModels={},{}
    local decorNames={CoffeeTable=true,MeetingTable=true,SideTable=true,LowCabinet=true,SideCabinet=true,FileCabinet=true,ReceptionDesk=true}
    local function consider(item)
        if item:IsA("Model") then
            if item.Name:find("^RubberPlant_") then
                plantModels[#plantModels+1]=item
            else
                local stripped=item.Name:gsub("^V%d+_%d+_","")
                if decorNames[stripped] then
                    local rooms=item:FindFirstAncestor("Rooms")
                    if rooms and rooms.Parent==office then decorModels[#decorModels+1]=item end
                end
            end
        end
    end
    local addedConnection=office.DescendantAdded:Connect(consider)
    for index,item in ipairs(office:GetDescendants()) do
        consider(item)
        if index%20000==0 then task.wait() end
    end
"""
PLANT_LOOP_OLD = """        for _,model in ipairs(office:GetDescendants()) do
            if model:IsA("Model") and model.Name:find("^RubberPlant_") and not done[model] then"""
PLANT_LOOP_NEW = """        for _,model in ipairs(plantModels) do
            if not done[model] and model:IsDescendantOf(office) then"""
DECOR_LOOP_OLD = """        for _,model in ipairs(office.Rooms:GetDescendants()) do
            if model:IsA("Model") then
                local n=model.Name:gsub("^V%d+_%d+_","")"""
DECOR_LOOP_NEW = """        for _,model in ipairs(decorModels) do
            if model:IsDescendantOf(office) then
                local n=model.Name:gsub("^V%d+_%d+_","")"""
INSTANCE_OLD = """local function instance(key)
    local spec=PLANTS[key]
    if not templates[key] then templates[key]=build(spec) end
    local t=templates[key]"""
INSTANCE_NEW = """local failedAt={}
local function instance(key)
    local spec=PLANTS[key]
    if not templates[key] then
        -- v39: a failed build is not repeated for 15 s (each retry decodes the data and adds thousands of vertices)
        if failedAt[key] and os.clock()-failedAt[key]<15 then error("no template "..key.." (recent failure)") end
        local ok,built=pcall(build,spec)
        if not ok or not built then failedAt[key]=os.clock() end
        templates[key]=ok and built or nil
    end
    local t=templates[key]"""


DECOR_END_ANCHOR = "    -- extra floor plants in free room corners (overlap-checked)\n"
DECOR_END_NEW = """    -- v39: placement loops are done, stop listening and drop the references
    addedConnection:Disconnect()
    table.clear(plantModels)
    table.clear(decorModels)
"""


def apply(plants_code, replace):
    plants_code = replace(plants_code, SETUP_ANCHOR, SETUP_NEW + SETUP_ANCHOR)  # deadline starts after the one-time scan
    plants_code = replace(plants_code, PLANT_LOOP_OLD, PLANT_LOOP_NEW)
    plants_code = replace(plants_code, DECOR_LOOP_OLD, DECOR_LOOP_NEW)
    plants_code = replace(plants_code, INSTANCE_OLD, INSTANCE_NEW)
    plants_code = replace(plants_code, DECOR_END_ANCHOR, DECOR_END_NEW + DECOR_END_ANCHOR)
    return plants_code
