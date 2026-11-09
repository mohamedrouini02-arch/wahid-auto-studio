"""Style frames for approval before the full film.
blender -b -P style.py -- OUT_DIR studio|port [W H SAMPLES]"""
import bpy, os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import world as W

args = sys.argv[sys.argv.index('--') + 1:]
OUT, FRAME = args[0], args[1]
RW, RH = (int(args[2]), int(args[3])) if len(args) > 3 else (1600, 900)
SAMPLES = int(args[4]) if len(args) > 4 else 64
random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(OUT, exist_ok=True)


def studio():
    import bmesh
    # a soft white cyclorama: floor curving up into the wall
    bm = bmesh.new(); prof = []
    for i in range(0, 21): prof.append((-30 + i * 1.5, 0))
    for i in range(1, 13):
        a = i / 12 * math.pi / 2; prof.append((0 + math.sin(a) * 7, 7 - math.cos(a) * 7))
    prof.append((7, 20))
    rows = []
    for x in (-40, 40):
        rows.append([bm.verts.new((x, y, z)) for (y, z) in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new('cyc'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('cyc', me); bpy.context.scene.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(W.mat('cyc_m', '#E8EAE8', .75))
    # turntable
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=3.6, depth=.08, location=(0, 0, .04))
    tt = bpy.context.object; tt.data.materials.append(W.mat('tt', '#D9DCD9', .35))
    for p in tt.data.polygons: p.use_smooth = True
    car = W.real('sorento', (0, 0, .08), heading=math.radians(28))
    # lights: big soft top, key from the front left, rim from behind
    def area(name, loc, rot, size, power, sy=None):
        l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = size; l.size_y = sy or size; l.energy = power
        ob = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    area('top', (0, 0, 7.5), (0, 0, 0), 9, 2600, 5)
    area('key', (6, -7, 3.2), (math.radians(68), 0, math.radians(40)), 5, 1400, 2.4)
    area('rim', (-6, 6, 3.5), (math.radians(-65), 0, math.radians(-140)), 6, 900, 1.5)
    W.sky(.35, 0)
    W.camera((7.6, -8.2, 2.1), (0, .1, .75), lens=55, dof=(0, 0, .8), fstop=5.6)
    W.render_settings(RW, RH, SAMPLES, exposure=.1)


def port():
    W.sky(1.0, math.radians(110))
    concrete = W.mat('concrete', '#BEBBB3', .85, noise=(.08, '#CFCCC4'), bump=.05)
    asphalt = W.mat('asphalt', '#55585A', .8, noise=(.15, '#63666A'), bump=.08)
    grass = W.mat('grass', '#5E7B3A', .95, noise=(.04, '#7C9450'), bump=.15)
    dirt = W.mat('dirt', '#8C7B5F', .95, noise=(.1, '#9D8C70'))
    yellow = W.mat('paint_y', '#E2B53A', .6)
    white = W.mat('paint_w', '#EDEDE8', .6)
    building = W.mat('building', '#D8D6CF', .7)
    glass = W.mat('glassband', '#2E3B40', .12)
    steel = W.mat('steel', '#3A3D3F', .5, metal=.6)
    # land: quay (concrete), container yard (asphalt), green belt with trees
    W.plane('land', -420, 0, 420, 420, -.02, grass, thick=6)
    W.plane('quay', -420, 0, 420, 62, .02, concrete)
    W.plane('yard', -260, 62, 280, 172, .03, asphalt)
    W.plane('carlot', -400, 62, -262, 172, .03, asphalt)
    W.plane('road', -420, 176, 420, 190, .03, asphalt)
    W.plane('verge', -420, 190, 420, 196, .025, dirt)
    W.box('quaywall', (840, 2.5, 8), (0, -1.25, -8), W.mat('quaywall', '#9D9A92', .9))
    for x in range(-410, 420, 12):
        W.box('dash', (6, .3, .02), (x, 183, .035), white)
    for x in (-420, 420):
        pass
    W.box('edge_line', (840, .35, .02), (0, 3, .025), yellow)
    W.box('lane1', (840, .3, .02), (0, 58, .035), yellow)
    # the ship alongside the quay
    W.place('ship', (10, -24, -9.5), heading=0)
    W.sea(-900, -700, 900, -1, z=-.8)
    # cranes along the quay, booms over the water
    for x in (-95, -15, 65):
        W.place('crane', (x, 14, 0), heading=-math.pi / 2)
    # container yard: real colours, stacked 1-3 high
    for ix in range(26):
        for iy in range(8):
            x, y = -245 + ix * 20.5, 74 + iy * 12.5
            if (ix + 3) % 9 == 0: continue                      # driving lanes
            for k in range(random.choice((1, 1, 2, 2, 3))):
                W.place('containers', (x, y, k * 5.2), heading=random.choice((0, math.pi)))
    # export car terminal: rows of new cars waiting for the ship
    for row in range(6):
        for i in range(18):
            if random.random() < .12: continue
            W.place('sorento', (-392 + i * 7.4, 72 + row * 16, .03), heading=math.pi / 2 if row % 2 else -math.pi / 2)
        W.box('bayline', (134, .2, .02), (-330, 80 + row * 16, .04), white)
    # our car on the truck, on its way to the ship
    W.real('truck', (-30, 36, .03), heading=0, name='truck')
    W.box('deck', (13.4, 2.55, .35), (-40.5, 36, 1.15), steel)
    for wx in (-45.5, -44.1, -42.7):
        for wy in (1.1, -1.1):
            bpy.ops.mesh.primitive_cylinder_add(radius=.52, depth=.38, location=(wx, 36 + wy, .52), rotation=(math.pi / 2, 0, 0))
            bpy.context.object.data.materials.append(W.mat('tyre', '#1E1F20', .8))
    W.place('sorento', (-38.5, 36, 1.5), heading=0)
    W.place('sorento', (-38.5 - 5.6, 36, 1.5), heading=0)
    # port buildings
    for (x, y, w, d, h) in [(210, 120, 46, 22, 14), (262, 118, 26, 26, 22), (-190, 214, 40, 18, 10)]:
        W.box('bld', (w, d, h), (x, y, 0), building)
        for z in range(3, h - 1, 4): W.box('win', (w + .1, d + .1, 1.2), (x, y, z), glass)
    # trees: a green belt behind the road and a few groups in the yard corners
    for i in range(170):
        x = random.uniform(-420, 420); y = random.uniform(200, 410)
        W.place('fir', (x, y, 0), heading=random.uniform(0, 6.28), scale=random.uniform(.8, 1.25))
    for i in range(30):
        x = random.uniform(-260, 280); y = random.uniform(196, 205)
        W.place('fir', (x, y, 0), heading=random.uniform(0, 6.28), scale=random.uniform(.7, 1.0))
    # emons-like view: high, from the sea, long lens, shallow focus (miniature feel)
    tgt = (-35, 40, 0)
    W.camera((-185, -255, 215), tgt, lens=60, dof=tgt, fstop=.35)
    W.render_settings(RW, RH, SAMPLES, exposure=.15)


def debug():
    # each tricky model alone, with a list of its parts (to spot strays and broken materials)
    import bpy
    from mathutils import Vector
    key = os.environ.get('J3D_KEY', 'ship')
    t = W.template(key)
    for o in t['col'].objects:
        if o.type != 'MESH': continue
        lo = Vector((1e9,) * 3); hi = -lo
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        ms = [s.material.name for s in o.material_slots if s.material]
        print('PART', o.name, 'size', tuple(round(v, 1) for v in hi - lo), 'at', tuple(round(v, 1) for v in (hi + lo) / 2), ms[:4])
    for m in {s.material for o in t['col'].objects for s in getattr(o, 'material_slots', []) if s.material}:
        b = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        if b: print('MAT', m.name, tuple(round(c, 2) for c in b.inputs['Base Color'].default_value)[:3], 'linked' if b.inputs['Base Color'].is_linked else '', 'alpha', round(b.inputs['Alpha'].default_value, 2), 'blend', m.blend_method)
    W.place(key, (0, 0, 0)); W.sky(1.0, 1.0)
    d = t['dims']; r = max(d) * .9
    W.camera((r * .9, -r * 1.3, r * .7), (0, 0, d.z * .35), lens=40)
    W.render_settings(RW, RH, SAMPLES)


{'studio': studio, 'port': port, 'debug': debug}[FRAME]()
bpy.context.scene.render.filepath = os.path.join(OUT, FRAME + '.jpg')
bpy.ops.render.render(write_still=True)
print('rendered', FRAME, flush=True)
