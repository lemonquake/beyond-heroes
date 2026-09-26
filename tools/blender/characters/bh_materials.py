"""Contract material names with sensible standalone PBR values (Godot overrides them by name)."""

# name: (base_rgb, metallic, roughness, emission_rgb, emission_strength, alpha)
BASE = {
    "BH_Steel": ((0.56, 0.57, 0.59), 1.0, 0.34, None, 0.0, 1.0),
    "BH_DarkSteel": ((0.16, 0.16, 0.18), 1.0, 0.48, None, 0.0, 1.0),
    "BH_Gold": ((0.78, 0.55, 0.22), 1.0, 0.30, None, 0.0, 1.0),
    "BH_Leather": ((0.085, 0.047, 0.026), 0.0, 0.62, None, 0.0, 1.0),
    "BH_Cloth_Primary": ((0.30, 0.025, 0.035), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Cloth_Secondary": ((0.10, 0.09, 0.085), 0.0, 0.9, None, 0.0, 1.0),
    "BH_Skin": ((0.62, 0.43, 0.33), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Bone": ((0.66, 0.60, 0.47), 0.0, 0.6, None, 0.0, 1.0),
    "BH_Rust": ((0.30, 0.15, 0.075), 0.45, 0.82, None, 0.0, 1.0),
    "BH_Emissive": ((0.2, 0.6, 1.0), 0.0, 0.4, (0.3, 0.75, 1.0), 6.0, 1.0),
    "BH_Shadow": ((0.035, 0.03, 0.06), 0.0, 0.7, (0.06, 0.03, 0.12), 0.6, 1.0),
    "BH_WeakPoint": ((1.0, 0.45, 0.1), 0.0, 0.3, (1.0, 0.42, 0.08), 12.0, 1.0),
    "BH_Wood": ((0.12, 0.07, 0.038), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Hair": ((0.06, 0.045, 0.035), 0.0, 0.6, None, 0.0, 1.0),
    "BH_Aether": ((0.55, 0.95, 1.0), 0.0, 0.25, (0.45, 0.92, 1.0), 9.0, 1.0),
}

# Per-character palette overrides (same names; different base colors)
OVERRIDES = {
    "knight": {},
    "mage": {"BH_Cloth_Primary": ((0.055, 0.045, 0.2), 0.0, 0.82, None, 0.0, 1.0),
             "BH_Cloth_Secondary": ((0.12, 0.10, 0.12), 0.0, 0.9, None, 0.0, 1.0),
             "BH_Emissive": ((0.3, 0.7, 1.0), 0.0, 0.4, (0.35, 0.8, 1.0), 8.0, 1.0)},
    "hollow_soldier": {"BH_Cloth_Primary": ((0.20, 0.05, 0.04), 0.0, 0.9, None, 0.0, 1.0),
                       "BH_Emissive": ((0.3, 0.9, 0.8), 0.0, 0.4, (0.35, 1.0, 0.85), 6.0, 1.0)},
    "bonewarden": {"BH_Cloth_Primary": ((0.12, 0.10, 0.07), 0.0, 0.9, None, 0.0, 1.0),
                   "BH_Emissive": ((0.3, 0.9, 0.8), 0.0, 0.4, (0.35, 1.0, 0.85), 6.0, 1.0)},
    "grave_archer": {"BH_Cloth_Primary": ((0.09, 0.11, 0.08), 0.0, 0.9, None, 0.0, 1.0),
                     "BH_Emissive": ((0.3, 0.9, 0.8), 0.0, 0.4, (0.35, 1.0, 0.85), 6.0, 1.0)},
    "ashen_cultist": {"BH_Cloth_Primary": ((0.13, 0.11, 0.10), 0.0, 0.9, None, 0.0, 1.0),
                      "BH_Cloth_Secondary": ((0.28, 0.05, 0.03), 0.0, 0.88, None, 0.0, 1.0),
                      "BH_Emissive": ((1.0, 0.35, 0.05), 0.0, 0.4, (1.0, 0.38, 0.06), 9.0, 1.0)},
    "ghoul_brute": {"BH_Skin": ((0.36, 0.38, 0.33), 0.0, 0.5, None, 0.0, 1.0),
                    "BH_Cloth_Primary": ((0.14, 0.10, 0.07), 0.0, 0.92, None, 0.0, 1.0),
                    "BH_Emissive": ((0.5, 0.9, 0.3), 0.0, 0.4, (0.55, 1.0, 0.3), 5.0, 1.0)},
    "shade_stalker": {"BH_Cloth_Primary": ((0.05, 0.04, 0.08), 0.0, 0.85, None, 0.0, 1.0),
                      "BH_Emissive": ((0.65, 0.35, 1.0), 0.0, 0.4, (0.7, 0.35, 1.0), 7.0, 1.0)},
    "boss_warden": {"BH_Cloth_Primary": ((0.10, 0.04, 0.08), 0.0, 0.88, None, 0.0, 1.0),
                    "BH_Emissive": ((0.55, 0.25, 1.0), 0.0, 0.4, (0.6, 0.28, 1.0), 9.0, 1.0)},
}


def make_materials(char="knight", vertex_color=True):
    import bpy
    spec = dict(BASE)
    spec.update(OVERRIDES.get(char, {}))
    out = {}
    for name, (rgb, met, rough, erg, estr, alpha) in spec.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Metallic"].default_value = met
        bsdf.inputs["Roughness"].default_value = rough
        if erg:
            bsdf.inputs["Emission Color"].default_value = (*erg, 1.0)
            bsdf.inputs["Emission Strength"].default_value = estr
        if vertex_color and not erg:
            # multiply the baked AO/wear vertex colors into the base color (same as the game does)
            vc = nt.nodes.new("ShaderNodeVertexColor")
            vc.layer_name = "Col"
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs[6].default_value = (*rgb, 1.0)
            nt.links.new(vc.outputs["Color"], mix.inputs[7])
            nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        m.diffuse_color = (*rgb, 1.0)
        m.metallic = met
        m.roughness = rough
        out[name] = m
    return out


def bake_vertex_ao(ob, rays=24, dist=0.35, strength=0.75, seed=7):
    """Bake ambient occlusion (hemisphere ray casts against the mesh itself, rest pose) plus a subtle
    height gradient into the byte color attribute 'Col' (exported as glTF COLOR_0)."""
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    me = ob.data
    bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons], epsilon=0.0)
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    nor = np.empty(n * 3)
    me.vertices.foreach_get("normal", nor)
    nor = nor.reshape(-1, 3)
    rng = np.random.default_rng(seed)
    dirs = rng.normal(size=(rays, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    ao = np.ones(n)
    for i in range(n):
        nv = nor[i]
        o = Vector(co[i] + nv * 0.002)
        occ = 0.0
        tot = 0.0
        for d in dirs:
            c = float(np.dot(d, nv))
            if c < 0:
                d = -d
                c = -c
            hit = bvh.ray_cast(o, Vector(d), dist)
            w = c
            tot += w
            if hit[0] is not None:
                occ += w * (1.0 - hit[3] / dist) ** 0.5
        ao[i] = 1.0 - strength * occ / max(tot, 1e-6)
    zmax = max(co[:, 2].max(), 1e-3)
    grad = 0.82 + 0.18 * np.clip(co[:, 2] / zmax, 0, 1) ** 0.6
    val = np.clip(ao * grad, 0.25, 1.0)
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "POINT")
    cols = np.ones((n, 4))
    cols[:, 0] = cols[:, 1] = cols[:, 2] = val
    attr.data.foreach_set("color", cols.ravel())
    me.color_attributes.active_color = attr
    return attr
