#!/usr/bin/env python3
"""Static load scanner for KONTUR Luau sources (stdlib only).

Usage:
  static_scan.py <dir> [--json] [--diff previous_scan.json] [--top N]

Counts, per .luau file, patterns that cost CPU/memory on a phone. It reads text
only; it does not measure FPS. Numbers are a guide for where to measure next.
"""
import argparse, json, re, sys
from pathlib import Path

PATTERNS = {
    "frame_loops": r"\b(RenderStepped|Heartbeat|PreRender|PreSimulation|PostSimulation|Stepped)\b",
    "while_true": r"\bwhile\s+true\s+do\b",
    "get_descendants": r"\bGetDescendants\s*\(",
    "get_children": r"\bGetChildren\s*\(",
    "clone": r":Clone\s*\(",
    "instance_new": r"\bInstance\.new\s*\(",
    "particles": r"\bParticleEmitter\b",
    "lights": r"\b(PointLight|SpotLight|SurfaceLight)\b",
    "editable_mesh": r"\bEditable(Mesh|Image)\b",
    "tween": r"\bTweenService\b",
    "pcall": r"\bpcall\s*\(",
    "remotes": r"\b(FireServer|FireClient|FireAllClients|OnServerEvent|OnClientEvent|InvokeServer|OnServerInvoke)\b",
    "raycast": r"\b(Raycast|GetPartBoundsInBox|GetPartBoundsInRadius)\s*\(",
}
CLIENT_LIMIT = 300_000  # Studio hangs on bigger client scripts (see START_HERE.md)


def scan_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    row = {"chars": len(text), "lines": text.count("\n") + 1, "strict": "--!strict" in text[:200]}
    for key, pattern in PATTERNS.items():
        row[key] = len(re.findall(pattern, text))
    row["client"] = ".client." in path.name
    return row


def risk(row: dict) -> list:
    flags = []
    if row["frame_loops"] + row["while_true"] >= 3:
        flags.append("много циклов")
    if row["frame_loops"] and (row["get_descendants"] or row["clone"] or row["instance_new"]):
        flags.append("аллокации/обход в кадровом цикле?")
    if row["editable_mesh"] and not row["pcall"]:
        flags.append("EditableMesh без pcall")
    if row["client"] and row["chars"] > CLIENT_LIMIT * 0.8:
        flags.append("близко к лимиту клиентского скрипта")
    if row["lights"] > 6:
        flags.append("много света")
    if row["particles"] > 6:
        flags.append("много эмиттеров")
    return flags


def version_of(path: Path) -> int:
    for part in reversed(path.parts):
        m = re.search(r"-v(\d+)$", part)
        if m:
            return int(m.group(1))
    return 0


def current_only(files: list) -> list:
    """Sources keep every historical version side by side (anomalies-v33..v35, ...).
    For each file name keep only the copy from the newest version folder."""
    best: dict = {}
    for p in files:
        if p.name not in best or version_of(p) > version_of(best[p.name]):
            best[p.name] = p
    return sorted(best.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--all", action="store_true", help="включить старые версии одноимённых файлов")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--diff")
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()
    root = Path(a.root)
    files = sorted(p for p in root.rglob("*.luau") if "checks" not in p.parts and "preview" not in p.parts)
    if not a.all:
        files = current_only(files)
    if not files:
        print("нет .luau файлов в", root, file=sys.stderr)
        return 1
    data = {str(p): scan_file(p) for p in files}
    total = {k: sum(r[k] for r in data.values()) for k in ["chars", "frame_loops", "while_true", "get_descendants", "clone", "instance_new", "particles", "lights", "editable_mesh", "pcall"]}
    total["files"] = len(data)
    total["strict_files"] = sum(1 for r in data.values() if r["strict"])
    total["client_chars"] = sum(r["chars"] for r in data.values() if r["client"])
    out = {"total": total, "files": data}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print(f"Файлов: {total['files']}  strict: {total['strict_files']}  символов: {total['chars']}  клиентских: {total['client_chars']} (лимит одного скрипта {CLIENT_LIMIT})")
    print(f"Кадровых циклов: {total['frame_loops']}  while true: {total['while_true']}  Clone: {total['clone']}  Instance.new: {total['instance_new']}  света: {total['lights']}  частицы: {total['particles']}  EditableMesh: {total['editable_mesh']}  pcall: {total['pcall']}")
    print("\nТоп по нагрузке (циклы + аллокации + обходы):")
    ranked = sorted(data.items(), key=lambda kv: -(kv[1]["frame_loops"] * 3 + kv[1]["while_true"] * 2 + kv[1]["get_descendants"] * 2 + kv[1]["clone"] + kv[1]["instance_new"] + kv[1]["particles"] + kv[1]["lights"]))
    for name, r in ranked[: a.top]:
        flags = "; ".join(risk(r))
        print(f"- {name}: симв {r['chars']}, циклы {r['frame_loops']}+{r['while_true']}, обходы {r['get_descendants']}, Clone {r['clone']}, new {r['instance_new']}, свет {r['lights']}, частицы {r['particles']}" + (f"  ⚠ {flags}" if flags else ""))
    if a.diff:
        prev = json.loads(Path(a.diff).read_text())
        pt = prev.get("total", {})
        print("\nИзменение к прошлому снимку:")
        for k, v in total.items():
            if k in pt and pt[k] != v:
                print(f"- {k}: {pt[k]} → {v} ({v - pt[k]:+d})")
        pf = prev.get("files", {})
        new = [n for n in data if n not in pf]
        gone = [n for n in pf if n not in data]
        if new:
            print("Новые файлы:", ", ".join(new))
        if gone:
            print("Удалены:", ", ".join(gone))
    return 0


if __name__ == "__main__":
    sys.exit(main())
