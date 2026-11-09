"""Build the normal and test maps from v24 using the existing binary patcher."""

import argparse
import importlib.util
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("base", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--qa", action="store_true")
args = parser.parse_args()
assert args.base.resolve() != args.output.resolve()

folder = Path(__file__).resolve().parent
parent = folder.parent
patcher = parent / "ceiling-worker-v24" / "build_place.py"
if not patcher.exists():
    patcher = parent / "ceiling_worker_v24" / "build_place.py"
spec = importlib.util.spec_from_file_location("patch_v24", patcher)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

server = (folder / "OfficeReportService.luau").read_text()
if args.qa:
    server = 'script:SetAttribute("ForceMirrorInStudio", true)\n' + server
    hook = '''if game:GetService("RunService"):IsStudio() then
    local submitPreview=Instance.new("BindableFunction")
    submitPreview.Name="MirrorLocalQA"
    submitPreview.OnInvoke=function(player,choice)
        local button=devices[1]:FindFirstChild("ReportButton_"..choice)
        if button then
            submit(player,{Choice=choice,Room="ВЕСЬ ОФИС",Category="ОБЩАЯ ПРОВЕРКА",Source="Console",RoundId=modelState.round},button)
        end
    end
    submitPreview.Parent=Storage
end
'''
    anchor = "Players.PlayerRemoving:Connect("
    assert server.count(anchor) == 1
    server = server.replace(anchor, hook + anchor)

replacements = {
    ("Script", "OfficeReportService"): server,
    ("LocalScript", "OfficeMirrors"): (folder / "OfficeMirrors.luau").read_text(),
}
data = patch.patch_place(args.base.read_bytes(), replacements, None)
args.output.parent.mkdir(parents=True, exist_ok=True)
temporary = args.output.with_suffix(".partial")
temporary.write_bytes(data)
temporary.replace(args.output)
