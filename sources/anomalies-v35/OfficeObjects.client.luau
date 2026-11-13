task.spawn(function()
    local Players=game:GetService("Players")
    local RunService=game:GetService("RunService")
    local player=Players.LocalPlayer
    local office=workspace:WaitForChild("OfficeMap")
    local state=office:WaitForChild("AnomalyReportState")
    local phase=state:WaitForChild("Phase")
    local scene,current,roundId
    local archiveRound, archiveRead, archiveChanged
    local archiveAt=Vector3.new(1031.785,5.36,-17.1)
    local ventAt=ventMount+Vector3.xAxis*.24
    local doorAt=doorMount+Vector3.yAxis*4.45
    local update
    local function part(parent,name,size,color,material,pose,alpha)
        local p=Instance.new("Part")
        p.Name=name; p.Size=size; p.Color=color; p.Material=material; p.CFrame=pose
        p.Transparency=alpha or 0; p.Anchored=true
        p.CanCollide=false; p.CanTouch=false; p.CanQuery=false; p.CastShadow=false
        p.Parent=parent
        return p
    end
    local function ease(t) t=math.clamp(t,0,1); return t*t*(3-2*t) end
    local function archive()
        local at=archiveAt
        local basis=CFrame.fromMatrix(at,-Vector3.zAxis,Vector3.yAxis,Vector3.xAxis)
        local holder=part(scene,"WallInk",Vector3.new(8.1,2.08,.01),Color3.new(),Enum.Material.SmoothPlastic,basis,1)
        local canvas=Instance.new("SurfaceGui")
        canvas.Name="WallPaint"; canvas.Face=Enum.NormalId.Front
        canvas.CanvasSize=Vector2.new(1120,288); canvas.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
        canvas.LightInfluence=.85; canvas.MaxDistance=25; canvas.Parent=holder
        local random=Random.new(3119)
        local advances={[" "]=40,["Г"]=59,["Д"]=75,["Ж"]=87,["З"]=64,["Л"]=70,
            ["О"]=76,["Т"]=65,["Ш"]=86,["Ы"]=84,["Ь"]=66}
        local function lettering(text,name,color,y)
            local row=Instance.new("Frame")
            row.Name=name; row.Size=UDim2.fromScale(1,1)
            row.BackgroundTransparency=1; row.Parent=canvas
            local chars={}
            local width=0
            for _,cp in utf8.codes(text) do
                local ch=utf8.char(cp)
                table.insert(chars,ch)
                width+=advances[ch] or 70
            end
            local glyphs={}
            local cursor=(canvas.CanvasSize.X-width)*.5
            for i,ch in ipairs(chars) do
                local advance=advances[ch] or 70
                local label=Instance.new("TextLabel")
                label.Size=UDim2.fromOffset(96,132)
                label.Position=UDim2.fromOffset(cursor+advance*.5-48+random:NextNumber(-2,2),y+random:NextNumber(-5,5))
                cursor+=advance
                label.BackgroundTransparency=1; label.Font=Enum.Font.GothamBold
                label.Text=ch; label.TextSize=85+random:NextInteger(-4,4)
                label.TextColor3=color:Lerp(Color3.fromRGB(114,45,37),random:NextNumber(0,.26))
                label.TextTransparency=1; label.Rotation=random:NextNumber(-5,5)
                label.Parent=row
                local trail
                if ch~=" " and i%3==1 then
                    trail=Instance.new("Frame")
                    trail.BorderSizePixel=0
                    trail.BackgroundColor3=label.TextColor3
                    trail.BackgroundTransparency=1
                    trail.Size=UDim2.fromOffset(2,random:NextInteger(3,9))
                    trail.Position=label.Position+UDim2.fromOffset(random:NextInteger(18,48),96)
                    trail.Rotation=label.Rotation
                    trail.Parent=row
                end
                glyphs[i]={label,trail}
            end
            return glyphs
        end
        local first=lettering("НЕ ОГЛЯДЫВАЙСЯ","First",Color3.fromRGB(107,63,53),63)
        local second=lettering("ТЕПЕРЬ ПОЗДНО","Second",Color3.fromRGB(117,34,28),72)
        local scratchMarks={}
        for i=1,13 do
            local mark=Instance.new("Frame")
            mark.BackgroundColor3=Color3.fromRGB(92,54,46)
            mark.BackgroundTransparency=1; mark.BorderSizePixel=0
            mark.Size=UDim2.fromOffset(random:NextInteger(1,3),random:NextInteger(2,12))
            mark.Rotation=random:NextNumber(-22,16)
            mark.Position=UDim2.fromOffset(random:NextInteger(106,970),random:NextInteger(160,184))
            mark.Parent=canvas; scratchMarks[i]=mark
        end
        local sound=Instance.new("Sound")
        sound.Name="BackWallTick"; sound.SoundId="rbxassetid://9117233449"
        sound.PlaybackSpeed=.66; sound.Volume=.24; sound.RollOffMinDistance=3; sound.RollOffMaxDistance=14
        local behind=part(scene,"ShelfSoundOrigin",Vector3.one*.04,Color3.new(),Enum.Material.SmoothPlastic,CFrame.new(1026,4.7,-14),1)
        sound.Parent=behind
        local seen,away,shift=0,0,archiveChanged==true
        local exposure=archiveRead and 1.4 or 0
        local lastExposure,lastShift,lastRead
        local visibilityPoints={at,at+Vector3.zAxis*2.1,at-Vector3.zAxis*2.1}
        local function updateInk(glyphs,amount,delay,ramp)
            for i,glyph in ipairs(glyphs) do
                local strength=ease((amount-i*delay)/ramp)
                glyph[1].TextTransparency=1-strength
                if glyph[2] then glyph[2].BackgroundTransparency=1-.36*strength end
            end
        end
        local params=RaycastParams.new()
        params.FilterType=Enum.RaycastFilterType.Exclude
        return function(dt)
            local camera=workspace.CurrentCamera
            local char=player.Character
            local head=char and char:FindFirstChild("Head")
            if not camera or not head then return end
            local view=camera.CFrame
            local delta=at-view.Position
            local inArchive=head.Position.X>1000.35 and head.Position.X<1031.7
                and head.Position.Z<-.35 and head.Position.Z>-31.7
            local facing=delta.Magnitude>0 and view.LookVector:Dot(delta.Unit) or -1
            local levelLook=Vector3.new(view.LookVector.X,0,view.LookVector.Z)
            local flatDelta=Vector3.new(delta.X,0,delta.Z)
            local turned=levelLook.Magnitude>.55 and flatDelta.Magnitude>.2
                and levelLook.Unit:Dot(flatDelta.Unit)<-.26
            local near=inArchive and (at-head.Position).Magnitude<14
            local watching=false
            if near and facing>.80 then
                params.FilterDescendantsInstances={char,scene}
                local visible=0
                for _,point in ipairs(visibilityPoints) do
                    local _,onScreen=camera:WorldToViewportPoint(point)
                    if onScreen and not workspace:Raycast(view.Position,point-view.Position,params) then
                        visible+=1
                    end
                end
                watching=visible>=2
            end
            if shift then
                exposure=math.min(1.4,exposure+dt)
            elseif watching then
                seen+=dt
                if seen>1.03 then archiveRead=true end
                away=0
                exposure=math.min(1.4,exposure+dt)
            elseif archiveRead and near and turned and not shift then
                away+=dt
                if away>.42 and not shift then
                    shift=true; archiveChanged=true; exposure=0; sound:Play()
                end
            else
                away=0
                if not archiveRead then
                    seen=0
                    exposure=math.max(0,exposure-dt*.75)
                end
            end
            if lastExposure==exposure and lastShift==shift and lastRead==archiveRead then return end
            lastExposure,lastShift,lastRead=exposure,shift,archiveRead
            updateInk(first,shift and .91*(1-ease(exposure/.24)) or exposure,.025,.46)
            updateInk(second,shift and math.max(0,exposure-.14) or 0,.024,.32)
            for i,mark in ipairs(scratchMarks) do
                mark.BackgroundTransparency=1-(shift and .48 or .23)*ease((exposure-i*.018)/.64)
            end
            holder:SetAttribute("Stage",shift and "Changed" or archiveRead and "Read" or "Hidden")
        end
    end
    local function vent()
        local origin=ventAt
        local source=part(scene,"VentVaporOrigin",Vector3.new(.08,1.06,1.53)*ventScale,Color3.new(),
            Enum.Material.SmoothPlastic,CFrame.lookAt(origin,origin+Vector3.xAxis),1)
        local random=Random.new(3157)
        local function emitter(name,offset,rate,color,size,speed,accel)
            local a=Instance.new("Attachment")
            a.CFrame=CFrame.new(offset*ventScale)
            a.Parent=source
            local p=Instance.new("ParticleEmitter")
            p.Name=name; p.Texture="rbxasset://textures/particles/smoke_main.dds"
            p.EmissionDirection=Enum.NormalId.Front; p.Color=color
            p.Rate=rate; p.Lifetime=NumberRange.new(.74,1.25); p.Speed=speed
            p.Size=NumberSequence.new({NumberSequenceKeypoint.new(0,size*.32),NumberSequenceKeypoint.new(.44,size*.65),NumberSequenceKeypoint.new(1,size)})
            p.Transparency=NumberSequence.new({NumberSequenceKeypoint.new(0,1),NumberSequenceKeypoint.new(.16,.50),NumberSequenceKeypoint.new(.61,.77),NumberSequenceKeypoint.new(1,1)})
            p.Acceleration=accel; p.Drag=.75
            p.SpreadAngle=Vector2.new(19,16); p.Rotation=NumberRange.new(-180,180); p.RotSpeed=NumberRange.new(-31,27)
            p.LightInfluence=.75; p.Parent=a
            return p
        end
        local core=emitter("GreenJet",Vector3.new(.26,.08,0),20,
            ColorSequence.new(Color3.fromRGB(99,161,57),Color3.fromRGB(153,177,87)),.69,NumberRange.new(.79,1.45),Vector3.new(.09,.12,0))
        local haze=emitter("DiluteHaze",Vector3.new(-.16,-.12,.07),12,
            ColorSequence.new(Color3.fromRGB(127,164,73),Color3.fromRGB(172,183,124)),1.06,NumberRange.new(.47,.93),Vector3.new(0,.17,-.10))
        local runnels={}
        local dripTips={}
        local color=ColorSequence.new(Color3.fromRGB(87,131,40),Color3.fromRGB(96,146,48))
        local streams={
            {"SeepOnWall",.348,8,.057,.032,0,.013},
            {"SideRunnel1",-.50,6,.052,.025,.26,-.015},
            {"SideRunnel2",.56,5,.043,.020,.58,.019},
        }
        for _,stream in ipairs(streams) do
            local name,offset,count,step,width,delay,bend=table.unpack(stream)
            local runoff=ventMount+Vector3.new(.035,-1.05*ventScale,offset)
            local last
            for i=0,count do
                local y=runoff.Y-i*step
                local z=runoff.Z+math.sin(i*.73)*bend+i*.0024
                local point=Instance.new("Attachment")
                point.Parent=source
                point.WorldPosition=Vector3.new(runoff.X,y,z)
                if last then
                    local beam=Instance.new("Beam")
                    beam.Name=i==1 and name or "Runnel"
                    beam.Attachment0=last; beam.Attachment1=point
                    beam.FaceCamera=true; beam.Segments=2
                    beam.Width0=width*(1-.77*(i-1)/count); beam.Width1=width*(1-.77*i/count)
                    beam.Color=color
                    beam.Transparency=NumberSequence.new(1)
                    beam.LightEmission=.08; beam.LightInfluence=.82
                    beam.Parent=source
                    local stain=part(scene,"AbsorbedWetness",
                        Vector3.new(.006,step*2.6,width*(1.45+random:NextNumber(0,.51))),Color3.fromRGB(81,108,49),
                        Enum.Material.SmoothPlastic,CFrame.new(runoff.X-.013,y+.027,z-.005)*CFrame.Angles(math.sin(i)*.10,0,0),1)
                    stain.Shape=Enum.PartType.Cylinder
                    runnels[#runnels+1]={beam,stain,i,delay}
                end
                last=point
            end
            dripTips[#dripTips+1]=last.WorldPosition+Vector3.new(.009,-.006,0)
        end
        local function travel(tip,age)
            return tip+Vector3.new(.16*age+.058*age*age,-.022-6.7*age*age,.032*age)
        end
        local function floorWetness(name,landing,scale)
            local floor=part(scene,name,Vector3.new(.64,.006,.52)*scale,Color3.new(),
                Enum.Material.SmoothPlastic,CFrame.new(landing.X,.112,landing.Z),1)
            local wet=Instance.new("SurfaceGui")
            wet.Name="MergedWetness"; wet.Face=Enum.NormalId.Top
            wet.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize; wet.CanvasSize=Vector2.new(144,128)
            wet.LightInfluence=.82; wet.MaxDistance=21; wet.Parent=floor
            local footprint=Instance.new("CanvasGroup")
            footprint.BackgroundTransparency=1; footprint.GroupTransparency=1
            footprint.AnchorPoint=Vector2.new(.5,.5); footprint.Position=UDim2.fromScale(.5,.5)
            footprint.Parent=wet
            local function lobe(x,y,w,h,roll,color,alpha)
                local f=Instance.new("Frame")
                f.Position=UDim2.fromScale(x,y); f.Size=UDim2.fromScale(w,h)
                f.BackgroundColor3=color; f.BackgroundTransparency=alpha
                f.BorderSizePixel=0; f.Rotation=roll; f.Parent=footprint
                local corner=Instance.new("UICorner")
                corner.CornerRadius=UDim.new(.48,0); corner.Parent=f
            end
            local shade=Color3.fromRGB(107,119,72)
            if scale==1 then
                lobe(.17,.28,.66,.45,-12,shade,0)
                lobe(.21,.38,.49,.39,22,shade,0)
                lobe(.48,.20,.34,.37,-31,shade,0)
                lobe(.52,.37,.19,.06,-21,Color3.fromRGB(137,146,101),.58)
            else
                lobe(.12,.43,.71,.25,-20,shade,0)
                lobe(.37,.28,.42,.34,-30,shade,0)
                lobe(.27,.56,.24,.20,10,shade,0)
            end
            return footprint
        end
        local drops={}
        for i,schedule in ipairs({{2.34,2.34,.036,1},{3.85,4.21,.029,.70}}) do
            local first,period,width,scale=table.unpack(schedule)
            local tip=dripTips[i]
            local fall=math.sqrt((tip.Y-.022-.15)/6.7)
            local landing=travel(tip,fall)
            local drop=part(scene,"FallingDrop"..i,Vector3.one*width,Color3.fromRGB(119,164,56),
                Enum.Material.Glass,CFrame.new(tip),1)
            local bead=part(scene,i==1 and "CondensationBead" or "SideCondensationBead",Vector3.one*width,
                Color3.fromRGB(113,155,55),Enum.Material.Glass,CFrame.new(tip),1)
            bead.Shape=Enum.PartType.Ball
            drop.Shape=Enum.PartType.Ball
            local hit=part(scene,"DropImpact"..i,Vector3.new(.006,.05,.05),Color3.fromRGB(126,153,80),
                Enum.Material.SmoothPlastic,CFrame.new(landing.X,.117,landing.Z)*CFrame.Angles(0,0,math.pi/2),1)
            hit.Shape=Enum.PartType.Cylinder
            local wet=floorWetness(i==1 and "WetFootprint" or "SideWetFootprint",landing,scale)
            drops[i]={tip=tip,first=first,period=period,width=width,fall=fall,drop=drop,bead=bead,hit=hit,wet=wet,scale=scale}
        end
        local start=state:GetAttribute("OfficeDetailStartedAt") or workspace:GetServerTimeNow()
        return function()
            local t=workspace:GetServerTimeNow()-start
            local flow=ease((t-.36)/.88)
            local cycle=t%7.3
            local pressure=ease((cycle-1.1)/.52)*(1-ease((cycle-2.05)/1.50))
            core.Rate=flow*(5+12*pressure)
            haze.Rate=flow*(3+5*pressure)
            for _,segment in ipairs(runnels) do
                local runnel,stain,i,delay=table.unpack(segment)
                local advance=ease((t-.3-delay-i*.09)/.61)
                runnel.Transparency=NumberSequence.new(1-advance*(.56+.21*pressure+.08*math.sin(t*4.2-i*.43)^2))
                stain.Transparency=1-(.22-i*.011)*ease((t-.88-delay-i*.11)/2.4)
            end
            for _,stream in ipairs(drops) do
                local sinceFirst=t-stream.first
                local age=sinceFirst%stream.period
                local width=stream.width
                local charge=t>=stream.first-.44 and ease((age-stream.period+.44)/.44) or 0
                local bead=stream.bead
                bead.Transparency=charge>0 and .19 or 1
                if charge>0 then
                    bead.Size=Vector3.new(width,width*(.55+.70*charge),width)*charge
                    bead.Position=stream.tip-Vector3.yAxis*bead.Size.Y*.5
                end
                local drop=stream.drop
                local falling=sinceFirst>=0 and age<stream.fall
                drop.Transparency=falling and .15 or 1
                if falling then
                    drop.Size=Vector3.new(width,width*(1.05+1.35*age/stream.fall),width)
                    drop.CFrame=CFrame.new(travel(stream.tip,age))*CFrame.Angles(0,0,.06)
                end
                local impactAge=age-stream.fall
                local splashing=sinceFirst>=0 and impactAge>=0 and impactAge<.26
                local splash=stream.hit
                splash.Transparency=splashing and .34+.66*impactAge/.26 or 1
                if splashing then
                    local spread=(.045+.15*impactAge/.26)*stream.scale
                    splash.Size=Vector3.new(.006,spread*.79,spread)
                end
                local wetAge=sinceFirst-stream.fall
                if wetAge<5.2 or not stream.settled then
                    local growth=ease((wetAge+.02)/5.2)
                    stream.wet.Size=UDim2.fromScale(.34+.66*growth,.40+.60*growth)
                    stream.wet.GroupTransparency=wetAge>=0 and 1-stream.scale*(.16+.30*growth) or 1
                    stream.settled=wetAge>=5.2
                end
            end
        end
    end
    local function whisperDoor()
        local source=part(scene,"BehindDoorAudio",Vector3.one*.04,Color3.new(),Enum.Material.SmoothPlastic,
            CFrame.new(doorAt-Vector3.xAxis*.13),1)
        local function sound(name,asset,speed)
            local item=Instance.new("Sound")
            item.Name=name; item.SoundId="rbxasset://sounds/"..asset
            item.PlaybackSpeed=speed; item.Volume=0
            item.RollOffMode=Enum.RollOffMode.Linear
            item.RollOffMinDistance=.68; item.RollOffMaxDistance=2.62
            local muffler=Instance.new("EqualizerSoundEffect")
            muffler.LowGain=2; muffler.MidGain=-7; muffler.HighGain=-22
            muffler.Parent=item; item.Parent=source
            return item
        end
        local breath=sound("MuffledBreath","action_falling.ogg",.72)
        local knock=sound("DullKnock","action_jump_land.mp3",.67)
        local elapsed,current=0,1
        local playing,volume,stopAt
        local cues={{.38,breath,.19,.72},{1.46,knock,.12,.22},{1.79,knock,.075,.21},{3.8,breath,.14,.54}}
        local lever,leverRest,strike
        local kick=0
        local function settleLever()
            if strike and lever and lever.Parent then lever:PivotTo(leverRest) end
            strike=nil
        end
        scene.Destroying:Connect(settleLever)
        local query=RaycastParams.new()
        query.FilterType=Enum.RaycastFilterType.Exclude
        return function(dt)
            local character=player.Character
            local head=character and character:FindFirstChild("Head")
            local delta=head and (head.Position-doorAt)
            local planar=delta and Vector2.new(delta.X-.08,math.max(0,math.abs(delta.Z)-1.28)).Magnitude or math.huge
            local close=delta and delta.X>.13 and math.abs(delta.Z)<1.95 and planar<2.18 and math.abs(delta.Y)<1.30
            if close then
                query.FilterDescendantsInstances={character,scene}
                local front=doorAt+Vector3.new(.25,math.clamp(delta.Y,-.6,.6),math.clamp(delta.Z,-1.72,1.72))
                close=workspace:Raycast(head.Position,front-head.Position,query)==nil
            end
            if not close then
                if playing then playing:Stop(); playing=nil end
                settleLever()
                elapsed,current=0,1
                return
            end
            elapsed+=dt
            if playing and elapsed>=stopAt then playing:Stop(); playing=nil end
            local level=ease((2.18-planar)/1.12)
            local cue=cues[current]
            if elapsed>=cue[1] then
                playing,volume=cue[2],cue[3]
                playing.TimePosition=0
                playing.Volume=volume*level
                playing:Play()
                if playing==knock then
                    local door=office:FindFirstChild("UnlistedServiceDoor")
                    local currentLever=door and door:FindFirstChild("DoorLever")
                    if currentLever~=lever then
                        lever=currentLever
                        leverRest=lever and lever:GetAttribute("RestPose")
                        if leverRest then lever.WorldPivot=leverRest end
                    end
                    if lever and leverRest then
                        strike=workspace:GetServerTimeNow()
                        kick=current==2 and .145 or .082
                    end
                end
                stopAt=elapsed+cue[4]
                current=current%#cues+1
                if current==1 then
                    elapsed-=5.6
                    stopAt-=5.6
                end
            end
            if playing then playing.Volume=volume*level end
            if strike then
                local age=workspace:GetServerTimeNow()-strike
                if age<.32 and lever.Parent then
                    local rebound=math.sin(age*38)*(1-age/.32)^2
                    lever:PivotTo(leverRest*CFrame.Angles(0,0,-kick*rebound))
                else
                    settleLever()
                end
            end
        end
    end
    local builders={ArchiveWriting=archive,GreenVent=vent,WhisperDoor=whisperDoor}
    local anchors={ArchiveWriting=archiveAt,GreenVent=ventAt,WhisperDoor=doorAt}
    local elapsed=0
    RunService.RenderStepped:Connect(function(dt)
        elapsed+=dt
        if elapsed<1/24 then return end
        local step=elapsed; elapsed=0
        local scenario=state:GetAttribute("OfficeDetailScenario")
        local round=state:GetAttribute("OfficeDetailRound")
        if round~=archiveRound then
            archiveRound,archiveRead,archiveChanged=round,nil,nil
        end
        local character=player.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        local anchor=anchors[scenario]
        local selected=phase.Value=="Active" and player:GetAttribute("KonturZone")=="Office"
            and root and anchor and (root.Position-anchor).Magnitude<(scene and 42 or 36) and scenario or nil
        if selected~=current or (selected and round~=roundId) then
            if scene then scene:Destroy() end
            scene,update=nil,nil
            current,roundId=selected,round
            if selected then
                scene=Instance.new("Folder")
                scene.Name="OfficeDetailPresentation"; scene.Parent=office
                update=builders[selected]()
            end
        end
        if update then update(step) end
    end)
end)
