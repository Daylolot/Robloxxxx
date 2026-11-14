import sys, json, base64, time
sys.path.insert(0,'/Users/nikitakorcagin/Desktop/Claude/Robloxxxx_work')
from studio_bridge import StudioBridge
class S:
    def __init__(self,want="v36"):
        self.b=StudioBridge().__enter__()
        for _ in range(40):
            st=json.loads(self.b.call("list_roblox_studios",{})["content"][0]["text"])["studios"]
            st=[x for x in st if x.get("mode")!="Unavailable" and want in (x.get("file") or "")]
            if st: break
            time.sleep(1.5)
        else: raise RuntimeError("no studio")
        self.id=st[0]["id"]
    def luau(self,code,mode="Edit"):
        r=self.b.call("execute_luau",{"studio_id":self.id,"datamodel_type":mode,"code":code})
        return "\n".join(c.get("text","") for c in r["content"])
    def shot(self,path):
        r=self.b.call("screen_capture",{"studio_id":self.id,"capture_id":"x"})
        for c in r["content"]:
            if c["type"]=="image":
                open(path,"wb").write(base64.b64decode(c["data"])); return path
    def close(self): self.b.close()
