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
    local ventAt=Vector3.new(1000.57,4.82,45.8)
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
        local seen,away,shift,exposure=0,0,archiveChanged==true,0
        local lastExposure,lastShift,lastRead
        local visibilityPoints={at,at+Vector3.zAxis*2.1,at-Vector3.zAxis*2.1}
        local function updateInk(glyphs,active,delay,ramp)
            for i,glyph in ipairs(glyphs) do
                local strength=active and ease((exposure-i*delay)/ramp) or 0
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
                    if not workspace:Raycast(view.Position,point-view.Position,params) then
                        visible+=1
                    end
                end
                watching=visible>=2
            end
            if watching then
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
            updateInk(first,not shift,.025,.46)
            updateInk(second,shift,.032,.38)
            for i,mark in ipairs(scratchMarks) do
                mark.BackgroundTransparency=1-(shift and .48 or .23)*ease((exposure-i*.018)/.64)
            end
            holder:SetAttribute("Stage",shift and "Changed" or archiveRead and "Read" or "Hidden")
        end
    end
    local function vent()
        local origin=ventAt
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
        local floor=part(scene,"WetFootprint",Vector3.new(.92,.006,.76),Color3.new(),
            Enum.Material.SmoothPlastic,CFrame.new(1000.56,.112,46.43),1)
        local wet=Instance.new("SurfaceGui")
        wet.Name="MergedWetness"; wet.Face=Enum.NormalId.Top
        wet.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize; wet.CanvasSize=Vector2.new(144,128)
        wet.LightInfluence=.82; wet.MaxDistance=21; wet.Parent=floor
        local footprint=Instance.new("CanvasGroup")
        footprint.BackgroundTransparency=1; footprint.GroupTransparency=1
        footprint.AnchorPoint=Vector2.new(.5,.5); footprint.Position=UDim2.fromScale(.5,.5)
        footprint.Size=UDim2.fromScale(.5,.5); footprint.Parent=wet
        local function lobe(x,y,w,h,roll,color,alpha)
            local f=Instance.new("Frame")
            f.Position=UDim2.fromScale(x,y); f.Size=UDim2.fromScale(w,h)
            f.BackgroundColor3=color; f.BackgroundTransparency=alpha
            f.BorderSizePixel=0; f.Rotation=roll; f.Parent=footprint
            local corner=Instance.new("UICorner")
            corner.CornerRadius=UDim.new(.48,0); corner.Parent=f
        end
        local shade=Color3.fromRGB(107,119,72)
        lobe(.17,.28,.66,.45,-12,shade,0)
        lobe(.21,.38,.49,.39,22,shade,0)
        lobe(.48,.20,.34,.37,-31,shade,0)
        lobe(.52,.37,.19,.06,-21,Color3.fromRGB(137,146,101),.58)
        local droplets={}
        local floorSpecks={}
        for i=1,3 do
            local p=part(scene,"DropImpact",Vector3.new(.006,.05,.05),Color3.fromRGB(126,153,80),
                Enum.Material.SmoothPlastic,CFrame.new(),1)
            p.Shape=Enum.PartType.Cylinder
            floorSpecks[i]=p
        end
        local puddlesSettled=false
        for i=1,7 do
            local p=part(scene,"FallingDrop",Vector3.new(.038,.075,.041),Color3.fromRGB(119,164,56),Enum.Material.Glass,CFrame.new(),1)
            p.Shape=Enum.PartType.Ball
            local width=random:NextNumber(.025,.045)
            droplets[i]={p,random:NextNumber(.87,1.34),random:NextNumber(),random:NextNumber(-.055,.058),width}
        end
        local start=state:GetAttribute("OfficeDetailStartedAt") or workspace:GetServerTimeNow()
        return function()
            local t=workspace:GetServerTimeNow()-start
            local flow=ease((t-.36)/.88)
            local cycle=t%7.3
            local pressure=ease((cycle-1.1)/.52)*(1-ease((cycle-2.05)/1.50))
            core.Rate=flow*(9+18*pressure)
            haze.Rate=flow*(5+6*pressure)
            for i,runnel in ipairs(runnels) do
                local advance=ease((t-.3-i*.09)/.61)
                runnel.Transparency=NumberSequence.new(1-advance*(.56+.21*pressure+.08*math.sin(t*4.2-i*.43)^2))
                stains[i].Transparency=1-(.22-i*.011)*ease((t-.88-i*.11)/2.4)
            end
            if not puddlesSettled then
                local growth=ease((t-1.4)/4.6)
                footprint.Size=UDim2.fromScale(.38+.62*growth,.44+.56*growth)
                footprint.GroupTransparency=1-.46*growth
                puddlesSettled=t>=6
            end
            local fallTime=math.sqrt((3.02-.15)/6.7)
            for i,item in ipairs(droplets) do
                local p,period,offset,spread,width=table.unpack(item)
                local a=(t+offset)%period
                local y=3.02-6.7*a*a
                if t<.8 or y<.15 then
                    p.Transparency=1
                else
                    p.Transparency=.15
                    p.Size=Vector3.new(width,width*(1.05+1.35*a/fallTime),width)
                    p.CFrame=CFrame.new(1000.35+.23*a,y,46.39+spread+a*.045)*CFrame.Angles(0,0,.06)
                end
                local splash=floorSpecks[i]
                if splash then
                    local hit=a-fallTime
                    local progress=math.clamp(hit/.24,0,1)
                    splash.Transparency=t>=1.4 and hit>=0 and hit<.24 and .34+.66*progress or 1
                    local width=.06+.21*progress
                    splash.Size=Vector3.new(.006,width*.79,width)
                    splash.CFrame=CFrame.new(1000.35+.23*fallTime,.117+i*.001,
                        46.39+spread+fallTime*.045)*CFrame.Angles(0,0,math.pi/2)
                end
            end
        end
    end
    local builders={ArchiveWriting=archive,GreenVent=vent}
    local anchors={ArchiveWriting=archiveAt,GreenVent=ventAt}
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
