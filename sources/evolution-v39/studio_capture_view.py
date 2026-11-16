"""Fixed-camera frame of the open map in Studio Play (for before/after comparisons).
Usage (repo root, repo venv): python sources/evolution-v39/studio_capture_view.py <out.png> [px py pz lx ly lz]
Default: office CENTER room desks. Pass the player position and look-at point for other places (hub spawn: 0 3.2 -25 0 3 0)."""
import base64, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
POS = [float(v) for v in sys.argv[2:8]] if len(sys.argv) >= 8 else [1030, 4.6, 28, 1039, 2.6, 42]
SERVER = """
local p=game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local c=p.Character or p.CharacterAdded:Wait()
p:SetAttribute("KonturZone","Office")
c:PivotTo(CFrame.new(%f,3.2,%f)) return "ok" """ % (POS[0], POS[2])
CLIENT = """
local cam=workspace.CurrentCamera;cam.CameraType=Enum.CameraType.Scriptable
cam.CFrame=CFrame.lookAt(Vector3.new(%f,%f,%f),Vector3.new(%f,%f,%f)) return "ok" """ % tuple(POS)
with StudioBridge() as b:
    for _ in range(80):
        s = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(s)
        if picked: studio = picked; break
        time.sleep(.5)
    b.call("start_stop_play", {"studio_id": studio, "is_start": True})
    for _ in range(30):
        if "Server" in b.call("get_studio_state", {"studio_id": studio})["content"][0]["text"]: break
        time.sleep(2)
    try:
        time.sleep(10)
        for mode, code in (("Server", SERVER), ("Client", CLIENT)):
            r = b.call("execute_luau", {"studio_id": studio, "datamodel_type": mode, "code": code}); assert not r.get("isError"), r
            time.sleep(3)
        for item in b.call("screen_capture", {"studio_id": studio, "capture_id": "view"})["content"]:
            if item["type"] == "image": Path(sys.argv[1]).write_bytes(base64.b64decode(item["data"]))
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
