-- Local liquid visuals: the surface changes shape; no rigid crest object.
local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local Run=game:GetService("RunService")
local player=Players.LocalPlayer
local office=workspace:WaitForChild("OfficeMap")
local shared=assert(office:WaitForChild("BloodFloodState",60),"Local flood server did not initialize")
local regionFolder=shared:WaitForChild("Regions")
local Defaults=require(RS:WaitForChild("BloodFloodConfig"))
local Surface=require(RS:WaitForChild("BloodLiquidSurface"))
local Seep=require(RS:WaitForChild("BloodFloodSeep"))
local Impacts=require(RS:WaitForChild("BloodImpactSurface"))
local WallFilm=require(RS:WaitForChild('BloodWallSurface'))
local assets=RS:WaitForChild("BloodFloodAssets")
task.spawn(function()pcall(function()game:GetService("ContentProvider"):PreloadAsync({assets})end)end)
local templates={}
for _,o in ipairs(assets:GetDescendants())do if o:IsA("MeshPart")then templates[o.Name]=o end end
assert(templates.Blood_Body,"Missing verified local blood material")
local appearance=templates.Blood_Body:FindFirstChildOfClass("SurfaceAppearance")
local folder=Instance.new("Folder");folder.Name="BloodFloodVisuals";folder.Parent=workspace
local regions,tiles,marks={},{},{}
local sourceCache=nil
local epoch=0
local function setting(name)return shared:GetAttribute(name)or Defaults[name]end
local function make(name)
    local p=templates[name]:Clone();p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
    p.CastShadow=false;p.Parent=folder;return p
end
local function clear()
    epoch+=1
    for _,tile in pairs(tiles)do if tile.surface then tile.surface:Destroy()end end
    if sourceCache and sourceCache.surface then sourceCache.surface:Destroy()end
    if sourceCache and sourceCache.impacts then sourceCache.impacts:Destroy()end
    if sourceCache and sourceCache.walls then sourceCache.walls:Destroy()end
    folder:ClearAllChildren();tiles={};marks={};regions={};sourceCache=nil
end
local function collect()
    regions={}
    for _,o in ipairs(regionFolder:GetChildren())do local a=o:GetAttributes()
        if a.id and a.start and a.id~="SourceEast"then table.insert(regions,a)end
    end
end
regionFolder.ChildAdded:Connect(collect);regionFolder.ChildRemoved:Connect(collect)
local function drawRegions(now)
    local started=shared:GetAttribute("StartedAt")or 0
    local tile=tiles.Office
    if not tile then
        tile={pending=true};tiles.Office=tile;local token=epoch
        task.spawn(function()
            local config=table.clone(Defaults);for k in pairs(config)do config[k]=setting(k)end
            local topology=require(RS.BloodFloodTopology).New(config)
            topology:Start(0,0);topology:Step(100,function()return true end,function()end)
            local defs={}
            for id,r in pairs(topology.regions)do
                if id~="SourceEast"then
                    r=table.clone(r)
                    if id=="West"or id=="East"then r.z0=7.65 end
                    if id=="SouthW"or id=="SouthE"then r.x0=1007.65;r.x1=1056.35 end
                    if id=="Entry"then r.z1=.35 end
                    -- Cover the measured 0.7-stud wall thickness inside door openings.
                    if id=="NW"then r.z1=.35 end
                    if id=="WEST"then r.x1=1000.35 end
                    if id=="CENTER"then r.x0=1007.65 end
                    if id=="EAST"then r.x0=1063.65 end
                    if id=="MEN"or id=="WOMEN"then r.z0=67.65 end
                    if id=="ReceptionEntry"then r.x1=1000.35 end
                    table.insert(defs,r)
                end
            end
            local ok,surface=pcall(Surface.New,defs,folder,appearance,config)
            if token~=epoch then if ok then surface:Destroy()end;return end
            tile.pending=false
            if ok then tile.surface=surface else tile.error=tostring(surface);warn("Local fluid surface: "..tile.error)end
        end)
    elseif tile.surface then tile.surface:Update(now,started,regions)end
end
local function sourceMarks(elapsed,started)
    if not sourceCache then
        local cache={rims={}};sourceCache=cache;local token=epoch
        task.spawn(function()
            local ok,walls=pcall(WallFilm.New,folder,function()return token~=epoch end)
            if token~=epoch then if ok then walls:Destroy()end;return end
            if ok then cache.walls=walls else warn('Local porous plaster: '..tostring(walls))end
        end)
        task.spawn(function()
            local ok,surface=pcall(require(RS.BloodSeepSurface).New,folder,appearance)
            if token~=epoch then if ok then surface:Destroy()end;return end
            if ok then cache.surface=surface else warn('Local continuous seep: '..tostring(surface))end
            local impactOK,impact=pcall(Impacts.New,folder,appearance)
            if token~=epoch then if impactOK then impact:Destroy()end;return end
            if impactOK then cache.impacts=impact else warn('Local impact detail: '..tostring(impact))end
        end)
        for i,s in ipairs(Seep.LampRim)do
            local p=Instance.new('Part');p.Name='BloodOnLampEdge_'..i;p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
            p.Material=Enum.Material.SmoothPlastic;p.Color=Color3.fromRGB(100,2,8);p.Reflectance=.05;p.CastShadow=false;p.CFrame=CFrame.new(s.position);p.Parent=folder
            cache.rims[i]=p
        end
        local anchor=Instance.new('Part');anchor.Name='SourceSound';anchor.Size=Vector3.one*.1;anchor.CFrame=CFrame.new(1090,6,-27)
        anchor.Transparency=1;anchor.Anchored=true;anchor.CanCollide=false;anchor.CanQuery=false;anchor.CanTouch=false;anchor.Parent=folder
        local function sound(name,id,speed)
            local s=Instance.new('Sound');s.Name=name;s.SoundId=id;s.Looped=true;s.Volume=0;s.PlaybackSpeed=speed
            s.RollOffMinDistance=12;s.RollOffMaxDistance=180;s.RollOffMode=Enum.RollOffMode.InverseTapered;s.Parent=anchor;return s
        end
        cache.rumble=sound('PressureRumble',setting('RumbleSoundId'),setting('RumblePlaybackSpeed'))
        local eq=Instance.new('EqualizerSoundEffect');eq.LowGain=3;eq.MidGain=-12;eq.HighGain=-20;eq.Parent=cache.rumble
        cache.surge=sound('Surge',setting('SurgeSoundId'),setting('SurgePlaybackSpeed'))
    end
    if sourceCache.surface then sourceCache.surface:Update(elapsed)end
    if sourceCache.impacts then sourceCache.impacts:Update(elapsed,workspace.CurrentCamera)end
    for i,s in ipairs(Seep.LampRim)do
        local p=sourceCache.rims[i];local growth=math.clamp((elapsed-(s.delay or 5))/(s.duration or 8),0,1)
        p.Transparency=growth>.015 and 0 or 1
        p.Size=Vector3.new(math.max(.025,s.size.X*growth),s.size.Y*(1+.12*math.sin(elapsed+i)),math.max(.025,s.size.Z*growth))
    end
    local warning=setting('RumbleBeginsAt')
    if started and elapsed>=warning then
        if not sourceCache.rumble.IsPlaying then sourceCache.rumble:Play()end
        sourceCache.rumble.Volume=setting('RumbleMaxVolume')*math.clamp((elapsed-warning)/12,0,1)
    end
    if started and elapsed>=setting('SourceBeginsAt')then
        if not sourceCache.surge.IsPlaying then sourceCache.surge:Play()end
        sourceCache.surge.Volume=setting('SurgeMaxVolume')*math.clamp((elapsed-setting('SourceBeginsAt'))/3,0,1)
    end
    if sourceCache.walls then sourceCache.walls:Update(elapsed)end
end
local was=false
Run.RenderStepped:Connect(function()
    local active=shared:GetAttribute("Active")==true and player:GetAttribute("KonturZone")=="Office"
    if not active then if was then clear();was=false end;return end
    if not was then was=true;collect()end
    local now=workspace:GetServerTimeNow();local start=shared:GetAttribute("StartedAt") or 0
    local elapsed=start>0 and math.max(0,now-start) or 0
    sourceMarks(elapsed,start>0)
    drawRegions(now)
end)
