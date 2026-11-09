# Сборка сцены принтера v28

Готовый файл Blender уже содержит нужные материалы и звук. Для пересборки из исходников используй Blender 5.2 и Python с NumPy. На Mac для повторного создания бланков понадобится Pillow и системный Arial. Готовые изображения бланков лежат рядом со скриптом и входят в проект. Геометрия надписей в готовой сцене читается без системного шрифта.

Из корня этого каталога выполни:

```sh
mkdir -p review
python3 build_foley.py review/Printer_Paper_Review.wav
blender -b --python build_study.py -- Room_CENTER.json review
blender -b review/Kontur_Printer_Paper_v28.blend --python verify_study.py -- review
blender -b review/Kontur_Printer_Paper_v28.blend --python check_sheet_overlap.py -- review
blender -b review/Kontur_Printer_Paper_v28.blend --python render_review.py -- review
blender -b review/Kontur_Printer_Paper_v28.blend --python render_video.py -- review
```

`Room_CENTER.json` содержит примитивы центрального офиса и соседних границ. Источник геометрии — локальный файл карты v13 в XML. `extract_center.py` принимает этот файл и путь для JSON. `paper_motion.py` определяет отдельные траектории, время отрыва и сгибы для всех 42 листов. Траектории записаны в кадры Blender, при просмотре выполнение Python не требуется.
