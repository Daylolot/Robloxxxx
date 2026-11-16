"""Upload the synthesised horror sounds (sources/evolution-v39/audio/out/*.wav) to Roblox as Audio assets (Open Cloud through the Studio MCP bridge,
same prerequisites as studio_upload_assets.py) and record the asset ids in audio/uploaded_audio.json.
Usage (repo venv): python sources/evolution-v39/studio_upload_audio.py [--only KONTUR_Drone,...] [--force]"""
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(HERE))
import studio_pick

only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
user = "11833648922"
force = "--force" in sys.argv
registry = HERE / "audio" / "uploaded_audio.json"
done = json.loads(registry.read_text()) if registry.exists() else {}
files = sorted((HERE / "audio" / "out").glob("*.wav"))
with StudioBridge() as b:
    studio = None
    for _ in range(80):
        listing = studio_pick.studios(b)
        cloud = [w for w in listing if w.get("persistedToCloud") and w.get("mode") == "Edit"]
        studio = cloud[0]["id"] if cloud else studio_pick.mine(listing)
        if studio:
            break
        time.sleep(.5)

    def call(args, timeout=180):
        r = b.request("tools/call", {"name": "open_cloud_invoke", "arguments": {"studio_id": studio, **args}}, timeout=timeout)
        return r.get("isError"), r["content"][0]["text"]

    for path in files:
        name = path.stem
        if (only and name not in only) or (done.get(name, {}).get("assetId") and not force):
            continue
        body = json.dumps({"request": {"assetType": "Audio", "displayName": name, "description": "KONTUR synthesised horror sound", "creationContext": {"creator": {"userId": user}}}})
        err, text = call({"method": "POST", "endpoint": "/assets/v1/assets", "body": body, "files": [{"name": "fileContent", "path": str(path)}], "scopes": ["asset:read", "asset:write"]})
        print(name, "->", text[:400], flush=True)
        if err:
            print("stopped:", text[:300])
            break
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
                done[name]["error"] = state.get("error")
                print(name, "asset", done[name]["assetId"], state.get("error") or "", flush=True)
                break
        registry.write_text(json.dumps(done, indent=1))
