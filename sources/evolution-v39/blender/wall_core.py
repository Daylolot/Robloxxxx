"""Wall decor core for wall_hero.py (exec'd): helpers in Roblox-local wall coordinates and a wall-backdrop renderer.
Item frame: origin = centre of the item ON the wall plane; x right-hand of the wall's own frame (viewer's right = -x), y up, wall plane z = 0, the item
sticks out toward the viewer (negative z = front). The game places an item with CFrame.lookAt(wallPoint, wallPoint + wallNormal) so -Z faces the room."""
import math, random

MATS.update({
    "stain": ("#aaaaaa", .96, 0, 0, 0),
    "plastic": ("#ffffff", .36, 0, 0, 0),
    "glow": ("#7fe0c0", .4, 0, 3.2, 0),
    "copper": ("#b8693a", .28, .9, 0, 0),
    "brick": ("#a85f4a", .9, 0, 0, 0),
    "tint": ("#e1e2d3", .95, 0, 0, 0),      # recoloured by the game to the colour of the wall it hangs on (flakes, filler)
    "plaster": ("#e1e2d3", .95, 0, 0, 0),
    "dark": ("#15181a", .5, 0, 0, 0),
})

_RP = [0]
FLAT_GROUPS = set()   # (material, colour) groups made of flat decals: shaded flat
_CM = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # Roblox (x, y, z) -> Blender (-x, z, y)


def P(x, y, z):
    return (-x, z, y)


def RR(axis, angle):
    """Rotation about a ROBLOX axis ('X', 'Y' or 'Z'), as a Blender matrix."""
    return _CM @ Matrix.Rotation(angle, 4, axis) @ _CM.inverted()


def rbc(it, mat, w, h, d, x, y, z, rot=None, bevel=0.0, seg=2, color=None):
    """Box centred at (x, y, z), rotated about its OWN centre by `rot` (an RR matrix)."""
    M = T(-x, z, y) if rot is None else T(-x, z, y) @ rot
    it.put(_cube(w, d, h, bevel, seg), mat, color, M)


def rpost(it, mat, r, y0, y1, x, z, seg=18, color=None, bevel=0.0):
    """Vertical cylinder (axis along Roblox y) from y0 to y1 at (x, z)."""
    cyl(it, mat, r, y1 - y0, (-x, z, y0), seg=seg, color=color, bevel=bevel)


def rdisc(it, mat, r, x, y, zback, thick, color=None, bevel=0.0, r2=None, seg=36):
    """Disc whose axis is Roblox z: from z=zback towards the viewer by `thick`."""
    cyl(it, mat, r, thick, (-x, zback, y), seg=seg, color=color, rot=Rx(math.pi / 2), bevel=bevel, r2=r2)


def rpipex(it, mat, r, x0, x1, y, z, color=None, seg=20, bevel=0.0):
    if x1 < x0:
        x0, x1 = x1, x0
    cyl(it, mat, r, x1 - x0, (-x0, z, y), seg=seg, color=color, rot=Ry(-math.pi / 2), bevel=bevel)


def rcyl(it, mat, r, p0, p1, color=None, seg=20, r2=None, bevel=0.0):
    """Cylinder from Roblox point p0 to p1 (any direction); r2 = radius at p1 for a cone."""
    a, b = Vector(P(*p0)), Vector(P(*p1))
    d = b - a
    if d.length < 1e-6:
        return
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    cyl(it, mat, r, d.length, tuple(a), seg=seg, r2=r2, color=color, rot=rot, bevel=bevel)


def rot_to(fwd):
    """Blender rotation matrix taking the item's front axis (Roblox -z) to the Roblox direction `fwd`."""
    return Vector((0, -1, 0)).rotation_difference(Vector(P(*fwd)).normalized()).to_matrix().to_4x4()


def rtube(it, mat, pts, radii, sides=14, color=None, squash=(1.0, 1.0), caps=True):
    tube(it, mat, [P(*p) for p in pts], radii, sides, color, squash, caps)


def _ear_clip(pts):
    """Triangulate a simple polygon [(x, y)] -> list of index triples (counter-clockwise in x, y). Always returns len(pts) - 2 triangles."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    idx = list(range(n)) if area > 0 else list(range(n))[::-1]
    tris = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    while len(idx) > 3:
        m = len(idx)
        best = None
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = pts[i0], pts[i1], pts[i2]
            cr = cross(a, b, c)
            if cr <= 0:
                continue
            inside = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = pts[j]
                if cross(a, b, p) > 1e-12 and cross(b, c, p) > 1e-12 and cross(c, a, p) > 1e-12:
                    inside = True
                    break
            if not inside:
                best = k
                break
        if best is None:      # degenerate input: cut the sharpest convex corner anyway so no area is lost
            best = max(range(m), key=lambda k: cross(pts[idx[k - 1]], pts[idx[k]], pts[idx[(k + 1) % m]]))
        tris.append((idx[best - 1], idx[best], idx[(best + 1) % m]))
        idx.pop(best)
    tris.append(tuple(idx))
    return tris


def rpoly(it, mat, pts, z, thick, color=None, bevel=0.0):
    """Flat prism: polygon `pts` [(x, y)] on the plane z (back face), extruded toward the viewer by `thick`. Own ear-clipping keeps the winding
    right for concave outlines (Roblox draws single-sided faces)."""
    pts = [(float(x), float(y)) for x, y in pts]
    _RP[0] += 1
    z -= (_RP[0] % 17) * 0.00011        # never exactly coplanar with another decal layer (two coplanar prisms render black in Cycles)
    # drop duplicate neighbours
    clean = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-4:
            clean.append(p)
    pts = clean
    if len(pts) < 3:
        return
    bm = bmesh.new()
    back = [bm.verts.new(P(x, y, z)) for x, y in pts]
    front = [bm.verts.new(P(x, y, z - thick)) for x, y in pts]
    n = len(pts)
    tris = _ear_clip(pts)
    # orientation: the front face must look toward -Y (Blender)
    a, b, c = (Vector(front[i].co) for i in tris[0])
    flip = ((b - a).cross(c - a)).y > 0
    for i0, i1, i2 in tris:
        if flip:
            bm.faces.new((front[i0], front[i2], front[i1])); bm.faces.new((back[i0], back[i1], back[i2]))
        else:
            bm.faces.new((front[i0], front[i1], front[i2])); bm.faces.new((back[i0], back[i2], back[i1]))
    for i in range(n):
        j = (i + 1) % n
        q = (back[i], back[j], front[j], front[i])
        try:
            bm.faces.new(q if flip else q[::-1])
        except ValueError:
            pass
    bm.verts.index_update(); bm.faces.index_update(); bm.normal_update()
    FLAT_GROUPS.add((mat, (color or MATS[mat][0]).lstrip("#").lower()))
    it.put(bm, mat, color)


def rring(it, mat, outer, inner, z, thick, color=None):
    """Closed ribbon between two outlines with the same number of points (a ring/stroke around a shape)."""
    n = len(outer)
    bm = bmesh.new()
    ob = [bm.verts.new(P(x, y, z - thick)) for x, y in outer]
    ib = [bm.verts.new(P(x, y, z - thick)) for x, y in inner]
    ob2 = [bm.verts.new(P(x, y, z)) for x, y in outer]
    ib2 = [bm.verts.new(P(x, y, z)) for x, y in inner]
    a, b, d = Vector(ob[0].co), Vector(ob[1].co), Vector(ib[0].co)
    flip = ((b - a).cross(d - a)).y > 0
    for i in range(n):
        j = (i + 1) % n
        q = (ob[i], ob[j], ib[j], ib[i])
        bm.faces.new(q[::-1] if flip else q)
        q2 = (ob2[i], ob2[j], ib2[j], ib2[i])
        bm.faces.new(q2 if flip else q2[::-1])
    bm.verts.index_update(); bm.faces.index_update(); bm.normal_update()
    FLAT_GROUPS.add((mat, (color or MATS[mat][0]).lstrip("#").lower()))
    it.put(bm, mat, color)


def clip_top(pts, top):
    """Clamp a polygon to y <= top, collapsing runs of clamped points to their end points (no collinear runs for the ear clipper)."""
    out = []
    run = []
    for p in pts + [pts[0]]:
        if p[1] > top:
            run.append((p[0], top))
        else:
            if run:
                out.append(run[0])
                if len(run) > 1:
                    out.append(run[-1])
                run = []
            out.append(p)
    return out[:-1] if out and out[-1] == pts[0] else out


def blob_pts(cx, cy, rx, ry, rng, n=40, noise=0.2, harmonics=4, flat=None):
    """Smooth organic outline. flat='top' cuts the top at cy+ry (stain hanging from the ceiling)."""
    ph = [rng.uniform(0, math.tau) for _ in range(harmonics)]
    am = [noise / (k + 1) * rng.uniform(0.6, 1.2) for k in range(harmonics)]
    pts = []
    for i in range(n):
        a = i / n * math.tau
        r = 1 + sum(am[k] * math.sin((k + 2) * a + ph[k]) for k in range(harmonics))
        x, y = cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r
        if flat == "top":
            y = min(y, cy + ry)
        pts.append((x, y))
    return pts


def streak_pts(x, ytop, length, w0, w1, rng, wob=0.12, n=18):
    """Drip streak hanging from (x, ytop): width grows from w0 to w1, wobbling edges, rounded tip."""
    left, right = [], []
    off = 0.0
    for i in range(n + 1):
        t = i / n
        w = (w0 + (w1 - w0) * (t ** 0.8)) * (1 + rng.uniform(-wob, wob))
        off += rng.uniform(-0.04, 0.04)
        y = ytop - length * t
        left.append((x + off - w / 2, y)); right.append((x + off + w / 2, y))
    wl = w1 / 2
    tip = [(x + off + math.cos(math.pi - k / 6 * math.pi) * wl, ytop - length - math.sin(k / 6 * math.pi) * wl * 1.1) for k in range(1, 6)]
    return left + tip + right[::-1]


def ribbon_pts(path, widths):
    left, right = [], []
    n = len(path)
    for i, (x, y) in enumerate(path):
        a = path[max(i - 1, 0)]; b = path[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / l, dx / l
        w = widths[i] / 2
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def crack_path(start, ang, length, rng, step=0.35, wander=0.35, curve=0.0):
    pts = [start]
    x, y = start
    a = ang
    d = 0.0
    while d < length:
        a += rng.uniform(-wander, wander) + curve
        s = step * rng.uniform(0.6, 1.4)
        x += math.cos(a) * s; y += math.sin(a) * s
        pts.append((x, y)); d += s
    return pts


def draw_crack(it, path, w0, z, dark="#2e2c29", dust="#c4bfae", thick=0.012):
    n = len(path)
    ws = [w0 * (1 - 0.8 * (i / max(n - 1, 1)) ** 1.2) + 0.012 for i in range(n)]
    rpoly(it, "stain", ribbon_pts(path, [w * 3.2 + 0.03 for w in ws]), z, thick, dust)
    rpoly(it, "stain", ribbon_pts(path, ws), z - thick, thick, dark)


def view_setup(name, objs, mounted_y=0.0):
    pass


def render_wall(sc, name, objs, views):
    """Render `views` = [(azimuth deg, elevation deg)] with a plaster wall behind the item (plane at Blender y = 0)."""
    mins = Vector((1e9, 1e9, 1e9)); maxs = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        for v in ob.bound_box:
            w = ob.matrix_world @ Vector(v)
            mins = Vector(map(min, mins, w)); maxs = Vector(map(max, maxs, w))
    center = (mins + maxs) / 2; size = maxs - mins
    span = max(size.x, size.z) + 0.8
    span = max(span, 3.0)
    # wall
    wall = bpy.data.meshes.new("wall"); bm = bmesh.new()
    s = span * 3.0
    vs = [bm.verts.new(p) for p in [(-s, 0.0, -s), (s, 0.0, -s), (s, 0.0, s), (-s, 0.0, s)]]
    bm.faces.new(vs[::-1]); bm.to_mesh(wall); bm.free()
    wo = bpy.data.objects.new("wall", wall); sc.collection.objects.link(wo)
    wm = bpy.data.materials.new("wallm"); wm.use_nodes = True
    wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = hexc("#e1e2d3")
    wm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    wo.data.materials.append(wm)
    # lights: warm ceiling light from above-front, cool fill from the side
    for lname, pos, energy, col in (("key", (center.x + span * 0.6, -span * 1.6, center.z + span * 1.9), 124 * span * span, (1, .94, .84)),
                                    ("fill", (center.x - span * 1.8, -span * 1.2, center.z + span * 0.3), 52 * span * span, (.8, .88, 1))):
        ld = bpy.data.lights.new(lname, "AREA"); ld.energy = energy; ld.size = span * 1.6; ld.color = col
        lo = bpy.data.objects.new(lname, ld); lo.location = pos; sc.collection.objects.link(lo)
        lo.rotation_euler = (Vector((center.x, 0, center.z)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 46
    cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 520, 400
    dist = max(size.x / 1.05, size.z / 0.8) * 1.2 + 3.5
    (OUT / "previews").mkdir(exist_ok=True)
    for k, v in enumerate(views):
        if len(v) == 6:                                   # detail view: (azimuth, elevation, target x, y, z in Roblox coords, distance)
            az, el, tx, ty, tz, dd = v
            tgt = Vector(P(tx, ty, tz)); dist_k = dd
            sc.render.resolution_x, sc.render.resolution_y = 780, 600
        else:
            az, el = v; tgt = center; dist_k = dist
        a, e = math.radians(az) - math.pi / 2, math.radians(el)
        cam.location = tgt + Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * dist_k
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(OUT / "previews" / f"{name}_w{k}.png")
        bpy.ops.render.render(write_still=True)


def flatten_decals(objs):
    """Flat shading for the decal groups (stains, cracks): smooth shading across a 0.008 thick prism only smears the colours."""
    for ob in objs:
        key = tuple(ob.name.split("_", 1)[1].rsplit("_", 1))
        if key in FLAT_GROUPS or key[0] in ("stain",):
            for p in ob.data.polygons:
                p.use_smooth = False
