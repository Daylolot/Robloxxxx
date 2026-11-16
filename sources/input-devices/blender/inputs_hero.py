"""КОНТУР: клавиатура и мышь с ковриком, Blender, уровень 5 (замена упрощённых моделей рабочих мест).
Запуск: Blender -b --python inputs_hero.py -- <out_dir> [keyboard,mouseset] [--norender]
Помощники (Group/Item/box/cyl/lathe/finish/export/render_views) берутся из sources/evolution-v39/blender/interior_hero.py (exec), tube из hub_hero.py.
Единицы: 1 единица Blender = 1 stud, Z вверх, перёд предмета смотрит в -Y, начало координат = центр габарита (как у старого Keyboard).
Цвет и материал уходят в имя меша: <Предмет>_<материал>_<hex>, сервер ставит MeshPart.Color и Material."""
import sys, math, random
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

_ev = Path(__file__).resolve().parents[2] / "evolution-v39" / "blender"
_src = (_ev / "interior_hero.py").read_text()
exec(compile(_src[:_src.index("# ---------------------------------------------------------------- items")], "interior_hero_head", "exec"), globals())
exec(compile(_src[_src.index("import struct, base64"):_src.index("def main():")], "interior_hero_tail", "exec"), globals())
_hub = (_ev / "hub_hero.py").read_text()
exec(compile(_hub[_hub.index("MATS.update({"):_hub.index("def hazmat():")], "hub_helpers", "exec"), globals())

MATS.update({
    "casebody": ("#8b978e", .5, 0, 0, 0),
    "bezel": ("#a6b3a7", .46, 0, 0, 0),
    "plate": ("#6f7b74", .55, 0, 0, 0),
    "keycap": ("#d9dcc8", .42, 0, 0, 0),
    "keymod": ("#bfc5b3", .42, 0, 0, 0),
    "legend": ("#2b332f", .5, 0, 0, 0),
    "foot": ("#262a28", .85, 0, 0, 0),
    "cable": ("#2e3431", .7, 0, 0, 0),
    "led": ("#7fe0a0", .3, 0, 1.0, 0),
})

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
_font = None


def font():
    global _font
    if _font is None:
        _font = bpy.data.fonts.load(FONT_PATH)
    return _font


def glyph_bm(text, size, depth=0.0016):
    """Текст -> bmesh, лежит в плоскости XY, центрирован, низ на z=0, выдавлен вверх на depth."""
    cu = bpy.data.curves.new("t", "FONT")
    cu.body = text
    cu.font = font()
    cu.size = size
    cu.extrude = depth / 2
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.resolution_u = 1
    ob = bpy.data.objects.new("t", cu)
    bpy.context.scene.collection.objects.link(ob)
    deps = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(deps)
    me = bpy.data.meshes.new_from_object(ev, depsgraph=deps)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    zmin = min(v.co.z for v in bm.verts) if bm.verts else 0.0
    for v in bm.verts:
        v.co.z -= zmin
    # нижние грани не видны (лежат на колпачке): убираем, это треть треугольников надписей
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.5], context="FACES")
    # плоские торцы текста не нужны: оставляем всё, на лишние треугольники строгий лимит есть только у меша целиком
    return bm


def keycap_bm(w, d, h, slope_deg=0.0, dish=0.0, taper=0.1):
    """Колпачок клавиши как поле высот над прямоугольником w x d: вертикальные стенки, скруглённая верхняя кромка, вогнутая площадка.
    Низ открыт (закрыт корпусом). Начало: центр основания, z=0 внизу."""
    us = [-1.0, -0.93, -0.55, 0.0, 0.55, 0.93, 1.0]
    vs = [-1.0, -0.92, -0.5, 0.0, 0.5, 0.92, 1.0]
    tan = math.tan(math.radians(slope_deg))
    bm = bmesh.new()
    grid = []
    for iv, v in enumerate(vs):
        row = []
        for iu, u in enumerate(us):
            edge = max(abs(u), abs(v)) >= 0.999
            top = h + v * (d / 2) * tan - dish * (1.0 - 0.5 * (u * u + v * v))
            if edge:
                z = 0.0
                x, y = u * w / 2, v * d / 2
                if abs(u) >= 0.999 and abs(v) >= 0.999:           # угол основания чуть срезан
                    x *= 0.93
                    y *= 0.9
            else:
                ring = max(abs(u), abs(v)) >= 0.9
                z = top * (0.9 if ring else 1.0)
                k = 1.0 - taper if ring else 1.0 - taper * 0.7
                x, y = u * w / 2 * k, v * d / 2 * k
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for iv in range(len(vs) - 1):
        for iu in range(len(us) - 1):
            bm.faces.new((grid[iv][iu], grid[iv][iu + 1], grid[iv + 1][iu + 1], grid[iv + 1][iu]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm, (h - dish)


# ---------------------------------------------------------------- клавиатура
# ряд: (метка, кириллица или "", ширина в u, группа цвета)
def _row(items):
    return items


def keyboard_layout():
    """Полноразмерная раскладка на 104 клавиши в единицах u (ширина 22.5u). Возвращает [(x_left_u, row, w_u, h_rows, latin, cyr, kind)]."""
    keys = []

    def add(x, row, w, latin, cyr="", kind="key", rows=1):
        keys.append((x, row, w, rows, latin, cyr, kind))
    # ряд 0: функциональные
    add(0, 0, 1, "Esc", "", "mod")
    x = 2.0
    for blk in range(3):
        for k in range(4):
            add(x, 0, 1, f"F{blk * 4 + k + 1}", "", "mod")
            x += 1
        x += 0.5 if blk < 2 else 0
    add(15.25, 0, 1, "PrtSc", "", "mod"); add(16.25, 0, 1, "Scr", "", "mod"); add(17.25, 0, 1, "Pause", "", "mod")
    # ряд 1: цифры
    nums = [("`", "Ё"), ("1", ""), ("2", ""), ("3", ""), ("4", ""), ("5", ""), ("6", ""), ("7", ""), ("8", ""), ("9", ""), ("0", ""), ("-", ""), ("=", "")]
    x = 0.0
    for l, c in nums:
        add(x, 1, 1, l, c); x += 1
    add(x, 1, 2.0, "<-", "", "mod")
    # ряд 2
    add(0, 2, 1.5, "Tab", "", "mod")
    q = [("Q", "Й"), ("W", "Ц"), ("E", "У"), ("R", "К"), ("T", "Е"), ("Y", "Н"), ("U", "Г"), ("I", "Ш"), ("O", "Щ"), ("P", "З"), ("[", "Х"), ("]", "Ъ")]
    x = 1.5
    for l, c in q:
        add(x, 2, 1, l, c); x += 1
    add(x, 2, 1.5, "\\", "")
    # ряд 3
    add(0, 3, 1.75, "Caps", "", "mod")
    a = [("A", "Ф"), ("S", "Ы"), ("D", "В"), ("F", "А"), ("G", "П"), ("H", "Р"), ("J", "О"), ("K", "Л"), ("L", "Д"), (";", "Ж"), ("'", "Э")]
    x = 1.75
    for l, c in a:
        add(x, 3, 1, l, c); x += 1
    add(x, 3, 2.25, "Enter", "", "mod")
    # ряд 4
    add(0, 4, 2.25, "Shift", "", "mod")
    z = [("Z", "Я"), ("X", "Ч"), ("C", "С"), ("V", "М"), ("B", "И"), ("N", "Т"), ("M", "Ь"), (",", "Б"), (".", "Ю"), ("/", ".")]
    x = 2.25
    for l, c in z:
        add(x, 4, 1, l, c); x += 1
    add(x, 4, 2.75, "Shift", "", "mod")
    # ряд 5
    add(0, 5, 1.25, "Ctrl", "", "mod"); add(1.25, 5, 1.25, "Win", "", "mod"); add(2.5, 5, 1.25, "Alt", "", "mod")
    add(3.75, 5, 6.25, "", "", "key")
    add(10.0, 5, 1.25, "Alt", "", "mod"); add(11.25, 5, 1.25, "Win", "", "mod"); add(12.5, 5, 1.25, "Menu", "", "mod"); add(13.75, 5, 1.25, "Ctrl", "", "mod")
    # навигация
    for i, t in enumerate(("Ins", "Home", "PgUp")):
        add(15.25 + i, 1, 1, t, "", "mod")
    for i, t in enumerate(("Del", "End", "PgDn")):
        add(15.25 + i, 2, 1, t, "", "mod")
    add(16.25, 4, 1, "^", "", "mod")
    for i, t in enumerate(("<", "v", ">")):
        add(15.25 + i, 5, 1, t, "", "mod")
    # цифровой блок
    for i, t in enumerate(("Num", "/", "*", "-")):
        add(18.5 + i, 1, 1, t, "", "mod")
    for i, t in enumerate(("7", "8", "9")):
        add(18.5 + i, 2, 1, t, "")
    add(21.5, 2, 1, "+", "", "mod", rows=2)
    for i, t in enumerate(("4", "5", "6")):
        add(18.5 + i, 3, 1, t, "")
    for i, t in enumerate(("1", "2", "3")):
        add(18.5 + i, 4, 1, t, "")
    add(21.5, 4, 1, "Ent", "", "mod", rows=2)
    add(18.5, 5, 2.0, "0", ""); add(20.5, 5, 1, ".", "")
    return keys


SHIFTED = {"1": "!", "2": "@", "3": "#", "4": "$", "5": "%", "6": "^", "7": "&", "8": "*", "9": "(", "0": ")", "-": "_", "=": "+", "\\": "|"}
ROW_H = [0.024, 0.029, 0.032, 0.032, 0.030, 0.027]       # высота колпачков по рядам (скульптурный профиль)
ROW_SLOPE = [0.0, 7.0, 3.0, 0.0, -3.0, -6.0]
TILT_DEG = 4.0
UKEY = 0.0715                                              # шаг клавиши 1u
KW, KD, KH = 1.87, 0.58, 0.13                              # габарит старой модели: ширина, глубина, высота


def keyboard():
    it = Item("Keyboard")
    u = UKEY
    plate_top = -0.002
    x0 = -22.5 * u / 2
    # положение рядов по оси Y (ряд 0 дальше от игрока, это +Y)
    y_top = 0.2335
    def row_y(r, rows=1):
        off = 0.0 if r == 0 else 1.32 + (r - 1)
        return y_top - (off + rows / 2) * u
    # ---- корпус: нижняя оболочка, рамка, пластина, ножки
    box(it, "casebody", (1.87, 0.58, 0.04), (0, 0, -0.066), bevel=0.03, seg=3)
    box(it, "casebody", (1.79, 0.50, 0.012), (0, 0, -0.03), bevel=0.012, seg=2, color="#7b877f")          # пояс под рамкой
    fw = 0.058
    box(it, "bezel", (fw, 0.58, 0.026), (-(1.87 - fw) / 2, 0, -0.024), bevel=0.012, seg=3)
    box(it, "bezel", (fw, 0.58, 0.026), ((1.87 - fw) / 2, 0, -0.024), bevel=0.012, seg=3)
    box(it, "bezel", (1.87 - 2 * fw + 0.02, 0.052, 0.026), (0, -0.264, -0.024), bevel=0.012, seg=3)
    box(it, "bezel", (1.87 - 2 * fw + 0.02, 0.04, 0.03), (0, 0.27, -0.024), bevel=0.012, seg=3)
    box(it, "plate", (1.87 - 2 * fw, 0.488, 0.02), (0, 0.004, -0.0225 - 0.0), bevel=0.003, seg=1)         # пластина, на ней колпачки
    # ---- колпачки и надписи
    keys = keyboard_layout()
    for (xl, row, w, rows, latin, cyr, kind) in keys:
        cx = x0 + (xl + w / 2) * u
        cy = row_y(row, rows)
        kw = w * u * 0.93
        kd = rows * u * 0.93 - (0.0 if rows == 1 else 0.0)
        h = ROW_H[row] if rows == 1 else ROW_H[row]
        slope = ROW_SLOPE[row]
        dish = 0.0035 if (kind == "key" and w <= 1.0 and latin) else 0.0025
        color = "#d9dcc8" if kind == "key" else "#bfc5b3"
        mat = "keycap" if kind == "key" else "keymod"
        bm, top_h = keycap_bm(kw, kd, h, slope, dish)
        it.put(bm, mat, color, T(cx, cy, plate_top))
        # надписи: латиница сверху слева, кириллица снизу справа; отдельные слова и стрелки по центру
        zt = plate_top + top_h + 0.0003
        rot = Rx(math.radians(slope))
        if latin in ("F", "J") and cyr:
            box(it, "keycap", (0.022, 0.0045, 0.0028), (cx, cy - 0.0235, zt - 0.0006), bevel=0.0012, seg=1, color="#d9dcc8", rot=rot)    # тактильные метки
        if latin:
            single = len(latin) == 1
            if cyr:
                g = glyph_bm(latin, 0.021)
                it.put(g, "legend", None, T(cx - 0.016, cy + 0.011, zt) @ rot)
                g = glyph_bm(cyr, 0.016)
                it.put(g, "legend", None, T(cx + 0.017, cy - 0.011, zt) @ rot)
            elif latin in SHIFTED:
                g = glyph_bm(SHIFTED[latin], 0.0185)
                it.put(g, "legend", None, T(cx, cy + 0.0155, zt) @ rot)
                g = glyph_bm(latin, 0.0215)
                it.put(g, "legend", None, T(cx, cy - 0.0105, zt) @ rot)
            else:
                size = 0.026 if single else (0.0185 if len(latin) <= 3 else 0.0155)
                glyph = {"<-": "←", "^": "▲", "v": "▼", "<": "◄", ">": "►"}.get(latin, latin)
                if kind == "mod" and len(glyph) >= 3 and w < 1.3:
                    size = 0.0155
                g = glyph_bm(glyph, size)
                it.put(g, "legend", None, T(cx, cy, zt) @ rot)
    # ---- индикаторы NumLock/Caps/Scroll справа вверху на рамке, значок «КОНТУР» на переднем борту
    for k in range(3):
        box(it, "led", (0.02, 0.007, 0.0035), (0.70 + k * 0.058, 0.272, 0.0052), bevel=0.0015, seg=2)
    g = glyph_bm("КОНТУР", 0.0175, 0.0012)
    it.put(g, "legend", None, T(0.0, -0.2902, -0.0105) @ Rx(math.radians(90)))
    # ---- ножки: 4 резиновые, задние выше (наклон), откидные ножки сзади
    for sx in (-1, 1):
        box(it, "foot", (0.16, 0.06, 0.012), (sx * 0.75, -0.23, -0.078), bevel=0.004, seg=2)
        box(it, "foot", (0.16, 0.06, 0.03), (sx * 0.75, 0.23, -0.096), bevel=0.004, seg=2)
        box(it, "foot", (0.1, 0.02, 0.02), (sx * 0.5, 0.265, -0.084), bevel=0.005, seg=2, color="#3a403d")   # шарнир ножки
    # ---- узел разгрузки кабеля сзади по центру (сам провод строится после наклона, в системе стола)
    box(it, "cable", (0.07, 0.05, 0.034), (0, 0.3, -0.058), bevel=0.012, seg=3)
    # ---- наклон всей клавиатуры: поворот вокруг передней нижней кромки, затем привязка ножек к плоскости стола
    th = math.radians(TILT_DEG)
    pivot = Vector((0.0, -0.29, -0.078))
    M = T(*pivot) @ Rx(th) @ T(*(-pivot))
    for grp in it.groups.values():
        bmesh.ops.transform(grp.bm, matrix=M, verts=grp.bm.verts)
    # задние ножки доводим до плоскости стола z = -0.065 (низ габарита), всё смещаем вниз на разницу
    zmin = min(v.co.z for grp in it.groups.values() if grp.mat == "foot" for v in grp.bm.verts)
    shift = -KH / 2 - zmin
    for grp in it.groups.values():
        bmesh.ops.transform(grp.bm, matrix=T(0, 0, shift), verts=grp.bm.verts)
    # ---- провод: от узла разгрузки назад, ложится на стол, плавный изгиб в сторону и уход в столешницу
    p0 = (T(0, 0, shift) @ M) @ Vector((0, 0.335, -0.056))
    desk_z, r = -KH / 2, 0.0125
    pts, radii = [], []
    n = 26
    for i in range(n + 1):
        t = i / n
        ss = min(1.0, t / 0.3)
        ss = ss * ss * (3 - 2 * ss)
        sx_ = min(1.0, t / 0.45)
        sx_ = sx_ * sx_ * (3 - 2 * sx_)
        y = p0.y + 0.78 * t
        x = p0.x + 0.72 * sx_                                   # уходит вправо, мимо подставки монитора (она шире не заходит за x=+-0.54)
        z = p0.z + (desk_z + r - p0.z) * ss
        if t > 0.86:
            z -= (t - 0.86) / 0.14 * 0.045            # конец уходит под поверхность стола
        pts.append((x, y, z)); radii.append(r)
    tube(it, "cable", pts, radii, 10, "#2e3431")
    return it


# ---------------------------------------------------------------- мышь с ковриком
MATS.update({
    "mat_fabric": ("#526863", .95, 0, 0, 0),
    "mat_edge": ("#3f524d", .9, 0, 0, 0),
    "mat_rubber": ("#1e2220", .9, 0, 0, 0),
    "mat_label": ("#8ea39b", .8, 0, 0, 0),
    "mouse_shell": ("#c3cbbb", .42, 0, 0, 0),
    "mouse_button": ("#cdd4c6", .4, 0, 0, 0),
    "mouse_grip": ("#6c7a73", .8, 0, 0, 0),
    "mouse_wheel": ("#2b312e", .75, 0, 0, 0),
    "mouse_led": ("#7fe0a0", .3, 0, 1.0, 0),
    "ptfe": ("#e9ebe4", .3, 0, 0, 0),
})


def lerp_table(tab, t):
    """Гладкая (кубический Эрмит с конечными разностями) интерполяция таблицы [(t, v)]: без изломов наклона в узлах."""
    n = len(tab)
    if t <= tab[0][0]:
        return tab[0][1]
    if t >= tab[-1][0]:
        return tab[-1][1]
    i = 0
    while t > tab[i + 1][0]:
        i += 1
    t0, v0 = tab[i]
    t1, v1 = tab[i + 1]

    def slope(k):
        a, b = max(k - 1, 0), min(k + 1, n - 1)
        return (tab[b][1] - tab[a][1]) / (tab[b][0] - tab[a][0])
    m0, m1 = slope(i) * (t1 - t0), slope(i + 1) * (t1 - t0)
    k = (t - t0) / (t1 - t0)
    return ((2 * k ** 3 - 3 * k ** 2 + 1) * v0 + (k ** 3 - 2 * k ** 2 + k) * m0 + (-2 * k ** 3 + 3 * k ** 2) * v1 + (k ** 3 - k ** 2) * m1)


MOUSE_L, MOUSE_W, MOUSE_H = 0.44, 0.27, 0.128
HW_TAB = [(0.0, 0.66), (0.10, 0.88), (0.28, 1.0), (0.5, 0.98), (0.78, 0.86), (1.0, 0.64)]     # полуширина по длине (доля от W/2)
H_TAB = [(0.0, 0.46), (0.12, 0.80), (0.30, 1.0), (0.52, 0.90), (0.78, 0.70), (1.0, 0.50)]      # высота купола по длине (доля от H)
TS = [0.0, 0.006, 0.02, 0.04, 0.07, 0.11, 0.16, 0.22, 0.29, 0.36, 0.43, 0.48, 0.488, 0.503, 0.512, 0.545, 0.595, 0.65, 0.71, 0.77, 0.83, 0.88, 0.925, 0.96, 0.985, 0.996, 1.0]
SS_HALF = [0.0, 0.012, 0.04, 0.075, 0.18, 0.33, 0.48, 0.62, 0.74, 0.83, 0.9, 0.95, 0.98, 0.995, 1.0]
SS = [-x for x in reversed(SS_HALF[1:])] + SS_HALF[:1] + SS_HALF[1:]
SS = sorted(set([-1.0, -0.995, -0.98, -0.95, -0.9, -0.83, -0.74, -0.62, -0.48, -0.33, -0.18, -0.075, -0.04, -0.012, 0.012, 0.04, 0.075, 0.18, 0.33, 0.48, 0.62, 0.74, 0.83, 0.9, 0.95, 0.98, 0.995, 1.0]))


def mouse_point(t, s_, base_z=0.004, out=0.0):
    """Точка поверхности мыши: (x, y, z) в системе коврика-мыши до сдвига по высоте; out - вынос наружу вдоль нормали плана."""
    hw = MOUSE_W / 2 * lerp_table(HW_TAB, t)
    e = abs(2 * t - 1)
    end = max(0.0, 1.0 - e ** 3.2) ** (1 / 3.2)
    ext = max(0.0, 1.0 - e ** 9) ** 0.35
    h = MOUSE_H * lerp_table(H_TAB, t)
    z = base_z + h * max(0.0, 1.0 - s_ * s_) ** 0.4 * ext
    # вогнутая площадка под пальцы на кнопках
    if t > 0.52:
        z -= 0.0065 * math.sin(min(1.0, (t - 0.52) / 0.45) * math.pi) * (1.0 - s_ * s_) * 0.9
    x = s_ * (hw * end) + math.copysign(out, s_) if s_ != 0 else 0.0
    return x, (t - 0.5) * MOUSE_L, z


def orient(bm, want):
    """Открытая сетка: разворачиваем грани так, чтобы суммарная нормаль смотрела в сторону want (Roblox отсекает обратные грани)."""
    total = Vector((0, 0, 0))
    for f in bm.faces:
        total += f.normal * f.calc_area()
    if total.dot(Vector(want)) < 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.verts.index_update()                                       # Group.add сопоставляет вершины по index


def mouse_surface(it, mat, color, lift, groove=None):
    bm = bmesh.new()
    grid = []
    for t in TS:
        row = []
        for s_ in SS:
            x, y, z = mouse_point(t, s_)
            if groove:
                z -= groove(t, s_)
            row.append(bm.verts.new((x, y, z + lift)))
        grid.append(row)
    for i in range(len(TS) - 1):
        for j in range(len(SS) - 1):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bm.normal_update()
    orient(bm, (0, 0, 1))
    it.put(bm, mat, color)


def mouseset():
    it = Item("MouseSetV2")
    mat_w, mat_d, mat_t = 0.551, 0.72, 0.021
    mat_z0 = -0.0875
    # ---- коврик: резиновое основание, тканевая верхняя часть с обмётанным краем и строчкой, значок
    box(it, "mat_rubber", (mat_w, mat_d, 0.007), (0, 0, mat_z0), bevel=0.003, seg=2, color="#1e2220")
    box(it, "mat_fabric", (mat_w - 0.004, mat_d - 0.004, 0.014), (0, 0, mat_z0 + 0.007), bevel=0.006, seg=3, color="#526863")
    ew = 0.011
    z_e = mat_z0 + 0.0125
    for sx in (-1, 1):
        box(it, "mat_edge", (ew, mat_d - 0.004, 0.0085), (sx * (mat_w / 2 - ew / 2 - 0.002), 0, z_e), bevel=0.0035, seg=2)
    for sy in (-1, 1):
        box(it, "mat_edge", (mat_w - 0.004, ew, 0.0085), (0, sy * (mat_d / 2 - ew / 2 - 0.002), z_e), bevel=0.0035, seg=2)
    for sx in (-1, 1):
        box(it, "mat_label", (0.0018, mat_d - 0.05, 0.0006), (sx * (mat_w / 2 - ew - 0.006), 0, mat_z0 + 0.0215), color="#7f958d")
    for sy in (-1, 1):
        box(it, "mat_label", (mat_w - 0.05, 0.0018, 0.0006), (0, sy * (mat_d / 2 - ew - 0.006), mat_z0 + 0.0215), color="#7f958d")
    g = glyph_bm("КОНТУР", 0.021, 0.0008)
    it.put(g, "mat_label", "#9fb3ab", T(0.14, -0.31, mat_z0 + 0.0212))
    box(it, "mat_label", (0.05, 0.004, 0.0007), (0.145, -0.335, mat_z0 + 0.0212), color="#9fb3ab")
    # ---- мышь
    top = mat_z0 + mat_t                                          # верх коврика, на нём ножки

    def groove(t, s_):
        d = 0.0
        if t > 0.515 and abs(s_) < 0.045:
            d = 0.009                                              # продольная щель между кнопками (ширина ~0.012)
        if 0.486 <= t <= 0.512:
            d = max(d, 0.0075)                                     # поперечная щель между кнопками и корпусом
        return d
    mouse_surface(it, "mouse_shell", "#c3cbbb", top, groove)
    # боковые накладки-грипы с рёбрами: поверхность чуть снаружи, ряды чередуют вынос (рёбра)
    for sg in (-1, 1):
        t_list = [0.20 + k * 0.025 for k in range(19)]             # 0.20..0.65
        s_list = [0.80, 0.86, 0.91, 0.95, 0.975]
        bm = bmesh.new(); grid = []
        for k, t in enumerate(t_list):
            row = []
            for s_ in s_list:
                x, y, z = mouse_point(t, sg * s_, out=0.0005 + (0.0009 if k % 2 == 0 else 0.0))
                row.append(bm.verts.new((x, y, z + top)))
            grid.append(row)
        for i in range(len(t_list) - 1):
            for j in range(len(s_list) - 1):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                bm.faces.new(f if sg < 0 else f[::-1])
        bm.normal_update()
        orient(bm, (sg, 0, 0.3))
        it.put(bm, "mouse_grip", "#6c7a73")
    # колесо
    t_w = 0.64
    xw, yw, zs = mouse_point(t_w, 0.0)
    zw = zs + top
    rw = 0.034
    cyl(it, "mouse_wheel", rw, 0.03, (-0.015, yw, zw - rw + 0.0065), seg=24, color="#2b312e", rot=Ry(math.pi / 2), bevel=0.004)
    for k in range(18):
        a = k / 18 * math.tau
        box(it, "mouse_wheel", (0.03, 0.0065, 0.0055), (0.0, yw + math.cos(a) * (rw + 0.0004), zw - rw + 0.0065 + math.sin(a) * (rw + 0.0004)), bevel=0.0012, seg=1, color="#1e2321", rot=Rx(a))
    # боковые кнопки «назад/вперёд» на левом борту (поверхность выше накладки)
    for t in (0.57, 0.67):
        x, y, z = mouse_point(t, -0.9, out=0.0015)
        box(it, "mouse_button", (0.0055, 0.056, 0.019), (x - 0.0015, y, z + top - 0.0095 - 0.012), bevel=0.003, seg=2, color="#cdd4c6")
    # светодиод DPI за колесом и логотип на спинке
    x, y, z = mouse_point(0.54, 0.0)
    box(it, "mouse_led", (0.014, 0.011, 0.003), (0.0, y, z + top - 0.003), bevel=0.0012, seg=2)
    # ножки скольжения: четыре пластины PTFE внутри габарита
    for sx, sy, fy in ((-1, -1, -0.125), (1, -1, -0.125), (-1, 1, 0.115), (1, 1, 0.115)):
        box(it, "ptfe", (0.04, 0.06, 0.004), (sx * 0.055, fy, top), bevel=0.0015, seg=1, color="#e9ebe4")
    # ---- кабель: узел у носа, S-кривая вперёд по коврику, плавный сход с края коврика на стол, уход в столешницу
    x, y, z = mouse_point(1.0, 0.0)
    zc = z + top - 0.0 + 0.045
    box(it, "cable", (0.03, 0.04, 0.026), (0, y - 0.004, top + 0.004 + 0.012), bevel=0.01, seg=3)
    pts, radii = [], []
    n = 30
    y0 = y + 0.012
    y_end = mat_d / 2 + 0.28
    for i in range(n + 1):
        t = i / n
        yy = y0 + (y_end - y0) * t
        xx = 0.05 * math.sin(t * math.pi * 1.7)
        k1 = min(1.0, t / 0.16)
        k1 = k1 * k1 * (3 - 2 * k1)
        zz = (top + 0.0165) + (top + 0.0106 - (top + 0.0165)) * k1          # ложится на коврик
        edge0 = mat_d / 2 - 0.03
        if yy > edge0:
            kk = min(1.0, (yy - edge0) / 0.12)
            kk = kk * kk * (3 - 2 * kk)
            zz = zz + (mat_z0 + 0.0106 - zz) * kk                            # плавный сход с коврика на стол
        if t > 0.9:
            zz -= (t - 0.9) / 0.1 * 0.045                                    # конец уходит под поверхность стола
        pts.append((xx, yy, zz)); radii.append(0.0105)
    tube(it, "cable", pts, radii, 10, "#2e3431")
    return it


ITEMS = {"keyboard": keyboard, "mouseset": mouseset}
FOCUS = {"keyboard": (0.0, 0.03, 0.0), "mouseset": (0.0, 0.06, -0.06)}
DIST = {"keyboard": 3.0, "mouseset": 1.9}
DESKZ = {"keyboard": -0.065, "mouseset": -0.0875}
EXTRA = {"mouseset": (("macroMouse", 25, 30, 0.75, (0.0, 0.0, -0.02)), ("macroWheel", 10, 55, 0.45, (0.0, 0.07, 0.04)), ("macroSide", 90, 22, 0.6, (-0.12, 0.0, -0.02)), ("macroRear", 180, 18, 0.7, (0.0, -0.05, -0.03))), "keyboard": (("macroL", 25, 38, 1.1), ("macroTop", 0, 82, 1.2), ("macroFront", 0, 6, 0.6, (0.0, -0.29, -0.01)), ("macroLED", 160, 38, 0.7, (0.78, 0.26, 0.0)), ("macroNum", 15, 40, 0.9, (0.55, 0.0, 0.0)))}


def bbox_of(objs):
    mins = Vector((1e9, 1e9, 1e9)); maxs = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        for v in ob.bound_box:
            mins = Vector(map(min, mins, v)); maxs = Vector(map(max, maxs, v))
    return mins, maxs


def render_small(sc, name, objs, focus=(0.0, 0.0, 0.0), dist=3.0, desk_z=-0.065, extra=()):
    """Рендер мелкого предмета на столешнице: десять стандартных ракурсов (8 по кругу через 45 град на 20 град, сверху 62 град, низкий 4 град)
    и дополнительные крупные планы из extra [(имя, az, el, dist)]."""
    from mathutils import Vector
    center = Vector(focus)
    # стол: дубовая столешница под предметом
    desk = bpy.data.meshes.new("desk"); bm = bmesh.new()
    s_ = 6.0
    vs = [bm.verts.new(p) for p in [(-s_, -s_, desk_z), (s_, -s_, desk_z), (s_, s_, desk_z), (-s_, s_, desk_z)]]
    bm.faces.new(vs); bm.to_mesh(desk); bm.free()
    dobj = bpy.data.objects.new("desk", desk); sc.collection.objects.link(dobj)
    dm = bpy.data.materials.new("desk"); dm.use_nodes = True
    dm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = hexc("#a98a62")
    dm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
    dobj.data.materials.append(dm)
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.20, 0.23, 0.26, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    sc.view_settings.exposure = -0.75
    for lname, pos, energy, col in (("key", (2.4, -2.6, 3.2), 520, (1, .93, .85)), ("fill", (-3.0, -1.0, 1.8), 170, (.8, .88, 1)), ("rim", (0.4, 3.2, 2.6), 260, (1, 1, 1))):
        ld = bpy.data.lights.new(lname, "AREA"); ld.energy = energy; ld.size = 2.0; ld.color = col
        lo = bpy.data.objects.new(lname, ld); lo.location = pos; sc.collection.objects.link(lo)
        lo.rotation_euler = (center - lo.location).to_track_quat("-Z", "Y").to_euler()
    cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 50
    cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    (OUT / "previews").mkdir(exist_ok=True)
    shots = []
    for k in range(10):
        if k < 8: az, el, d = k * 45, 20, dist
        elif k == 8: az, el, d = 20, 62, dist * .95
        else: az, el, d = 200, 4, dist * .8
        shots.append((f"{name}_v{k}", az, el, d))
    for ex in extra:
        nm, az, el, d = ex[:4]
        shots.append((f"{name}_{nm}", az, el, d, ex[4] if len(ex) > 4 else None))
    shots = [x if len(x) == 5 else (*x, None) for x in shots]
    for fname, az, el, d, fo in shots:
        ctr = Vector(fo) if fo is not None else center
        a, e = math.radians(az) - math.pi / 2, math.radians(el)
        cam.location = ctr + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * d
        center_ = ctr
        cam.rotation_euler = (center_ - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(OUT / "previews" / f"{fname}.png")
        bpy.ops.render.render(write_still=True)


def main():
    names = WANT or list(ITEMS)
    global _font
    for n in names:
        sc = setup_scene()
        _font = None                                  # read_factory_settings сбрасывает данные Blender, шрифт загружаем заново
        sc.render.resolution_x, sc.render.resolution_y = 900, 600
        sc.cycles.samples = 32
        it = ITEMS[n]()
        for grp in it.groups.values():
            # вырожденные грани (сошедшиеся вершины на кончиках купола мыши) Roblox отклоняет при загрузке: «Unknown Error»
            bmesh.ops.remove_doubles(grp.bm, verts=list(grp.bm.verts), dist=1e-5)
            bad = [f for f in grp.bm.faces if f.calc_area() < 1e-9]
            if bad:
                bmesh.ops.delete(grp.bm, geom=bad, context="FACES")
            stray = [v for v in grp.bm.verts if not v.link_faces]
            if stray:
                bmesh.ops.delete(grp.bm, geom=stray, context="VERTS")
        objs = finish(it)
        stats(it.name, objs)
        mn, mx = bbox_of(objs)
        print(f"BBOX {it.name}: x {mn.x:.3f}..{mx.x:.3f} y {mn.y:.3f}..{mx.y:.3f} z {mn.z:.3f}..{mx.z:.3f} size {mx.x-mn.x:.3f} x {mx.y-mn.y:.3f} x {mx.z-mn.z:.3f}", flush=True)
        if RENDER:
            render_small(sc, it.name, objs, FOCUS.get(n, (0, 0, 0)), DIST.get(n, 3.0), desk_z=DESKZ.get(n, -0.065), extra=EXTRA.get(n, ()))
        export(it.name, objs)
    print("DONE", flush=True)


main()
