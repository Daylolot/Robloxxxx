"""Hidden-scenario check: for prop-module scenarios the correct answer "Anomaly" must still be accepted by the server
(the round truth lives in the server round state, not in the replicated attribute), a clean round answered
"Anomaly" must be rejected, and the client must see "Clear". Usage (repo root, repo venv):
  python sources/evolution-v39/studio_verify_answer.py <out.json> [Scenario ...]"""
import json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick

SERVER = re.search(r'SERVER = """(.*?)"""\n\nSTEP', (Path(__file__).resolve().parent / "studio_verify_props.py").read_text(), re.S).group(1)
WANTED = sys.argv[2:] or ["ClockTilted", "RoomBlackout", "BoardMeetingTime"]
out = {}
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
    try:
        time.sleep(10)
        # control: a clean level-1 round answered "Anomaly" must be rejected
        out["control_clean_answered_anomaly"] = run("Server", SERVER + 'ready() local r=state.RoundId.Value nearButton("Anomaly") qa:Invoke(p,"Anomaly") task.wait(.5) local t=state.ResultText.Value newRound(r) return t')
        for scenario in WANTED:
            # level 1 is clean: answer it correctly, then the forced scenario round starts
            run("Server", SERVER + f'ready() local r=state.RoundId.Value state:SetAttribute("OfficeQANext","{scenario}") nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok"')
            client = run("Client", 'return tostring(workspace.OfficeMap.AnomalyReportState:GetAttribute("OfficeDetailScenario"))')
            answer = run("Server", SERVER + 'local r=state.RoundId.Value nearButton("Anomaly") qa:Invoke(p,"Anomaly") task.wait(.5) local t=state.ResultText.Value newRound(r) task.wait(1) return t')
            out[scenario] = {"clientSees": client, "answerAnomalyResult": answer}
            print(scenario, out[scenario], flush=True)
            # leave the chain at a clean state: answer wrong once if the next round is an anomaly round (level reset to 1)
            run("Server", SERVER + 'state:SetAttribute("OfficeQANext",nil) ready() local r=state.RoundId.Value nearButton("Clear") qa:Invoke(p,"Clear") newRound(r) task.wait(1) return "ok"')
    finally:
        try: b.call("start_stop_play", {"studio_id": studio, "is_start": False})
        except Exception: pass
        Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=2))
print("control:", out.get("control_clean_answered_anomaly"))
