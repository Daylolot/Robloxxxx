"""KONTUR v36 plants, Blender level 5 study.
Run: Blender -b --python plants_v36.py -- <out_dir>
Builds three potted plants (fiddle-leaf fig, peace lily, monstera) as single vertex-coloured meshes in studs
(1 Blender unit = 1 stud, Z up), renders previews and writes PlantData.luau for runtime EditableMesh creation."""
import sys, math, random, base64, struct
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

out = Path(sys.argv[sys.argv.index("--") + 1]); out.mkdir(parents=True, exist_ok=True)
Z = Vector((0, 0, 1))

def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def srgb(r, g, b): return (r / 255, g / 255, b / 255)

class Builder:
    """Accumulates verts, per-vertex colours and triangles."""
    def __init__(self): self.v = []; self.c = []; self.t = []
    def add(self, p, col): self.v.append(tuple(p)); self.c.append(col); return len(self.v) - 1
    def tri(self, a, b, c): self.t.append((a, b, c))
    def grid(self, ids):  # ids[row][col] -> quads split into triangles
        for r in range(len(ids) - 1):
            for k in range(len(ids[0]) - 1):
                a, b, c, d = ids[r][k], ids[r][k + 1], ids[r + 1][k + 1], ids[r + 1][k]
                self.tri(a, b, c); self.tri(a, c, d)

def rot(vec, axis, ang): return Matrix.Rotation(ang, 3, axis) @ vec

def leaf(B, origin, direction, length, width, shape, droop, fold, wave, base_col, rnd, rows=8, cols=5, phase=0.0):
    d = direction.normalized(); side = d.cross(Z)
    if side.length < 1e-4: side = Vector((1, 0, 0))
    side.normalize()
    centre = [Vector(origin)]
    dirs = []
    for i in range(rows):
        u = i / (rows - 1)
        di = rot(d, side, -droop * u ** 1.6) if False else rot(d, side, droop * u ** 1.6)  # positive droop pitches the tip down
        dirs.append(di)
        if i < rows - 1: centre.append(centre[-1] + di * length / (rows - 1))
    ids = []
    for i in range(rows):
        u = i / (rows - 1)
        w = width * shape(u)
        nrm = side.cross(dirs[i]).normalized()
        if nrm.z < 0: nrm = -nrm
        row = []
        for k in range(cols):
            v = -1 + 2 * k / (cols - 1)
            p = centre[i] + side * (w * v) + nrm * (-fold * w * abs(v) + wave * w * math.sin(u * 6.0 + phase) * abs(v))
            vein = max(0.0, 1 - abs(v) * 3.2) * 0.38 * (1 - u * 0.5)
            edge = abs(v) ** 2 * 0.22
            col = lerp(lerp(base_col, srgb(176, 210, 150), vein), srgb(14, 40, 26), edge)
            row.append(B.add(p, col))
        ids.append(row)
    B.grid(ids)
    return centre[-1]

def tube(B, pts, radii, col, sides=6, col_end=None):
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.cross(Z)
        if a.length < 1e-4: a = Vector((1, 0, 0))
        a.normalize(); b = t.cross(a).normalized()
        c = lerp(col, col_end, i / (len(pts) - 1)) if col_end else col
        rings.append([B.add(p + (a * math.cos(2 * math.pi * s / sides) + b * math.sin(2 * math.pi * s / sides)) * radii[i], c) for s in range(sides)])
    for i in range(len(rings) - 1):
        for s in range(sides):
            n = (s + 1) % sides
            B.tri(rings[i][s], rings[i + 1][s], rings[i + 1][n]); B.tri(rings[i][s], rings[i + 1][n], rings[i][n])

def lathe(B, profile, col_fn, seg=18):
    rings = []
    for (r, z) in profile:
        rings.append([B.add(Vector((r * math.cos(2 * math.pi * s / seg), r * math.sin(2 * math.pi * s / seg), z)), col_fn(r, z)) for s in range(seg)])
    for i in range(len(rings) - 1):
        for s in range(seg):
            n = (s + 1) % seg
            B.tri(rings[i][s], rings[i + 1][s], rings[i + 1][n]); B.tri(rings[i][s], rings[i + 1][n], rings[i][n])

def pot(B, R, H, col, rim_col=None, soil=srgb(34, 28, 24)):
    rim = rim_col or lerp(col, (1, 1, 1), 0.12)
    prof = [(0.0, 0.0), (R * 0.62, 0.0), (R * 0.70, 0.04 * H), (R * 0.86, 0.45 * H), (R * 0.97, 0.88 * H), (R * 1.04, 0.94 * H),
            (R * 1.05, H), (R * 0.97, H * 1.0), (R * 0.94, H * 0.95), (R * 0.88, H * 0.92)]
    seg = 20
    cols = [col, col, col, col, col, rim, rim, rim, lerp(col, (0, 0, 0), 0.35), soil]
    rings = []
    for (r, z), c in zip(prof, cols):
        rings.append([B.add(Vector((r * math.cos(2 * math.pi * s / seg), r * math.sin(2 * math.pi * s / seg), z)), c) for s in range(seg)])
    for i in range(len(rings) - 1):
        for s in range(seg):
            n = (s + 1) % seg
            B.tri(rings[i][s], rings[i + 1][s], rings[i + 1][n]); B.tri(rings[i][s], rings[i + 1][n], rings[i][n])
    # soil cap with a little relief
    centre = B.add(Vector((0, 0, H * 0.97)), soil)
    for s in range(seg): B.tri(rings[-1][s], centre, rings[-1][(s + 1) % seg])
    return Vector((0, 0, H * 0.96))

def fig(seed=11):
    B = Builder(); rnd = random.Random(seed)
    top = pot(B, 0.95, 1.05, srgb(44, 52, 62), srgb(70, 82, 96))
    H = 4.1
    pts = [top + Vector((0.07 * math.sin(i * 0.9), 0.06 * math.cos(i * 0.7), H * i / 7)) for i in range(8)]
    tube(B, pts, [0.14 - 0.013 * i for i in range(8)], srgb(104, 82, 62), 7, srgb(150, 120, 88))
    n = 22
    for i in range(n):
        t = i / (n - 1)
        h = 1.35 + 0.66 * H * t
        j = min(int(h / H * 7), 6); f = h / H * 7 - j
        stem = pts[min(j, 7)].lerp(pts[min(j + 1, 7)], f)
        base = Vector((stem.x, stem.y, top.z + h))
        ang = i * 2.39996 + rnd.uniform(-0.12, 0.12)
        d = Vector((math.cos(ang), math.sin(ang), rnd.uniform(0.18, 0.5)))
        L = rnd.uniform(1.25, 1.65) * (0.8 + 0.25 * t)
        col = lerp(srgb(26, 80, 44), srgb(60, 124, 62), rnd.random())
        pe = base + d.normalized() * 0.34
        tube(B, [base, base + d.normalized() * 0.17 + Vector((0, 0, 0.03)), pe], [0.04, 0.034, 0.03], srgb(96, 120, 70), 4)
        shape = lambda u: (math.sin(math.pi * u ** 0.8) ** 0.85) * (1 + 0.32 * math.sin(math.pi * min(1, max(0, (u - 0.35) / 0.65))))
        leaf(B, pe, d, L, 0.36, shape, rnd.uniform(0.45, 0.85), 0.26, 0.06, col, rnd, 11, 7, rnd.uniform(0, 6))
    # small crown of new leaves
    for i in range(4):
        ang = i * 1.7
        d = Vector((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 1.0))
        shape = lambda u: math.sin(math.pi * u ** 0.8) ** 0.85
        leaf(B, pts[-1], d, 0.9, 0.2, shape, 0.2, 0.3, 0.0, srgb(86, 148, 70), rnd, 9, 5)
    return B

def lily(seed=5):
    B = Builder(); rnd = random.Random(seed)
    top = pot(B, 0.9, 0.95, srgb(232, 234, 236), srgb(250, 250, 250))
    for i in range(18):
        ang = i * 2.39996 + rnd.uniform(-0.1, 0.1)
        r0 = rnd.uniform(0.1, 0.38)
        base = top + Vector((math.cos(ang) * r0, math.sin(ang) * r0, 0))
        d = Vector((math.cos(ang), math.sin(ang), rnd.uniform(0.4, 1.0)))
        L = rnd.uniform(1.35, 1.8)
        col = lerp(srgb(22, 78, 44), srgb(56, 124, 64), rnd.random())
        shape = lambda u: math.sin(math.pi * min(1, u * 1.04) ** 0.55) ** 0.85
        leaf(B, base, d, L, 0.4, shape, rnd.uniform(1.3, 2.0), 0.18, 0.04, col, rnd, 11, 7, rnd.uniform(0, 6))
    for i in range(7):
        ang = i * 2.39996 + 0.6
        r0 = rnd.uniform(0.08, 0.3)
        base = top + Vector((math.cos(ang) * r0, math.sin(ang) * r0, 0))
        h = rnd.uniform(2.4, 3.3)
        lean = Vector((math.cos(ang), math.sin(ang), 0)) * rnd.uniform(0.15, 0.55)
        pts = [base, base + Vector((0, 0, h * 0.5)) + lean * 0.25, base + Vector((0, 0, h * 0.85)) + lean * 0.7, base + Vector((0, 0, h)) + lean]
        tube(B, pts, [0.032, 0.028, 0.024, 0.022], srgb(70, 118, 66), 5)
        tip = pts[-1]
        d = (Vector((0, 0, 1)) * 0.55 + Vector((math.cos(ang), math.sin(ang), 0)) * 0.55).normalized()
        shape = lambda u: math.sin(math.pi * min(1, u * 1.02) ** 0.7) ** 0.9
        leaf(B, tip, d, 0.66, 0.24, shape, 0.35, -0.7, 0.0, srgb(247, 247, 240), rnd, 8, 7)
        sp = tip + d * 0.05
        tube(B, [sp, sp + d * 0.34], [0.04, 0.034], srgb(238, 214, 146), 6)
    return B

def monstera(seed=3):
    B = Builder(); rnd = random.Random(seed)
    top = pot(B, 1.0, 0.95, srgb(176, 120, 92), srgb(196, 140, 108))
    for i in range(10):
        ang = i * 2.39996 + rnd.uniform(-0.2, 0.2)
        r0 = rnd.uniform(0.05, 0.4)
        base = top + Vector((math.cos(ang) * r0, math.sin(ang) * r0, 0))
        h = rnd.uniform(1.2, 3.0)
        lean = Vector((math.cos(ang), math.sin(ang), 0)) * rnd.uniform(0.5, 1.1)
        pts = [base, base + Vector((0, 0, h * 0.5)) + lean * 0.25, base + Vector((0, 0, h * 0.9)) + lean * 0.8, base + Vector((0, 0, h)) + lean]
        tube(B, pts, [0.05, 0.043, 0.038, 0.034], srgb(70, 112, 62), 5)
        tip = pts[-1]
        d = Vector((math.cos(ang), math.sin(ang), -0.12)) + Vector((0, 0, 0.0))
        L = rnd.uniform(1.4, 1.8); W = rnd.uniform(0.78, 0.95)
        col = lerp(srgb(24, 80, 44), srgb(58, 128, 66), rnd.random())
        rows, cols = 19, 13
        d = d.normalized(); side = d.cross(Z).normalized(); nrm = side.cross(d).normalized()
        if nrm.z < 0: nrm = -nrm
        ids = []
        for r in range(rows):
            u = r / (rows - 1)
            # heart: widest near the petiole, pointed tip, rounded lobes behind the stem
            w = W * (math.sin(math.pi * min(1, u * 0.92 + 0.04) ** 0.5) ** 0.9) * (1 - 0.28 * u)
            notch = 1.0 - 0.34 * (max(0.0, math.sin(u * math.pi * 3.6 + 0.4)) ** 3) * (1 if 0.12 < u < 0.9 else 0)
            row = []
            for k in range(cols):
                v = -1 + 2 * k / (cols - 1)
                wk = w * (1 - (1 - notch) * max(0.0, (abs(v) - 0.45) / 0.55))
                lobe = -0.20 * (1 - u) ** 2 * (abs(v) ** 1.5)
                p = tip + d * (L * (u + lobe)) + side * (wk * v) + nrm * (-0.12 * W * abs(v) * (1 - 0.4 * u) + 0.05 * math.sin(u * 5 + i))
                p = p + Vector((0, 0, -0.55 * u * u * L * 0.3))
                vein = max(0.0, 1 - abs(v) * 4.2) * 0.4 + max(0.0, 1 - abs(abs(v) - 0.5) * 10) * 0.12 * (1 - u)
                row.append(B.add(p, lerp(lerp(col, srgb(168, 208, 146), vein), srgb(14, 40, 26), (abs(v) ** 2) * 0.22)))
            ids.append(row)
        B.grid(ids)
    return B

def vase(seed=21):
    """Tall bottle vase with eucalyptus-like branches (for tables)."""
    B = Builder(); rnd = random.Random(seed)
    cw = srgb(236, 238, 238)
    prof = [(0.0, 0.0), (0.26, 0.0), (0.30, 0.05), (0.34, 0.22), (0.33, 0.38), (0.22, 0.52), (0.12, 0.64), (0.10, 0.80), (0.115, 0.84), (0.10, 0.84), (0.075, 0.80), (0.075, 0.6)]
    seg = 16; rings = []
    for (r, z) in prof:
        rings.append([B.add(Vector((r * math.cos(2 * math.pi * s / seg), r * math.sin(2 * math.pi * s / seg), z)), cw if z < 0.8 else lerp(cw, (0.6, 0.6, 0.6), 0.2)) for s in range(seg)])
    for i in range(len(rings) - 1):
        for s in range(seg):
            n = (s + 1) % seg
            B.tri(rings[i][s], rings[i + 1][s], rings[i + 1][n]); B.tri(rings[i][s], rings[i + 1][n], rings[i][n])
    top = Vector((0, 0, 0.82))
    for i in range(7):
        ang = i * 2.39996
        out_d = Vector((math.cos(ang), math.sin(ang), 0))
        L = rnd.uniform(0.9, 1.5)
        pts = [top, top + Vector((0, 0, L * 0.45)) + out_d * L * 0.08, top + Vector((0, 0, L * 0.8)) + out_d * L * 0.28, top + Vector((0, 0, L * 0.98)) + out_d * L * 0.5]
        tube(B, pts, [0.016, 0.014, 0.012, 0.01], srgb(116, 108, 80), 4)
        for k in range(1, 4 if i % 2 else 5):
            f = k / 4.2
            q = pts[0].lerp(pts[-1], f) if False else (pts[min(int(f * 3), 2)].lerp(pts[min(int(f * 3) + 1, 3)], (f * 3) % 1))
            for sd in (-1, 1):
                ds = (out_d.cross(Z) * sd * 0.9 + out_d * 0.35 + Vector((0, 0, 0.45))).normalized()
                col = lerp(srgb(78, 120, 104), srgb(130, 168, 150), rnd.random())
                leaf(B, q, ds, 0.2, 0.095, lambda u: math.sin(math.pi * u ** 0.7) ** 0.8, 0.3, 0.1, 0.0, col, rnd, 4, 3)
        leaf(B, pts[-1], (Vector((0, 0, 1)) + out_d * 0.5).normalized(), 0.2, 0.085, lambda u: math.sin(math.pi * u ** 0.7) ** 0.8, 0.2, 0.1, 0.0, lerp(srgb(78, 120, 104), srgb(130, 168, 150), rnd.random()), rnd, 4, 3)
    return B


def add_box(B, centre, size, rotz, col_fn, bevel=0.0, cuts_y=0, cuts_z=0, tilt=0.0):
    """Beveled box (studs) appended to the builder. col_fn(local (x,y,z) normalised -1..1) -> colour."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    if cuts_y:
        edges = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 0.5]
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts_y, use_grid_fill=True)
    if cuts_z:
        edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5]
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts_z, use_grid_fill=True)
    for v in bm.verts:  # real size first so the bevel is uniform (studs)
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(size) * 0.45), segments=1, affect='EDGES')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    m = Matrix.Translation(Vector(centre)) @ Matrix.Rotation(rotz, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'X')
    idx = {}
    for v in bm.verts:
        loc = v.co.copy()
        idx[v.index] = B.add(m @ loc, col_fn((v.co.x / size[0] * 2, v.co.y / size[1] * 2, v.co.z / size[2] * 2)))
    for f in bm.faces:
        a, b, c = [idx[v.index] for v in f.verts]
        B.tri(a, b, c)
    bm.free()

COVERS = [srgb(126, 36, 40), srgb(30, 50, 96), srgb(34, 88, 62), srgb(188, 138, 60), srgb(56, 60, 68), srgb(214, 206, 188), srgb(32, 96, 110), srgb(120, 78, 120)]
PAGE = srgb(238, 232, 214); PAGE_L = srgb(206, 198, 176)

def book(B, centre, w, d, h, rotz, cover, tilt=0.0, upright=False):
    """One hardcover. Lying (upright=False): spine on the -x side. Upright: standing on the shelf, spine facing -y."""
    gold = srgb(214, 178, 96)
    if not upright:
        # cover boards top and bottom, pages between, spine at -x
        ct = h * 0.12
        add_box(B, (centre[0], centre[1], centre[2] + ct / 2), (w, d, ct), rotz, lambda p: cover, 0.012, tilt=tilt)
        add_box(B, (centre[0], centre[1], centre[2] + h - ct / 2), (w, d, ct), rotz, lambda p: lerp(cover, (1, 1, 1), 0.06), 0.012, tilt=tilt)
        add_box(B, (centre[0] + w * 0.03, centre[1], centre[2] + h / 2), (w * 0.92, d * 0.96, h - 2 * ct), rotz, lambda p: PAGE_L if int((p[2] + 1) * 7) % 2 else PAGE, 0.0, cuts_z=10, tilt=tilt)
        # spine (rounded look via a thin box) with gold bands
        add_box(B, (centre[0] - w * 0.47, centre[1], centre[2] + h / 2), (w * 0.08, d, h), rotz, lambda p: cover, 0.015, tilt=tilt)
        for zz in (0.22, 0.78):
            add_box(B, (centre[0] - w * 0.515, centre[1], centre[2] + h * zz), (w * 0.02, d * 0.9, h * 0.07), rotz, lambda p: gold, 0.0, tilt=tilt)
    else:
        th = w  # thickness along x
        ct = th * 0.12
        add_box(B, (centre[0] - th / 2 + ct / 2, centre[1], centre[2] + h / 2), (ct, d, h), rotz, lambda p: cover, 0.01)
        add_box(B, (centre[0] + th / 2 - ct / 2, centre[1], centre[2] + h / 2), (ct, d, h), rotz, lambda p: cover, 0.01)
        add_box(B, (centre[0], centre[1] + d * 0.03, centre[2] + h / 2), (th - 2 * ct, d * 0.94, h * 0.94), rotz, lambda p: PAGE_L if int((p[0] + 1) * 4) % 2 else PAGE, 0.0)
        add_box(B, (centre[0], centre[1] - d / 2 + 0.01, centre[2] + h / 2), (th, d * 0.1, h), rotz, lambda p: cover, 0.01)
        for zz in (0.2, 0.55, 0.85):
            add_box(B, (centre[0], centre[1] - d / 2 - 0.004, centre[2] + h * zz), (th * 1.0, d * 0.02, h * 0.05), rotz, lambda p: gold, 0.0)

def bookstack(seed=31):
    B = Builder(); rnd = random.Random(seed)
    z = 0.0
    for i in range(4):
        w = 0.72 - 0.05 * i + rnd.uniform(-0.03, 0.03); d = 0.98 - 0.06 * i + rnd.uniform(-0.03, 0.03); h = rnd.uniform(0.13, 0.2)
        book(B, (rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), z), w, d, h, math.radians(rnd.uniform(-14, 14)), COVERS[(i * 3 + seed) % len(COVERS)])
        z += h + 0.004
    # a small pencil on top
    add_box(B, (0.05, -0.05, z + 0.03), (0.04, 0.55, 0.04), math.radians(25), lambda p: srgb(224, 182, 70) if p[1] > -0.8 else srgb(232, 190, 160), 0.004)
    return B

def bookrow(seed=7):
    B = Builder(); rnd = random.Random(seed); x = 0.0
    for i in range(8):
        th = rnd.uniform(0.1, 0.22); h = rnd.uniform(0.85, 1.15); d = rnd.uniform(0.62, 0.78)
        book(B, (x + th / 2, 0, 0), th, d, h, 0.0, COVERS[(i * 5 + seed) % len(COVERS)], upright=True)
        x += th + 0.006
    # last book leans on its neighbour
    th = 0.16; h = 1.0
    book(B, (x + 0.2, 0, 0), th, 0.7, h, 0.0, COVERS[3], upright=True)
    return B

def openbook(seed=5):
    B = Builder(); rnd = random.Random(seed)
    cover = COVERS[1]
    add_box(B, (0, 0, 0.02), (1.5, 1.02, 0.04), 0.0, lambda p: cover, 0.015)
    for sd in (-1, 1):
        def pagecol(p, sd=sd):
            line = (int((p[1] + 1) * 13) % 3 == 0)
            return srgb(120, 116, 104) if (line and p[2] > 0.5 and abs(p[0]) > 0.05) else (PAGE if p[2] > 0.5 else PAGE_L)
        add_box(B, (sd * 0.37, 0, 0.1), (0.72, 0.94, 0.12), 0.0, pagecol, 0.006, cuts_y=26, tilt=0.0)
    add_box(B, (0, 0, 0.115), (0.06, 0.94, 0.05), 0.0, lambda p: PAGE_L, 0.0)
    add_box(B, (0.05, 0.1, 0.17), (0.02, 0.6, 0.012), math.radians(8), lambda p: srgb(190, 50, 50), 0.0)  # ribbon
    return B

def finish(B):
    v = np.array(B.v, dtype=np.float64); t = np.array(B.t, dtype=np.int64); c = np.array(B.c, dtype=np.float64)
    n = np.zeros_like(v)
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    for k in range(3): np.add.at(n, t[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True); n = n / np.maximum(ln, 1e-9)
    return v, n, c, t

def to_blender_mesh(name, v, t, c, loc):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in v], [], [tuple(f) for f in t])
    me.update()
    ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
    for i, col in enumerate(c): ca.data[i].color = (*col, 1)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.location = loc
    mat = bpy.data.materials.new(name + "M"); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = "Col"
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.inputs["Roughness"].default_value = 0.55
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(a.outputs["Color"], b.inputs["Base Color"]); nt.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    ob.data.materials.append(mat)
    for pg in me.polygons: pg.use_smooth = True
    mat.use_backface_culling = False
    return ob

def encode(v, n, c, t):
    centre = (v.min(axis=0) + v.max(axis=0)) / 2
    vr = np.stack([v[:, 0] - centre[0], v[:, 2] - centre[2], -(v[:, 1] - centre[1])], axis=1)  # Blender Z-up -> Roblox Y-up
    nr = np.stack([n[:, 0], n[:, 2], -n[:, 1]], axis=1)
    # winding preserved by the proper rotation (x, z, -y); recompute face order unchanged
    vb = b"".join(struct.pack("<hhh", *[int(round(x * 1000)) for x in p]) for p in vr)
    nb = b"".join(struct.pack("<bbb", *[int(round(x * 127)) for x in p]) for p in nr)
    cb = b"".join(struct.pack("<BBB", *[min(31, max(0, int(round(x * 31)))) for x in p]) for p in c)
    tb = b"".join(struct.pack("<HHH", *map(int, f)) for f in t)
    b64 = lambda b: base64.b64encode(b).decode()
    cen = (centre[0], centre[2], -centre[1])
    return dict(v=b64(vb), n=b64(nb), c=b64(cb), t=b64(tb), center=cen, nv=len(vr), nt=len(t))

def setup_render(path, cam_loc, target):
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.device = 'CPU'
    sc.render.resolution_x = 560; sc.render.resolution_y = 700; sc.render.filepath = str(path)
    w = bpy.data.worlds.new("w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.68, 0.72, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.1; sc.world = w
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.scene.collection.objects.link(cam)
    cam.location = cam_loc; cam.data.lens = 55
    d = Vector(target) - Vector(cam_loc); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); sc.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); sun.data.energy = 3.0; bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    fl = bpy.data.objects.new("floor", bpy.data.meshes.new("floor")); bpy.context.scene.collection.objects.link(fl)
    fl.data.from_pydata([(-9, -9, 0), (9, -9, 0), (9, 9, 0), (-9, 9, 0)], [], [(0, 1, 2, 3)])

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    species = {"fig": fig(), "lily": lily(), "monstera": monstera(), "vase": vase(), "bookstack": bookstack(), "bookrow": bookrow(), "openbook": openbook()}
    data = {}
    for name, B in species.items():
        v, n, c, t = finish(B); data[name] = encode(v, n, c, t)
        print(name, "verts", len(v), "tris", len(t))
    for i, (name, B) in enumerate(species.items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        v, n, c, t = finish(B)
        to_blender_mesh(name, v, t, c, (0, 0, 0))
        setup_render(out / f"plant_{name}.png", (0.0, -9.5, 3.2) if name in ("fig","lily","monstera") else ((0.0, -4.2, 1.4) if name == "vase" else (0.6, -3.2, 2.0)), (0, 0, 1.9) if name in ("fig","lily","monstera") else ((0, 0, 0.9) if name == "vase" else (0.4, 0, 0.45)))
        bpy.ops.render.render(write_still=True)
    # Luau data file
    lines = ["-- Generated by blender/plants_v36.py. Vertices i16*0.001 studs, normals i8, colours 5-bit sRGB, triangles u16 (base64).", "return {"]
    for name, d in data.items():
        lines.append(f'  {name}={{nv={d["nv"]},nt={d["nt"]},center=Vector3.new({d["center"][0]:.4f},{d["center"][1]:.4f},{d["center"][2]:.4f}),')
        for k in "vnct": lines.append(f'    {k}="{d[k]}",')
        lines.append("  },")
    lines.append("}")
    (out / "PlantData.luau").write_text("\n".join(lines))
    print("data bytes", (out / "PlantData.luau").stat().st_size)
main()
