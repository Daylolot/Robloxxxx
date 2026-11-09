# Сборка КОНТУР v31

База — игровая карта v26. Сборщик повторно использует экспорт 60 листов и серверный принтер v30. Скрипты v31 подключают новые события принтера и локальные эффекты офиса. Для сборки копий Roblox нужен Python с пакетом zstandard.

    python3 sources/anomalies-v31/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v31.rbxl
    python3 sources/anomalies-v31/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v31_QA.rbxl --qa

Тестовая карта показывает принтер на втором уровне. Чтобы выбрать другую аномалию для следующего уровня, в серверной командной строке Studio во время Play задай атрибут. Первый уровень всё равно чистый.

    workspace.OfficeMap.AnomalyReportState:SetAttribute("OfficeQANext", "ArchiveWriting")

Остальные варианты — GreenVent, ArchiveArtSwap, ArchiveCalendarShift, WestPlanterColor и Printer. Затем ответь у стойки, чтобы перейти на следующий уровень. Скрипт studio_verify.py прогоняет всю последовательность через локальный мост Studio MCP.

## Сцены

- printer_study.py открывает Blender v30 и добавляет контакты листов, дугу и демонстрацию складывающегося листа. Позиции и время берутся из PrinterDirection.luau.
- study.py принимает после двух дефисов тип archive, static или vent, номер итерации и выходную папку. Для статичных изменений используй итерацию 5. Сцены используют размеры частей карты из файлов Geometry.json.
- vent_spec.py задаёт размеры люка для Blender и генерирует VentParts.luau для Roblox.
- verify_blender.py проверяет открытый файл Blender по имени типа и сохраняет отчёт JSON.

[Карты, кадры и десять циклов проверки](../../models/anomalies-v31/REVIEW.md).
