-- Local, asset-free ceiling workstation. The server shares only its start time.
local Scene = {}
Scene.__index = Scene
-- PORTRAIT_BAKE

local SCALE = 2.64
local ORIGIN = CFrame.new(1020, 11.44, 45.7) * CFrame.Angles(0, math.rad(-96), 0) * CFrame.Angles(math.pi, 0, 0)
local BODY = Enum.Material.SmoothPlastic
local C = {
    oak = Color3.fromRGB(118, 83, 58),
    edge = Color3.fromRGB(79, 52, 39),
    steel = Color3.fromRGB(47, 62, 65),
    black = Color3.fromRGB(30, 41, 44),
    chair = Color3.fromRGB(53, 76, 80),
    shirt = Color3.fromRGB(224, 218, 196),
    seam = Color3.fromRGB(181, 175, 155),
    trousers = Color3.fromRGB(35, 49, 58),
    skin = Color3.fromRGB(185, 132, 98),
    nail = Color3.fromRGB(210, 157, 124),
    hair = Color3.fromRGB(64, 39, 29),
    bone = Color3.fromRGB(230, 225, 197),
    glaze = Color3.fromRGB(233, 228, 207),
    mint = Color3.fromRGB(70, 122, 110),
    coffee = Color3.fromRGB(48, 25, 16),
    crema = Color3.fromRGB(141, 88, 47),
    ink = Color3.fromRGB(33, 57, 59),
    panel = Color3.fromRGB(231, 237, 224),
    moss = Color3.fromRGB(73, 119, 107),
    warm = Color3.fromRGB(255, 233, 181),
}
local function v(x, depth, height)
    return Vector3.new(x, height, -depth) * SCALE
end
local function place(x, depth, height)
    return CFrame.new(v(x, depth, height))
end
local function model(parent, name, pivot)
    local m = Instance.new("Model")
    m.Name = name
    m.WorldPivot = pivot or CFrame.identity
    m.Parent = parent
    return m
end
local function part(parent, name, frame, size, color, shape, material)
    local p = Instance.new("Part")
    p.Name = name
    p.Shape = shape or Enum.PartType.Block
    p.Size = size
    p.Color = color
    p.Material = material or BODY
    p.CFrame = frame
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = size.Magnitude > .4
    p.Parent = parent
    return p
end
local function block(parent, name, frame, x, depth, height, color, material)
    return part(parent, name, frame, Vector3.new(x, height, depth) * SCALE, color, nil, material)
end
local function oval(parent, name, frame, x, depth, height, color)
    local piece=part(parent, name, frame, Vector3.new(x, height, depth) * SCALE, color)
    local mesh=Instance.new("SpecialMesh")
    mesh.MeshType=Enum.MeshType.Sphere
    mesh.Parent=piece
    return piece
end
local function disc(parent, name, frame, radius, height, color)
    return part(parent, name, frame * CFrame.Angles(0, 0, math.pi / 2),
        Vector3.new(height, radius * 2, radius * 2) * SCALE, color, Enum.PartType.Cylinder)
end
local function beam(parent, name, a, b, radius, color)
    local frame = CFrame.lookAt((a + b) * .5, b) * CFrame.Angles(0, math.pi / 2, 0)
    return part(parent, name, frame, Vector3.new((b - a).Magnitude, radius * 2 * SCALE, radius * 2 * SCALE), color, Enum.PartType.Cylinder)
end
local function roundCorner(frame, r)
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, r)
    corner.Parent = frame
end
local function surface(p, name, face, width, height)
    local g = Instance.new("SurfaceGui")
    g.Name = name
    g.Face = face
    g.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
    g.CanvasSize = Vector2.new(width, height)
    g.LightInfluence = 0
    g.MaxDistance = 42
    g.Parent = p
    return g
end
local function rect(parent, x, y, w, h, color)
    local f = Instance.new("Frame")
    f.Position = UDim2.fromOffset(x, y)
    f.Size = UDim2.fromOffset(w, h)
    f.BackgroundColor3 = color
    f.BorderSizePixel = 0
    f.Parent = parent
    return f
end
local function text(parent, label, x, y, w, h, size, color, bold)
    local t = Instance.new("TextLabel")
    t.Name = label
    t.BackgroundTransparency = 1
    t.Position = UDim2.fromOffset(x, y)
    t.Size = UDim2.fromOffset(w, h)
    t.Text = label
    t.TextXAlignment = Enum.TextXAlignment.Left
    t.TextColor3 = color
    t.TextSize = size
    t.Font = bold and Enum.Font.GothamBold or Enum.Font.Gotham
    t.Parent = parent
    return t
end

local function buildDesk(root)
    block(root, "Ceiling desk", place(0,.13,.768),1.86,.90,.071,C.oak,Enum.Material.Wood)
    block(root, "Walnut edge", place(0,-.319,.768),1.84,.014,.057,C.edge)
    for _, x in ipairs({-.81,.81}) do
        for _, depth in ipairs({-.24,.48}) do
            block(root,"Steel desk leg",place(x,depth,.365),.047,.047,.73,C.steel,Enum.Material.Metal)
            block(root,"Ceiling mount",place(x,depth,.009),.129,.105,.018,C.steel)
            for _, dx in ipairs({-.037,.037}) do
                disc(root,"Mount bolt",place(x+dx,depth,.022),.007,.009,C.black)
            end
        end
        beam(root,"Cross rail",v(x,-.24,.154),v(x,.48,.154),.016,C.steel)
    end
    block(root,"Seat cushion",place(0,-.68,.488),.47,.46,.089,C.chair,Enum.Material.Fabric)
    block(root,"Chair back",place(0,-.912,.811),.46,.104,.56,C.chair,Enum.Material.Fabric)
    beam(root,"Chair column",v(0,-.69,.104),v(0,-.69,.454),.036,C.steel)
    for i = 0, 4 do
        local angle = i * math.pi * 2 / 5
        local x, d = math.cos(angle)*.275, -.69+math.sin(angle)*.275
        beam(root,"Caster spoke",v(0,-.69,.127),v(x,d,.075),.015,C.steel)
        oval(root,"Caster wheel",place(x,d,.044),.073,.044,.064,C.black)
    end
    for _, x in ipairs({-.281,.281}) do
        beam(root,"Armrest support",v(x,-.72,.472),v(x,-.72,.644),.019,C.steel)
        block(root,"Armrest",place(x,-.68,.652),.074,.29,.043,C.black)
    end
    disc(root,"Lamp base",place(-.755,.402,.817),.092,.034,C.steel)
    beam(root,"Lamp upright",v(-.755,.402,.823),v(-.78,.453,1.151),.017,C.steel)
    beam(root,"Lamp upper arm",v(-.78,.453,1.151),v(-.65,.286,1.269),.016,C.steel)
    block(root,"Lamp enamel shade",place(-.65,.286,1.267),.188,.142,.051,C.mint)
    local diffuser=block(root,"Lamp warm diffuser",place(-.65,.281,1.237),.149,.103,.016,C.warm,Enum.Material.Neon)
    local pool=Instance.new("PointLight")
    pool.Name="Desk light"
    pool.Color=C.warm
    pool.Range=7
    pool.Brightness=1.10
    pool.Parent=diffuser
    local fill=Instance.new("PointLight")
    fill.Color=Color3.fromRGB(209,230,223)
    fill.Range=7
    fill.Brightness=.55
    fill.Parent=block(root,"Monitor bounce",place(.08,.12,1.05),.03,.03,.03,C.warm)
    fill.Parent.Transparency=1
    return pool,diffuser
end

local function buildMonitor(root)
    local monitor=model(root,"Monitor housing",place(.084,.398,1.078))
    block(monitor,"Monitor foot",place(.084,.38,.811),.29,.23,.030,C.steel)
    block(monitor,"Monitor stand",place(.084,.412,.912),.077,.071,.185,C.steel)
    block(monitor,"Monitor casing",place(.084,.398,1.078),.652,.093,.437,C.black)
    block(monitor,"Front bezel",place(.084,.349,1.078),.634,.039,.414,C.steel)
    local p=block(monitor,"Screen",place(.084,.326,1.080),.596,.011,.374,C.panel)
    local glow=Instance.new("SurfaceLight")
    glow.Name="Reflected monitor light"
    glow.Face=Enum.NormalId.Back
    glow.Color=Color3.fromRGB(220,233,241)
    glow.Range=5
    glow.Angle=105
    glow.Brightness=1.25
    glow.Parent=p
    local g=surface(p,"Work register",Enum.NormalId.Back,720,450)
    rect(g,0,0,720,450,C.panel)
    rect(g,0,0,720,48,C.ink)
    text(g,"КОНТУР",21,8,120,32,22,C.bone,true)
    text(g,"ВНУТРЕННИЙ РЕЕСТР / 4.2",147,10,320,28,13,C.bone)
    text(g,"А. МОРОЗОВ  ●  19:42",532,11,171,27,14,C.bone)
    rect(g,0,48,116,375,C.steel)
    for i, name in ipairs({"РАБОЧИЙ СТОЛ","Поручения","Входящие","Журналы","Архив"}) do
        if i==2 then roundCorner(rect(g,8,85,100,34,C.moss),5) end
        text(g,name,15,49+i*32,100,34,i==1 and 10 or 13,C.bone,i<=2)
    end
    text(g,"СМЕНА № 03",15,365,95,25,12,C.bone)
    text(g,"Реестр поручений",134,61,350,33,25,C.ink,true)
    text(g,"Отдел внутреннего учёта",136,91,330,22,14,C.moss)
    rect(g,136,122,350,28,Color3.fromRGB(196,215,201))
    text(g,"№     ПОРУЧЕНИЕ                         СТАТУС",142,122,338,28,12,C.ink,true)
    local status
    local orders={
        {"А-241", "Сверка накладных", "В работе"},
        {"А-238", "Ведомость пропусков", "Готово"},
        {"А-236", "Заявка на лампы", "Готово"},
        {"А-232", "Расход бумаги", "Открыто"},
        {"А-228", "Ключи от 3-го этажа", "Открыто"},
        {"А-227", "Журнал выдачи", "Готово"},
    }
    for i, row in ipairs(orders) do
        local y=150+(i-1)*35
        if i==1 then rect(g,136,y,350,34,Color3.fromRGB(207,225,195)) end
        rect(g,136,y+34,350,1,Color3.fromRGB(185,205,194))
        text(g,row[1],142,y,50,34,12,C.moss)
        text(g,row[2],194,y,220,34,14,C.ink,i==1)
        local flag=text(g,row[3],419,y,65,34,12,C.moss,i==1)
        if i==1 then status=flag end
    end
    local card=rect(g,505,122,196,283,Color3.fromRGB(243,242,224))
    roundCorner(card,6)
    text(card,"КАРТОЧКА  А-241",12,7,171,26,14,C.moss,true)
    text(card,"ПЛАН ОФИСА",12,30,181,23,14,C.ink,true)
    local map=rect(card,12,55,172,128,C.ink)
    map.ClipsDescendants=true
    local function project(x,z)
        return (x-964)/148*172,(z+32)/120*128
    end
    for _, room in ipairs({
        {1000,1032,-32,0},{1032,1096,-32,0},{964,1000,8,52},
        {1008,1056,8,60},{1064,1112,8,60},{1000,1008,0,76},
        {1056,1064,0,68},{1008,1032,68,88},{1032,1056,68,88},{976,1000,56,76},
    }) do
        local x1,y1=project(room[1],room[3])
        local x2,y2=project(room[2],room[4])
        rect(map,x1,y1,x2-x1,y2-y1,C.moss)
        rect(map,x1+1,y1+1,x2-x1-2,y2-y1-2,C.ink)
    end
    local marker=rect(map,0,0,7,7,Color3.fromRGB(255,184,75))
    marker.Name="Local player on office plan"
    marker.AnchorPoint=Vector2.new(.5,.5)
    marker.Visible=false
    roundCorner(marker,5)
    text(card,"СЛУЖЕБНАЯ ЗАМЕТКА",12,194,177,22,11,C.moss,true)
    local note=text(card,"Ожидает сверки",12,218,173,52,12,C.ink)
    note.TextWrapped=true
    local cursor=text(g,"›",461,154,24,25,23,C.ink,true)
    rect(g,0,423,720,27,Color3.fromRGB(199,219,204))
    local saved=text(g,"●   ЛОКАЛЬНАЯ КОПИЯ",19,424,291,26,12,C.moss,true)
    text(g,"ОТДЕЛ 04  /  АРХИВ",569,424,144,26,12,C.moss)
    local led=oval(monitor,"Monitor green LED",place(.36,.324,.884),.009,.004,.009,Color3.fromRGB(131,230,119))
    led.Material=Enum.Material.Neon
    monitor:PivotTo(place(.48,.398,1.078)*CFrame.Angles(0,math.rad(-20),0))
    return {status=status,note=note,saved=saved,cursor=cursor,marker=marker,project=project}
end

local function buildKeyboard(root)
    block(root,"Keyboard shell",place(0,-.133,.813),.563,.233,.028,C.black)
    block(root,"Switch plate",place(0,-.133,.827),.535,.211,.009,C.steel)
    local keys={}
    local rows={"1234567890-=","QWERTYUIOP[]","ASDFGHJKL;","ZXCVBNM,./"}
    for r, row in ipairs(rows) do
        local shift=r>=3 and .009 or 0
        for i=1,#row do
            local letter=row:sub(i,i)
            local frame=place(-.235+(i-1)*.041+shift,-.054-(r-1)*.0418,.836)
            local key=block(root,"Key "..letter,frame,.037,.036,.013,C.bone)
            if string.find("DFGJKL",letter,1,true) then
                keys[letter]={key=key,frame=frame}
            end
            if r==3 then
                local label=surface(key,"Legend",Enum.NormalId.Top,32,32)
                text(label,letter,8,3,22,26,19,C.ink,true)
            end
        end
    end
    block(root,"Space bar",place(-.010,-.222,.836),.247,.034,.013,C.bone)
    for _, x in ipairs({-.233,-.17,.156,.215}) do
        block(root,"Control key",place(x,-.222,.836),.049,.035,.013,C.steel)
    end
    block(root,"Mouse pad",place(.339,-.141,.807),.259,.258,.008,C.black)
    local mouse=model(root,"Mouse",place(.326,-.13,.818))
    local base=mouse.WorldPivot
    oval(mouse,"Mouse shell",base*place(0,0,.018),.083,.14,.048,C.black)
    for _, x in ipairs({-.020,.020}) do
        oval(mouse,"Mouse button",base*place(x,.034,.033),.038,.057,.013,C.steel)
    end
    oval(mouse,"Scroll wheel",base*place(0,.042,.046),.012,.023,.016,C.black)
    return keys,mouse
end

local function buildCup(root)
    local cup=model(root,"Coffee mug",place(.596,-.065,.806))
    local base=cup.WorldPivot
    disc(cup,"Ceramic base",base*place(0,0,.006),.048,.012,C.glaze)
    local count=30
    for i=1,count do
        local a=(i-1)*math.pi*2/count
        local cs,sn=math.cos(a),math.sin(a)
        block(cup,"Ceramic shell",base*place(.052*cs,.052*sn,.056)*CFrame.Angles(0,a,0),.007,.0123,.105,C.glaze)
        block(cup,"Glazed rim",base*place(.052*cs,.052*sn,.111)*CFrame.Angles(0,a,0),.010,.0123,.005,C.glaze)
        block(cup,"Printed green band",base*place(.056*cs,.056*sn,.027)*CFrame.Angles(0,a,0),.002,.0126,.004,C.mint)
    end
    local handle={{.051,.083},{.074,.089},{.096,.079},{.106,.061},{.101,.043},{.084,.028},{.063,.029},{.051,.035}}
    for i, p in ipairs(handle) do
        local at=base*v(p[1],0,p[2])
        oval(cup,"Handle curve",CFrame.new(at),.021,.020,.021,C.glaze)
        if i>1 then
            local prev=handle[i-1]
            beam(cup,"Handle stem",base*v(prev[1],0,prev[2]),at,.0105,C.glaze)
        end
    end
    disc(cup,"Coffee surface",base*place(0,0,.090),.048,.006,C.coffee)
    for i=1,11 do
        local a=i*2.39996
        local d=.031+.012*(i%3)/2
        disc(cup,"Crema bubble",base*place(d*math.cos(a),d*math.sin(a),.0933),.0025+.001*(i%3),.0015,C.crema)
    end
    local anchor=block(cup,"Steam source",base*place(0,0,.100),.012,.012,.008,C.glaze)
    anchor.Transparency=1
    local steam=Instance.new("ParticleEmitter")
    steam.Name="Coffee steam"
    steam.Texture="rbxasset://textures/particles/smoke_main.dds"
    steam.EmissionDirection=Enum.NormalId.Top
    steam.Color=ColorSequence.new(Color3.fromRGB(212,222,218))
    steam.Lifetime=NumberRange.new(.77,1.24)
    steam.Speed=NumberRange.new(.20,.38)
    steam.Rate=11
    steam.SpreadAngle=Vector2.new(11,11)
    steam.RotSpeed=NumberRange.new(-22,22)
    steam.Size=NumberSequence.new({
        NumberSequenceKeypoint.new(0,.036),NumberSequenceKeypoint.new(.48,.127),NumberSequenceKeypoint.new(1,.224),
    })
    steam.Transparency=NumberSequence.new({
        NumberSequenceKeypoint.new(0,1),NumberSequenceKeypoint.new(.18,.66),NumberSequenceKeypoint.new(.5,.82),NumberSequenceKeypoint.new(1,1),
    })
    steam.LightEmission=.37
    steam.Parent=anchor
    return cup
end

local function buildPaper(root)
    block(root,"File cover",place(-.599,.022,.807),.266,.312,.013,C.mint)
    for i=1,4 do
        block(root,"Paper stack",place(-.596+.002*i,.014,.813+.0018*i)*CFrame.Angles(0,.023*i,0),.214,.269,.0018,C.bone)
    end
    local sheet=model(root,"Inspection form",place(-.583,.019,.824))
    local body=block(sheet,"A-241 sheet",sheet.WorldPivot,.213,.273,.003,C.bone)
    local g=surface(body,"Printed inspection form",Enum.NormalId.Top,216,280)
    rect(g,0,0,216,280,C.bone)
    rect(g,0,0,216,28,C.moss)
    text(g,"КОНТУР  /  УЧЁТ",12,2,196,23,14,C.bone,true)
    text(g,"Лист сверки",12,35,191,30,22,C.ink,true)
    text(g,"А-241   ·   14 НОЯБРЯ",12,70,191,20,13,C.moss)
    for i, pair in ipairs({{"Реестр накладных","07"},{"Талоны приёмки","06"},{"Листы возврата","05"}}) do
        local y=100+(i-1)*35
        rect(g,11,y,193,30,Color3.fromRGB(215,219,196))
        text(g,pair[1],16,y,154,30,13,C.ink)
        text(g,pair[2].." ✓",162,y,41,30,13,C.moss,true)
    end
    text(g,"ИТОГО  18 / 18",13,208,173,22,15,C.moss,true)
    text(g,"А. Морозов",13,244,126,22,13,C.ink)
    text(g,"СВЕРЕНО",129,244,72,22,13,Color3.fromRGB(143,80,66),true)
    beam(root,"Pen barrel",v(-.774,-.112,.824),v(-.658,-.091,.824),.0065,C.mint)
    beam(root,"Pen nib",v(-.658,-.091,.824),v(-.642,-.089,.824),.0035,C.steel)
    block(root,"Pen clip",place(-.759,-.109,.833),.031,.005,.004,C.steel)
    return sheet
end

local function buildFace(parent)
    local head=model(parent,"Worker head",place(0,-.627,1.266))
    local f=head.WorldPivot
    oval(head,"Head",f,.231,.219,.259,C.skin)
    oval(head,"Hair",f*place(0,-.026,.101),.235,.190,.102,C.hair)
    for i=1,6 do
        local x=-.080+(i-1)*.031
        oval(head,"Combed hair lock",f*place(x,.018,.117+.014*math.sin(i)),.054,.166,.049,C.hair)
    end
    oval(head,"Nose",f*place(0,.107,-.015),.048,.050,.059,C.skin)
    oval(head,"Mouth",f*place(0,.098,-.066),.065,.013,.009,C.hair)
    local eyes={}
    for i, sign in ipairs({-1,1}) do
        local x=sign*.050
        oval(head,"Ear",f*place(sign*.115,0,-.004),.042,.060,.070,C.skin)
        local socket=oval(head,"Sclera",f*place(x,.094,.031),.052,.024,.031,C.glaze)
        local pupil=oval(head,"Pupil "..i,f*place(x,.108,.031),.021,.010,.023,C.ink)
        local glint=oval(head,"Catchlight",f*place(x-.004,.114,.037),.006,.004,.006,C.glaze)
        oval(head,"Brow",f*place(x,.091,.060)*CFrame.Angles(0,0,sign*.10),.057,.018,.012,C.hair)
        eyes[i]={socket=socket,pupil=pupil,glint=glint,x=x}
    end
    return head,eyes
end

local function buildHand(parent, sign)
    local hand={palm=oval(parent,"Palm",CFrame.identity,.090,.086,.037,C.skin),fingers={}}
    for i, spec in ipairs({
        {-.034,.077},{-.012,.096},{.011,.099},{.033,.079},{-.047,.064},
    }) do
        local segments={}
        for j, fraction in ipairs({.43,.33,.24}) do
            local length=spec[2]*fraction
            local width=(i==5 and .022 or .018)-j*.0012
            segments[j]={
                length=length*SCALE,
                segment=oval(parent,"Finger phalanx",CFrame.identity,width,length+.009,width*.91,C.skin),
                nail=j==3 and oval(parent,"Fingernail",CFrame.identity,width*.72,length*.73,.004,C.nail) or nil,
            }
        end
        hand.fingers[i]={x=sign*spec[1],thumb=i==5,segments=segments}
    end
    return hand
end
local function buildWorker(root)
    local worker=model(root,"Seated worker",place(0,-.68,.54))
    local torso=model(worker,"Torso",place(0,-.688,.869))
    local f=torso.WorldPivot
    oval(torso,"Shirt",f,.398,.256,.430,C.shirt)
    block(torso,"Button placket",f*place(0,.123,-.010),.022,.007,.32,C.seam)
    block(torso,"Pocket",f*place(-.110,.118,.021),.083,.014,.072,C.seam)
    block(torso,"Badge",f*place(-.112,.132,.028),.059,.008,.029,C.bone)
    for i=1,5 do
        oval(torso,"Shirt button",f*place(.006,.127,-.18+i*.057),.013,.006,.013,C.bone)
    end
    oval(worker,"Neck",place(0,-.641,1.111),.113,.103,.130,C.skin)
    for _, x in ipairs({-.099,.099}) do
        oval(worker,"Seated thigh",place(x,-.536,.552),.183,.391,.169,C.trousers)
        oval(worker,"Trousers",place(x,-.356,.343),.125,.128,.461,C.trousers)
        oval(worker,"Shoe",place(x,-.277,.095),.138,.222,.088,C.black)
    end
    local head,eyes=buildFace(worker)
    local arms={}
    for i,sign in ipairs({-1,1}) do
        arms[i]={
            sign=sign,
            upper=oval(worker,"Sleeve",CFrame.identity,.145,.15,.25,C.shirt),
            fore=oval(worker,"Forearm",CFrame.identity,.102,.108,.26,C.skin),
            cuff=oval(worker,"Sleeve cuff",CFrame.identity,.112,.105,.069,C.seam),
            hand=buildHand(worker,sign),
        }
    end
    return {root=worker,torso=torso,head=head,eyes=eyes,arms=arms}
end

function Scene.new(parent)
    local root=model(nil,"CeilingWorkstation")
    local lamp,diffuser=buildDesk(root)
    local monitor=buildMonitor(root)
    local keys,mouse=buildKeyboard(root)
    local cup=buildCup(root)
    local sheet=buildPaper(root)
    local worker=buildWorker(root)
    local self=setmetatable({
        root=root,monitor=monitor,keys=keys,mouse=mouse,cup=cup,sheet=sheet,worker=worker,
        yaw=0,pitch=0,eyeYaw=0,eyePitch=0,activity=1,lamp=lamp,diffuser=diffuser,
    },Scene)
    root:PivotTo(ORIGIN)
    self:Update(0,nil,1/30)
    root.Parent=parent
    if game:GetService("RunService"):IsStudio() then
        root:SetAttribute("PortraitMode","Loading")
        task.spawn(function()
            local portrait,problem=Portrait.build(ORIGIN)
            if not root.Parent then
                if portrait then Portrait.destroy(portrait) end
                return
            end
            if not portrait then
                root:SetAttribute("PortraitMode","Parts")
                warn("Ceiling anatomy preview: "..problem)
                return
            end
            self.worker.root:Destroy()
            local chairShift=portraitData.seat-v(0,-.68,.488)
            for _,object in root:GetChildren() do
                local name=object.Name
                if name:match("^Key ") or name=="Keyboard shell" or name=="Switch plate"
                    or name=="Control key" or name=="Space bar" then
                    object:Destroy()
                elseif name=="Seat cushion" or name=="Chair back" or name=="Armrest" or name=="Armrest support" then
                    object.CFrame+=ORIGIN:VectorToWorldSpace(chairShift)
                elseif name=="Caster spoke" or name=="Caster wheel" or name=="Chair column" then
                    local shift=Vector3.new(0,0,chairShift.Z)
                    if name=="Chair column" then
                        shift+=Vector3.yAxis*chairShift.Y*.5
                        object.Size+=Vector3.xAxis*chairShift.Y
                    end
                    object.CFrame+=ORIGIN:VectorToWorldSpace(shift)
                end
            end
            portrait.model.Parent=root
            self.portrait=portrait
            root:SetAttribute("PortraitMode","Anatomy")
        end)
    end
    return self
end

local function eased(t,a,b)
    local d=math.clamp((t-a)/(b-a),0,1)
    return d*d*(3-2*d)
end
local function pulse(t,a,b,c,d)
    return eased(t,a,b)*(1-eased(t,c,d))
end
local function span(p,a,b,radius)
    local d=b-a
    p.Size=Vector3.new(radius*SCALE,d.Magnitude*1.14,radius*SCALE)
    p.CFrame=ORIGIN*CFrame.lookAt((a+b)*.5,b)*CFrame.Angles(math.pi/2,0,0)
end

local handKeys={{"G","F","D"},{"J","K","L"}}

local function moveHand(arm, frame, grip, keys, labels, typing)
    arm.hand.palm.CFrame=ORIGIN*frame*place(0,.036,0)
    for i,finger in ipairs(arm.hand.fingers) do
        local base=frame*place(finger.x,finger.thumb and .028 or .068,0)
            * CFrame.Angles(0,finger.thumb and arm.sign*.69 or (i-2.5)*.05*(1-grip),0)
        local key=keys[labels[i]]
        if key then
            local capHeight=key.frame.Position.Y+SCALE*(.0065-.0048*key.press)
            local contactHeight=capHeight+.007*SCALE*(1-key.press)
            local tip=Vector3.new(key.frame.Position.X,contactHeight,key.frame.Position.Z)
            local start=base.Position
            local reach=tip-start
            local arch=Vector3.yAxis*(.014*SCALE)
            local joints={start,start+reach*.36+arch,start+reach*.72+arch*.62,tip}
            for j,seg in ipairs(finger.segments) do
                base=base*CFrame.Angles(-(.11+.095*j+grip*(.50+.07*j)),0,0)
                local free=base*CFrame.new(0,0,-seg.length*.50)
                local a,b=joints[j],joints[j+1]
                local touch=CFrame.lookAt((a+b)*.5,b)
                local size=seg.segment.Size
                local touchLength=(b-a).Magnitude+.009*SCALE
                if j==#finger.segments then
                    -- For an ellipsoid, find its lowest point along the key's vertical axis.
                    local radius=math.sqrt((touch.RightVector.Y*size.X)^2
                        +(touch.UpVector.Y*size.Y)^2+(touch.LookVector.Y*touchLength)^2)*.5
                    touch+=Vector3.yAxis*(contactHeight-touch.Position.Y+radius)
                end
                local pose=free:Lerp(touch,typing)
                seg.segment.CFrame=ORIGIN*pose
                seg.segment.Size=Vector3.new(size.X,size.Y,(seg.length+.009*SCALE)*(1-typing)+touchLength*typing)
                if seg.nail then seg.nail.CFrame=ORIGIN*pose*CFrame.new(0,.005*SCALE,-.004*SCALE) end
                base=base*CFrame.new(0,0,-seg.length)
            end
            continue
        end
        for j, seg in ipairs(finger.segments) do
            base=base*CFrame.Angles(-(.09+.10*j+grip*(.50+.07*j)),0,0)
            seg.segment.CFrame=ORIGIN*base*CFrame.new(0,0,-seg.length*.50)
            if seg.nail then seg.nail.CFrame=ORIGIN*base*CFrame.new(0,.005*SCALE,-seg.length*.57) end
            base=base*CFrame.new(0,0,-seg.length)
        end
    end
end

local NOTES={"С","Св","Све","Свер","Свере","Сверен","Сверено","Сверено 18","Сверено 18 из","Сверено 18 из 18.","Сверено 18 из 18. Замечаний нет."}

function Scene:GetLookPoint()
    if self.portrait then
        return self.portrait.meshes.face.part.Position
    end
    return self.worker.head:GetPivot().Position
end

function Scene:SetLamp(on)
    if on == self.lampOn then return end
    self.lampOn=on
    self.lamp.Enabled=on
    self.diffuser.Material=on and Enum.Material.Neon or BODY
end

function Scene:Update(elapsed,target,dt,playerPosition)
    self.attention=target and ((self.attention or 0)+dt) or 0
    self.resumeDelay=target and .22 or math.max(0,(self.resumeDelay or 0)-dt)
    self.activity+=((self.resumeDelay>0 and 0 or 1)-self.activity)*(1-math.exp(-dt*10))
    self.workTime=(self.workTime or elapsed)+dt*self.activity
    local t=self.workTime%20
    local mouse=pulse(t,4.35,4.90,6.02,6.49)
    if self.portrait then
        Portrait.update(self.portrait,ORIGIN,self.attention>=.14 and target or nil,dt,self.activity)
    else
    local grip=pulse(t,6.45,6.96,9.78,10.25)
    local lift=pulse(t,6.97,7.85,8.88,9.77)
    local paper=pulse(t,10.43,11.05,13.65,14.15)
    local raised=pulse(t,11.10,11.73,12.98,13.60)
    local left=self.worker
    local pitch=.055+.070*raised-.095*lift
    local yaw=.047+.037*math.sin(t*1.23)
    local eyeYaw,eyePitch=0,0
    local headPosition=v(0,-.627+.012*math.sin(t*1.4),1.266+.005*math.sin(t*2.6))
    if target then
        local delta=ORIGIN:PointToObjectSpace(target)-headPosition
        if delta.Magnitude>.05 then
            local unit=delta.Unit
            local side=math.atan2(-unit.X,-unit.Z)
            local up=math.asin(unit.Y)
            yaw=math.clamp(side*.83,-1.02,1.02)
            pitch=math.clamp(up*.80,-.68,.90)
            eyeYaw=math.clamp((side-yaw)*.024,-.016,.016)
            eyePitch=math.clamp((up-pitch)*.024,-.011,.011)
        end
    end
    local headEase=1-math.exp(-dt*6)
    local eyeEase=1-math.exp(-dt*18)
    self.yaw+=(yaw-self.yaw)*headEase
    self.pitch+=(pitch-self.pitch)*headEase
    self.eyeYaw+=(eyeYaw-self.eyeYaw)*eyeEase
    self.eyePitch+=(eyePitch-self.eyePitch)*eyeEase
    local pose=CFrame.new(headPosition)*CFrame.Angles(0,self.yaw,0)*CFrame.Angles(self.pitch,0,0)
    local head=ORIGIN*pose
    left.head:PivotTo(head)
    left.torso:PivotTo(ORIGIN*place(0,-.688,.869+.007*math.sin(t*2.6)+.012*lift)
        *CFrame.Angles(.044+.031*math.sin(t*.98)-.050*raised,0,0))
    local blink=math.clamp(math.abs((t+.15)%2.65-1.39)/.10,.07,1)
    for _, eye in ipairs(left.eyes) do
        eye.socket.Size=Vector3.new(.052,.031*blink,.024)*SCALE
        eye.pupil.Size=Vector3.new(.021,.023*blink,.010)*SCALE
        eye.pupil.CFrame=head*place(eye.x-self.eyeYaw,.108,.031+self.eyePitch)
        eye.glint.CFrame=head*place(eye.x-self.eyeYaw-.004,.114,.035+self.eyePitch)
        eye.glint.Transparency=blink<.30 and 1 or 0
    end

    local cupPosition=v(.596,-.065,.806):Lerp(v(.086,-.450,1.160),lift)
    local cupPose=CFrame.new(cupPosition)*CFrame.Angles(.44*lift,-.17*lift,.12*lift)
    if self.cupLift ~= lift then
        self.cup:PivotTo(ORIGIN*cupPose)
        self.cupLift=lift
    end
    local sheetPosition=v(-.583,.019,.824):Lerp(v(-.303,-.322,.988),raised)
    local sheetPose=CFrame.new(sheetPosition)*CFrame.Angles(.60*raised,-.108+.26*raised,-.11*raised)
    if self.paperLift ~= raised then
        self.sheet:PivotTo(ORIGIN*sheetPose)
        self.paperLift=raised
    end
    local mousePosition=v(.326+.028*mouse*math.sin(t*7),-.13+.024*mouse*math.sin(t*4),.818)
    if mouse>0 or self.mouseMoving then
        self.mouse:PivotTo(ORIGIN*CFrame.new(mousePosition)*CFrame.Angles(0,.1*mouse*math.sin(t*5),0))
        self.mouseMoving=mouse>0
    end
    for i,labels in ipairs(handKeys) do
        local typing=(1-(i==1 and paper or math.max(grip,mouse)))*self.activity
        for finger,letter in ipairs(labels) do
            local k=self.keys[letter]
            k.press=math.max(0,math.sin(t*17.8+i*2.6+finger*1.9))^9*typing
            k.key.CFrame=ORIGIN*k.frame*CFrame.new(0,-.0048*SCALE*k.press,0)
        end
    end
    for i, arm in ipairs(left.arms) do
        local isRight=arm.sign>0
        local typing=1-(isRight and math.max(grip,mouse) or paper)
        local wrist=v(isRight and .061 or -.103,-.282,.885)
        if isRight then
            wrist=wrist:Lerp(mousePosition+v(.002,-.071,.044),mouse)
            wrist=wrist:Lerp(cupPose*v(.093,-.067,.056),grip)
        else
            wrist=wrist:Lerp(sheetPose*v(-.070,-.153,.022),paper)
        end
        local holding=isRight and grip or paper
        local up=isRight and lift or raised
        local shoulder=v(arm.sign*.192,-.665,1.007+.012*lift)
        local elbow=v(arm.sign*.127,-.508,.878):Lerp(
            v(arm.sign*(.223+.034*math.max(holding,mouse)),-.503,.752+.144*up),1-typing)
        span(arm.upper,shoulder,elbow,.148)
        span(arm.fore,elbow,wrist,.110)
        arm.cuff.CFrame=ORIGIN*CFrame.lookAt(elbow:Lerp(wrist,.24),wrist)*CFrame.Angles(math.pi/2,0,0)
        local hand=CFrame.new(wrist)*CFrame.Angles(isRight and .15*mouse or .38*raised,
            (isRight and -.11 or .11)-.60*(isRight and grip or 0),isRight and .88*grip or -.06*raised)
        moveHand(arm,hand,holding,self.keys,handKeys[i],typing)
    end
    end

    local s=self.monitor
    local noteIndex=math.clamp(math.floor((t-14.20)*6)+1,1,#NOTES)
    local screen=t>=18.04 and "saved" or t>=14.20 and tostring(noteIndex) or "work"
    if screen~=self.screen then
        s.note.Text=screen=="work" and "Ожидает сверки\nпо бумажному журналу." or NOTES[noteIndex]
        s.status.Text=screen=="saved" and "Готово" or "В работе"
        s.saved.Text=screen=="saved" and "●   СОХРАНЕНО" or "●   ЛОКАЛЬНАЯ КОПИЯ"
        self.screen=screen
    end
    local cursorMotion=self.portrait and 0 or mouse
    s.cursor.Position=UDim2.fromOffset(462+cursorMotion*math.sin(t*7)*17,154+cursorMotion*math.sin(t*4)*12)
    if playerPosition then
        local x,y=s.project(playerPosition.X,playerPosition.Z)
        s.marker.Visible=x>=0 and x<=172 and y>=0 and y<=128
        s.marker.Position=UDim2.fromOffset(x,y)
    end
end

function Scene:Destroy()
    if self.portrait then Portrait.destroy(self.portrait) end
    self.root:Destroy()
end

return Scene
