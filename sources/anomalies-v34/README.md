# Сборка КОНТУР v34

Из корня репозитория запусти сборку с Python и zstandard.

    python3 sources/anomalies-v34/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v34.rbxl
    python3 sources/anomalies-v34/build_place.py maps/Kontur_Office_v26_Mirror.rbxl /tmp/Kontur_Office_v34_QA.rbxl --qa

В QA второй уровень по умолчанию показывает принтер. Для другого сценария задай атрибут в серверной командной строке перед ответом у стойки.

    workspace.OfficeMap.AnomalyReportState:SetAttribute("OfficeQANext", "ArchiveWriting")

Другие значения — GreenVent, WhisperDoor, ArchiveArtSwap, ArchiveCalendarShift, WestPlanterColor и Printer.

Одиночный тест запускается из открытой карты QA через studio_verify.py. Передай путь к выходной папке и добавь --walk для отдельного прохода со звуком. Для локального подключения скрипту нужен studio_bridge.py. Для проверки с двумя клиентами открой отдельную копию QA под именем Kontur_Office_v34_Coop_QA.rbxl и передай путь к выходному JSON в coop/run.py. Наблюдатели устанавливаются в тестовую копию.

Для каждой обновлённой сцены открой её вариант v33 в Blender 4.5 LTS. Для Door возьми исходную сцену Vent v33. Аргументы после двух дефисов — имя Printer, Archive, Vent или Door и выходная папка. В макете двери маркеры показывают время начала звуков. Слышимость проверяется в игре.

    blender -b models/anomalies-v33/blender/Kontur_Vent_v33.blend --python-exit-code 1 --python sources/anomalies-v34/refine_studies.py -- Vent /tmp/kontur-v34

[Карты, результаты и сцены](../../models/anomalies-v34/REVIEW.md).
