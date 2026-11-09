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
    prof.append((7, 40))
    rows = []
    for x in (-90, 90):
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
    car = W.real('sorento', (0, 0, .08), heading=math.radians(-12))
    # lights: big soft top, key from the front left, rim from behind
    def area(name, loc, rot, size, power, sy=None):
        l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = size; l.size_y = sy or size; l.energy = power
        ob = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    area('top', (0, 0, 7.5), (0, 0, 0), 9, 2600, 5)
    area('key', (6, -7, 3.2), (math.radians(68), 0, math.radians(40)), 5, 1400, 2.4)
    area('rim', (-6, 6, 3.5), (math.radians(-65), 0, math.radians(-140)), 6, 900, 1.5)
    W.sky(.35, 0)
    W.camera((6.4, -9.4, 2.3), (0, .2, .8), lens=50, dof=(0, 0, .8), fstop=5.6)
    W.render_settings(RW, RH, SAMPLES, exposure=.1)


def pctc(x, y, z=0., heading=0.):
    """A pure car and truck carrier (the ships that bring cars from Korea): one long white box on a dark hull."""
    import bmesh
    L, B = 199., 32.
    root = bpy.data.objects.new('ship', None); bpy.context.scene.collection.objects.link(root)
    def hull(name, z0, z1, m, inset=0., bow=1.):
        bm = bmesh.new(); pts = []
        for i in range(13):                       # rounded, blunt bow
            a = -math.pi / 2 + i / 12 * math.pi
            pts.append((L / 2 - 18 + math.cos(a) * 18 * bow - inset, math.sin(a) * (B / 2 - inset)))
        pts += [(-L / 2 + inset + 2, B / 2 - inset), (-L / 2 + inset, B / 2 - inset - 2), (-L / 2 + inset, -B / 2 + inset + 2), (-L / 2 + inset + 2, -B / 2 + inset)]
        bot = [bm.verts.new((px, py, z0)) for px, py in pts]; top = [bm.verts.new((px, py, z1)) for px, py in pts]
        n = len(pts)
        for i in range(n): bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
        bm.faces.new(top); bm.faces.new(list(reversed(bot)))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(m); o.parent = root
        bev = o.modifiers.new('b', 'BEVEL'); bev.width = .6; bev.segments = 3; bev.limit_method = 'ANGLE'
        return o
    red = W.mat('antifoul', '#7E2B26', .7); navy = W.mat('hullnavy', '#1F2A33', .45, noise=(.05, '#26323C'))
    white = W.mat('shipwhite', '#ECEDEA', .5, noise=(.03, '#E2E4E0')); green = W.mat('shipgreen', '#2E7A62', .45)
    deck = W.mat('shipdeck', '#8A8E8A', .8); dark = W.mat('shipdark', '#2B3034', .3)
    hull('h_red', -9, -1.5, red, bow=.98); hull('h_navy', -1.5, 7, navy); hull('h_band', 7, 8.2, green, inset=.05)
    hull('h_box', 8.2, 31, white, inset=.4); hull('h_top', 31, 31.6, deck, inset=.9)
    def part(name, size, loc, m):
        o = W.box(name, size, loc, m); o.parent = root; return o
    # bridge across the front, windows all round
    part('bridge', (12, 30, 4.2), (L / 2 - 32, 0, 31.6), white)
    part('bridge_win', (12.2, 30.2, 1.4), (L / 2 - 32, 0, 33.6), dark)
    part('wing', (4, 36, .5), (L / 2 - 30, 0, 35.2), white)
    # funnel aft, in the brand green
    part('funnel', (8, 5, 8), (-L / 2 + 22, 0, 31.6), white)
    part('funnel_top', (8.1, 5.1, 2.2), (-L / 2 + 22, 0, 37.4), green)
    # stern ramp, lifeboat, deck rails, rows of vents on the side
    rp = part('ramp', (7, 16, .5), (-L / 2 + 12, B / 2 + 6.5, 1.0), deck); rp.rotation_euler = (math.radians(7), 0, 0)
    part('lifeboat', (9, 3, 3), (-L / 2 + 10, -B / 2 - 1.5, 26), W.mat('lifeboat', '#E4632A', .5))
    for i in range(22):
        part('vent', (2.4, .25, 1.6), (-L / 2 + 16 + i * 7.6, -B / 2 + .25, 26.5), W.mat('vent', '#B9BCB8', .6))
    root.location = (x, y, z); root.rotation_euler = (0, 0, heading)
    return root


def sts_crane(x, y, heading=0., colour='#5C8FB8'):
    """Ship-to-shore gantry crane: four legs on the quay, boom out over the ship."""
    root = bpy.data.objects.new('sts', None); bpy.context.scene.collection.objects.link(root)
    m = W.mat('sts_' + colour, colour, .45, noise=(.2, colour)); w = W.mat('sts_w', '#E9EAE6', .5)
    def b(size, loc, mm=m, rot=(0, 0, 0)):
        o = W.box('sts', size, loc, mm); o.parent = root; o.rotation_euler = rot; return o
    for lx in (-8, 8):
        for ly in (6, 36):
            b((1.6, 1.6, 44), (lx, ly, 0))
        b((1.4, 30, 1.4), (lx, 21, 44))
        b((1.2, 30, 1.2), (lx, 21, 14))
        b((1.0, 1.0, 34), (lx, 21, 12), rot=(math.radians(41), 0, 0))
    for ly in (6, 36):
        b((17.6, 1.4, 1.4), (0, ly, 44)); b((17.6, 1.2, 1.2), (0, ly, 30))
        b((2.6, 3.4, 1.8), (-8, ly, 0), w); b((2.6, 3.4, 1.8), (8, ly, 0), w)
    b((5, 118, 3.2), (0, -14, 47))                      # boom over the water and back
    b((12, 14, 7), (0, 30, 47.5), w)                    # machinery house
    b((3, 6, 2.6), (0, -6, 44.4), w)                    # trolley and cab
    b((1, 1, 22), (0, 30, 50), rot=(math.radians(-52), 0, 0)); b((1, 1, 22), (0, 10, 50), rot=(math.radians(52), 0, 0))
    b((2, 2, 16), (0, 22, 50))                          # apex
    root.location = (x, y, 0); root.rotation_euler = (0, 0, heading)
    return root


def port():
    W.sky(1.0, math.radians(110))
    concrete = W.mat('concrete', '#BDBAB2', .85, noise=(.08, '#CDCAC2'), bump=.05)
    asphalt = W.mat('asphalt', '#55585A', .8, noise=(.15, '#63666A'), bump=.08)
    grass = W.mat('grass', '#5E7B3A', .95, noise=(.04, '#7C9450'), bump=.15)
    dirt = W.mat('dirt', '#8C7B5F', .95, noise=(.1, '#9D8C70'))
    yellow = W.mat('paint_y', '#E2B53A', .6)
    white = W.mat('paint_w', '#EDEDE8', .6)
    building = W.mat('building', '#D8D6CF', .7)
    glass = W.mat('glassband', '#2E3B40', .12)
    steel = W.mat('steel', '#3A3D3F', .5, metal=.6)
    W.plane('land', -420, 0, 420, 420, -.02, grass, thick=6)
    W.plane('quay', -420, 0, 420, 62, .02, concrete)
    W.plane('yard', -150, 62, 280, 175, .03, asphalt)
    W.plane('carlot', -400, 62, -152, 172, .03, asphalt)
    W.plane('road', -420, 176, 420, 190, .03, asphalt)
    W.plane('verge', -420, 190, 420, 196, .025, dirt)
    W.box('quaywall', (840, 2.5, 8), (0, -1.25, -8), W.mat('quaywall', '#9D9A92', .9))
    for x in range(-410, 420, 12):
        W.box('dash', (6, .3, .02), (x, 183, .035), white)
    W.box('edge_line', (840, .35, .02), (0, 3, .025), yellow)
    W.box('lane1', (840, .3, .02), (0, 58, .035), yellow)
    # the car carrier alongside, stern ramp down on the quay
    pctc(25, -18, 0)
    sea_o, _ = W.sea(-900, -700, 900, -1, z=-.8)
    sea_o.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = W.hexc('#173F4A')
    # cars queuing on the quay to drive up the ramp, bollards along the edge
    for i in range(14):
        W.place('sorento', (-82 + (i % 7) * 6.2, 9 + (i // 7) * 3.6, .03), heading=0)
    for x in range(-400, 400, 18):
        bpy.ops.mesh.primitive_cylinder_add(radius=.35, depth=.9, location=(x, 1.2, .45)); bpy.context.object.data.materials.append(W.mat('bollard', '#2C2F31', .5))
    for x in range(-380, 400, 40):
        W.box('pole', (.35, .35, 24), (x, 56, 0), W.mat('pole', '#9AA0A3', .4, metal=.5)); W.box('lamp', (3, 1.2, .5), (x, 56, 24), W.mat('pole', '#9AA0A3', .4, metal=.5))
    for x in (-55, 25, 105):
        sts_crane(x, 0, 0)
    # container yard: neat blocks, stacked 1 to 4 high, natural colours
    for bx in range(5):
        for by in range(3):
            x0, y0 = -140 + bx * 82, 74 + by * 33
            for i in range(10):
                for j in range(9):
                    h = random.choice((1, 2, 2, 3, 3, 4)) if random.random() > .06 else 0
                    for k in range(h):
                        W.place('crate%d' % random.choice((0, 1, 2, 3, 0, 3)), (x0 + i * 6.6, y0 + j * 2.75, k * 2.6), heading=0)
    # export car terminal: new cars waiting to board
    for row in range(6):
        for i in range(30):
            if random.random() < .1: continue
            W.place('sorento', (-385 + i * 7.4, 72 + row * 16, .03), heading=math.pi / 2 if row % 2 else -math.pi / 2)
        W.box('bayline', (238, .2, .02), (-277, 80 + row * 16, .04), white)
    # our car arriving on the truck
    W.real('truck', (-108, 36, .03), heading=0, name='truck')
    W.box('deck', (13.4, 2.55, .35), (-118.5, 36, 1.15), steel)
    for wx in (-123.5, -122.1, -120.7):
        for wy in (1.1, -1.1):
            bpy.ops.mesh.primitive_cylinder_add(radius=.52, depth=.38, location=(wx, 36 + wy, .52), rotation=(math.pi / 2, 0, 0))
            bpy.context.object.data.materials.append(W.mat('tyre', '#1E1F20', .8))
    W.place('sorento', (-116.5, 36, 1.5), heading=0)
    W.place('sorento', (-122.1, 36, 1.5), heading=0)
    for (x, y, w, d, h) in [(210, 210, 46, 22, 14), (262, 214, 26, 26, 22), (-190, 214, 40, 18, 10)]:
        W.box('bld', (w, d, h), (x, y, 0), building)
        for z in range(3, h - 1, 4): W.box('win', (w + .1, d + .1, 1.2), (x, y, z), glass)
    for i in range(240):
        x = random.uniform(-420, 420); y = random.uniform(200, 410)
        if abs(x - 230) < 50 and y < 240: continue
        W.place(random.choice(('fir_a', 'fir_b', 'fir_c')), (x, y, 0), heading=random.uniform(0, 6.28), scale=random.uniform(.8, 1.2))
    tgt = (-60, 40, 0)
    W.camera((-330, -330, 300), tgt, lens=60, dof=tgt, fstop=.35)
    W.render_settings(RW, RH, SAMPLES, exposure=.15)


def paint_sorento(colour='#575C60'):
    """Grey metallic paint like the real car, black trim, black rubber tyres."""
    def new(name, col, rough, metal=0., coat=0.):
        m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = W.hexc(col); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
        if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .03
        return m
    paint = new('sorento_paint', colour, .32, .7, 1.)
    trim = new('sorento_trim', '#0E0F10', .25, 0, .6)
    rubber = new('sorento_rubber', '#141516', .85)
    for o in bpy.data.objects:
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if not m: continue
            n = m.name.split('.')[0]
            if n in ('template_carpaint',): sl.material = paint
            elif n == 'template_blackpaint': sl.material = trim
            elif n in ('template_tyres', 'template_rubber'): sl.material = rubber


def on_white():
    """Transparent render with the shadow, laid on pure white in the compositor."""
    sc = bpy.context.scene; sc.render.film_transparent = True; sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers'); ao = nt.nodes.new('CompositorNodeAlphaOver'); out = nt.nodes.new('CompositorNodeComposite')
    ao.inputs[1].default_value = (1, 1, 1, 1)
    nt.links.new(rl.outputs['Image'], ao.inputs[2]); nt.links.new(ao.outputs['Image'], out.inputs['Image'])


def hero():
    """The grey Sorento, photoreal, on pure white with a soft shadow (the emons truck look)."""
    sc = bpy.context.scene
    # floor: white, catches the shadow; the background is pure white for the camera
    floor = W.plane('floor', -60, -60, 60, 60, 0, W.mat('floor', '#FFFFFF', .9)); floor.is_shadow_catcher = True
    car = W.real('sorento', (0, 0, 0), heading=math.radians(-12))
    paint_sorento()
    w = bpy.data.worlds.new('studio'); sc.world = w; w.use_nodes = True; nt = w.node_tree
    env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(W.PH, 'studio.exr'))
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, math.radians(200))
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    bg = nt.nodes['Background']; bg.inputs['Strength'].default_value = 1.1
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    white = nt.nodes.new('ShaderNodeBackground'); white.inputs['Color'].default_value = (1, 1, 1, 1); white.inputs['Strength'].default_value = 1
    lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac']); nt.links.new(bg.outputs['Background'], mix.inputs[1]); nt.links.new(white.outputs['Background'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], nt.nodes['World Output'].inputs['Surface'])
    # one large soft light above, like a photo studio ceiling
    l = bpy.data.lights.new('soft', 'AREA'); l.shape = 'RECTANGLE'; l.size = 10; l.size_y = 6; l.energy = 2200
    ob = bpy.data.objects.new('soft', l); sc.collection.objects.link(ob); ob.location = (0, 0, 9)
    W.camera((6.6, -9.0, 2.0), (0, .15, .78), lens=55, dof=(0, 0, .8), fstop=8)
    W.render_settings(RW, RH, SAMPLES, exposure=.25)
    sc.view_settings.look = 'AgX - Medium High Contrast'
    on_white()


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


{'studio': studio, 'port': port, 'debug': debug, 'hero': hero}[FRAME]()
bpy.context.scene.render.filepath = os.path.join(OUT, FRAME + '.jpg')
bpy.ops.render.render(write_still=True)
print('rendered', FRAME, flush=True)
