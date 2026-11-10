"""Assemble v34 with the established binary-place patcher and v30 flight data."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--qa", action="store_true")
    args = parser.parse_args()
    assert args.base.resolve() != args.output.resolve()
    folder = Path(__file__).resolve().parent
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
    mounts = (folder / "OfficeMounts.luau").read_text()
    shared = (folder / "OfficeObjects.server.luau").read_text()
    shared = replace(shared, "-- VENT_SPEC", (folder / "VentParts.luau").read_text())
    shared = replace(shared, "-- DOOR_SPEC", (folder / "DoorParts.luau").read_text())
    scripts[server_key] = mounts + "\n" + shared + "\n" + server
    scripts[("LocalScript", "KonturScenePresentation")] += "\n" + mounts + "\n" + (folder / "OfficeObjects.client.luau").read_text()
    result = patch.patch_place(data, scripts, None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".partial")
    temporary.write_bytes(result)
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
