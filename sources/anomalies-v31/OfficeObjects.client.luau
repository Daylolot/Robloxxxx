task.spawn(function()
    local Players=game:GetService("Players")
    local RunService=game:GetService("RunService")
    local player=Players.LocalPlayer
    local office=workspace:WaitForChild("OfficeMap")
    local state=office:WaitForChild("AnomalyReportState")
    local phase=state:WaitForChild("Phase")
    local scene,current,roundId
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
        local at=Vector3.new(1031.785,5.36,-17.1)
        local basis=CFrame.fromMatrix(at,-Vector3.zAxis,Vector3.yAxis,Vector3.xAxis)
        local holder=part(scene,"WallInk",Vector3.new(8.1,2.08,.01),Color3.new(),Enum.Material.SmoothPlastic,basis,1)
        local canvas=Instance.new("SurfaceGui")
        canvas.Name="WallPaint"; canvas.Face=Enum.NormalId.Front
        canvas.CanvasSize=Vector2.new(1120,288); canvas.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
        canvas.LightInfluence=.85; canvas.MaxDistance=25; canvas.Parent=holder
        local random=Random.new(3119)
        local function lettering(text,name,color,y,offset)
            local row=Instance.new("Frame")
            row.Name=name; row.Size=UDim2.fromScale(1,1)
            row.BackgroundTransparency=1; row.Parent=canvas
            local chars={}
            for _,cp in utf8.codes(text) do table.insert(chars,utf8.char(cp)) end
            local glyphs={}
            for i,ch in ipairs(chars) do
                local label=Instance.new("TextLabel")
                label.Size=UDim2.fromOffset(79,132)
                label.Position=UDim2.fromOffset(offset+(i-1)*65+random:NextNumber(-4,4),y+random:NextNumber(-8,8))
                label.BackgroundTransparency=1; label.Font=Enum.Font.GothamBold
                label.Text=ch; label.TextSize=86+random:NextInteger(-8,8)
                label.TextColor3=color:Lerp(Color3.fromRGB(114,45,37),random:NextNumber(0,.26))
                label.TextTransparency=1; label.Rotation=random:NextNumber(-5,5)
                label.Parent=row
                glyphs[i]=label
            end
            return glyphs
        end
        local first=lettering("НЕ ОГЛЯДЫВАЙСЯ","First",Color3.fromRGB(107,63,53),63,76)
        local second=lettering("ТЕПЕРЬ ПОЗДНО","Second",Color3.fromRGB(117,34,28),76,99)
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
        local seen,away,shift,exposure=0,0,false,0
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
            local near=inArchive and (at-head.Position).Magnitude<14
            local watching=false
            if near and facing>.83 then
                params.FilterDescendantsInstances={char,scene}
                watching=not workspace:Raycast(view.Position,delta,params)
            end
            if watching then
                seen+=dt
                away=0
                exposure=math.min(1.4,exposure+dt)
            elseif seen>1.03 and near and facing<.15 then
                away+=dt
                if away>.42 and not shift then
                    shift=true; exposure=0; sound:Play()
                end
            else
                away=0
                if seen<=1.03 then
                    seen=0
                    exposure=math.max(0,exposure-dt*.75)
                end
            end
            for i,letter in ipairs(first) do
                letter.TextTransparency=shift and 1 or 1-ease((exposure-i*.025)/.46)
            end
            for i,letter in ipairs(second) do
                letter.TextTransparency=shift and 1-ease((exposure-i*.032)/.38) or 1
            end
            for i,mark in ipairs(scratchMarks) do
                mark.BackgroundTransparency=1-(shift and .62 or .31)*ease((exposure-i*.018)/.64)
            end
            holder:SetAttribute("Stage",shift and "Changed" or seen>1.03 and "Read" or "Hidden")
        end
    end
    local function vent()
        local origin=Vector3.new(1000.57,4.82,45.8)
        local source=part(scene,"VentVaporOrigin",Vector3.new(.08,1.06,1.53),Color3.new(),
            Enum.Material.SmoothPlastic,CFrame.lookAt(origin,origin+Vector3.xAxis),1)
        local random=Random.new(3157)
        local function emitter(name,offset,rate,color,size,speed,accel)
            local a=Instance.new("Attachment")
            a.CFrame=CFrame.new(offset)
            a.Parent=source
            local p=Instance.new("ParticleEmitter")
            p.Name=name; p.Texture="rbxasset://textures/particles/smoke_main.dds"
            p.EmissionDirection=Enum.NormalId.Front; p.Color=color
            p.Rate=rate; p.Lifetime=NumberRange.new(.95,1.8); p.Speed=speed
            p.Size=NumberSequence.new({NumberSequenceKeypoint.new(0,size*.32),NumberSequenceKeypoint.new(.44,size*.65),NumberSequenceKeypoint.new(1,size)})
            p.Transparency=NumberSequence.new({NumberSequenceKeypoint.new(0,1),NumberSequenceKeypoint.new(.16,.57),NumberSequenceKeypoint.new(.61,.77),NumberSequenceKeypoint.new(1,1)})
            p.Acceleration=accel; p.Drag=.75
            p.SpreadAngle=Vector2.new(19,16); p.Rotation=NumberRange.new(-180,180); p.RotSpeed=NumberRange.new(-31,27)
            p.LightInfluence=.75; p.Parent=a
            return p
        end
        local core=emitter("GreenJet",Vector3.new(.26,.08,0),20,
            ColorSequence.new(Color3.fromRGB(99,161,57),Color3.fromRGB(153,177,87)),1.23,NumberRange.new(1.65,2.7),Vector3.new(.15,.55,0))
        local haze=emitter("DiluteHaze",Vector3.new(-.16,-.12,.07),12,
            ColorSequence.new(Color3.fromRGB(127,164,73),Color3.fromRGB(172,183,124)),2.15,NumberRange.new(.9,1.7),Vector3.new(0,.83,-.16))
        local runnels, stains={},{}
        local last
        for i=0,8 do
            local y=3.77-i*.092
            local z=46.38+math.sin(i*.73)*.021+i*.004
            local point=Instance.new("Attachment")
            point.Parent=source
            point.WorldPosition=Vector3.new(1000.235,y,z)
            if last then
                local beam=Instance.new("Beam")
                beam.Name=i==1 and "SeepOnWall" or "Runnel"
                beam.Attachment0=last; beam.Attachment1=point
                beam.FaceCamera=true; beam.Segments=2
                beam.Width0=.049-(i-1)*.0046; beam.Width1=.049-i*.0046
                beam.Color=ColorSequence.new(Color3.fromRGB(87,131,40),Color3.fromRGB(96,146,48))
                beam.Transparency=NumberSequence.new(1)
                beam.LightEmission=.08; beam.LightInfluence=.82
                beam.Parent=source
                runnels[i]=beam
                local stain=part(scene,"AbsorbedWetness",
                    Vector3.new(.006,.26,.067+random:NextNumber(0,.037)),Color3.fromRGB(81,108,49),
                    Enum.Material.SmoothPlastic,CFrame.new(1000.222,y+.045,z-.009)*CFrame.Angles(math.sin(i)*.10,0,0),1)
                stain.Shape=Enum.PartType.Cylinder
                stains[i]=stain
            end
            last=point
        end
        local puddles={}
        for i=1,5 do
            local d=.14+i*.055
            local puddle=part(scene,"FloorWetness",Vector3.new(.008,d*(.6+random:NextNumber(0,.6)),d),Color3.fromRGB(69,102,40),
                Enum.Material.SmoothPlastic,CFrame.new(1000.44+random:NextNumber(0,.32),.114,46.39+random:NextNumber(-.24,.22))*CFrame.Angles(0,random:NextNumber(),math.pi/2),1)
            puddle.Shape=Enum.PartType.Cylinder; puddles[i]={puddle,puddle.Size}
        end
        local droplets={}
        for i=1,7 do
            local p=part(scene,"FallingDrop",Vector3.new(.038,.075,.041),Color3.fromRGB(119,164,56),Enum.Material.Glass,CFrame.new(),1)
            p.Shape=Enum.PartType.Ball
            droplets[i]={p,random:NextNumber(.76,1.31),random:NextNumber(),random:NextNumber(-.043,.057)}
        end
        local start=state:GetAttribute("OfficeDetailStartedAt") or workspace:GetServerTimeNow()
        return function()
            local t=workspace:GetServerTimeNow()-start
            local flow=ease((t-.36)/.88)
            core.Rate=flow*(18+6*math.sin(t*1.83)^2)
            haze.Rate=flow*(7+3*math.sin(t*1.16)^2)
            for i,runnel in ipairs(runnels) do
                local advance=ease((t-.3-i*.09)/.61)
                runnel.Transparency=NumberSequence.new(1-advance*(.65+.16*math.sin(t*4.2-i*.43)^2))
                stains[i].Transparency=1-(.22-i*.011)*ease((t-.88-i*.11)/2.4)
            end
            for i,item in ipairs(puddles) do
                local p,size=table.unpack(item)
                local growth=ease((t-1.4-i*.33)/4)
                p.Transparency=1-(.54-i*.037)*growth
                p.Size=Vector3.new(size.X,size.Y*(.35+.65*growth),size.Z*(.35+.65*growth))
            end
            for _,item in ipairs(droplets) do
                local p,period,offset,spread=table.unpack(item)
                local a=(t+offset)%period
                local y=3.02-6.7*a*a
                if t<.8 or y<.15 then p.Transparency=1 else p.Transparency=.19 end
                p.CFrame=CFrame.new(1000.35+.23*a,math.max(.14,y),46.39+spread+a*.045)
            end
        end
    end
    local builders={ArchiveWriting=archive,GreenVent=vent}
    local elapsed=0
    RunService.RenderStepped:Connect(function(dt)
        elapsed+=dt
        if elapsed<1/24 then return end
        local step=elapsed; elapsed=0
        local scenario=state:GetAttribute("OfficeDetailScenario")
        local round=state:GetAttribute("OfficeDetailRound")
        local selected=phase.Value=="Active" and player:GetAttribute("KonturZone")=="Office" and builders[scenario] and scenario or nil
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
