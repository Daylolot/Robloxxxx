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
    cb = b"".join(struct.pack("<BBB", *[min(31, max(0, int(round(math.pow(x, 1 / 2.2) * 31)))) for x in p]) for p in c)
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
    species = {"fig": fig(), "lily": lily(), "monstera": monstera()}
    data = {}
    for name, B in species.items():
        v, n, c, t = finish(B); data[name] = encode(v, n, c, t)
        print(name, "verts", len(v), "tris", len(t))
    for i, (name, B) in enumerate(species.items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        v, n, c, t = finish(B)
        to_blender_mesh(name, v, t, c, (0, 0, 0))
        setup_render(out / f"plant_{name}.png", (0.0, -9.5, 3.2), (0, 0, 1.9))
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
