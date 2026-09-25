"""Render helpers: textured preview materials (mapped from the BH_* contract names) + a consistent 3/4 light rig.

The exported GLBs carry flat colours only; for evidence renders we re-import them and swap every BH_* material for a
textured Principled node tree that follows the recommended Godot mapping documented in README.md.
"""
import math
import os

import bpy
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TEX = os.path.join(ROOT, "game", "assets", "textures")
ENV = os.path.join(ROOT, "game", "assets", "environment")
EVI = os.path.join(ROOT, "work", "lemondev", "bh-001", "evidence", "environment")

# name -> (texture set or None, albedo tint (linear multiplier), roughness override, metallic, emission, alpha mode)
RENDER_MAP = {
    "BH_Stone": ("rock_cliff", (1.25, 1.22, 1.18), None, 0.0, None, None),
    "BH_StoneDark": ("rock_cliff", (0.62, 0.62, 0.64), None, 0.0, None, None),
    "BH_Brick": ("brick", (1, 1, 1), None, 0.0, None, None),
    "BH_Cobble": ("cobblestone", (1, 1, 1), None, 0.0, None, None),
    "BH_Wood": ("wood_grain", (1.1, 1.05, 1.0), None, 0.0, None, None),
    "BH_WoodDark": ("wood_grain", (0.5, 0.45, 0.42), None, 0.0, None, None),
    "BH_Bark": ("bark", (1.2, 1.15, 1.1), None, 0.0, None, None),
    "BH_Leaves": ("leaves_atlas", (1.25, 1.25, 1.25), 0.75, 0.0, None, "CLIP"),
    "BH_Grass": ("grass_blades", (1.3, 1.3, 1.3), 0.8, 0.0, None, "CLIP"),
    "BH_Moss": ("moss", (1.1, 1.1, 1.1), None, 0.0, None, None),
    "BH_Metal": ("metal_iron", (1.9, 1.85, 1.8), None, 1.0, None, None),
    "BH_Iron": ("metal_iron", (1.0, 1.0, 1.0), None, 0.85, None, None),
    "BH_Gold": ("metal_iron", (3.2, 2.2, 0.75), 0.35, 1.0, None, None),
    "BH_Cloth": ("cloth", (1.0, 0.95, 0.88), None, 0.0, None, None),
    "BH_ClothRed": ("cloth", (1.05, 0.22, 0.18), None, 0.0, None, None),
    "BH_Bone": (None, (0.62, 0.56, 0.44), 0.65, 0.0, None, None),
    "BH_Candle": (None, (0.75, 0.66, 0.48), 0.45, 0.0, None, None),
    "BH_Flame": (None, (1.0, 0.5, 0.15), 0.5, 0.0, ((1.0, 0.45, 0.12), 10.0), None),
    "BH_Rune": (None, (0.2, 0.7, 0.9), 0.4, 0.0, ((0.25, 0.8, 1.0), 5.0), None),
    "BH_Corruption": (None, (0.3, 0.07, 0.45), 0.4, 0.0, ((0.55, 0.12, 0.9), 5.0), None),
    "BH_Water": (None, (0.02, 0.14, 0.16), 0.04, 0.0, ((0.05, 0.45, 0.45), 0.35), "BLEND"),
    "BH_Glass": (None, (0.5, 0.6, 0.6), 0.05, 0.0, None, "BLEND"),
    "BH_Thatch": ("thatch", (1.0, 1.0, 1.0), None, 0.0, None, None),
    "BH_Dirt": ("dirt", (1.0, 1.0, 1.0), None, 0.0, None, None),
}

_img_cache = {}


def _img(path, colorspace):
    key = (path, colorspace)
    if key in _img_cache:
        return _img_cache[key]
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = colorspace
    _img_cache[key] = im
    return im


def make_render_material(name):
    base = name.split(".")[0]
    spec = RENDER_MAP.get(base)
    m = bpy.data.materials.get("R_" + base)
    if m:
        return m
    m = bpy.data.materials.new("R_" + base)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    texset, tint, rough, metal, emis, alpha = spec
    vcol = nt.nodes.new("ShaderNodeVertexColor")
    vcol.layer_name = "Color"
    tintn = nt.nodes.new("ShaderNodeRGB")
    tintn.outputs[0].default_value = (*tint, 1)
    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    mix1.blend_type = "MULTIPLY"
    mix1.inputs["Factor"].default_value = 1.0
    nt.links.new(tintn.outputs[0], mix1.inputs["B"])
    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    mix2.blend_type = "MULTIPLY"
    mix2.inputs["Factor"].default_value = 1.0
    nt.links.new(mix1.outputs["Result"], mix2.inputs["A"])
    nt.links.new(vcol.outputs["Color"], mix2.inputs["B"])
    nt.links.new(mix2.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = metal
    if texset:
        uv = nt.nodes.new("ShaderNodeUVMap")
        single = texset in ("leaves_atlas", "grass_blades")
        ap = os.path.join(TEX, texset + (".png" if single else "_albedo.png"))
        ta = nt.nodes.new("ShaderNodeTexImage")
        ta.image = _img(ap, "sRGB")
        nt.links.new(uv.outputs[0], ta.inputs[0])
        nt.links.new(ta.outputs["Color"], mix1.inputs["A"])
        if single:
            nt.links.new(ta.outputs["Alpha"], bsdf.inputs["Alpha"])
        else:
            tr = nt.nodes.new("ShaderNodeTexImage")
            tr.image = _img(os.path.join(TEX, texset + "_rough.png"), "Non-Color")
            nt.links.new(uv.outputs[0], tr.inputs[0])
            if rough is None:
                nt.links.new(tr.outputs["Color"], bsdf.inputs["Roughness"])
            else:
                bsdf.inputs["Roughness"].default_value = rough
            tn = nt.nodes.new("ShaderNodeTexImage")
            tn.image = _img(os.path.join(TEX, texset + "_normal.png"), "Non-Color")
            nt.links.new(uv.outputs[0], tn.inputs[0])
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value = 1.0
            nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        mix1.inputs["A"].default_value = (1, 1, 1, 1)
        bsdf.inputs["Roughness"].default_value = rough if rough is not None else 0.6
    if emis:
        bsdf.inputs["Emission Color"].default_value = (*emis[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emis[1]
    if alpha == "BLEND":
        bsdf.inputs["Alpha"].default_value = 0.72
        m.surface_render_method = "BLENDED"
    if base in ("BH_Leaves", "BH_Grass"):
        m.use_backface_culling = False
    return m


def swap_materials(objs):
    for ob in objs:
        if ob.type != "MESH":
            continue
        for slot in ob.material_slots:
            if slot.material and slot.material.name.split(".")[0] in RENDER_MAP:
                slot.material = make_render_material(slot.material.name)


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.name.endswith("-colonly") or "-colonly" in o.name:
            o.hide_render = True
            o.hide_viewport = True
    swap_materials(new)
    return new


def world_bounds(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != "MESH" or o.hide_render:
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


def setup_scene(res=(512, 512), world=(0.03, 0.035, 0.05), world_strength=1.0, samples=48):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = samples
    try:
        sc.eevee.use_shadows = True
    except Exception:
        pass
    try:
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 0.3
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*world, 1)
    bg.inputs[1].default_value = world_strength
    sc.render.film_transparent = False
    return sc


def add_sun(name, az, el, strength, color, angle=3.0):
    l = bpy.data.lights.new(name, "SUN")
    l.energy = strength
    l.color = color
    l.angle = math.radians(angle)
    o = bpy.data.objects.new(name, l)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = Euler((math.radians(90 - el), 0, math.radians(az + 90)), "XYZ")
    return o


def add_point(name, loc, energy, color, radius=0.1):
    l = bpy.data.lights.new(name, "POINT")
    l.energy = energy
    l.color = color
    l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l)
    o.location = loc
    bpy.context.scene.collection.objects.link(o)
    return o


def standard_rig():
    add_sun("key", -35, 48, 3.6, (1.0, 0.86, 0.7))
    add_sun("fill", 150, 30, 0.9, (0.55, 0.65, 0.9))
    add_sun("rim", 100, 18, 1.2, (0.7, 0.75, 1.0))


def ground(size=60, color=(0.055, 0.05, 0.048)):
    me = bpy.data.meshes.new("ground")
    s = size / 2
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("ground", me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("ground_mat")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    me.materials.append(m)
    return ob


def camera_34(mn, mx, az=-40.0, el=34.0, lens=50.0, margin=1.08):
    ctr = (mn + mx) / 2
    rad = (mx - mn).length / 2
    cam = bpy.data.cameras.new("cam")
    cam.lens = lens
    cam.sensor_width = 36
    fov = 2 * math.atan(18 / lens)
    d = rad / math.sin(fov / 2) * margin
    a, e = math.radians(az), math.radians(el)
    dirv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    o = bpy.data.objects.new("cam", cam)
    o.location = ctr + dirv * d
    o.rotation_euler = (-dirv).to_track_quat("-Z", "Y").to_euler()
    cam.clip_end = d * 4 + 100
    bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    return o
