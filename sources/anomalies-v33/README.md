# Сборка КОНТУР v33

Для сборки нужны Python и zstandard. Запусти команды из корня репозитория.

    python3 sources/anomalies-v33/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v33.rbxl
    python3 sources/anomalies-v33/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v33_QA.rbxl --qa

Тестовая карта показывает принтер на втором уровне. Для других аномалий задай атрибут в серверной командной строке перед ответом у стойки.

    workspace.OfficeMap.AnomalyReportState:SetAttribute("OfficeQANext", "ArchiveWriting")

Остальные значения — GreenVent, ArchiveArtSwap, ArchiveCalendarShift, WestPlanterColor и Printer.

studio_verify.py принимает выходную папку и опциональный флаг --walk для отдельного прогона со звуком. Для доступа к Studio ему нужен локальный studio_bridge.py. Для кооператива открой отдельную копию QA под именем Kontur_Office_v33_Coop_QA.rbxl и запусти coop/run.py с путём для отчёта JSON. Тестовые наблюдатели устанавливаются только в открытую копию.

Пример пересборки Blender 4.5 LTS для люка. Для Static также используй файл v32, для Archive и Printer используй файлы v31.

    blender -b models/anomalies-v32/blender/Kontur_Vent_v32.blend --python sources/anomalies-v33/refine_studies.py -- Vent /tmp/kontur-v33

Для геометрической проверки запусти следующую команду.

    blender -b --python-exit-code 1 --python sources/anomalies-v33/audit_paper.py -- sources/printer-v28/Room_CENTER.json sources/printer-v30/PrinterFlightData.luau sources/anomalies-v33/PrinterDirection.luau /tmp/kontur-clearance.json

[Карты, сцены и проверки](../../models/anomalies-v33/REVIEW.md).
