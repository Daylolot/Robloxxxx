"""Create a copy of the v17 binary place with selected Luau sources replaced."""

import argparse
from pathlib import Path
import struct

import zstandard


HEADER = struct.Struct("<4sIII")
SCRIPT_CLASSES = {"Script", "LocalScript", "ModuleScript"}
REPLACEMENTS = {
    ("LocalScript", "CeilingWorker"): "CeilingWorker.client.luau",
    ("ModuleScript", "CeilingWorkerRound"): "CeilingWorkerRound.luau",
    ("ModuleScript", "CeilingWorkerScene"): "CeilingWorkerScene.luau",
}


def read_string(data, offset):
    length = struct.unpack_from("<I", data, offset)[0]
    start = offset + 4
    return data[start:start + length].decode(), start + length


def encode_string(value):
    data = value.encode()
    return struct.pack("<I", len(data)) + data


def patch_place(data, replacements, qa):
    assert data[:14] == b"<roblox!\x89\xff\r\n\x1a\n"
    position = 32
    chunks = []
    names = {}
    classes = {}
    while position < len(data):
        tag, compressed, size, reserved = HEADER.unpack_from(data, position)
        start = position + HEADER.size
        end = start + (compressed or size)
        original = data[position:end]
        position = end
        packed = data[start:end]
        if tag not in {b"INST", b"PROP"}:
            chunks.append((original, None))
            continue
        body = zstandard.ZstdDecompressor().decompress(packed, max_output_size=size) if compressed else packed
        class_id = struct.unpack_from("<I", body)[0]
        label, offset = read_string(body, 4)
        if tag == b"INST":
            classes[class_id] = (label, struct.unpack_from("<I", body, offset + 1)[0])
        else:
            class_name, count = classes[class_id]
            if class_name in SCRIPT_CLASSES and label in {"Name", "Source"}:
                assert body[offset] == 1
                offset += 1
                prefix = body[:offset]
                values = []
                for _ in range(count):
                    value, offset = read_string(body, offset)
                    values.append(value)
                assert offset == len(body)
                if label == "Name":
                    names[class_id] = values
                else:
                    chunks.append((original, (class_id, prefix, values, reserved)))
                    continue
        chunks.append((original, None))

    output = bytearray(data[:32])
    changed = set()
    for original, record in chunks:
        if record is None:
            output.extend(original)
            continue
        class_id, prefix, values, reserved = record
        class_name, _ = classes[class_id]
        modified = False
        for index, name in enumerate(names[class_id]):
            key = (class_name, name)
            if key in replacements:
                assert key not in changed, key
                values[index] = replacements[key]
            elif qa and key == ("Script", "OfficeReportService"):
                marker = "local flood\n"
                assert values[index].count(marker) == 1
                values[index] = values[index].replace(marker, marker + qa)
            else:
                continue
            changed.add(key)
            modified = True
        if modified:
            body = prefix + b"".join(map(encode_string, values))
            packed = zstandard.ZstdCompressor(level=9).compress(body)
            output.extend(HEADER.pack(b"PROP", len(packed), len(body), reserved) + packed)
        else:
            output.extend(original)
    required = set(replacements)
    if qa:
        required.add(("Script", "OfficeReportService"))
    assert changed == required, (changed, required)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--qa", action="store_true")
    args = parser.parse_args()
    assert args.base.resolve() != args.output.resolve()
    folder = Path(__file__).parent
    replacements = {key: (folder / name).read_text() for key, name in REPLACEMENTS.items()}
    qa = (folder / "StudioPreview.luau").read_text() + "\n" if args.qa else None
    result = patch_place(args.base.read_bytes(), replacements, qa)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(".partial")
    temp.write_bytes(result)
    temp.replace(args.output)


if __name__ == "__main__":
    main()
