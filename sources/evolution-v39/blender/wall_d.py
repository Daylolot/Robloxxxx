"""Wall decor, group D (exec'd last by wall_hero.py): redone/new items after the user's review of 15.11. Overrides earlier definitions of the same keys."""


def _scale_item(it, f):
    for g in it.groups.values():
        bmesh.ops.scale(g.bm, vec=(f, f, f), verts=list(g.bm.verts), space=Matrix.Identity(4))


def _flat_runner(it, cx, cy, s, z, color):
    """Running figure as flat decals: head disc + six limbs, every limb at its own depth."""
    rdisc(it, "stain", 0.085 * s, cx + 0.03 * s, cy + 0.4 * s, z - 0.0006, 0.004, color, seg=14)
    limbs = ((0.11, 0.36, 0.25, 0.0, 0.15), (0.09, 0.3, -0.9, -0.12, 0.17), (0.09, 0.3, 0.8, 0.1, 0.2),
             (0.1, 0.38, -0.55, -0.04, -0.17), (0.1, 0.34, 0.85, 0.12, -0.14), (0.1, 0.28, -0.2, 0.2, -0.3))
    for i, (w, h, ang, dx, dy) in enumerate(limbs):
        rbc(it, "stain", w * s, h * s, 0.004, cx + dx * s, cy + dy * s, z - 0.001 * (i + 2), rot=RR("Z", ang), color=color)


def exitsign():
    """Flat emergency exit sign 3.4 x 1.1 that lies on the wall (6 cm deep): glowing green field, thin white rim, white decals (arrow, door, runner)."""
    it = Item("ExitSign")
    W, H = 3.4, 1.1
    white = "#f4fff6"
    rbc(it, "plastic", W + 0.1, H + 0.1, 0.03, 0, 0, -0.015, bevel=0.012, color="#e9ece8")
    rbc(it, "glow", W - 0.04, H - 0.04, 0.025, 0, 0, -0.04, color="#2fbf74")
    for sx in (-1, 1):
        rbc(it, "stain", 0.03, H - 0.16, 0.004, sx * (W / 2 - 0.1), 0, -0.0535, color=white)
    for sy in (-1, 1):
        rbc(it, "stain", W - 0.2, 0.03, 0.004, 0, sy * (H / 2 - 0.08), -0.0535, color=white)
    rpoly(it, "stain", [(1.28, 0.0), (0.92, 0.3), (0.92, 0.12), (0.6, 0.12), (0.6, -0.12), (0.92, -0.12), (0.92, -0.3)], -0.054, 0.004, white)
    rbc(it, "stain", 0.46, 0.7, 0.004, 0.0, 0.0, -0.0555, color=white)
    rbc(it, "glow", 0.3, 0.58, 0.004, 0.0, -0.03, -0.0565, color="#2fbf74")
    rbc(it, "stain", 0.03, 0.06, 0.004, -0.09, -0.03, -0.0575, color=white)
    _flat_runner(it, -1.0, -0.02, 0.85, -0.054, white)
    return it


def lightswitch():
    """Modern wall switch: square anthracite plate with a thin brushed-metal frame, one wide rocker, a small status LED."""
    it = Item("LightSwitch")
    rbc(it, "metal", 0.92, 0.92, 0.03, 0, 0, -0.015, bevel=0.015, color="#b9bec1")
    rbc(it, "plastic", 0.84, 0.84, 0.045, 0, 0, -0.04, bevel=0.03, seg=3, color="#2e3338")
    rbc(it, "plastic", 0.54, 0.7, 0.04, 0, 0, -0.075, bevel=0.025, seg=3, color="#3c434a", rot=RR("X", 0.04))
    rbc(it, "stain", 0.44, 0.012, 0.01, 0, 0.1, -0.098, color="#565e66")
    rbc(it, "stain", 0.44, 0.012, 0.01, 0, -0.1, -0.098, color="#565e66")
    rdisc(it, "glow", 0.028, 0.0, 0.34, -0.065, 0.012, "#7fe0ff", seg=12)
    return it


def _cam(name, yaw):
    """Small bullet camera: the former model at 0.58 scale plus a wall-plate with four screws, a serial label and a lens glare ring."""
    it = Item(name)
    rbc(it, "metal", 0.8, 0.8, 0.1, 0, 0, -0.05, bevel=0.03, color="#d7dad7")
    rbc(it, "metal", 0.36, 0.36, 0.5, 0, 0, -0.35, bevel=0.1, color="#d7dad7")
    rtube(it, "metal", [(0, 0.0, -0.4), (0, -0.15, -0.85), (0, -0.3, -1.2)], [0.14, 0.13, 0.13], 14, "#c9ccc9")
    ball(it, "metal", 0.22, P(0, -0.35, -1.25), color="#bfc3c0", seg=14)
    pivot = Vector((0.0, -0.35, -1.25))
    fwd = Vector((-math.sin(yaw) * math.cos(0.3), -math.sin(0.3), -math.cos(yaw) * math.cos(0.3)))
    p0 = pivot + fwd * 0.15
    p1 = pivot + fwd * 2.0
    rcyl(it, "plastic", 0.38, tuple(p0), tuple(p1), "#e4e7e4", seg=30, bevel=0.06)
    rcyl(it, "plastic", 0.44, tuple(p1 - fwd * 0.16), tuple(p1), "#d3d7d3", seg=30, bevel=0.03)
    rcyl(it, "dark", 0.31, tuple(p1), tuple(p1 + fwd * 0.09), "#121618", seg=26)
    rcyl(it, "metal", 0.12, tuple(p1 + fwd * 0.08), tuple(p1 + fwd * 0.13), "#2a3a44", seg=18)
    rcyl(it, "metal", 0.2, tuple(p1 + fwd * 0.085), tuple(p1 + fwd * 0.095), "#1b2a33", seg=24)
    upv = Vector((0, 1, 0)) - fwd * Vector((0, 1, 0)).dot(fwd)
    upv.normalize()
    sc = (p0 + p1) / 2 + upv * 0.43
    rbc(it, "plastic", 0.66, 0.05, 1.9, sc.x, sc.y, sc.z, rot=rot_to(fwd), bevel=0.02, color="#d9dcd9")
    for k in range(10):
        a = k / 10 * math.tau
        side = Vector((fwd.z, 0, -fwd.x)).normalized()
        c = p1 + fwd * 0.05 + side * math.cos(a) * 0.33 + upv * math.sin(a) * 0.33
        rcyl(it, "glow", 0.035, tuple(c), tuple(c + fwd * 0.06), "#ff4a3a", seg=8)
    mid = (p0 + p1) / 2 - upv * 0.39
    rbc(it, "paper", 0.5, 0.012, 0.3, mid.x, mid.y, mid.z, rot=rot_to(fwd), color="#f1f1ea")               # serial label under the barrel
    for sx in (-1, 1):
        for sy in (-1, 1):
            rdisc(it, "metal", 0.045, sx * 0.3, sy * 0.3, -0.1, 0.03, "#8a908e", seg=8)
    box(it, "rubber", (0.12, 0.3, 0.1), (0.0, -0.55, -0.1), bevel=0.02, color="#1e2123") if False else None
    _scale_item(it, 0.58)
    return it


def cambullet():
    return _cam("CamBullet", 0.22)


def camcorner():
    """The same camera, aimed 43 degrees along the wall: for a corner mount, so that it looks toward the middle of the room."""
    return _cam("CamCorner", -0.75)


def firealarm():
    """Manual call point, rebuilt so that nothing floats: back plate, body with a SMALL bevel (flat front face reaches +-0.48 x +-0.68), every detail
    sits fully inside that flat face and touches it: label band, window frame with pane, pull strip, flame, key lock, LED, a hammer lying in two clips,
    four tamper screws set inside the corners (domed heads that start ON the face)."""
    it = Item("FireAlarm")
    RED, DEEP = "#c2312c", "#a82723"
    ZF = -0.39                                                                                               # front face of the body (z)
    rbc(it, "plastic", 1.2, 1.6, 0.1, 0, 0, -0.05, bevel=0.04, color=DEEP)                                    # back plate, z 0 .. -0.1
    rbc(it, "plastic", 1.08, 1.5, 0.3, 0, 0, -0.24, bevel=0.06, seg=4, color=RED)                             # body, z -0.09 .. -0.39 (overlaps the plate by 0.01)
    rbc(it, "plastic", 0.64, 0.17, 0.03, 0.0, 0.56, ZF - 0.015, bevel=0.008, color="#f6f1e6")                 # label band on the face
    for k in range(5):
        rbc(it, "stain", 0.05, 0.1, 0.006, -0.2 + k * 0.1, 0.56, ZF - 0.033, color=RED)
    rbc(it, "plastic", 0.86, 0.78, 0.05, 0, 0.03, ZF - 0.025, bevel=0.025, color="#b8272a")                   # window frame, on the face
    rbc(it, "plastic", 0.7, 0.62, 0.03, 0, 0.03, ZF - 0.065, bevel=0.015, color="#e9f1f2")                    # pale pane, sits in the frame
    rbc(it, "stain", 0.7, 0.05, 0.004, 0.0, 0.22, ZF - 0.082, color="#d0dde0")
    rbc(it, "stain", 0.46, 0.08, 0.004, 0.0, -0.17, ZF - 0.082, color="#f0c419")                              # pull strip
    rpoly(it, "stain", [(0.0, 0.3), (-0.12, 0.08), (-0.04, 0.1), (-0.1, -0.08), (0.05, 0.1), (0.0, 0.1), (0.12, 0.0)], ZF - 0.085, 0.004, "#c2312c")
    rpoly(it, "stain", [(0.0, 0.3), (0.12, 0.0), (0.04, 0.1), (0.1, -0.08), (-0.05, 0.1)], ZF - 0.0865, 0.004, "#c2312c")
    rbc(it, "plastic", 0.7, 0.06, 0.07, 0.0, -0.4, ZF - 0.035, bevel=0.015, color="#e7e3d6")                  # lip under the pane, resting on the face
    rdisc(it, "metal", 0.09, 0.32, -0.55, ZF, 0.04, "#a9afac", seg=16)                                       # key lock (back face on the face)
    rbc(it, "dark", 0.025, 0.1, 0.012, 0.32, -0.55, ZF - 0.046, color="#202325")
    rdisc(it, "glow", 0.03, -0.34, -0.49, ZF, 0.025, "#4aff9a", seg=12)                                      # status LED
    # hammer lying horizontally in two clips fixed to the face
    for cx in (-0.17, 0.11):
        rbc(it, "metal", 0.07, 0.13, 0.07, cx, -0.55, ZF - 0.035, bevel=0.012, color="#8f9699")
    rbc(it, "dark", 0.4, 0.05, 0.05, -0.03, -0.55, ZF - 0.075, bevel=0.012, color="#2b3033")                 # handle, on top of the clips
    rbc(it, "metal", 0.1, 0.12, 0.06, -0.2, -0.55, ZF - 0.075, bevel=0.012, color="#b8bcbd")                 # head
    for sx in (-1, 1):                                                                                       # four tamper screws, fully inside the flat face
        for sy in (-1, 1):
            rdisc(it, "metal", 0.05, sx * 0.41, sy * 0.6, ZF, 0.035, "#a9afac", seg=12)
            rbc(it, "dark", 0.07, 0.012, 0.01, sx * 0.41, sy * 0.6, ZF - 0.04, rot=RR("Z", 0.7), color="#3d4244")
    return it


def _bracket(it, x, y, depth, color="#2a2f33"):
    rbc(it, "metal", 0.1, 0.1, depth, x, y - 0.1, -depth / 2, bevel=0.012, color=color)
    rbc(it, "metal", 0.1, 0.55, 0.07, x, y - 0.4, -0.035, bevel=0.012, color=color)
    rbc(it, "metal", 0.07, 0.07, 0.07, x, y - 0.18, -0.18, rot=RR("X", 0.7), color=color)


def _shelf_plank(it, w, d, y, wood="wood_mid", color="#6b4a31", lip=True):
    rbc(it, wood, w, 0.14, d, 0, y, -d / 2, bevel=0.025, color=color)
    if lip:
        rbc(it, wood, w, 0.2, 0.04, 0, y + 0.03, -d + 0.02, bevel=0.01, color=color)
    for x in (-w / 2 + 0.7, w / 2 - 0.7):
        _bracket(it, x, y - 0.07, d)


def _cup(it, x, y, z, s, color="#b8913f", base="#2a1d14"):
    """Trophy cup: stepped plinth with plaque, stem, knop, bowl, handles, rim ring, lid dome."""
    rbc(it, "wood_dark", 0.9 * s, 0.1 * s, 0.9 * s, x, y + 0.05 * s, z, bevel=0.02, color=base)
    rbc(it, "wood_dark", 0.66 * s, 0.1 * s, 0.66 * s, x, y + 0.15 * s, z, bevel=0.02, color=base)
    rbc(it, "brass", 0.4 * s, 0.07 * s, 0.01, x, y + 0.1 * s, z - 0.46 * s, color="#d9c98a")
    rcyl(it, "brass", 0.22 * s, (x, y + 0.2 * s, z), (x, y + 0.3 * s, z), color, seg=26, r2=0.12 * s)
    rcyl(it, "brass", 0.06 * s, (x, y + 0.3 * s, z), (x, y + 0.62 * s, z), color, seg=14)
    ball(it, "brass", 0.11 * s, P(x, y + 0.46 * s, z), color=color, seg=14)
    rcyl(it, "brass", 0.14 * s, (x, y + 0.62 * s, z), (x, y + 1.12 * s, z), color, seg=28, r2=0.34 * s)
    torus(it, "brass", 0.34 * s, 0.025 * s, P(x, y + 1.12 * s, z), color=color, seg=28, minor=6)
    for sx in (-1, 1):
        rtube(it, "brass", [(x + sx * 0.3 * s, y + 1.0 * s, z), (x + sx * 0.5 * s, y + 1.0 * s, z), (x + sx * 0.52 * s, y + 0.8 * s, z), (x + sx * 0.3 * s, y + 0.72 * s, z)], [0.03 * s] * 4, 8, color)


def shelfdecor():
    """Shelf A: dark wood plank; a big trophy cup, an hourglass, a framed photo leaning, a small globe on a ring stand, a stack of papers."""
    it = Item("ShelfDecor"); rng = random.Random(82)
    W, D = 4.4, 1.0
    _shelf_plank(it, W, D, 0.0, "wood_dark", "#4a2f1e")
    _cup(it, 1.5, 0.07, -0.5, 1.0)
    rbc(it, "wood_dark", 1.0, 1.3, 0.07, 0.35, 0.8, -0.3, rot=RR("X", 0.2), bevel=0.015, color="#2a1b12")
    rbc(it, "paper", 0.8, 1.1, 0.03, 0.35, 0.8, -0.34, rot=RR("X", 0.2), color="#d9ccb0")
    rbc(it, "stain", 0.8, 0.45, 0.012, 0.35, 0.55, -0.37, rot=RR("X", 0.2), color="#5f8a9a")
    rbc(it, "stain", 0.8, 0.3, 0.012, 0.35, 0.95, -0.37, rot=RR("X", 0.2), color="#d9b36a")
    ball(it, "paper", 0.14, P(0.35, 0.8, -0.37), color="#e0c9a8", seg=10)
    rcyl(it, "wood_dark", 0.26, (-0.8, 0.07, -0.5), (-0.8, 0.14, -0.5), "#2a1b12", seg=20)
    rcyl(it, "ceramic", 0.2, (-0.8, 0.14, -0.5), (-0.8, 0.5, -0.5), "#efe9d8", seg=20, r2=0.03)
    rcyl(it, "ceramic", 0.03, (-0.8, 0.5, -0.5), (-0.8, 0.86, -0.5), "#efe9d8", seg=20, r2=0.2)
    rcyl(it, "wood_dark", 0.26, (-0.8, 0.86, -0.5), (-0.8, 0.93, -0.5), "#2a1b12", seg=20)
    for sx in (-1, 1):
        rpost(it, "metal", 0.012, 0.14, 0.93, -0.8 + sx * 0.22, -0.5, seg=6, color="#b8913f")
    rcyl(it, "brass", 0.2, (-1.7, 0.07, -0.5), (-1.7, 0.13, -0.5), "#b8913f", seg=22, r2=0.17)
    rcyl(it, "brass", 0.035, (-1.7, 0.13, -0.5), (-1.7, 0.45, -0.5), "#b8913f", seg=8)
    ball(it, "plastic_blue", 0.38, P(-1.7, 0.85, -0.5), color="#2f6fb0", seg=24)
    torus(it, "brass", 0.44, 0.022, P(-1.7, 0.85, -0.5), color="#b8913f", seg=28, minor=6, rot=Rx(0.4))
    for k in range(5):
        rbc(it, "paper", 0.9, 0.05, 0.65, -2.0 + 0.0, 0.14 + k * 0.055, -0.5, rot=RR("Y", rng.uniform(-0.12, 0.12)), color="#efe9d8")
    return it


def shelfdecorb():
    """Shelf B: white floating shelf with black brackets; a retro round desk clock, a transistor radio, a small framed certificate, a candle jar and
    a row of three bound reports leaning on a metal bookend."""
    it = Item("ShelfDecorB"); rng = random.Random(83)
    W, D = 4.0, 0.95
    _shelf_plank(it, W, D, 0.0, "plastic_white", "#ece8dd", lip=False)
    # clock
    rdisc(it, "metal", 0.46, 1.4, 0.74, -0.35, 0.16, "#b8bcbd", bevel=0.03, seg=36)
    rdisc(it, "paper", 0.4, 1.4, 0.74, -0.5, 0.012, "#f1ecdc", seg=36)
    for k in range(12):
        a = k / 12 * math.tau
        rbc(it, "stain", 0.03, 0.07 if k % 3 == 0 else 0.04, 0.006, 1.4 + math.sin(a) * 0.34, 0.74 + math.cos(a) * 0.34, -0.512, rot=RR("Z", -a), color="#2c3032")
    rbc(it, "dark", 0.02, 0.26, 0.008, 1.4 + 0.05, 0.74 + 0.11, -0.52, rot=RR("Z", 0.5), color="#1d2022")
    rbc(it, "dark", 0.016, 0.32, 0.008, 1.4 - 0.1, 0.74 + 0.08, -0.525, rot=RR("Z", -1.2), color="#1d2022")
    rbc(it, "metal", 0.5, 0.06, 0.3, 1.4, 0.07, -0.35, color="#9aa1a5")                                   # clock foot
    # radio
    rbc(it, "plastic", 1.0, 0.62, 0.4, 0.2, 0.45, -0.45, bevel=0.07, seg=3, color="#7a4a2a")
    rdisc(it, "paper", 0.17, 0.0, 0.46, -0.66, 0.02, "#e2d6b8", seg=22)
    rdisc(it, "paper", 0.11, 0.42, 0.46, -0.66, 0.02, "#e2d6b8", seg=18)
    rbc(it, "dark", 0.34, 0.015, 0.01, 0.05, 0.28, -0.66, color="#3a2414")
    rbc(it, "stain", 0.3, 0.04, 0.008, 0.1, 0.62, -0.665, color="#2b1a0e")
    rbc(it, "metal", 0.02, 0.55, 0.02, 0.62, 0.9, -0.4, rot=RR("Z", -0.6), color="#b8bcbd")                # antenna
    # candle jar
    rcyl(it, "ceramic", 0.2, (-0.75, 0.07, -0.5), (-0.75, 0.42, -0.5), "#e8e1d0", seg=24, r2=0.21)
    rcyl(it, "paper", 0.18, (-0.75, 0.3, -0.5), (-0.75, 0.38, -0.5), "#f5efdc", seg=22)
    rcyl(it, "dark", 0.012, (-0.75, 0.38, -0.5), (-0.75, 0.45, -0.5), "#1d2022", seg=6)
    rdisc(it, "glow", 0.02, -0.75, 0.46, -0.5, 0.02, "#ffd27a", seg=8)
    # certificate frame
    rbc(it, "metal", 0.9, 0.7, 0.05, -1.55, 0.42, -0.3, rot=RR("X", 0.18), bevel=0.01, color="#b8913f")
    rbc(it, "paper", 0.78, 0.58, 0.03, -1.55, 0.42, -0.33, rot=RR("X", 0.18), color="#efe6cf")
    for k in range(4):
        rbc(it, "stain", 0.5 - k * 0.06, 0.02, 0.008, -1.55, 0.58 - k * 0.1, -0.35, rot=RR("X", 0.18), color="#7a6a4a")
    # reports leaning on a bookend
    rbc(it, "metal", 0.05, 0.5, 0.5, 0.95, 0.32, -0.55, bevel=0.01, color="#4b5356")
    rbc(it, "metal", 0.5, 0.05, 0.5, 1.12, 0.095, -0.55, color="#4b5356")
    for k, c in enumerate(("#2c5270", "#8a2c2c", "#3a6246")):
        rbc(it, "paper", 0.07, 0.62, 0.45, 0.82 - k * 0.1, 0.38, -0.5, bevel=0.008, color=c)
    return it


def shelfdecorc():
    """Shelf C (awards): pale oak plank; three trophies of different heights (cup, star plaque on a stand, small statuette), a medal on a ribbon draped
    over a peg, a mini flag on a pole."""
    it = Item("ShelfDecorC"); rng = random.Random(84)
    W, D = 4.2, 0.9
    _shelf_plank(it, W, D, 0.0, "wood_light", "#c9a46b")
    _cup(it, -1.4, 0.07, -0.45, 0.78, "#c0c4c6", "#3a2a1c")                                                # silver cup
    # star plaque on a stand
    rbc(it, "wood_dark", 0.7, 0.12, 0.5, -0.2, 0.13, -0.45, bevel=0.02, color="#3a2a1c")
    pts = []
    for k in range(10):
        r = 0.42 if k % 2 == 0 else 0.18
        a = k / 10 * math.tau + math.pi / 2
        pts.append((-0.2 + math.cos(a) * r, 0.88 + math.sin(a) * r))
    rpoly(it, "brass", pts, -0.4, 0.05, "#d6b04a")
    rcyl(it, "brass", 0.04, (-0.2, 0.19, -0.45), (-0.2, 0.55, -0.45), "#8f7a3a", seg=8)
    # statuette: figure with raised arm on a round base
    rcyl(it, "wood_dark", 0.3, (0.95, 0.07, -0.45), (0.95, 0.2, -0.45), "#3a2a1c", seg=26)
    rcyl(it, "brass", 0.1, (0.95, 0.2, -0.45), (0.95, 0.75, -0.45), "#c9a24a", seg=14, r2=0.07)
    ball(it, "brass", 0.1, P(0.95, 0.86, -0.45), color="#c9a24a", seg=12)
    rtube(it, "brass", [(0.95, 0.68, -0.45), (1.12, 0.84, -0.45), (1.2, 1.05, -0.45)], [0.035, 0.03, 0.03], 8, "#c9a24a")
    rdisc(it, "brass", 0.1, 1.2, 1.12, -0.45, 0.03, "#e0c26a", seg=16)
    # mini flag
    rpost(it, "metal", 0.012, 0.07, 1.3, -2.0, -0.6, seg=6, color="#b8bcbd")
    rbc(it, "paper", 0.5, 0.3, 0.012, -1.73, 1.15, -0.6, color="#2c5aa0")
    rbc(it, "paper", 0.5, 0.06, 0.014, -1.73, 1.15, -0.6, color="#f1f1ea")
    return it


def _cactus(it, x, y, z, s=1.0):
    """Columnar cactus with ribs (a ring of slim ellipsoids), two arms, areoles with spines, in a terracotta pot with pebbles."""
    rcyl(it, "paint", 0.3 * s, (x, y, z), (x, y + 0.34 * s, z), "#b5653c", seg=26, r2=0.38 * s, bevel=0.015)
    torus(it, "paint", 0.38 * s, 0.035 * s, P(x, y + 0.34 * s, z), color="#a45a35", seg=26, minor=8)
    rcyl(it, "dark", 0.33 * s, (x, y + 0.3 * s, z), (x, y + 0.33 * s, z), "#3a2a1f", seg=22)
    for k in range(11):
        a = k / 11 * math.tau
        ball(it, "stain", 0.035 * s, P(x + math.cos(a) * 0.16 * s, y + 0.345 * s, z + math.sin(a) * 0.16 * s), scale=(1, 0.5, 1), color="#bfb7a8", seg=6)
    ribs = 9
    H = 1.55 * s
    for k in range(ribs):
        a = k / ribs * math.tau
        rx, rz = math.cos(a) * 0.17 * s, math.sin(a) * 0.17 * s
        ball(it, "leaf", 0.2 * s, P(x + rx, y + 0.34 * s + H * 0.5, z + rz), scale=(0.55, 0.55, 0.52 * H / (0.2 * s)), color="#3f8a52" if k % 2 else "#4c9a5c", seg=10)
    ball(it, "leaf", 0.3 * s, P(x, y + 0.34 * s + H * 0.5, z), scale=(0.7, 0.7, 0.5 * H / (0.3 * s)), color="#3a7f4c", seg=16)
    ball(it, "leaf", 0.24 * s, P(x, y + 0.34 * s + H, z), scale=(1, 1, 0.8), color="#4c9a5c", seg=14)
    for ax, ay, dirx in ((0.3, 0.75, 1), (-0.28, 1.0, -1)):                                               # arms: out, then up
        pts = [(x + dirx * 0.2 * s, y + (0.34 + ay) * s, z), (x + dirx * (ax + 0.15) * s * 1.2, y + (0.34 + ay) * s, z), (x + dirx * (ax + 0.42) * s, y + (0.34 + ay + 0.25) * s, z), (x + dirx * (ax + 0.45) * s, y + (0.34 + ay + 0.6) * s, z)]
        rtube(it, "leaf", pts, [0.12 * s, 0.11 * s, 0.1 * s, 0.085 * s], 10, "#4c9a5c")
        ball(it, "leaf", 0.09 * s, P(*pts[-1]), color="#56a866", seg=10)
    rng = random.Random(5)
    for _ in range(46):                                                                                    # spines in clusters
        a = rng.uniform(0, math.tau)
        h = rng.uniform(0.5, 1.8) * s
        px, pz = x + math.cos(a) * 0.3 * s, z + math.sin(a) * 0.3 * s
        rcyl(it, "stain", 0.004, (px, y + 0.34 * s + h, pz), (px + math.cos(a) * 0.12 * s, y + 0.34 * s + h + 0.05 * s, pz + math.sin(a) * 0.12 * s), "#efe6c8", seg=4, r2=0.0)


def shelfbooks():
    """Shelf with a row of books, a book lying flat, a detailed cactus (replaces the former bush) and no mug."""
    it = Item("ShelfBooks"); rng = random.Random(81)
    W, D = 5.0, 1.1
    _shelf_plank(it, W, D, 0.0, "wood_mid", "#6b4a31")
    pal = ["#7a2c2c", "#2c5270", "#3a6246", "#c4a85c", "#583e6e", "#d6ceb8", "#464a54", "#966038", "#26383f", "#b07a4c"]
    x = W / 2 - 0.3
    for i in range(14):
        w = rng.uniform(0.12, 0.28); h = rng.uniform(0.9, 1.5)
        if x - w < -0.2:
            break
        rbc(it, "paper", w, h, 0.62, x - w / 2, 0.12 + h / 2, -0.55, bevel=0.012, color=rng.choice(pal))
        rbc(it, "stain", w * 0.7, 0.07, 0.02, x - w / 2, 0.12 + h * 0.65, -0.87, color="#e7dfc8")
        x -= w + 0.01
    rbc(it, "paper", 0.95, 0.2, 0.7, -0.9, 0.22, -0.55, rot=RR("Y", 0.1), bevel=0.01, color="#a64a2a")
    rbc(it, "paper", 0.85, 0.16, 0.62, -0.9, 0.4, -0.55, rot=RR("Y", -0.1), bevel=0.01, color="#2c5270")
    _cactus(it, -2.0, 0.07, -0.55, 0.85)
    return it


def handdryer():
    """Modern jet hand dryer, no label: soft white shell with side vents, a recessed dark hand slot with an IR sensor, brushed bottom grille, a
    thin metal back plate and a status LED."""
    it = Item("HandDryer")
    rbc(it, "metal", 1.1, 2.3, 0.04, 0, 0, -0.02, bevel=0.012, color="#9aa1a5")
    rbc(it, "plastic", 1.0, 2.2, 0.62, 0, 0, -0.35, bevel=0.2, seg=6, color="#f2f2ee")
    rbc(it, "plastic", 0.78, 1.2, 0.2, 0, 0.18, -0.63, bevel=0.1, seg=4, color="#dedfda")                   # hand well surround
    rbc(it, "dark", 0.52, 0.86, 0.22, 0, 0.18, -0.65, bevel=0.05, seg=3, color="#16191b")                   # the slot
    for sx in (-1, 1):
        rbc(it, "metal", 0.02, 0.74, 0.02, sx * 0.19, 0.18, -0.76, color="#4a5256")                       # jet rails
    rdisc(it, "glow", 0.035, 0.0, 0.7, -0.64, 0.02, "#7fe0ff", seg=14)                                   # IR sensor window
    rdisc(it, "dark", 0.05, 0.0, 0.7, -0.62, 0.012, "#16191b", seg=14)
    for k in range(9):
        rbc(it, "dark", 0.6, 0.025, 0.04, 0, -0.62 - k * 0.045, -0.66, color="#2a2f33")                     # bottom grille slots
    rdisc(it, "glow", 0.022, 0.32, 0.7, -0.64, 0.012, "#4aff9a", seg=10)
    return it


ITEMS_D = {"camcorner": camcorner, "exitsign": exitsign, "lightswitch": lightswitch, "cambullet": cambullet, "firealarm": firealarm, "shelfdecor": shelfdecor,
           "shelfdecorb": shelfdecorb, "shelfdecorc": shelfdecorc, "shelfbooks": shelfbooks, "handdryer": handdryer}


# ---------------------------------------------------------------- hero items for OfficeDecor (floor items; origin = floor centre, front = -Y)
def watercooler():
    """Water cooler 1.45 x 1.35 x 6.3: pedestal base with vent grille, double cabinet doors, hot/cold taps with levers and indicator lamps, drip tray
    with a steel grille, cup dispenser with a stack of cups, control panel, a 19 L bottle with ribs, handle neck and a cap."""
    it = Item("WaterCooler")
    box(it, "plastic_white", (1.5, 1.4, 0.2), (0, 0, 0), bevel=0.05, color="#b8bec2")
    box(it, "plastic_white", (1.44, 1.32, 3.0), (0, 0, 0.2), bevel=0.12, seg=4, color="#eceef0")
    box(it, "plastic_gray", (1.1, 0.04, 1.0), (0, -0.68, 0.42), bevel=0.02, color="#cdd2d6")                                # cabinet doors
    box(it, "plastic_gray", (0.012, 0.05, 1.0), (0, -0.69, 0.42), color="#8f979c")
    for sx in (-0.07, 0.07):
        box(it, "metal", (0.025, 0.04, 0.3), (sx, -0.72, 0.8), bevel=0.008, color="#9aa1a5")
    for k in range(6):
        box(it, "metal_dark", (0.8, 0.025, 0.03), (0, -0.7, 1.42 + k * 0.045), color="#6d7578")
    box(it, "plastic_gray", (1.12, 0.05, 1.05), (0, -0.68, 1.95), bevel=0.03, color="#2e3338")                              # tap panel (dark)
    box(it, "plastic_gray", (0.9, 0.12, 0.08), (0, -0.72, 1.62), bevel=0.02, color="#9aa1a5")                              # drip tray shelf
    box(it, "metal", (0.9, 0.3, 0.02), (0, -0.82, 1.66), color="#b8bcbe")
    for sx, col in ((-0.28, "#2f6fb0"), (0.28, "#c0392b")):                                                                 # taps
        cyl(it, "metal", 0.09, 0.34, (sx, -0.72, 2.2), rot=Rx(math.pi / 2), seg=16, bevel=0.015)
        cyl(it, "metal", 0.055, 0.16, (sx, -1.0, 2.14), seg=12)
        box(it, "plastic_gray", (0.1, 0.07, 0.34), (sx, -1.05, 2.4), bevel=0.02, color=col)
        cyl(it, "glow", 0.035, 0.02, (sx, -0.71, 1.95), rot=Rx(math.pi / 2), seg=10, color="#7fe0ff" if sx < 0 else "#ffb04a")
    box(it, "plastic_gray", (0.5, 0.03, 0.22), (0, -0.7, 2.62), bevel=0.01, color="#1b1f22")                              # status window
    box(it, "glow", (0.3, 0.015, 0.06), (0, -0.72, 2.62), color="#7fe0ff")
    box(it, "plastic_white", (1.28, 1.16, 0.16), (0, 0, 3.2), bevel=0.05, color="#dde0e2")
    cyl(it, "plastic_white", 0.56, 0.2, (0, 0, 3.36), r2=0.44, seg=36, color="#dde0e2")
    # 19 L bottle, upside down: short neck with a cap at the bottom, rounded shoulder, a ribbed cylinder, domed bottom on top, a grip groove
    lathe(it, "glass_blue", [(0.0, 3.56), (0.2, 3.56), (0.22, 3.7), (0.3, 3.9), (0.52, 4.15), (0.62, 4.5), (0.64, 4.8), (0.64, 6.2), (0.6, 6.5), (0.46, 6.72), (0.22, 6.84), (0.0, 6.86)], (0, 0, 0), 44, color="#a9d3ec")
    for k in range(3):
        cyl(it, "glass_blue", 0.655, 0.05, (0, 0, 5.0 + k * 0.5), seg=44, color="#8fc2e2")
    cyl(it, "glass_blue", 0.66, 0.06, (0, 0, 6.1), seg=44, color="#8fc2e2")
    cyl(it, "plastic_blue", 0.25, 0.14, (0, 0, 3.56), seg=24, color="#2f6fb0", bevel=0.025)
    lathe(it, "glass_blue", [(0.0, 4.55), (0.58, 4.55), (0.6, 4.8), (0.6, 5.55), (0.0, 5.55)], (0, 0, 0), 40, color="#7db7e0")
    cyl(it, "plastic_gray", 0.2, 1.3, (0.88, 0, 1.0), seg=22, bevel=0.03, color="#d6dadd")                                  # cup dispenser
    cyl(it, "metal_dark", 0.22, 0.06, (0.88, 0, 2.3), seg=22)
    for k in range(5):
        lathe(it, "paper", [(0.0, 0), (0.08, 0), (0.13, 0.3), (0.0, 0.3)], (0.88, 0, 2.38 + k * 0.1), 16, color="#f2efe6")
    ball(it, "plastic_blue", 0.045, (0.0, -0.69, 2.9), seg=10, color="#6cc1ff")
    return it


def coatrack():
    """Coat stand 1.8 wide x 7 high: round weighted base with a chrome ring, turned pole with a brass collar, six hooks on two tiers with ball ends, and
    three garments: a long wool coat (collar, lapels, belt, buttons, cuffs), a quilted jacket with a hood, a knitted scarf; plus a canvas bag and a hat."""
    it = Item("CoatRack")
    cyl(it, "wood_dark", 0.8, 0.14, (0, 0, 0), seg=40, bevel=0.06, color="#2b2118")
    torus(it, "metal", 0.74, 0.03, (0, 0, 0.15), color="#b8bcbd", seg=40, minor=8)
    cyl(it, "wood_dark", 0.3, 0.4, (0, 0, 0.14), r2=0.14, seg=26, color="#2b2118")
    cyl(it, "wood_mid", 0.1, 6.3, (0, 0, 0.5), r2=0.075, seg=22, color="#5a3a24")
    cyl(it, "brass", 0.13, 0.1, (0, 0, 2.4), seg=22, color="#b8913f")
    cyl(it, "brass", 0.12, 0.1, (0, 0, 5.2), seg=22, color="#b8913f")
    ball(it, "wood_dark", 0.17, (0, 0, 6.95), scale=(1, 1, 1.15), seg=16, color="#2b2118")
    hooks = []
    for tier, zh, off in ((0, 5.9, 0.0), (1, 5.2, math.pi / 3)):
        for k in range(3):
            a = off + k * math.tau / 3
            d = Vector((math.cos(a), math.sin(a), 0))
            cyl(it, "metal", 0.05, 0.62, (d.x * 0.08, d.y * 0.08, zh), seg=10, rot=Rz(a) @ Ry(math.pi / 2))
            ball(it, "metal", 0.075, (d.x * 0.7, d.y * 0.7, zh), seg=12)
            cyl(it, "metal", 0.04, 0.2, (d.x * 0.64, d.y * 0.64, zh), seg=8)
            hooks.append((a, zh))

    def garment(a, zt, body, trim, long_, wide=1.0, hood=False):
        d = Vector((math.cos(a), math.sin(a), 0))
        px, py = d.x * 0.72, d.y * 0.72
        side = Vector((-d.y, d.x, 0))
        L = 3.0 if long_ else 2.1
        # hanger bar and hook
        box(it, "metal_dark", (0.75 * wide, 0.05, 0.05), (px, py, zt - 0.2), bevel=0.012, rot=Rz(a + math.pi / 2), color="#2b2f33")
        # torso: loft downwards with an elliptic section (wide, thin), flaring to the hem
        pts = [(px, py, zt - 0.1), (px, py, zt - 0.4), (px, py, zt - 1.0), (px, py, zt - 0.5 - L * 0.55), (px, py, zt - L)]
        rad = [0.32 * wide, 0.4 * wide, 0.38 * wide, 0.44 * wide, 0.5 * wide]
        tube(it, "fabric", [tuple(Vector(p)) for p in pts], rad, 22, body, squash=(1.0, 0.55), caps=True)
        # sleeves: angled tubes down and slightly out
        for s in (-1, 1):
            p0 = Vector((px, py, zt - 0.42)) + side * (0.42 * wide * s)
            p1 = p0 + side * (0.12 * s) + Vector((0, 0, -0.9)) + d * 0.05
            p2 = p1 + side * (0.04 * s) + Vector((0, 0, -0.9)) + d * 0.1
            tube(it, "fabric", [tuple(p0), tuple(p1), tuple(p2)], [0.16 * wide, 0.14 * wide, 0.12 * wide], 12, body, squash=(1.0, 0.9), caps=True)
            cyl(it, "fabric", 0.125, 0.12, (p2.x, p2.y, p2.z - 0.04), seg=12, color=trim)
        # collar + lapel V, belt, buttons, pocket flaps
        cyl(it, "fabric", 0.36 * wide, 0.12, (px, py, zt - 0.3), r2=0.3 * wide, seg=20, color=trim, rot=None)
        for s in (-1, 1):
            box(it, "fabric", (0.1, 0.05, 0.7), (px + side.x * 0.12 * s - d.x * 0.0, py + side.y * 0.12 * s, zt - 0.9), color=trim, rot=Rz(a + math.pi / 2) @ Ry(s * 0.35), bevel=0.01)
        if long_:
            box(it, "fabric", (0.9 * wide, 0.62, 0.12), (px + d.x * 0.0, py + d.y * 0.0, zt - 1.75), bevel=0.03, color=trim, rot=Rz(a + math.pi / 2))
        for k in range(4 if long_ else 3):
            ball(it, "plastic_gray", 0.03, (px - d.x * 0.22, py - d.y * 0.22, zt - 0.85 - k * 0.38), seg=8, color="#16191b")
        for s in (-1, 1):
            box(it, "fabric", (0.26, 0.04, 0.14), (px - d.x * 0.22 + side.x * 0.22 * s, py - d.y * 0.22 + side.y * 0.22 * s, zt - 1.7 - (0.6 if long_ else 0)), color=trim, rot=Rz(a + math.pi / 2))
        if hood:
            ball(it, "fabric", 0.24, (px + d.x * 0.18, py + d.y * 0.18, zt - 0.28), scale=(1, 0.7, 0.9), seg=14, color=trim)
    garment(hooks[0][0], hooks[0][1] + 0.1, "#3d4650", "#2b323a", True, 1.0)
    garment(hooks[2][0], hooks[2][1] + 0.1, "#7a4a2d", "#5a3420", False, 0.9, hood=True)
    # scarf on the lower tier, bag on another hook, hat on the top knob
    a, zh = hooks[4]
    d = Vector((math.cos(a), math.sin(a), 0))
    for k in range(2):
        tube(it, "fabric", [(d.x * 0.7, d.y * 0.7, zh + 0.1), (d.x * 0.76, d.y * 0.76, zh - 0.5), (d.x * 0.74, d.y * 0.74, zh - 1.3 - 0.3 * k)], [0.13, 0.12, 0.11], 10, "#a8362e" if k == 0 else "#d8d3c4", squash=(1.0, 0.45))
    a, zh = hooks[3]
    d = Vector((math.cos(a), math.sin(a), 0))
    tube(it, "fabric", [(d.x * 0.7, d.y * 0.7, zh + 0.05), (d.x * 0.9, d.y * 0.9, zh - 0.35), (d.x * 0.9, d.y * 0.9, zh - 0.9)], [0.02, 0.02, 0.02], 8, "#2b2f33")
    box(it, "fabric", (0.7, 0.28, 0.75), (d.x * 0.92, d.y * 0.92, zh - 1.65), bevel=0.05, color="#8a7a5a", rot=Rz(math.atan2(d.y, d.x) + math.pi / 2))
    cyl(it, "fabric", 0.34, 0.2, (0, 0, 7.05), r2=0.3, seg=26, color="#3a3f46", bevel=0.04)
    cyl(it, "fabric", 0.5, 0.04, (0, 0, 7.02), seg=26, color="#3a3f46")
    return it


ITEMS_D.update({"watercooler": watercooler, "coatrack": coatrack})


def filingcabinet():
    """Filing cabinet as before but without the round brass lock cylinder at the top (the user asked to remove it)."""
    it = Item("FilingCabinet")
    W, D, H = 1.6, 2.0, 4.3
    box(it, "metal_dark", (W - 0.08, D - 0.08, 0.2), (0, 0, 0), bevel=0.03)
    box(it, "enamel", (W, D, H - 0.2), (0, 0, 0.2), bevel=0.06, seg=3)
    dh = (H - 0.5) / 4
    for k in range(4):
        z = 0.32 + k * dh
        box(it, "enamel", (W - 0.18, 0.07, dh - 0.07), (0, -D / 2 - 0.01, z), bevel=0.03, color="#7b858c")
        box(it, "metal_dark", (0.8, 0.05, 0.06), (0, -D / 2 - 0.08, z + dh - 0.35), bevel=0.02)
        for sx in (-0.38, 0.38):
            box(it, "metal_dark", (0.06, 0.07, 0.06), (sx, -D / 2 - 0.06, z + dh - 0.35))
        box(it, "paper", (0.5, 0.012, 0.18), (0, -D / 2 - 0.047, z + dh - 0.7), color="#efe6d2")
        box(it, "plastic_gray", (0.34, 0.012, 0.04), (0, -D / 2 - 0.05, z + dh - 0.64), color="#4a4f57")
    return it


def docpile():
    """Carelessly left documents on top of a cabinet: eleven A4 sheets at different heights and angles (corners curled, printed text lines, a stamp),
    a half-open manila folder with a tab, a clipped bundle with a metal bulldog clip, a pen. Footprint about 1.9 x 1.4, height 0.5. Origin = centre of
    the bottom (the cabinet top), front -Y."""
    it = Item("DocPile"); rng = random.Random(91)
    sheet_cols = ["#f1ede2", "#d9e2ea", "#f4eed0", "#e6d9d2"]
    for i in range(11):
        x, y = rng.uniform(-0.55, 0.55), rng.uniform(-0.35, 0.35)
        z = 0.012 + i * 0.022
        a = rng.uniform(-0.7, 0.7)
        box(it, "paper", (0.62, 0.86, 0.008), (x, y, z), bevel=0.004, rot=Rz(a) @ Rx(rng.uniform(-0.03, 0.03)), color=rng.choice(sheet_cols))
        for k in range(7):                                                                           # printed text lines
            ox = rng.uniform(-0.04, 0.04)
            wlen = rng.uniform(0.28, 0.5)
            box(it, "stain", (wlen, 0.012, 0.0015), (x + ox * math.cos(a), y + (0.3 - k * 0.09), z + 0.0055), rot=Rz(a), color="#6a6e70")
    # curled loose sheet hanging a little over the edge
    box(it, "paper", (0.6, 0.8, 0.008), (0.75, -0.1, 0.07), rot=Rz(0.5) @ Ry(0.28), bevel=0.004, color="#f4f1e8")
    # manila folder, half open
    box(it, "paper", (0.7, 0.92, 0.012), (-0.5, 0.1, 0.27), rot=Rz(0.35), bevel=0.006, color="#d8b977")
    box(it, "paper", (0.7, 0.92, 0.012), (-0.45, 0.18, 0.31), rot=Rz(0.3) @ Rx(-0.35), bevel=0.006, color="#e0c488")
    box(it, "paper", (0.24, 0.1, 0.012), (-0.62, 0.62, 0.275), rot=Rz(0.35), color="#d8b977")             # tab
    box(it, "stain", (0.16, 0.025, 0.002), (-0.62, 0.62, 0.283), rot=Rz(0.35), color="#6a4a2a")
    # bulldog clip on a small bundle
    box(it, "paper", (0.5, 0.7, 0.07), (0.55, -0.15, 0.04), rot=Rz(-0.25), bevel=0.01, color="#f1ede2")
    box(it, "metal", (0.3, 0.1, 0.09), (0.5, 0.17, 0.1), rot=Rz(-0.25), bevel=0.012, color="#2b2f33")
    for sx in (-1, 1):
        box(it, "metal", (0.02, 0.2, 0.02), (0.5 + sx * 0.13, 0.28, 0.19), rot=Rz(-0.25), color="#b8bcbd")
    # a pen
    cyl(it, "plastic_blue", 0.02, 0.7, (-0.1, -0.5, 0.26), rot=Ry(math.pi / 2) @ Rz(0.4), seg=10, color="#2c5aa0")
    cyl(it, "metal", 0.02, 0.1, (-0.4, -0.38, 0.26), rot=Ry(math.pi / 2) @ Rz(0.4), seg=10, color="#b8bcbd")
    _scale_item(it, 1.55)
    for g in it.groups.values():
        pass
    return it


ITEMS_D.update({"filingcabinet": filingcabinet, "docpile": docpile})


# ---------------------------------------------------------------- realistic plants (floor items; origin = centre of the pot bottom, Blender coords, 1 unit = 1 stud)
def _leaf(it, color, base, yaw, L, W, elev, arch, cup, shape, twist=0.0, holes=None, nu=12, nv=6, mat="leaf"):
    """One leaf as a bent surface patch. base = (x, y, z) of the stalk end; yaw = compass angle of the leaf axis; elev = starting elevation (rad);
    arch = how much the axis droops along its length; cup = V-fold across the midrib; shape(u) = relative half width 0..1; holes(u, v) -> True cuts a cell."""
    bm = bmesh.new()
    h = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    side = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    pts = [Vector(base)]
    th = elev
    for i in range(nu):
        u = (i + 0.5) / nu
        th = elev - arch * u
        pts.append(pts[-1] + (h * math.cos(th) + Vector((0, 0, math.sin(th)))) * (L / nu))
    rows = []
    for i, pc in enumerate(pts):
        u = i / nu
        th_i = elev - arch * u
        up = (-h * math.sin(th_i) + Vector((0, 0, math.cos(th_i)))).normalized()
        sd = (side * math.cos(twist * u) + up * math.sin(twist * u))
        w = W * 0.5 * shape(u)
        row = []
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            off = sd * (v * w) + up * (cup * w * (v * v) * 0.9 - cup * w * 0.15) + up * (-0.012 * (1 - abs(v)) * 0)
            row.append(bm.verts.new(pc + off))
        rows.append(row)
    for i in range(nu):
        for j in range(nv):
            uc, vc = (i + 0.5) / nu, -1 + 2 * (j + 0.5) / nv
            if holes and holes(uc, vc):
                continue
            if shape(uc) < 0.03 and shape((i + 1) / nu) < 0.03:
                continue
            try:
                bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    it.put(bm, mat, color)
    return pts[-1]


def _pot(it, rng, r, h, color, soil="#2b2119", rim="#d8d2c4", saucer=True, glaze=None):
    """Ceramic pot: tapered body with a rolled rim, a foot ring, a saucer with a lip, a mound of soil with pebbles and a tuft of moss."""
    if saucer:
        cyl(it, "ceramic", r * 1.1, 0.09, (0, 0, 0), seg=40, color="#b9b4a6", r2=r * 1.16, bevel=0.025)
    z0 = 0.09 if saucer else 0.0
    lathe(it, "ceramic", [(0, z0), (r * 0.72, z0), (r * 0.74, z0 + 0.05), (r * 0.8, z0 + 0.12), (r * 0.98, z0 + h * 0.6), (r * 1.06, z0 + h * 0.96),
                         (r * 1.12, z0 + h), (r * 1.08, z0 + h + 0.05), (r * 0.98, z0 + h + 0.04), (r * 0.94, z0 + h - 0.05), (0, z0 + h - 0.05)], (0, 0, 0), 44, color=color)
    torus(it, "ceramic", r * 1.09, 0.035, (0, 0, z0 + h + 0.015), color=rim, seg=44, minor=8)
    cyl(it, "dark", r * 0.97, 0.03, (0, 0, z0 + h - 0.22), seg=36, color=soil)
    ball(it, "dark", r * 0.9, (0, 0, z0 + h - 0.2), scale=(1, 1, 0.14), seg=24, color=soil)
    for _ in range(26):
        a = rng.uniform(0, math.tau); d = rng.uniform(0.15, r * 0.82)
        ball(it, "ceramic", rng.uniform(0.035, 0.07), (math.cos(a) * d, math.sin(a) * d, z0 + h - 0.17), scale=(1, 1, 0.6), seg=6, color=rng.choice(["#8c8577", "#a8a190", "#6e685c"]))
    return z0 + h - 0.18


def plantfig():
    """Fiddle-leaf fig (Ficus lyrata): pale pot, a trunk with a slight lean and bark rings, three branch levels, 34 big violin-shaped leaves with a lighter
    midrib stripe, drooping and cupped, some turned toward the viewer; two buds at the crown."""
    it = Item("PlantFig"); rng = random.Random(201)
    top = _pot(it, rng, 0.95, 1.25, "#e9e4d8", rim="#f4f0e6")
    trunk = [(0.0, 0.0, top), (0.05, 0.02, top + 1.1), (0.0, 0.06, top + 2.2), (-0.06, 0.04, top + 3.2), (-0.02, 0.0, top + 4.0)]
    tube(it, "wood_mid", [Vector(p) for p in trunk], [0.12, 0.105, 0.09, 0.07, 0.05], 12, "#7a6347", squash=(1, 1))
    for k in range(6):
        z = top + 0.5 + k * 0.6
        torus(it, "wood_mid", 0.1 - k * 0.008, 0.012, (trunk[min(4, int(k * 0.8))][0], trunk[min(4, int(k * 0.8))][1], z), color="#6a553b", seg=14, minor=5)
    greens = ["#2f5d33", "#386b3a", "#2a5430", "#40763f"]
    def fid(u):
        return (math.sin(math.pi * (u ** 0.72)) ** 0.62) * (0.62 + 0.55 * u ** 1.4) if u < 0.97 else 0.0
    for lvl, (zz, n, Lbase) in enumerate(((top + 1.4, 8, 1.6), (top + 2.2, 9, 1.8), (top + 3.0, 10, 1.85), (top + 3.7, 8, 1.6), (top + 4.1, 5, 1.3))):
        for k in range(n):
            a = k / n * math.tau + lvl * 0.7 + rng.uniform(-0.2, 0.2)
            tx = trunk[min(4, max(0, int((zz - top) / 1.0)))]
            px, py = tx[0] + math.cos(a) * 0.07, tx[1] + math.sin(a) * 0.07
            L = Lbase * rng.uniform(0.85, 1.15)
            col = rng.choice(greens)
            e = rng.uniform(0.35, 0.8) - 0.12 * lvl
            end = _leaf(it, col, (px, py, zz + rng.uniform(-0.15, 0.15)), a, L, L * 0.62, e, rng.uniform(0.9, 1.5), rng.uniform(0.35, 0.6), fid, twist=rng.uniform(-0.4, 0.4), nu=12, nv=6)
            # light midrib stripe
            _leaf(it, "#8fb87a", (px, py, zz + 0.012), a, L * 0.95, 0.05, e, rng.uniform(0.9, 1.5), 0.0, lambda u: 1.0 if u < 0.95 else 0.0, nu=10, nv=1)
    for k in range(2):
        a = k * math.pi + 0.5
        _leaf(it, "#b8cf8a", (0.0, 0.0, top + 4.0), a, 0.55, 0.22, 1.3, 0.2, 0.2, lambda u: math.sin(math.pi * u) ** 0.6, nu=6, nv=3)
    return it


def plantlily():
    """Areca palm: terracotta pot, a clump of 11 arching fronds; each frond has a ribbed rachis and 16 pairs of narrow leaflets that shorten toward the tip."""
    it = Item("PlantLily"); rng = random.Random(202)
    top = _pot(it, rng, 0.9, 1.15, "#b9653d", rim="#c97a4f")
    greens = ["#3b7a3f", "#4a8a45", "#336b38", "#58954c"]
    def narrow(u):
        return math.sin(math.pi * u) ** 0.5 if u < 0.98 else 0.0
    for f in range(11):
        a = f / 11 * math.tau + rng.uniform(-0.2, 0.2)
        elev = rng.uniform(1.1, 1.4)
        arch = rng.uniform(0.9, 1.4)
        L = rng.uniform(2.6, 3.4)
        h = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-math.sin(a), math.cos(a), 0))
        p = Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, top))
        path = [p.copy()]
        nseg = 14
        for i in range(nseg):
            u = (i + 0.5) / nseg
            th = elev - arch * u
            p = p + (h * math.cos(th) + Vector((0, 0, math.sin(th)))) * (L / nseg)
            path.append(p.copy())
        tube(it, "leaf", [Vector(q) for q in path], [0.045 - 0.03 * (i / nseg) for i in range(nseg + 1)], 8, "#5e8a45")
        for i in range(2, nseg + 1):
            u = i / nseg
            th = elev - arch * u
            ll = 0.95 * (1 - 0.55 * u) * rng.uniform(0.9, 1.05)
            for s in (-1, 1):
                ya = a + s * (1.15 - 0.4 * u)
                _leaf(it, rng.choice(greens), tuple(path[i]), ya, ll, 0.17, th * 0.4 - 0.1, 0.8, 0.5, narrow, nu=5, nv=2)
    return it


def plantmonstera():
    """Monstera deliciosa: charcoal pot, nine long petioles; each leaf is a big heart with deep marginal slits and two to three round holes, drooping."""
    it = Item("PlantMonstera"); rng = random.Random(203)
    top = _pot(it, rng, 1.0, 1.2, "#3a3d42", rim="#565a60")
    greens = ["#2d6a38", "#357a40", "#285f33", "#3f8a4a"]
    def heart(u):
        if u < 0.1:
            return 0.0 + u * 4
        return math.sin(math.pi * (u ** 0.75)) ** 0.7 * (1.0 if u > 0.2 else 0.5 + (u - 0.1) * 5)
    for k in range(12):
        a = k / 12 * math.tau + rng.uniform(-0.25, 0.25)
        hgt = rng.uniform(2.2, 4.4)
        reach = rng.uniform(0.6, 1.9)
        st = [Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, top)), Vector((math.cos(a) * reach * 0.25, math.sin(a) * reach * 0.25, top + hgt * 0.6)),
              Vector((math.cos(a) * reach, math.sin(a) * reach, top + hgt))]
        tube(it, "leaf", st, [0.075, 0.062, 0.05], 8, "#3f7a46")
        Lh = rng.uniform(2.1, 2.9)
        phase = rng.uniform(0, 1)
        def holes(u, v, phase=phase):
            av = abs(v)
            # slits slant from the edge toward the midrib and widen at the margin
            slit = av > 0.28 + 0.5 * ((u * 5.0 + phase + av * 0.9) % 1.0) * 0 and 0.18 < u < 0.94 and (((u * 5.0 + phase + av * 0.55) % 1.0) < 0.2 + 0.25 * av)
            hole = (abs(av - 0.22) < 0.07) and (abs(u - 0.42) < 0.05 or abs(u - 0.68) < 0.045)
            return slit or hole
        _leaf(it, rng.choice(greens), tuple(st[2]), a + rng.uniform(-0.3, 0.3), Lh, Lh * 0.95, rng.uniform(0.1, 0.5), rng.uniform(0.5, 1.0), rng.uniform(0.18, 0.32), heart,
              twist=rng.uniform(-0.3, 0.3), nu=28, nv=22, holes=holes)
    return it


ITEMS_D.update({"plantfig": plantfig, "plantlily": plantlily, "plantmonstera": plantmonstera})


# ------------------------------------------------------------------ toilet mirror (the old one was a flat grey metal sheet)
def _lerp_hex(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def wcmirror():
    """Wall mirror 2.6 x 3.35 for the toilets: aluminium frame with a recessed lip, a silvered glass made of a vertical gradient of bands (cool grey at the
    top and bottom, bright in the middle) with diagonal highlight streaks, a reflected window, bevelled silvering edge, four wall clips, water drops."""
    it = Item("WcMirror")
    GW, GH = 2.43, 3.16
    W, H = 2.59, 3.35
    rbc(it, "plastic", W, H, 0.03, 0, 0, -0.015, bevel=0.01, color="#2b3235")                                   # back plate
    # glass slab and the reflected room: light wall with a soft vertical gradient, teal dado with a tan rail at the bottom, ceiling strip at the top
    rbc(it, "plastic", GW, GH, 0.02, 0, 0, -0.04, bevel=0.004, color="#a9bcc4")
    z0 = -0.0505
    dado_top = -GH / 2 + 0.95
    nb = 22
    wall_h = GH / 2 - dado_top
    for i in range(nb):                                         # wall part: 22 thin bands, slightly darker toward the ceiling
        t = i / (nb - 1)
        col = _lerp_hex("#a3b8c0", "#c6d8de", 1.0 - abs(t - 0.55) / 0.55 * 0.9)
        y1 = GH / 2 - wall_h * i / nb
        y0 = GH / 2 - wall_h * (i + 1) / nb
        rbc(it, "stain", GW - 0.02, y1 - y0 + 0.001, 0.003, 0, (y0 + y1) / 2, z0 - i * 0.00004, color=col)
    nd = 10
    for i in range(nd):                                         # dado part: darkens downward
        col = _lerp_hex("#5f8993", "#3f6772", i / (nd - 1))
        y1 = dado_top - 0.07 - (dado_top - 0.07 + GH / 2) * i / nd
        y0 = dado_top - 0.07 - (dado_top - 0.07 + GH / 2) * (i + 1) / nd
        rbc(it, "stain", GW - 0.02, y1 - y0 + 0.001, 0.003, 0, (y0 + y1) / 2, z0 - 0.0012 - i * 0.00004, color=col)
    rbc(it, "stain", GW - 0.02, 0.07, 0.003, 0, dado_top - 0.035, z0 - 0.0016, color="#b7a47d")      # dado rail
    rbc(it, "stain", GW - 0.02, 0.012, 0.003, 0, dado_top - 0.075, z0 - 0.0018, color="#2c4b54")     # its shadow line
    rbc(it, "stain", 1.5, 0.05, 0.003, 0.2, GH / 2 - 0.2, z0 - 0.002, color="#f3fafd")               # ceiling light strip
    rbc(it, "stain", GW - 0.02, 0.1, 0.003, 0, GH / 2 - 0.06, z0 - 0.0014, color="#9fb4bc")          # darker ceiling edge
    # reflected window: dusk-blue pane with a frame cross and two lit windows of the city
    rbc(it, "stain", 0.9, 1.0, 0.003, 0.5, 0.55, z0 - 0.003, color="#6f7da0")
    rbc(it, "stain", 0.9, 0.35, 0.003, 0.5, 0.88, z0 - 0.0033, color="#8f86a6")
    rbc(it, "stain", 0.03, 1.0, 0.003, 0.5, 0.55, z0 - 0.0045, color="#cfdde2")
    rbc(it, "stain", 0.9, 0.03, 0.003, 0.5, 0.55, z0 - 0.0048, color="#cfdde2")
    rbc(it, "stain", 0.09, 0.07, 0.003, 0.3, 0.3, z0 - 0.0036, color="#e8d9a0")
    rbc(it, "stain", 0.09, 0.07, 0.003, 0.72, 0.4, z0 - 0.0037, color="#e8d9a0")
    # diagonal highlight streaks clipped to the glass rectangle (soft, not pure white)
    def clip_rect(pts, xmin, xmax, ymin, ymax):
        for axis, lim, keep_lt in ((0, xmax, True), (0, xmin, False), (1, ymax, True), (1, ymin, False)):
            out = []
            for i in range(len(pts)):
                p, q = pts[i], pts[(i + 1) % len(pts)]
                pin = (p[axis] <= lim) if keep_lt else (p[axis] >= lim)
                qin = (q[axis] <= lim) if keep_lt else (q[axis] >= lim)
                if pin != qin:
                    t = (lim - p[axis]) / (q[axis] - p[axis])
                    out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
                if qin:
                    out.append(q)
            pts = out
            if not pts:
                return []
        return pts
    for cx, w, sk, col, z in ((-0.55, 0.11, 0.9, "#cfdfe5", -0.0605), (-0.34, 0.035, 0.9, "#d9e7ec", -0.0615), (0.75, 0.07, 0.9, "#cddde3", -0.0625)):
        hh = 3.4
        quad = [(cx - w / 2 - sk, -hh / 2), (cx + w / 2 - sk, -hh / 2), (cx + w / 2 + sk, hh / 2), (cx - w / 2 + sk, hh / 2)]
        poly = clip_rect(quad, -GW / 2 + 0.06, GW / 2 - 0.06, -GH / 2 + 0.06, GH / 2 - 0.06)
        if len(poly) >= 3:
            rpoly(it, "stain", poly, z, 0.003, col)
    # bevelled silvering edge: dark outer line + bright inner line
    for sx in (-1, 1):
        rbc(it, "stain", 0.035, GH - 0.02, 0.004, sx * (GW / 2 - 0.02), 0, -0.0655, color="#7a8f98")
        rbc(it, "stain", 0.012, GH - 0.1, 0.004, sx * (GW / 2 - 0.058), 0, -0.0675, color="#e8f3f6")
    for sy in (-1, 1):
        rbc(it, "stain", GW - 0.07, 0.035, 0.004, 0, sy * (GH / 2 - 0.02), -0.0665, color="#7a8f98")
        rbc(it, "stain", GW - 0.15, 0.012, 0.004, 0, sy * (GH / 2 - 0.058), -0.0685, color="#e8f3f6")
    # water drops and a soap smear (low in the glass)
    rng = random.Random(7)
    for _ in range(14):
        x = rng.uniform(-GW / 2 + 0.2, GW / 2 - 0.2)
        y = rng.uniform(-GH / 2 + 0.2, -0.2)
        r = rng.uniform(0.012, 0.04)
        rdisc(it, "stain", r, x, y, -0.071 - rng.random() * 0.002, 0.003, "#eaf5f8", seg=10)
    # frame: four aluminium bars with a bevel, a brighter front edge line and a recessed dark lip inside
    bar = 0.1
    for sy in (-1, 1):
        rbc(it, "metal", W, bar, 0.085, 0, sy * (H / 2 - bar / 2), -0.0425, bevel=0.02, seg=3, color="#b4bec1")
        rbc(it, "stain", W - 0.16, 0.014, 0.004, 0, sy * (H / 2 - bar / 2), -0.0875, color="#eef3f4")
        rbc(it, "metal", GW + 0.04, 0.03, 0.05, 0, sy * (GH / 2 + 0.015), -0.07, color="#5d6a6f")
    for sx in (-1, 1):
        rbc(it, "metal", bar, H - 2 * bar + 0.02, 0.085, sx * (W / 2 - bar / 2), 0, -0.0425, bevel=0.02, seg=3, color="#aab5b8")
        rbc(it, "stain", 0.014, H - 0.3, 0.004, sx * (W / 2 - bar / 2), 0, -0.0875, color="#eef3f4")
        rbc(it, "metal", 0.03, GH - 0.02, 0.05, sx * (GW / 2 + 0.015), 0, -0.07, color="#5d6a6f")
    # four mounting clips on the long edges, each with a screw
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (W / 2 - 0.02), sy * (H / 2 - 0.62)
            rbc(it, "metal", 0.16, 0.34, 0.03, cx, cy, -0.1, bevel=0.012, color="#8a9599")
            rdisc(it, "metal", 0.03, cx, cy + sy * 0.1, -0.1, 0.012, "#4e5a5f", seg=12)
    return it


ITEMS_D.update({"wcmirror": wcmirror})


# ------------------------------------------------------------------ open book for tables (the old one had metallic ribbed pages)
def decoropenbook():
    """Hardcover book lying open: dark-blue cloth cover with a rounded spine, two fanned blocks of 22 thin pages whose edges alternate cream and
    darker cream, the page surfaces curved toward the gutter, printed text lines on both pages, a red ribbon bookmark and a curled corner. Footprint
    about 1.7 x 1.15, height 0.2. Origin = centre of the bottom, front -Y."""
    it = Item("DecorOpenBook"); rng = random.Random(5)
    cover = "#233a66"
    box(it, "paper", (1.72, 1.14, 0.03), (0, 0, 0.015), bevel=0.012, color=cover)                      # open cover, both boards
    box(it, "paper", (0.1, 1.12, 0.05), (0, 0, 0.025), bevel=0.02, seg=3, color="#1b2d52")           # spine / hinge channel
    nl = 22
    for side in (-1, 1):
        for i in range(nl):
            t = i / (nl - 1)
            tilt = 0.03 + 0.17 * t                    # upper pages bend more toward the gutter
            xc = side * (0.43 - 0.02 * t)
            w = 0.78 - 0.04 * t
            col = "#f2ead6" if i % 2 == 0 else "#e2d7ba"
            box(it, "paper", (w, 1.04 - 0.01 * t, 0.007), (xc, 0, 0.045 + i * 0.0062 + 0.03 * t * 0), rot=Ry(-side * tilt), bevel=0.0015, color=col)
    ztop = 0.045 + (nl - 1) * 0.0062 + 0.006
    for side in (-1, 1):
        xc = side * (0.43 - 0.02)
        tilt = 0.2
        for k in range(22):                                                               # printed text lines: thin grey, a heading, paragraph gaps
            if k in (6, 14):
                continue
            ln = rng.uniform(0.5, 0.64) if k not in (0, 21, 5, 13) else rng.uniform(0.2, 0.38)
            if k == 0:
                ln = 0.34
            y = 0.44 - k * 0.04
            x_off = xc - side * 0.07 + (0.0 if k else -side * 0.1)
            box(it, "stain", (ln, 0.0075 if k else 0.016, 0.0012), (x_off, y, ztop + 0.003), color="#8a8f93" if k else "#4a4f53")
    # red ribbon bookmark lying across the gutter and over the bottom edge
    box(it, "stain", (0.03, 0.9, 0.003), (0.0, -0.1, ztop + 0.008), color="#b3262c")
    box(it, "stain", (0.03, 0.22, 0.003), (0.0, -0.62, 0.05), rot=Rz(0.12), color="#b3262c")
    # curled corner of the right page
    box(it, "paper", (0.2, 0.2, 0.003), (0.66, -0.46, ztop + 0.012), rot=Rx(0.22), bevel=0.001, color="#efe6cf")
    return it


ITEMS_D.update({"decoropenbook": decoropenbook})


# ------------------------------------------------------------------ sofa cushion (the old one was a flat beige oval)
def sofacushion():
    """Scatter cushion 1.22 x 1.02 x 0.38: inflated square pillow (profile (1-|u|^3)(1-|v|^3), pointed corners), a pinched centre with a covered button and
    radial creases, piping around the seam (neutral grey body '#bdbdbd', darker piping '#8a8a8a': the game tints both to the sofa colour), small tag on the seam."""
    it = Item("SofaCushion")
    W, H, T = 1.22, 1.02, 0.38
    nx, ny = 24, 20
    def h(u, v):
        edge = max(0.0, (1 - abs(u) ** 3) * (1 - abs(v) ** 3)) ** 0.5
        dip = 1 - 0.34 * math.exp(-((u * 3.2) ** 2 + (v * 3.2) ** 2))
        crease = 1 - 0.035 * math.sin(math.atan2(v, u) * 8.0) * math.exp(-((u * 1.8) ** 2 + (v * 1.8) ** 2)) * 2
        return T / 2 * edge * dip * crease
    bm = bmesh.new()
    grid_f = {}
    grid_b = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            u, v = (i / nx) * 2 - 1, (j / ny) * 2 - 1
            hh = h(u, v)
            cf = 1.0 / (1.0 + 0.2 * (abs(u) * abs(v)) ** 2)
            x, y = u * W / 2 * cf, v * H / 2 * cf
            vf = bm.verts.new(P(x, y, -hh))
            grid_f[(i, j)] = vf
            border = i in (0, nx) or j in (0, ny)
            grid_b[(i, j)] = vf if border else bm.verts.new(P(x, y, hh))
    for i in range(nx):
        for j in range(ny):
            a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
            try:
                bm.faces.new([grid_f[a], grid_f[b], grid_f[c], grid_f[d]])
                bm.faces.new([grid_b[d], grid_b[c], grid_b[b], grid_b[a]])
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    it.put(bm, "plastic", "#bdbdbd")
    # piping around the seam (a closed tube of 8-sided section following the outline)
    pts = []
    for i in range(nx):
        pts.append((i / nx * 2 - 1, -1))
    for j in range(ny):
        pts.append((1, j / ny * 2 - 1))
    for i in range(nx):
        pts.append((1 - i / nx * 2, 1))
    for j in range(ny):
        pts.append((-1, 1 - j / ny * 2))
    path = [(u * W / 2 / (1.0 + 0.2 * (abs(u) * abs(v)) ** 2), v * H / 2 / (1.0 + 0.2 * (abs(u) * abs(v)) ** 2), 0.0) for u, v in pts]
    rtube(it, "plastic", path + [path[0]], [0.026] * (len(path) + 1), 8, "#8a8a8a")
    # covered button in the pinched centre
    c0 = h(0, 0)
    ball(it, "plastic", 0.05, P(0, 0, -c0 - 0.01), scale=(1, 1, 0.55), color="#8a8a8a", seg=10)
    ball(it, "plastic", 0.05, P(0, 0, c0 + 0.01), scale=(1, 1, 0.55), color="#8a8a8a", seg=10)
    # tag on the seam
    rbc(it, "plastic", 0.14, 0.09, 0.012, W / 2 - 0.2, -H / 2 - 0.045, 0.0, color="#8a8a8a")
    return it


ITEMS_D.update({"sofacushion": sofacushion})


# ------------------------------------------------------------------ pipe run, built from scratch (the old one used tubes whose rings twisted at the vertical riser)
def sweep(it, mat, pts, radius, sides=24, color=None):
    """Watertight pipe along the Roblox-space polyline `pts` with a rotation-minimising (parallel transport) frame: no ring twist anywhere, closed flat
    caps at both ends. Points should be dense on bends."""
    P3 = [Vector(P(*p)) for p in pts]
    n = len(P3)
    tans = []
    for i in range(n):
        a = P3[max(i - 1, 0)]; b = P3[min(i + 1, n - 1)]
        tans.append((b - a).normalized())
    t0 = tans[0]
    ref = Vector((0, 0, 1)) if abs(t0.dot(Vector((0, 0, 1)))) < 0.9 else Vector((1, 0, 0))
    nrm = t0.cross(ref).normalized()
    bm = bmesh.new()
    rings = []
    prev_t = t0
    for i in range(n):
        t = tans[i]
        if i:
            q = prev_t.rotation_difference(t)
            nrm = (q @ nrm).normalized()
            nrm = (nrm - t * nrm.dot(t)).normalized()
        side = t.cross(nrm).normalized()
        ring = [bm.verts.new(P3[i] + (nrm * math.cos(k / sides * math.tau) + side * math.sin(k / sides * math.tau)) * radius) for k in range(sides)]
        rings.append(ring)
        prev_t = t
    for i in range(n - 1):
        for k in range(sides):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % sides], rings[i + 1][(k + 1) % sides], rings[i + 1][k]))
    for end, idx in ((0, 0), (1, n - 1)):
        c = bm.verts.new(P3[idx])
        ring = rings[idx]
        for k in range(sides):
            bm.faces.new((c, ring[(k + 1) % sides], ring[k]) if end == 0 else (c, ring[k], ring[(k + 1) % sides]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    it.put(bm, mat, color)


def _arc(cx, cy, cz, ax, ay, r, a0, a1, n=18, plane="xz"):
    """Points of a circular arc in Roblox space. plane 'xz': x = cx + r cos a, z = cz + r sin a; plane 'xy': x = cx + r cos a, y = cy + r sin a."""
    out = []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        out.append((cx + r * math.cos(a), cy, cz + r * math.sin(a)) if plane == "xz" else (cx + r * math.cos(a), cy + r * math.sin(a), cz))
    return out


def piperun():
    """Wall service run (y -1.1 .. +3.9, x -4.5 .. +4.7). ONE continuous steel sweep: from inside the wall (left, through a bolted collar plate) with a
    real bend of radius = distance to the wall, straight main with flanged joints, valve, gauge, insulated stretch, a second real bend into a riser that
    goes up to the ceiling flange (top = 3.9, i.e. the ceiling underside when the origin is at 7.6). A second continuous copper sweep enters the wall
    at both ends through small collars. Every support is a stand-off bolted to a wall plate. Nothing ends in the air."""
    it = Item("PipeRun")
    zc, R = -0.62, 0.30
    Rw = -zc                                   # bend radius into the wall
    Rb = 0.9                                   # bend radius into the riser
    xs0 = 4.05                                 # where the left bend starts (main straight part begins here)
    xe = xs0 + Rw                              # x where the pipe enters the wall
    xb = -3.6                                  # where the right bend starts
    xr = xb - Rb                               # riser axis
    top = 3.9
    # --- steel: wall (left) -> bend -> main -> bend -> riser -> ceiling flange
    path = [(xe, 0.0, 0.35), (xe, 0.0, 0.1)]
    path += _arc(xs0, 0.0, 0.0, 0, 0, Rw, 0.0, -math.pi / 2, 18, "xz")[0:]               # from (xe, 0) turning to run toward -x at z = -Rw
    for x in (3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0):
        path.append((x, 0.0, zc))
    # right bend: from (xb, 0) heading -x, turning up around the centre (xb, Rb): angle -90 deg (point (xb, 0)) to -180 deg (point (xb - Rb, Rb))
    path += [(xb + Rb * math.cos(a), Rb + Rb * math.sin(a), zc) for a in [(-math.pi / 2) - (math.pi / 2) * k / 18 for k in range(19)]]
    for y in (1.6, 2.4, 3.2, top - 0.05):
        path.append((xr, y, zc))
    sweep(it, "metal", path, R, 28, STEEL)
    # wall collar plate with bolts + sleeve ring where the steel enters the wall
    rdisc(it, "metal", 0.52, xe, 0.0, 0.0, 0.07, "#8d9598", bevel=0.015, seg=30)
    rdisc(it, "metal", 0.42, xe, 0.0, -0.07, 0.05, "#7a8387", bevel=0.012, seg=30)
    rdisc(it, "metal", 0.37, xe, 0.0, -0.12, 0.04, "#6f797d", bevel=0.01, seg=30)
    for k in range(6):
        a = k / 6 * math.tau
        rdisc(it, "metal", 0.03, xe + math.cos(a) * 0.46, math.sin(a) * 0.46, -0.06, 0.02, "#4e5a5f", seg=8)
    # ceiling flange (plate on the ceiling underside) with bolts, collar ring on the pipe
    rbc(it, "metal", 0.95, 0.12, 0.95, xr, top - 0.06, zc, bevel=0.03, color="#8d9598")
    rpost(it, "metal", R * 1.28, top - 0.35, top - 0.1, xr, zc, seg=28, color="#7f898d")
    for sx in (-1, 1):
        for sz in (-1, 1):
            rpost(it, "metal", 0.035, top - 0.2, top - 0.06, xr + sx * 0.38, zc + sz * 0.38, seg=8, color="#4e5a5f")
    # --- couplings on the main
    for fx in (-1.7, 2.5):                                                                                   # bolted flange pairs
        for dx in (-0.07, 0.07):
            rbc(it, "metal", 0.12, R * 3.4, R * 3.4, fx + dx, 0.0, zc, bevel=0.03, color="#7f898d")
        for k in range(8):
            a = k / 8 * math.tau
            rbc(it, "metal", 0.32, 0.1, 0.1, fx, math.cos(a) * R * 1.22, zc + math.sin(a) * R * 1.22, color=DARKSTEEL)
    for yy in (1.25, 2.6):                                                                                   # riser couplings
        rpost(it, "metal", R * 1.24, yy, yy + 0.16, xr, zc, seg=28, color="#7f898d")
    # --- stand-offs for the main (wall plate + two arms + saddle clamp) at x = -3.2 .. 3.4 (not inside the bends)
    for cx in (-2.6, -0.5, 1.2, 3.0):
        rbc(it, "metal", 0.46, R * 4.6, 0.05, cx, 0.0, -0.025, bevel=0.012, color=DARKSTEEL)
        for sy in (-1, 1):
            rdisc(it, "metal", 0.03, cx, sy * R * 2.1, -0.07, 0.015, "#c9ceca", seg=8)
            rbc(it, "metal", 0.3, 0.16, abs(zc) - 0.08, cx, sy * R * 1.35, zc * 0.5, bevel=0.02, color=DARKSTEEL)
        rbc(it, "metal", 0.34, R * 2.7, 0.14, cx, 0.0, zc - R * 0.9, bevel=0.03, color=DARKSTEEL)
    # riser bracket: plate on the wall, arm to a saddle clamp
    rbc(it, "metal", 0.5, 0.7, 0.05, xr, 1.9, -0.025, bevel=0.012, color=DARKSTEEL)
    rbc(it, "metal", 0.34, 0.2, abs(zc) - 0.05, xr, 1.9, zc * 0.5, bevel=0.02, color=DARKSTEEL)
    rpost(it, "metal", R * 1.2, 1.82, 1.98, xr, zc, seg=28, color=DARKSTEEL)
    # --- insulation
    rpipex(it, "plastic", R * 1.25, -3.0, -2.1, 0.0, zc, "#e3e0cf", seg=26)
    for k in range(6):
        rpipex(it, "plastic", R * 1.27, -2.95 + k * 0.15, -2.88 + k * 0.15, 0.0, zc, "#b9b49c", seg=26)
    # --- valve with red handwheel
    vx = 0.45
    rpost(it, "metal", 0.17, R * 0.9, 1.0, vx, zc, seg=18, color=BRASS)
    rbc(it, "metal", 0.62, 0.5, 0.62, vx, 1.15, zc, bevel=0.1, seg=3, color=BRASS)
    rpost(it, "metal", 0.07, 1.35, 2.1, vx, zc, seg=12, color="#9aa1a5")
    for k in range(3):
        rbc(it, "plastic", 0.95, 0.1, 0.12, vx, 2.1, zc, rot=RR("Y", k * math.pi / 3), bevel=0.02, color="#c0392b")
    torus(it, "plastic", 0.47, 0.06, P(vx, 2.1, zc), color="#c0392b", seg=24, minor=8)
    # --- pressure gauge
    gx = -0.95
    rpost(it, "metal", 0.07, R * 0.9, 0.75, gx, zc, seg=10, color=BRASS)
    rdisc(it, "metal", 0.36, gx, 1.08, zc - 0.02, 0.2, "#c9ceca", bevel=0.03, seg=24)
    rdisc(it, "paper", 0.3, gx, 1.08, zc - 0.22, 0.02, "#efeee3", seg=24)
    rbc(it, "dark", 0.025, 0.26, 0.012, gx + 0.04, 1.1, zc - 0.245, rot=RR("Z", 0.7), color="#c0392b")
    for k in range(9):
        a = -2.3 + k * 0.55
        rbc(it, "dark", 0.025, 0.06, 0.008, gx + math.sin(a) * 0.25, 1.08 + math.cos(a) * 0.25, zc - 0.24, rot=RR("Z", -a), color="#2c3032")
    # --- copper: ONE sweep, both ends bend into the wall through collars
    ycu, zcu = -0.95, zc + 0.12
    Rc = -zcu
    xl, xrr = 3.85, -3.3
    cpath = [(xl + Rc, ycu, 0.35), (xl + Rc, ycu, 0.1)]
    cpath += _arc(xl, ycu, 0.0, 0, 0, Rc, 0.0, -math.pi / 2, 14, "xz")
    for x in (3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0):
        cpath.append((x, ycu, zcu))
    cpath += [(xrr - Rc * math.sin(a), ycu, zcu + Rc - Rc * math.cos(a)) for a in [(math.pi / 2) * k / 14 for k in range(15)]]
    cpath += [(xrr - Rc, ycu, 0.1), (xrr - Rc, ycu, 0.35)]
    sweep(it, "copper", cpath, 0.14, 18)
    for ex in (xl + Rc, xrr - Rc):
        rdisc(it, "metal", 0.3, ex, ycu, 0.0, 0.05, "#b9bfc1", bevel=0.012, seg=22)
        rdisc(it, "metal", 0.22, ex, ycu, -0.05, 0.04, "#9aa1a5", bevel=0.01, seg=22)
    for cx in (-2.4, -0.2, 2.0, 3.4):                                                                         # copper clips on the wall
        rbc(it, "metal", 0.2, 0.46, 0.05, cx, ycu, -0.025, bevel=0.012, color="#7f898d")
        rbc(it, "metal", 0.2, 0.46, 0.16, cx, ycu, zcu + 0.04, bevel=0.03, color="#7f898d")
    return it


ITEMS_D.update({"piperun": piperun})


# detail views (azimuth, elevation, target x, y, z in Roblox coords, camera distance): every junction of the pipe run
DETAILS = {"firealarm": [(0, 0, 0.0, 0.0, -0.4, 3.4), (45, 10, 0.4, 0.55, -0.4, 1.8), (-45, 10, -0.4, 0.55, -0.4, 1.8), (50, -12, 0.4, -0.6, -0.4, 1.8),
                         (-50, -12, -0.4, -0.6, -0.4, 1.8), (80, 0, 0.0, 0.0, -0.3, 3.0), (0, 40, 0.0, 0.7, -0.3, 3.0), (0, -40, 0.0, -0.7, -0.3, 3.0)],
           "piperun": [(25, 10, 4.5, 0.0, -0.3, 3.2), (-35, 12, 4.5, -0.4, -0.3, 3.0), (20, 20, -4.5, 0.9, -0.6, 3.4), (-30, 15, -4.5, 0.9, -0.6, 3.4),
                       (0, 55, -4.5, 3.5, -0.6, 3.2), (30, -20, -4.5, 3.3, -0.6, 3.4), (0, 0, -4.3, 1.8, -0.6, 4.5), (-60, 10, 4.7, -0.5, -0.2, 2.6)]}
