"""KONTUR interior hero items (Blender, quality level 5).
Run: Blender -b --python interior_hero.py -- <out_dir> [item,item,...]
Items: bookcase, watercooler, coatrack, floorlamp, armchair, filingcabinet.
Units: 1 Blender unit = 1 stud, Z up, item front faces -Y (becomes Roblox -Z on FBX export), origin = floor centre of the footprint.
Every item is built as one mesh per material (vertex colours carry the per-object tint), exported to <out_dir>/fbx/<Item>.fbx,
rendered from 10 views (8 around, 1 high, 1 low) to <out_dir>/previews/<item>_v<k>.png and a stats line is printed."""
import sys, math, random
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else Path("/tmp/kontur_hero"); OUT.mkdir(parents=True, exist_ok=True)
WANT = argv[1].split(",") if len(argv) > 1 and argv[1] != "all" else None
RENDER = "--norender" not in argv


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def unlin(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def srgb_of(rgba):
    return tuple(unlin(c) for c in rgba[:3])


def hexc(h):
    h = h.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (lin(r), lin(g), lin(b), 1.0)


# name -> (hex, roughness, metallic, emission strength, transmission)
MATS = {
    "wood_dark": ("#3a261b", .52, 0, 0, 0), "wood_mid": ("#6b4a31", .55, 0, 0, 0), "wood_light": ("#b98b5e", .5, 0, 0, 0),
    "metal": ("#9aa1a8", .34, .9, 0, 0), "metal_dark": ("#3b4046", .42, .8, 0, 0), "brass": ("#b8913f", .3, .9, 0, 0),
    "plastic_white": ("#e6e9eb", .38, 0, 0, 0), "plastic_gray": ("#6c7279", .5, 0, 0, 0), "plastic_blue": ("#2f6fb0", .35, 0, 0, 0),
    "plastic_red": ("#b8332f", .35, 0, 0, 0), "glass_blue": ("#9fd3ee", .08, 0, 0, .9), "rubber": ("#1b1d20", .8, 0, 0, 0),
    "paint": ("#ffffff", .68, 0, 0, 0), "fabric": ("#ffffff", .92, 0, 0, 0), "paper": ("#efe6d2", .85, 0, 0, 0),
    "shade": ("#ffe2b0", .9, 0, 0.55, 0), "enamel": ("#6e7880", .42, 0, 0, 0), "leaf": ("#2f6b3d", .6, 0, 0, 0), "ceramic": ("#d9d4c8", .25, 0, 0, 0),
}
PAL_BOOKS = ["#7a2c2c", "#2c5270", "#3a6246", "#c4a85c", "#583e6e", "#d6ceb8", "#464a54", "#966038", "#26383f", "#b07a4c", "#8a3f5c", "#2f4a2c", "#a64a2a", "#3d5f87"]


class Group:
    """One mesh per (material, colour): Roblox gets the colour from MeshPart.Color (set by the server from the mesh name), the
    vertex colours stay white."""
    def __init__(self, mat, colorhex):
        self.mat = mat; self.colorhex = colorhex
        self.bm = bmesh.new(); self.col = self.bm.loops.layers.color.new("Col"); self.face_srgb = []

    def add(self, local, color=None):
        rgba = (1.0, 1.0, 1.0, 1.0)
        vmap = {}
        for v in local.verts:
            vmap[v.index] = self.bm.verts.new(v.co)
        for f in local.faces:
            try:
                nf = self.bm.faces.new([vmap[v.index] for v in f.verts])
            except ValueError:
                continue
            nf.smooth = True
            self.face_srgb.append(srgb_of(hexc(self.colorhex)))
            for loop in nf.loops:
                loop[self.col] = rgba


class Item:
    def __init__(self, name):
        self.name = name; self.groups = {}

    def g(self, mat, colorhex):
        key = (mat, colorhex.lstrip("#").lower())
        if key not in self.groups:
            self.groups[key] = Group(mat, key[1])
        return self.groups[key]

    def put(self, local, mat, color=None, M=None):
        if M is not None:
            bmesh.ops.transform(local, matrix=M, verts=local.verts)
        self.g(mat, color or MATS[mat][0]).add(local)
        local.free()


def _cube(sx, sy, sz, bevel=0.0, seg=2):
    bm = bmesh.new()
    x, y, z = sx / 2, sy / 2, sz / 2
    vs = [bm.verts.new(p) for p in [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]]
    for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        bm.faces.new([vs[i] for i in f])
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(sx, sy, sz) * 0.45), segments=seg, profile=0.6, affect="EDGES", clamp_overlap=True)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm


def T(x=0, y=0, z=0):
    return Matrix.Translation((x, y, z))


def Rz(a): return Matrix.Rotation(a, 4, "Z")
def Rx(a): return Matrix.Rotation(a, 4, "X")
def Ry(a): return Matrix.Rotation(a, 4, "Y")


def box(it, mat, size, pos, bevel=0.0, seg=2, color=None, rot=None):
    """Box of `size` whose BOTTOM centre is at pos (x, y, z0)."""
    bm = _cube(*size, bevel=bevel, seg=seg)
    M = T(pos[0], pos[1], pos[2] + size[2] / 2)
    if rot is not None:
        M = T(pos[0], pos[1], pos[2]) @ rot @ T(0, 0, size[2] / 2)
    it.put(bm, mat, color, M)


def lathe(it, mat, profile, pos=(0, 0, 0), seg=32, color=None, scale=(1, 1, 1), rot=None, closed=False):
    """Revolve a (radius, z) profile around Z. Radius 0 points sit on the axis."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    if closed:
        es.append(bm.edges.new((vs[-1], vs[0])))
    bmesh.ops.spin(bm, geom=vs + es, axis=(0, 0, 1), cent=(0, 0, 0), angle=math.tau, steps=seg, use_merge=False)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    S = Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
    M = T(*pos) @ (rot if rot is not None else Matrix.Identity(4)) @ S
    it.put(bm, mat, color, M)


def cyl(it, mat, r, h, pos, seg=24, r2=None, color=None, rot=None, bevel=0.0):
    r2 = r if r2 is None else r2
    b = min(bevel, r * .45, h * .45)
    prof = [(0, 0), (max(r - b, 0.001), 0)]
    if b > 0:
        for k in range(1, 4):
            a = k / 3 * math.pi / 2
            prof.append((r - b + b * math.sin(a), b - b * math.cos(a)))
    prof += [(r2, h - b) if b > 0 else (r2, h)]
    if b > 0:
        for k in range(1, 4):
            a = k / 3 * math.pi / 2
            prof.append((r2 - b + b * math.cos(a), h - b + b * math.sin(a)))
    prof += [(0, h)]
    lathe(it, mat, prof, pos, seg, color, rot=rot)


def ball(it, mat, r, pos, scale=(1, 1, 1), color=None, seg=16, rot=None):
    prof = [(0, -r)] + [(r * math.sin(a), -r * math.cos(a)) for a in [i / 8 * math.pi for i in range(1, 8)]] + [(0, r)]
    lathe(it, mat, prof, pos, seg, color, scale=scale, rot=rot)


def finish(it):
    """groups -> objects (one per material+colour), smooth shading with sharp edges, returns list of objects."""
    objs = []
    for (mat, colorhex), grp in it.groups.items():
        bm = grp.bm
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(38):
                e.smooth = False
        me = bpy.data.meshes.new(f"{it.name}_{mat}_{colorhex}")
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(f"{it.name}_{mat}_{colorhex}", me)
        bpy.context.scene.collection.objects.link(ob)
        mname = f"{mat}_{colorhex}"
        m = bpy.data.materials.get(mname)
        if m is None:
            hexcol, rough, metal, emit, trans = MATS[mat]
            m = bpy.data.materials.new(mname); m.use_nodes = True
            bsdf = m.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Base Color"].default_value = hexc(colorhex)
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metal
            if trans:
                bsdf.inputs["Transmission Weight"].default_value = trans
                bsdf.inputs["IOR"].default_value = 1.4
            if emit:
                bsdf.inputs["Emission Color"].default_value = hexc(colorhex)
                bsdf.inputs["Emission Strength"].default_value = emit
        ob.data.materials.append(m)
        ob["face_srgb"] = [list(c) for c in grp.face_srgb]
        objs.append(ob)
    return objs


# ---------------------------------------------------------------- items
def book(it, rng, x, y0, z0, t, d, h, color, lean=0.0, bands=True, depth_shift=0.0):
    """Spine faces front (-Y). (x, z0) = bottom centre; y0 = back face y; lean tilts around the bottom edge."""
    M = T(x, y0 + d / 2 - depth_shift, z0) @ Ry(lean)
    bm = _cube(t, d, h, bevel=min(0.014, t * .22), seg=2)
    bmesh.ops.transform(bm, matrix=T(0, 0, h / 2), verts=bm.verts)
    it.put(bm, "paint", color, M)
    pg = _cube(t - 0.05, d - 0.07, h - 0.06, bevel=0.0)
    bmesh.ops.transform(pg, matrix=T(0, 0.03, h / 2), verts=pg.verts)
    it.put(pg, "paper", None, M)
    front = -d / 2 - 0.004
    for zc in ([h * .86, h * .14] if bands else []):
        b = _cube(t * .96, 0.012, 0.035)
        bmesh.ops.transform(b, matrix=T(0, front, zc), verts=b.verts)
        it.put(b, "brass" if rng.random() < .6 else "paint", "#d9c27a" if rng.random() < .6 else "#e8e2d0", M)
    if rng.random() < .75 and t > 0.12:
        lab = _cube(t * .62, 0.012, h * rng.uniform(.18, .3))
        bmesh.ops.transform(lab, matrix=T(0, front, h * rng.uniform(.5, .66)), verts=lab.verts)
        it.put(lab, "paper", "#efe6d2", M)


def bookcase():
    it = Item("Bookcase")
    rng = random.Random(7)
    W, D, H = 3.6, 1.1, 7.0
    sw = 0.14
    iw = W - 2 * sw
    plinth = 0.4
    top = 0.22
    # carcass (front toward -Y, back panel at +Y)
    box(it, "wood_dark", (W - 0.1, D - 0.12, plinth), (0, -0.02, 0), bevel=0.03)
    for sx in (-1, 1):
        box(it, "wood_mid", (sw, D, H - plinth - top + 0.02), (sx * (W / 2 - sw / 2), 0, plinth), bevel=0.02)
    box(it, "wood_mid", (W + 0.2, D + 0.16, top), (0, -0.01, H - top), bevel=0.06, seg=3)
    box(it, "wood_mid", (iw + 0.02, 0.07, H - plinth - top), (0, D / 2 - 0.05, plinth), color="#4a3223")
    # shelves
    z = plinth
    box(it, "wood_mid", (iw, D - 0.12, 0.13), (0, -0.04, z), bevel=0.02)
    cupboard = 1.45
    z += 0.13
    # lower cupboard with two doors
    for sx in (-1, 1):
        box(it, "wood_mid", (iw / 2 - 0.03, 0.08, cupboard - 0.06), (sx * (iw / 4), -D / 2 + 0.04, z + 0.03), bevel=0.025, seg=2)
        box(it, "wood_light", (iw / 2 - 0.4, 0.04, cupboard - 0.5), (sx * (iw / 4), -D / 2 - 0.005, z + 0.25), bevel=0.015)
        cyl(it, "brass", 0.045, 0.16, (sx * 0.18, -D / 2 - 0.03, z + cupboard * .6), r2=0.045, rot=Rx(math.pi / 2), seg=12, bevel=0.01)
    z += cupboard
    box(it, "wood_mid", (iw, D - 0.12, 0.13), (0, -0.04, z), bevel=0.02)
    z += 0.13
    comps = 4
    ch = (H - top - z - (comps - 1) * 0.13) / comps
    for ci in range(comps):
        back = -D / 2 + 0.1
        x = -iw / 2 + 0.06
        end = iw / 2 - 0.05
        mode = ["full", "prop", "full", "stack"][ci % 4]
        books = []
        while x < end - 0.2:
            t = rng.uniform(0.09, 0.27)
            hh = rng.uniform(0.66, ch - 0.14)
            if x + t > end:
                break
            books.append((x, t, hh)); x += t + rng.uniform(0.0, 0.012)
        keep = len(books) if mode == "full" else int(len(books) * rng.uniform(.55, .72))
        for k, (bx, t, hh) in enumerate(books[:keep]):
            d = rng.uniform(.62, .84)
            lean = 0.0
            if k == keep - 1 and mode != "full":
                lean = rng.uniform(.14, .28) * rng.choice([1, -1]) if rng.random() < .5 else 0.0
            book(it, rng, bx + t / 2, back, z, t, d, hh, rng.choice(PAL_BOOKS), lean, depth_shift=rng.uniform(0, .08))
        if mode != "full":
            px = books[keep - 1][0] + books[keep - 1][1] + 0.32 if keep else -iw / 2 + 0.5
            if mode == "prop" and px < end - 0.3:
                kind = ["plant", "frame", "trophy", "box"][ci % 4]
                if kind == "frame":
                    box(it, "wood_dark", (0.68, 0.07, 0.86), (px + 0.2, -0.05, z), bevel=0.012, rot=Rx(-0.1))
                    box(it, "paper", (0.5, 0.02, 0.68), (px + 0.2, -0.09, z + 0.09), rot=Rx(-0.1), color="#c9d6dc")
                    box(it, "plastic_gray", (0.22, 0.015, 0.2), (px + 0.2, -0.1, z + 0.24), rot=Rx(-0.1), color="#8c9aa0")
                elif kind == "plant":
                    cyl(it, "ceramic", 0.2, 0.34, (px + 0.2, 0, z), r2=.17, bevel=.03, seg=20, color="#bdb5a4")
                    for k in range(7):
                        a = k / 7 * math.tau
                        ball(it, "leaf", 0.12, (px + 0.2 + math.cos(a) * .12, math.sin(a) * .12, z + .5 + .08 * (k % 3)), (.55, .25, 1.5), color=rng.choice(["#2f6b3d", "#3f7b4a", "#25583a"]), seg=10, rot=Rz(a) @ Ry(math.cos(a * 2) * .5))
                elif kind == "trophy":
                    cyl(it, "wood_dark", 0.26, 0.14, (px + 0.2, 0, z), seg=18, bevel=.02)
                    cyl(it, "brass", 0.08, 0.34, (px + 0.2, 0, z + 0.14), r2=.05, seg=12)
                    lathe(it, "brass", [(0, 0), (0.06, 0.03), (0.2, 0.28), (0.22, 0.34), (0.18, 0.34), (0.15, 0.1), (0, 0.06)], (px + 0.2, 0, z + .48), 18)
                else:
                    box(it, "paper", (0.7, 0.62, 0.52), (px + .25, -0.02, z), bevel=0.015, color="#cdbb94")
                    box(it, "paper", (0.58, 0.012, 0.18), (px + .25, -0.34, z + .2), color="#efe6d2")
            elif mode == "stack":
                sx0 = end - 0.95
                zz = z
                for k in range(rng.randint(3, 4)):
                    bw, bd, bh = rng.uniform(.72, .92), rng.uniform(.6, .76), rng.uniform(.1, .16)
                    box(it, "paint", (bw, bd, bh), (sx0 + .45 + rng.uniform(-.04, .04), -0.02, zz), bevel=0.012, color=rng.choice(PAL_BOOKS), rot=Rz(rng.uniform(-.12, .12)))
                    zz += bh
                if rng.random() < .6:
                    ball(it, "paper", 0.0001, (0, 0, 0))  # placeholder no-op
        z += ch
        box(it, "wood_mid", (iw, D - 0.12, 0.13), (0, -0.04, z), bevel=0.02)
        z += 0.13
    return it


def watercooler():
    it = Item("WaterCooler")
    # body
    box(it, "plastic_white", (1.34, 1.2, 0.18), (0, 0, 0), bevel=0.05)                       # plinth lip
    box(it, "plastic_white", (1.3, 1.16, 2.5), (0, 0, 0.18), bevel=0.11, seg=3)
    box(it, "plastic_gray", (0.96, 0.05, 0.9), (0, -0.6, 1.38), bevel=0.02)                   # front tap recess
    box(it, "plastic_gray", (0.9, 0.3, 0.06), (0, -0.62, 0.92), bevel=0.01)                   # tray shelf
    for k in range(7):
        box(it, "metal", (0.9, 0.018, 0.03), (0, -0.7 + k * 0.026, 0.935))
    for sx, mat in ((-0.2, "plastic_blue"), (0.2, "plastic_red")):
        cyl(it, mat, 0.075, 0.2, (sx, -0.6, 1.6), rot=Rx(math.pi / 2 * 1), seg=14, bevel=0.02)
        cyl(it, "metal", 0.035, 0.12, (sx, -0.78, 1.55), seg=10)
    box(it, "plastic_white", (1.12, 1.0, 0.1), (0, 0, 2.68), bevel=0.04)
    cyl(it, "plastic_white", 0.5, 0.18, (0, 0, 2.75), r2=0.4, seg=28)
    # bottle (inverted, neck down)
    lathe(it, "glass_blue", [(0.0, 2.84), (0.18, 2.84), (0.2, 3.0), (0.38, 3.22), (0.52, 3.6), (0.54, 4.7), (0.48, 5.05), (0.28, 5.28), (0.0, 5.34)], (0, 0, 0), 36, color="#8fc8ea")
    cyl(it, "plastic_blue", 0.2, 0.06, (0, 0, 2.84), seg=18)
    # cup dispenser on the side
    cyl(it, "plastic_gray", 0.18, 1.0, (0.78, 0, 1.3), seg=18, bevel=0.03)
    cyl(it, "metal_dark", 0.2, 0.05, (0.78, 0, 2.3), seg=18)
    for k in range(3):
        lathe(it, "paper", [(0.0, 0), (0.07, 0), (0.12, 0.3), (0.0, 0.3)], (0.78, 0, 2.35 + k * 0.1), 14, color="#f2efe6")
    # drip lamp
    ball(it, "plastic_blue", 0.04, (0.45, -0.61, 2.2), seg=8, color="#6cc1ff")
    return it


def coatrack():
    it = Item("CoatRack")
    cyl(it, "wood_dark", 0.78, 0.12, (0, 0, 0), seg=36, bevel=0.05)
    cyl(it, "wood_dark", 0.28, 0.35, (0, 0, 0.12), r2=0.12, seg=24)
    cyl(it, "wood_mid", 0.095, 5.5, (0, 0, 0.3), r2=0.075, seg=20)
    ball(it, "wood_dark", 0.15, (0, 0, 5.88), scale=(1, 1, 1.15), seg=14)
    for tier, zh, off in ((0, 5.1, 0.0), (1, 4.5, math.pi / 3)):
        for k in range(3):
            a = off + k * math.tau / 3
            d = Vector((math.cos(a), math.sin(a), 0))
            cyl(it, "metal", 0.05, 0.62, (d.x * 0.08, d.y * 0.08, zh), seg=10, rot=Rz(a) @ Ry(math.pi / 2) @ Matrix.Identity(4))
            ball(it, "metal", 0.07, (d.x * 0.68, d.y * 0.68, zh), seg=10)
            cyl(it, "metal", 0.04, 0.18, (d.x * 0.64, d.y * 0.64, zh), seg=8)
    # coats
    def coat(a, zt, col, wide=1.0):
        d = Vector((math.cos(a), math.sin(a), 0))
        px, py = d.x * 0.68, d.y * 0.68
        rot = Rz(a + math.pi / 2)
        lathe(it, "metal_dark", [(0.02, 0), (0.34, -0.2), (0.36, -0.22)], (px, py, zt + .22), 6, scale=(1, .14, 1), rot=rot)  # hanger
        prof = [(0.0, 0.18), (0.3 * wide, 0.14), (0.42 * wide, -0.15), (0.46 * wide, -1.2), (0.52 * wide, -2.2), (0.5 * wide, -2.6), (0.0, -2.6)]
        lathe(it, "fabric", prof, (px, py, zt), 22, color=col, scale=(1, 0.66, 1), rot=rot)
        for s in (-1, 1):
            lathe(it, "fabric", [(0.0, 0.0), (0.15, 0.0), (0.12, -1.7), (0.0, -1.7)], (px + rot.col[0][0] * s * 0.46 * wide, py + rot.col[0][1] * s * 0.46 * wide, zt - 0.12), 12, color=col, scale=(1, 1, 1), rot=rot @ Ry(s * 0.14))
        lathe(it, "fabric", [(0.34, 0.1), (0.32, 0.0), (0.0, -0.05)], (px, py, zt + 0.1), 18, color="#2b2f35", scale=(1, 0.5, 1), rot=rot)  # collar
        for k in range(4):
            ball(it, "plastic_gray", 0.03, (px - d.y * 0.0 + d.x * 0.2, py + d.y * 0.2, zt - 0.5 - k * 0.5), seg=8)
    coat(0.0, 5.0, "#46505c", 1.0)
    coat(2 * math.tau / 3, 5.0, "#6a3a24", 0.9)
    # scarf and umbrella on tier 2
    a = math.pi / 3 + 2 * math.tau / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    cyl(it, "fabric", 0.14, 1.8, (d.x * 0.68, d.y * 0.68, 2.7), seg=10, color="#a8362e", bevel=0.04)
    a2 = math.pi / 3 + math.tau / 3
    d2 = Vector((math.cos(a2), math.sin(a2), 0))
    lathe(it, "fabric", [(0.0, 0.0), (0.42, -1.1), (0.0, -1.1)], (d2.x * 0.68, d2.y * 0.68, 4.35), 12, color="#1f2a44", scale=(.5, .5, 1))
    cyl(it, "metal_dark", 0.025, 0.7, (d2.x * 0.68, d2.y * 0.68, 3.4), seg=8)
    return it


def floorlamp():
    it = Item("FloorLamp")
    cyl(it, "metal_dark", 0.78, 0.12, (0, 0, 0), seg=36, bevel=0.05)
    cyl(it, "brass", 0.14, 0.18, (0, 0, 0.12), r2=0.09, seg=20)
    cyl(it, "brass", 0.05, 4.4, (0, 0, 0.3), seg=14)
    for zz in (1.9, 3.1):
        cyl(it, "brass", 0.085, 0.1, (0, 0, zz), seg=14, bevel=0.02)
    cyl(it, "metal_dark", 0.12, 0.28, (0, 0, 4.7), r2=0.08, seg=16)
    # drum shade (double wall so it reads from inside too)
    lathe(it, "shade", [(0.8, 5.0), (0.9, 5.45), (1.0, 6.0)], (0, 0, -0.15), 40, color="#e2b878")
    lathe(it, "shade", [(0.76, 5.0), (0.86, 5.45), (0.96, 6.0)], (0, 0, -0.15), 40, color="#f6cf94")
    for zz in (5.0 - 0.15, 6.0 - 0.15):
        lathe(it, "brass", [(0.76, zz), (0.8, zz)] if zz < 5.5 else [(0.96, zz), (1.0, zz)], (0, 0, 0), 40)
    for k in range(3):
        a = k * math.tau / 3
        cyl(it, "brass", 0.018, 0.78, (math.cos(a) * 0.04, math.sin(a) * 0.04, 4.95), seg=6, rot=Rz(a) @ Ry(math.pi / 2 - 0.4))
    ball(it, "shade", 0.18, (0, 0, 5.3), seg=14, color="#fff2cf")
    cyl(it, "brass", 0.012, 0.9, (0.3, 0, 4.0), seg=6)
    ball(it, "brass", 0.05, (0.3, 0, 3.98), seg=8)
    return it


def armchair():
    it = Item("Armchair")
    fab = "#2f6b6a"
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(it, "wood_mid", 0.09, 0.62, (sx * 0.95, sy * 0.9, 0), r2=0.055, seg=14, rot=Rx(-sy * 0.12) @ Ry(sx * 0.12) @ Matrix.Identity(4))
    box(it, "wood_dark", (2.3, 2.1, 0.18), (0, 0, 0.55), bevel=0.04)
    box(it, "fabric", (1.9, 1.9, 0.58), (0, -0.05, 0.73), bevel=0.2, seg=4, color=fab)                  # seat cushion
    box(it, "fabric", (0.5, 2.15, 1.35), (-1.1, 0.0, 0.6), bevel=0.17, seg=4, color=fab)              # arm
    box(it, "fabric", (0.5, 2.15, 1.35), (1.1, 0.0, 0.6), bevel=0.17, seg=4, color=fab)
    box(it, "fabric", (2.2, 0.62, 1.9), (0, 0.78, 0.7), bevel=0.2, seg=4, color=fab, rot=Rx(0.16) @ Matrix.Identity(4))  # back
    box(it, "fabric", (1.5, 0.35, 0.95), (0, 0.45, 1.3), bevel=0.15, seg=4, color="#3f8584", rot=Rx(0.12) @ Matrix.Identity(4))  # back cushion
    for sx in (-1, 1):
        box(it, "wood_dark", (0.5, 0.05, 0.04), (sx * 1.1, -1.03, 1.55), bevel=0.01)
    box(it, "wood_dark", (1.9, 0.03, 0.04), (0, -0.98, 1.2), bevel=0.01)
    return it


def filingcabinet():
    it = Item("FilingCabinet")
    W, D, H = 1.6, 2.0, 4.3
    box(it, "metal_dark", (W - 0.08, D - 0.08, 0.2), (0, 0, 0), bevel=0.03)
    box(it, "enamel", (W, D, H - 0.2), (0, 0, 0.2), bevel=0.06, seg=3)
    dh = (H - 0.5) / 4
    for k in range(4):
        z = 0.32 + k * dh
        box(it, "enamel", (W - 0.18, 0.07, dh - 0.07), (0, -D / 2 - 0.01, z), bevel=0.03, color="#7b858c")
        box(it, "metal_dark", (0.8, 0.05, 0.06), (0, -D / 2 - 0.08, z + dh - 0.35), bevel=0.02)        # pull handle bar
        for sx in (-0.38, 0.38):
            box(it, "metal_dark", (0.06, 0.07, 0.06), (sx, -D / 2 - 0.06, z + dh - 0.35))
        box(it, "paper", (0.5, 0.012, 0.18), (0, -D / 2 - 0.047, z + dh - 0.7), color="#efe6d2")
        box(it, "plastic_gray", (0.34, 0.012, 0.04), (0, -D / 2 - 0.05, z + dh - 0.64), color="#4a4f57")
    cyl(it, "brass", 0.07, 0.05, (0.55, -D / 2 - 0.045, H - 0.45), rot=Rx(math.pi / 2), seg=12)
    return it


ITEMS = {"bookcase": bookcase, "watercooler": watercooler, "coatrack": coatrack, "floorlamp": floorlamp, "armchair": armchair, "filingcabinet": filingcabinet}



import struct, base64


def encode_item(name, objs):
    """Per material group: split vertices (position, normal, colour) deduplicated, Roblox axes (x, y, z) = (-X, Z, Y),
    positions relative to the group's own bbox centre (stored as `center`). Returns a Luau table literal."""
    parts = []
    allmin = [1e9] * 3; allmax = [-1e9] * 3
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        cols = ob["face_srgb"]
        vmap = {}; verts = []; tris = []
        norms = me.corner_normals
        for tri in me.loop_triangles:
            ids = []
            for l in tri.loops:
                co = me.vertices[me.loops[l].vertex_index].co
                nr = norms[l].vector
                pos = (-co.x, co.z, co.y); nrm = (-nr.x, nr.z, nr.y)
                c = cols[tri.polygon_index]
                c16 = (min(31, max(0, round(c[0] * 31))) << 10) | (min(31, max(0, round(c[1] * 31))) << 5) | min(31, max(0, round(c[2] * 31)))
                key = (round(pos[0] * 1000), round(pos[1] * 1000), round(pos[2] * 1000), round(nrm[0] * 100), round(nrm[1] * 100), round(nrm[2] * 100), c16)
                if key not in vmap:
                    vmap[key] = len(verts); verts.append((pos, nrm, c16))
                ids.append(vmap[key])
            if len(set(ids)) == 3:
                tris.append(ids)
        mn = [min(v[0][i] for v in verts) for i in range(3)]; mx = [max(v[0][i] for v in verts) for i in range(3)]
        for i in range(3):
            allmin[i] = min(allmin[i], mn[i]); allmax[i] = max(allmax[i], mx[i])
        ctr = [(mn[i] + mx[i]) / 2 for i in range(3)]
        vb = b"".join(struct.pack("<hhh", *[int(round((v[0][i] - ctr[i]) * 1000)) for i in range(3)]) for v in verts)
        nb = b"".join(struct.pack("<bbb", *[int(round(max(-1, min(1, x)) * 127)) for x in v[1]]) for v in verts)
        cb = b"".join(struct.pack("<H", v[2]) for v in verts)
        tb = b"".join(struct.pack("<HHH", *t) for t in tris)
        b64 = lambda b: base64.b64encode(b).decode()
        mat = ob.name.split("_", 1)[1]
        parts.append((mat, ctr, len(verts), len(tris), b64(vb), b64(nb), b64(cb), b64(tb)))
    size = [allmax[i] - allmin[i] for i in range(3)]
    mid = [(allmax[i] + allmin[i]) / 2 for i in range(3)]
    lines = [f'  {name}={{size=Vector3.new({size[0]:.3f},{size[1]:.3f},{size[2]:.3f}),mid=Vector3.new({mid[0]:.3f},{mid[1]:.3f},{mid[2]:.3f}),groups={{']
    for mat, ctr, nv, nt, v, n, c, t in parts:
        lines.append(f'    {{mat="{mat}",center=Vector3.new({ctr[0]:.4f},{ctr[1]:.4f},{ctr[2]:.4f}),nv={nv},nt={nt},')
        lines.append(f'      v="{v}",n="{n}",c="{c}",t="{t}"}},')
    lines.append("  }},")
    return "\n".join(lines)

# ---------------------------------------------------------------- export + render
def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 28; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 560, 420
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.16, 0.18, 0.21, 1); bg.inputs[1].default_value = 0.9
    sc.view_settings.view_transform = "AgX" if "AgX" in [x.identifier for x in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items] else "Standard"
    return sc


def add_lights(sc, center, size):
    r = max(size)
    for name, pos, energy, col in (("key", (3.2 * r, -3.2 * r, 3.6 * r), 2600 * r, (1, .93, .84)), ("fill", (-3.6 * r, -1.2 * r, 1.6 * r), 900 * r, (.78, .87, 1)), ("rim", (0.5 * r, 3.8 * r, 3.2 * r), 1200 * r, (1, 1, 1))):
        ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = r * 2.4; ld.color = col
        lo = bpy.data.objects.new(name, ld); lo.location = pos; sc.collection.objects.link(lo)
        direction = Vector(center) - lo.location
        lo.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    floor = bpy.data.meshes.new("floor"); bm = bmesh.new()
    s = r * 6
    vs = [bm.verts.new(p) for p in [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)]]
    bm.faces.new(vs); bm.to_mesh(floor); bm.free()
    fo = bpy.data.objects.new("floor", floor); sc.collection.objects.link(fo)
    fm = bpy.data.materials.new("floor"); fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.1, 0.11, 1)
    fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    fo.data.materials.append(fm)


def render_views(sc, name, objs):
    mins = Vector((1e9, 1e9, 1e9)); maxs = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        for v in ob.bound_box:
            w = ob.matrix_world @ Vector(v)
            mins = Vector(map(min, mins, w)); maxs = Vector(map(max, maxs, w))
    center = (mins + maxs) / 2; size = maxs - mins
    add_lights(sc, center, size)
    cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 40
    cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    dist = max(size) * 1.9 + 2.0
    (OUT / "previews").mkdir(exist_ok=True)
    for k in range(10):
        if k < 8: az, el, d = k * 45, 20, dist
        elif k == 8: az, el, d = 20, 62, dist * .95
        else: az, el, d = 200, 4, dist * .8
        a, e = math.radians(az) - math.pi / 2, math.radians(el)       # az 0 = looking at the front (camera at -Y)
        cam.location = center + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * d
        cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(OUT / "previews" / f"{name}_v{k}.png")
        bpy.ops.render.render(write_still=True)


def to_srgb_numbers(objs):
    """Roblox reads FBX vertex colours as the displayed (sRGB) numbers; the Blender attribute holds linear values for shading,
    so right before export the numbers are converted and the exporter is told not to convert again (colors_type LINEAR)."""
    for ob in objs:
        attr = ob.data.color_attributes["Col"]
        for d in attr.data:
            r, g, b, a = d.color
            d.color = (unlin(r), unlin(g), unlin(b), a)


def export(name, objs):
    (OUT / "fbx").mkdir(exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=str(OUT / "fbx" / f"{name}.fbx"), use_selection=True, object_types={"MESH"}, global_scale=1.0,
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                             colors_type="NONE", mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False, path_mode="COPY", embed_textures=False)


def stats(name, objs):
    out = []
    tot = 0
    for ob in objs:
        me = ob.data; me.calc_loop_triangles(); tris = len(me.loop_triangles); tot += tris
        out.append(f"{ob.name.split('_', 1)[1]}={tris}")
    print(f"STATS {name}: tris={tot} verts={sum(len(o.data.vertices) for o in objs)} | " + " ".join(out), flush=True)


def main():
    names = WANT or list(ITEMS)
    luau = ["-- Generated by sources/evolution-v39/blender/interior_hero.py (Blender, level 5). Roblox axes, front = -Z.",
            "-- Per material group: v = int16*0.001 studs relative to group centre, n = int8*1/127, c = RGB555 sRGB, t = uint16 triangle indices; base64.",
            "HERO_DATA = {"]
    for n in names:
        sc = setup_scene()
        it = ITEMS[n]()
        objs = finish(it)
        stats(it.name, objs)
        luau.append(encode_item(it.name, objs))
        if RENDER:
            render_views(sc, it.name, objs)
        export(it.name, objs)   # last: it rewrites the colour numbers for Roblox
    luau.append("}")
    (OUT / "HeroData.luau").write_text("\n".join(luau))
    print("HERODATA bytes", (OUT / "HeroData.luau").stat().st_size, flush=True)
    print("DONE", flush=True)


main()
