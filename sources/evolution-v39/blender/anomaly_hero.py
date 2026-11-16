"""KONTUR anomaly objects of the main map, Blender level 5: office printer, bathroom mirror frame, picture frame, wall calendar, wall planter,
maintenance vent (frame + hinged leaf), service door and its lever.
Run: Blender -b --python anomaly_hero.py -- <out_dir> [printer,mirrorframe,venthatch_frame,...] [--norender]
Same helpers/exports as hub_hero.py (exec'd). Colours go into the mesh names (<Item>_<material>_<hex>)."""
import sys, math, random
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

_here = Path(__file__).resolve().parent
_src = (_here / "hub_hero.py").read_text()
_head = _src[:_src.index("def tube(")]            # interior_hero helpers + hub MATS
_helpers_src = (_here / "interior_hero.py").read_text()
exec(compile(_helpers_src[:_helpers_src.index("# ---------------------------------------------------------------- items")], "interior_hero_head", "exec"), globals())
exec(compile(_helpers_src[_helpers_src.index("import struct, base64"):_helpers_src.index("def main():")], "interior_hero_tail", "exec"), globals())
# tube/torus helpers and the extra materials of hub_hero.py
_hub = (_here / "hub_hero.py").read_text()
exec(compile(_hub[_hub.index("MATS.update({"):_hub.index("def hazmat():")], "hub_helpers", "exec"), globals())

MATS.update({
    "plant": ("#4a7a4a", .6, 0, 0, 0),
    "leaf": ("#638570", .6, 0, 0, 0),
    "dark": ("#1b2220", .5, 0, 0, 0),
    "tray": ("#8c9685", .5, 0, 0, 0),
    "display": ("#69e0ee", .3, 0, 0, 0),
    "body": ("#bdbfae", .5, 0, 0, 0),
    "lidtop": ("#69796e", .45, 0, 0, 0),
    "alu": ("#a9b6b6", .3, .8, 0, 0),
})


def printer():
    """Office MFP: body 2.48 x 1.76 (x, y) x 1.08, scanner lid to z 1.2, control panel with display, output slot and tray, cassette drawer.
    Origin = body bottom centre, front -Y (body spans y -0.58..1.18 like the old model), x_b = -x_roblox."""
    it = Item("Printer")
    W, y0, y1 = 2.48, -0.58, 1.18
    D = y1 - y0
    cy = (y0 + y1) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(it, "rubber", 0.09, 0.06, (sx * (W / 2 - 0.2), cy + sy * (D / 2 - 0.2), -0.0), seg=12, color="#15181a")
    # plinth and body
    box(it, "body", (W - 0.06, D - 0.06, 0.16), (0, cy, 0.0), bevel=0.05, color="#7c8478")
    box(it, "body", (W, D, 0.92), (0, cy, 0.16), bevel=0.1, seg=3, color="#bdbfae")
    # cassette drawer on the lower front: panel, handle, size indicator
    box(it, "body", (2.0, 0.05, 0.36), (0, y0 - 0.02, 0.2), bevel=0.03, color="#b3b6a4")
    box(it, "dark", (0.8, 0.05, 0.08), (0, y0 - 0.06, 0.34), bevel=0.02, color="#2b3230")
    box(it, "display", (0.18, 0.02, 0.07), (0.7, y0 - 0.05, 0.3), color="#69e0ee") if False else None
    box(it, "paper", (0.22, 0.015, 0.08), (-0.75, y0 - 0.045, 0.26), color="#e8e4d2")
    # output slot (dark recess) and its lip
    box(it, "dark", (1.9, 0.12, 0.2), (0, y0 - 0.0, 0.58), bevel=0.02, color="#1b2220")
    box(it, "body", (2.0, 0.05, 0.05), (0, y0 - 0.03, 0.79), bevel=0.015, color="#a9ab9a")
    # scanner lid: overhang, gasket, hinges, finger recess
    box(it, "dark", (W - 0.06, D - 0.1, 0.03), (0, cy, 1.07), bevel=0.01, color="#1b2220")                # gasket
    box(it, "lidtop", (W + 0.04, D + 0.04, 0.1), (0, cy, 1.1), bevel=0.05, seg=2, color="#69796e")
    box(it, "dark", (0.8, 0.06, 0.04), (0, y0 - 0.03, 1.11), bevel=0.015, color="#1b2220")                # finger recess
    for sx in (-1, 1):
        cyl(it, "alu", 0.05, 0.3, (sx * 0.85, y1 + 0.02, 1.05), rot=Ry(math.pi / 2), seg=12, color="#a9b6b6")   # hinges
    # control panel (tilted, front right in Roblox = x_b negative): plate, display, buttons, nav pad
    panel_c = (-0.52, y0 - 0.0, 1.0)
    plate = box(it, "dark", (1.25, 0.34, 0.07), (-0.52, y0 + 0.17, 1.12), bevel=0.02, color="#242b29", rot=Rx(0.32) if False else None) if False else None
    box(it, "body", (1.3, 0.4, 0.1), (-0.5, y0 + 0.22, 1.0), bevel=0.04, color="#a9ab9a", rot=Rx(-0.22))
    box(it, "dark", (0.86, 0.02, 0.34), (-0.48, y0 - 0.03, 0.98), bevel=0.01, color="#171c1b", rot=Rx(-0.22))     # screen bezel (visible from the front)
    box(it, "display", (0.74, 0.02, 0.26), (-0.48, y0 - 0.045, 1.0), color="#69e0ee", rot=Rx(-0.22))
    for k in range(5):
        cyl(it, "plastic_gray", 0.045, 0.03, (0.04 + k * 0.17 + 0.2, y0 - 0.045, 0.99 - 0.0), rot=Rx(math.pi / 2 - 0.22), seg=12, color=["#3d8a5c", "#c0a23a", "#b8433a", "#4a6a8a", "#8a8f86"][k])
    cyl(it, "plastic_gray", 0.1, 0.03, (-1.0, y0 - 0.045, 0.99), rot=Rx(math.pi / 2 - 0.22), seg=16, color="#8a8f86", bevel=0.01)   # nav pad
    box(it, "metal", (0.16, 0.02, 0.06), (-1.04, y0 - 0.02, 0.9), color="#9aa1a8")                         # USB port
    # status LED, brand badge
    ball(it, "display", 0.025, (0.4, y0 - 0.05, 0.9), seg=8, color="#7cf29a")
    box(it, "dark", (0.5, 0.02, 0.1), (0.62, y0 - 0.04, 0.72), bevel=0.01, color="#2b3230")
    # side vents (slits) on both sides
    for sx in (-1, 1):
        for k in range(7):
            box(it, "dark", (0.03, 0.9, 0.03), (sx * (W / 2 + 0.0), cy + 0.1, 0.3 + k * 0.1), color="#2b3230")
    # output tray: sloped plate with side guides, paper stack and one sheet half out
    for k in range(2):
        pass
    tray = box(it, "tray", (1.96, 0.8, 0.05), (0, y0 - 0.38, 0.5), bevel=0.02, color="#8c9685", rot=Rx(0.1))
    for sx in (-1, 1):
        box(it, "tray", (0.05, 0.8, 0.12), (sx * 0.98, y0 - 0.38, 0.52), bevel=0.015, color="#7c8478")
    box(it, "paper", (1.44, 0.64, 0.03), (0, y0 - 0.4, 0.55), bevel=0.005, color="#ebe6d6", rot=Rx(0.1))
    box(it, "paper", (1.42, 0.5, 0.012), (0.04, y0 - 0.08, 0.58), color="#f2efe4", rot=Rx(0.1))
    return it


def mirrorframe():
    """Mirror frame 2.59 x 3.35 (x, z) with the opening 2.43 x 3.16: aluminium bars with a raised inner lip, corner brackets, four wall standoffs.
    Origin = bottom centre of the mirror at the wall, front -Y (frame depth y -0.11..-0.03)."""
    it = Item("MirrorFrame")
    W, H = 2.59, 3.35
    bar_x, bar_z = 0.08, 0.095
    d = 0.08
    yc = -0.07
    # bars (mitred by overlap), chamfered
    box(it, "alu", (bar_x, d, H), (-W / 2 + bar_x / 2, yc, 0.0), bevel=0.018, color="#a7b3b3")
    box(it, "alu", (bar_x, d, H), (W / 2 - bar_x / 2, yc, 0.0), bevel=0.018, color="#a7b3b3")
    box(it, "alu", (W - 2 * bar_x + 0.02, d, bar_z), (0, yc, 0.0), bevel=0.018, color="#a7b3b3")
    box(it, "alu", (W - 2 * bar_x + 0.02, d, bar_z), (0, yc, H - bar_z), bevel=0.018, color="#a7b3b3")
    # inner lip raised in front of the glass (thin chamfered edge) and a dark gasket line
    box(it, "alu", (W - 2 * bar_x + 0.03, 0.025, 0.02), (0, yc - 0.045, bar_z - 0.012), color="#c8d2d2")
    box(it, "alu", (W - 2 * bar_x + 0.03, 0.025, 0.02), (0, yc - 0.045, H - bar_z - 0.008), color="#c8d2d2")
    for sx in (-1, 1):
        box(it, "alu", (0.02, 0.025, H - 2 * bar_z), (sx * (W / 2 - bar_x - 0.0), yc - 0.045, bar_z), color="#c8d2d2")
    # corner brackets (small squares with screws)
    for sx in (-1, 1):
        for z in (0.02, H - 0.1):
            box(it, "alu", (0.14, 0.02, 0.1), (sx * (W / 2 - 0.1), yc - 0.05, z), bevel=0.008, color="#8f9c9c")
            cyl(it, "metal", 0.016, 0.012, (sx * (W / 2 - 0.1), yc - 0.062, z + 0.05), rot=Rx(math.pi / 2), seg=8, color="#6a7272")
    # wall standoffs
    for sx in (-1.01, 1.01):
        for z in (0.34, 2.97):
            cyl(it, "metal", 0.05, 0.06, (sx, -0.015, z), rot=Rx(math.pi / 2), seg=12, color="#a7b3b3")
    return it


def artframe(W=5.3, H=3.72):
    """Archive picture frame (WorldTrade / GrowthTechnology): dark steel frame with a gold inner lip, backboard, rear tabs and wall bumpers.
    The mat, artwork and rear label of the game stay; origin = bottom centre of the frame, front -Y (frame y -0.10..0.08, backboard 0.05..0.09)."""
    it = Item("ArtFrame")
    bar = 0.14
    steel, gold = "#263238", "#bf9e4f"
    yc, d = -0.01, 0.18
    box(it, "alu", (bar, d, H), (-W / 2 + bar / 2, yc, 0.0), bevel=0.03, seg=2, color=steel)
    box(it, "alu", (bar, d, H), (W / 2 - bar / 2, yc, 0.0), bevel=0.03, seg=2, color=steel)
    box(it, "alu", (W - 2 * bar + 0.04, d, bar), (0, yc, 0.0), bevel=0.03, seg=2, color=steel)
    box(it, "alu", (W - 2 * bar + 0.04, d, bar), (0, yc, H - bar), bevel=0.03, seg=2, color=steel)
    # stepped moulding: slightly raised outer face line and the gold inner lip (all four sides)
    for sx in (-1, 1):
        box(it, "brass", (0.025, 0.04, H - 2 * bar + 0.02), (sx * (W / 2 - bar - 0.0125), -0.11, bar - 0.01), bevel=0.008, color=gold)
        box(it, "alu", (0.02, 0.03, H - 0.06), (sx * (W / 2 - 0.05), -0.108, 0.03), bevel=0.006, color="#3a4850")
    for z in (bar - 0.0125, H - bar + 0.0125 - 0.025):
        box(it, "brass", (W - 2 * bar + 0.05, 0.04, 0.025), (0, -0.11, z), bevel=0.008, color=gold)
    for z in (0.025, H - 0.045):
        box(it, "alu", (W - 0.06, 0.03, 0.02), (0, -0.108, z), bevel=0.006, color="#3a4850")
    # corner caps
    for sx in (-1, 1):
        for z in (0.0, H - 0.1):
            box(it, "brass", (0.1, 0.05, 0.1), (sx * (W / 2 - 0.05), -0.105, z), bevel=0.02, color=gold)
    # backboard
    box(it, "alu", (W - 0.02, 0.04, H - 0.05), (0, 0.07, 0.025), bevel=0.01, color=steel)
    # rear mounting tabs with screws and wall bumpers
    for sx in (-1.48, 1.48):
        box(it, "metal", (0.14, 0.012, 0.33), (sx, 0.106, H - 0.4), bevel=0.004, color="#9ca6a8")
        cyl(it, "metal", 0.022, 0.014, (sx, 0.118, H - 0.26), rot=Rx(math.pi / 2), seg=10, color="#9ca6a8")
    for sx in (-2.22, 2.22):
        for z in (0.22, H - 0.28):
            cyl(it, "rubber", 0.045, 0.04, (sx, 0.13, z), rot=Rx(math.pi / 2), seg=10, color="#2b3033")
    return it


def wallcalendar():
    """Hanging wall calendar: steel-blue backing board, stack of page sheets with a curl, 21 spiral coils, wire hanger.
    The printed page (WallCalendarPrint) and the hanging joints stay in the game; origin = bottom centre at the wall, front -Y."""
    it = Item("WallCalendar")
    steel = "#263238"
    box(it, "alu", (1.45, 0.045, 1.94), (0, 0.035, 0.0), bevel=0.012, seg=2, color=steel)
    # page stack: four sheets, slightly offset, cream; the front sheet is covered by the game's printed page
    for k in range(5):
        box(it, "paper", (1.37 - k * 0.004, 0.006, 1.78 - k * 0.006), (0.0, 0.012 - k * 0.0065, 0.06 + k * 0.006), color="#ece7d6")
    # bottom page curl: a thin cylinder segment along the lower edge
    cyl(it, "paper", 0.018, 1.36, (-0.68, -0.035, 0.07), rot=Ry(math.pi / 2), seg=10, color="#e4dfcd")
    # spiral binding: coils around the top edge
    for k in range(21):
        x = -0.64 + k * 0.065
        torus(it, "metal_dark", 0.05, 0.011, (x, -0.003, 1.865), rot=Ry(math.pi / 2), color="#434a4f", seg=14, minor=6)
    # hanger: triangle of wire over the top centre
    tube(it, "metal", [(-0.18, 0.0, 1.93), (-0.18, 0.0, 2.12), (0.0, 0.0, 2.24), (0.18, 0.0, 2.12), (0.18, 0.0, 1.93)], [0.012] * 5, 8, "#9ca6a8", caps=True)
    box(it, "metal", (0.5, 0.03, 0.06), (0, 0.02, 1.9), bevel=0.01, color="#7c868a")             # hanger bar behind the coils
    # corner protectors on the board
    for sx in (-1, 1):
        for z in (0.0, 1.9):
            box(it, "metal", (0.06, 0.05, 0.05), (sx * 0.7, 0.036, z), bevel=0.01, color="#434a4f")
    return it


def wallplanter():
    """Wall planter: teal steel trough (2.25 x 0.53 x 0.48) with a rolled rim, rear brackets, soil with pebbles, seven stems with 42 leaf blades.
    The leaf groups are named LeafBlade in the game so the WestPlanterColor anomaly can recolour them. origin = bottom centre, y = depth (wall at +0.33)."""
    it = Item("WallPlanter")
    rnd = random.Random(14)
    teal, dark = "#407278", "#263238"
    L, D, H = 2.25, 0.53, 0.48
    box(it, "alu", (L, D, H), (0, 0.0, 0.0), bevel=0.045, seg=3, color=teal)
    # rolled rim and bottom plate
    for sy in (-1, 1):
        box(it, "alu", (L + 0.04, 0.05, 0.05), (0, sy * (D / 2 - 0.0), H - 0.03), bevel=0.02, color="#5c9199")
    for sx in (-1, 1):
        box(it, "alu", (0.05, D + 0.04, 0.05), (sx * (L / 2 - 0.0), 0, H - 0.03), bevel=0.02, color="#5c9199")
    box(it, "alu", (L - 0.12, D - 0.12, 0.03), (0, 0, -0.0), bevel=0.01, color=dark)
    # rear wall brackets with countersunk screws
    for sx in (-0.7, 0.7):
        box(it, "alu", (0.12, 0.035, 0.66), (sx, D / 2 + 0.04, 0.05), bevel=0.012, color=dark)
        box(it, "alu", (0.12, 0.06, 0.07), (sx, D / 2 + 0.01, 0.22), bevel=0.012, color=dark)
        for z in (0.18, 0.55):
            cyl(it, "metal", 0.022, 0.012, (sx, D / 2 + 0.06, z), rot=Rx(math.pi / 2), seg=10, color="#9ca6a8")
    # soil mound and pebbles
    box(it, "plant", (L - 0.14, D - 0.1, 0.07), (0, 0, H - 0.07), bevel=0.03, seg=2, color="#4c4533")
    for k in range(14):
        ball(it, "ceramic", rnd.uniform(0.012, 0.022), (rnd.uniform(-1.0, 1.0), rnd.uniform(-0.15, 0.15), H + 0.0), scale=(1, 1, 0.6), seg=8, color=rnd.choice(["#9a9588", "#b0aa9a", "#7e7a70"]))
    # seven stems with leaf sprays
    greens = ["#638570", "#417278"]
    for i in range(7):
        x = -0.9 + i * 0.3 + rnd.uniform(-0.05, 0.05)
        y = rnd.uniform(-0.08, 0.08)
        top = H + rnd.uniform(0.45, 0.82)
        lean = rnd.uniform(-0.12, 0.12)
        pts = [(x, y, H), (x + lean * 0.4, y, H + (top - H) * 0.4), (x + lean, y + 0.02, top)]
        tube(it, "plant", pts, [0.014, 0.011, 0.008], 6, "#4a6e5a")
        for k in range(6):
            t = 0.3 + 0.7 * k / 5
            px = x + lean * t + (0.06 if k % 2 else -0.06)
            pz = H + (top - H) * t
            side = 1 if k % 2 else -1
            col = greens[(i + k) % 2]
            ball(it, "leaf", 0.1, (px + side * 0.05, y + 0.02 * side, pz), scale=(0.7, 0.14, 1.5), seg=10, color=col, rot=Ry(side * 0.6) @ Rx(rnd.uniform(-0.3, 0.3)))
        ball(it, "leaf", 0.09, (x + lean, y + 0.02, top + 0.09), scale=(0.7, 0.14, 1.5), seg=10, color=greens[i % 2], rot=Rx(rnd.uniform(-0.2, 0.2)))
    return it


# ---------------------------------------------------------------- wall objects built by the server (maintenance vent, service door)
# Table coordinates of the game (OfficeObjects.server): x = horizontal (Roblox local right), y = height, n = projection from the wall.
# Blender: x_b = -x, y_b = -n (front = -Y), z_b = y. All values below are final studs.
def tb(it, mat, w, h, d, x, y, n, bevel=0.0, seg=2, color=None, tilt=0.0):
    """Box centred at table point (x, y, n); w along x, h along y (up), d along n. tilt = Roblox rotation about the right axis."""
    if tilt:
        rot = Rx(-tilt)
        c = Vector((-x, -n, y))
        pos = c - (rot @ Vector((0, 0, h / 2)))
        box(it, mat, (w, d, h), (pos.x, pos.y, pos.z), bevel, seg, color, rot)
    else:
        box(it, mat, (w, d, h), (-x, -n, y - h / 2), bevel, seg, color)


def tpost(it, mat, r, h, x, y0, n, seg=14, color=None, bevel=0.0):
    """Vertical cylinder from height y0 up by h at table (x, n)."""
    cyl(it, mat, r, h, (-x, -n, y0), seg=seg, color=color, bevel=bevel)


def tface(it, mat, r, h, x, y, n0, seg=14, color=None, bevel=0.0):
    """Cylinder whose axis is the projection direction: base at depth n0, extends toward the viewer by h."""
    cyl(it, mat, r, h, (-x, -n0, y), seg=seg, color=color, rot=Rx(math.pi / 2), bevel=bevel)


VS = 0.6                       # ventScale of the game


def venthatch_frame():
    """Maintenance vent, fixed part: wall flange with raised inner lip, duct recess with baffles, full gasket, six cross-head screws,
    two hinge barrels with pin caps. Origin = hatch centre at the wall, projection toward -Y, hatch opening 1.9 x 1.79 (x S)."""
    it = Item("VentFrame")
    S = VS
    FL, LIP, DARK, HINGE = "#738076", "#919a8b", "#2e3731", "#3a463f"
    # flange: four bars, chamfered, slightly stepped; the rolled outer edge is a second thin bar
    tb(it, "alu", 2.24 * S, 0.17 * S, 0.132 * S, 0, -0.98 * S, 0.067 * S, bevel=0.012, seg=2, color=FL)
    tb(it, "alu", 2.24 * S, 0.17 * S, 0.132 * S, 0, 0.98 * S, 0.067 * S, bevel=0.012, seg=2, color=FL)
    tb(it, "alu", 0.17 * S, 1.86 * S, 0.132 * S, -1.037 * S, 0, 0.067 * S, bevel=0.012, seg=2, color=FL)
    tb(it, "alu", 0.17 * S, 1.86 * S, 0.132 * S, 1.037 * S, 0, 0.067 * S, bevel=0.012, seg=2, color=FL)
    for sy in (-1, 1):
        tb(it, "alu", 2.3 * S, 0.035 * S, 0.05 * S, 0, sy * 1.07 * S, 0.036 * S, bevel=0.006, color="#8a968c")
    for sx in (-1, 1):
        tb(it, "alu", 0.035 * S, 2.1 * S, 0.05 * S, sx * 1.12 * S, 0, 0.036 * S, bevel=0.006, color="#8a968c")
    # raised inner lip
    tb(it, "alu", 1.96 * S, 0.047 * S, 0.1 * S, 0, -0.878 * S, 0.125 * S, bevel=0.008, color=LIP)
    tb(it, "alu", 1.96 * S, 0.047 * S, 0.1 * S, 0, 0.878 * S, 0.125 * S, bevel=0.008, color=LIP)
    tb(it, "alu", 0.047 * S, 1.76 * S, 0.1 * S, -0.944 * S, 0, 0.125 * S, bevel=0.008, color=LIP)
    tb(it, "alu", 0.047 * S, 1.76 * S, 0.1 * S, 0.944 * S, 0, 0.125 * S, bevel=0.008, color=LIP)
    # duct recess: dark back plate and three baffles so the opening reads deep
    tb(it, "dark", 2.0 * S, 1.85 * S, 0.042 * S, 0, 0, 0.031 * S, color="#1f2720")
    for y in (-0.55, 0.0, 0.55):
        tb(it, "dark", 1.78 * S, 0.07 * S, 0.05 * S, 0, y * S, 0.075 * S, bevel=0.004, color="#2a342d")
    tb(it, "dark", 0.07 * S, 1.64 * S, 0.05 * S, 0.0, 0, 0.062 * S, bevel=0.004, color="#2a342d")
    # gasket loop under the leaf
    tb(it, "rubber", 1.88 * S, 0.022 * S, 0.035 * S, 0, -0.89 * S, 0.114 * S, bevel=0.004, color=DARK)
    tb(it, "rubber", 1.88 * S, 0.022 * S, 0.035 * S, 0, 0.89 * S, 0.114 * S, bevel=0.004, color=DARK)
    tb(it, "rubber", 0.022 * S, 1.76 * S, 0.035 * S, -0.935 * S, 0, 0.114 * S, bevel=0.004, color=DARK)
    tb(it, "rubber", 0.022 * S, 1.76 * S, 0.035 * S, 0.935 * S, 0, 0.114 * S, bevel=0.004, color=DARK)
    # six cross-head screws on the side flanges
    for x in (-1.017, 1.017):
        for y in (-0.81, 0.0, 0.81):
            tface(it, "metal", 0.027 * S * 1.0, 0.026 * S, x * S, y * S, 0.1295 * S, seg=12, color="#a4a692", bevel=0.004)
            tb(it, "dark", 0.034 * S, 0.008 * S, 0.01 * S, x * S, y * S, 0.1555 * S, color="#3f4539")
            tb(it, "dark", 0.008 * S, 0.034 * S, 0.01 * S, x * S, y * S, 0.1555 * S, color="#3f4539")
    # hinge barrels (axis vertical) with pin caps and a short mounting strap onto the flange
    for y in (-0.6, 0.6):
        tpost(it, "metal_dark", 0.052 * S, 0.26 * S, -1.0 * S, (y - 0.13) * S, 0.174 * S, seg=14, color=HINGE, bevel=0.006)
        tb(it, "alu", 0.1 * S, 0.22 * S, 0.014 * S, -1.02 * S, y * S, 0.1 * S, bevel=0.004, color=LIP)
        for cap in (-1, 1):
            tpost(it, "metal", 0.034 * S, 0.034 * S, -1.0 * S, (y + cap * 0.13 - (0.034 if cap > 0 else 0)) * S, 0.174 * S, seg=12, color=LIP, bevel=0.005)
    return it


def venthatch_leaf():
    """Maintenance vent, hinged leaf: rail frame, seven tilted louvers with return strips and three vertical straps, quarter-turn latch.
    Same origin as VentFrame (the game rotates the whole leaf about the hinge axis x = -0.97, n = 0.17)."""
    it = Item("VentLeaf")
    S = VS
    RAIL, LOUV = "#919a8b", ["#788477", "#7b8879", "#7e8b7b"]
    tb(it, "alu", 0.085 * S, 1.7 * S, 0.085 * S, -0.91 * S, 0, 0.17 * S, bevel=0.006, seg=2, color=RAIL)
    tb(it, "alu", 0.085 * S, 1.7 * S, 0.085 * S, 0.91 * S, 0, 0.17 * S, bevel=0.006, seg=2, color=RAIL)
    tb(it, "alu", 1.75 * S, 0.085 * S, 0.085 * S, 0, -0.81 * S, 0.17 * S, bevel=0.006, seg=2, color=RAIL)
    tb(it, "alu", 1.75 * S, 0.085 * S, 0.085 * S, 0, 0.81 * S, 0.17 * S, bevel=0.006, seg=2, color=RAIL)
    # louvers: tilted slats (top edge out), each with a dark return strip behind its lower edge
    for i in range(7):
        y = -0.65 + i * 0.214
        tb(it, "alu", 1.75 * S, 0.118 * S, 0.048 * S, 0, y * S, 0.17 * S, bevel=0.007, seg=2, color=LOUV[i % 3], tilt=-0.3839724354387525)
        tb(it, "dark", 1.74 * S, 0.019 * S, 0.031 * S, 0, (y - 0.033) * S, 0.193 * S, bevel=0.003, color="#2e3731")
    # vertical straps behind the slats keep them together
    for x in (-0.45, 0.0, 0.45):
        tb(it, "metal_dark", 0.03 * S, 1.64 * S, 0.026 * S, x * S, 0, 0.146 * S, bevel=0.003, color="#3a463f")
    # hinge straps on the rail
    for y in (-0.6, 0.6):
        tb(it, "alu", 0.09 * S, 0.22 * S, 0.014 * S, -0.97 * S, y * S, 0.134 * S, bevel=0.004, color=RAIL)
    # quarter-turn latch: housing, face plate, knob with a slot
    tb(it, "metal_dark", 0.126 * S, 0.24 * S, 0.094 * S, 0.985 * S, -0.02 * S, 0.205 * S, bevel=0.01, seg=2, color="#2e3731")
    tb(it, "alu", 0.082 * S, 0.142 * S, 0.029 * S, 0.985 * S, -0.02 * S, 0.261 * S, bevel=0.008, color=RAIL)
    tface(it, "metal", 0.034 * S, 0.02 * S, 0.985 * S, -0.02 * S, 0.272 * S, seg=14, color="#b6bba8", bevel=0.004)
    tb(it, "dark", 0.052 * S, 0.011 * S, 0.008 * S, 0.985 * S, -0.02 * S, 0.292 * S, color="#2e3731")
    return it


def servicedoor():
    """Unlisted service door (WhisperDoor anomaly): grey-green pressed-steel leaf with an inset groove, stepped dark frame with stops and
    seal, kick plate with screws, lock escutcheon with a cylinder, three hinges with knuckles, threshold, sign-plate bezel.
    The game keeps SignPlate (the text) and its screws as parts; the lever is a separate mesh (DoorLever). Origin = table origin
    (door centre line, floor + 0.1, wall plane), projection toward -Y."""
    it = Item("ServiceDoor")
    LEAF, JAMB, STOP, KICK, HING = "#6f8377", "#27413e", "#4a5e57", "#717c74", "#67756c"
    # shadow rebate behind the frame
    tb(it, "dark", 4.34, 9.04, 0.033, 0, 4.54, 0.001 + 0.016, color="#17201e")
    # frame: stepped jambs (outer jamb + inner stop), head, seal
    tb(it, "paint", 0.19, 9.04, 0.24, -2.12, 4.52, 0.032 + 0.0, bevel=0.025, seg=2, color=JAMB)
    tb(it, "paint", 0.19, 9.04, 0.24, 2.12, 4.52, 0.032 + 0.0, bevel=0.025, seg=2, color=JAMB)
    tb(it, "paint", 4.43, 0.2, 0.24, 0, 9.02, 0.032 + 0.0, bevel=0.025, seg=2, color=JAMB)
    tb(it, "paint", 0.046, 8.94, 0.042, -1.99, 4.49, 0.08, bevel=0.01, color=STOP)
    tb(it, "paint", 0.046, 8.94, 0.042, 1.99, 4.49, 0.08, bevel=0.01, color=STOP)
    tb(it, "paint", 3.98, 0.046, 0.042, 0, 8.89, 0.08, bevel=0.01, color=STOP)
    for sx in (-1, 1):
        tb(it, "rubber", 0.026, 8.7, 0.03, sx * 1.945, 4.4, 0.09, bevel=0.005, color="#1b2220")
    tb(it, "rubber", 3.86, 0.026, 0.03, 0, 8.76, 0.09, bevel=0.005, color="#1b2220")
    # floor threshold strip
    tb(it, "metal", 3.99, 0.07, 0.3, 0, 0.065, 0.14, bevel=0.012, color="#8f988f")
    # leaf: slab with rolled edge, then a shallow inset groove (four thin dark strips) and a raised border
    tb(it, "paint", 3.89, 8.81, 0.115, 0, 4.47, 0.025, bevel=0.03, seg=3, color=LEAF)
    for y in (8.45, 0.82):
        tb(it, "paint", 3.3, 0.04, 0.012, 0, y, 0.088, bevel=0.004, color="#566a5f")
    for x in (-1.65, 1.65):
        tb(it, "paint", 0.04, 7.67, 0.012, x, 4.635, 0.088, bevel=0.004, color="#566a5f")
    for y in (8.41, 0.86):
        tb(it, "paint", 3.3, 0.03, 0.008, 0, y, 0.0885, bevel=0.003, color="#85998c")
    # horizontal stiffening rib across the middle, below the sign plate
    tb(it, "paint", 3.3, 0.14, 0.02, 0, 5.4, 0.088, bevel=0.01, seg=2, color="#6a7d71")
    # kick plate with four screws
    tb(it, "metal", 3.70, 0.52, 0.019, 0, 0.41, 0.088, bevel=0.006, color=KICK)
    tb(it, "metal", 3.69, 0.014, 0.013, 0, 0.674, 0.1, bevel=0.003, color="#919791")
    for x in (-1.75, 1.75):
        for y in (0.24, 0.59):
            tface(it, "metal", 0.0185, 0.012, x, y, 0.0975, seg=10, color="#9b9f8f", bevel=0.003)
    # lock: round escutcheon with cylinder and key slot, two screws
    tface(it, "metal", 0.145, 0.045, -1.48, 4.27, 0.088, seg=22, color="#6f7a73", bevel=0.01)
    tb(it, "metal", 0.29, 0.63, 0.012, -1.48, 4.27, 0.094, bevel=0.006, color="#6f7a73")
    tface(it, "metal", 0.052, 0.04, -1.48, 4.10, 0.132, seg=18, color="#9fa493", bevel=0.006)
    tb(it, "dark", 0.027, 0.012, 0.013, -1.48, 4.10, 0.173, color="#222b28")
    for y in (4.54, 4.01):
        tface(it, "metal", 0.017, 0.015, -1.48, y, 0.13, seg=10, color="#97a191", bevel=0.003)
    # hinges: leaf plates on the jamb side, three knuckles each, pin cap
    for y in (1.28, 4.49, 7.67):
        tb(it, "metal", 0.15, 0.4, 0.014, 1.88, y, 0.1, bevel=0.003, color=HING)
        tb(it, "metal", 0.12, 0.4, 0.014, 1.99, y, 0.062, bevel=0.003, color=HING)
        for k in range(3):
            tpost(it, "metal", 0.048, 0.125, 1.925, y - 0.2 + k * 0.1375, 0.118, seg=14, color=HING, bevel=0.004)
        tpost(it, "metal", 0.03, 0.03, 1.925, y + 0.2, 0.118, seg=12, color="#8f9a91", bevel=0.004)
    # sign-plate bezel (the game's SignPlate part sits inside it) and a drip lip above the door
    tb(it, "metal", 1.9, 0.045, 0.045, 0, 6.54, 0.1, bevel=0.01, color="#8a8f80")
    tb(it, "metal", 1.9, 0.045, 0.045, 0, 6.14, 0.1, bevel=0.01, color="#8a8f80")
    for sx in (-1, 1):
        tb(it, "metal", 0.045, 0.45, 0.045, sx * 0.925, 6.34, 0.1, bevel=0.01, color="#8a8f80")
    tb(it, "metal", 4.5, 0.06, 0.34, 0, 9.18, 0.17, bevel=0.015, color="#7a847c")
    return it


def doorlever():
    """Service-door lever handle: round boss, neck and a rounded lever with a knob. Origin = the rotation axis of the lever at the plane
    of the game's lever pivot (n = 0.236); the handle points toward table -x ... +x (towards the door centre)."""
    it = Item("DoorLever")
    BRASS, DARKM = "#979c8d", "#6f7a73"
    n0 = 0.236
    # boss and rose (axis = projection direction, base slightly behind the pivot plane)
    tface(it, "metal", 0.108, 0.065, -1.48, 4.43, n0 - 0.05, seg=24, color="#8b9184", bevel=0.012)
    tface(it, "metal", 0.062, 0.05, -1.48, 4.43, n0 + 0.015, seg=20, color=BRASS, bevel=0.01)
    # lever arm from the boss toward +x (towards the centre of the door): rounded bar with a flat end knob
    tb(it, "metal", 0.50, 0.075, 0.064, -1.23, 4.43, n0 + 0.018, bevel=0.028, seg=3, color=BRASS)
    ball(it, "metal", 0.052, (-(-1.0), -(n0 + 0.018), 4.43), scale=(1.0, 0.95, 1.1), seg=14, color="#a1a696")
    return it


ITEMS = {"printer": printer, "mirrorframe": mirrorframe, "artframe": artframe, "wallcalendar": wallcalendar, "wallplanter": wallplanter,
         "venthatch_frame": venthatch_frame, "venthatch_leaf": venthatch_leaf, "servicedoor": servicedoor, "doorlever": doorlever}


def main():
    names = WANT or list(ITEMS)
    luau = []
    for n in names:
        sc = setup_scene()
        it = ITEMS[n]()
        objs = finish(it)
        stats(it.name, objs)
        if RENDER:
            render_views(sc, it.name, objs)
        export(it.name, objs)
    print("DONE", flush=True)


main()
