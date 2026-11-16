#!/usr/bin/env python3
"""Markdown table «цена аномалии» из нескольких docs/evolution/measure/anomaly_cost_*.json.
Счётчики клиента, дельта к чистому раунду; из каждого файла вычитается «шум» (медиана дельт деталей, инстансов, звуков,
GUI по сценариям этого файла: фоновая подгрузка, не относящаяся к аномалии). Для файла с одним сценарием берётся шум
первого файла. Строки с неверно включённым сценарием (detail не совпадает с именем) пропускаются.
Использование: cost_table.py part1.json part2.json [single.json ...]"""
import json, statistics, sys
FIELDS = ("parts", "instances", "sounds", "gui")
rows, floors = {}, None
for path in sys.argv[1:]:
    d = json.load(open(path))
    items = [(k, v) for k, v in d.items() if isinstance(v, dict) and "delta" in v]
    ok = [(k, v) for k, v in items if (v.get("state") or {}).get("detail") == k or (k == "Mirror" and (v.get("state") or {}).get("mirror"))]
    if len(items) >= 4:
        floors = {f: statistics.median(v["delta"][f] for _, v in ok) for f in FIELDS}
    for k, v in ok:
        rows[k] = (v, dict(floors or {f: 0 for f in FIELDS}))
def net(v, fl):
    dl = dict(v["delta"])
    for f in FIELDS:
        dl[f] = max(0, dl[f] - fl[f]) if f != "gui" else dl[f] - fl[f]
    return dl
def klass(dl):
    heavy = dl["parts"] > 250 or dl["lights"] >= 3 or dl["emitters"] >= 5
    mid = dl["parts"] > 60 or dl["lights"] >= 1 or dl["emitters"] >= 1 or dl["instances"] > 300
    return "тяжёлая" if heavy else "средняя" if mid else "лёгкая"
print("| Аномалия | Δ деталей | Δ света | Δ частиц | Δ звуков | Δ GUI | Δ инстансов клиента | Класс |")
print("|---|---|---|---|---|---|---|---|")
for k, (v, fl) in rows.items():
    dl = net(v, fl)
    print(f"| {k} | {dl['parts']} | {dl['lights']} | {dl['emitters']} | {dl['sounds']} | {dl['gui']} | {dl['instances']} | {klass(dl)} |")
print("\nШум (вычтен):", json.dumps(floors))
