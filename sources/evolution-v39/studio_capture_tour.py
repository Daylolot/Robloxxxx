"""Eye-level tour: one frame per room (and the hub) in a single Play session, for visual review.
Camera stands 35% in from a room corner at eye height and looks at the room centre.
Usage (repo root, repo venv): python sources/evolution-v39/studio_capture_tour.py <out_dir>"""
import base64, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SERVER_ROOMS = """
local out={}
for _,room in ipairs(workspace.OfficeMap.Rooms:GetChildren()) do
  local lx,lz,hx,hz=math.huge,math.huge,-math.huge,-math.huge
  for _,d in ipairs(room:GetDescendants()) do if d:IsA("BasePart") then local p=d.Position lx=math.min(lx,p.X) hx=math.max(hx,p.X) lz=math.min(lz,p.Z) hz=math.max(hz,p.Z) end end
  if lx<hx then out[#out+1]={name=room.Name,lx=lx,hx=hx,lz=lz,hz=hz} end
end
return game:GetService("HttpService"):JSONEncode(out)
"""
with StudioBridge() as b:
    for _ in range(80):
        s = studio_pick.mine(studio_pick.studios(b))
        if s: studio = s; break
        time.sleep(.5)
    studio = studio_pick.start_play(b, studio)
    def run(mode, code):
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": code}}, timeout=120)
        assert not r.get("isError"), r
        return r["content"][0]["text"]
    def shot(name, ex, ey, ez, lx, ly, lz):
        run("Server", f'local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait() local c=p.Character or p.CharacterAdded:Wait() p:SetAttribute("KonturZone","Office") c:PivotTo(CFrame.new({ex},3.2,{ez})) return "ok"')
        time.sleep(2.5)
        run("Client", f'local cam=workspace.CurrentCamera cam.CameraType=Enum.CameraType.Scriptable cam.CFrame=CFrame.lookAt(Vector3.new({ex},{ey},{ez}),Vector3.new({lx},{ly},{lz})) return "ok"')
        time.sleep(1.2)
        for item in b.call("screen_capture", {"studio_id": studio, "capture_id": name})["content"]:
            if item["type"] == "image": (OUT / f"{name}.png").write_bytes(base64.b64decode(item["data"]))
    try:
        time.sleep(10)
        rooms = json.loads(run("Server", SERVER_ROOMS))
        print([r["name"] for r in rooms], flush=True)
        for r in rooms:
            cx, cz = (r["lx"] + r["hx"]) / 2, (r["lz"] + r["hz"]) / 2
            w, d = r["hx"] - r["lx"], r["hz"] - r["lz"]
            shot("room_" + r["name"], r["lx"] + 0.3 * w, 4.6, r["lz"] + 0.3 * d, cx + 0.2 * w, 3.2, cz + 0.2 * d)
        shot("hub", 0, 4.6, -25, 0, 4, 0)
    finally:
        try: b.call("start_stop_play", {"studio_id": studio, "is_start": False})
        except Exception: pass
