# Сборка принтера v29

В исходнике `PrinterFlightData.luau` сохранены 164 отсчёта для каждого из 42 листов. Скрипт `export_flight.py` читает готовую сцену Blender v28 и переводит координаты в studs. Игровые скрипты используют общий серверный отсчёт. Четыре плоские секции передают форму листа средствами Roblox.

Из корня репозитория можно пересобрать карты с Python и пакетом zstandard:

```sh
python3 sources/printer-v29/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v29_Printer.rbxl
python3 sources/printer-v29/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v29_Printer_QA.rbxl --qa
```

Тестовая карта выбирает принтер на втором уровне. `studio_verify.py` использует локальный Studio MCP и установленный в рабочем каталоге мост `studio_bridge.py`. Инструкция для ручного теста есть в [обзоре](../../models/printer-v29/REVIEW.md).

Для кооперативного теста скопируй тестовую карту под именем `Kontur_Printer_Coop_QA.rbxl` и открой копию в Studio. Запусти `coop/run.py`, передав путь к будущему JSON с результатами и добавив каталог с `studio_bridge.py` в `PYTHONPATH`. Скрипт устанавливает наблюдателей в открытой копии. После получения отчёта закрой тестовую копию без сохранения наблюдателей.
