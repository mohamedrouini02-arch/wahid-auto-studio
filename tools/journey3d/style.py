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


def paint_sorento(colour='#575C60', objs=None):
    """Grey metallic paint like the real car, black trim, black rubber tyres."""
    def new(name, col, rough, metal=0., coat=0.):
        m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = W.hexc(col); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
        if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .03
        return m
    paint = new('sorento_paint', colour, .32, .7, 1.)
    gloss_black = new('sorento_rims', '#060607', .18, 0., 1.)
    trim = new('sorento_trim', '#0E0F10', .25, 0, .6)
    rubber = new('sorento_rubber', '#141516', .85)
    for o in (objs if objs is not None else bpy.data.objects):
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if not m: continue
            n = m.name.split('.')[0]
            if n in ('template_carpaint',): sl.material = paint
            elif n == 'template_blackpaint': sl.material = trim
            elif n in ('template_tyres', 'template_rubber'): sl.material = rubber
    # rims: every part sitting inside a tyre (same centre, smaller) becomes gloss black, except the brakes
    from mathutils import Vector
    def bbox(o):
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
        return (lo + hi) / 2, hi - lo
    meshes = [o for o in (objs if objs is not None else []) if o.type == 'MESH']
    bpy.context.view_layer.update()
    wheels = [bbox(o) for o in meshes if any(sl.material and sl.material.name == 'sorento_rubber' for sl in o.material_slots)
              and bbox(o)[0].z < .8]
    wheels = [w for w in wheels if max(w[1]) < 1.0]
    print('WHEELS', [(tuple(round(v, 2) for v in c), round(max(d), 2)) for c, d in wheels], flush=True)
    for o in meshes:
        c, d = bbox(o)
        for wc, wd in wheels:
            if (c - wc).length < .22 and max(d) <= max(wd) * 1.02:
                for sl in o.material_slots:
                    n = sl.material.name if sl.material else ''
                    if n and n != 'sorento_rubber' and not any(k in n for k in ('disc', 'brake', 'caliper', 'red')):
                        print('RIM', o.name, n, flush=True); sl.material = gloss_black
                break


def on_white():
    """Transparent PNG with the car's shadow; laid on pure white afterwards (outside the colour transform)."""
    sc = bpy.context.scene; sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'


def hero():
    """The grey Sorento, photoreal, on pure white with a soft shadow (the emons truck look)."""
    sc = bpy.context.scene
    # floor: white, catches the shadow; the background is pure white for the camera
    floor = W.plane('floor', -60, -60, 60, 60, 0, W.mat('floor', '#FFFFFF', .9)); floor.is_shadow_catcher = True
    car = W.real('sorento', (0, 0, 0), heading=math.radians(-12))
    paint_sorento(objs=list(car.children_recursive))
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


# ---------------------------------------------------------------- the clay world (emons look)
CLAY = '#F1F1EE'


def clay_mat(name='clay', col=CLAY, rough=.62):
    if name in bpy.data.materials: return bpy.data.materials[name]
    return W.mat(name, col, rough)


def clay_template(key, special=None):
    """Turn a model into white clay; `special` maps material-name keywords to other materials."""
    t = W.template(key)
    for o in t['col'].all_objects:
        for sl in getattr(o, 'material_slots', []):
            n = (sl.material.name if sl.material else '').lower()
            m = clay_mat()
            for kw, mm in (special or {}).items():
                if kw in n: m = mm; break
            sl.material = m


def lowpoly_tree(x, y, s=1.):
    import bmesh
    bm = bmesh.new()
    if random.random() < .35:       # a tall pointed tree among the round ones
        bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=2.2 * s, radius2=0, depth=7.5 * s)
        for v in bm.verts: v.co += v.co.normalized() * random.uniform(-.15, .15) * s
    else:
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=2.6 * s)
        for v in bm.verts:
            v.co.z *= random.uniform(1.0, 1.35); v.co += v.co.normalized() * random.uniform(-.35, .35) * s
    me = bpy.data.meshes.new('tree'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('tree', me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(random.choice(TREEMATS)); o.location = (x, y, 3.4 * s); o.rotation_euler = (0, 0, random.uniform(0, 6.3))
    W.box('trunk', (.35 * s, .35 * s, 1.4 * s), (x, y, 0), clay_mat())


def faceted_water(x0, y0, x1, y1, z=-1.0, step=7.):
    import bmesh
    bm = bmesh.new()
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    vs = [[bm.verts.new((x0 + i * step + random.uniform(-1.5, 1.5), y0 + j * step + random.uniform(-1.5, 1.5), z + random.uniform(-.35, .35)))
           for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            if (i + j) % 2: bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1])); bm.faces.new((vs[i][j], vs[i + 1][j + 1], vs[i][j + 1]))
            else: bm.faces.new((vs[i][j], vs[i + 1][j], vs[i][j + 1])); bm.faces.new((vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    me = bpy.data.meshes.new('water'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('water', me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(W.mat('water', '#BFDDD1', .35, noise=(.02, '#D3E9E0')))
    return o


def ribbon(name, pts, width, z, m):
    """A flat strip (road) along a polyline."""
    import bmesh
    from mathutils import Vector
    bm = bmesh.new(); left = []; right = []
    P = [Vector((x, y, 0)) for x, y in pts]
    for i, p in enumerate(P):
        d = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        n = Vector((-d.y, d.x, 0)) * width / 2
        left.append(bm.verts.new((p + n).to_tuple())); right.append(bm.verts.new((p - n).to_tuple()))
        left[-1].co.z = right[-1].co.z = z
    for i in range(len(P) - 1): bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(m)
    return o


def arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def person(x, y, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=.22, depth=1.25, location=(x, y, .63)); bpy.context.object.data.materials.append(m)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=.17, location=(x, y, 1.45)); bpy.context.object.data.materials.append(m)


def annulus(name, cx, cy, r0, r1, z, m, n=64):
    import bmesh
    bm = bmesh.new()
    a = [bm.verts.new((cx + r0 * math.cos(i / n * 6.2832), cy + r0 * math.sin(i / n * 6.2832), z)) for i in range(n)]
    b = [bm.verts.new((cx + r1 * math.cos(i / n * 6.2832), cy + r1 * math.sin(i / n * 6.2832), z)) for i in range(n)]
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(m)


def clay_port():
    global TREEMATS
    random.seed(11)
    TREEMATS = [W.mat('t1', '#5FB89B', .8), W.mat('t2', '#71C3A8', .8), W.mat('t3', '#4FA98B', .8)]
    W.sky(.9, math.radians(140))
    nt = bpy.context.scene.world.node_tree; out = nt.nodes['World Output']; src = out.inputs['Surface'].links[0].from_socket
    white = nt.nodes.new('ShaderNodeBackground'); white.inputs['Color'].default_value = W.hexc('#F3F4F2'); white.inputs['Strength'].default_value = 1
    lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac']); nt.links.new(src, mix.inputs[1]); nt.links.new(white.outputs['Background'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    ground = clay_mat(); road = clay_mat('road', '#E2E3E0', .7); line = clay_mat('line', '#FFFFFF', .5)
    pave = clay_mat('pave', '#EAEBE8', .75)
    accent = W.mat('accent', '#3F9C7F', .45); accent2 = W.mat('accent2', '#2E7A62', .45)
    glass = W.mat('cglass', '#A9BAB7', .15); dark = W.mat('cdark', '#5B615E', .6)
    # ground: top exactly at 0
    W.plane('land', -420, 0, 420, 420, -2.02, ground, thick=4)
    W.box('quaywall', (840, 1.5, 3.0), (0, -.75, -3.0), clay_mat('wall', '#E6E7E4', .7))
    W.plane('quayedge', -420, 0, 420, 14, .01, pave)
    faceted_water(-500, -400, 500, -1, z=-1.0)
    # roads: the port ring road, the lane to the ramp, the main road with a roundabout, the curve in from the gate
    ribbon('ring', [(-420, 92), (420, 92)], 10, .02, road)
    ribbon('lane', [(-96, 14), (-96, 92)], 12, .021, road)
    ribbon('main', [(-420, 128), (-78, 128)], 12, .02, road); ribbon('main2', [(-42, 128), (420, 128)], 12, .02, road)
    annulus('rab', -60, 128, 11, 20, .022, road); annulus('rab_kerb', -60, 128, 10.4, 11, .05, line)
    ribbon('gate_rd', [(-60, 108), (-60, 92)], 10, .023, road)
    ribbon('curve', arc(-60, 160, 30, -math.pi / 2, 0) + [(-30, 200), (-30, 260)], 10, .021, road)
    for x in range(-416, -80, 9): W.box('dash', (4.5, .22, .02), (x, 128, .03), line)
    for x in range(-38, 420, 9): W.box('dash', (4.5, .22, .02), (x, 128, .03), line)
    for x in range(-416, 420, 9): W.box('dash', (4.5, .2, .02), (x, 92, .03), line)
    # fence along the port boundary with the gate
    for x in range(-418, 420, 4):
        if abs(x + 60) < 7: continue
        W.box('fpost', (.12, .12, 2.2), (x, 108, 0), line)
    W.box('frail', (836, .08, .08), (0, 108, 2.1), line)
    W.box('booth', (3.4, 3, 3), (-52, 106, 0), ground); W.box('booth_roof', (4.2, 3.8, .35), (-52, 106, 3), accent)
    W.box('canopy', (16, 12, .5), (-60, 106, 5.5), ground)
    for cx in (-67.5, -52.5):
        W.box('cpost', (.4, .4, 5.5), (cx, 101, 0), ground); W.box('cpost', (.4, .4, 5.5), (cx, 111, 0), ground)
    bar = W.box('barrier', (7, .18, .18), (-63.5, 103, 1.0), accent)
    # export lot: rows of new cars (white clay) between trees
    W.plane('lot', -250, 18, -112, 84, .02, pave)
    for r in range(5):
        W.box('bay', (136, .16, .02), (-181, 24 + r * 13, .03), line)
    # our grey Sorento keeps its real materials (own copy of the meshes), then the other cars turn to clay
    hero = W.real('sorento', (-96, 61.2, 1.5), heading=-math.pi / 2, name='hero')
    for o in hero.children_recursive:
        if o.data is not None: o.data = o.data.copy()
    paint_sorento(objs=list(hero.children_recursive))
    clay_template('sorento', {'glass': glass, 'tyre': W.mat('ctyre', '#4A4E50', .8), 'rubber': W.mat('ctyre', '#4A4E50', .8)})
    for r in range(5):
        for i in range(18):
            if random.random() < .12: continue
            W.place('sorento', (-244 + i * 7.4, 24 + r * 13 + 4.2 * (1 if r % 2 else -1) + 4.2, .02), heading=math.pi / 2 if r % 2 else -math.pi / 2)
    # cars queuing down the lane to the stern ramp
    for i in range(7):
        for lx in (-98.4, -93.6):
            if lx < -96 and i > 4: continue
            W.place('sorento', (lx + 18.5, 16 + i * 6.0, .02), heading=-math.pi / 2)
    # the ship alongside, white with the brand green below, stern ramp down on the quay
    ship = pctc(10, -19, 0)
    for o in ship.children:
        n = o.name
        if n.startswith('h_red') or n.startswith('h_navy'): o.data.materials[0] = accent2
        elif n.startswith('h_band') or n.startswith('funnel_top'): o.data.materials[0] = accent
        elif n.startswith('bridge_win'): o.data.materials[0] = glass
        elif n.startswith('lifeboat') or n.startswith('vent'): o.data.materials[0] = clay_mat('clay2', '#E2E3E0')
        else: o.data.materials[0] = clay_mat()
    for x in range(-200, 200, 12):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.3, depth=.7, location=(x, 1.2, .35)); bpy.context.object.data.materials.append(line)
    # containers: white blocks, a few in green
    clay_template('crate0'); clay_template('crate1'); clay_template('crate2', {'': accent}); clay_template('crate3')
    for bx in range(3):
        for by in range(2):
            x0, y0 = 10 + bx * 64, 20 + by * 34
            for i in range(8):
                for j in range(9):
                    for k in range(random.choice((1, 2, 2, 3, 3))):
                        W.place('crate%d' % random.choice((0, 1, 3, 0, 1, 3, 2)), (x0 + i * 6.6, y0 + j * 2.75, k * 2.6))
    # buildings: terminal offices, warehouse, workshop
    def building(x, y, w, d, h, bands=2):
        W.box('bld', (w, d, h), (x, y, 0), ground)
        for k in range(bands): W.box('win', (w + .2, d + .2, 1.6), (x, y, 2.5 + k * (h - 3) / max(bands, 1)), glass)
        W.box('roof', (w - 4, d - 4, .6), (x, y, h), clay_mat('clay2', '#E2E3E0'))
        W.box('unit', (4, 3, 1.6), (x + w / 4, y, h), ground); W.box('unit', (3, 3, 1.4), (x - w / 4, y + 2, h), ground)
    building(-175, 150, 54, 24, 13, 3); building(-110, 170, 30, 20, 9, 2)
    W.box('shed', (90, 34, 12), (130, 160, 0), ground)
    for k in range(8): W.box('saw', (10, 34.4, 2.2), (95 + k * 10, 160, 12), clay_mat('clay2', '#E2E3E0'))
    building(260, 150, 40, 22, 10, 2)
    # green trucks carrying white cars on the roads
    tyre = W.mat('ctyre', '#4A4E50', .8)
    for o in W.template('truck')['col'].all_objects:
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if not m or m.name in ('accent', 'cglass', 'ctyre'): continue
            b = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
            n = m.name.lower(); alpha = b.inputs['Alpha'].default_value if b else 1; tr = b.inputs['Transmission Weight'].default_value if b else 0
            col = b.inputs['Base Color'].default_value if b else (1, 1, 1, 1); lum = .2126 * col[0] + .7152 * col[1] + .0722 * col[2]
            if alpha < .9 or tr > .4 or any(k in n for k in ('glass', 'window', 'wind', 'lens')): sl.material = glass
            elif any(k in n for k in ('tyre', 'tire', 'rubber', 'wheel')) or (lum < .03 and not (b and b.inputs['Base Color'].is_linked)): sl.material = tyre
            else: sl.material = accent
            print('TRUCKMAT', o.name, n, round(alpha, 2), round(tr, 2), round(lum, 3), '->', sl.material.name, flush=True)
    def carrier(x, y, heading, our=False):
        t = W.real('truck', (x, y, .02), heading=heading, name='truck')
        dx, dy = math.cos(heading), math.sin(heading)
        d = W.box('deck', (13.4, 2.55, .35), (x - dx * 8.45, y - dy * 8.45, 1.15), clay_mat('clay2', '#E2E3E0')); d.rotation_euler = (0, 0, heading)
        for off in (11.6, 13.0):
            for side in (-1, 1):
                bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=.5, depth=.4, location=(x - dx * off + side * dy * 1.05, y - dy * off - side * dx * 1.05, .5), rotation=(math.pi / 2, 0, heading))
                bpy.context.object.data.materials.append(tyre)
        if not our:
            for k in (0, 1): W.place('sorento', (x - dx * (5.5 + k * 5.7), y - dy * (5.5 + k * 5.7), 1.5), heading=heading)
    carrier(-96, 50, -math.pi / 2, our=True)                    # ours, on its way to the ramp
    carrier(-230, 125, 0); carrier(140, 131, math.pi); carrier(-30, 230, math.pi / 2)
    # a few cars on the main road
    for (x, y, h) in [(-300, 125.5, 0), (-150, 130.5, math.pi), (60, 125.5, 0), (250, 130.5, math.pi), (330, 125.5, 0)]:
        W.place('sorento', (x, y, .02), heading=h)
    # people: at the gate, at the ramp, in the lot
    for (x, y) in [(-50, 103), (-49, 104.5), (-84, 10), (-82, 12.5), (-86, 8.5), (-120, 40), (-160, 60), (-60, 20)]:
        person(x, y, dark)
    # lamps
    for x in range(-400, 420, 32):
        W.box('pole', (.22, .22, 13), (x, 12, 0), ground); W.box('lamp', (1.6, .5, .25), (x, 12.6, 13), ground)
    for x in range(-400, 420, 40):
        W.box('pole', (.2, .2, 9), (x, 121, 0), ground); W.box('lamp', (1.2, .4, .2), (x, 121.5, 9), ground)
    # trees: clusters, rows along the roads, a garden in the roundabout
    for (cx, cy, n) in [(-300, 40, 26), (-20, 175, 22), (60, 220, 34), (235, 110, 14), (330, 60, 18), (-280, 200, 34), (190, 250, 38), (-140, 250, 34), (-370, 120, 12)]:
        for i in range(n):
            lowpoly_tree(cx + random.gauss(0, 16), cy + random.gauss(0, 12), random.uniform(1.6, 2.5))
    for x in list(range(-410, -80, 9)) + list(range(-40, 420, 9)):
        for yy in (116, 140):
            if random.random() < .45: continue
            lowpoly_tree(x + random.uniform(-3, 3), yy + random.uniform(-2, 2), random.uniform(.8, 1.5))
    for y in range(22, 84, 11):
        lowpoly_tree(-256 + random.uniform(-1, 1), y, random.uniform(1.0, 1.3)); lowpoly_tree(-106 + random.uniform(-1, 1), y, random.uniform(.9, 1.1))
    for i in range(7):
        lowpoly_tree(-60 + random.gauss(0, 3.5), 128 + random.gauss(0, 3.5), random.uniform(1.0, 1.5))
    W.render_settings(RW, RH, SAMPLES, exposure=.45)


CLAY_VIEWS = {
    'wide': ((-330, -260, 270), (-70, 70, 0), 42, (-96, 50, 0), 1.2),
    'ramp': ((-205, -120, 92), (-86, 18, 2), 50, (-86, 18, 2), .9),
    'truck': ((-160, -10, 48), (-96, 52, 2), 62, (-96, 52, 2), 1.0),
}


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


if FRAME == 'clay':
    clay_port()
    for name, (loc, tgt, lens, focus, fstop) in CLAY_VIEWS.items():
        W.camera(loc, tgt, lens=lens, dof=focus, fstop=fstop)
        bpy.context.scene.render.filepath = os.path.join(OUT, 'clay-%s.jpg' % name)
        bpy.ops.render.render(write_still=True)
        print('rendered', name, flush=True)
else:
    {'studio': studio, 'port': port, 'debug': debug, 'hero': hero}[FRAME]()
    bpy.context.scene.render.filepath = os.path.join(OUT, FRAME + ('.png' if FRAME == 'hero' else '.jpg'))
    bpy.ops.render.render(write_still=True)
    print('rendered', FRAME, flush=True)
