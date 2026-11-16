--!strict
-- Подсчёт объектов карты для оценки нагрузки. Запускать в Studio (Edit или Play, сервер).
-- Печатает итог и разбивку по прямым потомкам OfficeMap и Rooms; JSON в конце для журнала.
local HttpService = game:GetService("HttpService")

local function count(root: Instance)
	local c = {
		parts = 0, meshparts = 0, lights = 0, shadowLights = 0, emitters = 0,
		sounds = 0, scripts = 0, beams = 0, decals = 0, models = 0, tris = 0,
	}
	local function visit(i: Instance)
		if i:IsA("MeshPart") then
			c.meshparts += 1
		elseif i:IsA("BasePart") then
			c.parts += 1
		elseif i:IsA("Light") then
			c.lights += 1
			if (i :: any).Shadows then c.shadowLights += 1 end
		elseif i:IsA("ParticleEmitter") then
			c.emitters += 1
		elseif i:IsA("Sound") then
			c.sounds += 1
		elseif i:IsA("LuaSourceContainer") then
			c.scripts += 1
		elseif i:IsA("Beam") or i:IsA("Trail") then
			c.beams += 1
		elseif i:IsA("Decal") or i:IsA("Texture") or i:IsA("SurfaceAppearance") then
			c.decals += 1
		elseif i:IsA("Model") then
			c.models += 1
		end
	end
	visit(root)
	for _, d in root:GetDescendants() do
		visit(d)
	end
	return c
end

local office = workspace:FindFirstChild("OfficeMap") or workspace
local result: {[string]: any} = { total = count(office), groups = {} }
local groups = result.groups :: {[string]: any}

local function addGroup(prefix: string, parent: Instance?)
	if not parent then return end
	for _, child in parent:GetChildren() do
		groups[prefix .. child.Name] = count(child)
	end
end
addGroup("", office)
addGroup("Rooms/", office:FindFirstChild("Rooms"))

local json = HttpService:JSONEncode(result)
print("KONTUR_BUDGET " .. json)
return json
