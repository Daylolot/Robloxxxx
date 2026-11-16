"""review-room: съёмка и инвентаризация предметов одной комнаты КОНТУР. ТОЛЬКО ЧТЕНИЕ: карту, скрипты и исходники не меняет.

Что делает:
  1. Копирует карту во временную папку и открывает копию в СВОЁМ Roblox Studio (не трогает чужие окна; PID запоминает и
     в конце закрывает только его, kill -9).
  2. Запускает Play, ждёт построения декора, читает инвентарь комнаты (room_inventory.luau) -> inventory.json, structural.md.
  3. Для каждого предмета снимает 10 ракурсов (8 по кругу через 45 градусов на возвышении 20, 1 сверху, 1 низкий).
     Камера подтягивается, если на пути стена или другой предмет; при блокировке пробует поднять камеру выше.
     Кадры -> frames/NNN_vK.jpg (обрезаны до вьюпорта), контактный лист 5x2 -> sheets/NNN_<имя>.jpg, мета -> meta.json.
  4. Закрывает Play и свою Studio.

Использование (из корня репозитория, python из venv с Pillow):
  python .claude/skills/review-room/scripts/inspect_room.py <ROOM> [--map maps/Kontur_Office_v42_QA.rbxl] [--out <папка>]
         [--only подстрока,подстрока] [--max N] [--resume] [--inventory-only] [--allow-parallel] [--wait-quiet СЕК]
По умолчанию карта = самая новая maps/Kontur_Office_v*_QA.rbxl, папка = docs/room-reviews/<ROOM>_<карта>_<дата>/.
Коды выхода: 0 готово, 2 неверные аргументы или комната не найдена, 3 Studio другой сессии открыта и ждать не разрешено."""
import argparse, base64, io, json, os, re, shutil, signal, subprocess, sys, tempfile, time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]            # .../Robloxxxx
WORK = HERE.parents[4]            # .../Robloxxxx_work (здесь лежит studio_bridge.py)
sys.path.insert(0, str(WORK))
from studio_bridge import StudioBridge  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

try:
    FONT = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)   # со знаками кириллицы
except Exception:
    FONT = ImageFont.load_default()

STUDIO_BIN = "/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"

# ---------------------------------------------------------------- Luau-шаблоны (клиент)
BIND = """
local RunService=game:GetService("RunService")
pcall(function() RunService:UnbindFromRenderStep("KonturReviewCam") end)
workspace:SetAttribute("InspectCF",workspace.CurrentCamera.CFrame)
local old=workspace:FindFirstChild("KonturReviewLamp") if old then old:Destroy() end
local lamp=Instance.new("Part") lamp.Name="KonturReviewLamp" lamp.Size=Vector3.new(.2,.2,.2) lamp.Transparency=1 lamp.Anchored=true lamp.CanCollide=false lamp.CanQuery=false lamp.CanTouch=false lamp.Parent=workspace
local light=Instance.new("PointLight") light.Range=30 light.Brightness=0.4 light.Shadows=false light.Color=Color3.fromRGB(255,244,225) light.Parent=lamp
pcall(function() game:GetService("StarterGui"):SetCoreGuiEnabled(Enum.CoreGuiType.All,false) end)
local pg=game.Players.LocalPlayer:WaitForChild("PlayerGui")
RunService:BindToRenderStep("KonturReviewCam",Enum.RenderPriority.Last.Value+10,function()
  for _,g in ipairs(pg:GetChildren()) do if g:IsA("ScreenGui") and g.Enabled then g.Enabled=false end end -- стартовые экраны и плашки игры закрывают кадр
  local cam=workspace.CurrentCamera
  cam.CameraType=Enum.CameraType.Scriptable cam.FieldOfView=workspace:GetAttribute("InspectFOV") or 58
  light.Brightness=workspace:GetAttribute("InspectLightB") or 0.4
  local cf=workspace:GetAttribute("InspectCF")
  if cf then cam.CFrame=cf lamp.CFrame=cf*CFrame.new(0.6,0.8,0) end
end)
return "bound"
"""

CAM = """
local HttpService=game:GetService("HttpService")
local path=HttpService:JSONDecode([==[__PATH__]==])
local name=[==[__NAME__]==]
local node=workspace
for _,n in ipairs(path) do node=node and node:FindFirstChild(n) end
local ignore={}
if node then for _,c in ipairs(node:GetChildren()) do
  if c.Name==name and (c:GetPivot().Position-Vector3.new(__PX__,__PY__,__PZ__)).Magnitude<0.05 then ignore[#ignore+1]=c end
end end
local CS=game:GetService("CollectionService")
for _,p in ipairs(CS:GetTagged("RRHidden")) do pcall(function() p.LocalTransparencyModifier=0 end) CS:RemoveTag(p,"RRHidden") end
local lp=game.Players.LocalPlayer
if lp.Character then ignore[#ignore+1]=lp.Character end
local params=RaycastParams.new() params.FilterType=Enum.RaycastFilterType.Exclude params.FilterDescendantsInstances=ignore
local center=Vector3.new(__CX__,__CY__,__CZ__)
local base=math.atan2(__LX__,__LZ__)
local want=__DIST__
local function try(azDeg,elDeg)
  local a=base+math.rad(azDeg) local e=math.rad(elDeg)
  local dir=Vector3.new(math.sin(a)*math.cos(e),math.sin(e),math.cos(a)*math.cos(e))
  local hit=workspace:Raycast(center,dir*(want+0.6),params)
  local use=want
  if hit then use=math.max(0,(hit.Position-center).Magnitude-0.6) end
  return dir,use
end
local dir,use=try(__AZ__,__EL__)
if use/want<0.5 then
  for _,extra in ipairs({20,40}) do
    local d2,u2=try(__AZ__,math.min(75,__EL__+extra))
    if u2>use then dir,use=d2,u2 end
    if use/want>=0.5 then break end
  end
end
local xray=0
if use/want<0.5 or __FORCE__==1 then
  -- сквозной ракурс: всё, что стоит между камерой и предметом, прячем ТОЛЬКО на этом клиенте (карта не меняется)
  local a=base+math.rad(__AZ__) local e=math.rad(__EL__)
  local d0=Vector3.new(math.sin(a)*math.cos(e),math.sin(e),math.cos(a)*math.cos(e))
  local ign={table.unpack(ignore)}
  local p2=RaycastParams.new() p2.FilterType=Enum.RaycastFilterType.Exclude p2.FilterDescendantsInstances=ign
  for i=1,8 do
    local hit=workspace:Raycast(center,d0*(want+0.6),p2)
    if not hit then break end
    local part=hit.Instance
    if part:IsA("BasePart") then part.LocalTransparencyModifier=1 CS:AddTag(part,"RRHidden") xray+=1 end
    ign[#ign+1]=part p2.FilterDescendantsInstances=ign
  end
  dir,use=d0,want
end
local fov=58
if use/want<0.85 then fov=math.min(88,58+(1-use/want)*50) end
workspace:SetAttribute("InspectFOV",fov)
workspace:SetAttribute("InspectLightB",math.clamp(use*0.1+0.05,0.12,1.0))
workspace:SetAttribute("InspectCF",CFrame.lookAt(center+dir*use,center))
return string.format("%.3f|%d",use/want,xray)
"""

PARK = """
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local c=p.Character or p.CharacterAdded:Wait()
p:SetAttribute("KonturZone","Office")
local hrp=c:FindFirstChild("HumanoidRootPart") if hrp then hrp.Anchored=true end
c:PivotTo(CFrame.new(__X__,__Y__,__Z__)) return "ok"
"""


class Done(Exception):
    def __init__(self, code):
        self.code = code


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def newest_qa_map() -> Path:
    best, best_v = None, -1
    for p in (REPO / "maps").glob("Kontur_Office_v*_QA.rbxl"):
        m = re.match(r"Kontur_Office_v(\d+)([A-Za-z]*)_QA\.rbxl$", p.name)
        if m:
            v = int(m.group(1)) * 10 + (1 if m.group(2) else 0)
            if v > best_v:
                best, best_v = p, v
    if not best:
        sys.exit("нет карт maps/Kontur_Office_v*_QA.rbxl")
    return best


def studio_pids():
    # якорь ^ нужен: иначе совпадают чужие shell-команды, в тексте которых встречается RobloxStudio
    r = subprocess.run(["pgrep", "-f", "^/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"], capture_output=True, text=True)
    return [int(x) for x in r.stdout.split() if x.strip()]


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)[:48] or "obj"


def crop_view(img: Image.Image) -> Image.Image:
    w, h = img.size
    return img.crop((int(w * 0.08), int(h * 0.12), int(w * 0.92), int(h * 0.89)))


WALL_MOUNTED = re.compile(r"Wall|Radiator|Socket|Clock|Calendar|Board|Sign|Planter|FireHose|Niche|Switch|Vent|Frame|Mirror|Shelf|Suspended|Hanging|Exit|Cable|Poster|Plate|Bracket|Lamp", re.I)


def is_flat(img: Image.Image) -> bool:
    """Кадр почти без деталей (камера упёрлась в плоскую поверхность)."""
    g = crop_view(img).convert("L").resize((64, 36))
    px = list(g.getdata())
    m = sum(px) / len(px)
    return (sum((p - m) ** 2 for p in px) / len(px)) ** 0.5 < 6.0


def structural_flags(o: dict):
    """(issues, notes): issues — вероятные недочёты, notes — справочные сведения (часто нормальны)."""
    f, n = [], []
    if o["parts"] == 0: f.append("пустая модель (нет деталей)")
    if o["noMesh"]: f.append(f"MeshPart без меша: {', '.join(o['noMesh'][:4])}")
    if o["emptyDecal"]: f.append(f"пустая текстура/декаль ({o['emptyDecal']})")
    if o["defaultGrey"]: f.append(f"детали серым цветом по умолчанию ({o['defaultGrey']}) — недокрашено?")
    if o["placeholderText"]: f.append(f"текст-заглушка: {o['texts']}")
    if o["unanchored"]: f.append(f"незакреплённые детали ({o['unanchored']})")
    t = o["tiltDeg"]
    off = min(t % 90, 90 - t % 90)      # 90° у моделей из Blender — ориентация pivot, не наклон
    if off > 2: f.append(f"наклон {off:.1f}° от осей")
    gap = o.get("gapBelow")
    if gap is not None and gap > 0.15 and 0.3 < o["heightAboveFloor"] < 2.5:
        msg = f"зазор {gap:.2f} под предметом"
        (n if WALL_MOUNTED.search(o["name"]) else f).append(msg + (" (настенный)" if WALL_MOUNTED.search(o["name"]) else " (парит?)"))
    if o["outOfRoom"]: f.append("центр вне границ комнаты")
    if o.get("duplicateOf"): f.append(f"дубль на той же позиции (объект №{o['duplicateOf']})")
    # справочно: бело-серые Blender-меши красятся через MeshPart.Color, поэтому «без текстуры» — норма
    if o["tiny"] and o["tiny"] > 0.2 * max(1, o["parts"]): n.append(f"много микродеталей <0.03 ({o['tiny']} из {o['parts']})")
    if o["meshNoAppearance"]: n.append(f"меши без SurfaceAppearance ({o['meshNoAppearance']})")
    if o["touches"]: n.append("рамка пересекается с: " + ", ".join(o["touches"]))
    return f, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("room")
    ap.add_argument("--map")
    ap.add_argument("--out")
    ap.add_argument("--only", default="")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--redo", default="", help="номера предметов через запятую: переснять (с --resume остальные пропускаются)")
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--allow-parallel", action="store_true")
    ap.add_argument("--wait-quiet", type=int, default=0)
    ap.add_argument("--warm", type=int, default=45, help="пауза перед первым кадром: после первого перемещения игрока свет комнаты плавно меняется, ранние кадры тёмные")
    ap.add_argument("--settle", type=int, default=60, help="пауза после построения декора: скрипты игры ещё двигают предметы")
    a = ap.parse_args()

    map_path = Path(a.map).resolve() if a.map else newest_qa_map()
    if not map_path.exists():
        sys.exit(f"нет карты {map_path}")
    out = Path(a.out) if a.out else REPO / "docs" / "room-reviews" / f"{a.room}_{map_path.stem}_{date.today().isoformat()}"

    # ---- свои окна: чужая Studio в списке = риск перехвата (скрипты другой сессии берут первое окно)
    # пауза = нет чужих Studio подряд QUIET_FOR секунд (вторая сессия перезапускает Studio с короткими разрывами)
    QUIET_FOR = 15
    deadline = time.time() + a.wait_quiet
    quiet_since = None
    announced = False
    while not a.allow_parallel:
        if studio_pids():
            quiet_since = None
        else:
            quiet_since = quiet_since or time.time()
            if time.time() - quiet_since >= QUIET_FOR:
                break
        if time.time() > deadline:
            log("Открыта чужая Roblox Studio, pid:", studio_pids(), "— не запускаю. Дождитесь паузы или добавьте --allow-parallel / --wait-quiet СЕК.")
            sys.exit(3)
        if not announced and studio_pids():
            log("жду паузу: открыта чужая Studio, pid", studio_pids())
            announced = True
        time.sleep(3)

    (out / "frames").mkdir(parents=True, exist_ok=True)
    (out / "sheets").mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="review-room-"))
    copy = tmp / f"ReviewRoom_{safe_name(a.room)}_{os.getpid()}.rbxl"
    shutil.copy2(map_path, copy)
    log("карта:", map_path.name, "| копия:", copy, "| результат:", out)
    proc = subprocess.Popen([STUDIO_BIN, "-task", "EditFile", "-localPlaceFile", str(copy)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    (tmp / "studio.pid").write_text(str(proc.pid))
    log("моя Studio pid", proc.pid)

    code = 0
    try:
        with StudioBridge() as b:
            sid = None
            for _ in range(180):
                try:
                    lst = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
                except Exception:
                    lst = []
                mine = [s for s in lst if (s.get("file") or "") == copy.name]
                if mine:
                    sid = mine[0]["id"]
                    if mine[0].get("mode") == "Edit":
                        break
                time.sleep(2)
            if not sid:
                sys.exit("моя Studio не появилась в списке")
            log("Studio в Edit:", sid)
            try:

                def run(mode, lua, timeout=120):
                    r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": sid, "datamodel_type": mode, "code": lua}}, timeout=timeout)
                    if r.get("isError"):
                        raise RuntimeError(r["content"][0]["text"])
                    return r["content"][0]["text"]

                for attempt in range(3):
                    try:
                        b.request("tools/call", {"name": "start_stop_play", "arguments": {"studio_id": sid, "is_start": True}}, timeout=240)
                        break
                    except TimeoutError:
                        log("start_stop_play: таймаут, попытка", attempt + 1)
                        try:
                            if "Server" in b.call("get_studio_state", {"studio_id": sid})["content"][0]["text"]:
                                break
                        except Exception:
                            pass
                for _ in range(90):
                    try:
                        if "Server" in b.call("get_studio_state", {"studio_id": sid})["content"][0]["text"]:
                            break
                    except TimeoutError:
                        pass
                    time.sleep(2)
                # декор строится скриптами при старте: ждём, пока число детей KonturDecor перестанет расти
                last, stable = -1, 0
                for _ in range(45):
                    try:
                        n = int(run("Server", 'local f=workspace:FindFirstChild("OfficeMap") and workspace.OfficeMap:FindFirstChild("KonturDecor") return f and #f:GetDescendants() or -1'))
                    except Exception:
                        n = -2
                    stable = stable + 1 if n == last and n > 0 else 0
                    last = n
                    if stable >= 3:
                        break
                    time.sleep(3)
                log("декор построен, деталей в KonturDecor:", last, "| жду", a.settle, "с, пока скрипты игры закончат расстановку")
                time.sleep(a.settle)

                template = (HERE / "room_inventory.luau").read_text().replace("__ROOM__", a.room)
                inv, page, total = None, 1, None
                while total is None or page <= total:
                    chunk = json.loads(run("Server", template.replace("__FROM__", str(page)).replace("__TO__", str(page + 24))))
                    if chunk.get("error"):
                        log("ОШИБКА инвентаря:", chunk)
                        raise Done(2)
                    if inv is None:
                        inv = chunk
                    else:
                        inv["objects"].extend(chunk["objects"])
                    total = chunk["total"]
                    page += 25
                inv["count"] = len(inv["objects"])
                objs = inv["objects"]
                if a.only:
                    keys = [k.lower() for k in a.only.split(",") if k]
                    objs = [o for o in objs if any(k in o["name"].lower() for k in keys)]
                if a.max and len(objs) > a.max:
                    step = len(objs) / a.max
                    objs = [objs[int(i * step)] for i in range(a.max)]
                (out / "inventory.json").write_text(json.dumps({**inv, "objects": objs, "map": map_path.name}, ensure_ascii=False, indent=1))
                lines = [f"# Структурная проверка: {a.room} ({map_path.name})", "",
                     f"Предметов в списке: {len(objs)}. Границы комнаты (minX,minY,minZ,maxX,maxY,maxZ): {[round(v, 1) for v in inv['bounds']]}.",
                     "«Вероятные недочёты» и «Справочно» — только КАНДИДАТЫ: решение принимается по кадрам.", "",
                     "| № | Предмет | Источник | Деталей | Позиция X,Z | Размер | Вероятные недочёты | Справочно |", "|---|---|---|---|---|---|---|---|"]
                for o in objs:
                    fl, nt = structural_flags(o)
                    lines.append(f"| {o['idx']} | {o['name']} | {o['source']} | {o['parts']} | {o['cx']:.1f}, {o['cz']:.1f} | "
                             f"{o['sx']:.2f}×{o['sy']:.2f}×{o['sz']:.2f} | {'; '.join(fl) if fl else '—'} | {'; '.join(nt) if nt else '—'} |")
                (out / "structural.md").write_text("\n".join(lines) + "\n")
                log("инвентарь:", len(objs), "предметов -> structural.md")
                if a.inventory_only:
                    raise Done(0)

                run("Client", BIND)
                meta_path = out / "meta.json"
                meta = json.loads(meta_path.read_text()) if (a.resume and meta_path.exists()) else []
                redo = {int(x) for x in a.redo.split(",") if x.strip()}
                meta = [m for m in meta if m["idx"] not in redo]
                done = {m["idx"] for m in meta}
                warm_done = False
                park_y = max(14.0, inv["bounds"][4] + 4)
                for k_obj, o in enumerate(objs):
                    if o["idx"] in done:
                        continue
                    tag = f"{o['idx']:03d}"
                    nm = safe_name(o["name"])
                    dims = sorted([o["sx"], o["sy"], o["sz"]])
                    if dims[2] > 6 * max(dims[1], 0.05):
                        # вытянутый предмет (плинтус, лента): расстояние по сечению, а не по длине, иначе камера уходит за десятки стадов
                        radius = max(0.15, (dims[0] ** 2 + dims[1] ** 2) ** 0.5 / 2)
                    else:
                        radius = max(0.15, (o["sx"] ** 2 + o["sy"] ** 2 + o["sz"] ** 2) ** 0.5 / 2)
                    dist = max(1.4, radius * 2.2 + 0.8)
                    run("Server", PARK.replace("__X__", str(o["cx"])).replace("__Y__", str(park_y)).replace("__Z__", str(o["cz"])))
                    time.sleep(2.0)
                    views = []
                    for v in range(10):
                        if v < 8:
                            az, el, d = v * 45, 20, dist
                        elif v == 8:
                            az, el, d = 20, 62, dist * 0.95
                        else:
                            az, el, d = 200, 4, dist * 0.8
                        base_lua = (CAM.replace("__PATH__", json.dumps(o["parent"], ensure_ascii=False)).replace("__NAME__", o["name"])
                                    .replace("__PX__", str(o["px"])).replace("__PY__", str(o["py"])).replace("__PZ__", str(o["pz"]))
                                    .replace("__CX__", str(o["cx"])).replace("__CY__", str(o["cy"])).replace("__CZ__", str(o["cz"]))
                                    .replace("__LX__", str(o["lx"])).replace("__LZ__", str(o["lz"]))
                                    .replace("__DIST__", str(d)).replace("__AZ__", str(az)).replace("__EL__", str(el)))

                        def grab(force):
                            """Ставит камеру и снимает. Возвращает (ratio, xray, img) или None при сбое камеры."""
                            try:
                                ratio_s, xr_s = run("Client", base_lua.replace("__FORCE__", "1" if force else "0")).split("|")
                            except Exception as e:
                                log("  камера:", e)
                                return None
                            ratio, xray = float(ratio_s), int(xr_s)
                            if ratio < 0.5 and not xray:
                                return ratio, xray, None
                            time.sleep(0.5)
                            img = None
                            for item in b.call("screen_capture", {"studio_id": sid, "capture_id": f"{tag}_v{v}"})["content"]:
                                if item["type"] == "image":
                                    img = Image.open(io.BytesIO(base64.b64decode(item["data"]))).convert("RGB")
                            return ratio, xray, img

                        if not warm_done:
                            warm_done = True
                            grab(False)          # включает камеру; первые секунды кадры в игре тёмные (эффекты света), снимки до этого бесполезны
                            time.sleep(a.warm)
                        got = grab(False)
                        if got is None or got[2] is None:
                            views.append(None)
                            continue
                        ratio, xray, img = got
                        flat = False
                        if is_flat(img):
                            # камера упёрлась в плоскую поверхность: повтор сквозным ракурсом
                            got2 = grab(True)
                            if got2 and got2[2] is not None:
                                ratio, xray, img = got2
                                flat = is_flat(img)
                        crop_view(img).save(out / "frames" / f"{tag}_v{v}.jpg", quality=90)
                        views.append({"v": v, "az": az, "el": el, "ratio": round(ratio, 2), "xray": xray, "flat": flat})
                    # контактный лист 5x2
                    W, H = 560, 330
                    sheet = Image.new("RGB", (W * 5, H * 2), (18, 18, 20))
                    dr = ImageDraw.Draw(sheet)
                    for v, info in enumerate(views):
                        x, y = (v % 5) * W, (v // 5) * H
                        if info is None:
                            dr.text((x + 12, y + 12), f"v{v}: ракурс недоступен (стена/предмет на пути)", fill=(220, 130, 130), font=FONT)
                            continue
                        im = Image.open(out / "frames" / f"{tag}_v{v}.jpg").resize((W - 4, H - 4))
                        sheet.paste(im, (x + 2, y + 2))
                        dr.rectangle((x + 4, y + 4, x + 190, y + 22), fill=(0, 0, 0))
                        dr.text((x + 8, y + 7), f"#{o['idx']} {o['name'][:22]} v{v} az{info['az']} el{info['el']}", fill=(255, 255, 255), font=FONT)
                        if info.get("flat"):
                            dr.rectangle((x + 4, y + 44, x + 330, y + 62), fill=(110, 40, 40))
                            dr.text((x + 8, y + 46), "плоский кадр: камера упёрлась в поверхность (сбой ракурса)", fill=(255, 170, 170), font=FONT)
                        if info.get("xray"):
                            dr.rectangle((x + 4, y + 24, x + 290, y + 42), fill=(120, 90, 0))
                            dr.text((x + 8, y + 26), f"сквозной: скрыто деталей {info['xray']} (стена/предмет)", fill=(255, 230, 120), font=FONT)
                    sheet.save(out / "sheets" / f"{tag}_{nm}.jpg", quality=88)
                    meta.append({"idx": o["idx"], "name": o["name"], "sheet": f"sheets/{tag}_{nm}.jpg",
                                 "views": views, "blocked": sum(1 for x in views if x is None)})
                    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
                    log(f"[{k_obj + 1}/{len(objs)}] #{o['idx']} {o['name']}: ракурсов {sum(1 for x in views if x)}/10")
                log("съёмка готова:", len(meta), "листов")
            finally:
                try:
                    b.call("start_stop_play", {"studio_id": sid, "is_start": False})
                    time.sleep(4)
                except Exception as e2:
                    log("остановка Play:", e2)
    except Done as e:
        code = e.code
    finally:
        try:
            os.kill(proc.pid, signal.SIGKILL)   # SIGTERM Studio не закрывает
        except Exception:
            pass
        time.sleep(1)
        shutil.rmtree(tmp, ignore_errors=True)
        log("моя Studio закрыта, временная копия удалена")
    sys.exit(code)


if __name__ == "__main__":
    main()
