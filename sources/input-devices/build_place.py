"""Слой «клавиатура и мышь» (v42I): клавиатуры и мыши с ковриками из Blender (уровень 5) поверх готовой карты КОНТУР.

Слой правит один скрипт карты (Script OfficeReportService, в него собраны все attach-функции):
  1. в таблице ассетов OfficeFurnitureUpgrade заменяет id клавиатуры на новый (старая подмена клавиатур работает как раньше, масштабируя меш
     под размер Body; имена мешей Keyboard_<материал>_<цвет> совпадают с её загрузчиком);
  2. вставляет attachMouseUpgrade (OfficeInputUpgrade.luau) и запускает его рядом с подменой мебели.
Идентификаторы берутся из sources/input-devices/blender/uploaded_assets.json (их пишет tools/upload_assets.py).

    python sources/input-devices/build_place.py maps/Kontur_Office_v42.rbxl    maps/Kontur_Office_v42I.rbxl
    python sources/input-devices/build_place.py maps/Kontur_Office_v42_QA.rbxl maps/Kontur_Office_v42I_QA.rbxl

Нужен venv с zstandard (../venv/bin/python). Базовая карта не меняется."""
import argparse, importlib.util, json, re, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHER = HERE.parent / "ceiling-worker-v24" / "build_place.py"
TARGET = ("Script", "OfficeReportService")
OLD_KEYBOARD = re.compile(r"Keyboard = 140494672316136(?=[,}])")
LOOK_OLD = "leather = Enum.Material.Leather,"          # таблица материалов загрузчика мебели: добавляем светодиоды клавиатуры (Neon)
ANCHOR = "local function attachFurnitureUpgrade(office: Instance?)"
SPAWN = 'task.spawn(function() local furnOk,furnErr=pcall(attachFurnitureUpgrade,office) if not furnOk then warn("KONTUR furniture upgrade failed: "..tostring(furnErr)) end end)\n'
MOUSE_SPAWN = '    task.spawn(function() local mouseOk,mouseErr=pcall(attachMouseUpgrade,office) if not mouseOk then warn("KONTUR mouse upgrade failed: "..tostring(mouseErr)) end end)\n'


def load_patcher():
    spec = importlib.util.spec_from_file_location("binary_patch", PATCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_sources(data, patch):
    """{(класс, имя): Source} для всех скриптов карты."""
    import zstandard
    position = 32
    classes, names, sources = {}, {}, {}
    while position < len(data):
        tag, compressed, size, _ = patch.HEADER.unpack_from(data, position)
        start = position + patch.HEADER.size
        end = start + (compressed or size)
        packed = data[start:end]
        position = end
        if tag not in (b"INST", b"PROP"):
            continue
        body = zstandard.ZstdDecompressor().decompress(packed, max_output_size=size) if compressed else packed
        class_id = struct.unpack_from("<I", body)[0]
        label, offset = patch.read_string(body, 4)
        if tag == b"INST":
            classes[class_id] = (label, struct.unpack_from("<I", body, offset + 1)[0])
            continue
        class_name, count = classes[class_id]
        if class_name in patch.SCRIPT_CLASSES and label in ("Name", "Source"):
            offset += 1
            values = []
            for _ in range(count):
                value, offset = patch.read_string(body, offset)
                values.append(value)
            (names if label == "Name" else sources)[class_id] = values
    out = {}
    for class_id, values in sources.items():
        for name, value in zip(names[class_id], values):
            out[(classes[class_id][0], name)] = value
    return out


def layer(scripts, data, patch):
    """Добавляет в `scripts` исправленный Source скрипта OfficeReportService. Все якоря проверяются: слой ломается громко, а не портит скрипт молча."""
    registry = json.loads((HERE / "blender" / "uploaded_assets.json").read_text())
    keyboard_id, mouse_id = str(registry["Keyboard"]["assetId"]), str(registry["MouseSetV2"]["assetId"])
    if not (keyboard_id.isdigit() and mouse_id.isdigit()):
        raise SystemExit("в uploaded_assets.json нет числовых id ассетов: сначала tools/upload_assets.py")
    text = read_sources(data, patch)[TARGET]
    for what, count in (("старый id клавиатуры", len(OLD_KEYBOARD.findall(text))), ("attachFurnitureUpgrade", text.count(ANCHOR)),
                        ("запуск подмены мебели", text.count(SPAWN)), ("таблица материалов мебели", text.count(LOOK_OLD))):
        if count != 1:
            raise SystemExit(f"{what}: ожидалось одно вхождение, найдено {count} (база не v42?)")
    raw = (HERE / "OfficeInputUpgrade.luau").read_text()
    if raw.count("\t-- @@INPUT_ASSETS@@\n") != 1:
        raise SystemExit("в OfficeInputUpgrade.luau нет метки @@INPUT_ASSETS@@")
    function = raw.replace("--!strict\n", "", 1).replace("\t-- @@INPUT_ASSETS@@\n", f"\tASSETS = {{MouseSetV2 = {mouse_id}}}\n")
    if "@@" in function:
        raise SystemExit("остались метки @@ в тексте функции")
    text = OLD_KEYBOARD.sub(f"Keyboard = {keyboard_id}", text)
    text = text.replace(LOOK_OLD, "led = Enum.Material.Neon, " + LOOK_OLD)
    text = text.replace(ANCHOR, function + ANCHOR)
    text = text.replace(SPAWN, SPAWN + MOUSE_SPAWN)
    scripts[TARGET] = text
    return scripts, keyboard_id


def verify(result, keyboard_id, patch):
    """Перечитываем собранную карту: функция и запуск по одному разу, id клавиатуры новый, метки убраны."""
    text = read_sources(bytes(result), patch)[TARGET]
    checks = {"определение attachMouseUpgrade": text.count("local function attachMouseUpgrade("), "запуск мыши": text.count("pcall(attachMouseUpgrade,office)"),
              "новый id клавиатуры": text.count(f"Keyboard = {keyboard_id}"), "старый id клавиатуры": text.count("140494672316136"), "метки @@": text.count("@@INPUT_ASSETS@@")}
    expected = {"определение attachMouseUpgrade": 1, "запуск мыши": 1, "новый id клавиатуры": 1, "старый id клавиатуры": 0, "метки @@": 0}
    for key, want in expected.items():
        if checks[key] != want:
            raise SystemExit(f"проверка собранной карты: {key} = {checks[key]}, ожидалось {want}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assert args.base.resolve() != args.output.resolve()
    patch = load_patcher()
    data = args.base.read_bytes()
    scripts, keyboard_id = layer({}, data, patch)
    result = patch.patch_place(data, scripts, None)
    verify(result, keyboard_id, patch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = args.output.with_name(args.output.name + ".partial")
    partial.write_bytes(result)
    partial.replace(args.output)
    print("готово:", args.output, len(result), "байт")


if __name__ == "__main__":
    main()
