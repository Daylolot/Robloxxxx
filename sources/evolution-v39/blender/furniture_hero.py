"""KONTUR office furniture of the main map, Blender level 5 (chairs; desks and monitors follow).
Run: Blender -b --python furniture_hero.py -- <out_dir> [ergochair] [--norender]
Same helpers/exports as anomaly_hero.py (exec'd). Colours go into the mesh names (<Item>_<material>_<hex>)."""
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
    "dark": ("#1b2220", .5, 0, 0, 0),
    "leather": ("#434442", .55, 0, 0, 0),
    "softplastic": ("#262729", .6, 0, 0, 0),
    "alu": ("#a9b6b6", .3, .8, 0, 0),
})

# Office furniture of the main map, Blender level 5. The game models are built from hundreds of parts; the meshes replace them,
# the game's PlacementPivot (origin, 'front' = model look vector) and the collision parts stay.
# Chair coordinates: Roblox local (x right, y up, z back) -> Blender (x_b = -x, y_b = z, z_b = y): front = -Y, up = +Z.


def rb(it, mat, w, h, d, x, y, z, bevel=0.0, seg=2, color=None, rot=None):
    """Box centred at the Roblox-local point (x, y, z): w along x, h along y (up), d along z (toward the back)."""
    box(it, mat, (w, d, h), (-x, z, y - h / 2), bevel, seg, color, rot)


def rpost(it, mat, r, y0, y1, x, z, seg=18, color=None, bevel=0.0):
    cyl(it, mat, r, y1 - y0, (-x, z, y0), seg=seg, color=color, bevel=bevel)


def ergochair():
    """Office swivel chair: five-star base with twin-wheel casters, gas lift with sleeve, tilt mechanism, quilted leather seat, mesh-style
    backrest with lumbar pad and headrest, T-arms with soft pads. Origin = floor under the gas lift (PlacementPivot), front -Y."""
    it = Item("ErgoChair")
    METAL, CHROME, DARKM, LEATHER, SOFT, RUB = "#8f9496", "#b8bcbe", "#44474a", "#434442", "#262729", "#1e1f21"
    # five-star base: one spoke points to the front; hub, tapered rising spokes, casters at the tips
    cyl(it, "metal", 0.23, 0.2, (0, 0, 0.47), seg=24, color=METAL, bevel=0.03)
    for k in range(5):
        a = -math.pi / 2 + k * math.tau / 5
        d = Vector((math.cos(a), math.sin(a), 0.0))
        t = Vector((-math.sin(a), math.cos(a), 0.0))
        pts = [tuple(d * 0.12 + Vector((0, 0, 0.60))), tuple(d * 0.55 + Vector((0, 0, 0.57))), tuple(d * 1.02 + Vector((0, 0, 0.50)))]
        tube(it, "metal", pts, [0.12, 0.10, 0.075], 10, METAL, squash=(1.0, 0.72))
        tip = d * 1.02
        cyl(it, "metal", 0.085, 0.07, tuple(tip + Vector((0, 0, 0.43))), seg=14, color=METAL, bevel=0.01)          # caster socket
        cyl(it, "metal_dark", 0.045, 0.2, tuple(tip + Vector((0, 0, 0.27))), seg=12, color=DARKM)                      # stem
        # fork: two cheeks either side of the twin wheels, a bridge on top
        rot = Rz(a)
        for s in (-1, 1):
            c = tip + t * (0.115 * s) + Vector((0, 0, 0.17))
            box(it, "metal_dark", (0.2, 0.025, 0.28), (c.x, c.y, c.z - 0.0), bevel=0.008, color=DARKM, rot=rot)
        box(it, "metal_dark", (0.2, 0.26, 0.04), (tip.x, tip.y, tip.z + 0.29), bevel=0.01, color=DARKM, rot=rot)
        # twin wheels (axis along the tangent)
        for s in (-1, 1):
            axis = t
            centre = tip + t * (0.065 * s) + Vector((0, 0, 0.17))
            start = centre - axis * 0.045
            cyl(it, "rubber", 0.17, 0.09, tuple(start), seg=20, color=RUB, rot=Rz(a + math.pi / 2) @ Ry(math.pi / 2), bevel=0.025)
    # gas lift: black sleeve with ribbed bands, chrome rod, bellows rings
    cyl(it, "metal_dark", 0.13, 0.81, (0, 0, 0.44), seg=22, color="#2c2f32", bevel=0.02)
    for z in (0.62, 0.9, 1.14):
        cyl(it, "metal_dark", 0.145, 0.03, (0, 0, z), seg=22, color="#3a3e42", bevel=0.008)
    cyl(it, "metal", 0.07, 0.62, (0, 0, 1.25), seg=16, color=CHROME)
    # tilt mechanism housing, side covers, knob and height lever (lever on the right = Roblox +x = Blender -x)
    rb(it, "metal_dark", 0.94, 0.17, 0.81, 0, 1.875, 0.035, bevel=0.05, seg=3, color=DARKM)
    rb(it, "metal_dark", 0.84, 0.05, 0.7, 0, 1.775, 0.04, bevel=0.015, color="#383b3f")
    cyl(it, "rubber", 0.075, 0.1, (0.47, 0.24, 1.9), seg=16, color=RUB, rot=Ry(math.pi / 2), bevel=0.02)             # tilt knob on the left side
    rb(it, "metal", 0.66, 0.05, 0.05, 0.66, 1.83, -0.1, bevel=0.01, color=CHROME)
    cyl(it, "rubber", 0.055, 0.25, (-0.94, -0.1, 1.81), seg=14, color=RUB, rot=Ry(-math.pi / 2), bevel=0.012)
    # seat pan and quilted leather cushion with a waterfall front edge
    rb(it, "softplastic", 2.1, 0.08, 1.8, 0, 2.0, -0.06, bevel=0.025, seg=2, color=SOFT)
    rb(it, "leather", 2.36, 0.3, 2.08, 0, 2.11, -0.06, bevel=0.13, seg=3, color=LEATHER)
    for x in (-0.58, 0.0, 0.58):
        rb(it, "softplastic", 0.018, 0.012, 1.75, x, 2.262, -0.06, color="#2a2b2a")                      # quilting seams along the seat
    for z in (-0.55, 0.12, 0.62):
        rb(it, "softplastic", 1.9, 0.012, 0.018, 0, 2.262, z, color="#2a2b2a")
    # backrest: support strut from the mechanism, frame, cushion, lumbar pad, headrest with stems
    tube(it, "metal", [(0.0, 0.34, 1.9), (0.0, 0.62, 2.2), (0.0, 0.88, 2.5), (0.0, 0.98, 2.63)], [0.065, 0.062, 0.06, 0.06], 10, METAL)
    rb(it, "softplastic", 0.16, 1.84, 0.47, -1.06, 3.19, 0.965, bevel=0.06, seg=2, color=SOFT)
    rb(it, "softplastic", 0.16, 1.84, 0.47, 1.06, 3.19, 0.965, bevel=0.06, seg=2, color=SOFT)
    rb(it, "softplastic", 2.28, 0.16, 0.47, 0, 4.03, 0.965, bevel=0.06, seg=2, color=SOFT)
    rb(it, "softplastic", 2.28, 0.16, 0.47, 0, 2.35, 0.965, bevel=0.06, seg=2, color=SOFT)
    rb(it, "leather", 2.0, 1.62, 0.4, 0, 3.19, 0.845, bevel=0.15, seg=3, color=LEATHER)
    for y in (2.9, 3.19, 3.48, 3.77):
        rb(it, "softplastic", 1.7, 0.012, 0.012, 0, y, 0.634, color="#2a2b2a")                     # seams across the backrest
    rb(it, "leather", 1.5, 0.37, 0.15, 0, 2.67, 0.66, bevel=0.07, seg=3, color="#4b4c4a")
    for x in (-0.4, 0.4):
        rb(it, "metal", 0.12, 0.56, 0.06, x, 4.22, 1.175, bevel=0.012, color=METAL)
    rb(it, "leather", 1.32, 0.44, 0.23, 0, 4.51, 1.175, bevel=0.09, seg=3, color=LEATHER)
    # T-arms: cross bar under the seat, posts and soft pads
    rb(it, "metal", 2.54, 0.09, 0.09, 0, 1.93, 0.38, bevel=0.015, color=METAL)
    for x in (-1.27, 1.27):
        rb(it, "metal", 0.1, 0.75, 0.09, x, 2.255, 0.38, bevel=0.015, color=METAL)
        rb(it, "softplastic", 0.22, 0.13, 1.35, x * 1.0, 2.665, -0.035, bevel=0.055, seg=3, color=SOFT)
        rb(it, "metal", 0.14, 0.04, 0.3, x, 2.585, 0.38, bevel=0.01, color=METAL)
    return it


def meetingchair():
    """Meeting-room chair: four tubular legs with rubber pads (the rear pair rises into the back supports), rail frame under the seat,
    upholstered seat on a pan and an upholstered back with seams. Origin = floor under the seat centre (PlacementPivot), front -Y."""
    it = Item("MeetingChair")
    METAL, LEATHER, SOFT, RUB = "#979999", "#434442", "#262729", "#1e1f21"
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 0.85, sz * 0.77
            rb(it, "rubber", 0.14, 0.04, 0.14, x, 0.02, z, bevel=0.012, color=RUB)
            if sz < 0:
                tube(it, "metal", [(-x, z, 0.04), (-x * 0.97, z * 0.96, 0.9), (-x * 0.94, z * 0.94, 1.86)], [0.05, 0.046, 0.046], 12, METAL)
            else:
                tube(it, "metal", [(-x, z, 0.04), (-x * 0.97, z * 0.96, 0.9), (-x * 0.94, z * 0.94, 1.86), (-x * 0.93, 0.74, 2.5), (-x * 0.92, 0.84, 3.28)], [0.05, 0.046, 0.046, 0.045, 0.045], 12, METAL)
    # rails under the seat and a low stretcher between the front legs
    for sz in (-1, 1):
        rb(it, "metal", 1.62, 0.06, 0.06, 0, 1.82, sz * 0.72, bevel=0.012, color=METAL)
    for sx in (-1, 1):
        rb(it, "metal", 0.06, 0.06, 1.44, sx * 0.8, 1.82, 0.0, bevel=0.012, color=METAL)
    rb(it, "metal", 1.6, 0.05, 0.05, 0, 0.6, -0.76, bevel=0.01, color=METAL)
    # seat: pan, cushion, seams
    rb(it, "softplastic", 1.82, 0.05, 1.64, 0, 1.9, -0.025, bevel=0.02, color=SOFT)
    rb(it, "leather", 2.0, 0.24, 1.81, 0, 1.98, -0.025, bevel=0.1, seg=3, color=LEATHER)
    for x in (-0.5, 0.5):
        rb(it, "softplastic", 0.016, 0.012, 1.5, x, 2.1, -0.025, color="#2a2b2a")
    # back: upholstered panel on two supports, seams, rear shell strip
    rb(it, "leather", 1.98, 1.12, 0.33, 0, 2.84, 0.845, bevel=0.12, seg=3, color=LEATHER)
    for y in (2.55, 2.84, 3.13):
        rb(it, "softplastic", 1.7, 0.012, 0.012, 0, y, 0.672, color="#2a2b2a")
    for sx in (-1, 1):
        rb(it, "metal", 0.1, 0.9, 0.05, sx * 0.78, 2.84, 0.99, bevel=0.012, color=METAL)
    return it


def visitorchair():
    """Visitor chair: chrome cantilever frame (floor runners, front risers, seat rails, back posts), upholstered seat and a slatted
    metal back. Origin = floor under the seat centre (PlacementPivot), front -Y."""
    it = Item("VisitorChair")
    CHROME, LEATHER, SOFT, RUB = "#a9aeb0", "#53544f", "#262729", "#1e1f21"
    for sx in (-1, 1):
        x = sx * 1.0
        pts = [(-x, 0.9, 0.05), (-x, -0.78, 0.05), (-x, -0.9, 0.16), (-x, -0.92, 1.55), (-x, -0.82, 1.84), (-x, 0.7, 1.86), (-x, 0.93, 2.35), (-x, 1.0, 3.3)]
        tube(it, "metal", pts, [0.05] * len(pts), 12, CHROME)
        rb(it, "rubber", 0.13, 0.03, 0.3, x, 0.015, 0.84, bevel=0.01, color=RUB)
        rb(it, "rubber", 0.13, 0.03, 0.3, x, 0.015, -0.8, bevel=0.01, color=RUB)
    rb(it, "metal", 2.0, 0.07, 0.07, 0, 1.84, -0.84, bevel=0.012, color=CHROME)
    rb(it, "metal", 2.0, 0.07, 0.07, 0, 1.84, 0.72, bevel=0.012, color=CHROME)
    rb(it, "softplastic", 2.0, 0.05, 1.72, 0, 1.89, -0.025, bevel=0.02, color=SOFT)
    rb(it, "leather", 2.2, 0.24, 1.93, 0, 1.96, -0.025, bevel=0.1, seg=3, color=LEATHER)
    for x in (-0.55, 0.55):
        rb(it, "softplastic", 0.016, 0.012, 1.6, x, 2.082, -0.025, color="#3a3b37")
    # slatted back
    for k in range(6):
        y = 2.45 + k * 0.2
        rb(it, "metal", 2.0, 0.13, 0.1, 0, y, 0.93 + (k * 0.012), bevel=0.04, seg=2, color=CHROME)
    for sx in (-1, 1):
        rb(it, "metal", 0.08, 1.2, 0.09, sx * 0.9, 2.98, 0.98, bevel=0.02, color=CHROME)
    return it


def _monitor_shell(it, W, H):
    """Monitor housing (the game keeps its own LCD part with the screen GUI in front of it): chamfered front plate, tapered back shell,
    vent slots, mounting hub and a badge. Centred on the origin, bbox W x 0.15 x H, front -Y."""
    SHELL, DARK = "#263336", "#1b2220"
    box(it, "softplastic", (W, 0.05, H), (0, -0.05, -H / 2), bevel=0.035, seg=3, color=SHELL)
    box(it, "softplastic", (W - 0.22, 0.095, H - 0.22), (0, 0.025, -(H - 0.22) / 2), bevel=0.055, seg=3, color=SHELL)
    # vent slots on the back face (upper corners) and a hub for the stand
    nvent = 7
    for k in range(nvent):
        for sx in (-1, 1):
            box(it, "dark", (0.16 if W > 1.5 else 0.1, 0.012, 0.02), (sx * (W * 0.3), 0.073, H / 2 - 0.2 - k * 0.04 - 0.0), color=DARK)
    cyl(it, "softplastic", 0.17, 0.02, (0, 0.07, -H * 0.2), seg=24, color="#2f3d40", rot=Rx(-math.pi / 2), bevel=0.006)
    box(it, "metal", (0.26 if W > 1.5 else 0.2, 0.006, 0.05), (0, 0.075, H * 0.12), bevel=0.004, color="#9aa4a6")


def monitorshell():
    it = Item("MonitorShell")
    _monitor_shell(it, 2.5, 1.62)
    return it


def monitorshellp():
    it = Item("MonitorShellP")
    _monitor_shell(it, 1.06, 2.55)
    return it


def monitorfoot():
    """Monitor stand: low rounded base plate, hinge boss, slim tapered neck with a cable slot and a head block. bbox 1.08 x 0.57 x 0.83,
    centred on the origin, the neck sits slightly behind the base centre (+Y = back)."""
    it = Item("MonitorFoot")
    GREY, DARK = "#6f7f76", "#3c4948"
    z0 = -0.415
    box(it, "metal", (1.08, 0.57, 0.04), (0, 0, z0), bevel=0.02, seg=3, color="#3c4948")
    box(it, "metal", (0.9, 0.46, 0.04), (0, 0, z0 + 0.04), bevel=0.02, seg=3, color=DARK)
    cyl(it, "metal", 0.13, 0.05, (0, 0.06, z0 + 0.08), seg=20, color=GREY, bevel=0.012)
    box(it, "metal", (0.15, 0.1, 0.66), (0, 0.06, z0 + 0.1), bevel=0.04, seg=3, color=GREY)
    box(it, "dark", (0.03, 0.012, 0.4), (0, 0.113, z0 + 0.22), color="#222c2b")
    box(it, "metal", (0.24, 0.09, 0.14), (0, 0.04, z0 + 0.69), bevel=0.03, seg=3, color=GREY)
    return it


def keyboard():
    """Keyboard: slim body with a raised front lip and 4 rows of bevelled keys with a space bar. bbox 1.87 x 0.58 x 0.13, centred on the origin."""
    it = Item("Keyboard")
    z0 = -0.065
    box(it, "softplastic", (1.87, 0.58, 0.1), (0, 0, z0), bevel=0.03, seg=3, color="#a6b3a7")
    keyc = "#d4d7c1"
    for row in range(4):
        y = -0.2 + row * 0.135
        if row < 3:
            for k in range(11):
                x = -0.8 + k * 0.16
                box(it, "softplastic", (0.135, 0.115, 0.03), (x, y, z0 + 0.1), bevel=0.012, seg=2, color=keyc)
        else:
            for x in (-0.76, -0.59, 0.55, 0.72):
                box(it, "softplastic", (0.15, 0.115, 0.03), (x, y, z0 + 0.1), bevel=0.012, seg=2, color=keyc)
            box(it, "softplastic", (0.9, 0.115, 0.03), (-0.02, y, z0 + 0.1), bevel=0.012, seg=2, color=keyc)
    return it


def foldingchair():
    """Hub folding chair (mission desk): crossed tubular side frames with a hinge bolt, rubber feet, seat frame with a padded seat,
    two back posts, padded back with stitching and a top rail. Origin = floor under the seat centre; front -Y. The game model pivot
    sits 1.79 above the floor, so the numbers below are pivot-centred Roblox-local (x, y, z) shifted up by 1.79."""
    it = Item("FoldingChair")
    FH = 1.79
    def P(x, y, z):
        return (-x, z, y + FH)
    def rbf(it, mat, w, h, d, x, y, z, **kw):
        rb(it, mat, w, h, d, x, y + FH, z, **kw)
    METAL, FRAME, PAD, STITCH, FOOT, HINGE = "#758994", "#5d7481", "#48504e", "#71776f", "#131b20", "#334450"
    for sx in (-1.23, 1.23):
        tube(it, "metal", [P(sx, -0.6, -1.0), P(sx, -1.14, -0.06), P(sx, -1.72, 0.95)], [0.055, 0.055, 0.055], 10, METAL)
        tube(it, "metal", [P(sx, -0.6, 0.85), P(sx, -1.14, -0.06), P(sx, -1.72, -1.05)], [0.055, 0.055, 0.055], 10, METAL)
        for z in (0.95, -1.05):
            cyl(it, "rubber", 0.1, 0.12, P(sx, -1.79, z), seg=14, color=FOOT, bevel=0.02)
        # hinge bolt through the crossing
        cyl(it, "metal", 0.07, 0.16, (-sx - 0.08, -0.06, -1.14 + FH), seg=12, color="#979999", rot=Ry(math.pi / 2), bevel=0.01)
        tube(it, "metal", [P(sx * 0.93, -0.5, 0.88), P(sx * 0.93, 0.6, 1.0), P(sx * 0.94, 1.74, 1.12)], [0.05, 0.05, 0.05], 10, METAL)
    rbf(it, "metal", 2.46, 0.09, 0.09, 0, -1.37, 0.34, bevel=0.015, color=FRAME)
    # seat frame, padded seat, stitching
    rbf(it, "metal", 2.5, 0.12, 2.2, 0, -0.605 + 0.0, -0.07, bevel=0.03, seg=2, color=FRAME)
    rbf(it, "softplastic", 2.22, 0.22, 2.04, 0, -0.44, -0.07, bevel=0.08, seg=3, color=PAD)
    for x in (-0.9, 0.9):
        rbf(it, "softplastic", 0.016, 0.012, 1.7, x, -0.325, -0.07, color=STITCH)
    for z in (-0.9, 0.78):
        rbf(it, "softplastic", 1.8, 0.012, 0.016, 0, -0.325, z, color=STITCH)
    # back: padded panel, stitching, top rail
    rbf(it, "softplastic", 2.2, 1.66, 0.5, 0, 0.84, 0.95, bevel=0.12, seg=3, color=PAD)
    for y in (1.44, 0.3):
        rbf(it, "softplastic", 1.9, 0.016, 0.012, 0, y, 0.7, color=STITCH)
    for x in (-0.95, 0.95):
        rbf(it, "softplastic", 0.016, 1.1, 0.012, x, 0.87, 0.7, color=STITCH)
    rbf(it, "metal", 2.32, 0.13, 0.13, 0, 1.725, 1.125, bevel=0.03, color=METAL)
    return it


def toilet():
    """Floor toilet of the washrooms (4716 game parts): foot plate, tapered pedestal, oval bowl with a rim and still water, hinged seat ring,
    raised lid resting against a rounded cistern with a dual-flush button, supply pipe and valve. Origin = floor under the pedestal
    (PlacementPivot), front -Y (Roblox -Z); cistern at the back (Roblox +Z)."""
    it = Item("Toilet")
    CER, CER2, METAL, DARK = "#edefe1", "#f7f5e9", "#a6b5b5", "#2b3032"
    rb(it, "paint", 1.12, 0.16, 1.54, 0, 0.08, 0.11, bevel=0.06, seg=3, color=CER)                    # foot plate
    rb(it, "paint", 0.92, 0.9, 1.29, 0, 0.57, 0.175, bevel=0.14, seg=3, color=CER)                    # pedestal
    # bowl: revolved profile (outside up over the rim and down inside), stretched to an oval, centre z = -0.27
    prof = [(0.0, 0.96), (0.4, 0.97), (0.78, 1.25), (0.94, 1.75), (0.97, 2.1), (0.9, 2.2), (0.8, 2.12), (0.74, 1.8), (0.58, 1.3), (0.35, 1.12), (0.0, 1.1)]
    lathe(it, "paint", prof, (0.0, -0.27, 0.0), seg=40, color=CER, scale=(1.0, 1.28, 1.0))
    ball(it, "glass_blue", 0.5, (0.0, -0.27, 1.12), scale=(0.62, 0.85, 0.02), seg=18, color="#6a9ea4")  # still water
    # rim and seat ring (ovals)
    torus(it, "paint", 0.88, 0.07, (0.0, -0.27, 2.2), scale=(1.07, 1.3, 1.0), color=CER, seg=40, minor=10)
    torus(it, "paint", 0.78, 0.085, (0.0, -0.27, 2.33), scale=(1.15, 1.34, 1.0), color=CER2, seg=40, minor=10)
    rb(it, "rubber", 0.36, 0.06, 0.12, -0.45, 2.255, 0.77, bevel=0.01, color="#2b3032")
    rb(it, "rubber", 0.36, 0.06, 0.12, 0.45, 2.255, 0.77, bevel=0.01, color="#2b3032")
    rb(it, "metal", 0.22, 0.14, 0.12, -0.5, 2.33, 0.86, bevel=0.02, color=METAL)                       # seat hinges
    rb(it, "metal", 0.22, 0.14, 0.12, 0.5, 2.33, 0.86, bevel=0.02, color=METAL)
    # raised lid leaning on the cistern, with an inset panel
    rb(it, "paint", 1.92, 2.34, 0.13, 0, 3.5, 0.84, bevel=0.07, seg=3, color=CER2, rot=Rx(0.05))
    rb(it, "paint", 1.62, 2.0, 0.04, 0, 3.5, 0.765, bevel=0.03, color=CER)
    # cistern with lid and the dual-flush button
    rb(it, "paint", 1.84, 1.36, 0.72, 0, 2.81, 1.35, bevel=0.13, seg=3, color=CER)
    rb(it, "paint", 1.9, 0.12, 0.78, 0, 3.56, 1.35, bevel=0.05, seg=2, color=CER2)
    for x in (-0.08, 0.08):
        cyl(it, "metal", 0.07, 0.03, (-x, 1.32, 3.62), seg=16, color=METAL, bevel=0.008)
    # supply pipe and valve on the right side (Roblox +x = Blender -x)
    cyl(it, "metal", 0.06, 1.55, (-0.95, 1.53, 0.73), seg=14, color=METAL)
    rb(it, "metal", 0.2, 0.2, 0.18, 1.02, 0.72, 1.54, bevel=0.03, color=METAL)
    cyl(it, "plastic_gray", 0.05, 0.2, (-1.06, 1.54, 0.8), seg=12, color="#407478", rot=Ry(-math.pi / 2), bevel=0.01)
    return it


def wallsockets():
    """Double wall socket plate (3210 game parts): plate with a rounded recess, two round sockets with pin holes, screws and an earth contact.
    Origin = bottom centre of the plate at the wall, front -Y; plate 1.48 x 0.37."""
    it = Item("WallSockets")
    PL, DK = "#f7f5e9", "#19212a"
    rb(it, "paint", 1.48, 0.37, 0.09, 0, 0.185, -0.005, bevel=0.035, seg=3, color=PL)
    rb(it, "dark", 1.3, 0.19, 0.03, 0, 0.185, -0.05, bevel=0.03, seg=2, color=DK)
    for x in (-0.33, 0.33):
        cyl(it, "paint", 0.085, 0.03, (-x, -0.07, 0.185 - 0.0), seg=20, color=PL, rot=Rx(math.pi / 2), bevel=0.01)
        for dx in (-0.032, 0.032):
            cyl(it, "metal", 0.012, 0.012, (-(x + dx), -0.1, 0.185), seg=8, color="#a9b2b2", rot=Rx(math.pi / 2))
    for x in (-0.57, 0.57):
        cyl(it, "metal", 0.03, 0.012, (-x, -0.052, 0.185), seg=10, color="#a9b2b2", rot=Rx(math.pi / 2))
    rb(it, "metal", 0.1, 0.03, 0.012, 0, 0.185 - 0.075, -0.052, bevel=0.004, color="#a9b2b2")
    return it


def _cabinetbody(name, half, per, pitch, x0):
    """Archive cabinet body (the doors are separate meshes on the game's hinge parts): plinth with levelling feet, rounded side panels, top cap
    with an overhang, back panel, four shelves with front lips and 60 binders (spines with label plates and finger holes, a few leaning).
    Origin = floor centre (PlacementPivot), front -Y (Roblox -Z: the doors are at Roblox z < 0). Game body: x +-1.956, y 0.1..7.93, z -1..+1."""
    it = Item(name)
    BODY, SHELF, METAL, DARK = "#27323b", "#cdd7c9", "#a5b5b4", "#161b1e"
    rnd = random.Random(20261114)
    for sx in (-half, half):
        rb(it, "paint", 0.0875, 7.675, 2.0, sx, 4.0375, 0, bevel=0.018, seg=2, color=BODY)                 # side panels
    rb(it, "paint", 2 * half - 0.087, 0.0875, 2.0, 0, 0.25, 0, bevel=0.012, color=BODY)                                # bottom
    rb(it, "paint", 2 * half - 0.087, 0.0875, 2.0, 0, 7.83, 0, bevel=0.012, color=BODY)                                # inner top
    rb(it, "paint", 2 * half + 0.21, 0.1, 2.16, 0, 7.93, 0.0, bevel=0.03, seg=3, color="#34434c")                      # top cap with overhang
    rb(it, "paint", 2 * half - 0.087, 7.38, 0.05, 0, 3.984, 0.975, color=BODY)                                         # back (Roblox +z = back)
    rb(it, "paint", 2 * half - 0.01, 0.22, 1.9, 0, 0.11, 0.0, bevel=0.02, color=DARK)                                   # plinth
    for fx in (-(half - 0.256), half - 0.256):
        for fz in (-0.78, 0.78):
            rpost(it, "metal", 0.07, 0.0, 0.13, fx, fz, seg=12, color=METAL)                                # levelling feet
    for y in (1.7656, 3.2656, 4.7656, 6.2656):
        rb(it, "paint", 2 * half - 0.137, 0.0563, 1.85, 0, y, 0.025, bevel=0.01, color=SHELF)                          # shelves
        rb(it, "paint", 2 * half - 0.137, 0.1, 0.03, 0, y + 0.04, -0.885, bevel=0.008, color=SHELF)                    # front lip
    colors = ["#785e46", "#39493d", "#2e3e5c", "#6e2d32", "#6e7276", "#785e46", "#39493d"]
    shelves = (0.25 + 0.0437, 1.7656 + 0.028, 3.2656 + 0.028, 4.7656 + 0.028)                                # binders stand on bottom, shelf 1-3 (60 = 4 x 15)
    for base in shelves:
        x = x0
        for i in range(per):
            h = rnd.uniform(1.12, 1.3)
            c = colors[rnd.randrange(len(colors))]
            lean = 0.0
            if i in (4, 11) and rnd.random() < 0.6:
                lean = rnd.uniform(0.05, 0.11)
            rb(it, "paint", 0.205, h, 1.55, x, base + h / 2, 0.12, bevel=0.012, seg=2, color=c, rot=Ry(lean) if lean else None)
            rb(it, "paint", 0.12, 0.45, 0.012, x, base + h * 0.62, -0.66, color="#e4e0cc")                   # label plate on the spine
            rb(it, "rubber", 0.07, 0.03, 0.012, x, base + h * 0.9, -0.66, color="#101214")                   # finger hole
            x += pitch
    return it




def archivecabinet():
    return _cabinetbody("ArchiveCabinet", 1.956, 15, 0.2335, -1.74)


def glazedcabinet():
    """Glazed cabinet body (4 shelves of binders; narrower than the archive cabinet): the game keeps the glass panes and hinge parts."""
    return _cabinetbody("GlazedCabinet", 1.706, 14, 0.2235, -1.45)


def _glazeddoor(name, mirror):
    """Glazed cabinet door frame in the local frame of the game's MotionPivot hinge: stiles and rails round the game's glass pane
    (x -1.678..0.015; mirrored: 0..1.678), inner beads, vertical pull bar on the free stile, lock, three hinge barrels."""
    it = Item(name)
    TEAL, METAL, BEAD = "#407477", "#a5b5b4", "#2f5a5d"
    s = -1.0 if mirror else 1.0
    X = lambda x: s * x
    for x in (-1.622, -0.041):
        rb(it, "metal", 0.112, 7.5, 0.069, X(x), 0.0, 0.119, bevel=0.014, seg=2, color=TEAL)                  # stiles
    for y in (-3.694, 3.694):
        rb(it, "metal", 1.469, 0.112, 0.069, X(-0.831), y, 0.119, bevel=0.014, seg=2, color=TEAL)             # rails
    for y in (-3.62, 3.62):
        rb(it, "metal", 1.5, 0.03, 0.03, X(-0.831), y, 0.088, color=BEAD)                                      # inner beads (front)
    for x in (-1.552, -0.111):
        rb(it, "metal", 0.03, 7.24, 0.03, X(x), 0.0, 0.088, color=BEAD)
    # slim muntin bars across the glass (the pane itself stays a game part)
    for y in (-1.2, 1.2):
        rb(it, "metal", 1.47, 0.04, 0.03, X(-0.831), y, 0.119, color=BEAD)
    hx = -1.545
    for y in (-0.6, 0.05):
        rb(it, "metal", 0.05, 0.05, 0.07, X(hx), y, 0.045, bevel=0.01, color=METAL)
    rb(it, "metal", 0.045, 0.78, 0.045, X(hx), -0.275, -0.006, bevel=0.015, seg=3, color=METAL)
    rb(it, "metal", 0.11, 0.11, 0.02, X(-1.622), 0.55, 0.078, bevel=0.03, seg=3, color="#8a9a99")
    rb(it, "rubber", 0.025, 0.06, 0.02, X(-1.622), 0.55, 0.07, color="#101a1c")
    for y in (-3.213, -0.213, 3.1):
        rpost(it, "metal", 0.05, y - 0.17, y + 0.17, X(0.0), 0.069, seg=14, color=METAL, bevel=0.005)
        rb(it, "metal", 0.1, 0.19, 0.04, X(-0.05), y, 0.101, bevel=0.01, color=METAL)
    return it


def glazeddoor():
    return _glazeddoor("GlazedDoor", False)


def glazeddoorm():
    return _glazeddoor("GlazedDoorM", True)


def shelfrack():
    """Open archive rack (MetalShelf / LoadedShelf frame): four slotted uprights with feet, six shelf decks with front/back lips,
    X braces at the back. Origin = floor centre (PlacementPivot), front -Y (Roblox -Z). Game: x +-2.425, z +-0.925, decks every 1.5 from y 0.416."""
    it = Item("ShelfRack")
    DARK, DECK, METAL = "#27323b", "#cdd7c9", "#a5b5b4"
    for ux in (-2.425, 2.425):
        for uz in (-0.925, 0.925):
            rb(it, "paint", 0.112, 7.9, 0.112, ux, 4.05, uz, bevel=0.01, color=DARK)
            rb(it, "paint", 0.25, 0.1, 0.25, ux, 0.05, uz, bevel=0.02, color=DARK)                             # foot plate
            for k in range(22):                                                                              # slots on the inner faces
                rb(it, "rubber", 0.02, 0.08, 0.06, ux + (0.057 if ux < 0 else -0.057), 0.6 + k * 0.33, uz, color="#101417")
    for i in range(6):
        y = 0.416 + 1.5 * i
        rb(it, "paint", 4.775, 0.069, 1.7, 0, y, 0, bevel=0.012, color=DECK)                                # deck
        rb(it, "paint", 4.775, 0.119, 0.05, 0, y - 0.025, -0.875, bevel=0.01, color=DARK)                   # lips
        rb(it, "paint", 4.775, 0.119, 0.05, 0, y - 0.025, 0.875, bevel=0.01, color=DARK)
    ang = math.atan2(7.5, 4.85)
    L = math.hypot(4.85, 7.5)
    for sgn in (1, -1):
        rb(it, "metal", L, 0.05, 0.05, 0, 4.05, 0.95, color=METAL, rot=Ry(sgn * ang))                       # X braces at the back
    return it


def shelfload():
    """Contents of the loaded archive rack: three archive boxes on decks 0, 2 and 4, 18 binders on decks 1 and 3. Same origin as ShelfRack."""
    it = Item("ShelfLoad")
    rnd = random.Random(7)
    CARD, LID, GRIP = "#a98f69", "#b09872", "#4d3f2c"
    for i in (0, 2, 4):
        top = 0.416 + 1.5 * i + 0.0345
        for bx in (-1.5, 0.0, 1.5):
            rb(it, "paper", 1.37, 1.0, 1.55, bx, top + 0.52, 0.0, bevel=0.02, seg=2, color=CARD)               # box body
            rb(it, "paper", 1.44, 0.06, 1.62, bx, top + 1.06, 0.0, bevel=0.02, seg=2, color=LID)               # lid with overhang
            for sx in (-0.69, 0.69):
                rb(it, "rubber", 0.012, 0.12, 0.5, bx + sx, top + 0.78, 0.0, color=GRIP)                        # side grips
    covers = ["#404c5f", "#3e444a", "#39493d", "#3e444a", "#404c5f"]
    for i in (1, 3):
        top = 0.416 + 1.5 * i + 0.0345
        x = -2.062
        for n in range(18):
            h = 1.1 + rnd.uniform(-0.04, 0.05)
            c = covers[rnd.randrange(len(covers))]
            rb(it, "paper", 0.2, h, 1.23, x, top + h / 2, 0.041, bevel=0.012, seg=2, color=c)                    # binder
            rb(it, "paper", 0.12, 0.5, 0.012, x, top + h * 0.6, -0.575, color="#e4e0cc")                       # spine label
            rb(it, "rubber", 0.07, 0.03, 0.012, x, top + h * 0.9, -0.575, color="#101214")                     # finger hole
            x += 0.243
    return it


def _archivedoor(name, mirror):
    """Archive cabinet door panel in the local frame of the game's MotionPivot hinge: panel at x -1.944..0 (mirrored: 0..+1.944), front -Z.
    Raised border, vent slots top and bottom, pull handle on the free edge, lock, three hinge barrels. The game keeps its label holder and prompt."""
    it = Item(name)
    TEAL, METAL, DARK = "#407477", "#a5b5b4", "#101a1c"
    s = -1.0 if mirror else 1.0
    X = lambda x: s * x
    cx = -0.972
    rb(it, "paint", 1.92, 7.45, 0.069, X(cx), 0.0, 0.119, bevel=0.012, seg=2, color=TEAL)                    # panel
    for y in (-3.7, 3.7):
        rb(it, "paint", 1.92, 0.1, 0.014, X(cx), y, 0.0775, bevel=0.004, color="#365f62")                    # top/bottom border
    for x in (-0.06, -1.884):
        rb(it, "paint", 0.1, 7.3, 0.014, X(x), 0.0, 0.0775, bevel=0.004, color="#365f62")                    # side borders
    for k in range(7):                                                                                        # vent slots
        for y0 in (3.05, -3.4):
            rb(it, "rubber", 1.1, 0.03, 0.012, X(cx), y0 + k * 0.07, 0.081, color=DARK)
    hx = -1.78
    for y in (-0.5, -0.05):
        rb(it, "metal", 0.05, 0.05, 0.07, X(hx), y, 0.045, bevel=0.01, color=METAL)                        # handle posts
    rb(it, "metal", 0.045, 0.62, 0.045, X(hx), -0.275, -0.006, bevel=0.015, seg=3, color=METAL)               # pull bar
    rb(it, "metal", 0.11, 0.11, 0.02, X(hx), 0.4, 0.078, bevel=0.03, seg=3, color="#8a9a99")                 # lock plate
    rb(it, "rubber", 0.025, 0.06, 0.02, X(hx), 0.4, 0.07, color=DARK)                                         # keyhole
    for y in (-3.213, -0.213, 3.1):
        rpost(it, "metal", 0.05, y - 0.17, y + 0.17, X(0.0), 0.069, seg=14, color=METAL, bevel=0.005)       # hinge barrels
        rb(it, "metal", 0.1, 0.19, 0.04, X(-0.05), y, 0.101, bevel=0.01, color=METAL)                       # hinge leaves
    return it


def archivedoor():
    return _archivedoor("ArchiveDoor", False)


def archivedoorm():
    return _archivedoor("ArchiveDoorM", True)



def lowcabinet():
    """Low two-door cabinet (WEST): plinth with feet, side panels, top cap with overhang, shelf, back. Game: x +-2.08, y 0.175..3.1, z +-0.906.
    Origin = floor centre (PlacementPivot), front -Y (Roblox -Z). Doors are separate meshes (LowDoor / LowDoorM)."""
    it = Item("LowCabinet")
    BODY, CAP, SHELF = "#27323b", "#2f3f48", "#b6c9bf"
    for sx in (-2.081, 2.081):
        rb(it, "paint", 0.087, 2.925, 1.81, sx, 1.6375, 0, bevel=0.012, color=BODY)
    rb(it, "paint", 4.4, 0.1, 2.0, 0, 3.05, 0, bevel=0.025, seg=3, color=CAP)                              # top cap with overhang
    rb(it, "paint", 4.074, 0.087, 1.81, 0, 0.22, 0, bevel=0.01, color=BODY)                                 # bottom
    rb(it, "paint", 4.04, 0.056, 1.66, 0, 1.6, 0.025, bevel=0.008, color=SHELF)                             # shelf
    rb(it, "paint", 4.07, 2.75, 0.05, 0, 1.637, 0.88, color=BODY)                                          # back
    rb(it, "paint", 3.9, 0.17, 1.6, 0, 0.09, 0, bevel=0.01, color="#161b1e")                                # plinth
    for fx in (-1.92, 1.92):
        for fz in (-0.74, 0.74):
            rpost(it, "metal", 0.075, 0.0, 0.12, fx, fz, seg=12, color="#a5b5b5")
    return it


def _lowdoor(name, mirror):
    """Low cabinet door in the local frame of its MotionPivot hinge: panel x 0..1.98 (mirrored: -1.98..0), back at +z 0.11, front -z.
    Raised border, vertical pull on the free edge, two hinge barrels."""
    it = Item(name)
    TEAL, RIM, METAL = "#407477", "#366064", "#a5b5b5"
    s = -1.0 if mirror else 1.0
    X = lambda x: s * x
    rb(it, "paint", 1.98, 2.75, 0.07, X(1.0), 0.0, 0.11, bevel=0.014, seg=2, color=TEAL)
    for y in (-1.3, 1.3):
        rb(it, "paint", 1.8, 0.08, 0.012, X(1.0), y, 0.068, bevel=0.004, color=RIM)
    for x in (0.12, 1.88):
        rb(it, "paint", 0.08, 2.6, 0.012, X(x), 0.0, 0.068, bevel=0.004, color=RIM)
    for y in (-0.25, 0.25):
        rb(it, "metal", 0.05, 0.05, 0.07, X(1.83), y, 0.04, bevel=0.01, color=METAL)
    rb(it, "metal", 0.045, 0.62, 0.045, X(1.83), 0.0, -0.005, bevel=0.015, seg=3, color=METAL)
    for y in (-1.07, 1.05):
        rpost(it, "metal", 0.05, y - 0.15, y + 0.15, X(0.0), 0.06, seg=12, color=METAL)
        rb(it, "metal", 0.1, 0.17, 0.04, X(0.05), y, 0.085, bevel=0.01, color=METAL)
    return it


def lowdoor():
    return _lowdoor("LowDoor", False)


def lowdoorm():
    return _lowdoor("LowDoorM", True)


def filecabinet():
    """Four-drawer file cabinet body (drawers are separate meshes): plinth, side panels, top cap, back, drawer rails, feet.
    Game: x +-0.99, y 0.19..6.125, z +-1.156; drawer pivots at y 1.0 + 1.5 k. Origin = floor centre, front -Y (Roblox -Z)."""
    it = Item("FileCabinet")
    BODY, CAP, RAIL = "#27323b", "#2f3f48", "#a5b5b4"
    for sx in (-0.988, 0.988):
        rb(it, "paint", 0.087, 5.937, 2.31, sx, 3.156, 0, bevel=0.012, color=BODY)
    rb(it, "paint", 2.2, 0.1, 2.45, 0, 6.17, 0, bevel=0.025, seg=3, color=CAP)
    rb(it, "paint", 1.9, 0.087, 2.31, 0, 0.23, 0, bevel=0.01, color=BODY)
    rb(it, "paint", 1.9, 5.76, 0.05, 0, 3.16, 1.13, color=BODY)
    rb(it, "paint", 1.85, 0.2, 2.2, 0, 0.1, 0, bevel=0.01, color="#161b1e")
    for k in range(4):
        y = 1.0 + 1.5 * k - 0.57
        for sx in (-0.93, 0.93):
            rb(it, "metal", 0.05, 0.06, 2.0, sx, y, 0, bevel=0.01, color=RAIL)
    for fx in (-0.88, 0.88):
        for fz in (-1.0, 1.0):
            rpost(it, "metal", 0.075, 0.0, 0.13, fx, fz, seg=12, color=RAIL)
    return it


def filedrawer():
    """One file-cabinet drawer in the local frame of its MotionPivot (centre of the drawer): front panel with raised border, pull handle,
    box with folders. The game keeps its label plate and prompt. Front -z."""
    it = Item("FileDrawer")
    TEAL, RIM, METAL, BOX = "#407477", "#366064", "#a5b5b4", "#b7c9c0"
    rb(it, "paint", 1.8, 1.3, 0.075, 0, 0.0, -1.22, bevel=0.014, seg=2, color=TEAL)                         # front
    rb(it, "paint", 1.72, 0.04, 0.012, 0, 0.6, -1.263, bevel=0.004, color=RIM)
    rb(it, "paint", 1.72, 0.04, 0.012, 0, -0.6, -1.263, bevel=0.004, color=RIM)
    rb(it, "paint", 0.04, 1.2, 0.012, -0.84, 0.0, -1.263, bevel=0.004, color=RIM)
    rb(it, "paint", 0.04, 1.2, 0.012, 0.84, 0.0, -1.263, bevel=0.004, color=RIM)
    for sx in (-0.2, 0.2):
        rb(it, "metal", 0.05, 0.05, 0.07, sx, 0.125, -1.3, bevel=0.01, color=METAL)                          # handle posts
    rb(it, "metal", 0.62, 0.05, 0.05, 0.0, 0.125, -1.34, bevel=0.018, seg=3, color=METAL)                  # pull
    rb(it, "metal", 1.72, 0.044, 2.15, 0, -0.619, 0, bevel=0.01, color=BOX)                                  # box bottom
    for sx in (-0.877, 0.877):
        rb(it, "metal", 0.04, 1.2, 2.15, sx, 0.0, 0.0, bevel=0.008, color=BOX)
    rb(it, "metal", 1.72, 1.2, 0.04, 0, 0.0, 1.062, bevel=0.008, color=BOX)
    cols = ["#b7c9c0", "#e4e3d0", "#52778c"]
    for i, z in enumerate((-0.85, -0.5, -0.15, 0.2, 0.55, 0.9)):
        rb(it, "paper", 1.55, 0.74, 0.03, 0, -0.22, z, bevel=0.006, color=cols[i % 3])
        rb(it, "paper", 0.9, 0.1, 0.03, (i - 2.5) * 0.14, 0.2, z, color="#ede9da")
    return it


def sortingcabinet():
    """Sorting cabinet (NW): 3 x 4 pigeonholes with paper stacks. Game: x +-1.875, y 0.19..5.75, z +-0.94; shelves every 1.375,
    dividers at x +-0.64. The game keeps its 12 label plates (front, z -0.96). Origin = floor centre, front -Y."""
    it = Item("SortingCabinet")
    BODY, SHELF = "#27323b", "#b7c9c0"
    rnd = random.Random(11)
    for sx in (-1.8375, 1.8375):
        rb(it, "paint", 0.075, 5.56, 1.875, sx, 2.97, 0, bevel=0.01, color=BODY)
    rb(it, "paint", 3.6, 5.56, 0.05, 0, 2.97, 0.91, color=BODY)
    ys = [0.225 + 1.375 * k for k in range(5)]
    for y in ys:
        rb(it, "paint", 3.6, 0.05, 1.825, 0, y, 0.0, bevel=0.008, color=SHELF)
    for k in range(4):
        for dx in (-0.638, 0.638):
            rb(it, "paint", 0.04, 1.32, 1.8, dx, ys[k] + 0.69, 0.0, bevel=0.005, color=SHELF)
    for sx in (-1.7, 1.7):
        for sz in (-0.78, 0.78):
            rpost(it, "metal", 0.07, 0.0, 0.16, sx, sz, seg=12, color="#a5b5b4")
    for k in range(4):
        for cx in (-1.25, 0.0, 1.25):
            n = rnd.choice((2, 3, 3))
            for j in range(n):
                w = rnd.uniform(0.82, 1.0)
                rb(it, "paper", w, 0.09, 1.25, cx + rnd.uniform(-0.1, 0.1), ys[k] + 0.07 + 0.1 * j, 0.1, bevel=0.01,
                   color="#ede9da", rot=Rz(rnd.uniform(-0.1, 0.1)))
    return it


def cornershelf():
    """Corner rack (NW): L-shaped decks on four posts, five levels. Game: back deck x -1.45..1.4, z 0.1..1.4, return deck x 0.1..1.4,
    z -1.4..0.1, decks every 1.514 from y 0.305. Origin = floor corner point (PlacementPivot), front -Y (Roblox -Z)."""
    it = Item("CornerShelf")
    DARK, DECK = "#27323b", "#cdd7c9"
    for px, pz in ((-1.45, 1.4), (1.4, 1.4), (1.4, -1.4), (0.1, 0.1)):
        rb(it, "paint", 0.1, 6.35, 0.1, px, 3.25, pz, bevel=0.01, color=DARK)
        rb(it, "paint", 0.22, 0.08, 0.22, px, 0.04, pz, bevel=0.01, color=DARK)
    for k in range(5):
        y = 0.305 + 1.514 * k
        rb(it, "paint", 2.85, 0.06, 1.3, -0.025, y, 0.75, bevel=0.01, color=DECK)
        rb(it, "paint", 1.3, 0.06, 1.5, 0.75, y, -0.65, bevel=0.01, color=DECK)
        rb(it, "paint", 2.85, 0.14, 0.035, -0.025, y - 0.03, 1.4, color=DARK)
        rb(it, "paint", 0.035, 0.14, 1.5, 1.4, y - 0.03, -0.65, color=DARK)
        rb(it, "paint", 1.45, 0.14, 0.035, -0.725, y - 0.03, 0.1, color=DARK)
        rb(it, "paint", 0.035, 0.14, 1.5, 0.1, y - 0.03, -0.65, color=DARK)
    return it


def formscabinet():
    """Forms cabinet (CENTER): open two-bay cabinet with a wide top and teal paper trays holding sheet stacks. Game: sides x +-1.73,
    y 0.24..2.68, z +-0.7, top 4.86 wide, trays on top. The game keeps its two label plates (ShelfLegend, InspectionExample) and collision.
    Origin = floor centre, front -Y."""
    it = Item("FormsCabinet")
    BODY, TOP, TEAL = "#27323b", "#e2e4d8", "#407477"
    rnd = random.Random(5)
    for sx in (-1.7, 0.0, 1.7):
        rb(it, "paint", 0.06, 2.44, 1.4, sx, 1.46, 0, bevel=0.008, color=BODY)
    rb(it, "paint", 3.42, 2.44, 0.05, 0, 1.46, 0.675, color=BODY)
    rb(it, "paint", 4.86, 0.1, 1.5, 0, 2.7, 0, bevel=0.03, seg=3, color=TOP)                                # wide top
    rb(it, "paint", 3.4, 0.06, 1.38, 0, 1.2, 0.0, bevel=0.008, color="#e2e4d8")                              # shelf
    rb(it, "paint", 3.4, 0.06, 1.38, 0, 0.27, 0.0, bevel=0.008, color="#e2e4d8")
    rb(it, "paint", 3.2, 0.16, 1.2, 0, 0.16, 0, bevel=0.01, color="#161b1e")                                 # plinth
    for fx in (-1.5, 1.5):
        for fz in (-0.6, 0.6):
            rpost(it, "metal", 0.07, 0.0, 0.12, fx, fz, seg=12, color="#a5b5b4")
    for bx in (-0.85, 0.85):
        for j in range(5):
            rb(it, "paper", 1.4, 0.03, 0.8, bx, 0.31 + 0.03 * j, 0.0 + rnd.uniform(-0.03, 0.03), color="#ede9da", rot=Rz(rnd.uniform(-0.03, 0.03)))
        for j in range(4):
            rb(it, "paper", 1.4, 0.03, 0.8, bx, 1.24 + 0.03 * j, 0.0 + rnd.uniform(-0.03, 0.03), color="#ede9da", rot=Rz(rnd.uniform(-0.03, 0.03)))
    for tx in (-1.05, 1.05):                                                                                  # trays on top
        rb(it, "paint", 1.6, 0.06, 1.12, tx, 2.78, 0, bevel=0.01, color=TEAL)
        rb(it, "paint", 1.6, 0.18, 0.05, tx, 2.84, -0.56, bevel=0.008, color=TEAL)
        rb(it, "paint", 1.6, 0.18, 0.05, tx, 2.84, 0.56, bevel=0.008, color=TEAL)
        rb(it, "paint", 0.05, 0.18, 1.12, tx - 0.8, 2.84, 0, bevel=0.008, color=TEAL)
        rb(it, "paint", 0.05, 0.18, 1.12, tx + 0.8, 2.84, 0, bevel=0.008, color=TEAL)
        for j in range(3):
            rb(it, "paper", 1.4, 0.012, 0.88, tx, 2.797 + 0.012 * j, 0.0, color="#ede9da")                 # sheet stack (top 2.833 < label plate 2.838)
    return it


def _kitchenbody(name, hx, hz, dividers, drawer_xs, drawer_w, counter_hx, counter_hz):
    """Kitchen base cabinet body (doors are separate meshes, KitchenDoorController keeps moving them): recessed plinth, side panels,
    floor, back, interior shelf, drawer fronts with bar handles under the countertop. Game: sides at +-hx, body y 0.25..3.04, z +-hz,
    countertop y 3.11..3.28. Origin = floor centre (PlacementPivot), front -Y (Roblox -Z)."""
    it = Item(name)
    BODY, TOP, DRW, HND = "#27323b", "#e2e3d8", "#27323b", "#adb7b5"
    for sx in (-hx, hx):
        rb(it, "paint", 0.1, 2.79, 2 * hz, sx, 1.645, 0, bevel=0.012, color=BODY)
    rb(it, "paint", 2 * hx - 0.1, 0.09, 2 * hz, 0, 0.295, 0, bevel=0.01, color=BODY)
    rb(it, "paint", 2 * hx - 0.1, 2.7, 0.05, 0, 1.69, hz - 0.025, color=BODY)
    rb(it, "paint", 2 * hx - 0.1, 0.06, 2 * hz - 0.2, 0, 1.45, 0.02, bevel=0.008, color="#e0e6dc")
    for dx in dividers:
        rb(it, "paint", 0.06, 2.74, 2 * hz - 0.1, dx, 1.67, 0.0, color=BODY)
    rb(it, "paint", 2 * hx - 0.3, 0.23, 2.0, 0, 0.115, 0.05, bevel=0.01, color="#161b1e")                       # recessed plinth
    rb(it, "paint", 2 * counter_hx, 0.17, 2 * counter_hz, 0, 3.195, 0, bevel=0.03, seg=3, color=TOP)            # countertop
    for dx in drawer_xs:
        rb(it, "paint", drawer_w, 0.4, 0.09, dx, 2.82, -hz - 0.035, bevel=0.012, seg=2, color=DRW)               # drawer front
        rb(it, "paint", drawer_w - 0.2, 0.02, 0.012, dx, 2.82, -hz - 0.085, bevel=0.003, color="#1b252b")
        rb(it, "metal", 0.55, 0.05, 0.05, dx, 2.82, -hz - 0.15, bevel=0.015, seg=3, color=HND)                  # bar handle
        for hx2 in (-0.2, 0.2):
            rb(it, "metal", 0.05, 0.05, 0.08, dx + hx2, 2.82, -hz - 0.11, bevel=0.01, color=HND)
    for xx in [(drawer_xs[i] + drawer_xs[i + 1]) / 2 for i in range(len(drawer_xs) - 1)]:
        rb(it, "rubber", 0.03, 0.4, 0.02, xx, 2.82, -hz - 0.08, color="#161d21")
    return it


def kitchenbody():
    return _kitchenbody("KitchenBody", 2.63, 1.12, (-0.9, 0.9), (-1.82, 0.0, 1.82), 1.74, 2.65, 1.18)


def sidebody():
    return _kitchenbody("SideBody", 1.5, 1.03, (0.0,), (-0.75, 0.75), 1.46, 1.54, 1.08)


def coffeebody():
    return _kitchenbody("CoffeeBody", 1.09, 1.03, (), (0.0,), 2.1, 1.12, 1.08)


def _kitchendoor(name, width, height, handle_y, mirror):
    """Kitchen door in the local frame of its HingePivot (hinge edge at x 0, door to +x; mirrored: to -x), centred vertically, front -z.
    Flat panel with a raised inset, vertical pull on the free edge, two concealed hinges."""
    it = Item(name)
    TEAL, INSET, METAL = "#407477", "#38686b", "#adb7b5"
    s = -1.0 if mirror else 1.0
    X = lambda x: s * x
    rb(it, "paint", width - 0.01, height, 0.08, X(width / 2 + 0.005), 0.0, 0.0, bevel=0.012, seg=2, color=TEAL)
    rb(it, "paint", width - 0.3, height - 0.3, 0.02, X(width / 2 + 0.005), 0.0, -0.05, bevel=0.006, color=INSET)
    rb(it, "metal", 0.045, 0.42, 0.045, X(width - 0.2), handle_y, -0.15, bevel=0.015, seg=3, color=METAL)
    for dy in (-0.18, 0.18):
        rb(it, "metal", 0.05, 0.05, 0.09, X(width - 0.2), handle_y + dy, -0.1, bevel=0.01, color=METAL)
    for y in (-height * 0.4, height * 0.4):
        rb(it, "metal", 0.1, 0.3, 0.05, X(0.03), y, 0.045, bevel=0.01, color=METAL)
    return it


def kitchendoor():
    return _kitchendoor("KitchenDoor", 1.75, 2.2, 0.835, False)


def kitchendoorm():
    return _kitchendoor("KitchenDoorM", 1.75, 2.2, 0.835, True)


def sidedoor():
    return _kitchendoor("SideDoor", 1.5, 2.42, 0.935, False)


def sidedoorm():
    return _kitchendoor("SideDoorM", 1.5, 2.42, 0.935, True)


def sinkdoor():
    return _kitchendoor("SinkDoor", 2.76, 2.42, 0.935, False)


def coffeedoor():
    return _kitchendoor("CoffeeDoor", 2.18, 2.42, 0.935, False)


def lockerbody():
    """Personal two-compartment locker (start room): plinth, three side walls, top and bottom, back, hat shelf, hanging rail with hooks, feet.
    Game: x +-1.67, y 0.27..4.68, z +-0.64 (front -Z), hinges at x -1.62 and 0.03, door panels 1.6 x 4.24 (separate meshes)."""
    it = Item("LockerBody")
    BODY, SHELF, METAL = "#27323b", "#e2e4d8", "#abb8b5"
    for sx in (-1.645, 0.0, 1.645):
        rb(it, "paint", 0.05, 4.45, 1.28, sx, 2.495, 0, bevel=0.01, color=BODY)
    rb(it, "paint", 3.34, 0.1, 1.3, 0, 4.67, 0, bevel=0.02, seg=2, color="#2f3f48")                  # top
    rb(it, "paint", 3.3, 0.08, 1.28, 0, 0.31, 0, bevel=0.01, color=BODY)                              # bottom
    rb(it, "paint", 3.3, 4.4, 0.06, 0, 2.47, 0.61, color=BODY)                                         # back
    rb(it, "paint", 3.3, 0.18, 1.24, 0, 0.19, 0, bevel=0.01, color="#161b1e")                         # plinth
    for sx in (-1.5, 1.5):
        for sz in (-0.5, 0.5):
            rpost(it, "metal", 0.06, 0.0, 0.12, sx, sz, seg=12, color=METAL)
    for cx in (-0.8, 0.8):
        rb(it, "paint", 1.56, 0.06, 1.16, cx, 3.64, -0.02, bevel=0.008, color=SHELF)                  # hat shelf
        rb(it, "metal", 1.5, 0.04, 0.04, cx, 3.31, 0.1, bevel=0.01, color=METAL)                      # hanging rail
        for k in range(6):
            rb(it, "metal", 0.05, 0.08, 0.14, cx - 0.62 + k * 0.25, 3.06, 0.45, bevel=0.01, color=METAL)  # hooks
    return it


def lockerdoor():
    """Locker door in the local frame of its HingePivot (hinge at x 0, panel to +x 1.58, centred vertically 4.24 tall, front -Z): raised
    border, 6 vent slots, lock cylinder and a vertical pull; the game keeps the label plate and the prompt."""
    it = Item("LockerDoor")
    TEAL, RIM, METAL, DARK = "#407477", "#366064", "#abb8b5", "#101a1c"
    rb(it, "paint", 1.58, 4.24, 0.06, 0.79, 0.0, 0.0, bevel=0.012, seg=2, color=TEAL)
    for y in (-2.0, 2.0):
        rb(it, "paint", 1.46, 0.08, 0.012, 0.79, y, -0.034, bevel=0.003, color=RIM)
    for x in (0.1, 1.48):
        rb(it, "paint", 0.08, 4.0, 0.012, x, 0.0, -0.034, bevel=0.003, color=RIM)
    for k in range(6):
        rb(it, "rubber", 1.0, 0.07, 0.012, 0.8, -1.81 + k * 0.725, -0.036, color=DARK)               # vent slots
    rb(it, "metal", 0.07, 0.5, 0.06, 1.34, -0.02, -0.08, bevel=0.02, seg=3, color=METAL)            # vertical pull
    rb(it, "metal", 0.12, 0.12, 0.03, 1.34, -0.28, -0.055, bevel=0.03, seg=3, color="#8a9a99")      # lock boss
    rb(it, "rubber", 0.03, 0.06, 0.02, 1.34, -0.28, -0.07, color=DARK)
    for y in (-1.57, 0.0, 1.5):
        rpost(it, "metal", 0.05, y - 0.22, y + 0.22, 0.0, 0.03, seg=12, color=METAL)                 # hinge barrels
    return it


def _disc(it, mat, r, thick, x, y, zback, color, bevel=0.0):
    """Disc with its axis along Roblox z: from z=zback towards the front (-z) by `thick`."""
    cyl(it, mat, r, thick, (-x, zback, y), seg=40, color=color, rot=Rx(math.pi / 2), bevel=bevel)


def firstaidbody():
    """First-aid wall cabinet (corridor): cream shell, three shelves with medicine bottles, cartons, bandage rolls, scissors and a sterile pack.
    Game: back x +-0.91, y 0..2.46, z -0.31..0.31 (front -z); the door hinge is at x -0.96, z -0.36."""
    it = Item("FirstAidBody")
    SH, SHELF, GREEN, WHITE, METAL = "#e2e3d3", "#dce1d2", "#457e6f", "#edeadb", "#abb8b5"
    for sx in (-0.97, 0.97):
        rb(it, "paint", 0.06, 2.46, 0.62, sx, 1.23, 0, bevel=0.01, color=SH)
    rb(it, "paint", 2.0, 0.07, 0.64, 0, 2.425, 0, bevel=0.012, color=SH)
    rb(it, "paint", 2.0, 0.07, 0.64, 0, 0.035, 0, bevel=0.012, color=SH)
    rb(it, "paint", 1.9, 2.38, 0.05, 0, 1.23, 0.285, color="#d6d9c6")
    for y in (0.14, 0.82, 1.63):
        rb(it, "paint", 1.88, 0.05, 0.5, 0, y, 0.02, bevel=0.008, color=SHELF)
    rb(it, "paper", 0.66, 0.5, 0.26, -0.5, 0.42, 0.05, bevel=0.015, color=GREEN)                # cartons
    rb(it, "paper", 0.66, 0.5, 0.26, 0.42, 0.42, 0.05, bevel=0.015, color=WHITE)
    rb(it, "paper", 0.5, 0.1, 0.012, -0.5, 0.5, -0.085, color="#edeadb")
    rb(it, "paper", 0.5, 0.1, 0.012, 0.42, 0.5, -0.085, color=GREEN)
    
    for x in (-0.55, -0.22, 0.1):                                                              # bandage rolls (axis z)
        _disc(it, "paper", 0.13, 0.22, x, 0.95, 0.11, WHITE, 0.01)
        _disc(it, "paper", 0.045, 0.23, x, 0.95, 0.115, "#c9c3a8")
    rb(it, "metal", 0.22, 0.02, 0.05, 0.72, 0.86, -0.08, bevel=0.005, color=METAL, rot=Rz(0.4))   # scissors
    rb(it, "metal", 0.22, 0.02, 0.05, 0.72, 0.86, -0.08, bevel=0.005, color=METAL, rot=Rz(-0.4))
    rb(it, "paper", 0.26, 0.04, 0.2, 0.28, 0.87, -0.05, color=WHITE)                              # sterile pack
    for i, x in enumerate((-0.75, -0.38, -0.02, 0.34, 0.68)):                                   # bottles on the top shelf
        rpost(it, "paint", 0.1, 1.655, 1.97, x, 0.045, seg=18, color=WHITE if i % 2 == 0 else "#e2e3d3", bevel=0.02)
        rpost(it, "paint", 0.045, 1.97, 2.06, x, 0.045, seg=14, color=WHITE)
        rpost(it, "paint", 0.06, 2.06, 2.13, x, 0.045, seg=14, color=GREEN, bevel=0.01)
        rb(it, "paper", 0.14, 0.16, 0.012, x, 1.82, -0.057, color=GREEN)
    return it


def firstaiddoor():
    """First-aid door in the local frame of its HingePivot (hinge at x 0, panel to +x 1.92, y +-1.18, front -z): green panel with raised
    border, vertical pull bar, hinge barrels. The game keeps the cross mark (MedicalMark) and the prompt part."""
    it = Item("FirstAidDoor")
    GREEN, RIM, METAL = "#457e6f", "#386657", "#abb8b5"
    rb(it, "paint", 1.92, 2.36, 0.06, 0.96, 0.0, 0.0, bevel=0.012, seg=2, color=GREEN)
    for y in (-1.1, 1.1):
        rb(it, "paint", 1.76, 0.1, 0.012, 0.96, y, -0.034, bevel=0.003, color=RIM)
    for x in (0.1, 1.82):
        rb(it, "paint", 0.1, 2.2, 0.012, x, 0.0, -0.034, bevel=0.003, color=RIM)
    rb(it, "metal", 0.06, 0.42, 0.05, 1.7, 0.0, -0.09, bevel=0.015, seg=3, color=METAL)
    for y in (-0.85, 0.85):
        rpost(it, "metal", 0.05, y - 0.18, y + 0.18, 0.0, 0.03, seg=12, color=METAL)
        rb(it, "metal", 0.1, 0.2, 0.04, 0.05, y, 0.06, bevel=0.01, color=METAL)
    return it


def extinguisherbody():
    """Extinguisher cabinet (corridor): red shell, wall bracket, base shoe, a red cylinder extinguisher with domed shoulder, valve block,
    gauge, lever, pull pin and a hose to a nozzle. Game: back x +-0.78, y 0..3.03, z -0.49..0.49, door hinge x -0.82, z -0.54."""
    it = Item("ExtinguisherBody")
    RED, DARK, METAL, GOLD, BLACK = "#b14136", "#8c322a", "#abb8b5", "#be9e50", "#2b3032"
    for sx in (-0.79, 0.79):
        rb(it, "paint", 0.06, 3.03, 0.98, sx, 1.515, 0, bevel=0.012, color=RED)
    rb(it, "paint", 1.64, 0.07, 1.0, 0, 3.0, 0, bevel=0.015, color=RED)
    rb(it, "paint", 1.64, 0.07, 1.0, 0, 0.035, 0, bevel=0.015, color=RED)
    rb(it, "paint", 1.56, 2.96, 0.05, 0, 1.52, 0.46, color=DARK)
    rb(it, "metal", 1.2, 0.08, 0.04, 0, 0.55, 0.43, color=METAL)
    rb(it, "metal", 1.2, 0.08, 0.04, 0, 2.15, 0.43, color=METAL)
    rb(it, "metal", 0.84, 0.05, 0.6, 0, 0.275, -0.02, bevel=0.01, color=METAL)                  # base shoe
    cx, cz = 0.0, -0.02
    rpost(it, "paint", 0.32, 0.30, 1.72, cx, cz, seg=40, color=RED, bevel=0.03)                 # body
    ball(it, "paint", 0.32, (-cx, cz, 1.72), scale=(1, 1, 0.55), color=RED, seg=24)            # shoulder dome (upper half visible)
    rpost(it, "metal", 0.085, 2.0, 2.15, cx, cz, seg=16, color=METAL)                           # neck collar
    rb(it, "metal", 0.16, 0.2, 0.2, 0.0, 2.2, cz - 0.02, bevel=0.03, color=GOLD)                # valve block
    rb(it, "paint", 0.55, 0.1, 0.07, -0.25, 2.36, cz - 0.02, bevel=0.02, color=RED, rot=Ry(-0.08))   # lever
    rb(it, "metal", 0.5, 0.06, 0.05, -0.27, 2.26, cz - 0.02, bevel=0.01, color=METAL)           # fixed handle
    _disc(it, "metal", 0.1, 0.06, 0.0, 2.12, cz - 0.1, "#cfd6d3", 0.01)                          # gauge
    _disc(it, "paper", 0.075, 0.01, 0.0, 2.12, cz - 0.16, WHITE if False else "#edeadb")
    rb(it, "rubber", 0.012, 0.07, 0.01, 0.01, 2.14, cz - 0.172, color="#b14136", rot=Rz(0.5))   # needle
    _disc(it, "metal", 0.07, 0.015, 0.14, 2.24, cz - 0.15, METAL, 0.003)                        # pull pin ring
    rb(it, "rubber", 0.07, 1.4, 0.07, 0.16, 1.55, cz - 0.2, bevel=0.03, color=BLACK)            # hose
    rb(it, "rubber", 0.5, 0.07, 0.07, 0.36, 0.78, cz - 0.2, bevel=0.03, color=BLACK)
    rb(it, "rubber", 0.13, 0.24, 0.13, 0.5, 0.68, cz - 0.15, bevel=0.03, color="#1a1d1f")      # nozzle
    rb(it, "paper", 0.94, 0.65, 0.09, 0, 1.245, -0.325, bevel=0.01, color="#edeadb")            # label backing (the game keeps the label)
    return it


def extinguisherdoor():
    """Extinguisher cabinet door (local frame of its hinge): red frame 1.64 x 2.92 around the game's glass pane (x .12..1.52, y +-1.35),
    vertical pull bar, hinge barrels. The game keeps the header (CabinetHeader) and the prompt part."""
    it = Item("ExtinguisherDoor")
    RED, METAL = "#b14136", "#abb8b5"
    for y in (-1.395, 1.395):
        rb(it, "paint", 1.64, 0.13, 0.06, 0.82, y, 0.0, bevel=0.012, seg=2, color=RED)
    for x in (0.06, 1.58):
        rb(it, "paint", 0.12, 2.92, 0.06, x, 0.0, 0.0, bevel=0.012, seg=2, color=RED)
    rb(it, "paint", 1.5, 0.05, 0.03, 0.82, -1.33, -0.02, color="#8c322a")
    rb(it, "paint", 1.5, 0.05, 0.03, 0.82, 1.2, -0.02, color="#8c322a")
    rb(it, "metal", 0.06, 0.46, 0.05, 1.43, 0.0, -0.09, bevel=0.015, seg=3, color=METAL)
    for y in (-1.23, 1.23):
        rpost(it, "metal", 0.05, y - 0.2, y + 0.2, 0.0, 0.03, seg=12, color=METAL)
        rb(it, "metal", 0.1, 0.22, 0.04, 0.05, y, 0.06, bevel=0.01, color=METAL)
    return it


def firehosebody():
    """Fire-hose cabinet (corridor): red shell with a coiled hose on a reel, nozzle, valve with a handwheel and supply pipe. Game: back
    x +-1.14, y 0..3.05, z -0.23..0.23, door hinge x -1.19, z -0.25."""
    it = Item("FireHoseBody")
    RED, DARK, METAL, GOLD, HOSE = "#b14136", "#8c322a", "#abb8b5", "#be9e50", "#e2e3d3"
    for sx in (-1.16, 1.16):
        rb(it, "paint", 0.06, 3.05, 0.46, sx, 1.525, 0, bevel=0.012, color=RED)
    rb(it, "paint", 2.38, 0.07, 0.48, 0, 3.015, 0, bevel=0.015, color=RED)
    rb(it, "paint", 2.38, 0.07, 0.48, 0, 0.035, 0, bevel=0.015, color=RED)
    rb(it, "paint", 2.3, 2.98, 0.04, 0, 1.52, 0.2, color=DARK)
    cx, cy = 0.03, 1.57
    _disc(it, "paint", 0.82, 0.04, cx, cy, 0.17, "#d6d9c6", 0.005)                              # reel plate
    for i, r in enumerate((0.78, 0.69, 0.60, 0.51, 0.42, 0.33)):                                 # coil rings, stepped so faces differ
        _disc(it, "rubber", r, 0.17 + 0.02 * i, cx, cy, 0.15, HOSE if i % 2 == 0 else "#cfd2bd", 0.012)
    _disc(it, "metal", 0.15, 0.32, cx, cy, 0.17, METAL, 0.01)                                   # hub
    rb(it, "metal", 0.5, 0.12, 0.1, 0.62, 0.9, -0.1, bevel=0.03, color="#4a4e50")              # nozzle body
    rb(it, "metal", 0.1, 0.14, 0.12, 0.84, 0.92, -0.1, bevel=0.02, color=GOLD)                  # nozzle collar
    rb(it, "metal", 0.22, 0.1, 0.1, 0.45, 0.78, -0.08, bevel=0.02, color="#2b2f31")            # nozzle grip
    rb(it, "metal", 0.19, 0.11, 0.11, -0.875, 2.435, 0.13, bevel=0.02, color=GOLD)             # supply pipe
    rpost(it, "metal", 0.06, 2.3, 2.5, -0.88, -0.02, seg=14, color=METAL)                       # valve stem
    _disc(it, "paint", 0.17, 0.03, -0.88, 2.44, -0.03, RED, 0.01)                              # handwheel
    return it


def firehosedoor():
    """Fire-hose cabinet door (local frame of its hinge): red frame 2.38 x 2.96 around the game's glass pane (x .12..2.25, y +-1.36),
    vertical pull bar, hinge barrels. The game keeps the header (HoseHeader) and the prompt part."""
    it = Item("FireHoseDoor")
    RED, METAL = "#b14136", "#abb8b5"
    for y in (-1.42, 1.42):
        rb(it, "paint", 2.38, 0.12, 0.04, 1.19, y, 0.0, bevel=0.01, seg=2, color=RED)
    for x in (0.06, 2.32):
        rb(it, "paint", 0.12, 2.96, 0.04, x, 0.0, 0.0, bevel=0.01, seg=2, color=RED)
    rb(it, "metal", 0.06, 0.46, 0.05, 2.16, 0.0, -0.06, bevel=0.015, seg=3, color=METAL)
    for y in (-1.24, 1.24):
        rpost(it, "metal", 0.05, y - 0.2, y + 0.2, 0.0, 0.0, seg=12, color=METAL)
        rb(it, "metal", 0.1, 0.22, 0.04, 0.05, y, 0.03, bevel=0.01, color=METAL)
    return it


ITEMS = {"ergochair": ergochair, "meetingchair": meetingchair, "visitorchair": visitorchair, "monitorshell": monitorshell, "monitorshellp": monitorshellp, "monitorfoot": monitorfoot, "keyboard": keyboard, "foldingchair": foldingchair, "toilet": toilet, "wallsockets": wallsockets, "archivecabinet": archivecabinet, "archivedoor": archivedoor, "archivedoorm": archivedoorm, "glazedcabinet": glazedcabinet, "glazeddoor": glazeddoor, "glazeddoorm": glazeddoorm, "shelfrack": shelfrack, "shelfload": shelfload, "lowcabinet": lowcabinet, "lowdoor": lowdoor, "lowdoorm": lowdoorm, "filecabinet": filecabinet, "filedrawer": filedrawer, "sortingcabinet": sortingcabinet, "cornershelf": cornershelf, "formscabinet": formscabinet, "kitchenbody": kitchenbody, "sidebody": sidebody, "coffeebody": coffeebody, "kitchendoor": kitchendoor, "kitchendoorm": kitchendoorm, "sidedoor": sidedoor, "sidedoorm": sidedoorm, "sinkdoor": sinkdoor, "coffeedoor": coffeedoor, "lockerbody": lockerbody, "lockerdoor": lockerdoor, "firstaidbody": firstaidbody, "firstaiddoor": firstaiddoor, "extinguisherbody": extinguisherbody, "extinguisherdoor": extinguisherdoor, "firehosebody": firehosebody, "firehosedoor": firehosedoor}


def main():
    names = WANT or list(ITEMS)
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
