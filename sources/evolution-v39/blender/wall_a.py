"""Wall decor, group A (exec'd by wall_hero.py): air conditioners, water stains, cracks, peeling paint."""


def _ac(name, W, old, seed):
    rng = random.Random(seed)
    it = Item(name)
    SH = "#d8d2b6" if old else "#eef0ec"        # shell
    PN = "#cfc8a9" if old else "#f6f7f3"        # front panel
    SIDE = "#c4bd9f" if old else "#e1e5e1"
    GR = "#8c9390"
    # mounting plate
    rbc(it, "metal", W - 0.4, 1.35, 0.1, 0, 0.0, -0.05, color="#9ba19f", bevel=0.01)
    # upper shell (rounded) and the lower outlet housing
    rbc(it, "plastic", W, 1.14, 1.02, 0, 0.27, -0.59, bevel=0.34, seg=6, color=SH)
    rbc(it, "plastic", W - 0.08, 0.6, 0.84, 0, -0.50, -0.50, bevel=0.2, seg=4, color=SIDE)
    # front panel with a raised face and seams
    rbc(it, "plastic", W - 0.55, 0.9, 0.05, 0, 0.30, -1.07, bevel=0.035, seg=3, color=PN)
    for y in (0.74, -0.1):
        rbc(it, "stain", W - 0.5, 0.025, 0.02, 0, y, -1.095, color=GR)
    for x in (-(W / 2 - 0.42), W / 2 - 0.42):
        rbc(it, "stain", 0.025, 0.84, 0.02, x, 0.31, -1.095, color=GR)
    # intake slats on the sloped top-front edge
    for i in range(int((W - 1.2) / 0.17)):
        x = -(W - 1.2) / 2 + i * 0.17 + 0.08
        rbc(it, "dark", 0.07, 0.025, 0.36, x, 0.835, -0.62, color="#4b5250")
    # outlet: dark mouth in the underside, vanes, the louver flap hinged at the back
    rbc(it, "dark", W - 0.9, 0.04, 0.66, 0, -0.815, -0.52)
    nv = int((W - 1.1) / 0.18)
    for i in range(nv):
        x = -(W - 1.1) / 2 + i * (W - 1.1) / (nv - 1)
        rbc(it, "plastic", 0.03, 0.16, 0.5, x, -0.88, -0.38, color="#c3c8c5" if not old else "#b3ad92")
    rbc(it, "plastic", W - 1.0, 0.07, 0.56, 0, -0.9, -0.62, rot=RR("X", -0.52 if not old else -0.1), bevel=0.02, color=SH)
    # display window and LEDs on the viewer's right end
    dx = -(W / 2 - 1.0)
    rbc(it, "dark", 1.0, 0.24, 0.035, dx, 0.2, -1.1, bevel=0.07, seg=3, color="#101517")
    if not old:
        rdisc(it, "glow", 0.045, dx - 0.3, 0.2, -1.115, 0.02, "#7dffb0", seg=12)
        rdisc(it, "glow", 0.045, dx - 0.12, 0.2, -1.115, 0.02, "#ffb04a", seg=12)
        for k, h in enumerate((0.1, 0.16, 0.2, 0.1)):
            rbc(it, "glow", 0.05, h, 0.02, dx + 0.16 + k * 0.12, 0.2, -1.12, color="#7fe0ff")
    else:
        rdisc(it, "dark", 0.045, dx - 0.3, 0.2, -1.115, 0.02, "#34412f", seg=12)
    rbc(it, "metal", 0.9, 0.06, 0.03, W / 2 - 1.0, 0.45, -1.1, color="#b9bfbd")        # logo bar
    # refrigerant line (black foam) and drain hose leaving the viewer's left end into the wall
    ex = W / 2
    rtube(it, "rubber", [(ex - 0.2, -0.55, -0.55), (ex + 0.3, -0.55, -0.55), (ex + 0.72, -0.55, -0.38), (ex + 0.9, -0.55, -0.04)], [0.15] * 4, 14, "#26292b")
    rtube(it, "plastic", [(ex - 0.2, -0.75, -0.45), (ex + 0.25, -0.75, -0.45), (ex + 0.5, -0.78, -0.2), (ex + 0.62, -0.82, -0.04)], [0.09] * 4, 10, "#e8ebe8")
    rtube(it, "copper", [(ex - 0.2, -0.38, -0.5), (ex + 0.25, -0.38, -0.5), (ex + 0.55, -0.38, -0.3), (ex + 0.72, -0.38, -0.04)], [0.07] * 4, 10)
    rdisc(it, "plastic", 0.24, ex + 0.9, -0.55, -0.04, 0.05, "#d6d9d6", seg=20)           # wall sleeve cover
    # energy label sticker on the front: coloured bars of a rating scale
    sx = W / 2 - 1.3
    rbc(it, "paper", 0.5, 0.36, 0.012, sx, -0.0, -1.098, color="#f1f1ea")
    for k, c in enumerate(("#3f9a4d", "#8bc34a", "#e6d23a", "#f1a73a", "#d9573a")):
        rbc(it, "stain", 0.1 + 0.05 * (4 - k) * 0.5, 0.045, 0.012, sx + 0.12 - (0.1 + 0.05 * (4 - k) * 0.5) / 2 + 0.05 + 0.0, 0.12 - k * 0.06, -1.108, color=c)
    # vertical front groove and a small status lamp on the left end cap
    rdisc(it, "glow", 0.04, -(W / 2 - 0.2), -0.3, -0.9, 0.02, "#7dffb0" if not old else "#3c4a34", seg=10)
    if old:
        # yellowed, dusty: faint grime lines on the panel, a dark tide line under the outlet, a thin rust drip under the drain hose
        for i in range(10):
            x = rng.uniform(-W / 2 + 0.7, W / 2 - 0.7)
            rbc(it, "stain", rng.uniform(0.04, 0.07), rng.uniform(0.2, 0.6), 0.008, x, 0.36, -1.094, color="#bdb48f")
        rbc(it, "stain", W - 0.9, 0.05, 0.008, 0, -0.16, -1.09, color="#a89f7b")
        for i in range(8):
            x = -(W - 1.4) / 2 + i * (W - 1.4) / 7 + rng.uniform(-0.1, 0.1)
            rpoly(it, "stain", streak_pts(x, -0.95, rng.uniform(0.35, 1.0), 0.04, 0.1, rng), -0.03 - i * 0.0012, 0.006, "#d6cfb4")
        rpoly(it, "stain", streak_pts(ex + 0.62, -0.95, 2.1, 0.05, 0.13, rng), -0.043, 0.008, "#c1a979")
        rpoly(it, "stain", streak_pts(ex + 0.62, -0.95, 1.4, 0.03, 0.07, rng), -0.056, 0.008, "#a2814e")
    return it


def acsplit():
    return _ac("AcSplit", 5.0, False, 11)


def acsplitold():
    return _ac("AcSplitOld", 4.4, False, 12)    # the user asked for a clean, newer unit: same white look as AcSplit, narrower


def acsplitwide():
    return _ac("AcSplitWide", 7.0, False, 13)


def _lerp_hex(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient_stain(it, rng, cx, cy, rx, ry, c_out, c_in, rim, n=9, topY=None, z0=-0.03, noise=0.18, shrink=0.2, dz=0.0095):
    """Soft-edged stain imitated by many thin blobs: pale halo -> dark thin tide rim -> fill that darkens towards the core."""
    z = z0
    base = [rng.uniform(0, math.tau) for _ in range(5)]
    for k in range(n):
        t = k / (n - 1)
        s = 1.0 - (1.0 - shrink) * t ** 0.85
        col = _lerp_hex(c_out, c_in, t ** 0.9)
        if k == 1:
            col = rim
        pts = blob_pts(cx + (0.05 * rx) * t, cy, rx * s, ry * s, rng, n=64, noise=noise * (0.6 + 0.6 * t), harmonics=6)
        if topY is not None:
            pts = clip_top(pts, topY)
        rpoly(it, "stain", pts, z, 0.006, col)
        z -= dz
    return z


def _salt(it, rng, cx, cy, rx, ry, n, z, a0=0, a1=math.tau):
    for _ in range(n):
        a = rng.uniform(a0, a1)
        r = rng.uniform(0.9, 1.04)
        rpoly(it, "stain", blob_pts(cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r, rng.uniform(.05, .14), rng.uniform(.03, .07), rng, n=12, noise=.35), z, 0.006, "#f1efe3")


def stainbloom():
    """Water stain spreading from the ceiling edge: soft halo, thin dark tide rim, darker core, drips, salt crust. Top edge = y +2.8."""
    it = Item("StainBloom"); rng = random.Random(21)
    T0 = 2.8
    z = _gradient_stain(it, rng, 0, T0, 4.3, 5.1, "#e4dcc8", "#b3a37f", "#b0a07c", n=18, topY=T0, dz=0.0052, noise=0.16)
    for x, ln, w in ((-2.3, 1.7, .2), (-0.9, 2.3, .16), (0.7, 1.2, .18), (2.0, 1.9, .15), (3.0, 0.9, .13)):
        y0 = T0 - 4.5 + rng.uniform(-0.2, 0.8)
        rpoly(it, "stain", streak_pts(x, y0, ln, w * .5, w, rng), z, 0.006, "#c3ae80")
    _salt(it, rng, 0, T0, 4.3, 5.1, 12, z - 0.012, math.pi * 1.05, math.pi * 1.95)
    for _ in range(10):
        a = rng.uniform(math.pi * 1.1, math.pi * 1.9); r = rng.uniform(0.78, 0.97)
        rpoly(it, "stain", blob_pts(math.cos(a) * 4.3 * r, T0 + math.sin(a) * 5.1 * r, rng.uniform(.04, .1), rng.uniform(.04, .09), rng, n=9, noise=.4), z - 0.012, 0.006, "#6f6a52")
    return it


def stainstreaks():
    """Six vertical leak streaks with a mineral crust at the top. Top edge y +3.6, up to 7 long."""
    it = Item("StainStreaks"); rng = random.Random(22)
    top = 3.6
    xs = (-2.0, -1.0, -0.1, 0.8, 1.7, 2.4)
    lens = (4.6, 6.8, 3.4, 5.6, 4.0, 2.6)
    ws = (0.42, 0.66, 0.32, 0.54, 0.4, 0.26)
    z = -0.03
    for k, (x, ln, w) in enumerate(zip(xs, lens, ws)):
        rpoly(it, "stain", streak_pts(x, top - 0.1, ln + 0.35, w * 2.3, w * 3.0, rng), z - k * 0.0016, 0.0012 + 0.006, "#e2d9c0")
    z -= 0.013
    for k, (x, ln, w) in enumerate(zip(xs, lens, ws)):
        rpoly(it, "stain", streak_pts(x, top - 0.12, ln, w * 1.1, w * 1.7, rng), z - k * 0.0016, 0.006, "#cbb98f")
    z -= 0.013
    for k, (x, ln, w) in enumerate(zip(xs, lens, ws)):
        rpoly(it, "stain", streak_pts(x, top - 0.16, ln * 0.9, w * 0.55, w * 0.95, rng), z - k * 0.0016, 0.006, "#ad9a6c")
    z -= 0.013
    for k, (x, ln, w) in enumerate(zip(xs, lens, ws)):
        rpoly(it, "stain", streak_pts(x, top - 0.2, ln * 0.55, w * 0.2, w * 0.38, rng), z - k * 0.0016, 0.006, "#8f7a52")
    z -= 0.013
    rpoly(it, "stain", blob_pts(0.2, top - 0.05, 3.0, 0.3, rng, n=40, noise=.2), z, 0.01, "#f1efe3")     # crust band
    for k, (x, ln, w) in enumerate(zip(xs, lens, ws)):
        rpoly(it, "stain", blob_pts(x, top - ln - 0.22, w * 1.5, w * 0.8, rng, n=18, noise=.28), z, 0.008, "#9a8559")  # where it stops
    return it


def staintide():
    it = Item("StainTide"); rng = random.Random(23)
    z = _gradient_stain(it, rng, 0, 0, 2.7, 2.1, "#e4dcc8", "#afa07e", "#b0a07c", n=16, dz=0.0052, noise=0.16)
    _salt(it, rng, 0, 0, 2.7, 2.1, 6, z - 0.01, math.pi * 0.1, math.pi * 1.2)
    return it


def rustdrip():
    it = Item("RustDrip"); rng = random.Random(24)
    z = -0.03
    cfg = ((-0.55, 3.2, .42), (0.1, 4.6, .34), (0.72, 2.2, .3))
    for k, (x, ln, w) in enumerate(cfg):
        rpoly(it, "stain", streak_pts(x, 0.9, ln + 0.35, w * 2.2, w * 3.0, rng), z - k * 0.0016, 0.006, "#e2cfae")
    z -= 0.013
    for k, (x, ln, w) in enumerate(cfg):
        rpoly(it, "stain", streak_pts(x, 0.85, ln, w * 1.0, w * 1.6, rng), z - k * 0.0016, 0.006, "#c98a56")
    z -= 0.013
    for k, (x, ln, w) in enumerate(cfg):
        rpoly(it, "stain", streak_pts(x, 0.8, ln * 0.85, w * 0.45, w * 0.8, rng), z - k * 0.0016, 0.006, "#a4562d")
    z -= 0.013
    for k, (x, ln, w) in enumerate(cfg):
        rpoly(it, "stain", streak_pts(x, 0.78, ln * 0.4, w * 0.18, w * 0.3, rng), z - k * 0.0016, 0.006, "#7a3a1b")
    rbc(it, "metal", 1.9, 0.5, 0.1, 0.1, 1.08, -0.05, bevel=0.03, color="#7c817f")                 # the bracket the rust comes from
    for x in (-0.65, 0.85):
        rdisc(it, "metal", 0.1, x, 1.08, -0.1, 0.06, "#6e4a30", seg=10)
    rbc(it, "stain", 1.6, 0.14, 0.015, 0.1, 0.78, -0.115, color="#9a5028")
    return it


def damplow():
    """Rising damp on the (teal) lower wall: the paint darkens below a wavy tide mark, salt crust along the line, drips and dark mould speckles."""
    it = Item("DampLow"); rng = random.Random(25)
    ph = [rng.uniform(0, math.tau) for _ in range(3)]
    tide = [(-3.2 + i * 6.4 / 39, 1.05 + 0.28 * math.sin(i * 0.22 + ph[0]) + 0.12 * math.sin(i * 0.61 + ph[1]) + 0.04 * math.sin(i * 1.9 + ph[2])) for i in range(40)]
    rpoly(it, "stain", [(-3.0, -1.25), (-3.28, -0.6), (-3.2, 0.5)] + [(x, y + 0.14) for x, y in tide] + [(3.2, 0.4), (3.3, -0.5), (3.0, -1.25)], -0.03, 0.008, "#2a6770")
    rpoly(it, "stain", [(-2.95, -1.25), (-3.18, -0.5), (-3.12, 0.4)] + tide + [(3.12, 0.3), (3.2, -0.5), (2.95, -1.25)], -0.043, 0.008, "#1d535b")
    rpoly(it, "stain", [(-2.8, -1.25), (-3.0, -0.6)] + [(x, y - 0.5 - 0.2 * math.sin(x * 1.3 + 1)) for x, y in tide[2:-2]] + [(3.0, -0.6), (2.8, -1.25)], -0.056, 0.008, "#144148")
    for x, y in tide[3:-3:5]:
        rpoly(it, "stain", streak_pts(x, y - 0.02, rng.uniform(0.5, 1.1), 0.05, 0.11, rng), -0.07, 0.008, "#103a40")
    rpoly(it, "stain", ribbon_pts(tide, [0.08] * len(tide)), -0.085, 0.008, "#c9dedc")                                      # salt crust along the tide mark
    for _ in range(26):
        x = rng.uniform(-3.0, 3.0); y = rng.uniform(-1.1, 0.3)
        rpoly(it, "stain", blob_pts(x, y, rng.uniform(.05, .16), rng.uniform(.04, .1), rng, n=10, noise=.3), -0.075, 0.006, "#0b2a2f")
    return it


def _chips(it, cx, cy, n, spread, rng, z=-0.03, size=(0.07, 0.17)):
    for _ in range(n):
        a = rng.uniform(0, math.tau); r = rng.uniform(0.15, spread)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        s = rng.uniform(*size)
        pts = [(x + math.cos(t) * s * rng.uniform(0.55, 1.25), y + math.sin(t) * s * rng.uniform(0.55, 1.25)) for t in sorted(rng.uniform(0, math.tau) for _ in range(5))]
        rpoly(it, "tint", pts, z, rng.uniform(0.025, 0.06))


def _crack_line(it, rng, start, ang, length, w0, z, depth, dark="#2f2d2a", kink=0.55):
    """Jagged crack with side branches spread along its whole length. Returns the path."""
    pts = [start]
    x, y = start
    a = ang
    d = 0.0
    k = 0
    while d < length:
        a += rng.uniform(-0.28, 0.28)
        if k % rng.randint(4, 7) == 0:
            a += rng.choice((-1, 1)) * rng.uniform(0.3, kink)         # kink
        s = rng.uniform(0.16, 0.34)
        x += math.cos(a) * s; y += math.sin(a) * s
        pts.append((x, y)); d += s; k += 1
        a = a * 0.85 + ang * 0.15
    n = len(pts)
    ws = [max(0.02, w0 * (1 - 0.85 * (i / max(n - 1, 1)) ** 1.1) * (1 + 0.3 * math.sin(i * 1.7))) for i in range(n)]
    rpoly(it, "stain", ribbon_pts(pts, [w * 2.2 + 0.025 for w in ws]), z, 0.006, "#cfcdbd")
    rpoly(it, "stain", ribbon_pts(pts, ws), z - 0.007, 0.006, dark)
    if depth > 0:
        m = int(2 + length / 2.2)
        for i in range(m):
            kk = int(n * (i + 0.6) / (m + 0.2))
            if 1 < kk < n - 2:
                _crack_line(it, rng, pts[kk], ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.05), length * rng.uniform(0.12, 0.3), w0 * 0.55, z - 0.003, depth - 1, dark, kink)
    return pts


def cracklong():
    it = Item("CrackLong"); rng = random.Random(31)
    z = -0.03
    _crack_line(it, rng, (0.6, 3.5), -math.pi / 2 - 0.12, 7.0, 0.2, z, 2)
    _chips(it, 0.0, 0.3, 7, 1.9, rng)
    # a blister of plaster that has lifted beside the crack
    rpoly(it, "stain", blob_pts(-0.8, 0.9, 0.9, 0.55, rng, n=24, noise=.25), z - 0.02, 0.006, "#d6d5c5")
    rpoly(it, "stain", blob_pts(-0.8, 0.83, 0.75, 0.42, rng, n=24, noise=.25), z - 0.028, 0.006, "#cdccbc")
    return it


def crackstar():
    it = Item("CrackStar"); rng = random.Random(32)
    z = -0.03
    for k in range(9):
        a = k / 9 * math.tau + rng.uniform(-0.2, 0.2)
        _crack_line(it, rng, (math.cos(a) * 0.55, math.sin(a) * 0.45), a, rng.uniform(1.4, 3.0), 0.12, z - 0.004, 1, kink=0.4)
    for r, a0 in ((1.15, 0.3), (1.9, 1.7)):                                  # ring cracks
        path = [(math.cos(t) * r * 1.12, math.sin(t) * r * 0.95) for t in [a0 + i * 0.17 + rng.uniform(-0.04, 0.04) for i in range(10)]]
        rpoly(it, "stain", ribbon_pts(path, [0.1] * 10), z - 0.01, 0.006, "#2f2d2a")
    pts = blob_pts(0, 0, 0.92, 0.74, rng, n=30, noise=.3, harmonics=5)
    rpoly(it, "stain", [(x * 1.18, y * 1.18) for x, y in pts], z - 0.012, 0.01, "#a7a597")          # dust halo
    rpoly(it, "stain", pts, z - 0.024, 0.01, "#5f5c52")                                                # broken edge
    rpoly(it, "stain", [(x * .7, y * .7) for x, y in pts], z - 0.036, 0.01, "#3b3934")
    rpoly(it, "stain", [(x * .38 + 0.03, y * .38) for x, y in pts], z - 0.048, 0.01, "#171716")
    for k in range(12):                                                                              # raised broken plaster edge
        a = k / 12 * math.tau + rng.uniform(-0.15, 0.15)
        x, y = math.cos(a) * 1.06, math.sin(a) * 0.86
        w, h = rng.uniform(0.16, 0.34), rng.uniform(0.1, 0.24)
        rbc(it, "tint", w, h, 0.07, x, y, -0.07, rot=RR("Z", a + rng.uniform(-0.6, 0.6)) @ RR("X", rng.uniform(-0.3, 0.3)), bevel=0.018)
    _chips(it, 0, 0, 9, 1.7, rng)
    return it


def crackstep():
    it = Item("CrackStep"); rng = random.Random(33)
    z = -0.03
    x, y = -2.8, 1.4
    path = [(x, y)]
    for i in range(10):
        x += rng.uniform(0.35, 0.75); path.append((x, y))
        y -= rng.uniform(0.18, 0.4) * (1 if i % 3 else 1.6); path.append((x, y))
    rpoly(it, "stain", ribbon_pts(path, [0.2] * len(path)), z, 0.006, "#cfcdbd")
    rpoly(it, "stain", ribbon_pts(path, [0.085 + 0.03 * math.sin(i * 1.3) for i in range(len(path))]), z - 0.007, 0.006, "#2f2d2a")
    sub = [path[9]]
    px, py = path[9]
    for i in range(4):
        px += rng.uniform(0.3, 0.55); sub.append((px, py)); py += rng.uniform(0.22, 0.4); sub.append((px, py))
    rpoly(it, "stain", ribbon_pts(sub, [0.15] * len(sub)), z - 0.004, 0.006, "#cfcdbd")
    rpoly(it, "stain", ribbon_pts(sub, [0.06] * len(sub)), z - 0.011, 0.006, "#2f2d2a")
    # repair: a rough trowelled rectangle, a shade lighter than the wall, with a pale crumbly rim
    rect = [(-1.05 + i * 0.35 + rng.uniform(-0.05, 0.05), -0.75 + rng.uniform(-0.06, 0.06)) for i in range(7)] + \
           [(1.05 + rng.uniform(-0.06, 0.04), -0.75 + i * 0.25 + rng.uniform(-0.05, 0.05)) for i in range(1, 5)] + \
           [(1.05 - i * 0.35 + rng.uniform(-0.05, 0.05), 0.25 + rng.uniform(-0.06, 0.06)) for i in range(7)] + \
           [(-1.05 + rng.uniform(-0.04, 0.06), 0.25 - i * 0.25 + rng.uniform(-0.05, 0.05)) for i in range(1, 5)]
    rring(it, "stain", [(x * 1.07, (y + 0.25) * 1.12 - 0.25) for x, y in rect], rect, -0.035, 0.006, "#c9c8b8")                  # soft edge
    rpoly(it, "tint", rect, -0.04, 0.03)                                                                                       # the patch itself: wall colour, slightly raised
    for k in range(3):
        rpoly(it, "stain", ribbon_pts([(-0.8 + k * 0.1, -0.45 + k * 0.28), (0.1, -0.4 + k * 0.28), (0.9, -0.48 + k * 0.28)], [0.03, 0.05, 0.03]), -0.074, 0.004, "#cbcab9")
    return it


def _brick_wall(it, rng, cx, cy, rx, ry, z, bed_color="#85817a"):
    """Courses of old bricks inside an ellipse-ish area: running bond, every brick slightly different in size, tilt, tone and depth; some chipped or missing."""
    row = 0
    y = cy - ry
    while y < cy + ry:
        bh = rng.uniform(0.3, 0.36)
        x = cx - rx - (0.45 if row % 2 else 0.0) - rng.uniform(0, 0.2)
        while x < cx + rx:
            bw = rng.choice((0.86, 0.86, 0.62, 0.74, 0.5)) * rng.uniform(0.92, 1.05)
            px, py = x + bw / 2, y + bh / 2
            d = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
            if d < 0.95 + rng.uniform(-0.15, 0.1) and rng.random() > 0.07:
                c = rng.choice(("#94604d", "#8a5846", "#9d6853", "#865543", "#a06e58", "#7d4f40", "#a87560"))
                dz = rng.uniform(0, 0.03)
                rbc(it, "brick", bw - 0.05, bh - 0.04, 0.04 + dz, px, py, z - 0.02 - dz / 2, rot=RR("Z", rng.uniform(-0.025, 0.025)), bevel=0.012, seg=2, color=c)
                if rng.random() < 0.3:                                                    # a chipped corner: a small dark notch
                    rbc(it, "stain", 0.13, 0.1, 0.01, px + rng.choice((-1, 1)) * (bw / 2 - 0.08), py + rng.choice((-1, 1)) * (bh / 2 - 0.06), z - 0.075, color="#4f4a44")
            x += bw + rng.uniform(0.0, 0.03)
        y += bh + 0.03; row += 1


def peelpatch():
    """Paint peeled off an old wall: a ragged bay of bare plaster with hairline cracks, an inner window of old brickwork, a satellite patch, the paint
    skin's thick cut edge with a shadow ring, curling flakes of different lengths and plaster crumbs."""
    it = Item("PeelPatch"); rng = random.Random(41)
    outline = blob_pts(0, 0, 1.9, 2.4, rng, n=44, noise=.34, harmonics=7)
    sat_c = (1.9, -1.9)
    sat = blob_pts(sat_c[0], sat_c[1], 0.62, 0.5, rng, n=22, noise=.3, harmonics=4)
    rpoly(it, "stain", [(x * 1.13, y * 1.1) for x, y in outline], -0.03, 0.008, "#c8c2b0")
    rpoly(it, "stain", [(x * 1.2 - 0.2 * 1.13 + 0.2, y * 1.2) for x, y in sat], -0.03, 0.008, "#c8c2b0")
    rpoly(it, "tint", [(x * 1.04, y * 1.04) for x, y in outline], -0.038, 0.014)
    rpoly(it, "tint", [((x - sat_c[0]) * 1.1 + sat_c[0], (y - sat_c[1]) * 1.1 + sat_c[1]) for x, y in sat], -0.038, 0.014)
    rpoly(it, "stain", outline, -0.056, 0.01, "#cdc4ad")
    rpoly(it, "stain", sat, -0.056, 0.01, "#c4baa2")
    rring(it, "stain", outline, [(x * 0.93, y * 0.93) for x, y in outline], -0.062, 0.006, "#8d8672")
    rring(it, "stain", sat, [(sat_c[0] + (x - sat_c[0]) * 0.9, sat_c[1] + (y - sat_c[1]) * 0.9) for x, y in sat], -0.062, 0.006, "#8d8672")
    for k in range(9):                                                                                  # hairline cracks in the bare plaster
        a = rng.uniform(0, math.tau)
        path = crack_path((math.cos(a) * 0.5, math.sin(a) * 0.6), a, rng.uniform(0.5, 1.2), rng, 0.2, 0.55)
        rpoly(it, "stain", ribbon_pts(path, [0.03] * len(path)), -0.068, 0.004, "#8f8878")
    bed = blob_pts(0.15, -0.25, 1.1, 1.3, rng, n=34, noise=.3, harmonics=6)
    rpoly(it, "stain", bed, -0.07, 0.01, "#6f6b64")                                                     # dark mortar bed
    _brick_wall(it, rng, 0.15, -0.25, 1.18, 1.38, -0.075)
    for i in range(0, len(outline)):                                                                    # curling flakes along the cut edge
        if rng.random() < 0.5:
            continue
        x, y = outline[i]
        ang = math.atan2(y, x)
        L = rng.choice((0.2, 0.3, 0.45, 0.7, 0.9)) * rng.uniform(0.8, 1.2)
        rbc(it, "tint", L, rng.uniform(0.14, 0.3), 0.025, x * 1.03, y * 1.03, -0.07 - rng.uniform(0, 0.05),
            rot=RR("Z", ang + math.pi / 2 + rng.uniform(-0.6, 0.6)) @ RR("X", rng.uniform(0.15, 1.0)), bevel=0.006)
    for _ in range(18):                                                                                 # crumbs on the bricks and around
        x, y = rng.uniform(-1.5, 1.7), rng.uniform(-2.2, 1.5)
        rbc(it, "tint", rng.uniform(.05, .13), rng.uniform(.04, .1), rng.uniform(.02, .05), x, y, -0.1, rot=RR("Z", rng.uniform(0, 3)))
    return it


def paintblister():
    """Blistered paint: clusters of low irregular domes (some elongated, a few with a wrinkled lip), burst blisters with a torn, curled flap and a dark
    crater, flecks of paint around, a faint damp halo under the cluster."""
    it = Item("PaintBlister"); rng = random.Random(43)
    rpoly(it, "stain", blob_pts(0, 0, 2.6, 2.0, rng, n=44, noise=.3, harmonics=6), -0.03, 0.006, "#d9d7c5")
    rpoly(it, "stain", blob_pts(-0.1, -0.1, 2.0, 1.5, rng, n=40, noise=.34, harmonics=6), -0.036, 0.006, "#d0cdb9")
    centres = [(rng.uniform(-1.6, 1.6), rng.uniform(-1.1, 1.1)) for _ in range(5)]
    spots = []
    for _ in range(220):
        c = rng.choice(centres)
        x, y = c[0] + rng.gauss(0, 0.75), c[1] + rng.gauss(0, 0.55)
        if (x / 2.4) ** 2 + (y / 1.8) ** 2 > 1:
            continue
        r = rng.choice((0.07, 0.1, 0.14, 0.2, 0.28, 0.4)) * rng.uniform(0.8, 1.2)
        if all(math.hypot(x - sx, y - sy) > (r + sr) * 0.85 for sx, sy, sr in spots):
            spots.append((x, y, r))
    for i, (x, y, r) in enumerate(spots):
        if i % 7 == 0 and r > 0.14:                                                                   # burst blister
            crater = blob_pts(x, y, r * 0.8, r * 0.65, rng, n=14, noise=.3, harmonics=3)
            rpoly(it, "tint", [(x + (px - x) * 1.45, y + (py - y) * 1.45) for px, py in crater], -0.04, 0.05)          # raised lip
            rpoly(it, "stain", crater, -0.095, 0.008, "#4d4a42")
            rbc(it, "tint", r * 1.1, r * 0.6, 0.022, x + r * 0.15, y + r * 0.85, -0.075, rot=RR("X", 0.85) @ RR("Z", rng.uniform(-0.6, 0.6)), bevel=0.006)   # torn flap
        else:
            sq = rng.uniform(0.18, 0.3)                                                                # flat domes: squash 0.18..0.3 of the radius
            ball(it, "tint", r, P(x, y, -0.03), scale=(rng.uniform(0.85, 1.35), sq, rng.uniform(0.85, 1.25)), seg=12, rot=Rx(0) @ Ry(rng.uniform(0, 3)))
            if r > 0.18 and rng.random() < 0.6:                                                        # a wrinkle line across a big dome
                rpoly(it, "stain", ribbon_pts([(x - r * 0.6, y + r * 0.1), (x, y - r * 0.05), (x + r * 0.6, y + r * 0.12)], [0.015, 0.025, 0.015]), -0.03 - r * sq - 0.004, 0.003, "#c4c2ae")
    for _ in range(26):                                                                                 # flecks of fallen paint
        rbc(it, "tint", rng.uniform(.04, .1), rng.uniform(.03, .08), 0.015, rng.uniform(-2.4, 2.4), rng.uniform(-1.8, 1.8), -0.04, rot=RR("Z", rng.uniform(0, 3)))
    return it


ITEMS_A = {"acsplit": acsplit, "acsplitold": acsplitold, "acsplitwide": acsplitwide, "stainbloom": stainbloom, "stainstreaks": stainstreaks, "staintide": staintide,
           "rustdrip": rustdrip, "damplow": damplow, "cracklong": cracklong, "crackstar": crackstar, "crackstep": crackstep, "peelpatch": peelpatch, "paintblister": paintblister}
