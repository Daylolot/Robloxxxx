"""Загрузка FBX клавиатуры и мыши в Roblox (Open Cloud Assets API через мост Studio MCP). Логика как у sources/evolution-v39/studio_upload_assets.py,
но свои папка (sources/input-devices/blender/out/fbx) и реестр (sources/input-devices/blender/uploaded_assets.json): общий реестр второй сессии не трогаем.

Условия (выдаёт владелец в Studio, Assistant -> MCP Permissions): права Open Cloud asset:read и asset:write у Assistant, каталог с FBX одобрен.
Права принадлежат месту, сохранённому в Roblox, поэтому скрипт открывает облачное место отдельной Studio (ТОЛЬКО ЧТЕНИЕ, место не меняется и не
сохраняется) и закрывает её kill -9 по своему pid. Запускается только когда нет чужих окон Studio.

Использование (корень репозитория, python из venv): python sources/input-devices/tools/upload_assets.py [--only Keyboard,MouseSetV2] [--force]
Пишет {предмет: {"operation": ..., "previous": ..., "assetId": ...}}; существующие записи сохраняются (без --force предмет с id пропускается)."""
import json, os, signal, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO.parent))
from studio_bridge import StudioBridge

PLACE_ID = "112192935217270"           # место «11142026_2», сохранённое в Roblox (см. память проекта)
UNIVERSE_ID = "10776556443"            # вселенная этого места (публичный API universes/v1/places/<id>/universe); без неё Studio отвечает «Invalid Launch Intent»
USER_ID = "11833648922"                # создатель ассетов (как в общем загрузчике)
HERE = REPO / "sources" / "input-devices" / "blender"
REGISTRY = HERE / "uploaded_assets.json"
STUDIO_RE = "^/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"


def studio_pids():
    r = subprocess.run(["pgrep", "-f", STUDIO_RE], capture_output=True, text=True)
    return {int(x) for x in r.stdout.split() if x.strip()}


only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
force = "--force" in sys.argv
done = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}
files = sorted((HERE / "out" / "fbx").glob("*.fbx"))
pending = [n for n, e in done.items() if e.get("operation") and not e.get("assetId") and not (only and n not in only)]
todo = [f for f in files if not (only and f.stem not in only) and (force or (not done.get(f.stem, {}).get("assetId") and f.stem not in pending))]
if not todo and not pending:
    print("нечего загружать:", [f.stem for f in files]); sys.exit(0)
if studio_pids():
    print("открыта чужая Studio, не запускаю (мост берёт первое окно)", file=sys.stderr); sys.exit(3)

subprocess.run(["open", f"roblox-studio:1+launchmode:edit+task:EditPlace+placeId:{PLACE_ID}+universeId:{UNIVERSE_ID}"], check=True)
mine = set()
for _ in range(60):
    time.sleep(1)
    mine = studio_pids()
    if mine:
        break
print("моя Studio pid:", sorted(mine), flush=True)
try:
    with StudioBridge() as b:
        studio = None
        for _ in range(150):
            try:
                listing = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
            except Exception:
                listing = []
            cloud = [w for w in listing if w.get("persistedToCloud") and w.get("mode") == "Edit"]
            if cloud:
                studio = cloud[0]["id"]
                break
            time.sleep(2)
        if not studio:
            print("облачное окно Studio не появилось (нужен вход в Roblox Studio и доступ к месту): остановка", file=sys.stderr); sys.exit(4)
        time.sleep(5)

        def call(args, timeout=180):
            r = b.request("tools/call", {"name": "open_cloud_invoke", "arguments": {"studio_id": studio, **args}}, timeout=timeout)
            return r.get("isError"), r["content"][0]["text"]

        def poll(name, op_id, tries=60):
            for _ in range(tries):
                time.sleep(3)
                err, text = call({"method": "GET", "endpoint": f"/assets/v1/operations/{op_id}", "scopes": ["asset:read"]})
                try:
                    state = json.loads(text[text.index("{"):])
                except Exception:
                    continue
                if state.get("done"):
                    done[name]["assetId"] = (state.get("response") or {}).get("assetId")
                    print(name, "asset", done[name]["assetId"], flush=True)
                    if not done[name]["assetId"]:
                        print("   ответ операции:", text[:1500].replace("\n", " "), flush=True)
                    return True
            return False
        for name in pending:                                  # операции, начатые раньше, но не дошедшие до конца
            print(name, "ждёт операцию", done[name]["operation"], flush=True)
            poll(name, done[name]["operation"], 20)
            REGISTRY.write_text(json.dumps(done, indent=1))
        for path in todo:
            name = path.stem
            body = json.dumps({"request": {"assetType": "Model", "displayName": "KONTUR_" + name, "description": "KONTUR input device modelled in Blender", "creationContext": {"creator": {"userId": USER_ID}}}})
            err, text = call({"method": "POST", "endpoint": "/assets/v1/assets", "body": body, "files": [{"name": "fileContent", "path": str(path)}], "scopes": ["asset:read", "asset:write"]})
            print(name, "->", text[:300], flush=True)
            if err:
                print("остановка: сначала выдать права (см. докстринг)", file=sys.stderr)
                sys.exit(5)
            try:
                operation = json.loads(text.split("\n", 1)[-1] if not text.lstrip().startswith("{") else text)
            except Exception:
                operation = {}
            op_id = operation.get("operationId") or operation.get("path", "").split("/")[-1]
            done[name] = {"operation": op_id, "previous": done.get(name, {}).get("assetId")}
            for _ in range(60):
                time.sleep(3)
                err, text = call({"method": "GET", "endpoint": f"/assets/v1/operations/{op_id}", "scopes": ["asset:read"]})
                try:
                    state = json.loads(text[text.index("{"):])
                except Exception:
                    continue
                if state.get("done"):
                    done[name]["assetId"] = (state.get("response") or {}).get("assetId")
                    print(name, "asset", done[name]["assetId"], flush=True)
                    break
            REGISTRY.write_text(json.dumps(done, indent=1))
finally:
    for pid in mine:
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    time.sleep(1)
    print("моя Studio закрыта", flush=True)
