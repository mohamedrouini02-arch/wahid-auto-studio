"""Import every source model, print what it contains and render one look at it.
blender -b -P inspect.py -- ASSETS_DIR OUT_DIR"""
import bpy, os, sys, math
from mathutils import Vector
A, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
os.makedirs(OUT, exist_ok=True)
MODELS = {
    'sorento': '2022-kia-sorento-phev-executive-line/source/2022 Kia Sorento PHEV Executive Line/Vehicle.fbx',
    'trailer': 'auto-mezzanine-deck-trailer/source/mezz_05_labels.fbx',
    'showroom': 'car-showroom-2/source/showroom 2.blend',
    'grass': 'grass_medium_01_4k/grass_medium_01_4k.blend',
    'ship': 'hawaiian-car-carrier/source/model.dae',
    'crane_ind': 'industrial-port-crane-model/source/base.obj',
    'truck': 'man-tgx-2010-v8-high-detail-semi-truck/source/man Truck.glb',
    'crane_sokol': 'port-crane-sokol/source/Crane_2.fbx',
    'containers': 'shipping-containers/source/Crates.fbx',
    'studio': 'studio-v1-for-car/source/Studio V1- Textures Packed.blend',
}

def load(path):
    ext = path.rsplit('.', 1)[1].lower()
    if ext == 'fbx': bpy.ops.import_scene.fbx(filepath=path)
    elif ext == 'obj': bpy.ops.wm.obj_import(filepath=path)
    elif ext == 'dae': bpy.ops.wm.collada_import(filepath=path)
    elif ext in ('glb', 'gltf'): bpy.ops.import_scene.gltf(filepath=path)
    elif ext == 'blend':
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = src.objects
        for o in dst.objects:
            if o is not None and o.type != 'CAMERA': bpy.context.scene.collection.objects.link(o)

for name, rel in MODELS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    path = os.path.join(A, rel)
    try:
        load(path)
    except Exception as e:
        print('MODEL', name, 'FAILED', e); continue
    try: bpy.ops.file.find_missing_files(directory=os.path.join(A, rel.split('/')[0]))
    except Exception as e: print('find_missing', e)
    meshes = [o for o in sc.objects if o.type == 'MESH']
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    dims = hi - lo
    mats = sorted({s.material.name for o in meshes for s in o.material_slots if s.material})
    missing = [i.filepath for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and not os.path.exists(bpy.path.abspath(i.filepath))]
    print(f'MODEL {name}: objects={len(sc.objects)} meshes={len(meshes)} tris={tris} dims={tuple(round(x,2) for x in dims)} min={tuple(round(x,2) for x in lo)}')
    print(f'  materials({len(mats)}): {mats[:40]}')
    print(f'  missing images: {missing[:10]}')
    print(f'  top objects: {[o.name for o in sc.objects if o.parent is None][:25]}')
    # look at it from a 3/4 view
    world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
    env = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(os.path.join(A, 'citrus_orchard_road_puresky_4k.exr'))
    world.node_tree.links.new(env.outputs['Color'], world.node_tree.nodes['Background'].inputs['Color'])
    ctr = (lo + hi) / 2; r = dims.length / 2
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 40; cam.data.clip_end = max(1000, r * 20)
    d = Vector((1.0, -1.25, .7)).normalized()
    cam.location = ctr + d * r * 2.4
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    r_ = sc.render; r_.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
    r_.resolution_x, r_.resolution_y = 800, 560; r_.filepath = os.path.join(OUT, name + '.jpg'); r_.image_settings.file_format = 'JPEG'
    try: bpy.ops.render.render(write_still=True); print('  rendered')
    except Exception as e: print('  render failed', e)
