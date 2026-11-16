# Отчёт по комнате START (Kontur_Office_v42_QA.rbxl, 16.11.2026)

Итог: в список попало 14 предметов (7 разных: Plant_8, WD_AcSplit, WD_LedgeDecor, WD_FireAlarm, WD_FireHorn, WD_CamCorner, 8 полос CoveStrip), осмотрено 14 листов из 14 (по 10 ракурсов), недоступных ракурсов нет. Замечаний высокой и средней серьёзности нет, низких 2.

**Важное ограничение: осмотр неполный.** Навык берёт мебель из `Rooms/<КОМНАТА>`, а у стартовой комнаты папка называется `Rooms/StartRoom` (в `Floors` она START). Поэтому не попали в список 26 основных предметов комнаты: StraightDesk, ErgoChair, KonturStartMonitor, Keyboard, MouseAndMat, Flashlight, Radio, SecurityIncidentJournal, Keys, DeskClocks, ClosedFolders, ClosedPC_Flashlight, PersonalLockers, VisitorBench, FormsCabinet, CoatStand, ReportStation и ReportStation_Anomaly, ShiftStatusBoard, KeyBoard, WallClock, WallCalendar, WallSockets, UtilityBulkhead, ReceptionOfficeSign, RubberPlant_Reception. Их ещё никто не смотрел по 10 ракурсам.

## Находки
| № | Предмет | Категория | Серьёзность | Ракурсы | Что не так | Возможная правка (не выполнялась) |
|---|---|---|---|---|---|---|
| 1 | WD_LedgeDecor | Посадка | низкая | v3, v4 | Полка с кубком висит на уровне кресла/сейфа у восточной стены, глобус стоит у самого края полки | сдвинуть глобус на 0,3 внутрь полки |
| 2 | Plant_8 | Единообразие | низкая | v0–v9 | Старая модель папоротника в горшке отличается от новых растений из Blender (фикус, лилия, монстера) | заменить на PlantFig/PlantLily с коллизией горшка |

«Сквозной: скрыто деталей» на листах это пометка скрипта: камера смотрела через стену, не дефект предмета.

## Предметы без замечаний
WD_AcSplit (форма, индикаторы, лоток дренажа), WD_FireAlarm (новая модель: винты на грани, молоток в скобах, ничего не парит), WD_FireHorn, WD_CamCorner (пластина у шва, объектив к центру комнаты), CoveStrip ×8 (светящиеся полосы по периметру).

## Не проверено
Все 26 основных предметов комнаты (см. выше). Кадры сняты в Studio Play, свет это подсветка у камеры, не игровой. Рядом с каждым предметом в бело-серых кадрах мало окружения, поэтому масштаб оценивался по соседям.
