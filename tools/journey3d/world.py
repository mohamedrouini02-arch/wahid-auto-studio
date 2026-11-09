"""Shared pieces for the Wahid Auto journey film: loading the source models at real-world size,
natural materials, sky and sea. Imported by style.py (style frames) and film.py (the full shot).

Every model is loaded once into a hidden collection with its origin at the bottom centre, facing +X,
at its real size in metres. Copies in the world are collection instances, so the scene stays light.
"""
import bpy, os, math, random
from mathutils import Vector, Matrix

A = os.environ.get('J3D_ASSETS', 'a3d/assets')
PH = os.environ.get('J3D_POLYHAVEN', 'ph')

# path, forward axis of the model (direction its front points), real size: ('len'|'h', metres)
MODELS = {
    'sorento': ('2022-kia-sorento-phev-executive-line/source/2022 Kia Sorento PHEV Executive Line/Vehicle.fbx', '+Y', ('len', 4.81)),
    'truck': ('man-tgx-2010-v8-high-detail-semi-truck/source/man Truck.glb', '-Y', ('h', 3.75)),
    'ship': ('hawaiian-car-carrier/source/model.dae', '+Y', ('len', 199.0)),
    'crane': ('port-crane-sokol/source/Crane_2.fbx', '+X', ('h', 46.0)),
    'crane2': ('industrial-port-crane-model/source/base.obj', '+Y', ('h', 38.0)),
    'containers': ('shipping-containers/source/Crates.fbx', '+X', None),
    'fir': (PH + '/fir_tree_01/fir_tree_01_1k.blend', '+X', None),
}


def hexc(h, a=1):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(x / 12.92) if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c] + [a]


def _import(path):
    ext = path.rsplit('.', 1)[1].lower()
    before = set(bpy.data.objects)
    if ext == 'fbx': bpy.ops.import_scene.fbx(filepath=path)
    elif ext == 'obj': bpy.ops.wm.obj_import(filepath=path)
    elif ext == 'dae': bpy.ops.wm.collada_import(filepath=path)
    elif ext in ('glb', 'gltf'): bpy.ops.import_scene.gltf(filepath=path)
    elif ext == 'blend':
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [n for n in src.objects]; dst.collections = [n for n in src.collections]
        for c in dst.collections:
            if c: print('BLENDCOL', c.name, [o.name for o in c.objects][:12], [ch.name for ch in c.children])
        for o in dst.objects:
            if o is None: continue
            print('BLENDOBJ', o.name, o.type, [(m.type, getattr(m, 'node_group', None) and m.node_group.name) for m in o.modifiers],
                  [ (ps.settings.render_type, ps.settings.instance_collection and ps.settings.instance_collection.name, ps.settings.instance_object and ps.settings.instance_object.name, ps.settings.count) for ps in o.particle_systems],
                  o.instance_type, o.instance_collection and o.instance_collection.name, o.hide_render)
            bpy.context.scene.collection.objects.link(o)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type not in ('CAMERA', 'LIGHT')]


def _tex(nt, path, colour=True):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(path, check_existing=True)
    if not colour: n.image.colorspace_settings.name = 'Non-Color'
    return n


def pbr_material(name, base, rough=None, normal=None, metal=None, ao=None, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    bc = _tex(nt, base)
    out = bc.outputs['Color']
    if tint:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1; mix.inputs[7].default_value = hexc(tint)
        nt.links.new(out, mix.inputs[6]); out = mix.outputs[2]
    nt.links.new(out, b.inputs['Base Color'])
    if rough and os.path.exists(rough): nt.links.new(_tex(nt, rough, False).outputs['Color'], b.inputs['Roughness'])
    if metal and os.path.exists(metal): nt.links.new(_tex(nt, metal, False).outputs['Color'], b.inputs['Metallic'])
    if normal and os.path.exists(normal):
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(_tex(nt, normal, False).outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m


def _fix_materials(key, objs):
    """Models whose textures did not come through the import get their materials here."""
    if key == 'containers':
        t = A + '/shipping-containers/textures/'
        mats = {c: pbr_material('cont_' + c, t + f'{c}_Base_color.png', t + f'{c}_Roughness.png', t + f'{c}_Normal_OpenGL.png', t + 'Cargo_Metallic.png')
                for c in ('Red', 'Blue', 'Green', 'White')}
        order = ['Red', 'Blue', 'Green', 'White']
        for i, o in enumerate(sorted([o for o in objs if o.type == 'MESH'], key=lambda o: o.name)):
            o.data.materials.clear(); o.data.materials.append(mats[order[i % 4]])
    if key == 'crane2':
        t = A + '/industrial-port-crane-model/source/'
        m = pbr_material('crane2', t + 'texture_diffuse.png', t + 'texture_roughness.png', t + 'texture_normal.png', t + 'texture_metallic.png')
        for o in objs:
            if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(m)
    if key == 'ship':   # SketchUp export: some walls came in 73% transparent
        for o in objs:
            for sl in getattr(o, 'material_slots', []):
                m = sl.material
                if m and m.use_nodes and 'Principled BSDF' in m.node_tree.nodes:
                    m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 1; m.blend_method = 'OPAQUE'
    if key == 'crane':
        t = A + '/port-crane-sokol/textures/'
        for o in objs:
            for s in getattr(o, 'material_slots', []):
                if s.material and s.material.name.split('.')[0] in ('Body', 'Decor', 'Details'):
                    n = s.material.name.split('.')[0]
                    s.material = pbr_material('sokol_' + n, t + f'{n}_AM.png', t + f'{n}_RM.png', t + f'{n}_NM.png', t + f'{n}_MM.png')


_templates = {}
def template(key):
    """The model in its own hidden collection, origin bottom-centre, facing +X, real size."""
    if key in _templates: return _templates[key]
    rel, fwd, size = MODELS[key]
    path = rel if rel.startswith('/') or rel.startswith(PH) else os.path.join(A, rel)
    objs = _import(path)
    try: bpy.ops.file.find_missing_files(directory=os.path.dirname(os.path.dirname(path)))
    except Exception: pass
    _fix_materials(key, objs)

    col = bpy.data.collections.new('T_' + key); bpy.context.scene.collection.children.link(col)
    for o in objs:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == 'MESH']
    lo = Vector((1e18,) * 3); hi = Vector((-1e18,) * 3)
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    dims = hi - lo
    s = 1.0
    if size:
        kind, metres = size
        s = metres / (max(dims.x, dims.y) if kind == 'len' else dims.z)
    rot = {'+X': 0, '-X': math.pi, '+Y': -math.pi / 2, '-Y': math.pi / 2}[fwd]
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    M = Matrix.Rotation(rot, 4, 'Z') @ Matrix.Scale(s, 4) @ Matrix.Translation(-centre)
    for o in objs:
        if o.parent is None or o.parent not in objs:
            o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
    lc = bpy.context.view_layer.layer_collection.children[col.name]; lc.exclude = True
    info = dict(col=col, dims=Vector((dims.x, dims.y, dims.z)) * s if fwd in ('+X', '-X') else Vector((dims.y, dims.x, dims.z)) * s)
    _templates[key] = info
    print('template', key, 'scale', round(s, 5), 'size', tuple(round(v, 2) for v in info['dims']), flush=True)
    return info


def place(key, loc, heading=0., scale=1., name=None):
    t = template(key)
    e = bpy.data.objects.new(name or ('I_' + key), None)
    e.instance_type = 'COLLECTION'; e.instance_collection = t['col']
    e.location = loc; e.rotation_euler = (0, 0, heading); e.scale = (scale,) * 3
    bpy.context.scene.collection.objects.link(e)
    return e


def real(key, loc, heading=0., name=None):
    """A real (not instanced) copy, for things that move or get recoloured."""
    t = template(key)
    root = bpy.data.objects.new(name or ('R_' + key), None); bpy.context.scene.collection.objects.link(root)
    mapping = {}
    for o in t['col'].objects:
        c = o.copy()
        if o.data is not None: c.data = o.data
        bpy.context.scene.collection.objects.link(c); mapping[o] = c
    for o, c in mapping.items():
        if o.parent in mapping: c.parent = mapping[o.parent]; c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        else: c.parent = root
    root.location = loc; root.rotation_euler = (0, 0, heading)
    return root


# ---------------------------------------------------------------- natural surfaces
def mat(name, col, rough=.6, metal=0., noise=None, bump=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if noise:
        tc = nt.nodes.new('ShaderNodeTexCoord'); n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = noise[0]; n.inputs['Detail'].default_value = 6; n.inputs['Roughness'].default_value = .6
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = hexc(col); ramp.color_ramp.elements[1].color = hexc(noise[1])
        ramp.color_ramp.elements[0].position = .35; ramp.color_ramp.elements[1].position = .7
        nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        if bump:
            bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
            n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = noise[0] * 40
            nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
            nt.links.new(n2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    else:
        b.inputs['Base Color'].default_value = hexc(col)
    return m


def plane(name, x0, y0, x1, y1, z, m, thick=0.):
    import bmesh
    bm = bmesh.new()
    if thick:
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts: v.co.x = (x0 + x1) / 2 + v.co.x * (x1 - x0); v.co.y = (y0 + y1) / 2 + v.co.y * (y1 - y0); v.co.z = z - thick / 2 + v.co.z * thick
    else:
        for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): bm.verts.new((x, y, z))
        bm.faces.new(bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(m)
    return o


def box(name, size, loc, m, rot=0.):
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co.x *= size[0]; v.co.y *= size[1]; v.co.z = (v.co.z + .5) * size[2]
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(m)
    o.location = loc; o.rotation_euler = (0, 0, rot)
    return o


def sea(x0, y0, x1, y1, z=-1.2):
    """Ocean modifier surface with a clear, natural sea colour."""
    o = plane('sea', x0, y0, x1, y1, z, mat('sea_m', '#1f5866', .04))
    m = o.data.materials[0]; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['IOR'].default_value = 1.33; b.inputs['Specular IOR Level'].default_value = .5
    oc = o.modifiers.new('ocean', 'OCEAN')
    oc.geometry_mode = 'DISPLACE'; oc.resolution = 12; oc.spatial_size = 60; oc.wave_scale = .55; oc.choppiness = .9
    sub = o.modifiers.new('sub', 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = sub.render_levels = 0
    o.modifiers.move(1, 0)
    # the plane needs vertices to displace
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=180, use_grid_fill=True); bm.to_mesh(o.data); bm.free()
    return o, oc


def sky(strength=1.0, rot=0.):
    w = bpy.data.worlds.new('sky'); bpy.context.scene.world = w; w.use_nodes = True; nt = w.node_tree
    env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(A, 'citrus_orchard_road_puresky_4k.exr'))
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, rot)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], nt.nodes['Background'].inputs['Color'])
    nt.nodes['Background'].inputs['Strength'].default_value = strength


def render_settings(W, H, samples, exposure=0.):
    sc = bpy.context.scene; r = sc.render
    r.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.cycles.use_denoising = True; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .02
    sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transparent_max_bounces = 16
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Base Contrast'; sc.view_settings.exposure = exposure
    r.image_settings.file_format = 'JPEG'; r.image_settings.quality = 94
    r.use_persistent_data = True


def camera(loc, target, lens=50, dof=None, fstop=4.0):
    sc = bpy.context.scene
    c = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(c); sc.camera = c
    c.data.lens = lens; c.data.clip_end = 5000; c.data.sensor_width = 36
    c.location = loc
    d = Vector(target) - Vector(loc); c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if dof:
        c.data.dof.use_dof = True; c.data.dof.focus_distance = (Vector(dof) - Vector(loc)).length; c.data.dof.aperture_fstop = fstop
    return c
