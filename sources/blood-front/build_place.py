"""Blood wave-front layer (v39F): replaces BloodLiquidMath and BloodLiquidSurface in an already built КОНТУР place.

The layer touches only the two ReplicatedStorage modules, so it applies to any build that carries the v38 liquid
(v38, v39, ...). Run it on the normal map and on the QA map separately:

    python sources/blood-front/build_place.py maps/Kontur_Office_v39.rbxl    maps/Kontur_Office_v39F.rbxl
    python sources/blood-front/build_place.py maps/Kontur_Office_v39_QA.rbxl maps/Kontur_Office_v39F_QA.rbxl

To fold the layer into another assembler call `layer(scripts, data, patch)` before `patch.patch_place(...)`.
Needs the venv with zstandard (../venv/bin/python).
"""
import argparse
import importlib.util
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHER = HERE.parent / "ceiling-worker-v24" / "build_place.py"
MODULES = ("BloodLiquidMath", "BloodLiquidSurface")


def load_patcher():
    spec = importlib.util.spec_from_file_location("binary_patch", PATCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stored_texts(data, patch):
    """Every Source string stored in the place (the module text we expect to replace must be among them)."""
    import zstandard
    position = 32
    decoder = zstandard.ZstdDecompressor()
    found = []
    while position < len(data):
        tag, compressed, size, _ = patch.HEADER.unpack_from(data, position)
        start = position + patch.HEADER.size
        end = start + (compressed or size)
        position = end
        if tag != b"PROP":
            continue
        body = decoder.decompress(data[start:end], max_output_size=size) if compressed else data[start:end]
        found.append(body)
    return found


def original_in_place(bodies, text):
    needle = struct.pack("<I", len(text)) + text
    return any(needle in body for body in bodies)


def layer(scripts, data, patch):
    """Add the two module replacements to `scripts` after checking the base still carries the expected originals."""
    bodies = stored_texts(data, patch)
    for name in MODULES:
        original = (HERE / "original" / (name + ".luau")).read_text().encode()
        assert original_in_place(bodies, original), name + " in the base place differs from blood-front/original"
        scripts[("ModuleScript", name)] = (HERE / (name + ".luau")).read_text()
    return scripts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assert args.base.resolve() != args.output.resolve()
    patch = load_patcher()
    data = args.base.read_bytes()
    result = patch.patch_place(data, layer({}, data, patch), None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".partial")
    temporary.write_bytes(result)
    temporary.replace(args.output)
    print("wrote", args.output, len(result))


if __name__ == "__main__":
    main()
