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


def make_materials(char="knight"):
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
        m.diffuse_color = (*rgb, 1.0)
        m.metallic = met
        m.roughness = rough
        out[name] = m
    return out
