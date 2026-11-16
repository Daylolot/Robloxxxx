"""Fast decor iteration: rerun OfficeDecor.luau (+ uploaded Blender asset ids) inside a running Play session without rebuilding the map.
Deletes workspace.OfficeMap.KonturDecor and its KonturDecor* attributes, runs attachOfficeDecor(office, {}) on the Server and
prints the counters. avoidPoints are empty here (the real build passes vent/door mounts), so placement differs slightly from the
built map; confirm with a real build. Play is left running with --keep so studio_inspect_objects.py can inspect the result.
Usage (repo venv): python sources/evolution-v39/studio_decor_dev.py [--keep]"""
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(HERE))
import studio_pick

keep = "--keep" in sys.argv
probe = sys.argv[sys.argv.index("--probe") + 1] if "--probe" in sys.argv else None
decor = (HERE / "OfficeDecor.luau").read_text().replace("--!strict\n", "", 1).replace("\nreturn attachOfficeDecor\n", "\n")
import json
registry = json.loads((HERE / "blender" / "uploaded_assets.json").read_text())
ids = {k: registry[k]["assetId"] for k in ("Bookcase", "WaterCooler", "CoatRack", "FloorLamp", "Armchair", "FilingCabinet") if registry.get(k, {}).get("assetId")}
decor = decor.replace("\t-- @@HERO_ASSETS@@\n", "\tHERO_ASSETS = {" + ", ".join(f"{k} = {v}" for k, v in ids.items()) + "}\n")

code = """
local office=workspace.OfficeMap
local old=office:FindFirstChild("KonturDecor") if old then old:Destroy() end
for k in pairs(office:GetAttributes()) do if string.find(k,"^KonturDecor") then office:SetAttribute(k,nil) end end
""" + decor + """
local t0=os.clock()
attachOfficeDecor(office,{})
local out={}
for k,v in pairs(office:GetAttributes()) do if string.find(k,"^KonturDecor") and not string.find(k,"Cand_") then out[#out+1]=k:gsub("^KonturDecor_?","")..'='..tostring(v) end end
table.sort(out)
local f=office:FindFirstChild("KonturDecor")
return string.format("%.1fs models=%d parts=%d | ",os.clock()-t0,f and #f:GetChildren() or -1,f and #f:GetDescendants() or -1)..table.concat(out,", ")
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
        time.sleep(12)
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": "Server", "code": code}}, timeout=900)
        print(r["content"][0]["text"][:3000])
        # background asset loading and the mesh swap: wait until every tagged model has its mesh (max 150 s)
        for _ in range(30):
            r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": "Server", "code": 'local f=workspace.OfficeMap.KonturDecor local t,a=0,0 for _,m in ipairs(f:GetChildren()) do if m:GetAttribute("HeroKey") then t+=1 if m:GetAttribute("HeroApplied") then a+=1 end end end return a.."/"..t'}}, timeout=60)
            progress = r["content"][0]["text"]
            if progress.split("/")[0] == progress.split("/")[1]:
                break
            time.sleep(5)
        print("hero swapped:", progress)
        if probe:
            def run(mode, code):
                return b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": code}}, timeout=300)["content"][0]["text"]
            run("Server", 'local p=game.Players:GetPlayers()[1] local c=p.Character local hrp=c.HumanoidRootPart hrp.Anchored=true p:SetAttribute("KonturZone","Office") local m=workspace.OfficeMap.KonturDecor:FindFirstChild("KD_Bookcase") c:PivotTo(CFrame.new(m:GetPivot().Position+Vector3.new(0,14,0))) return "ok"')
            time.sleep(25)
            print(run("Client", Path(probe).read_text()))
        con = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        print([l[:200] for l in con.splitlines() if "KONTUR" in l or "rror" in l][-8:])
    finally:
        if not keep:
            b.call("start_stop_play", {"studio_id": studio, "is_start": False})
