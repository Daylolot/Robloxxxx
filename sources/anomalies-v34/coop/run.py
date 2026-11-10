"""Install observation scripts only in the disposable copy and run two Studio clients."""
import json
from pathlib import Path
import sys
import time

from studio_bridge import StudioBridge

folder=Path(__file__).resolve().parent
output=Path(sys.argv[1])
with StudioBridge() as bridge:
    def decode(result):
        if result.get("isError"):
            raise RuntimeError(result)
        return json.loads(result["content"][0]["text"])
    for _ in range(50):
        available=decode(bridge.call("list_roblox_studios",{}))["studios"]
        candidates=[studio for studio in available if studio["name"]=="Kontur_Office_v34_Coop_QA.rbxl"]
        if len(candidates)==1:
            studio=candidates[0]["id"]
            break
        time.sleep(.5)
    else:
        raise RuntimeError("Could not connect to disposable copy")

    def run(code):
        result=bridge.call("execute_luau",{"studio_id":studio,"datamodel_type":"Edit","code":code})
        return decode(result)

    client=(folder/"client.luau").read_text()
    server=(folder/"server.luau").read_text()
    print(run(f"""
assert(not game:GetService("RunService"):IsRunning())
local function install(parent,class,name,source)
    local item=parent:FindFirstChild(name) or Instance.new(class)
    item.Name=name
    item.Source=source
    item.Parent=parent
end
install(game.ServerScriptService,"Script","PrinterCoopQA_Server",[====[{server}]====])
install(game.StarterPlayer.StarterPlayerScripts,"LocalScript","PrinterCoopQA_Client",[====[{client}]====])
_G.OfficeCoop34Result=nil
task.spawn(function()
    local ok,value=pcall(function()
        return game:GetService("StudioTestService"):ExecuteMultiplayerTestAsync(1,"OfficeCoop34")
    end)
    _G.OfficeCoop34Result={{ok=ok,value=value}}
end)
return {{launched=true}}
"""),flush=True)
    for _ in range(95):
        try:
            result=run("return _G.OfficeCoop34Result or {pending=true}")
        except (RuntimeError,TimeoutError) as error:
            print(str(error)[:250],flush=True)
        else:
            if not result.get("pending"):
                data=json.loads(result["value"]) if result.get("ok") and isinstance(result["value"],str) else result
                output.write_text(json.dumps(data,indent=2)+"\n")
                print(data,flush=True)
                sys.exit(0 if data.get("ok") else 1)
        time.sleep(2)
    raise RuntimeError("Multiplayer test did not return a result")
