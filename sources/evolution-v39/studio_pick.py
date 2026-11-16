"""Pick our own Studio window by place file name (several Studios can be open: other sessions work in parallel).
KONTUR_STUDIO_RE (regex, default r"^Kontur_Office_v(39|4[0-9])(_QA)?\\.rbxl$") is matched against the `file` of each listed window.
The default deliberately does not match neighbours' files such as Kontur_Office_v39F*.rbxl or FRONT*_QA.rbxl.
For baseline runs on another map set e.g. KONTUR_STUDIO_RE='^Kontur_Office_v38_QA\\.rbxl$'."""
import json, os, re

# pid file of the local Studio this session launched itself (-localPlaceFile). While that process lives, the listing may only
# answer with its file window: a fresh bridge process sees windows one by one and used to fall back to the cloud-saved place
# (an older build) when the file window was not listed yet.
PIDFILE = os.environ.get("KONTUR_STUDIO_PIDFILE", "/private/tmp/claude-501/ev/my_studio.pid")
STUDIO_RE = os.environ.get("KONTUR_STUDIO_RE", r"^Kontur_Office_v(39|4[0-9])(_QA)?\.rbxl$")


def _local_studio_alive():
    try:
        os.kill(int(open(PIDFILE).read().strip()), 0)
        return True
    except Exception:
        return False


def mine(listing):
    """listing: the `studios` list from list_roblox_studios. Returns the id of our window or None."""
    matches = [item for item in listing if re.search(STUDIO_RE, os.path.basename(item.get("file") or ""))]
    if matches:
        # the same file can be open twice (a stale window): the one that is playing is the one being tested
        for item in matches:
            if item.get("mode") == "Play":
                return item["id"]
        return matches[0]["id"]
    if _local_studio_alive():
        return None
    # a place saved to Roblox has no local file in the listing: with a single open window that one is ours
    ready = [item for item in listing if not item.get("file") and item.get("mode") not in (None, "Unavailable")]
    if len(ready) == 1:
        return ready[0]["id"]
    return None


def studios(bridge):
    try:
        return json.loads(bridge.call("list_roblox_studios", {})["content"][0]["text"])["studios"]
    except Exception:
        return []


def start_play(bridge, studio, tries=40):
    """Start Play and wait until the Server datamodel exists. Returns the (possibly re-picked) studio id.
    The freshly spawned bridge process needs a few seconds before it sees the Studio window, so calls made too early
    answer 'No Roblox Studio instances are connected' (isError) instead of raising: retry until Play really runs."""
    import time
    sid = studio
    for _ in range(tries):
        listing = studios(bridge)
        # keep the window that was already picked while it is still listed (a short listing glitch must never
        # silently switch to the cloud-saved place, which can hold an older build); re-pick only when it is gone
        found = studio if any(item.get("id") == studio for item in listing) else mine(listing)
        if found:
            sid = found
            result = bridge.call("get_studio_state", {"studio_id": sid})
            text = result["content"][0]["text"]
            if "Server" in text:
                return sid
            if not result.get("isError") and "Play" not in text:
                bridge.call("start_stop_play", {"studio_id": sid, "is_start": True})
        time.sleep(2)
    raise RuntimeError("Play did not start")
