"""Upload the Blender FBX models to Roblox (Open Cloud Assets API through the Studio MCP bridge) and record the asset ids.
Prerequisites (set by the creator in Studio, Assistant Settings -> MCP Permissions):
  1. Open Cloud scopes asset:read and asset:write granted to the Assistant;
  2. the directory holding the FBX files approved for uploads (default: sources/evolution-v39/blender/out, out_hub and out_wall).
Usage (repo venv): python sources/evolution-v39/studio_upload_assets.py [--only Bookcase,HazmatSuit] [--force] [--user <userId>]
Writes sources/evolution-v39/blender/uploaded_assets.json {item: {"operation": ..., "assetId": ...}}; existing entries are kept."""
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from studio_bridge import StudioBridge
sys.path.insert(0, str(HERE))
import studio_pick

only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
user = sys.argv[sys.argv.index("--user") + 1] if "--user" in sys.argv else "11833648922"
force = "--force" in sys.argv  # re-upload even when the item already has an asset id (new asset, the old id is kept as previous)
registry = HERE / "blender" / "uploaded_assets.json"
done = json.loads(registry.read_text()) if registry.exists() else {}
files = sorted(list((HERE / "blender" / "out" / "fbx").glob("*.fbx")) + list((HERE / "blender" / "out_hub" / "fbx").glob("*.fbx")) + list((HERE / "blender" / "out_wall" / "fbx").glob("*.fbx")))
with StudioBridge() as b:
    studio = None
    for _ in range(80):
        listing = studio_pick.studios(b)
        # Open Cloud rights belong to the place saved to Roblox, never to a local-file window: prefer the cloud window
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
        body = json.dumps({"request": {"assetType": "Model", "displayName": "KONTUR_" + name, "description": "KONTUR interior item modelled in Blender", "creationContext": {"creator": {"userId": user}}}})
        err, text = call({"method": "POST", "endpoint": "/assets/v1/assets", "body": body, "files": [{"name": "fileContent", "path": str(path)}], "scopes": ["asset:read", "asset:write"]})
        print(name, "->", text[:300], flush=True)
        if err:
            print("stopped: fix permissions first (see the docstring)")
            break
        try:
            operation = json.loads(text.split("\n", 1)[-1] if not text.lstrip().startswith("{") else text)
        except Exception:
            operation = {}
        op_id = (operation.get("operationId") or operation.get("path", "").split("/")[-1])
        done[name] = {"operation": op_id, "previous": done.get(name, {}).get("assetId")}
        for _ in range(40):
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
        registry.write_text(json.dumps(done, indent=1))
