-- review-room: инвентаризация предметов комнаты. ТОЛЬКО ЧТЕНИЕ: ничего не создаёт, не двигает и не меняет.
-- Запускается в Server-датамодели Play (декор строится скриптами при старте). __ROOM__ подставляет inspect_room.py.
-- Возвращает JSON: {room, bounds, objects=[{idx,name,source,parent,class,cx..sz,px,py,pz,lx,lz, checks...}]}
local HttpService = game:GetService("HttpService")
local ROOM = "__ROOM__"
local FROM, TO = __FROM__, __TO__ -- страница: полный JSON одним ответом может не пройти по размеру

local om = workspace:FindFirstChild("OfficeMap")
if not om then return HttpService:JSONEncode({error = "no OfficeMap"}) end
local rooms = om:FindFirstChild("Rooms")
local floors = om:FindFirstChild("Floors")
local roomFolder = rooms and rooms:FindFirstChild(ROOM)
local floorModel = floors and floors:FindFirstChild(ROOM)
if not roomFolder and not floorModel then
	local names, seenName = {}, {}
	for _, root in ipairs({rooms, floors}) do
		if root then
			for _, r in ipairs(root:GetChildren()) do
				if (r:IsA("Folder") or r:IsA("Model")) and not seenName[r.Name] then seenName[r.Name] = true names[#names + 1] = r.Name end
			end
		end
	end
	return HttpService:JSONEncode({error = "room not found", rooms = names})
end

local function bbox(inst: Instance)
	if inst:IsA("Model") then
		local ok, cf, size = pcall(function() local a, b = inst:GetBoundingBox() return a, b end)
		if ok then return cf, size end
	elseif inst:IsA("BasePart") then
		return inst.CFrame, inst.Size
	end
	return nil, nil
end

-- 1. объекты самой комнаты: дети Rooms/<ROOM> и дети папки KonturInterior_*
local objects: {{inst: Instance, source: string}} = {}
local function addChildren(folder: Instance, source: string)
	for _, c in ipairs(folder:GetChildren()) do
		if c:IsA("Model") or c:IsA("BasePart") then
			objects[#objects + 1] = {inst = c, source = source}
		elseif c:IsA("Folder") then
			addChildren(c, source .. "/" .. c.Name)
		end
	end
end
if roomFolder then addChildren(roomFolder, "Rooms/" .. ROOM) end

-- 2. границы комнаты: точный пол Floors/<ROOM>, иначе объединение рамок объектов
local minX, minY, minZ, maxX, maxY, maxZ = math.huge, math.huge, math.huge, -math.huge, -math.huge, -math.huge
for _, o in ipairs(objects) do
	local cf, size = bbox(o.inst)
	if cf then
		local p = cf.Position
		minX = math.min(minX, p.X - size.X / 2) maxX = math.max(maxX, p.X + size.X / 2)
		minY = math.min(minY, p.Y - size.Y / 2) maxY = math.max(maxY, p.Y + size.Y / 2)
		minZ = math.min(minZ, p.Z - size.Z / 2) maxZ = math.max(maxZ, p.Z + size.Z / 2)
	end
end
if floorModel then
	local fcf, fsize = bbox(floorModel)
	if fcf then
		minX, maxX = fcf.Position.X - fsize.X / 2, fcf.Position.X + fsize.X / 2
		minZ, maxZ = fcf.Position.Z - fsize.Z / 2, fcf.Position.Z + fsize.Z / 2
		minY = fcf.Position.Y + fsize.Y / 2 -- верхняя поверхность пола
		if maxY < minY + 3 then maxY = minY + 10 end
	end
end
if minX == math.huge then return HttpService:JSONEncode({error = "room has no objects and no floor"}) end
local PAD = 0.5
local function inRoom(p: Vector3): boolean
	return p.X >= minX - PAD and p.X <= maxX + PAD and p.Z >= minZ - PAD and p.Z <= maxZ + PAD
end

-- 3. доп. объекты из общих папок: KonturDecor (атрибут Room) и остальные папки декора, если центр внутри границ комнаты
local extraFolders = {"KonturDecor", "KonturPlants", "KonturWallDecor", "KonturEast", "KonturWC", "KonturCorridor", "KonturV36", "Misc", "Corridor", "Doors"}
for _, fname in ipairs(extraFolders) do
	local f = om:FindFirstChild(fname)
	if f then
		for _, c in ipairs(f:GetChildren()) do
			if c:IsA("Model") or c:IsA("BasePart") then
				local attrRoom = c:GetAttribute("Room") or c:GetAttribute("KonturRoom")
				local cf = bbox(c)
				if cf then
					local mine = if attrRoom ~= nil then tostring(attrRoom) == ROOM else inRoom(cf.Position)
					if mine then objects[#objects + 1] = {inst = c, source = fname} end
				end
			end
		end
	end
end

-- реестр объектов: для поиска, какому объекту принадлежит найденная деталь
local objByInst: {[Instance]: number} = {}
for i, o in ipairs(objects) do objByInst[o.inst] = i end

local FLOOR_Y = minY
local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Exclude

local DEFAULT_GREY = Color3.fromRGB(163, 162, 165)
local PLACEHOLDER_TEXT = {["label"] = true, ["textlabel"] = true, ["text"] = true, ["lorem"] = true, ["todo"] = true, ["test"] = true}

local function clip(s: string): string
	if utf8.len(s) == nil then return "?" end -- не-UTF-8: JSONEncode упал бы
	local cut = utf8.offset(s, 41)
	if cut then return string.sub(s, 1, cut - 1) end
	return s
end

local function pathOf(inst: Instance): {string}
	local chain = {}
	local p = inst.Parent
	while p and p ~= workspace do table.insert(chain, 1, p.Name) p = p.Parent end
	return chain
end

local out = {}
for i, o in ipairs(objects) do
	local inst = o.inst
	local cf, size = bbox(inst)
	if cf and i >= FROM and i <= TO then
		local pv = inst:GetPivot()
		local item = {
			idx = i, name = inst.Name, class = inst.ClassName, source = o.source, parent = pathOf(inst),
			cx = cf.Position.X, cy = cf.Position.Y, cz = cf.Position.Z, sx = size.X, sy = size.Y, sz = size.Z,
			px = pv.Position.X, py = pv.Position.Y, pz = pv.Position.Z, lx = pv.LookVector.X, lz = pv.LookVector.Z,
		}
		-- состав
		local parts, meshes, noMesh, defaultGrey, invisible, unanchored, tiny, decals, emptyDecal, guis = 0, 0, {}, 0, 0, 0, 0, 0, 0, 0
		local meshNoAppearance, texts, prompts, scripts = 0, {}, 0, 0
		local function scan(d: Instance)
			if d:IsA("BasePart") then
				parts += 1
				if d.Transparency >= 0.98 then invisible += 1 end
				if not d.Anchored then unanchored += 1 end
				if d.Size.Magnitude < 0.03 then tiny += 1 end
				if d:IsA("MeshPart") then
					meshes += 1
					if d.MeshId == "" then noMesh[#noMesh + 1] = d.Name end
					if not d:FindFirstChildOfClass("SurfaceAppearance") and d.TextureID == "" then meshNoAppearance += 1 end
				end
				if d.Color == DEFAULT_GREY and d.Material == Enum.Material.Plastic and d.Transparency < 0.98 then defaultGrey += 1 end
			elseif d:IsA("Decal") or d:IsA("Texture") then
				decals += 1
				if d.Texture == "" then emptyDecal += 1 end
			elseif d:IsA("SurfaceGui") or d:IsA("BillboardGui") then
				guis += 1
			elseif d:IsA("TextLabel") or d:IsA("TextButton") then
				if #texts < 6 then texts[#texts + 1] = clip(d.Text) end
			elseif d:IsA("ProximityPrompt") then
				prompts += 1
			elseif d:IsA("LuaSourceContainer") then
				scripts += 1
			end
		end
		scan(inst)
		for _, d in ipairs(inst:GetDescendants()) do scan(d) end
		item.parts, item.meshes, item.noMesh = parts, meshes, noMesh
		item.defaultGrey, item.invisible, item.unanchored, item.tiny = defaultGrey, invisible, unanchored, tiny
		item.decals, item.emptyDecal, item.guis, item.texts = decals, emptyDecal, guis, texts
		item.meshNoAppearance, item.prompts, item.scripts = meshNoAppearance, prompts, scripts
		local placeholder = false
		for _, t in ipairs(texts) do if PLACEHOLDER_TEXT[string.lower(t)] then placeholder = true end end
		item.placeholderText = placeholder
		-- ориентация
		local up = pv.UpVector
		item.tiltDeg = math.deg(math.acos(math.clamp(up.Y, -1, 1)))
		-- вне границ комнаты
		item.outOfRoom = not inRoom(cf.Position)
		-- зазор до поверхности под предметом (парение)
		local rp = RaycastParams.new()
		rp.FilterType = Enum.RaycastFilterType.Exclude
		rp.FilterDescendantsInstances = {inst}
		local bottomY = cf.Position.Y - size.Y / 2
		local hit = workspace:Raycast(Vector3.new(cf.Position.X, bottomY + 0.05, cf.Position.Z), Vector3.new(0, -3, 0), rp)
		item.gapBelow = if hit then (bottomY + 0.05) - hit.Position.Y else nil
		item.heightAboveFloor = bottomY - FLOOR_Y
		-- пересечения с другими объектами комнаты (по рамке, уменьшенной на 20%)
		overlapParams.FilterDescendantsInstances = {inst}
		local touching, seen = {}, {}
		local shrunk = Vector3.new(math.max(0.02, size.X * 0.8), math.max(0.02, size.Y * 0.8), math.max(0.02, size.Z * 0.8))
		local okq, hits = pcall(function() return workspace:GetPartBoundsInBox(cf, shrunk, overlapParams) end)
		if okq then
			for _, hp in ipairs(hits) do
				local a: Instance? = hp
				while a and a ~= workspace do
					local idx = objByInst[a]
					if idx then
						if idx ~= i and not seen[idx] then
							seen[idx] = true
							if #touching < 8 then touching[#touching + 1] = objects[idx].inst.Name end
						end
						break
					end
					a = a.Parent
				end
			end
		end
		item.touches = touching
		-- копии на той же позиции (дубль)
		item.duplicateOf = nil
		for j = 1, i - 1 do
			local oj = objects[j].inst
			if oj.Name == inst.Name and (oj:GetPivot().Position - pv.Position).Magnitude < 0.05 then item.duplicateOf = j break end
		end
		out[#out + 1] = item
	end
end

return HttpService:JSONEncode({
	room = ROOM,
	bounds = {minX, minY, minZ, maxX, maxY, maxZ},
	total = #objects,
	count = #out,
	objects = out,
})
