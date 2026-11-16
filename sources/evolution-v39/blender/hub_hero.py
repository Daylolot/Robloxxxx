"""KONTUR hub (FieldHub) hero items, Blender level 5: hazmat suit on a hanger, respirator dispensing station.
Run: Blender -b --python hub_hero.py -- <out_dir> [hazmat,maskstation] [--norender]
Reuses the helpers of interior_hero.py (Group/Item/box/cyl/lathe/ball/finish/encode_item/export/render are exec'd from it).
Units: 1 Blender unit = 1 stud, Z up, item front faces -Y, origin = floor centre of the footprint."""
import sys, math, random
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

_here = Path(__file__).resolve().parent
_src = (_here / "interior_hero.py").read_text()
_head = _src[:_src.index("# ---------------------------------------------------------------- items")]
_tail = _src[_src.index("import struct, base64"):_src.index("def main():")]
exec(compile(_head, "interior_hero_head", "exec"), globals())
exec(compile(_tail, "interior_hero_tail", "exec"), globals())

MATS.update({
    "suit": ("#f4d230", .8, 0, 0, 0),          # hazmat fabric (vertex colours add the shade variations)
    "tape": ("#c3cad0", .28, .5, 0, 0),         # reflective tape
    "visor": ("#0e242c", .06, 0, 0, 0),
    "steel": ("#6d838a", .5, .15, 0, 0),
    "dark_panel": ("#1d282c", .5, 0, 0, 0),
    "glass_clear": ("#bfe6f2", .05, 0, 0, .9),
    "mask_rubber": ("#5b6f7a", .6, 0, 0, 0),
    "shell": ("#3a4a46", .55, 0, 0, 0),         # case body: recoloured per instance on the server
    "lid": ("#3f504b", .55, 0, 0, 0),
    "trim": ("#1d2528", .5, .2, 0, 0),
})


def tube(it, mat, pts, radii, sides=16, color=None, squash=(1.0, 1.0), caps=True, ring_mod=None):
    """Loft a tube along 3D points with per-point radius (smooth, round). Returns [(point, radius, tangent)]."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tans = []
    for i in range(n):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        tans.append((b - a).normalized())
    bm = bmesh.new()
    rings = []
    up = Vector((0, 0, 1))
    for i, (p, r, t) in enumerate(zip(pts, radii, tans)):
        ref = up if abs(t.dot(up)) < 0.95 else Vector((1, 0, 0))
        side = t.cross(ref).normalized()
        nrm = side.cross(t).normalized()
        ring = []
        for k in range(sides):
            a = k / sides * math.tau
            rr = r * (ring_mod(i, k) if ring_mod else 1.0)
            ring.append(bm.verts.new(p + side * (math.cos(a) * rr * squash[0]) + nrm * (math.sin(a) * rr * squash[1])))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(sides):
            a, b = rings[i][k], rings[i][(k + 1) % sides]
            c, d = rings[i + 1][(k + 1) % sides], rings[i + 1][k]
            bm.faces.new((a, b, c, d))
    if caps:
        for end, idx in ((0, 0), (1, n - 1)):
            centre = bm.verts.new(pts[idx])
            ring = rings[idx]
            for k in range(sides):
                if end == 0:
                    bm.faces.new((centre, ring[(k + 1) % sides], ring[k]))
                else:
                    bm.faces.new((centre, ring[k], ring[(k + 1) % sides]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    it.put(bm, mat, color)
    return list(zip(pts, radii, tans))


def torus(it, mat, R, r, pos, scale=(1, 1, 1), color=None, rot=None, seg=28, minor=10):
    prof = [(R + r * math.cos(a), r * math.sin(a)) for a in [k / minor * math.tau for k in range(minor)]]
    lathe(it, mat, prof, pos, seg, color, scale=scale, rot=rot, closed=True)


def hazmat():
    it = Item("HazmatSuit")
    suit_a, suit_b = "#f4d230", "#e5bf24"
    boot, glove = "#1b1d20", "#23262a"
    sy = 0.64   # torso/limb cross-section squash (front-back)
    # --- feet plates and boots
    for sx in (-1, 1):
        box(it, "rubber", (0.95, 1.7, 0.07), (sx * 0.52, -0.12, 0), bevel=0.03)
        lathe(it, "rubber", [(0, 0), (0.43, 0), (0.46, 0.08), (0.43, 0.7), (0.32, 0.86), (0.0, 0.9)], (sx * 0.52, 0.08, 0.07), 20, scale=(1, 1.08, 1), color=boot)
        ball(it, "rubber", 0.4, (sx * 0.52, -0.5, 0.3), scale=(1.0, 1.35, 0.62), color=boot, seg=20)          # toe cap
        for k in range(5):                                                                                      # sole lugs
            box(it, "rubber", (0.9, 0.05, 0.05), (sx * 0.52, -0.95 + k * 0.28, 0.07), bevel=0.012, color="#2c2f33")
        torus(it, "tape", 0.34, 0.035, (sx * 0.52, 0.12, 0.86), scale=(1, 1.0, 1), color="#c9d0d5")           # ankle seal
    # --- legs: hip -> knee -> ankle with soft folds
    for sx in (-1, 1):
        pts = [(sx * 0.4, 0.02, 3.35), (sx * 0.44, 0.0, 2.7), (sx * 0.46, -0.07, 2.05), (sx * 0.47, -0.02, 1.4), (sx * 0.47, 0.06, 0.95)]
        rad = [0.54, 0.47, 0.43, 0.39, 0.34]
        s = tube(it, "suit", pts, rad, 20, suit_a, squash=(1.0, 0.92), ring_mod=lambda i, k: 1 + 0.05 * math.sin(i * 2.1 + k * 0.7))
        torus(it, "tape", 0.405, 0.032, (sx * 0.47, -0.04, 1.7), scale=(1, 0.92, 1), color="#c9d0d5")            # reflective bands
        torus(it, "tape", 0.395, 0.032, (sx * 0.47, -0.04, 1.62), scale=(1, 0.92, 1), color="#c9d0d5")
        ball(it, "suit", 0.2, (sx * 0.47, -0.4, 2.05), scale=(1.1, 0.5, 1.0), color="#cfa820", seg=14)         # knee patch
        for z, rr in ((2.7, .44), (1.1, .33)):
            torus(it, "suit", rr + 0.02, 0.035, (sx * 0.46, 0.0, z), scale=(1, 0.92, 1), color=suit_b)
    # --- torso (elliptical lathe) and pelvis
    lathe(it, "suit", [(0.0, 3.1), (0.62, 3.14), (0.82, 3.5), (0.78, 4.0), (0.84, 4.55), (0.92, 5.05), (0.84, 5.45), (0.58, 5.72), (0.0, 5.78)],
          (0, 0, 0), 36, color=suit_a, scale=(1, sy, 1))
    for z, rr in ((3.65, 0.8), (4.15, 0.79)):
        torus(it, "suit", rr + 0.02, 0.05, (0, 0, z), scale=(1, sy, 1), color=suit_b)                          # soft fabric folds at the waist
    torus(it, "tape", 0.9, 0.04, (0, 0, 5.3), scale=(1, sy, 1), color="#c9d0d5")                              # chest reflective band (above the name patch)
    torus(it, "tape", 0.915, 0.04, (0, 0, 5.18), scale=(1, sy, 1), color="#c9d0d5")
    torus(it, "rubber", 0.8, 0.07, (0, 0, 3.8), scale=(1, sy, 1), color="#2a2d31")                              # belt
    box(it, "metal_dark", (0.2, 0.06, 0.16), (0, -0.53, 3.72), bevel=0.02)                                      # buckle
    # zipper, pocket, name patch, hose
    box(it, "metal", (0.045, 0.04, 1.9), (0.0, -0.575, 3.85), bevel=0.01, color="#9aa1a8")
    for k in range(18):
        box(it, "metal", (0.1, 0.03, 0.025), (0.0, -0.585, 3.9 + k * 0.1), color="#7c838a")
    box(it, "suit", (0.55, 0.09, 0.58), (-0.4, -0.55, 3.9), bevel=0.04, color="#d3ae22")
    box(it, "suit", (0.55, 0.1, 0.16), (-0.4, -0.575, 4.35), bevel=0.04, color="#cfa820")
    box(it, "paper", (0.78, 0.03, 0.52), (0.42, -0.585, 4.48), bevel=0.01, color="#f2efe6")        # name patch: the label GUI of the game sits on it
    # --- shoulders / yoke
    ball(it, "suit", 0.5, (0, 0.0, 5.55), scale=(1.55, 0.78 * sy / 0.64 * 0.64, 0.5), color=suit_a, seg=24)
    # --- arms (A-pose) with sleeves, elbow pads, cuffs, gloves
    for sx in (-1, 1):
        pts = [(sx * 1.0, 0.0, 5.45), (sx * 1.28, 0.02, 4.9), (sx * 1.48, 0.08, 4.25), (sx * 1.6, 0.08, 3.65), (sx * 1.66, 0.04, 3.3)]
        rad = [0.42, 0.38, 0.35, 0.31, 0.27]
        s = tube(it, "suit", pts, rad, 18, suit_a, squash=(1.0, 0.9), ring_mod=lambda i, k: 1 + 0.045 * math.sin(i * 2.3 + k * 0.9))
        torus(it, "tape", 0.34, 0.03, (sx * 1.31, 0.02, 4.85), scale=(1, 0.9, 1), color="#c9d0d5", rot=Ry(sx * 0.32))
        torus(it, "tape", 0.335, 0.03, (sx * 1.34, 0.025, 4.75), scale=(1, 0.9, 1), color="#c9d0d5", rot=Ry(sx * 0.32))
        ball(it, "suit", 0.22, (sx * 1.52, 0.34, 4.18), scale=(0.9, 0.6, 1.1), color="#cfa820", seg=14)         # elbow pad
        torus(it, "rubber", 0.27, 0.07, (sx * 1.64, 0.06, 3.46), scale=(1, 0.9, 1), color=glove, rot=Ry(sx * 0.1))   # cuff seal
        # glove: palm + fingers + thumb
        palm = Vector((sx * 1.68, 0.06, 3.12))
        ball(it, "rubber", 0.24, palm, scale=(1.0, 0.55, 1.15), color=glove, seg=16)
        for f in range(4):
            fx = sx * (1.68 + (f - 1.5) * 0.095)
            tube(it, "rubber", [(fx, 0.06, 2.98), (fx + sx * 0.012 * (f - 1.5), 0.07, 2.72 - 0.04 * (1 if f in (1, 2) else 0)), (fx + sx * 0.02 * (f - 1.5), 0.08, 2.5 - 0.06 * (1 if f in (1, 2) else 0))],
                 [0.05, 0.047, 0.04], 8, glove)
        tube(it, "rubber", [(sx * 1.45, 0.02, 3.1), (sx * 1.38, -0.04, 2.92), (sx * 1.36, -0.08, 2.78)], [0.06, 0.055, 0.045], 8, glove)
    # --- helmet: smooth dome, smoked visor with frame, respirator filter, neck seal
    torus(it, "suit", 0.52, 0.11, (0, 0, 5.78), scale=(1, sy, 1), color=suit_b)                                 # neck ring
    lathe(it, "suit", [(0.0, 5.7), (0.6, 5.76), (0.8, 6.2), (0.88, 6.68), (0.78, 7.1), (0.46, 7.38), (0.0, 7.46)], (0, 0, 0.0), 36, scale=(1, 0.95, 1), color="#f8d63a")
    ball(it, "visor", 0.56, (0, -0.55, 6.62), scale=(1.0, 0.5, 0.92), seg=32)                                      # visor lens
    torus(it, "rubber", 0.6, 0.06, (0, -0.53, 6.62), scale=(1.0, 0.5, 0.95), rot=Rx(math.pi / 2), color="#1f2226")   # visor seal
    ball(it, "glass_clear", 0.12, (-0.26, -0.86, 6.9), scale=(1.5, 0.3, 0.55), seg=12, color="#9ad7e8")        # visor highlight
    cyl(it, "plastic_gray", 0.2, 0.28, (0, -0.74, 6.0), rot=Rx(math.pi / 2), seg=20, bevel=0.03, color="#59606a")  # front filter canister
    for sx in (-1, 1):
        cyl(it, "plastic_gray", 0.14, 0.22, (sx * 0.74, -0.1, 6.0), rot=Ry(sx * math.pi / 2), seg=16, bevel=0.025, color="#59606a")   # side vents
    # hanger bar and hook
    cyl(it, "metal", 0.04, 2.3, (-1.15, 0.0, 5.95), rot=Ry(math.pi / 2), seg=10, color="#8d949b")
    tube(it, "metal", [(0, 0, 5.9), (0, 0, 7.5), (0, 0.0, 8.35), (0.0, 0.0, 8.6)], [0.045, 0.045, 0.045, 0.045], 8, "#8d949b")
    ball(it, "metal", 0.07, (0, 0, 8.65), seg=10, color="#8d949b")
    return it


def respirator(it, pos, hang=0.0, cart="#6d4a9e", tilt=0.0):
    """Half-face respirator hanging on its harness (front faces -Y). pos = centre of the face seal."""
    x, y, z = pos
    rot = Rz(tilt)
    def P(dx, dy, dz):
        v = rot @ Vector((dx, dy, dz)); return (x + v.x, y + v.y, z + v.z)
    ball(it, "mask_rubber", 0.34, P(0, 0, 0), scale=(1.0, 0.55, 0.78), seg=18, rot=rot)                          # face seal
    ball(it, "mask_rubber", 0.16, P(0, -0.1, 0.12), scale=(1.0, 0.7, 0.8), seg=12, rot=rot, color="#4e606b")     # nose bridge
    for sx in (-1, 1):
        cyl(it, "plastic_gray", 0.13, 0.1, P(sx * 0.24, -0.15, -0.06), rot=rot @ Rx(math.pi / 2), seg=16, color="#585f68", bevel=0.015)
        cyl(it, "plastic_gray", 0.1, 0.07, P(sx * 0.24, -0.24, -0.06), rot=rot @ Rx(math.pi / 2), seg=16, color=cart, bevel=0.015)
    cyl(it, "metal", 0.05, 0.07, P(0, -0.19, -0.18), rot=rot @ Rx(math.pi / 2), seg=12, color="#9aa1a8")          # exhale valve
    tube(it, "rubber", [P(-0.3, 0.03, 0.05), P(-0.36, 0.05, 0.3), P(-0.1, 0.1, 0.6), P(0.0, 0.1, 0.8)], [0.022, 0.022, 0.022, 0.022], 6, "#1c1f23", caps=False)   # harness straps up to the hook
    tube(it, "rubber", [P(0.3, 0.03, 0.05), P(0.36, 0.05, 0.3), P(0.1, 0.1, 0.6), P(0.0, 0.1, 0.8)], [0.022, 0.022, 0.022, 0.022], 6, "#1c1f23", caps=False)
    ball(it, "metal", 0.035, P(0, 0.1, 0.82), seg=8, color="#9aa1a8")


def maskstation():
    it = Item("MaskStation")
    W = 3.8
    # base cabinet with two doors and toe kick
    box(it, "steel", (W - 0.3, 2.0, 0.22), (0, 0.0, 0.0), bevel=0.03, color="#2f3d41")                       # toe kick
    box(it, "steel", (W, 2.3, 1.2), (0, 0.0, 0.22), bevel=0.07, seg=3, color="#4a5c62")
    for sx in (-1, 1):
        box(it, "steel", (W / 2 - 0.14, 0.06, 1.02), (sx * (W / 4), -1.17, 0.3), bevel=0.04, color="#556870")      # door
        box(it, "steel", (W / 2 - 0.5, 0.03, 0.72), (sx * (W / 4), -1.2, 0.45), bevel=0.02, color="#4a5c62")       # door panel
        cyl(it, "metal", 0.045, 0.34, (sx * 0.2, -1.26, 0.55), rot=Rx(math.pi / 2) @ Matrix.Identity(4), seg=10)  # handle
        for k in range(5):
            box(it, "steel", (0.55, 0.02, 0.03), (sx * (W / 2 - 0.25) + 0, -1.19, 0.38 + k * 0.1), color="#2f3d41", rot=Ry(0))  # vent slits
    # control band (the MaskControl carrier of the original sits here) and label strip
    box(it, "steel", (W, 2.3, 0.18), (0, 0.0, 1.42), bevel=0.05, color="#38484d")                              # worktop
    box(it, "dark_panel", (3.1, 0.14, 0.82), (0, -1.15, 1.6), bevel=0.04)                      # control bezel
    # vitrine: frame, back panel, glass, masks on hooks
    top = 4.55
    for sx in (-1, 1):
        box(it, "steel", (0.16, 1.9, top - 1.6), (sx * (W / 2 - 0.08), 0.0, 1.6), bevel=0.04, color="#38484d")     # side posts
    box(it, "steel", (W, 1.9, 0.2), (0, 0.0, top), bevel=0.06, seg=3, color="#4a5c62")                           # cornice
    box(it, "steel", (W - 0.3, 0.08, top - 1.6), (0, 0.85, 1.6), bevel=0.02, color="#2a373b")                    # back panel
    for row, z in enumerate((2.2, 3.35)):
        box(it, "steel", (W - 0.3, 1.5, 0.07), (0, 0.1, z - 0.1), bevel=0.02, color="#3c4c52")                  # shelf
        for k in range(3):
            box(it, "metal_dark", (0.04, 0.05, 0.12), (-1.2 + k * 1.2, 0.78, z + 0.62), color="#8d949b")        # hook posts
    rng = random.Random(12)
    carts = ["#6d4a9e", "#d6b43a", "#3f7fb5", "#6d4a9e", "#b8433a"]
    for row, z in enumerate((2.45, 3.6)):
        for k in range(5):
            respirator(it, (-1.4 + k * 0.7, 0.55, z), cart=carts[(k + row) % 5], tilt=rng.uniform(-0.08, 0.08))
    if "--noglass" not in sys.argv:
        for sx in (-1, 1):
            box(it, "glass_clear", (0.04, 1.8, top - 1.7), (sx * (W / 2 - 0.22), 0, 1.65), color="#bfe6f2")
        box(it, "glass_clear", (W - 0.36, 0.04, top - 1.75), (0, -0.93, 1.65), color="#bfe6f2")                  # front glass
    box(it, "dark_panel", (W - 0.3, 0.06, 0.07), (0, -0.96, 1.6), bevel=0.02)                   # glass lower rail
    # header sign carrier plate and posts
    for sx in (-1, 1):
        box(it, "steel", (0.1, 0.1, 0.5), (sx * 1.4, -0.05, top + 0.2), bevel=0.02, color="#38484d")
    box(it, "dark_panel", (3.6, 0.2, 0.95), (0, -0.2, top + 0.7), bevel=0.05)                 # header plate
    # status light + take slot on the right post
    ball(it, "plastic_blue", 0.06, (W / 2 - 0.08, -0.98, 3.1), seg=10, color="#35e0d8")
    return it



def hubcase(L=4.78, D=3.0, H=2.54, low=1.4, medical=False):
    """Hard equipment case: shell + lid with seam, corner protectors, ribs, two latches, top handle, label plate.
    Dimensions follow the old hub cases (L along x, D deep, H tall including the handle); label carrier centre z = 0.6."""
    name = "HubCaseMed" if medical else "HubCase"
    it = Item(name)
    lid_top = H - 0.34
    feet = 0.05
    # feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(it, "rubber", (0.5, 0.5, feet + 0.02), (sx * (L / 2 - 0.45), sy * (D / 2 - 0.45), 0), bevel=0.04)
    # lower shell + lid (lid slightly larger lip over the seam)
    box(it, "shell", (L, D, low - feet), (0, 0, feet), bevel=0.16, seg=3)
    box(it, "lid", (L + 0.02, D + 0.02, lid_top - low), (0, 0, low), bevel=0.2, seg=3)
    box(it, "trim", (L + 0.04, D + 0.04, 0.05), (0, 0, low - 0.025), bevel=0.02)                          # seam gasket
    # corner protectors (vertical caps over the seam) and top corner caps
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(it, "trim", (0.55, 0.55, lid_top - feet - 0.04), (sx * (L / 2 - 0.22), sy * (D / 2 - 0.22), feet + 0.02), bevel=0.12, seg=2)
    # reinforcement ribs on the lid top and on the shell front/back
    for k in range(-2, 3):
        box(it, "trim", (0.12, D - 0.9, 0.07), (k * (L / 6), 0, lid_top - 0.04), bevel=0.03)
    for k in (-1, 0, 1):
        for sy in (-1, 1):
            box(it, "trim", (0.16, 0.06, low - feet - 0.5), (k * (L / 3.2), sy * (D / 2 + 0.01), feet + 0.25), bevel=0.02)
    # latches (front, -Y): base plate, hook, pin
    for sx in (-1, 1):
        x = sx * L * 0.27
        box(it, "metal", (0.55, 0.09, 0.6), (x, -D / 2 - 0.04, low - 0.32), bevel=0.03)
        box(it, "metal_dark", (0.34, 0.1, 0.22), (x, -D / 2 - 0.1, low + 0.12), bevel=0.03)
        cyl(it, "metal_dark", 0.05, 0.14, (x, -D / 2 - 0.1, low - 0.05), rot=Rx(math.pi / 2), seg=10)
    # label plate (front, centre z 0.6): the game's InventoryTag sits on it
    box(it, "paper", (1.7, 0.05, 0.78), (0, -D / 2 - 0.025, 0.21), bevel=0.015, color="#d9d6c8")
    # top handle: two mounts and a rubber grip arch
    for sx in (-1, 1):
        box(it, "trim", (0.28, 0.5, 0.2), (sx * 0.85, 0, lid_top - 0.02), bevel=0.05)
    grip = tube(it, "rubber", [(-0.85, 0, lid_top + 0.18), (-0.6, 0, lid_top + 0.33), (0.6, 0, lid_top + 0.33), (0.85, 0, lid_top + 0.18)], [0.1, 0.1, 0.1, 0.1], 12, "#15181a")
    # end handles (recessed grips on the short sides)
    for sx in (-1, 1):
        box(it, "rubber", (0.12, 0.9, 0.22), (sx * (L / 2 + 0.03), 0, low * 0.55), bevel=0.04, color="#15181a")
    if medical:
        # white cross on the lid top and on the front
        box(it, "paper", (0.9, 0.18, 0.04), (0, 0.0, lid_top - 0.02), color="#f2efe6")
        box(it, "paper", (0.18, 0.9, 0.04), (0, 0.0, lid_top - 0.02), color="#f2efe6")
        box(it, "paper", (0.7, 0.04, 0.16), (-L * 0.36, -D / 2 - 0.02, low + 0.12), color="#f2efe6")
        box(it, "paper", (0.16, 0.04, 0.7), (-L * 0.36, -D / 2 - 0.02, low - 0.15), color="#f2efe6") if False else None
    return it



def suitrack():
    """Gantry for the hazmat suits: two posts on foot bars with braces, the 18-stud rail, two header brackets.
    x = along the rail (world Z), y = front/back (world X; posts sit 0.09 behind the middle), origin = floor centre."""
    it = Item("SuitRack")
    steel, steel_d = "#4a565d", "#2e383d"
    top = 8.73            # rail height above the floor (world 9.5 - 0.77)
    for sx in (-9.0, 9.0):
        box(it, "steel", (0.3, 2.4, 0.25), (sx, 0.09, 0.0), bevel=0.06, seg=2, color=steel_d)              # foot bar
        for sy in (-1, 1):
            box(it, "rubber", (0.34, 0.2, 0.22), (sx, 0.09 + sy * 1.1, 0.0), bevel=0.04, color="#15181a")     # rubber end caps
        box(it, "steel", (0.34, 0.34, 0.12), (sx, 0.09, 0.25), bevel=0.04, color=steel_d)                 # base collar
        box(it, "steel", (0.22, 0.22, top - 0.3), (sx, 0.09, 0.3), bevel=0.05, seg=2, color=steel)          # post
        for sy in (-1, 1):                                                                                 # diagonal braces foot -> post
            tube(it, "steel", [(sx, 0.09 + sy * 1.0, 0.25), (sx, 0.09 + sy * 0.5, 1.1), (sx, 0.09, 2.0)], [0.05, 0.05, 0.05], 8, steel_d)
        box(it, "steel", (0.34, 0.34, 0.4), (sx, 0.09, top - 0.35), bevel=0.05, color=steel_d)              # rail mount block
        cyl(it, "metal", 0.06, 0.05, (sx, 0.09 + 0.12, 0.7), rot=Rx(math.pi / 2), seg=10, color="#9aa1a8")  # bolts
        cyl(it, "metal", 0.06, 0.05, (sx, 0.09 - 0.17, 0.7), rot=Rx(-math.pi / 2), seg=10, color="#9aa1a8")
    # rail with end caps
    tube(it, "steel", [(-9.05, 0.09, top), (9.05, 0.09, top)], [0.1, 0.1], 16, "#8d949b")
    for sx in (-1, 1):
        ball(it, "steel", 0.11, (sx * 9.1, 0.09, top), seg=12, color="#8d949b")
    # rail brackets every 3 studs (collars) so the rail does not look like a bare tube
    for k in range(-2, 3):
        torus(it, "metal_dark", 0.1, 0.03, (k * 3.0, 0.09, top), rot=Ry(math.pi / 2), color="#3b4046", seg=14, minor=6) if False else None
    # header brackets: arms from the rail up and forward, with a small plate at the top (the sign hangs there)
    for sx in (-4.0, 4.0):
        tube(it, "steel", [(sx, 0.12, top), (sx, -0.6, top + 0.7), (sx, -1.29, top + 1.34)], [0.055, 0.05, 0.05], 8, steel_d)
        box(it, "steel", (0.5, 0.14, 0.34), (sx, -1.36, top + 1.18), bevel=0.03, color=steel)
        box(it, "metal", (0.12, 0.05, 0.12), (sx, -1.45, top + 1.29), bevel=0.01, color="#9aa1a8")
    return it


def equipbench():
    """Equipment bench 3.2 x 7.0 (x width, y length), top at z 1.07: slatted seat in a frame, two U legs, bolts."""
    it = Item("EquipmentBench")
    W, Ln = 3.2, 7.0
    top = 1.07
    slat_c = "#4a5954"
    frame_c = "#2f393e"
    n = 8
    sw = (W - 0.12 - (n - 1) * 0.05) / n
    for k in range(n):
        x = -W / 2 + 0.06 + k * (sw + 0.05) + sw / 2
        box(it, "steel", (sw, Ln - 0.16, 0.2), (x, 0, top - 0.3), bevel=0.04, color=slat_c)
    for sx in (-1, 1):                                                   # long side rails (angle iron)
        box(it, "steel", (0.14, Ln, 0.34), (sx * (W / 2 - 0.07), 0, top - 0.34), bevel=0.04, color=frame_c)
    for sy in (-1, 1):                                                   # end rails
        box(it, "steel", (W, 0.14, 0.34), (0, sy * (Ln / 2 - 0.07), top - 0.34), bevel=0.04, color=frame_c)
    for sy in (-2.5, 2.5):                                               # two U-legs with cross bars and feet
        for sx in (-1, 1):
            box(it, "steel", (0.22, 0.25, top - 0.6), (sx * 1.2, sy, 0.05), bevel=0.05, color=frame_c)
            box(it, "rubber", (0.34, 0.4, 0.07), (sx * 1.2, sy, 0), bevel=0.02, color="#15181a")
        box(it, "steel", (2.64, 0.2, 0.18), (0, sy, 0.3), bevel=0.04, color=frame_c)           # lower cross bar
        box(it, "steel", (2.64, 0.28, 0.16), (0, sy, top - 0.62), bevel=0.04, color=frame_c)    # top support bar
    for sx in (-1, 1):                                                   # bolts on the rails
        for sy in range(-3, 4):
            cyl(it, "metal", 0.045, 0.03, (sx * (W / 2 - 0.0), sy * 0.95, top - 0.2), rot=Ry(sx * math.pi / 2), seg=8, color="#9aa1a8")
    return it

ITEMS = {"hazmat": hazmat, "maskstation": maskstation, "hubcase": lambda: hubcase(), "hubcasemed": lambda: hubcase(4.08, 2.6, 1.74, 1.0, True), "suitrack": suitrack, "equipbench": equipbench}


def main():
    names = WANT or list(ITEMS)
    luau = ["-- Generated by sources/evolution-v39/blender/hub_hero.py (Blender, level 5). Roblox axes, front = -Z.", "HERO_DATA = {"]
    for n in names:
        sc = setup_scene()
        it = ITEMS[n]()
        objs = finish(it)
        stats(it.name, objs)
        luau.append(encode_item(it.name, objs))
        if RENDER:
            render_views(sc, it.name, objs)
        export(it.name, objs)
    luau.append("}")
    (OUT / "HubHeroData.luau").write_text("\n".join(luau))
    print("DONE", flush=True)


main()
