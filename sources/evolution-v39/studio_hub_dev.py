"""Fast hub iteration: run OfficeHubUpgrade.luau (with the uploaded asset ids) in a running Play session and print the result.
Play stays running with --keep (use studio_inspect_hub.py afterwards). Usage (repo venv): python sources/evolution-v39/studio_hub_dev.py [--keep]"""
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(HERE))
import studio_pick

keep = "--keep" in sys.argv
registry = json.loads((HERE / "blender" / "uploaded_assets.json").read_text())
ids = {k: registry[k]["assetId"] for k in ("HazmatSuit", "MaskStation", "HubCase", "HubCaseMed", "SuitRack", "EquipmentBench") if registry.get(k, {}).get("assetId")}
module = (HERE / "OfficeHubUpgrade.luau").read_text().replace("--!strict\n", "", 1).replace("\nreturn attachHubUpgrade\n", "\n")
module = module.replace("\t-- @@HUB_ASSETS@@\n", "\tHUB_ASSETS = {" + ", ".join(f"{k} = {v}" for k, v in ids.items()) + "}\n")
code = module + """
local t0=os.clock()
attachHubUpgrade(workspace.FieldHub)
local suits,station=0,workspace.FieldHub.Equipment.MaskStation:GetAttribute("HubUpgraded")
for _,m in ipairs(workspace.FieldHub.Equipment:GetChildren()) do if m:GetAttribute("HubUpgraded") and string.find(m.Name,"^Hazmat") then suits+=1 end end
return string.format("%.1fs suits=%d station=%s parts=%d",os.clock()-t0,suits,tostring(station),#workspace.FieldHub.Equipment:GetDescendants())
"""
with StudioBridge() as b:
    studio = None
    for _ in range(80):
        studio = studio_pick.mine(studio_pick.studios(b))
        if studio:
            break
        time.sleep(.5)
    studio = studio_pick.start_play(b, studio)
    try:
        time.sleep(10)
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": "Server", "code": code}}, timeout=900)
        print(r["content"][0]["text"][:600])
        con = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        print([l[:200] for l in con.splitlines() if "KONTUR" in l or "rror" in l][-6:])
    finally:
        if not keep:
            b.call("start_stop_play", {"studio_id": studio, "is_start": False})
