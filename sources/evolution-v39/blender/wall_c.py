"""Wall decor, group C (exec'd by wall_hero.py): signs, vents, dispensers, switches, shelves, small curiosities."""


def _runner(it, cx, cy, s, color):
    """Pictogram of a running figure facing the viewer's left, built from boxes on the exit sign's face. Every limb sits at its own depth: overlapping
    coplanar boxes render black."""
    z = -0.49
    ball(it, "plastic", 0.09 * s, P(cx + 0.02 * s, cy + 0.4 * s, z - 0.03), color=color, seg=12)
    limbs = ((0.11, 0.36, 0.25, 0.0, 0.15), (0.09, 0.3, -0.9, -0.12, 0.17), (0.09, 0.3, 0.8, 0.1, 0.2),
             (0.1, 0.38, -0.55, -0.04, -0.17), (0.1, 0.34, 0.85, 0.12, -0.14), (0.1, 0.28, -0.2, 0.2, -0.3))
    for i, (w, h, ang, dx, dy) in enumerate(limbs):
        rbc(it, "plastic", w * s, h * s, 0.03, cx + dx * s, cy + dy * s, z - i * 0.004, rot=RR("Z", ang), bevel=0.01, color=color)


def exitsign():
    """Emergency exit lightbox 3.6 x 1.2: white housing, glowing green face with a running-figure pictogram, a door frame and an arrow."""
    it = Item("ExitSign")
    W, H = 3.6, 1.2
    rbc(it, "plastic", W, H, 0.12, 0, 0, -0.06, bevel=0.04, color="#e6e8e4")
    rbc(it, "plastic", W, H, 0.34, 0, 0, -0.29, bevel=0.1, seg=4, color="#f1f2ee")
    rbc(it, "glow", W - 0.36, H - 0.36, 0.03, 0, 0, -0.455, bevel=0.03, color="#38d27c")
    # pictogram, viewer-left to right: arrow, door, running figure (x is mirrored: viewer-left = +x)
    white = "#f6fff8"
    rpoly(it, "stain", [(1.36, 0.0), (0.98, 0.3), (0.98, 0.12), (0.62, 0.12), (0.62, -0.12), (0.98, -0.12), (0.98, -0.3)], -0.472, 0.01, white)
    rbc(it, "plastic", 0.5, 0.74, 0.012, 0.0, 0.0, -0.48, color=white)
    rbc(it, "glow", 0.28, 0.6, 0.012, 0.0, -0.03, -0.49, color="#38d27c")
    _runner(it, -0.98, -0.02, 0.9, white)
    for x in (-1.5, 1.5):
        rbc(it, "metal", 0.22, 0.14, 0.2, x, H / 2 + 0.07, -0.1, bevel=0.02, color="#b8bcbc")
    return it


def evacplan():
    """Evacuation plan frame 3.8 x 2.7: aluminium frame, paper face with a title band, a floor-plan sketch (room blocks, corridor, red route with an
    arrowhead, exit squares) and a 'you are here' marker. Every layer sits at its own depth so nothing is coplanar."""
    it = Item("EvacPlan")
    W, H = 3.8, 2.7
    rbc(it, "metal", W, H, 0.14, 0, 0, -0.07, bevel=0.02, color="#aeb4b6")
    rbc(it, "paper", W - 0.2, H - 0.2, 0.03, 0, 0, -0.155, color="#f3f2ea")
    rbc(it, "plastic", W - 0.2, 0.46, 0.03, 0, H / 2 - 0.33, -0.18, color="#2f8f5a")
    # outer wall of the sketched floor
    rbc(it, "stain", 3.2, 0.06, 0.01, 0, -1.05, -0.19, color="#555a5c")
    rbc(it, "stain", 3.2, 0.06, 0.01, 0, 0.65, -0.19, color="#555a5c")
    rbc(it, "stain", 0.06, 1.76, 0.01, 1.6, -0.2, -0.19, color="#555a5c")
    rbc(it, "stain", 0.06, 1.76, 0.01, -1.6, -0.2, -0.19, color="#555a5c")
    for (x, y, w, h) in ((1.0, 0.25, 1.0, 0.6), (-0.15, 0.25, 1.0, 0.6), (-1.1, 0.25, 0.8, 0.6), (1.0, -0.7, 1.0, 0.6), (-0.2, -0.7, 1.3, 0.6), (-1.15, -0.7, 0.7, 0.6)):
        rbc(it, "stain", w, h, 0.01, x, y, -0.2, color="#c9d8e0")
    rbc(it, "stain", 3.0, 0.26, 0.01, 0, -0.22, -0.21, color="#f3f2ea")                                    # corridor
    # red route with an arrowhead and green exit squares
    for k in range(8):
        rbc(it, "stain", 0.2, 0.06, 0.01, 1.0 - k * 0.3, -0.22, -0.23, color="#d7332b")
    rpoly(it, "stain", [(-1.38, -0.22), (-1.55, -0.12), (-1.55, -0.32)], -0.23, 0.01, "#d7332b")
    rbc(it, "glow", 0.22, 0.22, 0.012, 1.45, -0.22, -0.24, color="#38d27c")
    rdisc(it, "plastic", 0.1, -0.4, -0.22, -0.24, 0.012, "#1c63c9", seg=16)                               # you are here
    rdisc(it, "stain", 0.17, -0.4, -0.22, -0.23, 0.01, "#d7332b", seg=16)
    for k in range(3):
        rbc(it, "stain", 1.3 - k * 0.2, 0.05, 0.01, 0.9 - (k * 0.1), -1.14 - k * 0.1, -0.2, color="#7c8184")
    for sx in (-1, 1):
        for sy in (-1, 1):
            rdisc(it, "metal", 0.05, sx * (W / 2 - 0.1), sy * (H / 2 - 0.1), -0.14, 0.03, "#8a908e", seg=10)
    return it


def ventgrille():
    it = Item("VentGrille")
    W, H = 3.6, 2.4
    rbc(it, "plastic", W, H, 0.08, 0, 0, -0.04, bevel=0.02, color="#e4e6e1")
    rbc(it, "dark", W - 0.5, H - 0.5, 0.2, 0, 0, -0.14, color="#171b1c")
    rbc(it, "plastic", W, 0.2, 0.3, 0, H / 2 - 0.1, -0.22, bevel=0.04, color="#e4e6e1")
    rbc(it, "plastic", W, 0.2, 0.3, 0, -(H / 2 - 0.1), -0.22, bevel=0.04, color="#e4e6e1")
    for sx in (-1, 1):
        rbc(it, "plastic", 0.2, H, 0.3, sx * (W / 2 - 0.1), 0, -0.22, bevel=0.04, color="#e4e6e1")
    n = 10
    for i in range(n):
        y = -(H - 0.6) / 2 + i * (H - 0.6) / (n - 1)
        rbc(it, "plastic", W - 0.45, 0.17, 0.05, 0, y, -0.32, rot=RR("X", -0.55), bevel=0.012, color="#dfe1dc")
        rbc(it, "stain", W - 0.5, 0.03, 0.01, 0, y - 0.07, -0.34, color="#b9b9ad")                           # dust on the slat edge
    _screws(it, [(W / 2 - 0.1, H / 2 - 0.1), (-(W / 2 - 0.1), H / 2 - 0.1), (W / 2 - 0.1, -(H / 2 - 0.1)), (-(W / 2 - 0.1), -(H / 2 - 0.1))], -0.37, 0.05)
    rng = random.Random(71)
    for k in range(4):
        rpoly(it, "stain", streak_pts(-1.2 + k * 0.8, H / 2 + 0.05, rng.uniform(0.6, 1.6), 0.08, 0.16, rng), -0.03 - k * 0.0014, 0.005, "#cfcdbd")
    return it


def fanvent():
    """Round exhaust fan in a flanged ring behind a wire guard: dark well, hub and six blades, concentric guard rings with radial bars, four screws."""
    it = Item("FanVent")
    R = 1.55
    rdisc(it, "plastic", R + 0.28, 0, 0, 0.0, 0.1, "#e1e3de", bevel=0.03, seg=48)
    rdisc(it, "plastic", R + 0.12, 0, 0, -0.1, 0.18, "#e8eae5", bevel=0.05, seg=48)
    rdisc(it, "dark", R - 0.1, 0, 0, -0.1, 0.2, "#101416", seg=48)
    for k in range(6):
        rbc(it, "plastic", 0.62, 0.34, 0.03, math.cos(k * math.pi / 3) * 0.7, math.sin(k * math.pi / 3) * 0.7, -0.22,
            rot=RR("Z", k * math.pi / 3) @ RR("X", 0.5), bevel=0.01, color="#2e3639")
    rdisc(it, "metal", 0.28, 0, 0, -0.18, 0.16, "#7c8588", bevel=0.03, seg=24)
    for r in (0.55, 0.95, 1.35):
        torus(it, "metal", r, 0.025, P(0, 0, -0.34), color="#b8bcbc", seg=48, minor=6, rot=Rx(math.pi / 2))
    for k in range(10):
        a = k / 10 * math.pi
        rbc(it, "metal", 2 * 1.36, 0.035, 0.035, 0, 0, -0.34, rot=RR("Z", a), color="#b8bcbc")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        _screws(it, [(math.cos(a) * (R + 0.2), math.sin(a) * (R + 0.2))], -0.3, 0.06)
    rng = random.Random(72)
    for k in range(5):
        rpoly(it, "stain", streak_pts(-0.9 + k * 0.45, R + 0.3, rng.uniform(0.5, 1.4), 0.06, 0.14, rng), -0.03 - k * 0.0014, 0.005, "#cfcdbd")
    return it


def ventduct():
    """A galvanised rectangular duct stub leaving the wall: flanges with bolts at the wall and at the open end, rivet rows, louvres inside."""
    it = Item("VentDuct")
    W, H, L = 3.8, 2.4, 1.7
    sheet = "#a9b0b2"
    rbc(it, "metal", W + 0.7, H + 0.7, 0.12, 0, 0, -0.06, bevel=0.02, color="#9aa1a3")
    for sy in (-1, 1):
        rbc(it, "metal", W, 0.1, L, 0, sy * (H / 2 - 0.05), -0.12 - L / 2, bevel=0.015, color=sheet)
    for sx in (-1, 1):
        rbc(it, "metal", 0.1, H, L, sx * (W / 2 - 0.05), 0, -0.12 - L / 2, bevel=0.015, color=sheet)
    rbc(it, "dark", W - 0.2, H - 0.2, 0.1, 0, 0, -0.2, color="#101416")
    for i in range(6):
        y = -(H - 0.8) / 2 + i * (H - 0.8) / 5
        rbc(it, "metal", W - 0.3, 0.12, 0.05, 0, y, -0.55, rot=RR("X", -0.5), bevel=0.01, color="#8f979a")
    z = -0.12 - L
    for sy in (-1, 1):
        rbc(it, "metal", W + 0.5, 0.18, 0.12, 0, sy * (H / 2 + 0.07), z, bevel=0.02, color="#9aa1a3")
    for sx in (-1, 1):
        rbc(it, "metal", 0.18, H + 0.5, 0.12, sx * (W / 2 + 0.07), 0, z, bevel=0.02, color="#9aa1a3")
    for k in range(9):
        bx = -(W / 2) - 0.1 + k * (W + 0.2) / 8
        _screws(it, [(bx, H / 2 + 0.07), (bx, -(H / 2 + 0.07))], z - 0.06, 0.05)
    for k in range(1, 4):
        by = -H / 2 + k * H / 4
        _screws(it, [(W / 2 + 0.07, by), (-(W / 2 + 0.07), by)], z - 0.06, 0.05)
    rng = random.Random(73)
    for k in range(5):
        rpoly(it, "stain", streak_pts(-1.4 + k * 0.7, H / 2 + 0.38, rng.uniform(0.5, 1.2), 0.08, 0.18, rng), -0.03 - k * 0.0014, 0.005, "#cfcdbd")
    return it


def sanitizer():
    it = Item("Sanitizer")
    rbc(it, "plastic", 0.9, 2.0, 0.1, 0, 0, -0.05, bevel=0.03, color="#dfe1dc")
    rbc(it, "plastic", 0.82, 1.9, 0.42, 0, 0, -0.28, bevel=0.14, seg=4, color="#f4f5f1")
    rbc(it, "plastic", 0.5, 0.9, 0.02, 0, 0.3, -0.5, bevel=0.04, color="#3a7fc1")                              # liquid seen through the window
    rbc(it, "plastic", 0.52, 0.12, 0.05, 0, 0.78, -0.5, bevel=0.02, color="#cfd3cf")
    rbc(it, "stain", 0.1, 0.5, 0.012, 0.24, 0.35, -0.515, color="#9ccdf2")                                  # highlight
    rbc(it, "plastic", 0.3, 0.12, 0.55, 0, -0.45, -0.46, rot=RR("X", 0.3), bevel=0.04, color="#5a6064")       # pump lever
    rbc(it, "plastic", 0.5, 0.1, 0.4, 0, -0.85, -0.42, bevel=0.03, color="#c5c9c5")                           # drip tray
    rdisc(it, "plastic", 0.2, 0, -0.1, -0.505, 0.012, "#1c63c9", seg=20)
    rbc(it, "stain", 0.07, 0.18, 0.01, 0.0, -0.1, -0.52, color="#f6f7f3")
    rng = random.Random(74)
    rpoly(it, "stain", streak_pts(0.05, -1.0, 1.2, 0.06, 0.14, rng), -0.03, 0.005, "#a8c4dc")
    rpoly(it, "stain", blob_pts(0.05, -2.35, 0.28, 0.14, rng, n=14, noise=.3), -0.044, 0.005, "#8fb4d4")
    return it


def lightswitch():
    it = Item("LightSwitch")
    rbc(it, "plastic", 0.78, 1.2, 0.08, 0, 0, -0.04, bevel=0.03, color="#ecebe2")
    rbc(it, "plastic", 0.62, 1.04, 0.04, 0, 0, -0.1, bevel=0.025, color="#f4f3ea")
    for x, on in ((0.17, True), (-0.17, False)):
        rbc(it, "plastic", 0.28, 0.5, 0.06, x, 0.0, -0.15, rot=RR("X", 0.12 if on else -0.12), bevel=0.03, color="#e7e6dc")
    for y in (0.46, -0.46):
        rdisc(it, "metal", 0.045, 0, y, -0.12, 0.02, "#8a908e", seg=10)
    return it


def keypad():
    it = Item("Keypad")
    rbc(it, "plastic", 1.0, 1.7, 0.12, 0, 0, -0.06, bevel=0.04, color="#2b3033")
    rbc(it, "plastic", 0.9, 1.6, 0.2, 0, 0, -0.2, bevel=0.1, seg=4, color="#3a4044")
    rbc(it, "dark", 0.6, 0.32, 0.03, 0, 0.55, -0.31, bevel=0.03, color="#0c1113")
    for k in range(3):
        rbc(it, "glow", 0.12, 0.05, 0.012, -0.15 + k * 0.15, 0.55, -0.33, color="#ffb347" if k < 2 else "#ff4a3a")
    for r in range(4):
        for c in range(3):
            rbc(it, "plastic", 0.2, 0.17, 0.05, 0.25 - c * 0.25, 0.1 - r * 0.24, -0.31, bevel=0.025, color="#d7dad7")
    rbc(it, "dark", 0.62, 0.18, 0.025, 0, -0.78, -0.3, bevel=0.02, color="#1b2023")
    rdisc(it, "glow", 0.05, 0.25, -0.78, -0.312, 0.012, "#4aff9a", seg=10)
    return it


def _plank(it, w, d, y, color="#6b4a31"):
    rbc(it, "wood_mid", w, 0.24, d, 0, y, -d / 2, bevel=0.03, color=color)
    for x in (-w / 2 + 0.7, w / 2 - 0.7):
        rbc(it, "metal", 0.1, 0.9, 0.08, x, y - 0.5, -0.04, color="#4b5356")
        rbc(it, "metal", 0.1, 0.1, d * 0.8, x, y - 0.1, -d * 0.45, color="#4b5356")


def shelfbooks():
    it = Item("ShelfBooks"); rng = random.Random(81)
    W, D = 5.0, 1.1
    _plank(it, W, D, 0.0)
    pal = ["#7a2c2c", "#2c5270", "#3a6246", "#c4a85c", "#583e6e", "#d6ceb8", "#464a54", "#966038", "#26383f", "#b07a4c"]
    x = W / 2 - 0.3
    for i in range(14):
        w = rng.uniform(0.12, 0.28); h = rng.uniform(0.9, 1.5)
        if x - w < -0.2:
            break
        lean = 0.0
        rbc(it, "paper", w, h, 0.62, x - w / 2, 0.12 + h / 2, -0.55, rot=RR("Z", lean), bevel=0.012, color=rng.choice(pal))
        rbc(it, "stain", w * 0.7, 0.07, 0.02, x - w / 2, 0.12 + h * 0.65, -0.87, color="#e7dfc8")
        x -= w + 0.01
    rbc(it, "paper", 0.95, 0.2, 0.7, -0.9, 0.22, -0.55, rot=RR("Y", 0.1), bevel=0.01, color="#a64a2a")      # a book lying flat
    rbc(it, "paper", 0.85, 0.16, 0.62, -0.9, 0.4, -0.55, rot=RR("Y", -0.1), bevel=0.01, color="#2c5270")
    rcyl(it, "ceramic", 0.22, (-1.8, 0.12, -0.55), (-1.8, 0.62, -0.55), "#e6e2d4", seg=16, r2=0.25)                  # a mug
    torus(it, "ceramic", 0.14, 0.04, P(-1.55, 0.4, -0.55), color="#e6e2d4", seg=14, minor=6, rot=Rx(math.pi / 2))
    rcyl(it, "paint", 0.3, (-2.15, 0.12, -0.5), (-2.15, 0.52, -0.5), "#a0522d", seg=18, r2=0.34)                      # plant pot
    for k in range(7):
        a = k * 0.9
        rbc(it, "leaf", 0.12, 0.6, 0.05, -2.15 + math.cos(a) * 0.18, 0.8 + (k % 3) * 0.1, -0.5 + math.sin(a) * 0.18, rot=RR("Z", math.cos(a) * 0.5) @ RR("X", math.sin(a) * 0.4), bevel=0.01, color="#3b7a49")
    return it


def shelfdecor():
    it = Item("ShelfDecor"); rng = random.Random(82)
    W, D = 4.2, 1.0
    _plank(it, W, D, 0.0, "#9a7248")
    # trophy cup
    rcyl(it, "brass", 0.32, (1.5, 0.12, -0.5), (1.5, 0.26, -0.5), "#b8913f", seg=20)
    rcyl(it, "brass", 0.07, (1.5, 0.26, -0.5), (1.5, 0.6, -0.5), "#b8913f", seg=12)
    rcyl(it, "brass", 0.2, (1.5, 0.6, -0.5), (1.5, 1.15, -0.5), "#b8913f", seg=22, r2=0.38)
    torus(it, "brass", 0.4, 0.035, P(1.5, 1.12, -0.5), color="#b8913f", seg=22, minor=6)
    # photo frame leaning back
    rbc(it, "wood_dark", 1.0, 1.3, 0.07, 0.35, 0.8, -0.3, rot=RR("X", 0.2), bevel=0.015, color="#3a261b")
    rbc(it, "paper", 0.8, 1.1, 0.03, 0.35, 0.8, -0.34, rot=RR("X", 0.2), color="#c8b690")
    rbc(it, "stain", 0.8, 0.45, 0.012, 0.35, 0.55, -0.37, rot=RR("X", 0.2), color="#5f8a9a")
    ball(it, "paper", 0.14, P(0.35, 0.78, -0.37), color="#e0c9a8", seg=10)
    # hourglass
    rcyl(it, "wood_dark", 0.25, (-0.7, 0.12, -0.5), (-0.7, 0.2, -0.5), "#3a261b", seg=16)
    rcyl(it, "ceramic", 0.2, (-0.7, 0.2, -0.5), (-0.7, 0.5, -0.5), "#efe9d8", seg=16, r2=0.03)
    rcyl(it, "ceramic", 0.03, (-0.7, 0.5, -0.5), (-0.7, 0.8, -0.5), "#efe9d8", seg=16, r2=0.2)
    rcyl(it, "wood_dark", 0.25, (-0.7, 0.8, -0.5), (-0.7, 0.88, -0.5), "#3a261b", seg=16)
    # a small globe on a stand
    rcyl(it, "metal", 0.22, (-1.5, 0.12, -0.5), (-1.5, 0.2, -0.5), "#4b5356", seg=16)
    rcyl(it, "metal", 0.04, (-1.5, 0.2, -0.5), (-1.5, 0.5, -0.5), "#4b5356", seg=8)
    ball(it, "plastic_blue", 0.4, P(-1.5, 0.95, -0.5), color="#2f6fb0", seg=22)
    for k in range(5):                                                                                           # a stack of papers
        rbc(it, "paper", 0.9, 0.05, 0.65, -2.0 + 0.0, 0.14 + k * 0.055, -0.5, rot=RR("Y", rng.uniform(-0.12, 0.12)), color="#efe9d8")
    return it


def mousehole():
    """A mouse hole in the skirting: a dark arch with a chipped plaster rim, a wedge of cheese with holes and a few crumbs."""
    it = Item("MouseHole")
    R = 0.55
    pts = [(math.cos(a) * R, math.sin(a) * R * 1.1 - 0.05) for a in [i / 18 * math.pi for i in range(19)]] + [(-R, -0.62), (R, -0.62)]
    rpoly(it, "stain", [(x * 1.28, y * 1.2) for x, y in pts], -0.03, 0.006, "#b8b4a4")
    rpoly(it, "dark", pts, -0.045, 0.012, "#0e1011")
    rng = random.Random(83)
    for k in range(10):
        a = k / 10 * math.pi + rng.uniform(-0.1, 0.1)
        rbc(it, "tint", rng.uniform(0.14, 0.26), rng.uniform(0.1, 0.18), 0.04, math.cos(a) * (R + 0.08), math.sin(a) * R * 1.12 - 0.02, -0.06, rot=RR("Z", a), bevel=0.01)
    # a wedge of cheese lying in front of the hole: sloped top, darker rind on the back, holes on the face
    wedge = [(-0.15, -0.62), (-0.95, -0.62), (-0.95, -0.5), (-0.15, -0.3)]
    rpoly(it, "stain", wedge, -0.1, 0.2, "#f1c232")
    rpoly(it, "stain", [(-0.15, -0.3), (-0.95, -0.5), (-0.95, -0.46), (-0.15, -0.26)], -0.1, 0.2, "#cf9e1a")
    for (x, y, r) in ((-0.38, -0.52, 0.05), (-0.62, -0.55, 0.04), (-0.78, -0.58, 0.03), (-0.3, -0.45, 0.025)):
        rdisc(it, "stain", r, x, y, -0.3, 0.008, "#b98a12", seg=10)
    for k in range(6):
        rbc(it, "stain", 0.05, 0.04, 0.02, -1.0 + rng.uniform(-0.25, 0.2), -0.62 + rng.uniform(0.0, 0.03), -0.2, color="#f1c232", rot=RR("Z", rng.uniform(0, 3)))
    return it


def wallhole():
    it = Item("WallHole"); rng = random.Random(84)
    outline = blob_pts(0, 0, 1.55, 1.8, rng, n=26, noise=.28, harmonics=5)
    rpoly(it, "stain", [(x * 1.2, y * 1.15) for x, y in outline], -0.03, 0.006, "#b9b5a6")               # dust and fallen debris around
    rpoly(it, "dark", outline, -0.045, 0.02, "#08090a")
    rpoly(it, "stain", [(x * 0.8 + 0.1, y * 0.8) for x, y in outline], -0.07, 0.01, "#14100e")
    for k in range(16):                                                                                  # broken plaster rim, chunks sticking out
        a = k / 16 * math.tau + rng.uniform(-0.15, 0.15)
        x, y = math.cos(a) * 1.58, math.sin(a) * 1.82
        rbc(it, "tint", rng.uniform(0.3, 0.62), rng.uniform(0.2, 0.42), rng.uniform(0.1, 0.22), x, y, -0.1,
            rot=RR("Z", a + rng.uniform(-0.6, 0.6)) @ RR("X", rng.uniform(-0.3, 0.3)), bevel=0.03)
    # rusty reinforcement bars and torn wires inside
    for (x0, y0, x1, y1) in ((-1.1, -0.4, 0.9, -0.1), (-0.9, 0.9, 1.0, 0.5), (-0.3, -1.3, 0.2, 1.3)):
        rcyl(it, "metal", 0.05, (x0, y0, -0.22), (x1, y1, -0.26), "#7a4a2a", seg=10)
    for col, pts in (("#c0392b", [(0.5, 1.4, -0.1), (0.6, 0.6, -0.4), (0.3, 0.1, -0.6), (0.45, -0.5, -0.5)]),
                     ("#2c5aa0", [(0.8, 1.2, -0.1), (1.0, 0.4, -0.35), (0.9, -0.3, -0.55)]),
                     ("#1f1f20", [(-0.9, 1.3, -0.1), (-0.7, 0.5, -0.4), (-1.0, -0.2, -0.5), (-0.8, -0.9, -0.3)])):
        rtube(it, "rubber", pts, [0.06] * len(pts), 8, col)
    for k in range(5):                                                                                   # puffs of insulation
        ball(it, "paper", rng.uniform(0.2, 0.34), P(rng.uniform(-0.5, 0.6), rng.uniform(-1.2, -0.4), -0.18), scale=(1, 0.6, 1), color="#e9b4c2", seg=10)
    return it


def tallymarks():
    it = Item("TallyMarks"); rng = random.Random(85)
    graphite = "#3b3d3f"
    for g in range(5):
        gx = 1.2 - (g % 3) * 1.15
        gy = 0.5 - (g // 3) * 1.0
        for k in range(4):
            x = gx - 0.5 + k * 0.28 + rng.uniform(-0.02, 0.02)
            rbc(it, "stain", 0.05, 0.62 + rng.uniform(-0.04, 0.05), 0.01, x, gy + rng.uniform(-0.02, 0.02), -0.03 - (g * 4 + k) * 0.0007, rot=RR("Z", rng.uniform(-0.05, 0.05)), color=graphite)
        rbc(it, "stain", 1.25, 0.05, 0.01, gx - 0.12, gy + 0.02, -0.036 - g * 0.0007, rot=RR("Z", -0.62), color=graphite)
    return it


def emergencylamp():
    """Emergency luminaire: white plate, wide body, two adjustable lamp heads on stalks, a green test LED and a test button."""
    it = Item("EmergencyLamp")
    rbc(it, "plastic", 2.1, 0.9, 0.1, 0, 0, -0.05, bevel=0.03, color="#dfe1dc")
    rbc(it, "plastic", 1.9, 0.78, 0.34, 0, 0, -0.27, bevel=0.1, seg=4, color="#f1f2ee")
    for sx in (-1, 1):
        rcyl(it, "metal", 0.07, (sx * 0.65, 0.0, -0.4), (sx * 0.95, 0.35, -0.75), "#9aa1a5", seg=10)
        ball(it, "plastic", 0.24, P(sx * 1.0, 0.42, -0.82), color="#e9ebe7", seg=16)
        rcyl(it, "plastic", 0.3, (sx * 1.0, 0.42, -0.82), (sx * 1.18, 0.56, -1.12), "#d6d9d5", seg=22, r2=0.36)
        rcyl(it, "glow", 0.28, (sx * 1.18, 0.56, -1.12), (sx * 1.2, 0.575, -1.15), "#fff2c8", seg=22)
    rdisc(it, "glow", 0.05, 0.0, -0.2, -0.45, 0.02, "#4aff9a", seg=10)
    rdisc(it, "plastic", 0.09, 0.0, -0.02, -0.45, 0.03, "#c9ccc8", seg=14)
    return it


def wallladder():
    """A fixed steel service ladder 1.7 wide and 9 high: two rails with stand-off brackets, round rungs, a hoop cage on the upper part."""
    it = Item("WallLadder")
    H, W = 9.0, 1.7
    for sx in (-1, 1):
        rpost(it, "metal", 0.07, -H / 2, H / 2, sx * W / 2, -0.55, seg=12, color="#c9a21e")
    for k in range(int(H / 0.9)):
        y = -H / 2 + 0.45 + k * 0.9
        rpipex(it, "metal", 0.055, -W / 2, W / 2, y, -0.55, "#c9a21e", seg=10)
    for y in (-H / 2 + 1.2, -H / 2 + 4.0, -H / 2 + 6.8, H / 2 - 0.5):
        for sx in (-1, 1):
            rbc(it, "metal", 0.12, 0.2, 0.5, sx * W / 2, y, -0.28, bevel=0.02, color="#7f898d")
            rbc(it, "metal", 0.3, 0.2, 0.06, sx * W / 2, y, -0.04, bevel=0.02, color="#7f898d")
    # safety hoops around the upper part: half rings in front of the rails, joined by three vertical straps
    R = 0.9
    for y in (1.0, 2.2, 3.4):
        pts = [(R * math.sin(p), y, -0.55 - R * math.cos(p) * 1.0) for p in [-1.5 + k * 3.0 / 12 for k in range(13)]]
        rtube(it, "metal", pts, [0.04] * len(pts), 8, "#c9a21e")
    for x, z in ((0.0, -0.55 - R), (R * math.sin(0.75), -0.55 - R * math.cos(0.75)), (-R * math.sin(0.75), -0.55 - R * math.cos(0.75))):
        rpost(it, "metal", 0.035, 0.9, 3.5, x, z, seg=8, color="#c9a21e")
    return it


def cableloops():
    """Cables sagging between wall clips: five loops of different colours and thickness, clips with screws, one cable hanging loose."""
    it = Item("CableLoops"); rng = random.Random(86)
    cols = ["#1f1f20", "#b7312c", "#2c5aa0", "#caa21c", "#1f1f20", "#2f7a3e"]
    xs = [2.2, 0.9, -0.4, -1.7, -3.0]
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        for j in range(3):
            sag = rng.uniform(0.5, 1.1)
            pts = [(x0 + (x1 - x0) * t, -sag * math.sin(t * math.pi) - 0.05 * j, -0.18 - 0.05 * j - 0.12 * math.sin(t * math.pi)) for t in [k / 10 for k in range(11)]]
            rtube(it, "rubber", pts, [0.06 + 0.02 * (j == 0)] * 11, 8, cols[(i + j) % len(cols)])
    for x in xs:
        rbc(it, "metal", 0.26, 0.5, 0.08, x, 0.0, -0.1, bevel=0.02, color="#8a908e")
        rbc(it, "metal", 0.34, 0.2, 0.2, x, 0.0, -0.2, bevel=0.03, color="#8a908e")
        rdisc(it, "metal", 0.05, x, 0.2, -0.14, 0.03, "#6d7578", seg=8)
    loose = [(-3.0, 0.0, -0.22), (-3.12, -0.55, -0.26), (-3.1, -1.1, -0.28), (-3.2, -1.7, -0.3), (-3.15, -2.2, -0.3)]
    rtube(it, "rubber", loose, [0.07] * 5, 8, "#b7312c")
    for cy in (-0.7, -1.45):                                                        # the loose cable is held by two clips
        cx = -3.1 - 0.02 * abs(cy)
        rbc(it, "metal", 0.2, 0.16, 0.06, cx, cy, -0.12, bevel=0.015, color="#8a908e")
        rdisc(it, "metal", 0.035, cx, cy, -0.16, 0.02, "#6d7578", seg=8)
    # it ends in a plug: moulded housing, two pins, strain relief
    rbc(it, "plastic", 0.3, 0.42, 0.2, -3.15, -2.45, -0.3, bevel=0.05, seg=3, color="#26292b")
    rbc(it, "rubber", 0.13, 0.18, 0.13, -3.15, -2.2, -0.3, bevel=0.03, color="#b7312c")
    for px in (-0.07, 0.07):
        rbc(it, "metal", 0.035, 0.18, 0.03, -3.15 + px, -2.74, -0.3, color="#c8ccce")
    return it


ITEMS_C = {"emergencylamp": emergencylamp, "wallladder": wallladder, "cableloops": cableloops, "exitsign": exitsign, "evacplan": evacplan, "ventgrille": ventgrille, "fanvent": fanvent, "ventduct": ventduct, "sanitizer": sanitizer,
           "lightswitch": lightswitch, "keypad": keypad, "shelfbooks": shelfbooks, "shelfdecor": shelfdecor, "mousehole": mousehole, "wallhole": wallhole,
           "tallymarks": tallymarks}
