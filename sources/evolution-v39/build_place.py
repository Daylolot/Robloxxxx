"""Assemble v39 = v38 + phone-profile mirror (evolution-v39/OfficeMirrors.luau) + cheap prop anomalies (OfficePropAnomalies.luau)."""
import argparse
import json
import importlib.util
from pathlib import Path
import tempfile


def load_source(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def after(source, anchor, addition):
    assert source.count(anchor) == 1, anchor
    return source.replace(anchor, anchor + addition)


def replace(source, anchor, text):
    assert source.count(anchor) == 1, anchor
    return source.replace(anchor, text)


def original_in_place(data, patch, text):
    """True when a script source equal to `text` is stored in the binary place."""
    import struct
    import zstandard
    position = 32
    decoder = zstandard.ZstdDecompressor()
    while position < len(data):
        tag, compressed, size, _ = patch.HEADER.unpack_from(data, position)
        start = position + patch.HEADER.size
        end = start + (compressed or size)
        position = end
        if tag != b"PROP":
            continue
        body = decoder.decompress(data[start:end], max_output_size=size) if compressed else data[start:end]
        if struct.pack("<I", len(text)) + text in body:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--perf", action="store_true", help="performance profile: tiny-part trim, phone profile for mirror and printer. Default is the QUALITY build: nothing is cut for weak devices")
    parser.add_argument("--no-trim", action="store_true", help="(kept for old scripts) the trim is off unless --perf is given")
    parser.add_argument("--no-hero-assets", action="store_true", help="do not embed the uploaded Blender asset ids (part-built furniture only)")
    parser.add_argument("--keep-guard", action="store_true", help="QA build that keeps the inspection guard active (for guard tests)")
    args = parser.parse_args()
    assert args.base.resolve() != args.output.resolve()
    folder = Path(__file__).resolve().parent.parent / "anomalies-v35"; style_folder = Path(__file__).resolve().parent.parent / "visual-v36"
    here = Path(__file__).resolve().parent.parent / "visual-v38"  # v38 resources (blood, plant, style overrides)
    evo = Path(__file__).resolve().parent
    def style_file(name):
        """v38 overrides a v36 file when it has its own copy."""
        chosen = (here / name) if (here / name).exists() else (style_folder / name)
        print("style file:", name, "<-", chosen.parent.name)
        return chosen
    printer = folder.parent / "printer-v29"
    if not printer.exists():
        printer = folder.parent / "printer_v29"
    previous = printer.parent / ("printer-v30" if printer.name == "printer-v29" else "printer_v30")
    patcher = printer.parent / ("ceiling-worker-v24" if printer.name == "printer-v29" else "ceiling_worker_v24")
    patch = load_source(patcher / "build_place.py", "binary_patch")
    assembler = load_source(printer / "build_place.py", "printer_assembler")
    data = args.base.read_bytes()
    client_code = (folder / "PrinterPaper.client.luau").read_text()
    client_code = replace(client_code, "-- PRINTER_DIRECTION", (folder / "PrinterDirection.luau").read_text())
    # v38: every sheet gets its own tone and a slight warm or cool cast (no extra parts or lights).
    client_code = replace(client_code, "local tone = (index % 5) * 4\n",
        "local tone = (index * 7 % 5) * 3\n            local cast = (index * 13 % 7) - 3\n")
    client_code = replace(client_code, "part.Color = Color3.fromRGB(244 - tone, 241 - tone, 226 - tone)",
        "part.Color = Color3.fromRGB(245 - tone + cast, 241 - tone, 228 - tone - cast * 2)")
    # v39: printer flight data is prepared in the background, 20 Hz paper updates on phones.
    client_code = load_source(evo / "printer_patch.py", "printer_patch").apply(client_code, replace, phone_profile=args.perf)
    with tempfile.TemporaryDirectory() as temp:
        client_source = Path(temp) / "PrinterPaper.client.luau"
        client_source.write_text(client_code)
        scripts = assembler.make_sources(data, args.qa, patch, client_source,
            previous / "PrinterRound.luau", previous / "PrinterFlightData.luau")

    server_key = ("Script", "OfficeReportService")
    server = scripts[server_key]
    start = server.index("local blood=office.Rooms:")
    stop = server.index("local preview=RS:", start)
    server = server[:start] + server[stop:]
    server = replace(server, '    if blood then table.insert(pool,"ArchiveWriting")end\n',
        '    local KLOUD={BloodFlood=1,CeilingWorker=1,GreenVent=1,WhisperDoor=1,Printer=1,Mirror=1,ShadowFigure=1,HangingFigure=1,RedEyes=1,BreathingCabinet=1,SlowFootsteps=1,PhoneRingsAlone=1,CeilingKnocks=1,DrippingCeiling=1,RockingChair=1,WhisperMonitor=1,RoomBlackout=1,PanelFlicker=1,StatueWalks=1,BehindYou=1}\n'
        '    local KQUIET={HiddenPistol=1,BloodDrops=1,RedMug=1,KeyboardGone=1,CabinetAjar=1,FrameMissing=1,MuddyFootprints=1,StickyNote=1,FaucetRunning=1,AbandonedBriefcase=1,ItemRotated=1,ItemShifted=1,PlantColor=1,ShadowOnWall=1,MonitorWrongTime=1,MugSpilled=1,ChairGone=1,PlateWrongName=1,PapersOnFloor=1,ScreenOff=1,VanishWhenSeen=1,ClockTilted=1,PhotosBackwards=1,SignNumberChanged=1,BadgeNameChanged=1,CalendarWrongMonth=1,PlanningBoardNote=1}\n'
        '    for _,name in ipairs(officeObjects.names) do\n'
        '        local lv=modelState.level\n'
        '        local w=1\n'
        '        if KLOUD[name] then w=(lv>=9 and 1) or (lv>=4 and 2) or 3 elseif KQUIET[name] then w=(lv>=9 and 3) or (lv>=4 and 2) or 1 end\n'
        '        for _=1,w do table.insert(pool,name) end\n'
        '    end\n')
    # first round of a server session is always a clearly visible anomaly (the tutorial's first lesson); QA builds keep the random pick for tests
    if not args.qa:
        server = replace(server, 'local function chooseEnvironment()\n',
            'local konturFirstRound=true\n'
            'local konturFirstApplied=false\n'
            'local KEASY={ArchiveWriting=1,CeilingWorker=1,GreenVent=1,WhisperDoor=1,ShadowFigure=1,HangingFigure=1,RedEyes=1}\n'
            'local function chooseEnvironment()\n')
        server = after(server, '    local active=#pool>0 and random:NextNumber()<Logic.AnomalyChance(modelState.level)\n',
            '    if konturFirstRound then\n'
            '        local easy={}\n'
            '        for _,name in ipairs(pool) do if KEASY[name] and not table.find(easy,name) then table.insert(easy,name) end end\n'
            '        if #easy>0 then pool=easy active=true konturFirstApplied=true end\n'
            '        if game:GetService("RunService"):IsStudio() then game.ServerStorage:SetAttribute("KonturFirstPick",#easy.." easy, active="..tostring(active).." t="..os.clock()) end\n'
            '    end\n')
    server = after(server, 'local printer=createPrinter(office,state,phaseValue)\n',
        'local officeObjects=createOfficeObjects(office,state)\n')
    server = replace(server, '    showBlood(scenario=="ArchiveWriting")',
        '    officeObjects.activate(scenario,modelState.round)')
    server = replace(server, '        showBlood(false)\n', '')
    server = after(server, 'local function finishRound(player,message,record,deadHumanoid)\n',
        '    officeObjects.activate(nil,nil)\n')
    server = after(server, 'local officeObjects=createOfficeObjects(office,state)\n', '''
-- Disable the original archive panel before the first playable frame.
local legacyArchive=office.Rooms.NW:FindFirstChild("BloodMessage")
if legacyArchive then legacyArchive:Destroy() end
''')
    if args.qa:
        server = after(server, '    local active=#pool>0 and random:NextNumber()<Logic.AnomalyChance(modelState.level)\n',
            '    local forced=game:GetService("RunService"):IsStudio() and state:GetAttribute("OfficeQANext") or nil\n'
            '    if modelState.level>1 and table.find(pool,forced) then active=true end\n')
        server = replace(server, '        if script:GetAttribute("ForcePrinterInStudio") and printer then\n',
            '''        local requested=game:GetService("RunService"):IsStudio() and state:GetAttribute("OfficeQANext") or nil
        if requested and table.find(pool,requested) then
            scenario=requested
        elseif script:GetAttribute("ForcePrinterInStudio") and printer then
''')
    # KONTUR v37 core protection: inspection guard, pcall around the round change, watchdog.
    core = evo.parent / "core-v37"
    guard = (core / "InspectionGuard.luau").read_text()
    guard = guard.replace("__INSPECT_MIN_SECONDS__", "0" if args.qa and not args.keep_guard else "6")
    assert "__INSPECT" not in guard
    server = replace(server, 'local function context(player,button)\n', guard + 'local function context(player,button)\n')
    server = replace(server, 'local function finishRound(player,message,record,deadHumanoid)\n',
        (core / "RoundRecovery.luau").read_text() + 'local function finishRound(player,message,record,deadHumanoid)\n')
    if not args.qa:
        # if the easy pool was not ready at start (ceiling worker / flood availability), pick again once, a few seconds later
        server = replace(server, '\nchooseEnvironment()\nlevelValue.Value=1;',
            '\nchooseEnvironment()\ntask.delay(10,function() if konturFirstRound and not konturFirstApplied then chooseEnvironment() end end)\nlevelValue.Value=1;')
    if not args.qa:
        # the guarantee of an easy first round stays until the first answer is given (the round can be re-chosen before a player arrives)
        server = after(server, 'local function finishRound(player,message,record,deadHumanoid)\n', '    konturFirstRound=false\n')
    server = replace(server, '    officeObjects.activate(nil,nil)\n    -- Lock before any event, replication or deferred work can yield to another answer.\n    flood:Stop()\n    ceiling:SetActive(false)\n    state:SetAttribute("MirrorAnomalyRound",nil)\n    if printer then printer.activate(false) end\n',
        '    pendingRecord=record\n    -- Scene resets must not block the answer lock below: a failure here is logged, never fatal.\n'
        '    local resetOk,resetErr=pcall(function()\n        officeObjects.activate(nil,nil)\n        flood:Stop()\n        ceiling:SetActive(false)\n'
        '        state:SetAttribute("MirrorAnomalyRound",nil)\n        if printer then printer.activate(false) end\n    end)\n'
        '    if not resetOk then warn("KONTUR scene reset failed: "..tostring(resetErr)) end\n')
    server = replace(server, '        if not Logic.BeginNextRound(modelState,record)then return end\n        resetEvent:Fire()\n',
        '        if not Logic.BeginNextRound(modelState,record)then return end\n        pendingRecord=nil\n        roundEpoch+=1;local myEpoch=roundEpoch\n        local ok,err=pcall(function()\n        resetEvent:Fire()\n')
    server = replace(server, '        returnCrew()\n        chooseEnvironment()\n',
        '        returnCrew()\n        if myEpoch~=roundEpoch then return end -- recovery already opened a round while we waited\n        chooseEnvironment()\n')
    server = replace(server, '        phaseValue.Value="Active" -- Publish last, after geometry and arrivals are ready.\n    end)\n',
        '        phaseValue.Value="Active" -- Publish last, after geometry and arrivals are ready.\n        end)\n'
        '        if not ok then warn("KONTUR round change failed: "..tostring(err));forceOpenRound() end\n    end)\n')
    server = replace(server, '    local accepted,message,record=Logic.TrySubmit(modelState,context(player,button),request)\n',
        '    if modelState.accepting then\n'
        '        local hint=inspectionHint(player)\n'
        '        if hint then sendInspectionHint(player,hint,requestId);return end\n'
        '    end\n'
        '    local accepted,message,record=Logic.TrySubmit(modelState,context(player,button),request)\n')
    server = replace(server, 'Players.PlayerRemoving:Connect(function(p)modelState.lastByPlayer[p.UserId]=nil end)\n',
        'Players.PlayerRemoving:Connect(function(p)modelState.lastByPlayer[p.UserId]=nil;forgetInspection(p)end)\n'
        + (core / "RoundWatchdog.luau").read_text())
    # v43: the answer screens show a neutral status line (no verdict, no explanation of the round)
    server = load_source(evo / "debrief_patch.py", "debrief_patch").apply(server, replace)
    mounts = (folder / "OfficeMounts.luau").read_text()
    shared = (folder / "OfficeObjects.server.luau").read_text()
    # v42: the WestPlanterColor leaf list is read again after OfficeAnomalyUpgrade swaps the planter for a Blender mesh (leaf groups are named LeafBlade)
    leaves_old = """    local colors={}
    if plant then
        for _,part in ipairs(plant:GetDescendants()) do
            if part:IsA("BasePart") and (part.Name=="LeafBlade" or part.Name=="TerminalLeaf" or part.Name=="LeafMidrib_Wire") then
                local color=part.Color
                colors[part]={color,Color3.fromRGB(83+color.G*185,18+color.R*95,54+color.B*118)}
            end
        end
    end
"""
    leaves_new = """    local colors={}
    local function captureLeaves()
        table.clear(colors)
        if plant then
            for _,part in ipairs(plant:GetDescendants()) do
                if part:IsA("BasePart") and (part.Name=="LeafBlade" or part.Name=="TerminalLeaf" or part.Name=="LeafMidrib_Wire") then
                    local color=part.Color
                    colors[part]={color,Color3.fromRGB(83+color.G*185,18+color.R*95,54+color.B*118)}
                end
            end
        end
    end
    captureLeaves()
    local leavesRecaptured=false
"""
    shared = replace(shared, leaves_old, leaves_new)
    shared = replace(shared, """        for part,finish in pairs(colors) do
            part.Color=scenario=="WestPlanterColor" and finish[2] or finish[1]
        end
""", """        if plant and not leavesRecaptured and plant:GetAttribute("AnomalyUpgraded") then
            leavesRecaptured=true
            captureLeaves()
        end
        for part,finish in pairs(colors) do
            part.Color=scenario=="WestPlanterColor" and finish[2] or finish[1]
        end
""")
    shared = replace(shared, "-- VENT_SPEC", (folder / "VentParts.luau").read_text())
    shared = replace(shared, "-- DOOR_SPEC", (folder / "DoorParts.luau").read_text())
    # v39: cheap prop anomalies. The module file starts with --!strict and ends with a return; neither is valid mid-script.
    pack = (evo / "OfficePropAnomalies.luau").read_text()
    pack = replace(pack, "--!strict\n", "")
    pack = replace(pack, "\nreturn attachPropAnomalies\n", "\n")
    # v41 decor: extra furniture and wall decoration built from parts (see OfficeDecor.luau)
    decor = (evo / "OfficeDecor.luau").read_text()
    decor = replace(decor, "--!strict\n", "")
    decor = replace(decor, "\nreturn attachOfficeDecor\n", "\n")
    # Blender furniture: assets uploaded to Roblox (sources/evolution-v39/blender/uploaded_assets.json); the decor swaps the part-built
    # look for the meshes on the server in the background (InsertService:LoadAsset), the part-built look stays as fallback.
    import json
    assets_path = evo / "blender" / "uploaded_assets.json"
    decor_keys = ("Bookcase", "WaterCooler", "CoatRack", "FloorLamp", "Armchair", "FilingCabinet")
    registry = json.loads(assets_path.read_text()) if assets_path.exists() else {}
    ids = {k: registry[k]["assetId"] for k in decor_keys if registry.get(k, {}).get("assetId")}
    if ids and not args.no_hero_assets:
        decor = replace(decor, "\t-- @@HERO_ASSETS@@\n", "\tHERO_ASSETS = {" + ", ".join(f"{k} = {v}" for k, v in ids.items()) + "}\n")
        print("hero assets:", ", ".join(ids))
    else:
        print("hero assets: none (part-built items only)")
    # v42 hub: hazmat suits and the respirator station from Blender assets (OfficeHubUpgrade.luau), swapped in a background thread
    hub = (evo / "OfficeHubUpgrade.luau").read_text()
    hub = replace(hub, "--!strict\n", "")
    hub = replace(hub, "\nreturn attachHubUpgrade\n", "\n")
    hub_ids = {k: registry[k]["assetId"] for k in ("HazmatSuit", "MaskStation", "HubCase", "HubCaseMed", "SuitRack", "EquipmentBench", "FoldingChair") if registry.get(k, {}).get("assetId")}
    if hub_ids and not args.no_hero_assets:
        hub = replace(hub, "\t-- @@HUB_ASSETS@@\n", "\tHUB_ASSETS = {" + ", ".join(f"{k} = {v}" for k, v in hub_ids.items()) + "}\n")
        print("hub assets:", ", ".join(hub_ids))
    # v42 anomaly objects of the main map (printer, mirror frames) from Blender assets (OfficeAnomalyUpgrade.luau)
    anom = (evo / "OfficeAnomalyUpgrade.luau").read_text()
    anom = replace(anom, "--!strict\n", "")
    anom = replace(anom, "\nreturn attachAnomalyUpgrade\n", "\n")
    anom_ids = {k: registry[k]["assetId"] for k in ("Printer", "MirrorFrame", "ArtFrame", "WallCalendar", "WallPlanter", "VentFrame", "VentLeaf", "ServiceDoor", "DoorLever") if registry.get(k, {}).get("assetId")}
    if anom_ids and not args.no_hero_assets:
        anom = replace(anom, "\t-- @@ANOMALY_ASSETS@@\n", "\tASSETS = {" + ", ".join(f"{k} = {v}" for k, v in anom_ids.items()) + "}\n")
        print("anomaly assets:", ", ".join(anom_ids))
    # v42 plants and desk decor from Blender assets (OfficePlantUpgrade.luau) replace the client EditableMesh plants
    plant = (evo / "OfficePlantUpgrade.luau").read_text()
    plant = replace(plant, "--!strict\n", "")
    plant = replace(plant, "\nreturn attachPlantUpgrade\n", "\n")
    plant_keys = ("PlantFig", "PlantLily", "PlantMonstera", "DecorVase", "DecorBookStack", "DecorBookRow", "DecorOpenBook")
    plant_ids = {k: registry[k]["assetId"] for k in plant_keys if registry.get(k, {}).get("assetId")}
    if plant_ids and not args.no_hero_assets:
        plant = replace(plant, "\t-- @@PLANT_ASSETS@@\n", "\tASSETS = {" + ", ".join(f"{k} = {v}" for k, v in plant_ids.items()) + "}\n")
        print("plant assets:", len(plant_ids))
    # start room: two report stands instead of one (OfficeStartRoom.luau)
    startroom = (evo / "OfficeStartRoom.luau").read_text()
    startroom = replace(startroom, "--!strict\n", "")
    startroom = replace(startroom, "\nreturn fixStartRoom\n", "\n")
    # v42 office furniture (chairs) from Blender assets (OfficeFurnitureUpgrade.luau)
    furniture = (evo / "OfficeFurnitureUpgrade.luau").read_text()
    furniture = replace(furniture, "--!strict\n", "")
    furniture = replace(furniture, "\nreturn attachFurnitureUpgrade\n", "\n")
    furniture_ids = {k: registry[k]["assetId"] for k in ("ErgoChair", "MeetingChair", "VisitorChair", "MonitorShell", "MonitorShellP", "MonitorFoot", "Keyboard", "Toilet", "WallSockets") if registry.get(k, {}).get("assetId")}
    if furniture_ids and not args.no_hero_assets:
        furniture = replace(furniture, "\t-- @@FURNITURE_ASSETS@@\n", "\tASSETS = {" + ", ".join(f"{k} = {v}" for k, v in furniture_ids.items()) + "}\n")
        print("furniture assets:", ", ".join(furniture_ids))
    # v43 archive cabinets from Blender (OfficeArchiveUpgrade.luau)
    archive = (evo / "OfficeArchiveUpgrade.luau").read_text()
    archive = replace(archive, "--!strict\n", "")
    archive = replace(archive, "\nreturn attachArchiveUpgrade\n", "\n")
    archive_keys = ("ArchiveCabinet", "ArchiveDoor", "ArchiveDoorM", "GlazedCabinet", "GlazedDoor", "GlazedDoorM", "ShelfRack", "ShelfLoad", "LowCabinet", "LowDoor", "LowDoorM", "FileCabinet", "FileDrawer", "SortingCabinet", "CornerShelf", "FormsCabinet", "KitchenBody", "SideBody", "CoffeeBody", "KitchenDoor", "KitchenDoorM", "SideDoor", "SideDoorM", "SinkDoor", "CoffeeDoor", "LockerBody", "LockerDoor", "FirstAidBody", "FirstAidDoor", "ExtinguisherBody", "ExtinguisherDoor", "FireHoseBody", "FireHoseDoor")
    archive_ids = {k: registry[k]["assetId"] for k in archive_keys if registry.get(k, {}).get("assetId")}
    if archive_ids and not args.no_hero_assets:
        archive = replace(archive, "\t-- @@ARCHIVE_ASSETS@@\n", "\tASSETS = {" + ", ".join(f"{k} = {v}" for k, v in archive_ids.items()) + "}\n")
        print("archive assets:", ", ".join(archive_ids))
    # v43 EAST dressing: workstations and plants in the empty middle (OfficeEastDressing.luau)
    east = (evo / "OfficeEastDressing.luau").read_text()
    east = replace(east, "--!strict\n", "")
    east = replace(east, "\nreturn attachEastDressing\n", "\n")
    # v43 repair of double-encoded UTF-8 labels (OfficeTextFix.luau)
    textfix = (evo / "OfficeTextFix.luau").read_text()
    textfix = replace(textfix, "--!strict\n", "")
    textfix = replace(textfix, "\nreturn attachTextFix\n", "\n")
    # v43 intro memory (OfficeIntroMemory.luau)
    intro = (evo / "OfficeIntroMemory.luau").read_text()
    intro = replace(intro, "--!strict\n", "")
    intro = replace(intro, "\nreturn attachIntroMemory\n", "\n")
    # v43 atmosphere and stingers (OfficeAtmosphere.luau)
    atmos = (evo / "OfficeAtmosphere.luau").read_text()
    atmos = replace(atmos, "--!strict\n", "")
    atmos = replace(atmos, "\nreturn attachAtmosphere\n", "\n")
    horror_audio = json.loads((evo / "audio" / "uploaded_audio.json").read_text()) if (evo / "audio" / "uploaded_audio.json").exists() else {}
    atmos_keys = {"Vent": "KONTUR_Vent", "OfficeFar": "KONTUR_OfficeFar", "StingLevel": "KONTUR_StingLevel", "StingWrong": "KONTUR_StingWrong", "StingDeath": "KONTUR_StingDeath"}
    atmos_map = {k: horror_audio[v]["assetId"] for k, v in atmos_keys.items() if horror_audio.get(v, {}).get("assetId") and not horror_audio[v].get("error")}
    if atmos_map and not args.no_hero_assets:
        atmos = replace(atmos, "\t-- @@ATMOS_AUDIO@@\n", "\tA = {" + ", ".join(f"{k} = {v}" for k, v in atmos_map.items()) + "}\n")
        print("atmosphere audio:", ", ".join(atmos_map))
    # v43 live details: steam, LEDs, clocks (OfficeLiveDetails.luau)
    live = (evo / "OfficeLiveDetails.luau").read_text()
    live = replace(live, "--!strict\n", "")
    live = replace(live, "\nreturn attachLiveDetails\n", "\n")
    # v43 window views (OfficeWindowViews.luau)
    views = (evo / "OfficeWindowViews.luau").read_text()
    views = replace(views, "--!strict\n", "")
    views = replace(views, "\nreturn attachWindowViews\n", "\n")
    # v43 per-room floors (OfficeFloors.luau)
    floors = (evo / "OfficeFloors.luau").read_text()
    floors = replace(floors, "--!strict\n", "")
    floors = replace(floors, "\nreturn attachFloors\n", "\n")
    # v43 corridor dressing (OfficeCorridorDressing.luau)
    corridor = (evo / "OfficeCorridorDressing.luau").read_text()
    corridor = replace(corridor, "--!strict\n", "")
    corridor = replace(corridor, "\nreturn attachCorridorDressing\n", "\n")
    # v43 wall decor: air conditioners, stains, cracks, panels, pipes, alarms, cameras, signs, vents, shelves (OfficeWallDecor.luau, Blender meshes)
    walldecor = (evo / "OfficeWallDecor.luau").read_text()
    walldecor = replace(walldecor, "--!strict\n", "")
    walldecor = replace(walldecor, "\nreturn attachWallDecor\n", "\n")
    wall_dir = evo / "blender" / "out_wall" / "fbx"
    # removed at the user's request (15.11): stains, cracks, peeling paint, blisters, wall hole, tally marks, open panel, ladder, sanitizer, keypad
    WALL_NOT_DECOR = {"WaterCooler", "CoatRack", "FicusFloor", "DocPile", "FilingCabinet", "PlantFig", "PlantLily", "PlantMonstera", "WcMirror", "DecorOpenBook", "SofaCushion", "CamCorner"}  # hero items built in wall_hero.py for OfficeDecor, not wall decor
    wall_removed = {"StainBloom", "StainStreaks", "StainTide", "RustDrip", "DampLow", "CrackLong", "CrackStar", "CrackStep", "PeelPatch", "PaintBlister", "WallHole", "TallyMarks",
                    "ElecPanelOpen", "WallLadder", "Sanitizer", "Keypad", "ElecPanel", "Thermostat", "EmergencyLamp", "FanVent", "MouseHole"}
    wall_ids = {p.stem: registry[p.stem]["assetId"] for p in sorted(wall_dir.glob("*.fbx")) if registry.get(p.stem, {}).get("assetId") and p.stem not in wall_removed and p.stem not in WALL_NOT_DECOR} if wall_dir.exists() else {}
    if wall_ids and not args.no_hero_assets:
        walldecor = replace(walldecor, "\t-- @@WALL_ASSETS@@\n", "\tASSETS = {" + ", ".join(f"{k} = {v}" for k, v in wall_ids.items()) + "}\n")
        print("wall decor assets:", len(wall_ids))
    # v43 user cleanup (OfficeUserCleanup.luau)
    usercleanup = (evo / "OfficeUserCleanup.luau").read_text()
    usercleanup = replace(usercleanup, "--!strict\n", "")
    usercleanup = replace(usercleanup, "\nreturn attachUserCleanup\n", "\n")
    if registry.get("SofaCushion", {}).get("assetId") and not args.no_hero_assets:
        usercleanup = replace(usercleanup, "\t-- @@CUSHION_ASSET@@\n", "\tCUSHION_ID = " + str(registry["SofaCushion"]["assetId"]) + "\n")
    if registry.get("CamCorner", {}).get("assetId") and not args.no_hero_assets:
        usercleanup = replace(usercleanup, "\t-- @@CAMC_ASSET@@\n", "\tCAMC_ID = " + str(registry["CamCorner"]["assetId"]) + "\n")
    if registry.get("WcMirror", {}).get("assetId") and not args.no_hero_assets:
        usercleanup = replace(usercleanup, "\t-- @@MIRROR_ASSET@@\n", "\tMIRROR_ID = " + str(registry["WcMirror"]["assetId"]) + "\n")
    if registry.get("PlantLily", {}).get("assetId") and registry.get("PlantMonstera", {}).get("assetId") and not args.no_hero_assets:
        usercleanup = replace(usercleanup, "\t-- @@PLANTS_ASSET@@\n", "\tLILY_ID = " + str(registry["PlantLily"]["assetId"]) + "\n\tMONSTERA_ID = " + str(registry["PlantMonstera"]["assetId"]) + "\n")
    if registry.get("PlantFig", {}).get("assetId") and not args.no_hero_assets:
        usercleanup = replace(usercleanup, "\t-- @@FIG_ASSET@@\n", "\tFIG_ID = " + str(registry["PlantFig"]["assetId"]) + "\n")
    if registry.get("DocPile", {}).get("assetId") and not args.no_hero_assets:
        usercleanup = replace(usercleanup, "\t-- @@DOC_ASSET@@\n", "\tDOC_ID = " + str(registry["DocPile"]["assetId"]) + "\n")
    # v43 MEN/WOMEN dressing (OfficeWcDressing.luau)
    wcroom = (evo / "OfficeWcDressing.luau").read_text()
    wcroom = replace(wcroom, "--!strict\n", "")
    wcroom = replace(wcroom, "\nreturn attachWcDressing\n", "\n")
    # v43 horror anomalies with sound (OfficeHorrorAnomalies.luau)
    horror = (evo / "OfficeHorrorAnomalies.luau").read_text()
    horror = replace(horror, "--!strict\n", "")
    horror = replace(horror, "\nreturn attachHorrorAnomalies\n", "\n")
    horror_audio = json.loads((evo / "audio" / "uploaded_audio.json").read_text()) if (evo / "audio" / "uploaded_audio.json").exists() else {}
    horror_ids = {k.replace("KONTUR_", ""): v["assetId"] for k, v in horror_audio.items() if v.get("assetId") and not v.get("error")}
    if horror_ids and not args.no_hero_assets:
        horror = replace(horror, "\t-- @@HORROR_AUDIO@@\n", "\tAUDIO = {" + ", ".join(f"{k} = {v}" for k, v in horror_ids.items()) + "}\n")
        print("horror audio:", ", ".join(horror_ids))
    shared = replace(shared, "local function createOfficeObjects(office, state)\n", decor + "\n" + startroom + "\n" + hub + "\n" + anom + "\n" + plant + "\n" + furniture + "\n" + textfix + "\n" + archive + "\n" + east + "\n" + wcroom + "\n" + corridor + "\n" + walldecor + "\n" + usercleanup + "\n" + floors + "\n" + views + "\n" + live + "\n" + atmos + "\n" + intro + "\n" + pack + "\n" + horror + "\nlocal function createOfficeObjects(office, state)\n")
    shared = replace(shared, "    return {activate=activate,names=names}\n",
        "    local startOk,startErr=pcall(fixStartRoom,office) if not startOk then warn(\"KONTUR start room failed: \"..tostring(startErr)) end\n    local decorOk,decorErr=pcall(attachOfficeDecor,office,{ventMount,doorMount,Vector3.new(1000,3,72.5)})\n    if not decorOk then warn(\"KONTUR decor failed: \"..tostring(decorErr)) end\n    task.spawn(function() local hubOk,hubErr=pcall(attachHubUpgrade,workspace:FindFirstChild(\"FieldHub\")) if not hubOk then warn(\"KONTUR hub upgrade failed: \"..tostring(hubErr)) end end)\n    task.spawn(function() local anomOk,anomErr=pcall(attachAnomalyUpgrade,office) if not anomOk then warn(\"KONTUR anomaly upgrade failed: \"..tostring(anomErr)) end end)\n    task.spawn(function() local plantOk,plantErr=pcall(attachPlantUpgrade,office) if not plantOk then warn(\"KONTUR plant upgrade failed: \"..tostring(plantErr)) end end)\n    task.spawn(function() local furnOk,furnErr=pcall(attachFurnitureUpgrade,office) if not furnOk then warn(\"KONTUR furniture upgrade failed: \"..tostring(furnErr)) end end)\n    task.spawn(function() local fixOk,fixErr=pcall(attachTextFix,workspace) if not fixOk then warn(\"KONTUR text fix failed: \"..tostring(fixErr)) end end)\n    task.spawn(function() local archOk,archErr=pcall(attachArchiveUpgrade,office) if not archOk then warn(\"KONTUR archive upgrade failed: \"..tostring(archErr)) end end)\n    task.spawn(function() local introOk,introErr=pcall(attachIntroMemory) if not introOk then warn(\"KONTUR intro memory failed: \"..tostring(introErr)) end end)\n    task.spawn(function() local atmOk,atmErr=pcall(attachAtmosphere,office) if not atmOk then warn(\"KONTUR atmosphere failed: \"..tostring(atmErr)) end end)\n    task.spawn(function() local liveOk,liveErr=pcall(attachLiveDetails,office) if not liveOk then warn(\"KONTUR live details failed: \"..tostring(liveErr)) end end)\n    task.spawn(function() local viewOk,viewErr=pcall(attachWindowViews,office) if not viewOk then warn(\"KONTUR window views failed: \"..tostring(viewErr)) end end)\n    task.spawn(function() local floorOk,floorErr=pcall(attachFloors,office) if not floorOk then warn(\"KONTUR floors failed: \"..tostring(floorErr)) end end)\n    task.spawn(function() local corOk,corErr=pcall(attachCorridorDressing,office) if not corOk then warn(\"KONTUR corridor dressing failed: \"..tostring(corErr)) end end)\n    task.spawn(function() local wallOk,wallErr=pcall(attachWallDecor,office) if not wallOk then warn(\"KONTUR wall decor failed: \"..tostring(wallErr)) end end)\n    task.spawn(function() local ucOk,ucErr=pcall(attachUserCleanup,office) if not ucOk then warn(\"KONTUR user cleanup failed: \"..tostring(ucErr)) end end)\n        task.spawn(function() local wcOk,wcErr=pcall(attachWcDressing,office) if not wcOk then warn(\"KONTUR wc dressing failed: \"..tostring(wcErr)) end end)\n    task.spawn(function() local eastOk,eastErr=pcall(attachEastDressing,office) if not eastOk then warn(\"KONTUR east dressing failed: \"..tostring(eastErr)) end end)\n    local pack=attachPropAnomalies(office,names)\n    local horror=attachHorrorAnomalies(office,names)\n    local baseActivate=activate\n    local baseScenarios={ArchiveWriting=true,GreenVent=true,WhisperDoor=true,ArchiveArtSwap=true,ArchiveCalendarShift=true,WestPlanterColor=true,Mirror=true,CeilingWorker=true,BloodFlood=true,Printer=true}\n"
        "    return {activate=function(scenario,round)\n"
        "        local hOk,hHandled=pcall(horror,scenario,round)\n        if not hOk then warn(\"KONTUR horror anomaly failed: \"..tostring(hHandled)) pcall(horror,nil,round) hHandled=false end\n        local ok,handled=pcall(pack,if hHandled then nil else scenario,round)\n        if not ok then warn(\"KONTUR prop anomaly failed: \"..tostring(handled)) handled=scenario~=nil and not baseScenarios[scenario] end\n        if hHandled then handled=true if game:GetService(\"RunService\"):IsStudio() then game:GetService(\"ServerStorage\"):SetAttribute(\"KonturPackScenario\",scenario) end elseif not hOk and scenario~=nil and not baseScenarios[scenario] then handled=true end\n"
        "        -- scenarios served by the prop module are published to clients as a clean round (Clear): OfficeDetail* attributes replicate to everyone\n"
        "        if handled then baseActivate(\"Clear\",round) else baseActivate(scenario,round) end\n    end,names=names}\n")
    scripts[server_key] = mounts + "\n" + shared + "\n" + server + "\n" + style_file("RoomStyle.server.luau").read_text()
    if args.perf and not args.no_trim:
        # v39: tiny parts stop casting shadows and answering ray queries; runs first, before any player exists.
        trim = (evo / "PerfTrim.luau").read_text()
        trim = replace(trim, "--!strict\n", "")
        scripts[server_key] = "do\n" + trim + "\nend\n" + scripts[server_key]
    scripts[("LocalScript", "KonturScenePresentation")] += "\n" + mounts + "\n" + (folder / "OfficeObjects.client.luau").read_text()
    plants = style_file("RoomPlants.client.luau").read_text()
    plants = load_source(evo / "plants_patch.py", "plants_patch").apply(plants, replace)
    # v42: the client EditableMesh path built nothing (3 slots, Destroy kills the mesh) but took the slots of the blood and the ceiling worker;
    # plants and desk decor now come from the server (OfficePlantUpgrade.luau)
    if plant_ids and not args.no_hero_assets:
        plants = replace(plants, "local editable=AssetService:CreateEditableMesh()", "local editable=nil -- v42: off, see OfficePlantUpgrade.luau")
        # the disabled client path would warn for every plant, decor item and the printer shell: the server builds them now
        for warning in ('warn("KonturV36 plant failed: "..tostring(part))', 'warn("KonturV36 decor failed: "..tostring(part))',
                        'warn("KonturV36 printer shell failed: "..tostring(part))'):
            plants = replace(plants, warning, "do end")
    plants = replace(plants,
        '        local function restyle(ws)\n            task.wait(1.5)\n',
        '        local function restyle(ws)\n' + (here / "WorkerDeskPlant.luau").read_text() + '            task.wait(1.5)\n')
    scripts[("LocalScript", "KonturScenePresentation")] += "\n" + plants
    scripts[("LocalScript", "KonturScenePresentation")] += "\n" + (evo / "OfficeReactiveClient.luau").read_text()
    scripts[("LocalScript", "KonturScenePresentation")] += "\n" + (evo / "OfficeIntroClient.luau").read_text()
    # v42: the level announcement ("УРОВЕНЬ N") moves from the screen centre to the top, so it does not cover an anomaly at round start
    original_client = (evo / "OfficeReportClient.original.luau").read_text()
    client_key = ("LocalScript", "OfficeReportClient")
    assert client_key not in scripts, "an earlier layer already replaces OfficeReportClient"
    assert original_in_place(data, patch, original_client.encode()), "OfficeReportClient in the base place differs from the stored original"
    client_text = original_client
    for old, new_text in (
        ("announcement.Position=UDim2.fromScale(.5,.45);announcement.Size=UDim2.new(.84,0,.18,0)", "announcement.Position=UDim2.fromScale(.5,.11);announcement.Size=UDim2.new(.7,0,.13,0)"),
        ("announcement.Position=UDim2.fromScale(.5,.45);announcement.Visible=true", "announcement.Position=UDim2.fromScale(.5,.11);announcement.Visible=true"),
        ("Position=UDim2.fromScale(.5,.42)})", "Position=UDim2.fromScale(.5,.08)})"),
        ("ns.MinTextSize=28;ns.MaxTextSize=64", "ns.MinTextSize=24;ns.MaxTextSize=48"),
    ):
        assert client_text.count(old) == 1, old
        client_text = client_text.replace(old, new_text)
    # v43: no verdict on screen: the toast after an accepted answer is hidden (rejections keep their text), the transition screen is neutral
    for old, new_text in (
        ('toast.Visible=phase.Value=="Active"', 'toast.Visible=(not accepted) and phase.Value=="Active"'),
        ('resultLabel.Text=result.Value~="" and result.Value or "ПОДГОТОВКА ОФИСА"', 'resultLabel.Text="ПОДГОТОВКА ОФИСА"'),
        ('resultLabel.TextColor3=correct.Value and Color3.fromRGB(128,220,187) or Color3.fromRGB(240,162,133)', 'resultLabel.TextColor3=Color3.fromRGB(190,212,216)'),
    ):
        assert client_text.count(old) == 1, old
        client_text = client_text.replace(old, new_text)
    scripts[client_key] = client_text
    # v38: blood liquid shading replaces the ReplicatedStorage module (patcher accepts ModuleScript keys).
    for module in ("BloodLiquidSurface",):
        # The base place must still hold exactly the module text this patch was written against.
        original = (here / "blood" / "original" / (module + ".luau")).read_text().encode()
        assert original_in_place(data, patch, original), module + " in the base place differs from blood/original"
        scripts[("ModuleScript", module)] = (here / "blood" / (module + ".luau")).read_text()
    # v39: phone-profile mirror replaces the LocalScript "OfficeMirrors" stored in the base place (13 890 chars in v26).
    mirror_key = ("LocalScript", "OfficeMirrors")
    assert mirror_key not in scripts, "an earlier layer already replaces OfficeMirrors"
    mirror_text = (evo / "OfficeMirrors.luau").read_text()
    if not args.perf:
        # quality build: the mirror keeps the original behaviour on every device (full reflected room, 30 Hz, 480 canvas)
        for old, new in (("local PHONE=UserInput.TouchEnabled and not UserInput.KeyboardEnabled", "local PHONE=false"),
                         ("local MAX_PARTS=PHONE and 500 or 1500", "local MAX_PARTS=math.huge"),
                         ("local COPY_RADIUS=PHONE and 30 or 40", "local COPY_RADIUS=math.huge")):
            assert mirror_text.count(old) == 1, old
            mirror_text = mirror_text.replace(old, new)
    scripts[mirror_key] = mirror_text
    result = patch.patch_place(data, scripts, None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".partial")
    temporary.write_bytes(result)
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
