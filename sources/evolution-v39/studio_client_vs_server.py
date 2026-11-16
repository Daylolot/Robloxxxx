"""Where do client-only parts come from? Counts parts per top-level group on server and client and prints the biggest differences.
Usage (repo root, repo venv): python sources/evolution-v39/studio_client_vs_server.py <out.json>"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_pick
CODE = """
local groups,cast={},{}
local function key(d)
  local k=d
  -- group by the first two levels below Workspace.OfficeMap (or the top-level name elsewhere)
  local chain={}
  while k and k~=workspace do table.insert(chain,1,k.Name) k=k.Parent end
  if chain[1]=="OfficeMap" then return table.concat({chain[1],chain[2] or "",chain[3] or ""},"/") end
  return chain[1] or "?"
end
for _,d in ipairs(workspace:GetDescendants()) do
  if d:IsA("BasePart") then local k=key(d) groups[k]=(groups[k] or 0)+1 if d.CastShadow then cast[k]=(cast[k] or 0)+1 end end
end
return game:GetService("HttpService"):JSONEncode({groups=groups,cast=cast})
"""
with StudioBridge() as b:
    for _ in range(80):
        s = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(s)
        if picked: studio = picked; break
        time.sleep(.5)
    for _ in range(10):
        r = b.call("start_stop_play", {"studio_id": studio, "is_start": True})
        if not r.get("isError"): break
        time.sleep(3)
        found = json.loads(b.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
        picked = studio_pick.mine(found)
        if picked: studio = picked
    try:
        time.sleep(25)
        def run(mode):
            for _ in range(6):
                r = b.request("tools/call", {"name": "execute_luau", "arguments": {"studio_id": studio, "datamodel_type": mode, "code": CODE}}, timeout=120)
                if r.get("isError") and "not connected" in r["content"][0]["text"]: time.sleep(3); continue
                assert not r.get("isError"), r; return json.loads(r["content"][0]["text"])
        server, client = run("Server"), run("Client")
    finally:
        b.call("start_stop_play", {"studio_id": studio, "is_start": False})
    keys = set(server["groups"]) | set(client["groups"])
    diff = sorted(((client["groups"].get(k, 0) - server["groups"].get(k, 0), k, client["cast"].get(k, 0), server["cast"].get(k, 0)) for k in keys), reverse=True)
    Path(sys.argv[1]).write_text(json.dumps({"server": server, "client": client, "diff": diff}, ensure_ascii=False, indent=1))
    print("total server", sum(server["groups"].values()), "client", sum(client["groups"].values()))
    for d in diff[:12]: print(d)
