"""Decor check: attributes KonturDecor* on OfficeMap, model/part counts and KONTUR warnings from the console (Studio Play).
Usage (repo root, repo venv): python sources/evolution-v39/studio_decor_info.py"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
with StudioBridge() as b:
    for _ in range(80):
        s = studio_pick.mine(studio_pick.studios(b))
        if s: studio = s; break
        time.sleep(.5)
    studio = studio_pick.start_play(b, studio)
    time.sleep(16)
    def run(code):
        r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": "Server", "code": code}}, timeout=120)
        return r["content"][0]["text"]
    try:
        print(run('local o=workspace.OfficeMap local t={} for k,v in pairs(o:GetAttributes()) do if string.find(k,"KonturDecor") then t[#t+1]=k.."="..tostring(v) end end table.sort(t) local f=o:FindFirstChild("KonturDecor") return table.concat(t,", ").." | models="..(f and #f:GetChildren() or -1)..", parts="..(f and #f:GetDescendants() or -1)'))
        c = b.call("get_console_output", {"studio_id": studio})["content"][0]["text"]
        print([l[:220] for l in c.splitlines() if "KONTUR" in l or "rror" in l][-8:])
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
