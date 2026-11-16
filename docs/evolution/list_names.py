#!/usr/bin/env python3
"""Список имён объектов в бинарной карте .rbxl без Studio (только чтение).
Нужен zstandard (venv проекта: ../venv/bin/python). Использование:
  list_names.py maps/Kontur_Office_v37.rbxl [--grep Chair] [--count]
Выводит «Класс<TAB>Имя<TAB>сколько раз». Иерархию не восстанавливает."""
import argparse, collections, struct, sys
import zstandard

def chunks(data):
    off = 32
    while off + 16 <= len(data):
        name = data[off:off + 4]; clen, ulen = struct.unpack_from("<II", data, off + 4)
        off += 16
        body = data[off:off + (clen or ulen)]; off += clen or ulen
        if clen:
            if body[:4] == b"\x28\xb5\x2f\xfd":
                body = zstandard.ZstdDecompressor().decompress(body, max_output_size=ulen)
            else:
                import lz4.block
                body = lz4.block.decompress(body, uncompressed_size=ulen)
        yield name, body
        if name == b"END\0":
            break

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("place"); ap.add_argument("--grep", default="")
    a = ap.parse_args()
    data = open(a.place, "rb").read()
    classes, names = {}, collections.defaultdict(list)
    for tag, body in chunks(data):
        if tag == b"INST":
            cid, = struct.unpack_from("<I", body, 0); n, = struct.unpack_from("<I", body, 4)
            classes[cid] = body[8:8 + n].decode("utf8", "replace")
        elif tag == b"PROP":
            cid, = struct.unpack_from("<I", body, 0); n, = struct.unpack_from("<I", body, 4)
            prop = body[8:8 + n]
            if prop == b"Name" and body[8 + n] == 1:
                p = 9 + n
                while p < len(body):
                    ln, = struct.unpack_from("<I", body, p); names[cid].append(body[p + 4:p + 4 + ln].decode("utf8", "replace")); p += 4 + ln
    for cid, lst in names.items():
        for name, count in collections.Counter(lst).most_common():
            if a.grep.lower() in name.lower() and classes.get(cid) not in ("Script", "LocalScript", "ModuleScript"):
                print(f"{classes.get(cid)}\t{name}\t{count}")

main()
