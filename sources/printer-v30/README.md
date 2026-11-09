# Сборка принтера v30

Сборщик v29 принимает серверный и клиентский скрипты v30, а также экспорт 60 траекторий из Blender v30. Для сборки из корня репозитория нужны Python и `zstandard`.

```sh
python3 sources/printer-v29/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v30_Printer.rbxl \
  --client sources/printer-v30/PrinterPaper.client.luau --round sources/printer-v30/PrinterRound.luau \
  --flight sources/printer-v30/PrinterFlightData.luau
python3 sources/printer-v29/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v30_Printer_QA.rbxl \
  --client sources/printer-v30/PrinterPaper.client.luau --round sources/printer-v30/PrinterRound.luau \
  --flight sources/printer-v30/PrinterFlightData.luau --qa
```

Сцену Blender можно пересобрать скриптом `build_study.py`. Первый аргумент после `--` — `sources/printer-v28/Room_CENTER.json`, второй — папка результата. Для звуковой дорожки скопируй в папку результата `models/printer-v30/Printer_Paper_Review.wav`. `verify_study.py` и `check_sheet_overlap.py` принимают папку результата после `--`. `export_flight.py` принимает путь для нового `PrinterFlightData.luau`.

`studio_verify.py` использует локальный мост `studio_bridge.py` для Studio MCP. В отдельную папку он сохраняет кадры и `Studio_Check.json`. Ручная проверка описана в [обзоре](../../models/printer-v30/REVIEW.md).
