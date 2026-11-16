"""Debrief check: after a wrong and after a correct answer print the server ResultText and capture the client screen.
Usage (repo root, repo venv): python sources/evolution-v39/studio_capture_debrief.py <out_dir> [Scenario]"""
import base64, json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCENARIO = sys.argv[2] if len(sys.argv) > 2 else "ClockTilted"
SERVER = re.search(r'SERVER = """(.*?)"""\n\nSTEP', (Path(__file__).resolve().parent / "studio_verify_props.py").read_text(), re.S).group(1)
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
    def capture(name):
        for item in b.call("screen_capture", {"studio_id": studio, "capture_id": name})["content"]:
            if item["type"] == "image": (OUT / f"{name}.png").write_bytes(base64.b64decode(item["data"]))
    try:
        time.sleep(10)
        run("Server", SERVER + f'ready() local r=state.RoundId.Value state:SetAttribute("OfficeQANext","{SCENARIO}") nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok"')
        wrong = run("Server", SERVER + 'nearButton("Clear") qa:Invoke(p,"Clear") task.wait(.8) return state.ResultText.Value')
        time.sleep(0.5); capture("wrong_answer"); print("wrong:", wrong)
        run("Server", SERVER + 'ready() local r=state.RoundId.Value state:SetAttribute("OfficeQANext","{0}") nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok"'.replace("{0}", SCENARIO))
        right = run("Server", SERVER + 'nearButton("Anomaly") qa:Invoke(p,"Anomaly") task.wait(.8) return state.ResultText.Value')
        time.sleep(0.5); capture("right_answer"); print("right:", right)
        # recovery: the round change throws (BloodFloodConfig removed), recovery opens a clean round: no stale "БЫЛО"
        run("Server", SERVER + f'ready() local r=state.RoundId.Value state:SetAttribute("OfficeQANext","{SCENARIO}") nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok"')
        recovered = run("Server", SERVER + """
local RS=game:GetService("ReplicatedStorage")
local config=RS:FindFirstChild("BloodFloodConfig")
if config then config.Parent=nil end
local before=state.RoundId.Value
nearButton("Clear") qa:Invoke(p,"Clear")
local deadline=os.clock()+40
repeat task.wait(.3) until (state.RoundId.Value>before and state.Phase.Value=="Active") or os.clock()>deadline
if config then config.Parent=RS end
task.wait(1)
nearButton("Anomaly") qa:Invoke(p,"Anomaly") task.wait(.8)
return state.ResultText.Value""")
        print("after recovery, answered anomaly on the clean round:", recovered)
        clean = run("Server", SERVER + 'state:SetAttribute("OfficeQANext",nil) ready() local r=state.RoundId.Value nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok"')
        # a clean round (level 1 after the reset above) answered "Anomaly"
        run("Server", SERVER + 'ready() return state.ResultText.Value')
        cleanWrong = run("Server", SERVER + 'ready() nearButton("Anomaly") qa:Invoke(p,"Anomaly") task.wait(.8) return state.ResultText.Value')
        print("clean answered anomaly:", cleanWrong)
    finally:
        try: b.call("start_stop_play", {"studio_id": studio, "is_start": False})
        except Exception: pass
