# Сборка КОНТУР v32

Сборщик использует оригинальную геометрию v26 и траектории принтера из v30. Для сборки нужны Python и пакет zstandard.

    python3 sources/anomalies-v32/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v32.rbxl
    python3 sources/anomalies-v32/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v32_QA.rbxl --qa

В QA первый уровень чистый, на втором появляется принтер. Для выбора другого сценария задай атрибут в серверной командной строке Studio перед ответом у стойки.

    workspace.OfficeMap.AnomalyReportState:SetAttribute("OfficeQANext", "ArchiveWriting")

Остальные значения — GreenVent, ArchiveArtSwap, ArchiveCalendarShift, WestPlanterColor и Printer.

Для повторной проверки в одиночном Play используй studio_verify.py и локальный мост studio_bridge.py. Для двух игроков открой отдельную копию QA с именем Kontur_Office_v32_Coop_QA.rbxl, затем запусти coop/run.py с путём к будущему отчёту JSON. Скрипт добавляет наблюдателей только в открытую копию. Закрой копию без сохранения наблюдателей.

refine_studies.py открывает сцену v31 и принимает после двух дефисов тип Vent или Static и папку для результата. [Сцены v31](../../models/anomalies-v31/REVIEW.md).
