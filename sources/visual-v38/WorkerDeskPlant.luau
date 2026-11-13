            -- KONTUR v38: small potted lily on the ceiling desk, built from plain parts (editable meshes are unavailable once the worker scene is up).
            -- Its pot sits on the desk top, so the plant grows down toward the room.
            local desk=ws:FindFirstChild("Ceiling desk")
            if desk and desk:IsA("BasePart") and not ws:FindFirstChild("DeskLily") then
                local plant=Instance.new("Model") plant.Name="DeskLily"
                local base=desk.CFrame*CFrame.new(-.55,desk.Size.Y/2,-.78)
                local function bit(shape,size,frame,color,material)
                    local p=Instance.new("Part") p.Shape=shape p.Size=size p.CFrame=frame p.Color=color
                    p.Material=material or Enum.Material.SmoothPlastic
                    p.Anchored=true p.CanCollide=false p.CanTouch=false p.CanQuery=false p.CastShadow=false
                    p.Parent=plant return p
                end
                -- Ellipsoid = Block + Sphere mesh (a Ball part with uneven Size is not guaranteed to stay an ellipsoid).
                local function oval(size,frame,color)
                    local p=bit(Enum.PartType.Block,size,frame,color)
                    local mesh=Instance.new("SpecialMesh") mesh.MeshType=Enum.MeshType.Sphere mesh.Parent=p
                    return p
                end
                local cyl=Enum.PartType.Cylinder
                bit(cyl,Vector3.new(.17,.26,.26),base*CFrame.new(0,.085,0)*CFrame.Angles(0,0,math.pi/2),Color3.fromRGB(236,238,240))
                bit(cyl,Vector3.new(.02,.23,.23),base*CFrame.new(0,.172,0)*CFrame.Angles(0,0,math.pi/2),Color3.fromRGB(48,38,32),Enum.Material.Slate)
                local greens={Color3.fromRGB(58,122,72),Color3.fromRGB(40,100,64),Color3.fromRGB(84,142,82)}
                for i=1,8 do
                    local len=.30+.06*(i%3)
                    local pivot=base*CFrame.new(0,.17,0)*CFrame.Angles(0,i*2.4,0)*CFrame.Angles(.62+.16*(i%4),0,0)
                    oval(Vector3.new(.17,len,.06),pivot*CFrame.new(0,len/2,0),greens[i%3+1])
                end
                local stem=base*CFrame.new(.03,.17,0)*CFrame.Angles(.12,0,0)
                bit(cyl,Vector3.new(.5,.02,.02),stem*CFrame.new(0,.25,0)*CFrame.Angles(0,0,math.pi/2),Color3.fromRGB(70,128,76))
                oval(Vector3.new(.11,.22,.06),stem*CFrame.new(0,.56,0)*CFrame.Angles(.12,0,0),Color3.fromRGB(244,242,232))
                plant.Parent=ws
            end
