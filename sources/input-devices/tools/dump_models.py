"""Только чтение: открывает копию карты в своей Studio (Edit) и печатает устройство моделей Keyboard и MouseAndMat (детали, размеры,
положение относительно модели, цвет, материал, меш) плюс число таких моделей по комнатам. Карту не меняет.
Использование (корень репозитория, python из venv): python sources/input-devices/tools/dump_models.py [maps/Kontur_Office_v42_QA.rbxl] > dump.json
Запускается, только когда нет чужих окон Studio (код 3 иначе)."""
import json, os, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO.parent))
from studio_bridge import StudioBridge
BIN = "/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"
src = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((REPO / "maps").glob("Kontur_Office_v*_QA.rbxl"))[-1]
def others():
    r = subprocess.run(["pgrep", "-f", "^/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"], capture_output=True, text=True)
    return r.stdout.split()
if others():
    print("чужая Studio открыта, не запускаю", file=sys.stderr); sys.exit(3)
tmp = Path(tempfile.mkdtemp(prefix="inputs-dump-"))
copy = tmp / "InputsDump.rbxl"; shutil.copy2(src, copy)
proc = subprocess.Popen([BIN, "-task", "EditFile", "-localPlaceFile", str(copy)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
LUA = r'''
local H=game:GetService("HttpService")
local om=workspace.OfficeMap
local out={models={}, counts={}}
local function dump(m)
  local pv=m:GetPivot()
  local cf,size=m:GetBoundingBox()
  local item={name=m.Name,path=m:GetFullName(),bbox={size.X,size.Y,size.Z},bboxCenterRel={pv:PointToObjectSpace(cf.Position).X,pv:PointToObjectSpace(cf.Position).Y,pv:PointToObjectSpace(cf.Position).Z},attrs=m:GetAttributes(),parts={}}
  for _,d in ipairs(m:GetDescendants()) do
    if d:IsA("BasePart") then
      local rel=pv:ToObjectSpace(d.CFrame)
      local ex={name=d.Name,class=d.ClassName,size={d.Size.X,d.Size.Y,d.Size.Z},pos={rel.X,rel.Y,rel.Z},rot={rel:ToEulerAnglesXYZ()},color=d.Color:ToHex(),material=d.Material.Name,transparency=d.Transparency,collide=d.CanCollide,anchored=d.Anchored}
      if d:IsA("MeshPart") then ex.mesh=d.MeshId ex.tex=d.TextureID end
      local kids={}
      for _,c in ipairs(d:GetChildren()) do kids[#kids+1]=c.ClassName..":"..c.Name end
      ex.kids=kids
      item.parts[#item.parts+1]=ex
    end
  end
  return item
end
local firstK,firstM
for _,d in ipairs(om:GetDescendants()) do
  if d:IsA("Model") then
    if d.Name=="Keyboard" then out.counts.Keyboard=(out.counts.Keyboard or 0)+1 if not firstK then firstK=d end
    elseif d.Name=="MouseAndMat" then out.counts.MouseAndMat=(out.counts.MouseAndMat or 0)+1 if not firstM then firstM=d end end
  end
end
if firstK then out.models[1]=dump(firstK) end
if firstM then out.models[2]=dump(firstM) end
local lenList={}
for _,d in ipairs(om:GetDescendants()) do
  if d:IsA("Model") and d.Name=="Keyboard" then local b=d:FindFirstChild("Body") if b then lenList[#lenList+1]=string.format("%.2fx%.2fx%.2f",b.Size.X,b.Size.Y,b.Size.Z) end end
end
out.keyboardBodySizes=lenList
local mm={}
for _,d in ipairs(om:GetDescendants()) do
  if d:IsA("Model") and d.Name=="MouseAndMat" then local cf,sz=d:GetBoundingBox() mm[#mm+1]=string.format("%.2fx%.2fx%.2f",sz.X,sz.Y,sz.Z) end
end
out.mouseSizes=mm
return H:JSONEncode(out)
'''
try:
    with StudioBridge() as b:
        sid = None
        for _ in range(120):
            try:
                lst = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
            except Exception:
                lst = []
            hit = [s for s in lst if (s.get("file") or "") == copy.name]
            if hit and hit[0].get("mode") == "Edit":
                sid = hit[0]["id"]; break
            time.sleep(2)
        time.sleep(6)
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": sid, "datamodel_type": "Edit", "code": LUA}}, timeout=180)
        print(r["content"][0]["text"])
finally:
    try: os.kill(proc.pid, signal.SIGKILL)
    except Exception: pass
    time.sleep(1); shutil.rmtree(tmp, ignore_errors=True)
