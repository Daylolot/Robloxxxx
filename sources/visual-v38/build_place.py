"""Assemble v38 (v37 core protection + v36 room style + v38 anomaly visuals) with the established binary-place patcher."""
import argparse
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
    parser.add_argument("--keep-guard", action="store_true", help="QA build that keeps the inspection guard active (for guard tests)")
    args = parser.parse_args()
    assert args.base.resolve() != args.output.resolve()
    folder = Path(__file__).resolve().parent.parent / "anomalies-v35"; style_folder = Path(__file__).resolve().parent.parent / "visual-v36"
    here = Path(__file__).resolve().parent
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
        '    for _,name in ipairs(officeObjects.names) do table.insert(pool,name) end\n')
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
            '    local forced=state:GetAttribute("OfficeQANext")\n'
            '    if modelState.level>1 and table.find(pool,forced) then active=true end\n')
        server = replace(server, '        if script:GetAttribute("ForcePrinterInStudio") and printer then\n',
            '''        local requested=state:GetAttribute("OfficeQANext")
        if requested and table.find(pool,requested) then
            scenario=requested
        elseif script:GetAttribute("ForcePrinterInStudio") and printer then
''')
    # KONTUR v37 core protection: inspection guard, pcall around the round change, watchdog.
    core = Path(__file__).resolve().parent.parent / "core-v37"
    guard = (core / "InspectionGuard.luau").read_text()
    guard = guard.replace("__INSPECT_MIN_SECONDS__", "0" if args.qa and not args.keep_guard else "6")
    assert "__INSPECT" not in guard
    server = replace(server, 'local function context(player,button)\n', guard + 'local function context(player,button)\n')
    server = replace(server, 'local function finishRound(player,message,record,deadHumanoid)\n',
        (core / "RoundRecovery.luau").read_text() + 'local function finishRound(player,message,record,deadHumanoid)\n')
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
    mounts = (folder / "OfficeMounts.luau").read_text()
    shared = (folder / "OfficeObjects.server.luau").read_text()
    shared = replace(shared, "-- VENT_SPEC", (folder / "VentParts.luau").read_text())
    shared = replace(shared, "-- DOOR_SPEC", (folder / "DoorParts.luau").read_text())
    scripts[server_key] = mounts + "\n" + shared + "\n" + server + "\n" + style_file("RoomStyle.server.luau").read_text()
    scripts[("LocalScript", "KonturScenePresentation")] += "\n" + mounts + "\n" + (folder / "OfficeObjects.client.luau").read_text()
    plants = style_file("RoomPlants.client.luau").read_text()
    plants = replace(plants,
        '        local function restyle(ws)\n            task.wait(1.5)\n',
        '        local function restyle(ws)\n' + (here / "WorkerDeskPlant.luau").read_text() + '            task.wait(1.5)\n')
    scripts[("LocalScript", "KonturScenePresentation")] += "\n" + plants
    # v38: blood liquid shading replaces the ReplicatedStorage module (patcher accepts ModuleScript keys).
    for module in ("BloodLiquidSurface",):
        # The base place must still hold exactly the module text this patch was written against.
        original = (here / "blood" / "original" / (module + ".luau")).read_text().encode()
        assert original_in_place(data, patch, original), module + " in the base place differs from blood/original"
        scripts[("ModuleScript", module)] = (here / "blood" / (module + ".luau")).read_text()
    result = patch.patch_place(data, scripts, None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".partial")
    temporary.write_bytes(result)
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
