"""Проверка слоя «клавиатура и мышь» в игре (Studio Play, один клиент). Карту не меняет, работает с копией.

Что проверяет:
  1. состав: у всех моделей Keyboard и MouseAndMat (и копий KE_...) старые детали Body/Key/Mat/Mouse заменены мешами, всё закреплено, число совпадает с базой;
  2. в консоли нет ошибок и предупреждений KONTUR mouse / furniture upgrade;
  3. аномалия KeyboardGone на новой клавиатуре: модель прячется целиком (все меши прозрачные), аномалия не падает;
  4. затем запускает штатную регрессию раундов studio_verify_rounds.py (кадры и Studio_Check.json).
Использование (корень репозитория, python из venv): python sources/input-devices/tools/verify_inputs.py <карта> <папка_результата>
Запускается только когда нет чужих окон Studio (код 3)."""
import json, os, re, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO.parent))
from studio_bridge import StudioBridge

BIN = "/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"
src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
ROUNDS = REPO / "sources" / "evolution-v39" / "studio_verify_rounds.py"
STUDIO_RE = "^/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"


def studio_pids():
    r = subprocess.run(["pgrep", "-f", STUDIO_RE], capture_output=True, text=True)
    return {int(x) for x in r.stdout.split() if x.strip()}


if studio_pids():
    print("чужая Studio открыта, не запускаю", file=sys.stderr)
    sys.exit(3)

tmp = Path(tempfile.mkdtemp(prefix="inputs-verify-"))
# копия называется как штатная QA-карта, чтобы studio_verify_rounds.py (studio_pick.mine) нашёл именно это окно
copy = tmp / "Kontur_Office_v42_QA.rbxl"
shutil.copy2(src, copy)
proc = subprocess.Popen([BIN, "-task", "EditFile", "-localPlaceFile", str(copy)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
(tmp / "studio.pid").write_text(str(proc.pid))
report = {}

CHECK = r'''
local H=game:GetService("HttpService")
local office=workspace.OfficeMap
local out={keyboards={},mice={},bad={}}
for _,m in ipairs(office:GetDescendants()) do
  if m:IsA("Model") and m.Name=="Keyboard" then
    local meshes,old,unanch=0,0,0
    for _,d in ipairs(m:GetDescendants()) do
      if d:IsA("MeshPart") then meshes+=1 end
      if d:IsA("BasePart") and (d.Name=="Body" or d.Name=="Key") then old+=1 end
      if d:IsA("BasePart") and not d.Anchored then unanch+=1 end
    end
    out.keyboards[#out.keyboards+1]={meshes=meshes,old=old,unanch=unanch,upgraded=m:GetAttribute("FurnitureUpgraded")==true}
  elseif m:IsA("Model") and (m.Name=="MouseAndMat" or m.Name=="KE_MouseAndMat") then
    local meshes,old,unanch=0,0,0
    for _,d in ipairs(m:GetDescendants()) do
      if d:IsA("MeshPart") then meshes+=1 end
      if d:IsA("BasePart") and (d.Name=="Mat" or d.Name=="Mouse") then old+=1 end
      if d:IsA("BasePart") and not d.Anchored then unanch+=1 end
    end
    out.mice[#out.mice+1]={name=m.Name,meshes=meshes,old=old,unanch=unanch,upgraded=m:GetAttribute("InputUpgraded")==true}
  end
end
return H:JSONEncode(out)
'''

try:
    with StudioBridge() as b:
        sid = None
        for _ in range(150):
            try:
                lst = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
            except Exception:
                lst = []
            hit = [s for s in lst if (s.get("file") or "") == copy.name]
            if hit and hit[0].get("mode") == "Edit":
                sid = hit[0]["id"]
                break
            time.sleep(2)
        assert sid, "моя Studio не появилась в списке"
        time.sleep(8)

        def run(mode, lua, timeout=120):
            r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": sid, "datamodel_type": mode, "code": lua}}, timeout=timeout)
            assert not r.get("isError"), r["content"][0]["text"]
            return r["content"][0]["text"]

        for attempt in range(3):
            try:
                b.request("tools/call", {"name": "start_stop_play", "arguments": {"studio_id": sid, "is_start": True}}, timeout=240)
                break
            except TimeoutError:
                print("start_stop_play: таймаут, попытка", attempt + 1, flush=True)
        for _ in range(90):
            try:
                if "Server" in b.call("get_studio_state", {"studio_id": sid})["content"][0]["text"]:
                    break
            except TimeoutError:
                pass
            time.sleep(2)
        time.sleep(100)                                           # декор, подмена мебели и мыши (включая второй проход для восточного зала)
        data = json.loads(run("Server", CHECK))
        report["keyboards"] = {"count": len(data["keyboards"]), "all_upgraded": all(k["upgraded"] for k in data["keyboards"]),
                               "old_parts": sum(k["old"] for k in data["keyboards"]), "unanchored": sum(k["unanch"] for k in data["keyboards"]),
                               "meshes_min_max": [min(k["meshes"] for k in data["keyboards"]), max(k["meshes"] for k in data["keyboards"])]}
        report["mice"] = {"count": len(data["mice"]), "all_upgraded": all(k["upgraded"] for k in data["mice"]), "old_parts": sum(k["old"] for k in data["mice"]),
                          "unanchored": sum(k["unanch"] for k in data["mice"]), "meshes_min_max": [min(k["meshes"] for k in data["mice"]), max(k["meshes"] for k in data["mice"])],
                          "names": sorted({k["name"] for k in data["mice"]})}
        console = b.call("get_console_output", {"studio_id": sid})["content"][0]["text"]
        lines = [l[:220] for l in console.splitlines() if "KONTUR mouse" in l or "furniture upgrade" in l or ("KONTUR" in l and "failed" in l)]
        report["console_kontur"] = lines[-10:]
        # аномалия KeyboardGone на новой клавиатуре
        src_rounds = ROUNDS.read_text()
        server_helpers = re.search(r'server="""(.*?)"""', src_rounds, re.S).group(1)
        lua = server_helpers + r'''
p:SetAttribute("KonturZone","Office")
-- тихие аномалии (KeyboardGone и др.) пишут имя в OfficeScenario, а штатный switch() ждёт OfficeDetailScenario: своя версия
local previous=state.RoundId.Value
state:SetAttribute("OfficeQANext","KeyboardGone")
answer("Clear")
local deadline=os.clock()+14
repeat task.wait(.1) until (state.RoundId.Value>previous and state.Phase.Value=="Active") or os.clock()>deadline
task.wait(1.5)
local hidden,total=0,0
for _,m in ipairs(office:GetDescendants()) do
  if m:IsA("Model") and m.Name=="Keyboard" then
    total+=1
    local allHidden,anyPart=true,false
    for _,d in ipairs(m:GetDescendants()) do
      if d:IsA("BasePart") then anyPart=true if d.Transparency<0.99 then allHidden=false end end
    end
    if anyPart and allHidden then hidden+=1 end
  end
end
return game:GetService("HttpService"):JSONEncode({scenario=state:GetAttribute("OfficeScenario"),detail=state:GetAttribute("OfficeDetailScenario"),roundAdvanced=state.RoundId.Value>previous,phase=state.Phase.Value,hidden=hidden,total=total})
'''
        try:
            report["keyboard_gone"] = json.loads(run("Server", lua, 180))
        except Exception as e:
            report["keyboard_gone"] = {"error": str(e)[-1500:]}
        b.call("start_stop_play", {"studio_id": sid, "is_start": False})
        time.sleep(6)
        (out / "inputs_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
        print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)
        if "--skip-rounds" in sys.argv:
            raise SystemExit(0)
        # штатная регрессия раундов (кадры и Studio_Check.json)
        env = dict(os.environ, PYTHONPATH=str(REPO.parent), KONTUR_STUDIO_PIDFILE=str(tmp / "studio.pid"))
        r = subprocess.run([sys.executable, str(ROUNDS), str(out / "rounds")], env=env, capture_output=True, text=True, cwd=str(REPO), timeout=1500)
        (out / "rounds.log").write_text(r.stdout[-6000:] + "\n---stderr---\n" + r.stderr[-3000:])
        print("регрессия раундов: код", r.returncode, flush=True)
        print((r.stdout or "")[-600:], flush=True)
finally:
    try:
        os.kill(proc.pid, signal.SIGKILL)
    except Exception:
        pass
    time.sleep(1)
    shutil.rmtree(tmp, ignore_errors=True)
    print("моя Studio закрыта, копия удалена", flush=True)
