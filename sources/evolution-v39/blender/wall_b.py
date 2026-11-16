"""Wall decor, group B (exec'd by wall_hero.py): electrical panels, service pipes, fire alarm, thermostat, cameras."""

STEEL = "#6d777c"
DARKSTEEL = "#4b5356"
BRASS = "#b8913f"


def _screws(it, pts, z, r=0.07, color="#8a908e"):
    for x, y in pts:
        rdisc(it, "metal", r, x, y, z, 0.03, color, seg=10)
        rbc(it, "dark", r * 1.5, 0.018, 0.012, x, y, z - 0.03, rot=RR("Z", 0.6), color="#3d4244")


def _breakers(it, x0, y, n, z, rng, pitch=0.3):
    for i in range(n):
        x = x0 - i * pitch
        rbc(it, "plastic", 0.26, 0.62, 0.3, x, y, z, bevel=0.02, color="#dfe1dc")
        on = rng.random() < 0.8
        rbc(it, "dark", 0.14, 0.13, 0.12, x, y + (0.1 if on else -0.1), z - 0.2, bevel=0.01, color="#26292b")
        rbc(it, "stain", 0.16, 0.04, 0.01, x, y - 0.26, z - 0.151, color="#2a6f9a" if i % 3 else "#c0392b")


def _cabinet_shell(it, W, H, D, body):
    rbc(it, "metal", W, H, 0.06, 0, 0, -0.03, color=body)
    for sx in (-1, 1):
        rbc(it, "metal", 0.06, H, D, sx * (W / 2 - 0.03), 0, -D / 2, bevel=0.01, color=body)
    for sy in (-1, 1):
        rbc(it, "metal", W, 0.06, D, 0, sy * (H / 2 - 0.03), -D / 2, bevel=0.01, color=body)
    for sx in (-1, 1):
        rbc(it, "metal", 0.14, H, 0.05, sx * (W / 2 - 0.07), 0, -D - 0.02, bevel=0.01, color=body)
    for sy in (-1, 1):
        rbc(it, "metal", W, 0.14, 0.05, 0, sy * (H / 2 - 0.07), -D - 0.02, bevel=0.01, color=body)


def _conduits(it, H, xs, rise):
    for cx in xs:
        rpost(it, "metal", 0.2, H / 2, H / 2 + rise, cx, -0.34, seg=18, color="#8f979a")
        rbc(it, "metal", 0.56, 0.16, 0.3, cx, H / 2 + 0.02, -0.34, bevel=0.03, color="#7c8588")
        for k in range(int(rise)):
            y = H / 2 + 0.7 + k * 1.0
            rbc(it, "metal", 0.58, 0.12, 0.12, cx, y, -0.34, bevel=0.02, color="#767f82")
            rbc(it, "metal", 0.24, 0.12, 0.34, cx, y, -0.17, bevel=0.01, color="#767f82")
            _screws(it, [(cx - 0.18, y), (cx + 0.18, y)], -0.46, 0.05)


def elecpanel():
    """Closed steel distribution cabinet 3.0 x 4.0 x 0.9 with two conduits to the ceiling: pressed door, quarter-turn handle with lock, hazard
    sticker, label plate, bottom louvres, hinge barrels on the viewer's left."""
    it = Item("ElecPanel")
    W, H, D = 3.0, 4.0, 0.85
    _cabinet_shell(it, W, H, D, "#b9beb8")
    _conduits(it, H, (-0.7, 0.55), 3)
    z0 = -D - 0.06
    rbc(it, "metal", W - 0.18, H - 0.18, 0.08, 0, 0, z0, bevel=0.025, seg=3, color="#c6cac3")
    rbc(it, "metal", W - 0.5, H - 0.5, 0.03, 0, 0, z0 - 0.06, bevel=0.02, color="#cdd1ca")
    for y in (H / 2 - 0.5, -H / 2 + 0.5):
        rpost(it, "metal", 0.07, y - 0.4, y + 0.4, W / 2 - 0.04, -D - 0.1, seg=10, color="#6d7578")
    rdisc(it, "metal", 0.26, -0.9, 0.15, z0 - 0.09, 0.07, "#8f969a", bevel=0.02)
    rbc(it, "metal", 0.5, 0.15, 0.14, -0.9, 0.15, z0 - 0.2, bevel=0.04, color="#3e4549")
    rdisc(it, "dark", 0.07, -0.9, 0.15, z0 - 0.15, 0.04, "#202426", seg=10)
    tri = [(0.0, 0.62), (-0.55, -0.34), (0.55, -0.34)]
    rpoly(it, "stain", [(x + 0.7, y + 0.95) for x, y in tri], z0 - 0.095, 0.01, "#101010")
    rpoly(it, "stain", [(x * 0.8 + 0.7, y * 0.8 + 0.95 - 0.04) for x, y in tri], z0 - 0.108, 0.01, "#f0c419")
    rpoly(it, "stain", [(0.78, 1.18), (0.58, 0.88), (0.72, 0.88), (0.62, 0.64), (0.88, 0.98), (0.72, 0.98)], z0 - 0.121, 0.008, "#151515")
    rbc(it, "paper", 1.35, 0.7, 0.02, 0.5, -0.55, z0 - 0.095, color="#efede0")
    for i, wd in enumerate((1.1, 0.9, 1.0, 0.6)):
        rbc(it, "stain", wd, 0.05, 0.008, 0.5 + (1.1 - wd) * 0.5, -0.4 - i * 0.14, z0 - 0.113, color="#5b5f60")
    for i in range(7):
        rbc(it, "dark", 1.7, 0.05, 0.03, 0, -1.45 - i * 0.075, z0 - 0.07, color="#2e3335")
    _screws(it, [(W / 2 - 0.3, H / 2 - 0.3), (-(W / 2 - 0.3), H / 2 - 0.3), (W / 2 - 0.3, -(H / 2 - 0.3)), (-(W / 2 - 0.3), -(H / 2 - 0.3))], z0 - 0.09, 0.06)
    return it


def elecpanelopen():
    """The same cabinet with the door swung open about 100 degrees on the viewer-left hinge: three DIN rails of breakers, coloured wires into slotted
    ducts, a main isolator; the door's inside shows a wiring diagram."""
    it = Item("ElecPanelOpen"); rng = random.Random(52)
    W, H, D = 3.0, 4.0, 0.85
    _cabinet_shell(it, W, H, D, "#b9beb8")
    _conduits(it, H, (-0.7, 0.55), 3)
    rbc(it, "paper", W - 0.4, H - 0.4, 0.04, 0, 0, -0.1, color="#d8c9a6")                                  # mounting plate
    for y in (1.25, 0.2, -0.85):
        rbc(it, "metal", W - 0.7, 0.2, 0.05, 0, y - 0.2, -0.16, color="#9ea5a8")
        n = 9
        _breakers(it, (n - 1) * 0.15, y, n, -0.34, rng)
        for k in range(n):
            col = rng.choice(("#1f1f20", "#b7312c", "#2c5aa0", "#caa21c", "#2f7a3e"))
            rbc(it, "rubber", 0.06, 0.34, 0.06, (n - 1) * 0.15 - k * 0.3, y - 0.48, -0.2, color=col, bevel=0.015)
        rbc(it, "plastic", W - 0.7, 0.18, 0.18, 0, y - 0.72, -0.22, bevel=0.02, color="#9aa3a6")
        for k in range(12):
            rbc(it, "dark", 0.04, 0.12, 0.02, -1.05 + k * 0.19, y - 0.72, -0.32, color="#4a5154")
    rbc(it, "plastic", 0.7, 0.7, 0.34, 0.95, 1.7, -0.3, bevel=0.03, color="#2c3033")
    rbc(it, "plastic", 0.3, 0.5, 0.2, 0.95, 1.7, -0.52, bevel=0.03, color="#c0392b")
    # the open door: a slab turned about the hinge axis (x = +W/2 - 0.05, z = -D - 0.04)
    ang = math.radians(100)
    hx, hz = W / 2 - 0.05, -D - 0.04
    slab = W - 0.18
    cx, cz = hx - math.cos(ang) * slab / 2, hz - math.sin(ang) * slab / 2
    rot = RR("Y", ang)
    rbc(it, "metal", slab, H - 0.18, 0.08, cx, 0, cz, rot=rot, bevel=0.02, seg=3, color="#c6cac3")
    # inside the door (facing the cabinet's right side): a wiring diagram on a paper sheet, offset along the door's own normal
    nx, nz = -math.sin(ang), math.cos(ang)
    px, pz = cx + nx * 0.06, cz + nz * 0.06
    rbc(it, "paper", slab * 0.7, H * 0.5, 0.012, px, 0.5, pz, rot=rot, color="#efede0")
    for i in range(8):
        rbc(it, "stain", slab * 0.55, 0.04, 0.01, px + nx * 0.008, 0.9 - i * 0.2, pz + nz * 0.008, rot=rot, color="#5b5f60")
    rpost(it, "metal", 0.07, -H / 2 + 0.3, H / 2 - 0.3, hx, hz, seg=10, color="#6d7578")
    return it


def piperun():
    """Horizontal service run 9.2 long (y -1.1 .. +3.4): painted steel main, copper line, flanged joints, clamps, valve with red handwheel, pressure
    gauge, insulated stretch with tape, wall escutcheon at viewer-left, an elbow rising to the ceiling at viewer-right."""
    it = Item("PipeRun"); rng = random.Random(61)
    zc = -0.62
    R = 0.3
    rpipex(it, "metal", R, -3.6, 4.05, 0.0, zc, STEEL, seg=26)
    # viewer-left end: the main bends 90 degrees INTO the wall and passes through a round escutcheon (collar plate + sleeve ring)
    xs0 = 4.05                                                                                              # steel main bends into the wall with a real bend radius (= distance to the wall), then runs straight through the collar
    Rw = -zc
    steel = [(xs0 - 0.2, 0.0, zc)] + [(xs0 + Rw * math.sin(k / 14 * math.pi / 2), 0.0, zc + Rw - Rw * math.cos(k / 14 * math.pi / 2)) for k in range(15)] + [(xs0 + Rw, 0.0, 0.3)]
    xe = xs0 + Rw
    rtube(it, "metal", steel, [R] * len(steel), 24, STEEL)
    rdisc(it, "metal", 0.52, xe, 0.0, 0.0, 0.06, "#8d9598", bevel=0.015, seg=28)                             # round wall collar plate
    rdisc(it, "metal", 0.42, xe, 0.0, -0.06, 0.05, "#7a8387", bevel=0.012, seg=28)
    rdisc(it, "metal", 0.36, xe, 0.0, -0.11, 0.04, "#6f797d", bevel=0.01, seg=28)                             # sleeve ring around the pipe
    for k in range(6):
        a = k / 6 * math.tau
        rdisc(it, "metal", 0.03, xe + math.cos(a) * 0.46, math.sin(a) * 0.46, -0.05, 0.02, "#4e5a5f", seg=8)





    # smooth 90-degree elbow (quarter circle, radius 0.9, 14 segments) from the main (running to -x) into the riser (going up), same radius as both pipes
    Rb, xr = 0.9, -3.6 - 0.9
    arc = [(-3.6 - Rb * math.sin(k / 14 * math.pi / 2), Rb - Rb * math.cos(k / 14 * math.pi / 2), zc) for k in range(15)]
    arc[0] = (-3.55, 0.0, zc)
    rtube(it, "metal", [(-3.4, 0.0, zc)] + arc[1:] + [(xr, Rb + 0.08, zc)], [R] * (len(arc) + 1), 24, STEEL)
    rpost(it, "metal", R, Rb, 3.86, xr, zc, seg=26, color=STEEL)
    # couplings hide both seams: collar at the start of the elbow, one where the elbow meets the riser, one halfway up, and a wall-bracketed clamp
    rpipex(it, "metal", R * 1.22, -3.5, -3.3, 0.0, zc, "#7f898d", seg=24)
    rpost(it, "metal", R * 1.22, Rb - 0.08, Rb + 0.1, xr, zc, seg=24, color="#7f898d")
    rpost(it, "metal", R * 1.22, 2.0, 2.14, xr, zc, seg=24, color="#7f898d")
    rbc(it, "metal", 0.5, 0.7, 0.05, xr, 2.07, -0.025, bevel=0.012, color=DARKSTEEL)
    rbc(it, "metal", 0.34, 0.2, 0.55, xr, 2.07, -0.3, bevel=0.02, color=DARKSTEEL)
    rbc(it, "metal", 0.9, 0.12, 0.9, xr, 3.84, zc, bevel=0.03, color="#8d9598")                                  # ceiling flange: plate top = ceiling underside (7.6 + 3.9 = 11.5)
    for fx in (-1.7, 2.5):
        for dx in (-0.07, 0.07):
            rbc(it, "metal", 0.12, R * 3.4, R * 3.4, fx + dx, 0.0, zc, bevel=0.03, color="#7f898d")
        for k in range(8):
            a = k / 8 * math.tau
            rbc(it, "metal", 0.32, 0.1, 0.1, fx, math.cos(a) * R * 1.22, zc + math.sin(a) * R * 1.22, color=DARKSTEEL)
    for cx in (-3.2, -0.5, 1.2, 3.4):
        rbc(it, "metal", 0.34, R * 2.7, 0.14, cx, 0.0, zc - R * 0.9, bevel=0.03, color=DARKSTEEL)
        rbc(it, "metal", 0.46, R * 4.6, 0.05, cx, 0.0, -0.025, bevel=0.012, color=DARKSTEEL)                # wall plate the stand-offs are bolted to
        for sy in (-1, 1):
            rdisc(it, "metal", 0.03, cx, sy * R * 2.1, -0.07, 0.015, "#c9ceca", seg=8)
        rbc(it, "metal", 0.34, 0.2, 0.55, cx, -R * 1.35, -0.3, bevel=0.02, color=DARKSTEEL)
        rbc(it, "metal", 0.34, 0.2, 0.55, cx, R * 1.35, -0.3, bevel=0.02, color=DARKSTEEL)
    rpipex(it, "plastic", R * 1.25, -3.0, -2.1, 0.0, zc, "#e3e0cf", seg=24)                                 # insulated stretch
    for k in range(6):
        rpipex(it, "plastic", R * 1.27, -2.95 + k * 0.15, -2.88 + k * 0.15, 0.0, zc, "#b9b49c", seg=24)
    vx = 0.45                                                                                               # valve
    rpost(it, "metal", 0.17, R, 1.0, vx, zc, seg=18, color=BRASS)
    rbc(it, "metal", 0.62, 0.5, 0.62, vx, 1.15, zc, bevel=0.1, seg=3, color=BRASS)
    rpost(it, "metal", 0.07, 1.35, 2.1, vx, zc, seg=12, color="#9aa1a5")
    for k in range(3):
        rbc(it, "plastic", 0.95, 0.1, 0.12, vx, 2.1, zc, rot=RR("Y", k * math.pi / 3), bevel=0.02, color="#c0392b")
    torus(it, "plastic", 0.47, 0.06, P(vx, 2.1, zc), color="#c0392b", seg=24, minor=8)
    gx = -0.95                                                                                              # gauge
    rpost(it, "metal", 0.07, R, 0.75, gx, zc, seg=10, color=BRASS)
    rdisc(it, "metal", 0.36, gx, 1.08, zc - 0.02, 0.2, "#c9ceca", bevel=0.03, seg=24)
    rdisc(it, "paper", 0.3, gx, 1.08, zc - 0.22, 0.02, "#efeee3", seg=24)
    rbc(it, "dark", 0.025, 0.26, 0.012, gx + 0.04, 1.1, zc - 0.245, rot=RR("Z", 0.7), color="#c0392b")
    for k in range(9):
        a = -2.3 + k * 0.55
        rbc(it, "dark", 0.025, 0.06, 0.008, gx + math.sin(a) * 0.25, 1.08 + math.cos(a) * 0.25, zc - 0.24, rot=RR("Z", -a), color="#2c3032")
    ycu = -0.95                                                                                             # copper line
    rpipex(it, "copper", 0.14, -3.3, 3.85, ycu, zc + 0.12, seg=18)
    zcu = zc + 0.12
    Rc = -zcu
    for sx, xs in ((-1, -3.3), (1, 3.85)):                                                                     # both ends of the copper line bend into the wall with a proper radius
        pts = [(xs - sx * 0.15, ycu, zcu)] + [(xs + sx * Rc * math.sin(k / 12 * math.pi / 2), ycu, zcu + Rc - Rc * math.cos(k / 12 * math.pi / 2)) for k in range(13)] + [(xs + sx * Rc, ycu, 0.3)]
        rtube(it, "copper", pts, [0.14] * len(pts), 14)
        rdisc(it, "metal", 0.3, xs + sx * Rc, ycu, 0.0, 0.05, "#b9bfc1", bevel=0.012, seg=20)
        rdisc(it, "metal", 0.22, xs + sx * Rc, ycu, -0.05, 0.04, "#9aa1a5", bevel=0.01, seg=20)
    for cx in (-2.4, -0.2, 2.0, 3.8):
        rbc(it, "metal", 0.2, 0.46, 0.16, cx, ycu, zc + 0.04, bevel=0.03, color="#7f898d")
    return it


def piperiser():
    """Two vertical service pipes floor to ceiling (11.4 high): brackets every 2.6, flanged joints, a valve with a red handwheel, insulation with
    tape on the small pipe, a wet rusty stain under the first joint."""
    it = Item("PipeRiser"); rng = random.Random(62)
    H = 11.4                                                                                                # floor (y 0.1) to the ceiling tile underside (y 11.5)
    y0, y1 = -H / 2, H / 2
    big = (0.0, 0.34, STEEL, -0.66)
    small = (-0.95, 0.2, "#7b858a", -0.5)
    for x, r, col, z in (big, small):
        rpost(it, "metal", r, y0 + 0.2, y1 - 0.2, x, z, seg=26, color=col)
        rbc(it, "metal", r * 3.2, 0.2, r * 3.2, x, y0 + 0.1, z, bevel=0.05, color="#7f898d")
        rbc(it, "metal", r * 3.0, 0.18, r * 3.0, x, y1 - 0.09, z, bevel=0.05, color="#7f898d")
    for y in (y0 + 2.0, y0 + 4.6, y0 + 7.2, y0 + 9.4, y0 + 10.7):
        for x, r, col, z in (big, small):
            rbc(it, "metal", r * 2.5, 0.12, 0.1, x, y, z - r * 0.9, bevel=0.025, color="#59636a")
            rbc(it, "metal", 0.16, 0.12, abs(z) - r * 0.8, x, y, z * 0.5 + 0.1, bevel=0.02, color="#59636a")
    for y in (y0 + 3.3, y0 + 7.9):
        for dy in (-0.07, 0.07):
            rbc(it, "metal", 1.2, 0.12, 1.2, 0.0, y + dy, -0.66, bevel=0.04, color="#7f898d")
        for k in range(8):
            a = k / 8 * math.tau
            rbc(it, "metal", 0.1, 0.34, 0.1, math.cos(a) * 0.5, y, -0.66 + math.sin(a) * 0.5, color=DARKSTEEL)
    vy = y0 + 5.6
    rbc(it, "metal", 0.6, 0.5, 0.5, 0.0, vy, -0.66, bevel=0.08, color=BRASS)
    rtube(it, "metal", [(0.0, vy, -0.95), (0.0, vy, -1.3), (0.0, vy, -1.6)], [0.16, 0.12, 0.08], 14, "#9aa1a5")
    for k in range(3):
        rbc(it, "plastic", 0.1, 1.0, 0.1, 0.0, vy, -1.65, rot=RR("Z", k * math.pi / 3), bevel=0.02, color="#c0392b")
    torus(it, "plastic", 0.5, 0.06, P(0.0, vy, -1.65), color="#c0392b", seg=24, minor=8, rot=Rx(math.pi / 2))
    rpost(it, "plastic", 0.3, y0 + 4.7, y0 + 6.6, -0.95, -0.5, seg=22, color="#e3e0cf")
    for k in range(9):
        rpost(it, "plastic", 0.31, y0 + 4.8 + k * 0.2, y0 + 4.86 + k * 0.2, -0.95, -0.5, seg=22, color="#b9b49c")
    for k, (w, ln) in enumerate(((0.9, 3.0), (0.55, 2.4), (0.25, 1.5))):
        rpoly(it, "stain", streak_pts(-0.2 + k * 0.15, y0 + 3.15, ln, w * 0.2, w * 0.5, rng), -0.03 - k * 0.013, 0.006, ("#dcc9a6", "#c08a56", "#8f4f2a")[k])
    return it


def firealarm():
    it = Item("FireAlarm")
    RED = "#c2312c"
    rbc(it, "plastic", 1.1, 1.5, 0.12, 0, 0, -0.06, bevel=0.04, color="#a82723")
    rbc(it, "plastic", 1.0, 1.4, 0.3, 0, 0, -0.24, bevel=0.1, seg=4, color=RED)
    rbc(it, "plastic", 0.86, 0.22, 0.05, 0, 0.5, -0.4, bevel=0.015, color="#f3efe4")
    for k in range(7):
        rbc(it, "stain", 0.07, 0.1, 0.01, -0.3 + k * 0.1, 0.5, -0.43, color=RED)
    rbc(it, "plastic", 0.5, 0.52, 0.07, 0, -0.02, -0.38, bevel=0.03, color="#f6f3ea")
    for k in range(5):
        rbc(it, "stain", 0.42, 0.025, 0.01, 0, -0.2 + k * 0.1, -0.425, color="#cfcabb")
    rbc(it, "plastic", 0.5, 0.06, 0.1, 0, 0.3, -0.4, bevel=0.015, color="#e7e3d6")
    rpoly(it, "stain", [(0.1, -0.3), (-0.1, -0.3), (-0.1, -0.18), (-0.18, -0.18), (0.0, -0.06), (0.18, -0.18), (0.1, -0.18)], -0.433, 0.008, "#1e1e1e")
    rdisc(it, "metal", 0.09, 0.3, -0.52, -0.39, 0.04, "#a9afac", seg=14)
    rbc(it, "dark", 0.025, 0.1, 0.012, 0.3, -0.52, -0.43, color="#202325")
    rbc(it, "metal", 0.18, 0.5, 0.05, -0.38, -0.5, -0.36, bevel=0.01, color="#b8bcbd")
    _screws(it, [(-0.45, 0.65), (0.45, 0.65), (-0.45, -0.65), (0.45, -0.65)], -0.4, 0.045)
    return it


def firehorn():
    it = Item("FireHorn")
    rbc(it, "plastic", 1.35, 1.35, 0.16, 0, 0, -0.08, bevel=0.05, color="#a82723")
    rbc(it, "plastic", 1.25, 1.25, 0.36, 0, 0, -0.34, bevel=0.14, seg=4, color="#c2312c")
    rdisc(it, "plastic", 0.46, 0, 0.3, -0.55, 0.12, "#ece9e0", bevel=0.04, seg=32)
    rdisc(it, "glow", 0.32, 0, 0.3, -0.66, 0.03, "#fff4d4", seg=32)
    for k in range(6):
        rbc(it, "stain", 0.03, 0.55, 0.01, -0.25 + k * 0.1, 0.3, -0.695, color="#e0d8c0")
    for k in range(7):
        rbc(it, "dark", 0.7, 0.045, 0.04, 0, -0.18 - k * 0.09, -0.52, color="#541511")
    rbc(it, "paper", 0.9, 0.16, 0.02, 0, -0.5, -0.52, color="#f4f0e4")
    for k in range(4):
        rbc(it, "stain", 0.12, 0.1, 0.01, -0.28 + k * 0.19, -0.5, -0.535, color="#c2312c")
    _screws(it, [(-0.5, 0.5), (0.5, 0.5), (-0.5, -0.5), (0.5, -0.5)], -0.5, 0.045)
    return it


_SEG7 = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg"}


def _digit(it, x, y, h, d, z, color="#9dffd4"):
    w = h * 0.55; t = h * 0.12
    seg = {"a": (0, h / 2, w, t), "d": (0, -h / 2, w, t), "g": (0, 0, w, t),
           "b": (w / 2, h / 4, t, h / 2), "c": (w / 2, -h / 4, t, h / 2), "f": (-w / 2, h / 4, t, h / 2), "e": (-w / 2, -h / 4, t, h / 2)}
    for k in _SEG7[d]:
        sx, sy, sw, sh = seg[k]
        rbc(it, "glow", sw, sh, 0.012, x - sx, y + sy, z, color=color)


def thermostat():
    it = Item("Thermostat")
    rbc(it, "plastic", 1.05, 1.35, 0.1, 0, 0, -0.05, bevel=0.03, color="#ddddd2")
    rbc(it, "plastic", 0.95, 1.25, 0.2, 0, 0, -0.18, bevel=0.1, seg=4, color="#f3f3ec")
    rbc(it, "dark", 0.72, 0.5, 0.03, 0, 0.22, -0.285, bevel=0.04, color="#10191b")
    _digit(it, 0.17, 0.22, 0.32, 2, -0.3)
    _digit(it, -0.1, 0.22, 0.32, 1, -0.3)
    rbc(it, "glow", 0.07, 0.07, 0.012, -0.3, 0.14, -0.3, color="#9dffd4")
    rbc(it, "glow", 0.07, 0.07, 0.012, -0.3, 0.37, -0.3, color="#ffb060")                    # heating lamp, clear of the digits
    for x in (-0.25, 0.25):
        rbc(it, "plastic", 0.3, 0.2, 0.05, x, -0.32, -0.3, bevel=0.03, color="#e0e0d4")
    rbc(it, "stain", 0.12, 0.025, 0.01, -0.25, -0.32, -0.33, color="#6a6e6c")
    rbc(it, "stain", 0.12, 0.025, 0.01, 0.25, -0.32, -0.33, color="#6a6e6c")
    rbc(it, "stain", 0.025, 0.12, 0.01, 0.25, -0.32, -0.33, color="#6a6e6c")
    for k in range(5):
        rbc(it, "dark", 0.5, 0.02, 0.015, 0, -0.5 - k * 0.04, -0.285, color="#c4c4b8")
    return it


def cambullet():
    """Bullet camera on a swivel arm: wall plate, knuckle, arm, barrel with sun visor, lens with IR LED ring, cable loop. Aims down and to the
    viewer's right."""
    it = Item("CamBullet")
    rbc(it, "metal", 0.8, 0.8, 0.1, 0, 0, -0.05, bevel=0.03, color="#d7dad7")
    rbc(it, "metal", 0.36, 0.36, 0.5, 0, 0, -0.35, bevel=0.1, color="#d7dad7")
    rtube(it, "metal", [(0, 0.0, -0.4), (0, -0.15, -0.85), (0, -0.3, -1.2)], [0.14, 0.13, 0.13], 14, "#c9ccc9")
    ball(it, "metal", 0.22, P(0, -0.35, -1.25), color="#bfc3c0", seg=14)
    # barrel: from the swivel ball (back) forward along a pitched, yawed axis
    pivot = Vector((0.0, -0.35, -1.25))
    fwd = Vector((-math.sin(0.35) * math.cos(0.3), -math.sin(0.3), -math.cos(0.35) * math.cos(0.3)))      # forward: -z, pitched down 0.3, yawed to the viewer's right (-x)
    p0 = pivot + fwd * 0.15
    p1 = pivot + fwd * 2.0
    rcyl(it, "plastic", 0.38, tuple(p0), tuple(p1), "#e4e7e4", seg=30, bevel=0.06)
    rcyl(it, "dark", 0.3, tuple(p1 + fwd * 0.03), tuple(p1 + fwd * 0.1), "#121618", seg=26)             # lens glass
    rcyl(it, "metal", 0.12, tuple(p1 + fwd * 0.08), tuple(p1 + fwd * 0.12), "#2a3a44", seg=18)
    upv = Vector((0, 1, 0)) - fwd * Vector((0, 1, 0)).dot(fwd)
    upv.normalize()
    rcyl(it, "plastic", 0.44, tuple(p1 - fwd * 0.16), tuple(p1 + fwd * 0.0), "#d3d7d3", seg=30, bevel=0.03)       # front bezel ring
    rcyl(it, "dark", 0.31, tuple(p1), tuple(p1 + fwd * 0.09), "#121618", seg=26)                                  # lens glass, proud of the bezel
    rcyl(it, "metal", 0.12, tuple(p1 + fwd * 0.08), tuple(p1 + fwd * 0.13), "#2a3a44", seg=18)
    sc = (p0 + p1) / 2 + upv * 0.43
    rbc(it, "plastic", 0.66, 0.05, 1.9, sc.x, sc.y, sc.z, rot=rot_to(fwd), bevel=0.02, color="#d9dcd9")           # sun shield on top
    for k in range(10):                                                                                     # IR LEDs around the lens
        a = k / 10 * math.tau
        side = Vector((fwd.z, 0, -fwd.x)).normalized()
        off = side * math.cos(a) * 0.33 + upv * math.sin(a) * 0.33
        c = p1 + fwd * 0.05 + off
        rcyl(it, "glow", 0.035, tuple(c), tuple(c + fwd * 0.06), "#ff4a3a", seg=8)
    rtube(it, "rubber", [(0.0, -0.1, -0.15), (0.35, -0.2, -0.35), (0.5, -0.5, -0.45), (0.4, -0.9, -0.25), (0.15, -1.2, -0.08)], [0.05] * 5, 8, "#1e2123")
    return it


def camdome():
    """Dome camera hanging from an L-bracket: wall plate, bracket, white base ring, smoked dome with a lens block inside, red tally LED."""
    it = Item("CamDome")
    rbc(it, "metal", 0.7, 0.9, 0.1, 0, 0.1, -0.05, bevel=0.03, color="#d7dad7")
    rcyl(it, "metal", 0.2, (0, 0.3, -0.1), (0, 0.3, -1.25), "#d7dad7", seg=16)
    rcyl(it, "metal", 0.2, (0, 0.3, -1.25), (0, -0.05, -1.25), "#d7dad7", seg=16)
    rcyl(it, "plastic", 0.62, (0, -0.05, -1.25), (0, -0.32, -1.25), "#eceeec", seg=34, r2=0.66, bevel=0.03)
    ball(it, "dark", 0.52, P(0, -0.32, -1.25), scale=(1, 1, 0.9), color="#171c1f", seg=26)
    rcyl(it, "plastic", 0.5, (0, -0.32, -1.25), (0, -0.36, -1.25), "#eceeec", seg=34)
    rcyl(it, "metal", 0.17, (0.0, -0.6, -1.0), (0.0, -0.7, -1.2), "#25323a", seg=16)
    ball(it, "glow", 0.05, P(0.34, -0.1, -1.55), color="#ff3b2f", seg=10)
    return it


ITEMS_B = {"elecpanel": elecpanel, "elecpanelopen": elecpanelopen, "piperun": piperun, "piperiser": piperiser, "firealarm": firealarm, "firehorn": firehorn,
           "thermostat": thermostat, "cambullet": cambullet, "camdome": camdome}
