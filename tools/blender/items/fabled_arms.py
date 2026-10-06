"""bh-039: the Fabled Arms — fifty-four named weapons from Legendary to Primordial (game/src/data/data_fabled.gd).

Every arm is one of the parametric weapon builders (item_weapons.py, artisan_weapons.py) in its own palette, with its
own ornaments: halos, wings, sun crowns, rune rings, clock dials, serpent coils, roots, obsidian shards, lava petals,
scales... Divine and Primordial arms carry the richest ornaments; the moving light is added in the game (FabledFx).

  blender -b --factory-startup --python tools/blender/items/fabled_arms.py -- [models] [icons] [ids...]
  python tools/blender/items/fabled_arms.py post        # 128 px game icons + contact sheets (system Python, PIL)

Models: game/assets/items/<id>.glb (hand-socket convention: grip at the origin, long axis +Z).
Icons: raw renders in work/lemondev/bh-039/scratch/icons_raw, game icons in game/assets/ui/icons/items3d/<id>.png.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RAW = os.path.join(ROOT, "work", "lemondev", "bh-039", "scratch", "icons_raw")
EVID = os.path.join(ROOT, "output", "bh-039")
ITEMS_DIR = os.path.join(ROOT, "game", "assets", "items")
GAME_ICONS = os.path.join(ROOT, "game", "assets", "ui", "icons", "items3d")

# id: (tier, weapon type, metal hex, trim hex, glow hex, builder spec, ornaments)
#   spec: builder parameters; "M" / "T" / "G" / "J" / "D" stand for this arm's metal, trim, glow, gem and dark keys
#   ornaments: names from ORNAMENTS (each with its own parameters)
L, A, C, D, E, P = "legendary", "aether", "cosmic", "divine", "eternal", "primordial"
ARMS = {
    # ---- Legendary --------------------------------------------------------------------------------------------------
    "fa_vigil_of_the_last_oath": (L, "sword", "c8ccd4", "d8b060", "ffe6a0",
        {"len": 0.92, "w": (0.056, 0.034), "shape": "waisted", "blade": "M", "guard": "winged", "guard_half": 0.14, "guard_mat": "T",
         "pommel": "disc", "pommel_mat": "T", "grip_mat": "crimson", "gem": "J", "glow": "G", "lugs": True}, ["oath_tabard"]),
    "fa_gravewind_cleaver": (L, "greataxe", "8a9a98", "a0a8a0", "9cf0c0",
        {"two_handed": True, "head": "moon", "double": True, "head_mat": "M", "head_scale": 1.3, "band_mat": "T", "haft_mat": "darkwood",
         "glow": "G", "wrap": "forest", "pommel": True}, ["wind_ribbons"]),
    "fa_hearthguard_maul": (L, "club", "3a3430", "c07840", "ff8a30",
        {"kind": "flanged", "head_mat": "M", "flanges": 8, "glow": "G", "grip_mat": "redleather", "haft_mat": "darkwood"}, ["hearth_ring"]),
    "fa_thornwake": (L, "spear", "6a5a40", "8a7040", "c8e080",
        {"head": "barbed", "head_len": 0.38, "head_w": 0.075, "head_mat": "M", "shaft_mat": "darkwood", "band_mat": "T", "glow": "G"},
        ["thorn_vine"]),
    "fa_widows_needle": (L, "dagger", "202024", "8a8aa0", "a060ff",
        {"len": 0.32, "w": (0.02, 0.01), "blade": "M", "guard": "disc", "guard_mat": "T", "pommel": "ring", "pommel_mat": "T", "glow": "G",
         "gem": "J", "grip_mat": "black"}, ["veil_ring"]),
    "fa_frostfang_talons": (L, "claw", "b8d0e0", "e0e8f0", "a0e0ff",
        {"blades": 4, "len": 0.32, "hook": 0.08, "spacing": 0.032, "blade": "M", "frame_mat": "T", "glow": "G", "spikes": True},
        ["ice_crown"]),
    "fa_stormherald": (L, "bow", "2a3040", "d8c060", "fff080",
        {"len": 0.78, "bend": 0.14, "recurve": 0.12, "limb_mat": "M", "orn": "T", "glow": "G", "wraps": "navy"}, ["storm_bolts"]),
    "fa_ember_mandate": (L, "staff", "2a1810", "c08040", "ff6020",
        {"head": "prongs", "gem": "G", "wood": "darkwood", "metal": "T", "band": "T"}, ["ember_crown"]),
    "fa_tidecallers_javelin": (L, "javelin", "406880", "b09060", "40a0ff",
        {"head": "barbed", "head_w": 0.045, "head_mat": "M", "shaft_mat": "ash", "band_mat": "T", "glow": "G", "fins": "teal"},
        ["shell_ring"]),
    "fa_ironvow_knuckles": (L, "knuckles", "5a5a5c", "c09050", "ffb060",
        {"mat": "M", "plate": "T", "spikes": 4, "spike_len": 0.035, "spike_mat": "T", "glow": "G"}, ["vow_studs"]),
    # ---- Aether -----------------------------------------------------------------------------------------------------
    "fa_riftsong": (A, "sword", "1c2030", "a8c0e0", "90d0ff",
        {"len": 0.9, "w": (0.046, 0.03), "shape": "sabre", "blade": "M", "guard": "swept", "guard_mat": "T", "pommel_mat": "T",
         "glow": "G", "gem": "J", "grip_mat": "navy"}, ["rift_shards"]),
    "fa_veilpiercer": (A, "crossbow", "201828", "8070a0", "b070ff", {"design": 4}, ["veil_ring"]),
    "fa_lanternwood_wand": (A, "wand", "5a3a20", "d8b060", "fff0b0", {"wood": "ash", "head": "sun", "gem": "G", "orn": "T"}, ["lantern"]),
    "fa_glasswing_axe": (A, "axe", "c8f0f0", "a0c0d0", "c0fff0",
        {"head": "crescent", "head_mat": "M", "head_scale": 1.15, "band_mat": "T", "haft_mat": "ash", "glow": "G", "double": True},
        ["glass_wings"]),
    "fa_mournsteel": (A, "greatsword", "8090a8", "c0c8d8", "b0e8ff",
        {"len": 1.22, "z0": 0.135, "w": (0.07, 0.044), "thick": 0.009, "shape": "waisted", "blade": "M", "guard": "bar", "guard_half": 0.2,
         "guard_curve": -0.05, "guard_mat": "T", "grip_len": 0.34, "grip_r": 0.018, "grip_mat": "navy", "pommel": "ring", "pommel_mat": "T",
         "glow": "G", "gem": "J"}, ["ice_crown"]),
    "fa_wyrmbone_javelin": (A, "javelin", "d8cca8", "a04020", "ff7030",
        {"head": "leaf", "head_len": 0.26, "head_w": 0.05, "head_mat": "bone", "shaft_mat": "redwood", "band_mat": "T", "glow": "G",
         "fins": "crimson"}, ["wyrm_spine"]),
    "fa_silent_canticle": (A, "club", "6080a0", "d0d8e0", "60c0ff",
        {"kind": "flanged", "head_mat": "M", "flanges": 6, "glow": "G", "grip_mat": "navy", "haft_mat": "darkwood"}, ["bell_rings"]),
    "fa_nightjar_claws": (A, "claw", "18141c", "7050a0", "9050e0",
        {"blades": 3, "len": 0.3, "hook": 0.1, "spacing": 0.04, "blade": "M", "frame_mat": "T", "glow": "G"}, ["night_feathers"]),
    # ---- Cosmic -----------------------------------------------------------------------------------------------------
    "fa_polaris_edge": (C, "sword", "5a6ab0", "c9d2ff", "c0d0ff",
        {"len": 0.98, "w": (0.054, 0.032), "shape": "leaf", "blade": "M", "guard": "winged", "guard_half": 0.15, "guard_mat": "T",
         "pommel": "spike", "pommel_mat": "T", "gem": "J", "glow": "G", "lugs": True}, ["polestar", "orbit"]),
    "fa_nebula_reaper": (C, "greataxe", "6a58a8", "c8b8f0", "b080ff",
        {"two_handed": True, "head": "moon", "head_mat": "M", "head_scale": 1.45, "band_mat": "T", "haft_mat": "darkwood", "glow": "G",
         "pommel": True, "wrap": "violet"}, ["orbit", "nebula_gems"]),
    "fa_meridian_lance": (C, "spear", "5a6cac", "e8e0a0", "a0c8ff",
        {"head": "lance", "head_len": 0.48, "head_mat": "M", "shaft_mat": "darkwood", "band_mat": "T", "glow": "G"}, ["orbit", "polestar"]),
    "fa_starwell": (C, "staff", "34408a", "d0d8ff", "9cb0ff", {"head": "orb", "gem": "G", "wood": "darkwood", "metal": "T", "band": "T"},
        ["orbit", "star_ring"]),
    "fa_huntsman_of_seven_stars": (C, "bow", "5868a8", "d8d8f0", "b0c0ff",
        {"len": 0.84, "bend": 0.14, "recurve": 0.1, "limb_mat": "M", "orn": "T", "glow": "G", "wraps": "navy"}, ["seven_stars"]),
    "fa_fists_of_the_falling_sky": (C, "knuckles", "7068b0", "d0c0ff", "c0a0ff",
        {"mat": "M", "plate": "T", "spikes": 3, "spike_len": 0.04, "spike_mat": "T", "glow": "G"}, ["meteor_studs"]),
    "fa_moonshard": (C, "dagger", "c0d0e8", "e8f0ff", "c8e8ff",
        {"len": 0.34, "shape": "crescent", "blade": "M", "guard_mat": "T", "glow": "G", "gem": "J", "grip_mat": "navy"}, ["moon"]),
    "fa_eclipse_arbalest": (C, "crossbow", "3a3058", "e0a050", "8060ff", {"design": 9}, ["eclipse"]),
    # ---- Divine -----------------------------------------------------------------------------------------------------
    "fa_seraphs_promise": (D, "sword", "f0ead8", "e0b048", "fff0c0",
        {"len": 1.0, "w": (0.06, 0.036), "shape": "waisted", "blade": "M", "guard": "winged", "guard_half": 0.16, "guard_mat": "T",
         "pommel": "spike", "pommel_mat": "T", "gem": "J", "glow": "G", "lugs": True, "grip_mat": "white"}, ["seraph_wings", "halo_small"]),
    "fa_benediction": (D, "greatsword", "e8e4d8", "d8a840", "ffe090",
        {"len": 1.3, "z0": 0.135, "w": (0.08, 0.05), "thick": 0.009, "shape": "straight", "blade": "M", "guard": "winged", "guard_half": 0.24,
         "guard_mat": "T", "grip_len": 0.34, "grip_r": 0.018, "grip_mat": "white", "pommel": "disc", "pommel_mat": "T", "gem": "J",
         "glow": "G", "lugs": True}, ["halo_big", "cross_guard_gems"]),
    "fa_dawnspear": (D, "spear", "f0d8a0", "e0a030", "ffb040",
        {"head": "partisan", "head_len": 0.42, "head_w": 0.09, "head_mat": "M", "shaft_mat": "ash", "band_mat": "T", "glow": "G",
         "tassel": "white"}, ["sun_crown"]),
    "fa_choirmasters_mace": (D, "club", "e8e0c8", "d8b050", "fff4b0",
        {"kind": "flanged", "head_mat": "M", "flanges": 8, "glow": "G", "grip_mat": "white", "haft_mat": "ash"}, ["bell_rings", "halo_small"]),
    "fa_final_verdict": (D, "greataxe", "e0dcd0", "c8a040", "ffe8a0",
        {"two_handed": True, "head": "broad", "double": True, "head_mat": "M", "head_scale": 1.3, "band_mat": "T", "haft_mat": "ash",
         "glow": "G", "pommel": True, "wrap": "white"}, ["verdict_swords", "seraph_wings_small"]),
    "fa_featherfall": (D, "bow", "f0ece0", "d8b060", "f0ffe8",
        {"len": 0.84, "bend": 0.13, "recurve": 0.13, "limb_mat": "M", "orn": "T", "glow": "G", "leaf_tips": "T"}, ["bow_feathers", "halo_small"]),
    "fa_herald_of_morning": (D, "staff", "f0e0b0", "e0a830", "ffd060", {"head": "star", "gem": "G", "wood": "ash", "metal": "T", "band": "T"},
        ["sun_crown", "seraph_wings_small"]),
    "fa_sanctum": (D, "wand", "f0ead8", "d8b048", "fff0a0", {"wood": "pearl", "head": "claw", "gem": "G", "orn": "T"}, ["hexagram", "halo_small"]),
    "fa_auroras_reach": (D, "javelin", "c8f0e8", "b0a0e0", "70ffd0",
        {"head": "sun", "head_len": 0.26, "head_mat": "M", "shaft_mat": "ash", "band_mat": "T", "glow": "G", "fins": "T"}, ["aurora_ribbons"]),
    "fa_penance": (D, "knuckles", "e8e0c8", "d8a838", "ffe080",
        {"mat": "M", "plate": "T", "spikes": 3, "spike_len": 0.03, "spike_mat": "T", "glow": "G"}, ["scales"]),
    # ---- Eternal ----------------------------------------------------------------------------------------------------
    "fa_last_hour": (E, "sword", "e8d8e0", "e0b088", "ff90c8",
        {"len": 0.96, "w": (0.05, 0.03), "shape": "straight", "blade": "M", "guard": "disc", "guard_half": 0.07, "guard_mat": "T",
         "pommel": "disc", "pommel_mat": "T", "gem": "J", "glow": "G"}, ["clock", "hourglass_pommel"]),
    "fa_aeons_patience": (E, "greatsword", "d8d0e0", "d0a888", "ffb0d8",
        {"len": 1.26, "z0": 0.135, "w": (0.072, 0.048), "thick": 0.009, "shape": "waisted", "blade": "M", "guard": "winged", "guard_half": 0.2,
         "guard_mat": "T", "grip_len": 0.34, "grip_r": 0.018, "pommel": "disc", "pommel_mat": "T", "glow": "G", "gem": "J"}, ["clock", "orbit"]),
    "fa_evermoon": (E, "spear", "d0d0f0", "c0a8e0", "e0c0ff",
        {"head": "glaive", "head_len": 0.48, "head_mat": "M", "shaft_mat": "darkwood", "band_mat": "T", "glow": "G"}, ["moon", "orbit"]),
    "fa_stillwater_bow": (E, "bow", "e0d0e0", "d8b0a0", "ff98d0",
        {"len": 0.8, "bend": 0.12, "recurve": 0.08, "limb_mat": "M", "orn": "T", "glow": "G", "wraps": "teal"}, ["ripple_rings"]),
    "fa_talons_of_the_long_dusk": (E, "claw", "302040", "d0a0c0", "e080ff",
        {"blades": 3, "len": 0.34, "hook": 0.07, "blade": "M", "frame_mat": "T", "glow": "G", "spikes": True}, ["clock"]),
    "fa_unwritten_chronicle": (E, "staff", "e8d8d0", "d0a890", "ffc0e0", {"head": "fork", "gem": "G", "wood": "darkwood", "metal": "T", "band": "T"},
        ["book", "orbit"]),
    "fa_everember": (E, "axe", "e0c8c8", "d0a070", "ff90b0",
        {"head": "bearded", "head_mat": "M", "head_scale": 1.15, "band_mat": "T", "haft_mat": "redwood", "glow": "G", "pommel": True},
        ["clock", "ember_crown"]),
    "fa_sandglass_arbalest": (E, "crossbow", "d8c8b0", "d0a070", "ffc0a0", {"design": 7}, ["hourglass", "clock"]),
    # ---- Primordial -------------------------------------------------------------------------------------------------
    "fa_sunderer_of_ages": (P, "greatsword", "5c4c52", "802818", "ff5010",
        {"len": 1.34, "z0": 0.135, "w": (0.11, 0.08), "thick": 0.012, "shape": "straight", "tip": 0.08, "blade": "M", "guard": "bar",
         "guard_half": 0.22, "guard_curve": 0.06, "guard_mat": "D", "grip_len": 0.36, "grip_r": 0.02, "pommel": "spike", "pommel_mat": "T",
         "glow": "G", "serrate": True}, ["obsidian_spine", "lava_cracks", "molten_core"]),
    "fa_coil_of_the_first_serpent": (P, "spear", "64503f", "c06020", "ff7020",
        {"head": "leaf", "head_len": 0.46, "head_w": 0.085, "head_mat": "M", "shaft_mat": "darkwood", "band_mat": "T", "glow": "G"},
        ["serpent_coil", "molten_core"]),
    "fa_titans_knuckle": (P, "knuckles", "8a7868", "a06030", "e08040",
        {"mat": "M", "plate": "D", "spikes": 4, "spike_len": 0.05, "spike_mat": "D", "glow": "G"}, ["boulders", "lava_cracks"]),
    "fa_elderroot": (P, "staff", "5a4028", "608040", "80e060",
        {"head": "branch", "gem": "G", "wood": "darkwood", "metal": "T", "band": "T", "leaves": "leaf"}, ["root_coil", "leaf_crown"]),
    "fa_skyfall": (P, "bow", "5c4436", "c05020", "ff6010",
        {"len": 0.86, "bend": 0.15, "recurve": 0.12, "limb_mat": "M", "orn": "T", "glow": "G", "horn_tips": "D", "wraps": "redleather"},
        ["meteor_studs", "obsidian_spine"]),
    "fa_maw_of_the_deep": (P, "greataxe", "3a6080", "40a0a0", "2080ff",
        {"two_handed": True, "head": "crescent", "double": True, "head_mat": "M", "head_scale": 1.5, "band_mat": "T", "haft_mat": "darkwood",
         "glow": "G", "pommel": True, "spike_mat": "bone"}, ["maw_teeth", "serpent_coil"]),
    "fa_obsidian_heart": (P, "dagger", "5c4868", "a03020", "c040ff",
        {"len": 0.36, "shape": "kris", "blade": "M", "guard_mat": "T", "glow": "G", "gem": "J", "grip_mat": "black"}, ["obsidian_crown", "molten_core"]),
    "fa_cinder_tempest": (P, "axe", "6e5e56", "c06030", "ff8030",
        {"head": "broad", "head_mat": "M", "head_scale": 1.25, "band_mat": "T", "haft_mat": "darkwood", "glow": "G", "pommel": True,
         "double": True}, ["cinder_spiral", "lava_cracks"]),
    "fa_wyrmfathers_claws": (P, "claw", "7a4830", "d0a040", "ff4010",
        {"blades": 4, "len": 0.36, "hook": 0.09, "spacing": 0.034, "blade": "M", "frame_mat": "T", "glow": "G", "spikes": True,
         "scales": "D"}, ["wyrm_horns", "molten_core"]),
    "fa_genesis": (P, "wand", "6e4434", "d09040", "ff6030", {"wood": "darkwood", "head": "claw", "gem": "G", "orn": "T"},
        ["lava_flower", "molten_core"]),
}

ORDER = list(ARMS)
TIER_BASE = {L: "BH_Steel", A: "BH_Steel", C: "BH_Steel", D: "BH_Steel", E: "BH_Steel", P: "BH_Steel"}
TIER_TRIM = {L: "BH_Gold", A: "BH_Silver", C: "BH_Silver", D: "BH_Gold", E: "BH_Gold", P: "BH_Gold"}


def srgb(h):
    return tuple((int(h[i:i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4))


def palette(iid):
    import item_kit as K
    tier, wt, metal, trim, glow = ARMS[iid][:5]
    k = {}
    k["M"] = "fa_%s_metal" % iid
    K.MAT[k["M"]] = (TIER_BASE[tier], srgb(metal), 0.6 if tier in (C, P) else 0.95, 0.26, None, 0)
    k["T"] = "fa_%s_trim" % iid
    K.MAT[k["T"]] = (TIER_TRIM[tier], srgb(trim), 1.0, 0.24, None, 0)
    g = srgb(glow)
    k["G"] = "fa_%s_glow" % iid
    K.MAT[k["G"]] = ("BH_Emissive", g, 0.0, 0.25, g, 2.4 if tier in (D, P) else 1.8)
    k["J"] = "fa_%s_gem" % iid
    K.MAT[k["J"]] = ("BH_Gem", tuple(c * 0.7 for c in g), 0.0, 0.06, g, 1.3)
    k["D"] = "fa_%s_dark" % iid
    K.MAT[k["D"]] = ("BH_Steel", srgb("4a4250"), 0.6, 0.25, None, 0)
    return k


def _spec(iid, k):
    s = dict(ARMS[iid][5])
    for key, v in list(s.items()):
        if isinstance(v, str) and v in k:
            s[key] = k[v]
    return s


def _remap(parts, k):
    import item_kit as K
    for p in parts:
        src = K.MAT.get(p.mat)
        if src is None or p.mat.startswith("fa_"):
            continue
        if src[4] or src[0] in ("BH_Gem", "BH_Aether", "BH_Emissive"):
            p.mat = k["G"]
        elif p.mat in ("bright", "silver", "gold", "brass", "paleg", "bronze", "copper", "sunsteel"):
            p.mat = k["T"]
        elif src[0] not in ("BH_Leather", "BH_Cloth_Secondary", "BH_Wood"):
            p.mat = k["M"]
    return parts


def base_parts(iid, k):
    import item_weapons as W
    import artisan_weapons as AW
    wt = ARMS[iid][1]
    s = _spec(iid, k)
    if wt in ("sword", "greatsword"):
        return W.sword(s)
    if wt in ("axe", "greataxe"):
        return W.axe(s)
    if wt == "spear":
        return W.spear(s)
    if wt == "javelin":
        return W.javelin(s)
    if wt == "club":
        return W.club(s)
    if wt == "dagger":
        return W.dagger(s)
    if wt == "claw":
        return W.claw(s)
    if wt == "knuckles":
        return W.knuckles(s)
    if wt == "bow":
        return W.bow(s)
    if wt == "staff":
        return W.staff(s)
    if wt == "wand":
        return W.wand(s)
    if wt == "crossbow":
        return _remap(AW.crossbow(s), k)
    raise KeyError(wt)


# ------------------------------------------------------------------------------------------------------ ornaments
def _frame(parts, wt):
    import numpy as np
    V = np.vstack([p.V for p in parts])
    lo, hi = V.min(0), V.max(0)
    long_z = wt not in ("bow", "crossbow", "claw", "knuckles")
    if long_z:
        head = 0.86 if wt in ("staff", "wand", "spear", "javelin", "club", "axe", "greataxe") else 0.62
        c = (0.0, 0.0, lo[2] + (hi[2] - lo[2]) * head)
        r = max(0.055, min(0.15, (hi[0] - lo[0]) * 0.55))
    else:
        c = tuple(float(x) for x in (lo + hi) / 2)
        r = 0.11
    return lo, hi, c, r, long_z


def _feather(x, z, side, mat, n, scale=1.0, lift=0.045):
    import artisan_weapons as AW
    out = []
    for j in range(n):
        s = scale * (1.0 - 0.08 * j)
        pts = [(x, z + j * lift), (x + side * 0.07 * s, z + j * lift + 0.025 * s), (x + side * (0.13 + j * 0.014) * s, z + j * lift + 0.1 * s),
               (x + side * 0.035 * s, z + j * lift + 0.065 * s)]
        out.append(AW.plate(pts, mat, 0.008, 0.002))
    return out


def ornament(name, parts, wt, k):
    """Extra pieces for one ornament, placed from the weapon's bounds."""
    import numpy as np
    import item_kit as K
    import boss_regalia as RG
    from item_kit import Rx, Ry, Rz
    lo, hi, c, r, long_z = _frame(parts, wt)
    M_, T, G, J, Dk = k["M"], k["T"], k["G"], k["J"], k["D"]
    span = hi[2] - lo[2]
    out = []
    zgrip = 0.0
    if name in ("halo_small", "halo_big"):
        rr = r * (1.3 if name == "halo_big" else 0.95)
        cz = (c[0], c[1], hi[2] - (0.32 if name == "halo_big" else 0.12) * span) if long_z else c
        out.append(K.ring_tube(cz, rr, 0.007, G, axis="y", n=36))
        out.append(K.ring_tube(cz, rr * 1.12, 0.004, T, axis="y", n=36))
        for i in range(12 if name == "halo_big" else 8):
            a = math.radians(i * (30 if name == "halo_big" else 45))
            out.append(K.cone_spike((cz[0] + rr * 1.12 * math.cos(a), cz[1], cz[2] + rr * 1.12 * math.sin(a)),
                                    (cz[0] + rr * 1.42 * math.cos(a), cz[1], cz[2] + rr * 1.42 * math.sin(a)), 0.006, T))
    elif name in ("seraph_wings", "seraph_wings_small", "glass_wings"):
        sc = 1.3 if name == "seraph_wings" else 0.9
        zz = 0.1 if wt in ("sword", "greatsword") else (lo[2] + span * 0.62 if long_z else c[2])
        for side in (-1, 1):
            out += _feather(side * 0.03, zz, side, T if name != "glass_wings" else G, 5, sc)
            out += _feather(side * 0.03, zz + 0.012, side, G, 3, sc * 0.75, 0.05)
    elif name == "sun_crown":
        cz = (0, 0, hi[2] - 0.2 * span) if long_z else c
        out.append(K.ring_tube(cz, r * 1.05, 0.009, T, axis="y", n=32))
        for i in range(16):
            a = math.radians(i * 22.5)
            L_ = 1.7 if i % 2 == 0 else 1.35
            out.append(K.cone_spike((cz[0] + r * 1.05 * math.cos(a), 0, cz[2] + r * 1.05 * math.sin(a)),
                                    (cz[0] + r * L_ * math.cos(a), 0, cz[2] + r * L_ * math.sin(a)), 0.008, G if i % 2 else T))
        out.append(K.gem(cz, r * 0.4, J, rot=(90, 0, 0)))
    elif name == "hexagram":
        cz = (0, -0.012, hi[2] - 0.08)
        for rot in (90.0, 270.0):
            tri = [(r * 1.1 * math.cos(math.radians(rot + i * 120)), r * 1.1 * math.sin(math.radians(rot + i * 120))) for i in range(3)]
            for i in range(3):
                a, b = tri[i], tri[(i + 1) % 3]
                out.append(K.tube([(a[0], cz[1], cz[2] + a[1]), (b[0], cz[1], cz[2] + b[1])], [0.004, 0.004], G, n=5))
        out.append(K.ring_tube(cz, r * 1.2, 0.004, T, axis="y", n=32))
    elif name == "bell_rings":
        for i, rr in enumerate((r * 1.0, r * 1.35)):
            cz = (0, 0, hi[2] - 0.12 - 0.04 * i)
            out.append(K.ring_tube(cz, rr, 0.006, T if i == 0 else G, axis="z", n=32).rot(Rx(12 if i else -12), cz))
        for i in range(4):
            a = math.radians(i * 90 + 45)
            out.append(K.lathe([(0, 0), (0.016, -0.004), (0.02, -0.03), (0.0, -0.03)], T, 10).move((r * 1.35 * math.cos(a), r * 1.35 * math.sin(a), hi[2] - 0.17)))
    elif name == "verdict_swords":
        for i in range(3):
            a = math.radians(i * 120 + 90)
            p0 = np.array((r * 1.25 * math.cos(a), r * 1.25 * math.sin(a) * 0.4, hi[2] - 0.2 * span))
            out.append(K.box(0.012, 0.004, 0.14, tuple(p0 + (0, 0, 0.04)), G, 0.002))
            out.append(K.box(0.05, 0.008, 0.01, tuple(p0 - (0, 0, 0.035)), T, 0.002))
    elif name == "bow_feathers":
        for side in (-1, 1):
            out += _feather(-0.02, side * 0.22 if side > 0 else -0.42, 1, T, 4, 0.9)
            out += _feather(-0.02, side * 0.3 if side > 0 else -0.34, -1, G, 3, 0.7)
    elif name == "aurora_ribbons":
        for j, mat in enumerate((G, T, J)):
            pts = [(0.03 * math.sin(i * 0.9 + j), -0.012 * j, hi[2] - 0.32 - i * 0.07) for i in range(8)]
            out.append(K.tube(pts, [0.009 - 0.0008 * i for i in range(8)], mat, n=6))
    elif name == "scales":
        cz = np.array(c) + (0.0, -0.03, 0.09)
        out.append(K.box(0.008, 0.008, 0.08, tuple(cz), T, 0.002))
        out.append(K.box(0.14, 0.008, 0.008, tuple(cz + (0, 0, 0.04)), T, 0.002))
        for sx in (-1, 1):
            p = cz + (sx * 0.065, 0, 0.0)
            out.append(K.tube([tuple(p + (0, 0, 0.04)), tuple(p - (0, 0, 0.005))], [0.002, 0.002], T, n=4))
            out.append(K.lathe([(0, 0), (0.028, 0.006), (0.03, 0.012), (0.0, 0.004)], G, 12).move(tuple(p - (0, 0, 0.02))))
    elif name == "cross_guard_gems":
        for sx in (-1, 1):
            out.append(K.gem((sx * 0.16, 0, 0.12), 0.016, J, rot=(90, 0, 0)))
        out += W_channel(k, 0.2, 1.2)
    elif name in ("clock",):
        cz = (c[0], c[1] - 0.02, (lo[2] + span * 0.18) if long_z else c[2])
        rr = r * 0.9
        out.append(K.ring_tube(cz, rr, 0.006, T, axis="y", n=36))
        for i in range(12):
            a = math.radians(i * 30)
            out.append(K.box(0.008, 0.004, 0.02, (cz[0] + rr * 0.82 * math.cos(a), cz[1], cz[2] + rr * 0.82 * math.sin(a)), G).rot(Ry(-i * 30), (cz[0] + rr * 0.82 * math.cos(a), cz[1], cz[2] + rr * 0.82 * math.sin(a))))
        out.append(K.box(0.006, 0.006, rr * 0.7, (cz[0], cz[1] - 0.004, cz[2] + rr * 0.33), G))
        out.append(K.box(rr * 0.5, 0.006, 0.006, (cz[0] + rr * 0.24, cz[1] - 0.004, cz[2]), T))
    elif name in ("hourglass", "hourglass_pommel"):
        cz = (c[0], c[1], lo[2] + 0.03) if name == "hourglass_pommel" else (c[0], c[1] - 0.06, c[2])
        glass = [(-0.03, 0.045), (0.03, 0.045), (0.004, 0.0), (0.03, -0.045), (-0.03, -0.045), (-0.004, 0.0)]
        out.append(RG.slab([(u, v) for u, v in glass], 0.02, G).move(cz))
        for z in (0.05, -0.05):
            out.append(K.box(0.075, 0.03, 0.008, (cz[0], cz[1], cz[2] + z), T))
    elif name == "orbit":
        cz = c
        out.append(K.ring_tube(cz, r * 1.15, 0.005, T, axis="z", n=36).rot(Rx(22), cz))
        for i in range(3):
            a = math.radians(i * 120 + 30)
            p = (Rx(22) @ np.array((r * 1.15 * math.cos(a), r * 1.15 * math.sin(a), 0.0))) + np.array(cz)
            out.append(K.gem(tuple(p), 0.014, J, facets=4))
    elif name == "polestar":
        cz = (0, -0.02, hi[2] - 0.45 * span) if long_z else c
        out.append(RG.slab([(u * 0.09, v * 0.09) for u, v in RG.star_outline(0.9, 0.22, k=4, rot=90.0)], 0.012, T).move(cz))
        out.append(K.gem(cz, 0.018, J, rot=(90, 0, 0)))
    elif name == "star_ring":
        cz = (0, 0, hi[2] - 0.08)
        for i in range(7):
            a = math.radians(i * 360 / 7)
            p = (r * 1.4 * math.cos(a), 0, cz[2] + r * 1.4 * math.sin(a))
            out.append(RG.slab([(u * 0.03, v * 0.03) for u, v in RG.star_outline(0.9, 0.35, k=5, rot=90.0)], 0.006, G).move(p))
    elif name == "seven_stars":
        for i in range(7):
            z = (i - 3) * 0.1
            x = -0.13 * (abs(z) / 0.65) ** 1.5 * 0.9 - 0.02
            out.append(RG.slab([(u * 0.028, v * 0.028) for u, v in RG.star_outline(0.9, 0.35, k=5, rot=90.0)], 0.006, G).move((x, -0.018, z)))
    elif name == "nebula_gems":
        for i in range(5):
            out.append(K.gem((0.06 + 0.02 * math.sin(i), -0.03, hi[2] - 0.05 - i * 0.05), 0.014, J, rot=(90, 0, 0)))
    elif name == "moon":
        cz = (0, -0.02, hi[2] - 0.3 * span) if long_z else c
        pts = [(0.06 * math.cos(math.radians(a)), 0.06 * math.sin(math.radians(a))) for a in range(-110, 111, 20)]
        pts += [(0.035 * math.cos(math.radians(a)) + 0.018, 0.045 * math.sin(math.radians(a))) for a in range(110, -111, -20)]
        out.append(RG.slab(pts, 0.01, G).move(cz))
    elif name == "eclipse":
        cz = (c[0], c[1] - 0.08, c[2])
        out.append(K.ring_tube(cz, 0.07, 0.01, T, axis="y", n=32))
        out.append(K.sphere(0.055, cz, Dk, 14, 10))
        for i in range(12):
            a = math.radians(i * 30)
            out.append(K.cone_spike((cz[0] + 0.075 * math.cos(a), cz[1], cz[2] + 0.075 * math.sin(a)),
                                    (cz[0] + 0.11 * math.cos(a), cz[1], cz[2] + 0.11 * math.sin(a)), 0.005, G))
    elif name == "ripple_rings":
        for i, rr in enumerate((0.05, 0.075, 0.1)):
            out.append(K.ring_tube((0.01, 0, 0), rr, 0.004, G if i % 2 == 0 else T, axis="x", n=28))
    elif name == "book":
        cz = (0, 0, hi[2] - 0.12)
        out.append(K.box(0.1, 0.03, 0.12, cz, T, 0.004))
        out.append(K.box(0.09, 0.034, 0.11, (cz[0], cz[1], cz[2]), "paper", 0.002))
        out.append(K.gem((cz[0], cz[1] - 0.02, cz[2]), 0.018, J, rot=(90, 0, 0)))
    elif name == "obsidian_spine":
        n = 6
        for i in range(n):
            z = lo[2] + span * (0.3 + 0.55 * i / (n - 1)) if long_z else lo[2] + span * (0.15 + 0.7 * i / (n - 1))
            sx = -1 if i % 2 else 1
            x0 = 0.03 if long_z else -0.06 * (abs(z) / max(abs(lo[2]), 0.1))
            out.append(K.crystal((x0 + sx * 0.035, 0.0, z), 0.1, 0.015, Dk, rot=(0, sx * 40, 0)))
            out.append(K.cone_spike((x0 + sx * 0.02, 0.0, z - 0.02), (x0 + sx * 0.07, 0.0, z + 0.04), 0.004, G))
    elif name == "lava_cracks":
        if long_z:
            out += W_channel(k, lo[2] + span * 0.2, lo[2] + span * 0.92)
        else:
            for i in range(3):
                out.append(K.box(0.006, 0.05, 0.05, (c[0] + 0.04, c[1], c[2] - 0.04 + i * 0.04), G, 0.002))
    elif name == "molten_core":
        cz = (0, 0, lo[2] + span * 0.2) if long_z else c
        out.append(K.sphere(0.024, cz, G, 12, 8))
        out.append(K.ring_tube(cz, 0.034, 0.005, Dk, axis="z", n=18))
        out.append(K.ring_tube(cz, 0.034, 0.005, Dk, axis="x", n=18))
    elif name == "serpent_coil":
        z0, z1 = lo[2] + span * 0.25, hi[2] - span * 0.12
        pts = []
        for i in range(40):
            u = i / 39
            a = u * math.tau * 3.2
            rr = 0.04 + 0.01 * math.sin(u * 9)
            pts.append((rr * math.cos(a), rr * math.sin(a), z0 + (z1 - z0) * u))
        out.append(K.tube(pts, [0.006 + 0.008 * math.sin(math.pi * min(1, i / 36)) for i in range(40)], T, n=7))
        hp = pts[-1]
        out.append(K.sphere(0.017, hp, T, 10, 7, scale=(1.0, 0.8, 1.4)))
        for sy in (-1, 1):
            out.append(K.gem((hp[0] * 1.15, hp[1] + sy * 0.009, hp[2] + 0.008), 0.005, G))
    elif name == "root_coil":
        for j in range(3):
            pts = []
            for i in range(26):
                u = i / 25
                a = u * math.tau * 1.6 + j * 2.1
                rr = 0.03 + 0.012 * math.sin(u * 13 + j)
                pts.append((rr * math.cos(a), rr * math.sin(a), lo[2] + span * (0.1 + 0.62 * u)))
            out.append(K.tube(pts, [0.007 - 0.004 * i / 25 for i in range(26)], "darkwood", n=6))
        for i in range(6):
            z = lo[2] + span * (0.2 + 0.09 * i)
            a = i * 1.9
            o = [(0.0, 0.0), (0.02, 0.025), (0.0, 0.06), (-0.02, 0.025)]
            out.append(K.slab(o, 0.003, "leaf").rot(Ry(40)).rot(Rz(math.degrees(a))).move((0.04 * math.cos(a), 0.04 * math.sin(a), z)))
    elif name == "leaf_crown":
        for i in range(8):
            a = math.radians(i * 45)
            o = [(0.0, 0.0), (0.025, 0.03), (0.0, 0.08), (-0.025, 0.03)]
            out.append(K.slab(o, 0.003, "leaf" if i % 2 else G).rot(Ry(55)).rot(Rz(math.degrees(a))).move((0.05 * math.cos(a), 0.05 * math.sin(a), hi[2] - 0.2)))
    elif name == "boulders":
        for i in range(4):
            a = math.radians(i * 90 + 30)
            out.append(K.sphere(0.022, (c[0] + 0.06 * math.cos(a), c[1] + 0.035 * math.sin(a), c[2] + 0.07 * math.sin(a)), Dk, 6, 4,
                                scale=(1.0, 0.8, 1.2)))
    elif name == "meteor_studs":
        pts = [(c[0] + 0.02, c[1], c[2] + (i - 1.5) * 0.04) for i in range(4)] if wt == "knuckles" else \
              [(-0.03, -0.02, (i - 2) * 0.16) for i in range(5)]
        for p in pts:
            out.append(K.sphere(0.014, p, G, 8, 6))
            out.append(K.ring_tube(p, 0.018, 0.003, T, axis="y", n=12))
    elif name == "maw_teeth":
        for i in range(7):
            z = hi[2] - 0.05 - i * 0.035
            for sx in (-1, 1):
                out.append(K.cone_spike((sx * 0.12, 0, z), (sx * 0.15, 0, z - 0.03), 0.009, "bone"))
    elif name == "obsidian_crown":
        for i in range(6):
            a = math.radians(i * 60)
            out.append(K.crystal((0.03 * math.cos(a), 0.012 * math.sin(a), 0.05), 0.09, 0.012, Dk, rot=(math.degrees(0.6 * math.sin(a)), math.degrees(-0.6 * math.cos(a)), 0)))
    elif name == "cinder_spiral":
        pts = []
        for i in range(30):
            u = i / 29
            a = u * math.tau * 2.4
            rr = 0.05 + 0.05 * u
            pts.append((rr * math.cos(a), rr * math.sin(a), hi[2] - 0.32 + 0.28 * u))
        out.append(K.tube(pts, [0.004 + 0.003 * math.sin(math.pi * i / 29) for i in range(30)], G, n=5))
    elif name == "wyrm_horns":
        for sx in (-1, 1):
            out.append(K.tube([(sx * 0.05, 0, 0.05), (sx * 0.09, 0.01, 0.1), (sx * 0.08, 0.02, 0.17), (sx * 0.05, 0.02, 0.2)],
                              [0.014, 0.011, 0.006, 0.001], Dk, n=8))
    elif name == "lava_flower":
        cz = (0, 0, hi[2] - 0.03)
        for ring_, (n, ln, tilt) in enumerate(((6, 0.07, 40), (6, 0.05, 20))):
            for i in range(n):
                a = i * 360 / n + ring_ * 30
                o = [(0.0, 0.0), (0.02, 0.02), (0.0, ln), (-0.02, 0.02)]
                out.append(RG.slab(o, 0.004, Dk if ring_ == 0 else G, bevel=0.001).rot(Rx(tilt)).rot(Rz(a)).move(cz))
        out.append(K.sphere(0.016, (cz[0], cz[1], cz[2] + 0.015), G, 10, 8))
    elif name == "oath_tabard":
        out.append(K.tube([(0.0, -0.01, -0.02), (0.02, -0.015, -0.12), (0.01, -0.02, -0.22)], [0.012, 0.016, 0.006], "crimson", n=6))
        out.append(K.gem((0.0, -0.02, 0.118), 0.012, J, rot=(90, 0, 0)))
    elif name == "wind_ribbons":
        for j in range(2):
            pts = [(-0.02 - 0.03 * i, 0.01 * j, hi[2] - 0.35 - 0.04 * i + 0.03 * math.sin(i + j)) for i in range(7)]
            out.append(K.tube(pts, [0.006] * 7, "forest" if j else G, n=5))
    elif name == "hearth_ring":
        out.append(K.ring_tube((0, 0, hi[2] - 0.08), 0.07, 0.008, T, axis="z", n=24))
    elif name == "thorn_vine":
        for i in range(10):
            z = lo[2] + span * (0.35 + 0.045 * i)
            a = i * 1.7
            out.append(K.cone_spike((0.022 * math.cos(a), 0.022 * math.sin(a), z), (0.045 * math.cos(a), 0.045 * math.sin(a), z + 0.02), 0.005, T))
    elif name == "veil_ring":
        cz = c
        out.append(K.ring_tube(cz, r * 0.9, 0.004, G, axis="y", n=28, arc=250, a0=-30))
    elif name == "ice_crown":
        for i in range(5):
            a = math.radians(i * 72)
            base = (c[0] + 0.03 * math.cos(a), c[1] + 0.015 * math.sin(a), (lo[2] + 0.08) if long_z else c[2] - 0.06)
            out.append(K.crystal(base, 0.08, 0.012, G, rot=(math.degrees(0.4 * math.sin(a)), math.degrees(-0.5 * math.cos(a)), 0)))
    elif name == "storm_bolts":
        for side in (-1, 1):
            out.append(K.tube([(-0.05, 0, side * 0.2), (-0.02, 0, side * 0.26), (-0.06, 0, side * 0.3), (-0.03, 0, side * 0.36)], [0.006] * 4, G, n=4))
    elif name == "ember_crown":
        for i in range(6):
            a = math.radians(i * 60)
            out.append(K.cone_spike((0.03 * math.cos(a), 0.03 * math.sin(a), hi[2] - 0.12), (0.055 * math.cos(a), 0.055 * math.sin(a), hi[2] - 0.02), 0.007, G))
    elif name == "shell_ring":
        out.append(K.ring_tube((0, 0, hi[2] - 0.3), 0.025, 0.006, T, axis="z", n=16))
        out.append(K.lathe([(0, 0), (0.02, 0.01), (0.01, 0.03), (0, 0.035)], "pearl", 10).move((0, 0, hi[2] - 0.33)))
    elif name == "vow_studs":
        for i in range(4):
            out.append(K.ring_tube((c[0] + 0.03, c[1], c[2] - 0.045 + i * 0.03), 0.012, 0.003, G, axis="x", n=12))
    elif name == "rift_shards":
        for i in range(4):
            z = 0.25 + i * 0.15
            out.append(K.crystal((0.06 + 0.01 * (i % 2), -0.01, z), 0.06, 0.008, G, rot=(0, 30, 0)))
    elif name == "lantern":
        cz = (0, 0, hi[2] + 0.02)
        out.append(K.ring_tube(cz, 0.028, 0.003, T, axis="z", n=14))
        out.append(K.ring_tube((cz[0], cz[1], cz[2] + 0.04), 0.018, 0.003, T, axis="z", n=14))
        out.append(K.sphere(0.016, (cz[0], cz[1], cz[2] + 0.02), G, 10, 8))
    elif name == "wyrm_spine":
        for i in range(6):
            z = lo[2] + span * (0.25 + 0.07 * i)
            out.append(K.cone_spike((0.012, 0, z), (0.04, 0, z + 0.025), 0.006, "bone"))
    elif name == "night_feathers":
        out += _feather(-0.06, 0.04, -1, "black", 4, 0.8)
        out += _feather(0.06, 0.04, 1, "black", 4, 0.8)
    else:
        raise KeyError(name)
    return out


def W_channel(k, z0, z1):
    import item_weapons as W
    return W.channel(z0, z1, 0.014, 0.006, 0.012, k["G"])


def build_parts(iid):
    import item_kit as K
    k = palette(iid)
    parts = base_parts(iid, k)
    wt = ARMS[iid][1]
    extra = []
    for o in ARMS[iid][6]:
        extra += ornament(o, parts, wt, k)
    return parts + extra


def export_models(ids, log=print):
    sys.path.insert(0, HERE)
    import item_kit as K
    from item_kit import M
    sys.path.insert(0, K.CHARS)
    from build import reset
    import boss_regalia as RG
    report = []
    for iid in ids:
        reset()
        parts = build_parts(iid)
        obs = RG.objects_for(iid, parts)
        path = os.path.join(ITEMS_DIR, iid + ".glb")
        RG._export(path, obs)
        tris = sum(M.tri_count(o) for o in obs)
        assert tris < 16000, (iid, tris)
        report.append({"id": iid, "tris": tris})
        log("[fabled] %-36s %6d tris" % (iid, tris))
    os.makedirs(EVID, exist_ok=True)
    import json
    with open(os.path.join(EVID, "fabled_models_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    return report


def render_icons(ids, log=print):
    import bpy
    from mathutils import Vector
    sys.path.insert(0, HERE)
    import item_kit as K
    sys.path.insert(0, K.CHARS)
    from build import reset
    import build_items as B
    import boss_regalia as RG
    os.makedirs(RAW, exist_ok=True)
    for iid in ids:
        reset()
        parts = build_parts(iid)
        obs = RG.objects_for(iid, parts, textured=True)
        cam = B._studio(256)
        pitch, yaw = B._pose_for({"category": "weapon", "weapon_type": ARMS[iid][1], "id": iid}, obs[0])
        bpy.context.view_layer.update()
        pts = [o.matrix_world @ Vector(cc) for o in obs for cc in o.bound_box]
        c = sum(pts, Vector()) / len(pts)
        for o in obs:
            o.location -= c
        bpy.context.view_layer.update()
        p_, y_ = math.radians(pitch), math.radians(yaw)
        d = Vector((math.sin(y_) * math.cos(p_), -math.cos(y_) * math.cos(p_), math.sin(p_)))
        cam.location = d * 10.0
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        q = [inv @ (o.matrix_world @ Vector(cc)) for o in obs for cc in o.bound_box]
        ext = max(max(v.x for v in q) - min(v.x for v in q), max(v.y for v in q) - min(v.y for v in q))
        cam.data.ortho_scale = ext * 1.1
        cx = (max(v.x for v in q) + min(v.x for v in q)) / 2
        cy = (max(v.y for v in q) + min(v.y for v in q)) / 2
        cam.location = cam.matrix_world @ Vector((cx, cy, 0.0))
        cam.data.clip_start = 0.01
        cam.data.clip_end = 100
        bpy.context.scene.render.filepath = os.path.join(RAW, iid + ".png")
        bpy.ops.render.render(write_still=True)
        log("[icon] %s" % iid)


NAMES = {}


def post():
    """Game icons and labelled contact sheets per tier (system Python with PIL)."""
    import re
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0, HERE)
    import icons_post as IP
    src = open(os.path.join(ROOT, "game", "src", "data", "data_fabled.gd"), encoding="utf-8").read()
    for m in re.finditer(r'\["(fa_[a-z_]+)", "([^"]+)"', src):
        NAMES[m.group(1)] = m.group(2)
    os.makedirs(GAME_ICONS, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    for iid in ORDER:
        IP.game_icon(os.path.join(RAW, iid + ".png")).save(os.path.join(GAME_ICONS, iid + ".png"))
    title = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 30)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    col = {L: (255, 150, 40), A: (90, 220, 255), C: (160, 140, 255), D: (255, 225, 140), E: (255, 140, 200), P: (255, 90, 40)}
    for tier in (L, A, C, D, E, P):
        ids = [i for i in ORDER if ARMS[i][0] == tier]
        cols = 5
        cell = 260
        rows = (len(ids) + cols - 1) // cols
        img = Image.new("RGB", (cols * cell + 20, 70 + rows * (cell + 46)), (22, 20, 26))
        dr = ImageDraw.Draw(img)
        dr.text((20, 18), "Fabled Arms · %s (%d)" % (tier.title(), len(ids)), font=title, fill=col[tier])
        for j, iid in enumerate(ids):
            x, y = 10 + (j % cols) * cell, 70 + (j // cols) * (cell + 46)
            ic = IP.game_icon(os.path.join(RAW, iid + ".png"), cell - 12)
            img.paste(ic.convert("RGB"), (x + 6, y))
            dr.rectangle((x + 6, y, x + cell - 6, y + cell - 12), outline=col[tier], width=2)
            dr.text((x + 8, y + cell - 6), NAMES.get(iid, iid)[:30], font=font, fill=(235, 225, 200))
            dr.text((x + 8, y + cell + 12), ARMS[iid][1].title(), font=small, fill=(170, 165, 150))
        img.save(os.path.join(EVID, "fabled_%s.png" % tier))
        print("[fabled] sheet", tier, len(ids))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    targets = [a for a in argv if a in ("models", "icons")] or ["models"]
    ids = [a for a in argv if a in ARMS] or ORDER
    sys.path.insert(0, HERE)
    if "models" in targets:
        export_models(ids)
    if "icons" in targets:
        render_icons(ids)
    print("[fabled] done", len(ids))


if __name__ == "__main__":
    if "post" in sys.argv[1:]:
        post()
    else:
        main()
