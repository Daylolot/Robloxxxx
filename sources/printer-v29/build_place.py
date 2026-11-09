"""Add the printer round to a v26 map without rewriting map geometry."""
import argparse
import importlib.util
from pathlib import Path
import struct

from zstandard import ZstdDecompressor


def make_sources(data, folder, qa, patch):
    classes, names, sources = {}, {}, {}
    decoder = ZstdDecompressor()
    cursor = 32
    while cursor < len(data):
        tag, packed, size, _ = patch.HEADER.unpack_from(data, cursor)
        start = cursor + patch.HEADER.size
        cursor = start + (packed or size)
        if tag not in {b"INST", b"PROP"}:
            continue
        body = decoder.decompress(data[start:cursor], max_output_size=size) if packed else data[start:cursor]
        class_id = struct.unpack_from("<I", body)[0]
        key, offset = patch.read_string(body, 4)
        if tag == b"INST":
            classes[class_id] = key, struct.unpack_from("<I", body, offset + 1)[0]
            continue
        class_name, count = classes[class_id]
        if class_name not in {"Script", "LocalScript"} or key not in {"Name", "Source"}:
            continue
        assert body[offset] == 1
        offset += 1
        values = []
        for _ in range(count):
            value, offset = patch.read_string(body, offset)
            values.append(value)
        assert offset == len(body)
        (names if key == "Name" else sources)[class_id] = values

    server_name = ("Script", "OfficeReportService")
    client_name = ("LocalScript", "KonturScenePresentation")
    scripts = {}
    for class_id, values in names.items():
        for index, name in enumerate(values):
            key = classes[class_id][0], name
            if key in {server_name, client_name}:
                assert key not in scripts
                scripts[key] = sources[class_id][index]

    server = scripts[server_name]
    def insert(anchor, addition):
        nonlocal server
        assert server.count(anchor) == 1, anchor
        server = server.replace(anchor, anchor + addition)
    insert('local phaseValue=ensure("StringValue","Phase","Preparing")\n',
           'local printer=createPrinter(office,state,phaseValue)\n')
    insert('    if mirrorAvailable then table.insert(pool,"Mirror")end\n',
           '    if printer then table.insert(pool,"Printer")end\n')
    anchor = '        if script:GetAttribute("ForceMirrorInStudio") and mirrorAvailable then\n'
    assert server.count(anchor) == 1
    server = server.replace(anchor, '        if script:GetAttribute("ForcePrinterInStudio") and printer then\n'
                            '            scenario="Printer"\n        elseif' + anchor.split('if', 1)[1])
    insert('    state:SetAttribute("MirrorAnomalyRound",scenario=="Mirror" and modelState.round or nil)\n',
           '    if printer then printer.activate(scenario=="Printer") end\n')
    insert('    state:SetAttribute("MirrorAnomalyRound",nil)\n',
           '    if printer then printer.activate(false) end\n')
    if qa:
        server = 'script:SetAttribute("ForcePrinterInStudio",true)\n' + server
        hook = '''if game:GetService("RunService"):IsStudio() and printer then
    local preview=Instance.new("BindableFunction")
    preview.Name="PrinterLocalQA"
    preview.OnInvoke=function(player,choice)
        if choice=="Read" then return printer.read(player) end
        local button=devices[1]:FindFirstChild("ReportButton_"..choice)
        if button then
            submit(player,{Choice=choice,Room="ВЕСЬ ОФИС",Category="ОБЩАЯ ПРОВЕРКА",Source="Console",RoundId=modelState.round},button)
        end
    end
    preview.Parent=Storage
end
'''
        anchor = "Players.PlayerRemoving:Connect("
        assert server.count(anchor) == 1
        server = server.replace(anchor, hook + anchor)
    scripts[server_name] = (folder / "PrinterRound.luau").read_text() + "\n" + server
    client = (folder / "PrinterPaper.client.luau").read_text()
    assert client.count("-- PRINTER_FLIGHT_DATA") == 1
    client = client.replace("-- PRINTER_FLIGHT_DATA", (folder / "PrinterFlightData.luau").read_text())
    scripts[client_name] += "\n" + client
    return scripts


parser = argparse.ArgumentParser()
parser.add_argument("base", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--qa", action="store_true")
args = parser.parse_args()
assert args.base.resolve() != args.output.resolve()
folder = Path(__file__).resolve().parent
patcher = folder.parent / "ceiling-worker-v24" / "build_place.py"
if not patcher.exists():
    patcher = folder.parent / "ceiling_worker_v24" / "build_place.py"
spec = importlib.util.spec_from_file_location("binary_patch", patcher)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)
data = args.base.read_bytes()
result = patch.patch_place(data, make_sources(data, folder, args.qa, patch), None)
args.output.parent.mkdir(parents=True, exist_ok=True)
temporary = args.output.with_suffix(".partial")
temporary.write_bytes(result)
temporary.replace(args.output)
