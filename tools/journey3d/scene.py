"""Wahid Auto: the order-to-keys journey as one continuous 3D shot (Blender, Cycles).

A low-poly white world in the brand colours. One car goes from a dealer lot in Korea, through inspection,
onto a car-carrier truck, to the port, into a RoRo ship, across the sea, through customs in Algeria and
into the Wahid Auto showroom in Jijel. One camera follows it the whole way: there are no cuts.

blender -b -P scene.py -- OUT_DIR CAMERA(land|port) [FRAMES "a-b" or "1,2,3"] [WIDTH HEIGHT SAMPLES]
"""
import math, os, sys, random
import bpy, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/journey'
CAM = argv[1] if len(argv) > 1 else 'land'
FRAMES = argv[2] if len(argv) > 2 else '0-399'
W = int(argv[3]) if len(argv) > 3 else (1280 if CAM == 'land' else 720)
H = int(argv[4]) if len(argv) > 4 else (720 if CAM == 'land' else 1280)
SAMPLES = int(argv[5]) if len(argv) > 5 else 28
N = 400
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = scene.collection


# ---------------------------------------------------------------- materials
def hexc(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1]


_mats = {}
def M(name, col, rough=.55, metal=0., emit=0., spec=.4):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexc(col)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if emit:
        b.inputs['Emission Color'].default_value = hexc(col)
        b.inputs['Emission Strength'].default_value = emit
    _mats[name] = m
    return m


WHITE = M('white', '#F3F4F1', .6)
GROUND = M('ground', '#E6E9E5', .9, spec=.2)
PAVE = M('pave', '#D9DDD9', .85, spec=.2)
ROAD = M('road', '#C9CFCB', .8, spec=.25)
LINE = M('line', '#FBFBF9', .7)
GREEN = M('green', '#3F9C7F', .45)
GREEN2 = M('green2', '#2E7A62', .45)
MINT = M('mint', '#5FB89B', .7)
DARK = M('dark', '#1C2220', .5)
GLASS = M('glass', '#2A3634', .08, spec=.8)
GLASS_L = M('glassl', '#9DB6B1', .1, spec=.8)
TYRE = M('tyre', '#202322', .7)
RIM = M('rim', '#B9BEBB', .3, metal=.6)
HEAD = M('head', '#FFFFFF', .2, emit=3)
TAIL = M('tail', '#E0453A', .3, emit=2)
SCAN = M('scan', '#5FE0B4', .3, emit=9)
RING = M('ring', '#5FB89B', .4, emit=2.5)
TRUNK = M('trunk', '#8A6E55', .8)
RED = M('red', '#C9483A', .5)
STONE = M('stone', '#ECEEEA', .8, spec=.2)
HILL = M('hill', '#B9D6C9', .95, spec=.1)
HILL2 = M('hill2', '#CFE3DA', .95, spec=.1)
CONT = [M('c1', '#F1F2EF', .55), M('c2', '#C8CFCB', .55), M('c3', '#3F9C7F', .5), M('c4', '#2B3331', .55), M('c5', '#8FC9B3', .55)]
TREES = [M('t1', '#5FB89B', .85), M('t2', '#3F9C7F', .85), M('t3', '#7CC5AB', .85)]
CARCOL = {'white': M('car_w', '#F4F4F2', .25, spec=.6), 'silver': M('car_s', '#BFC4C2', .3, metal=.4),
          'black': M('car_k', '#1E2222', .25, spec=.6), 'grey': M('car_g', '#7A817E', .3, metal=.3),
          'blue': M('car_b', '#34465A', .3, metal=.2)}

# sea: blue with moving ripples
SEA = bpy.data.materials.new('sea'); SEA.use_nodes = True
nt = SEA.node_tree; bsdf = nt.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = hexc('#86B9C6'); bsdf.inputs['Roughness'].default_value = .12
noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 1.4; noise.inputs['Detail'].default_value = 3
mapping = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord')
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .25
nt.links.new(tc.outputs['Object'], mapping.inputs['Vector']); nt.links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
nt.links.new(noise.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
mapping.inputs['Scale'].default_value = (1, 2.2, 1)


# ---------------------------------------------------------------- geometry helpers
def _obj(name, bm, mat, loc, rot, parent, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    me.materials.append(mat)
    ob.location = loc; ob.rotation_euler = rot
    if parent: ob.parent = parent
    return ob


def box(name, size, loc, mat, bev=0.04, parent=None, rot=(0, 0, 0), base=True, taper=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        top = v.co.z > 0
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        if taper and top: v.co.x = v.co.x * taper[0] + taper[2]; v.co.y *= taper[1]
        if base: v.co.z += size[2] / 2
    ob = _obj(name, bm, mat, loc, rot, parent)
    if bev:
        m = ob.modifiers.new('bev', 'BEVEL'); m.width = bev; m.segments = 2; m.limit_method = 'ANGLE'
    return ob


def cyl(name, r, d, loc, mat, rot=(0, 0, 0), seg=24, parent=None, r2=None, smooth=True):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=d)
    return _obj(name, bm, mat, loc, rot, parent, smooth)


def ico(name, r, loc, mat, sub=1, scale=(1, 1, 1), parent=None):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts: v.co.x *= scale[0]; v.co.y *= scale[1]; v.co.z *= scale[2]
    return _obj(name, bm, mat, loc, (0, 0, 0), parent)


def text(name, body, size, loc, mat, rot=(math.radians(90), 0, 0), ext=.06, parent=None, align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = ext
    cu.align_x = align; cu.align_y = 'BOTTOM'
    ob = bpy.data.objects.new(name, cu); coll.objects.link(ob); cu.materials.append(mat)
    ob.location = loc; ob.rotation_euler = rot
    if parent: ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); coll.objects.link(e); e.location = loc; return e


# ---------------------------------------------------------------- props
def car(name, color='white', loc=(0, 0, 0), heading=0.):
    root = empty(name, loc); root.rotation_euler = (0, 0, heading)
    body = CARCOL[color]
    box(name + '_body', (4.5, 1.86, .74), (0, 0, .3), body, bev=.2, parent=root, taper=(.97, .96, 0))
    box(name + '_cabin', (2.7, 1.72, .64), (-.45, 0, 1.0), GLASS, bev=.12, parent=root, taper=(.78, .86, -.12))
    box(name + '_roof', (2.05, 1.5, .08), (-.57, 0, 1.62), body, bev=.04, parent=root)
    box(name + '_sill', (4.4, 1.9, .16), (0, 0, .3), DARK, bev=.06, parent=root)
    for sx in (1.42, -1.42):
        for sy in (.84, -.84):
            cyl(name + '_t', .37, .27, (sx, sy, .37), TYRE, rot=(math.radians(90), 0, 0), parent=root)
            cyl(name + '_r', .22, .29, (sx, sy, .37), RIM, rot=(math.radians(90), 0, 0), seg=12, parent=root)
    for sy in (.6, -.6):
        box(name + '_hl', (.06, .42, .1), (2.25, sy, .82), HEAD, bev=0, parent=root)
        box(name + '_tl', (.06, .4, .1), (-2.25, sy, .86), TAIL, bev=0, parent=root)
    return root


def tree(x, y, s=1.):
    cyl('trunk', .14 * s, 1.4 * s, (x, y, .7 * s), TRUNK, seg=6, smooth=False)
    ico('crown', 1.5 * s, (x, y, 2.4 * s), random.choice(TREES), sub=1, scale=(1, 1, 1.25))


def palm(x, y, s=1.):
    lean = random.uniform(-.12, .12)
    cyl('ptrunk', .18 * s, 5 * s, (x, y, 2.5 * s), TRUNK, rot=(lean, lean * .6, 0), seg=6, r2=.13 * s, smooth=False)
    top = Vector((x + math.sin(lean * .6) * 2.5 * s, y - math.sin(lean) * 2.5 * s, 5 * s))
    for k in range(7):
        a = k / 7 * math.tau + random.uniform(-.2, .2)
        leaf = cyl('leaf', .55 * s, 3.2 * s, top + Vector((math.cos(a) * 1.3 * s, math.sin(a) * 1.3 * s, -.2 * s)),
                   random.choice(TREES), rot=(0, math.radians(100), a), seg=4, r2=0, smooth=False)
        leaf.scale = (1, .35, 1)


def lamp(x, y):
    cyl('pole', .08, 6, (x, y, 3), DARK, seg=8)
    box('lamphead', (1.2, .3, .15), (x + .5, y, 5.95), DARK, bev=0)


def building(name, x, y, w, d, h, sign=None, glass=True, mat=WHITE, sign_mat=GREEN):
    box(name, (w, d, h), (x, y, 0), mat, bev=.08)
    if glass:
        for z in [h * .22, h * .58]:
            box(name + '_g', (w * .9, .06, h * .2), (x, y - d / 2 - .02, z), GLASS_L, bev=0)
    if sign:
        text(name + '_s', sign, min(1.6, w / (len(sign) * .62)), (x, y - d / 2 - .06, h * .82), sign_mat)


def crane(x, y):
    for dx in (-3, 3):
        for dy in (-3.5, 3.5):
            box('leg', (.6, .6, 15), (x + dx, y + dy, 0), GREEN, bev=0)
    box('beam', (7.6, 8.2, 1.2), (x, y, 15), GREEN, bev=.05)
    box('boom', (26, 1.1, .9), (x + 10, y, 16.2), WHITE, bev=.05)
    box('cab', (2, 2, 1.6), (x + 6, y, 13.4), WHITE, bev=.08)


def containers(x0, y0, cols, rows, levels):
    for i in range(cols):
        for j in range(rows):
            for k in range(random.randint(1, levels)):
                box('cont', (6, 2.4, 2.5), (x0 + i * 6.4, y0 + j * 2.7, k * 2.6), random.choice(CONT), bev=.03)


# ---------------------------------------------------------------- world
box('sea_bed', (2000, 1200, .1), (200, 0, -1.6), SEA, bev=0)
sea_plane = bpy.data.objects['sea_bed']
box('land_kr', (240, 240, 3), (66, 40, -3), GROUND, bev=0)            # Korea: x -54 .. 186
box('land_dz', (200, 240, 3), (430, 40, -3), GROUND, bev=0)           # Algeria: x 330 .. 530
box('quay_kr', (24, 60, .03), (174, 0, 0), PAVE, bev=0)
box('quay_dz', (40, 60, .03), (350, 0, 0), PAVE, bev=0)
# hills behind both coasts
for (x, y, r, m) in [(-20, 95, 26, HILL), (40, 110, 34, HILL2), (110, 100, 28, HILL), (160, 120, 30, HILL2),
                     (360, 100, 30, HILL), (420, 115, 38, HILL2), (480, 95, 28, HILL), (520, 120, 34, HILL2)]:
    ico('hill', r, (x, y, -r * .45), m, sub=2, scale=(1.4, 1, .75))

# roads (y = 0) with dashes
box('road_kr', (190, 7, .06), (90, 0, 0), ROAD, bev=0)
box('road_dz', (100, 7, .06), (382, 0, 0), ROAD, bev=0)
for x in range(-2, 186, 6):
    box('dash', (2.6, .18, .02), (x, 0, .061), LINE, bev=0)
for x in range(334, 430, 6):
    box('dash', (2.6, .18, .02), (x, 0, .061), LINE, bev=0)

# 1. dealer lot in Korea
box('lot', (34, 18, .04), (10, 13, 0), PAVE, bev=0)
for i in range(7):
    box('pline', (.15, 5, .02), (-6 + i * 4 + 2, 7.5, .041), LINE, bev=0)
    box('pline', (.15, 5, .02), (-6 + i * 4 + 2, 16.5, .041), LINE, bev=0)
box('lot_lane', (4, 2, .04), (12, 3, 0), PAVE, bev=0)
cols = ['silver', 'black', 'grey', None, 'blue', 'white', 'silver']
for i, c in enumerate(cols):
    if c: car('p%d' % i, c, (-4 + i * 4 + 2, 7.5, .05), -math.pi / 2)
for i, c in enumerate(['white', 'grey', 'black', 'silver', 'white', 'blue']):
    car('q%d' % i, c, (-4 + i * 4 + 2, 16.5, .05), math.pi / 2)
building('dealer', 10, 28, 30, 8, 7, 'KOREA')
lamp(-8, 3); lamp(28, 3)

# 2. inspection bay
box('bay_floor', (11, 8, .075), (34, 0, 0), M('bayfloor', '#DCEDE6', .7), bev=0)
for dx in (-5.3, 5.3):
    for dy in (-3.8, 3.8):
        box('bay_post', (.4, .4, 4.6), (34 + dx, dy, 0), WHITE, bev=.05)
box('bay_roof', (11.6, 8.4, .5), (34, 0, 4.6), WHITE, bev=.08)
text('bay_sign', 'INSPECTION', .9, (34, -4.25, 4.66), GREEN)
scanner = empty('scanner', (30, 0, 0))
box('scan_bar_l', (.18, .18, 4.2), (0, -3.4, 0), SCAN, bev=0, parent=scanner)
box('scan_bar_r', (.18, .18, 4.2), (0, 3.4, 0), SCAN, bev=0, parent=scanner)
box('scan_bar_t', (.18, 7, .18), (0, 0, 4.2), SCAN, bev=0, parent=scanner)

# 3. export office and the truck
building('office', 50, 13, 12, 8, 6, 'EXPORT')
truck = empty('truck', (63, 0, 0))
box('trailer', (13, 2.5, .3), (-1, 0, 1.0), DARK, bev=.04, parent=truck)
box('trailer_rail', (13, .12, .5), (-1, 1.2, 1.3), GREEN, bev=0, parent=truck)
box('trailer_rail2', (13, .12, .5), (-1, -1.2, 1.3), GREEN, bev=0, parent=truck)
box('cab', (2.6, 2.5, 2.7), (6.8, 0, .6), GREEN2, bev=.2, parent=truck)
box('cab_glass', (.1, 2.2, .9), (8.12, 0, 2.2), GLASS, bev=0, parent=truck)
for wx in (-6, -4.8, 3.2, 7.2):
    for wy in (1.05, -1.05):
        cyl('tw', .5, .4, (wx, wy, .5), TYRE, rot=(math.radians(90), 0, 0), parent=truck)

# road trees
for x in range(60, 186, 9):
    for side in (-1, 1):
        if 44 < x < 58 and side == 1: continue
        tree(x + random.uniform(-2, 2), side * random.uniform(7.5, 11), random.uniform(.85, 1.15))
for x in range(-30, 30, 7):
    tree(x + random.uniform(-2, 2), -random.uniform(7, 10), random.uniform(.8, 1.1))
for x in range(-10, 60, 8):
    tree(x + random.uniform(-2, 2), random.uniform(36, 44), random.uniform(.9, 1.2))

# 4. port in Korea
crane(176, 12); crane(162, -13)
containers(140, 16, 5, 4, 3)
containers(128, -24, 4, 3, 2)
building('port_office', 150, -12, 8, 6, 5, 'INCHEON')

# 5. the ship (stern at its origin, bow at +40)
ship = empty('ship', (186.4, 0, 0))
box('hull_low', (40, 9.2, 3.2), (20, 0, -4), DARK, bev=.15, parent=ship)
box('hull_stripe', (40, 9.3, .35), (20, 0, -.85), GREEN, bev=0, parent=ship)
box('hull', (40, 9, 10.5), (20, 0, -.5), WHITE, bev=.25, parent=ship)
box('bridge', (4.5, 9.4, 1.8), (33, 0, 10), WHITE, bev=.12, parent=ship)
box('bridge_g', (4.6, 9.5, .6), (33, 0, 10.7), GLASS, bev=0, parent=ship)
box('funnel', (2.2, 1.8, 2.6), (6, 0, 10), GREEN, bev=.1, parent=ship)
text('ship_name', 'WAHID AUTO', 2.4, (20, -4.56, 3.4), GREEN, parent=ship)
for i in range(9):
    box('port_win', (.9, .06, .5), (6 + i * 3.6, -4.53, 7.6), GLASS, bev=0, parent=ship)
stern_ramp = empty('stern_ramp', (0, 0, 1.2)); stern_ramp.parent = ship
box('sramp', (8.4, 4.4, .25), (-4.2, 0, -.12), PAVE, bev=.04, parent=stern_ramp)
bow_ramp = empty('bow_ramp', (40, 0, 1.2)); bow_ramp.parent = ship
box('bramp', (8.4, 4.4, .25), (4.2, 0, -.12), PAVE, bev=.04, parent=bow_ramp)

# 6. Algeria: port, customs, Jijel showroom
crane(338, 14)
containers(352, 14, 4, 3, 2)
box('booth', (3.4, 3, 3), (356, -6.2, 0), WHITE, bev=.1)
box('booth_roof', (4.2, 3.8, .4), (356, -6.2, 3), GREEN, bev=.06)
box('booth_g', (3, .06, 1.1), (356, -7.72, 1.4), GLASS_L, bev=0)
text('douane', 'DOUANE', .75, (356, -8.2, 3.5), GREEN)
barrier = empty('barrier', (359, -4.2, 1.05))
for i in range(7):
    box('arm', (.22, 1, .22), (0, .5 + i, 0), RED if i % 2 == 0 else WHITE, bev=0, parent=barrier, base=False)
box('barrier_post', (.5, .5, 1.1), (359, -4.2, 0), DARK, bev=.04)
box('plaza', (40, 26, .045), (402, 12.5, 0), STONE, bev=0)
box('showroom', (30, 14, 8.5), (402, 18, 0), WHITE, bev=.12)
box('show_glass', (27, .1, 6), (402, 10.96, .6), GLASS_L, bev=0)
for i in range(6):
    box('mullion', (.25, .2, 6.2), (389 + i * 5.2, 10.9, .5), WHITE, bev=0)
box('show_band', (30.4, 14.4, 1.4), (402, 18, 7.4), GREEN, bev=.08)
text('show_sign', 'WAHID AUTO', 1.15, (402, 10.7, 7.62), M('signw', '#FFFFFF', .4, emit=.6))
car('d1', 'black', (394, 15, .05), -math.pi / 2 + .5)
car('d2', 'silver', (410, 15, .05), -math.pi / 2 - .5)
for (x, y) in [(384, -9), (420, -9), (382, 4), (422, 4), (340, -12), (372, -10)]:
    palm(x, y, random.uniform(.9, 1.15))
for x in range(430, 470, 8):
    tree(x, random.uniform(-10, 30), 1.1)
lamp(370, -5); lamp(392, -5); lamp(412, -5)

# ---------------------------------------------------------------- the hero car + ring
hero = car('hero', 'white', (12, 7.5, .05), -math.pi / 2)
ring = bpy.data.objects.new('ring', bpy.data.meshes.new('ring')); coll.objects.link(ring)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, segments=64, radius=3.2)
e = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:])
for v in [x for x in e['geom'] if isinstance(x, bmesh.types.BMVert)]: v.co *= .9
bm.to_mesh(ring.data); bm.free(); ring.data.materials.append(RING)


# ---------------------------------------------------------------- choreography
def ease(t): t = max(0., min(1., t)); return t * t * t * (t * (t * 6 - 15) + 10)


def path(segs, f, start):
    """segs: (f0, f1, p0, p1, ctrl or None, reverse). Returns position (x,y,z) and heading."""
    pos, hd = Vector(start[0]), start[1]
    for (f0, f1, p0, p1, c, rev) in segs:
        if f < f0: break
        t = ease((f - f0) / (f1 - f0)) if f1 > f0 else 1
        p0, p1 = Vector(p0), Vector(p1)
        if c is None:
            pos = p0.lerp(p1, t); d = p1 - p0
        else:
            c = Vector(c); pos = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t * t * p1
            d = 2 * (1 - t) * (c - p0) + 2 * t * (p1 - c)
        if d.xy.length > 1e-4:
            hd = math.atan2(d.y, d.x) + (math.pi if rev else 0)
    return pos, hd


Z = .05
CAR_SEGS = [
    (40, 64, (12, 7.5, Z), (24, 0, Z), (12, 0, Z), False),        # out of the lot onto the road
    (64, 76, (24, 0, Z), (34, 0, Z), None, False),               # into the inspection bay
    (98, 118, (34, 0, Z), (55, 0, Z), None, False),              # towards the export office / truck
    (118, 128, (55, 0, Z), (62, 0, 1.35), None, False),          # up onto the trailer
    (132, 172, (62, 0, 1.35), (152, 0, 1.35), None, False),      # on the truck to the port
    (178, 190, (152, 0, 1.35), (138, 0, Z), None, True),         # reverses off the trailer
    (206, 222, (138, 0, Z), (178, 0, Z), None, False),           # to the stern ramp
    (222, 232, (178, 0, Z), (186.4, 0, 1.2), None, False),       # up the ramp
    (232, 240, (186.4, 0, 1.2), (196, 0, 1.2), None, False),     # inside the ship
]
TRUCK_SEGS = [
    (132, 172, (63, 0, 0), (153, 0, 0), None, False),
    (192, 214, (153, 0, 0), (168, 24, 0), (168, 0, 0), False),   # leaves for the next job
]
SHIP_X0, SHIP_X1 = 186.4, 289.6
def ship_x(f): return SHIP_X0 + (SHIP_X1 - SHIP_X0) * ease((f - 248) / 60)
def stern_angle(f):
    down, up = math.radians(-8.5), math.radians(82)
    if f < 238: return down
    return down + (up - down) * ease((f - 238) / 10)
def bow_angle(f):
    down, up = math.radians(8.5), math.radians(-82)
    return up + (down - up) * ease((f - 306) / 10)
DZ_SEGS = [
    (316, 326, (329.6, 0, 1.2), (338, 0, Z), None, False),       # down the bow ramp
    (326, 338, (338, 0, Z), (352, 0, Z), None, False),           # to customs
    (348, 366, (352, 0, Z), (384, 0, Z), None, False),           # through the barrier
    (366, 392, (384, 0, Z), (402, -7, Z), (402, 0, Z), False),   # turns onto the showroom forecourt
]


def car_state(f):
    if f < 314:
        return path(CAR_SEGS, f, ((12, 7.5, Z), -math.pi / 2))
    return path(DZ_SEGS, f, ((329.6, 0, 1.2), 0.))


def car_visible(f): return not (240 <= f < 316)


# camera: follows a smoothed focus, distance changes per chapter
DIST = [(0, 64), (34, 30), (60, 26), (96, 28), (130, 34), (176, 40), (214, 50), (250, 66), (300, 56),
        (320, 36), (356, 32), (372, 34), (400, 44)]
def dist(f):
    for (a, da), (b, db) in zip(DIST, DIST[1:]):
        if a <= f <= b: return da + (db - da) * ease((f - a) / (b - a))
    return DIST[-1][1]


raw = []
for f in range(N):
    if car_visible(f):
        p, _ = car_state(f)
    else:
        p = Vector((ship_x(f) + 20, 0, 3))
    q = Vector((p.x, p.y, max(p.z, 0) + 1))
    k = ease((f - 360) / 30)
    raw.append(q.lerp(Vector((402, 3, 3.2)), k * .85))
focus = []
SIG = 9
for f in range(N):
    acc, wsum = Vector((0, 0, 0)), 0
    for k in range(-3 * SIG, 3 * SIG + 1):
        g = math.exp(-k * k / (2 * SIG * SIG)); acc += raw[min(N - 1, max(0, f + k))] * g; wsum += g
    focus.append(acc / wsum)

DIR = Vector((-.32, -1.0, .66)).normalized()
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 35 if CAM == 'land' else 30
cam_data.sensor_fit = 'HORIZONTAL' if CAM == 'land' else 'VERTICAL'
cam_data.shift_y = .04 if CAM == 'land' else .12
cam = bpy.data.objects.new('cam', cam_data); coll.objects.link(cam); scene.camera = cam
target = empty('target')
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = target; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
CAM_MUL = 1.0 if CAM == 'land' else 1.35

for f in range(N):
    scene.frame_set(f)
    p, hd = car_state(f)
    hero.location = p; hero.rotation_euler = (0, 0, hd)
    hero.keyframe_insert('location', frame=f); hero.keyframe_insert('rotation_euler', frame=f)
    vis = car_visible(f)
    for ob in [hero] + list(hero.children):
        ob.hide_render = not vis; ob.keyframe_insert('hide_render', frame=f)
    tp, thd = path(TRUCK_SEGS, f, ((63, 0, 0), 0.))
    truck.location = tp; truck.rotation_euler = (0, 0, thd)
    truck.keyframe_insert('location', frame=f); truck.keyframe_insert('rotation_euler', frame=f)
    ship.location = (ship_x(f), 0, -.15 + .12 * math.sin(f * .21) * (1 if 244 < f < 312 else 0))
    ship.keyframe_insert('location', frame=f)
    stern_ramp.rotation_euler = (0, stern_angle(f), 0); stern_ramp.keyframe_insert('rotation_euler', frame=f)
    bow_ramp.rotation_euler = (0, bow_angle(f), 0); bow_ramp.keyframe_insert('rotation_euler', frame=f)
    sc = 0 if f < 76 or f > 96 else (f - 76) / 20
    scanner.location = (29.5 + 9 * (1 - abs(1 - 2 * ((sc * 2) % 1))) if 76 <= f <= 96 else 29.5, 0, 0)
    scanner.keyframe_insert('location', frame=f)
    for ob in [scanner] + list(scanner.children):
        ob.hide_render = not (74 <= f <= 98); ob.keyframe_insert('hide_render', frame=f)
    barrier.rotation_euler = (math.radians(80) * (ease((f - 338) / 9) if f < 366 else 1 - ease((f - 366) / 10)), 0, 0)
    barrier.keyframe_insert('rotation_euler', frame=f)
    pulse = 1 + .08 * math.sin(f * .25)
    ring.location = (12, 7.5, .08); ring.scale = (pulse, pulse, 1)
    ring.hide_render = f > 44; ring.keyframe_insert('scale', frame=f); ring.keyframe_insert('hide_render', frame=f)
    mapping.inputs['Location'].default_value = (f * .03, f * .012, f * .02)
    mapping.inputs['Location'].keyframe_insert('default_value', frame=f)
    fo = focus[f]; d = dist(f) * CAM_MUL
    target.location = fo; target.keyframe_insert('location', frame=f)
    cam.location = fo + DIR * d; cam.keyframe_insert('location', frame=f)

for fc_owner in bpy.data.actions:
    for fc in fc_owner.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------- light, render
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = hexc('#E9EFED')
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); coll.objects.link(sun)
sun.data.energy = 4.2; sun.data.angle = math.radians(4); sun.rotation_euler = (math.radians(42), math.radians(8), math.radians(-35))

r = scene.render
r.engine = 'CYCLES'; scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = .03
scene.cycles.max_bounces = 4; scene.cycles.diffuse_bounces = 2; scene.cycles.glossy_bounces = 2; scene.cycles.transmission_bounces = 2
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = .3
r.image_settings.file_format = 'JPEG'; r.image_settings.quality = 93
os.makedirs(OUT, exist_ok=True)

if '-' in FRAMES:
    a, b = map(int, FRAMES.split('-')); frames = range(a, b + 1)
else:
    frames = [int(x) for x in FRAMES.split(',')]
for f in frames:
    scene.frame_set(f)
    r.filepath = os.path.join(OUT, '%04d.jpg' % f)
    bpy.ops.render.render(write_still=True)
    print('rendered', f, flush=True)
